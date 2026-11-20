from pyspark import pipelines as dp
from pyspark.sql.functions import col
from utilities.helpers import bronze_table

KRUGER_RULES = {
    "valid_stats": "view_count >= comment_count",
    "valid_title": "title IS NOT NULL"
}

# 1. Cast columns and check rules in a streaming view
@dp.view(name="silver_kruger_clean")
@dp.expect_all(KRUGER_RULES)
def silver_kruger_clean():
    return (
        spark.readStream.table(bronze_table("bronze_kruger_valid"))
        .withColumn("published_at", col("published_at").cast("timestamp"))
        .withColumn("view_count", col("view_count").cast("long"))
        .withColumn("comment_count", col("comment_count").cast("long"))
        .withColumn("like_count", col("like_count").cast("long"))
        .drop("live_broadcast_content", "favorite_count", "_source_file", "is_quarantined")
    )

# 2. Target streaming table
dp.create_streaming_table(
    name="silver_kruger",
    comment="Deduplicated YouTube video statistics (latest metrics per video ID)"
)

# 3. Upsert latest stats by video ID
dp.create_auto_cdc_flow(
    target="silver_kruger",
    source="silver_kruger_clean",
    keys=["id"],
    sequence_by=col("_ingested_at"),
    stored_as_scd_type=1
)
