import pytest
from pyspark.sql import Row
from pyspark.sql.functions import col, month

def test_gold_seasonal_routing_logic(spark):
    """Validates that records are separated into appropriate half-year windows based on published_at date."""
    
    # 1. Mock inputs spanning different months (formatted to match casted timestamp strings)
    mock_silver_records = [
        Row(id="vid_jan", published_at="2026-01-15 12:00:00"),
        Row(id="vid_jun", published_at="2026-06-30 23:59:59"),
        Row(id="vid_jul", published_at="2026-07-01 00:00:01"),
        Row(id="vid_dec", published_at="2026-12-25 08:30:00")
    ]
    
    # Create the DataFrame and explicitly cast to timestamp as your Silver layer does
    silver_df = spark.createDataFrame(mock_silver_records).withColumn(
        "published_at", col("published_at").cast("timestamp")
    )
    
    # 2. Apply the exact logic from gold_kruger_jan_to_jun
    h1_df = silver_df.filter((month(col("published_at")) >= 1) & (month(col("published_at")) <= 6))
    h1_results = h1_df.collect()
    h1_ids = [row.id for row in h1_results]
    
    # Verify January and June rows are caught in H1
    assert len(h1_results) == 2
    assert "vid_jan" in h1_ids
    assert "vid_jun" in h1_ids
    assert "vid_jul" not in h1_ids
    
    # 3. Apply the exact logic from gold_kruger_jul_to_dec
    h2_df = silver_df.filter((month(col("published_at")) >= 7) & (month(col("published_at")) <= 12))
    h2_results = h2_df.collect()
    h2_ids = [row.id for row in h2_results]
    
    # Verify July and December rows are caught in H2
    assert len(h2_results) == 2
    assert "vid_jul" in h2_ids
    assert "vid_dec" in h2_ids
    assert "vid_jan" not in h2_ids


def test_gold_empty_input_handling(spark):
    """Ensures empty dataframes don't crash the logic filters."""
    empty_df = spark.createDataFrame([], "id STRING, published_at TIMESTAMP")
    
    h1_filtered = empty_df.filter((month(col("published_at")) >= 1) & (month(col("published_at")) <= 6))
    
    assert h1_filtered.count() == 0
