import pytest
from pyspark.sql import Row
from pyspark.sql.functions import expr

# --- Inline Logic Copied Directly From Your Notebook Pipeline Scripts ---
def quarantine_rule(rules: dict) -> str:
    if not rules:
        raise ValueError("quarantine_rule() requires at least one rule — an empty dict would produce invalid SQL (\"NOT()\").")
    return "NOT({0})".format(" AND ".join(rules.values()))

KRUGER_RULES = {
    "valid_id": "id IS NOT NULL",
    "valid_content": "live_broadcast_content NOT IN ('live')"
}


# --- Unit Tests ---
def test_quarantine_rule_combines_multiple_rules():
    """Verifies that multiple validation rules are grouped together safely with AND inside the NOT expression."""
    rules = {
        "valid_id": "id IS NOT NULL",
        "valid_content": "live_broadcast_content NOT IN ('live')"
    }
    result = quarantine_rule(rules)
    assert result == "NOT(id IS NOT NULL AND live_broadcast_content NOT IN ('live'))"


def test_quarantine_rule_rejects_empty_dict():
    """Ensures a descriptive ValueError is thrown if an empty rule map is provided."""
    with pytest.raises(ValueError, match="requires at least one rule"):
        quarantine_rule({})



