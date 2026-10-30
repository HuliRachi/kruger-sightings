from pyspark import pipelines as dp
from pyspark.sql.functions import col

from utilities.helpers import bronze_table

KRUGER_RULES ={
    "valid_stats": "view_count > comment_count",
    "valid_title": "title IS NOT NULL", 
}

@dp.table(
    name="silver_kruger",
    comment="SCD Type 2 animals history"
)

@dp.expect_all(KRUGER_RULES)
def silver_kruger():
    return (
        spark.readStream.table(bronze_table("bronze_kruger_valid"))
        .withColumn("published_at", col("published_at").cast("timestamp"))
        .withColumn("view_count", col("view_count").cast("long"))
        .withColumn("comment_count", col("comment_count").cast("long"))
        .withColumn("like_count", col("like_count").cast("long"))
        .drop("live_broadcast_content", "favorite_count", "_source_file", "is_quarantined", "_ingested_at")
    )

