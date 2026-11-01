import os
import subprocess
import pytest

# Aligns directly with TOTAL_RECORDS = 15 configured inside your kruger data_generator.py file
EXPECTED_LANDING_COUNTS = {
    "kruger": 15,    
}

def _generate_fixed_seed_batch() -> str:
    """
    Executes your updated Kruger data generator via a CLI subprocess.
    """
    result = subprocess.run(
        ["python3", "../../data_generator.py"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"data_generator.py execution failed:\n{result.stderr}"
    # FIX: Direct the uploader up to the project root directory where batch_01 lives
    return "../../batch_01"


def _upload_batch_to_landing(workspace_client, batch_dir: str, catalog: str):
    """
    Scans the local generated batch directory and syncs it to the 
    Kruger Unity Catalog Staging Volume folder endpoint.
    """
    landing_root = f"/Volumes/{catalog}/kruger/staging"
    
    if not os.path.exists(batch_dir):
        raise FileNotFoundError(f"Target batch generation path not found: {batch_dir}")
        
    for folder in os.listdir(batch_dir):
        local_folder = os.path.join(batch_dir, folder)
        if not os.path.isdir(local_folder):
            continue
            
        for filename in os.listdir(local_folder):
            local_path = os.path.join(local_folder, filename)
            remote_path = f"{landing_root}/{folder}/{filename}"
            
            with open(local_path, "rb") as f:
                workspace_client.files.upload(remote_path, f, overwrite=True)


def _table_count_safe(workspace_client, catalog: str, warehouse_id: str, table: str) -> int:
    """
    Queries Kruger table row metrics via the Databricks SQL Statement Execution API.
    """
    try:
        result = workspace_client.statement_execution.execute_statement(
            warehouse_id=warehouse_id,
            catalog=catalog,
            schema="kruger",
            statement=f"SELECT COUNT(*) FROM {table}",
            wait_timeout="30s",
        )
        if result.status.state.value == "SUCCEEDED":
            return int(result.result.data_array[0][0])
        return 0
    except Exception:
        return 0


def test_orchestration_job_end_to_end(
    workspace_client, uat_resource_ids, reset_uat
):
    """
    Core End-to-End Integration Test for Kruger Pipeline:
    Measures existing baseline records, runs data_generator.py, uploads output JSON lines,
    triggers the DLT orchestration workflow, and asserts the records are successfully ingested.
    """
    catalog = "uat"
    
    # 1. Capture current baseline state across your valid and quarantined splits
    initial_counts = {}
    for source in EXPECTED_LANDING_COUNTS.keys():
        v_count = _table_count_safe(workspace_client, catalog, uat_resource_ids.warehouse_id, f"bronze_{source}_valid")
        q_count = _table_count_safe(workspace_client, catalog, uat_resource_ids.warehouse_id, f"bronze_{source}_quarantined")
        initial_counts[source] = v_count + q_count

    # 2. Run the programmatic data generation step 
    batch_dir = _generate_fixed_seed_batch()
    
    # 3. Synchronize generated files into Unity Catalog Staging Volumes
    _upload_batch_to_landing(workspace_client, batch_dir, catalog=catalog)
 
    # 4. Programmatically run the Databricks Ingestion Job and await final result
    run = workspace_client.jobs.run_now(
        job_id=int(uat_resource_ids.orchestration_job_id),
    ).result()
 
    assert run.state.result_state.value == "SUCCESS", (
        f"Master orchestration run failed: {run.state.state_message}"
    )
 
    # 5. Verify the growth increments match expected rows precisely
    for source, expected_new_rows in EXPECTED_LANDING_COUNTS.items():
        valid = _table_count_safe(
            workspace_client, catalog, uat_resource_ids.warehouse_id, f"bronze_{source}_valid"
        )
        quarantined = _table_count_safe(
            workspace_client, catalog, uat_resource_ids.warehouse_id, f"bronze_{source}_quarantined"
        )
        
        final_total = valid + quarantined
        net_new_processed = final_total - initial_counts[source]
        
        assert net_new_processed == expected_new_rows, (
            f"Row mismatch on {source} tables! Expected precisely {expected_new_rows} "
            f"new records to process, but the delta grew by {net_new_processed} rows."
        )
