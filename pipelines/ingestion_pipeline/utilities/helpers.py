from pyspark.sql import SparkSession

def get_catalog() -> str:
    spark = SparkSession.getActiveSession()
    return spark.conf.get("kruger.catalog", "dev")

def get_staging_path(subfolder: str = "filtered_youtube") -> str:
    catalog = get_catalog()
    return f"/Volumes/{catalog}/kruger/staging/{subfolder}"
