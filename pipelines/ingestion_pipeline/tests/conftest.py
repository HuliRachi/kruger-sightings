import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark():
    """Provides a local, isolated SparkSession for testing."""
    session = (
        SparkSession.builder
        .master("local")
        .appName("kruger-sighting-unit-tests")
        .config("spark.sql.shuffle.partitions", "1")
        .config("spark.default.parallelism", "1")
        .getOrCreate()
    )
    yield session
    session.stop()
