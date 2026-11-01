import pytest

GOLD_TABLES = [
    "gold_kruger_jan_to_jun",
    "gold_kruger_jul_to_dec"
]
 
def test_kruger_pipeline_exists_and_is_reachable(workspace_client, prod_resource_ids):
    """Smoke Test: Verify the DLT ingestion pipeline is deployed and reachable."""
    pipeline = workspace_client.pipelines.get(pipeline_id=prod_resource_ids.kruger_pipeline_id)
    assert pipeline is not None, f"Pipeline {prod_resource_ids.kruger_pipeline_id} not reachable"
 
 
def test_pipeline_latest_update_did_not_fail(workspace_client, prod_resource_ids):
    """Smoke Test: Verify the most recent pipeline calculation update completed cleanly."""
    response = workspace_client.pipelines.list_updates(
        pipeline_id=prod_resource_ids.kruger_pipeline_id, max_results=1
    )
    updates = response.updates or []
    if not updates:
        print(f"Pipeline {prod_resource_ids.kruger_pipeline_id}: no update history yet — skipping check.")
        return
 
    latest = updates[0]
    assert latest.state.value not in ("FAILED", "CANCELED"), (
        f"Pipeline {prod_resource_ids.kruger_pipeline_id}'s most recent update is in an unhealthy state: {latest.state.value}"
    )
 
 
def test_orchestration_job_exists_and_is_reachable(workspace_client, prod_resource_ids):
    """Smoke Test: Verify the master orchestration job exists and can be securely pinged."""
    job = workspace_client.jobs.get(job_id=int(prod_resource_ids.orchestration_job_id))
    assert job is not None, f"Orchestration job {prod_resource_ids.orchestration_job_id} not reachable"
 
 
def test_gold_tables_are_queryable(workspace_client, prod_resource_ids):
    """Smoke Test: Query row metrics from your semi-annual split Gold tables via the SQL Warehouse."""
    for table in GOLD_TABLES:
        result = workspace_client.statement_execution.execute_statement(
            warehouse_id=prod_resource_ids.warehouse_id,
            catalog="prod",
            schema="kruger",
            statement=f"SELECT COUNT(*) FROM {table}",
            wait_timeout="30s",
        )
        assert result.status.state.value == "SUCCEEDED", (
            f"Gold table {table} is not queryable! Error: {result.status.error}"
        )
        row_count = int(result.result.data_array[0][0])
        print(f"Verified {table}: Contains {row_count} records.")
