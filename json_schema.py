"""JSON Schema validation for HAMSTERS task definitions"""

import json
from pathlib import Path


def _load_schema() -> dict:
    """Load schema from hamsters-task.schema.json file"""
    schema_path = Path(__file__).parent / "hamsters-task.schema.json"
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load schema file: {e}")
        return {}


def validate_json_schema(data: dict) -> tuple:
    """
    Validate JSON data against HAMSTERS task schema loaded from hamsters-task.schema.json.
    
    Args:
        data: JSON data to validate
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    try:
        import jsonschema
        from jsonschema import Draft7Validator
        
        # Load schema from file
        schema = _load_schema()
        if not schema:
            # If schema loading failed, skip validation
            return (True, "")
        
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(data))
        
        if not errors:
            return (True, "")
        
        # Collect first 3 errors
        error_messages = []
        for error in errors[:3]:
            path = ".".join(str(p) for p in error.path) if error.path else "root"
            error_messages.append(f"{path}: {error.message}")
        
        return (False, "; ".join(error_messages))
        
    except ImportError:
        # jsonschema not installed, skip validation
        return (True, "")
    except Exception as e:
        return (False, f"Schema validation error: {str(e)}")
