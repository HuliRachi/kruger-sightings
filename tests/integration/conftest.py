import os
from dataclasses import dataclass
from pathlib import Path

import pytest
from databricks.sdk import WorkspaceClient

TARGET = "uat"
 
@dataclass
class UatResourceIds:
    kruger_pipeline_id: str
    orchestration_job_id: str
    warehouse_id: str
 
 
@pytest.fixture(scope="session")
def workspace_client() -> WorkspaceClient:
    """
    Generates an authorized Databricks SDK WorkspaceClient instance.
    """
    return WorkspaceClient()
 
 
@pytest.fixture(scope="session")
def uat_resource_ids(workspace_client: WorkspaceClient) -> UatResourceIds:
    """
    Looks up deployment resource IDs natively using the Databricks Python SDK,
    matching your exact kruger asset naming structures.
    """
    pipeline_id = None
    orchestration_id = None
    warehouse_id = None

    try:
        # Search for your Delta Live Tables Pipeline
        for p in workspace_client.pipelines.list_pipelines():
            name_lower = p.name.lower()
            if "pipeline" in name_lower and "kruger" in name_lower:
                pipeline_id = p.pipeline_id
                break
                
        # Search for your Multi-Task Orchestration Job
        for j in workspace_client.jobs.list():
            current_name = ""
            if hasattr(j, "settings") and j.settings and hasattr(j.settings, "name"):
                current_name = j.settings.name
            elif hasattr(j, "job_name") and j.job_name:
                current_name = j.job_name
                
            name_lower = current_name.lower()
            if "orchestration" in name_lower and "kruger" in name_lower:
                orchestration_id = j.job_id
                break

        # Locate active SQL Warehouse ID to perform count queries
        for w in workspace_client.warehouses.list():
            if "warehouse" in w.name.lower() or "kruger" in w.name.lower():  
                warehouse_id = w.id
                break

    except Exception as e:
        pytest.fail(f"Failed to query workspace metadata using Databricks SDK: {str(e)}")

    missing_resources = []
    if not pipeline_id: missing_resources.append("kruger-dlt-pipeline")
    if not orchestration_id: missing_resources.append("kruger-orchestration-job")
    
    if missing_resources:
        actual_pipelines = [p.name for p in workspace_client.pipelines.list_pipelines()]
        actual_jobs = [j.job_name if hasattr(j, "job_name") else j.settings.name for j in workspace_client.jobs.list()]
        
        pytest.fail(
            f"Could not locate deployed assets containing keys: {missing_resources}.\n"
            f"Actual pipelines found in workspace: {actual_pipelines}\n"
            f"Actual jobs found in workspace: {actual_jobs}"
        )

    if not warehouse_id:
        # Default fallback warehouse token if list permissions are restrictive
        warehouse_id = "7ffa80bc21a73630"

    return UatResourceIds(
        kruger_pipeline_id=pipeline_id,
        orchestration_job_id=orchestration_id,
        warehouse_id=warehouse_id,
    )
 
 
@pytest.fixture(scope="function")
def reset_uat(workspace_client: WorkspaceClient):
    """
    Cleans up landing volumes before test execution to isolate batch runs.
    """
    catalog = TARGET  
    landing_root = f"/Volumes/{catalog}/kruger/staging"
    subfolders = ["filtered_youtube"]
    
    for folder in subfolders:
        dir_path = f"{landing_root}/{folder}"
        try:
            for entry in workspace_client.files.list_directory_contents(dir_path):
                workspace_client.files.delete(f"{dir_path}/{entry.name}")
        except Exception:
            pass
 
    yield
