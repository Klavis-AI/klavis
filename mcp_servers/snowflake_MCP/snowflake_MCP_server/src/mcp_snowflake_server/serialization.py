"""
Simple serialization utilities for Snowflake data types.
Handles both JSON and YAML serialization consistently.
"""

from datetime import date
import pandas as pd
from decimal import Decimal
import math
import json
import yaml


def _serialize_value(obj):
    """Convert Snowflake-specific types to serializable values"""
    if isinstance(obj, date):
        return obj.isoformat()
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, float) and math.isnan(obj):
        return None
    else:
        return obj


def json_serializer(obj):
    """JSON serializer for Snowflake types"""
    return _serialize_value(obj)


def _yaml_representer(dumper, data):
    """YAML representer for Snowflake types"""
    serialized = _serialize_value(data)
    
    if serialized is None:
        return dumper.represent_scalar('tag:yaml.org,2002:null', '')
    elif isinstance(serialized, bool):
        return dumper.represent_scalar('tag:yaml.org,2002:bool', str(serialized).lower())
    elif isinstance(serialized, int):
        return dumper.represent_scalar('tag:yaml.org,2002:int', str(serialized))
    elif isinstance(serialized, float):
        return dumper.represent_scalar('tag:yaml.org,2002:float', str(serialized))
    else:
        return dumper.represent_scalar('tag:yaml.org,2002:str', str(serialized))


# Custom YAML dumper
class SnowflakeDumper(yaml.SafeDumper):
    pass


# Register all Snowflake types with YAML
SnowflakeDumper.add_representer(date, _yaml_representer)
SnowflakeDumper.add_representer(pd.Timestamp, _yaml_representer)
SnowflakeDumper.add_representer(Decimal, _yaml_representer)
SnowflakeDumper.add_representer(float, _yaml_representer)


# Public API
def to_yaml(data) -> str:
    """Convert data to YAML with Snowflake type handling"""
    return yaml.dump(data, Dumper=SnowflakeDumper, indent=2, sort_keys=False)


def to_json(data) -> str:
    """Convert data to JSON with Snowflake type handling"""
    return json.dumps(data, default=json_serializer, indent=2)
