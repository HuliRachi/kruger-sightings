import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark():
    """Retrieves the pre-configured, existing Databricks cluster Spark session for testing."""
    # This safely grabs the active cluster/notebook context without spawning a master conflict
    return SparkSession.builder.getOrCreate()
