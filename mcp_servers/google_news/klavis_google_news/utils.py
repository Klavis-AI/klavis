# klavis_google_news/utils.py
from datetime import date, datetime
from typing import Any, Dict


def remove_none_values(d: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in d.items() if v is not None}


def iso8601(value):
    """Return an ISO-8601 string or None."""
    if value is None:
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


# --------------------------------------------------------------------------- #
#  Helper – convert a Pydantic model to an OpenAPI-compatible JSON-Schema     #
# --------------------------------------------------------------------------- #
def schema_from_model(model) -> Dict[str, Any]:
    """Return the `.model_json_schema()` without the top-level `$schema` key."""
    schema: Dict[str, Any] = model.model_json_schema()
    schema.pop("$schema", None)
    return schema
