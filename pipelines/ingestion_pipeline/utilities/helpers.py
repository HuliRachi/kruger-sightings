from pyspark.sql import SparkSession

def get_catalog() -> str:
    """Retrieves the active catalog environment, defaulting to dev."""
    spark = SparkSession.getActiveSession()
    # Scoped to your project configuration key
    return spark.conf.get("kruger.catalog", "dev")

def get_staging_path(subfolder: str = "filtered_youtube") -> str:
    """Builds a path into this project's staging volume for a given subfolder."""
    catalog = get_catalog()
    return f"/Volumes/{catalog}/kruger/staging/{subfolder}"
