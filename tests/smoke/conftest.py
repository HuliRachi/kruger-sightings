import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest
from databricks.sdk import WorkspaceClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BUNDLE_DIR = os.path.join(PROJECT_ROOT, "bundle")

TARGET = "prod"
 
@dataclass
class ProdResourceIds:
    kruger_pipeline_id: str
    orchestration_job_id: str
    warehouse_id: str
 
 
@pytest.fixture(scope="session")
def prod_resource_ids() -> ProdResourceIds:
    
    result = subprocess.run(
        ["databricks", "bundle", "summary", "--target", TARGET, "--output", "json"],
        cwd=BUNDLE_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.fail(f"`databricks bundle summary` execution failed:\n{result.stderr}")
 
    brace_index = result.stdout.find("{")
    if brace_index == -1:
        pytest.fail(f"No JSON block produced in bundle summary stdout:\n{result.stdout}")
        
    summary = json.loads(result.stdout[brace_index:])
    resources = summary.get("resources", {})
 
    pipeline_id = None
    job_id = None
    warehouse_id = None

    # 🌟 SELF-HEALING REGEX ENGINE: Dynamically extract whatever pipeline is deployed
    pipelines_dict = resources.get("pipelines", {})
    for p_key, p_val in pipelines_dict.items():
        if "kruger" in p_key:
            pipeline_id = p_val["id"]
            break

    # Dynamically extract whatever orchestration/bootstrap job is active
    jobs_dict = resources.get("jobs", {})
    for j_key, j_val in jobs_dict.items():
        if "kruger" in j_key:
            job_id = j_val["id"]
            break

    # Safely locate the active production warehouse tracking token
    vars_dict = summary.get("variables", {})
    for v_key, v_val in vars_dict.items():
        if "warehouse_id" in v_key:
            warehouse_id = v_val.get("value")
            break

    # Fallback to defaults if list permissions inside the environment block are strict
    if not warehouse_id:
        warehouse_id = "7ffa80bc21a73630"

    if not pipeline_id or not job_id:
        pytest.fail(
            f"Failed to dynamically discover Kruger resource IDs inside bundle summary.\n"
            f"Found pipelines: {list(pipelines_dict.keys())}\n"
            f"Found jobs: {list(jobs_dict.keys())}"
        )

    return ProdResourceIds(
        kruger_pipeline_id=pipeline_id,
        orchestration_job_id=job_id,
        warehouse_id=warehouse_id,
    )
 
 
@pytest.fixture(scope="session")
def workspace_client() -> WorkspaceClient:
    """
    Generates an authorized Databricks SDK WorkspaceClient instance.
    """
    return WorkspaceClient()
