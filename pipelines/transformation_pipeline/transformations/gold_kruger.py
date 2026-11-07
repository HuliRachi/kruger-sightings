import dlt as dp
from pyspark.sql.functions import col, month

@dp.materialized_view(
    name="gold_kruger_jan_to_jun",
    comment="Pre-computed behavioral metrics for events published in the first half of the year (January - June)."
)
def gold_kruger_jan_to_jun():
    return (
        dp.read("silver_kruger")
        .filter((month(col("published_at")) >= 1) & (month(col("published_at")) <= 6))
    )

@dp.materialized_view(
    name="gold_kruger_jul_to_dec",
    comment="Pre-computed behavioral metrics for events published in the second half of the year (July - December)."
)
def gold_kruger_jul_to_dec():
    return (
        dp.read("silver_kruger")
        .filter((month(col("published_at")) >= 7) & (month(col("published_at")) <= 12))
    )
