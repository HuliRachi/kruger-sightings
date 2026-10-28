from pyspark import pipelines as dp  # <-- Matches your company standard perfectly!
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType

from utilities.helpers import get_staging_path, get_catalog

# 1. Your clean explicit schema matching staging JSON output
KRUGER_SCHEMA = StructType([
    StructField("title", StringType(), True),
    StructField("id", StringType(), True),
    StructField("published_at", StringType(), True),
    StructField("live_broadcast_content", StringType(), True),
    StructField("view_count", StringType(), True),
    StructField("comment_count", StringType(), True),
    StructField("favorite_count", StringType(), True),
    StructField("like_count", StringType(), True)
])

def _read_file_bronze(subfolder: str, schema: StructType):
    """Shared Auto Loader read for YouTube tracking."""
    return (
        spark.readStream.format("cloudFiles")
            .option("cloudFiles.format", "json")
            .schema(schema)
            .load(get_staging_path(subfolder))
            .withColumn("_ingested_at", F.current_timestamp())
            .withColumn("_source_file", F.col("_metadata.file_path"))
    )

# 2. Use the new @dp.table decorator
@dp.table(
    name="bronze_kruger",
    comment="Raw video statistics append-only table from YouTube staging area"
)
def bronze_kruger():
    # Automatically skips _SUCCESS logs, reads part-0000 files from your staging folder
    return _read_file_bronze("filtered_youtube", KRUGER_SCHEMA)