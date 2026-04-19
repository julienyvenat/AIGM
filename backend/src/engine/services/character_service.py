from typing import Dict, Any

class SchemaValidationError(ValueError):
    pass

def validate_character_stats(stats: Dict[str, Any], schema: Dict[str, Any]) -> None:
    expected_keys = set(schema.keys())
    provided_keys = set(stats.keys())

    if expected_keys != provided_keys:
        missing = expected_keys - provided_keys
        extra = provided_keys - expected_keys
        error_msg = "Invalid character stats."
        if missing:
            error_msg += f" Missing keys: {', '.join(missing)}."
        if extra:
            error_msg += f" Extra keys not allowed: {', '.join(extra)}."
        raise SchemaValidationError(error_msg)
