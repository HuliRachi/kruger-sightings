from pyspark.sql import SparkSession


def get_catalog() -> str:
    
    spark = SparkSession.getActiveSession()
    return spark.conf.get("kruger.catalog", "dev")


def bronze_table(name: str) -> str:
    
    return f"{get_catalog()}.kruger.{name}"
