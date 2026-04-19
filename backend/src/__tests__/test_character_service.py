import pytest
from src.engine.services.character_service import validate_character_stats, SchemaValidationError

def test_validate_character_stats_valid():
    schema = {"STR": "int", "DEX": "int", "HP": "int"}
    stats = {"STR": 10, "DEX": 15, "HP": 20}
    # Should not raise an exception
    validate_character_stats(stats, schema)

def test_validate_character_stats_missing_key():
    schema = {"STR": "int", "DEX": "int", "HP": "int"}
    stats = {"STR": 10, "HP": 20}
    with pytest.raises(SchemaValidationError, match="Missing keys: DEX"):
        validate_character_stats(stats, schema)

def test_validate_character_stats_extra_key():
    schema = {"STR": "int", "DEX": "int", "HP": "int"}
    stats = {"STR": 10, "DEX": 15, "HP": 20, "WIS": 12}
    with pytest.raises(SchemaValidationError, match="Extra keys not allowed: WIS"):
        validate_character_stats(stats, schema)

def test_validate_character_stats_missing_and_extra():
    schema = {"STR": "int", "DEX": "int", "HP": "int"}
    stats = {"STR": 10, "HP": 20, "WIS": 12}
    with pytest.raises(SchemaValidationError) as exc_info:
        validate_character_stats(stats, schema)
    error_msg = str(exc_info.value)
    assert "Missing keys: DEX" in error_msg
    assert "Extra keys not allowed: WIS" in error_msg
