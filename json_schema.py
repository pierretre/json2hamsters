"""JSON Schema for HAMSTERS task definitions"""

TASK_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "HAMSTERS Task Definition",
    "description": "Schema for validating HAMSTERS task definitions in JSON format",
    "type": "object",
    "properties": {
        "id": {
            "type": "string",
            "description": "Unique task identifier (auto-generated if omitted)",
            "pattern": "^[a-zA-Z0-9_-]+$"
        },
        "label": {
            "type": "string",
            "description": "Task label (required)",
            "minLength": 1,
            "maxLength": 200
        },
        "type": {
            "type": "string",
            "description": "Task type",
            "enum": ["abstract", "goal", "user", "system", "cognitive", "interaction", "cooperative"]
        },
        "description": {
            "type": "string",
            "description": "Task description",
            "maxLength": 1000
        },
        "operator": {
            "type": "string",
            "description": "Temporal operator",
            "enum": ["sequence", "choice", "order-independent", "concurrency", "loop", "optional", "interrupt", "suspend_resume"]
        },
        "duration": {
            "type": "object",
            "description": "Task duration",
            "properties": {
                "min": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1000000
                },
                "max": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1000000
                },
                "unit": {
                    "type": "string",
                    "enum": ["ms", "s", "min", "h"]
                }
            },
            "additionalProperties": False
        },
        "loop": {
            "type": "object",
            "description": "Loop configuration",
            "properties": {
                "minIterations": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 10000
                },
                "maxIterations": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 10000
                }
            },
            "additionalProperties": False
        },
        "optional": {
            "type": "boolean",
            "description": "Whether the task is optional"
        },
        "children": {
            "type": "array",
            "description": "Child tasks",
            "items": {
                "$ref": "#"
            },
            "maxItems": 100
        },
        "metadata": {
            "type": "object",
            "description": "Additional metadata",
            "additionalProperties": True,
            "maxProperties": 50
        }
    },
    "required": ["label"],
    "additionalProperties": False
}


def validate_json_schema(data: dict) -> tuple:
    """
    Validate JSON data against HAMSTERS task schema.
    
    Args:
        data: JSON data to validate
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    try:
        import jsonschema
        from jsonschema import Draft7Validator
        
        validator = Draft7Validator(TASK_SCHEMA)
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
