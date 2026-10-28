from pyspark import pipelines as dp
from pyspark.sql.functions import expr

def quarantine_rule(rules: dict) -> str:
    if not rules:
        raise ValueError("quarantine_rule() requires at least one rule — an empty dict would produce invalid SQL (\"NOT()\").")
    return "NOT({0})".format(" AND ".join(rules.values()))

KRUGER_RULES ={
    "valid_id": "id IS NOT NULL",
    "valid_content": "live_broadcast_content NOT IN ('live')"
}


@dp.table(private=True, partition_cols=["is_quarantined"])
@dp.expect_all(KRUGER_RULES)

def bronze_kruger_quality_check():
    return spark.readStream.table("bronze_kruger").withColumn(
        "is_quarantined", expr(quarantine_rule(KRUGER_RULES))
    )

@dp.table(comment="Table that passed quality check")
def bronze_kruger_valid():
    return spark.readStream.table("bronze_kruger_quality_check").filter("is_quarantined = false")

@dp.table(comment="Table that failed data quality check")
def bronze_kruger_quarantined():
    return spark.readStream.table("bronze_kruger_quality_check").filter("is_quarantined = true")