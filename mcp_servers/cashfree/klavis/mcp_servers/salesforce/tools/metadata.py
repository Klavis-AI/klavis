import logging
from typing import Any, Dict, List
from .base import get_salesforce_conn

# Configure logging
logger = logging.getLogger(__name__)

async def execute_soql_query(query: str) -> Dict[str, Any]:
    """Execute a SOQL query on Salesforce."""
    logger.info(f"Executing tool: execute_soql_query with query: {query}")
    try:
        sf = get_salesforce_conn()
        result = sf.query(query)
        return dict(result)
    except Exception as e:
        logger.exception(f"Error executing SOQL query: {e}")
        raise e

async def execute_tooling_query(query: str) -> Dict[str, Any]:
    """Execute a query against the Salesforce Tooling API."""
    logger.info(f"Executing tool: execute_tooling_query with query: {query}")
    try:
        sf = get_salesforce_conn()
        result = sf.toolingexecute(f"query/?q={query}")
        return dict(result)
    except Exception as e:
        logger.exception(f"Error executing tooling query: {e}")
        raise e

async def describe_object(object_name: str, detailed: bool = False) -> Dict[str, Any]:
    """Get detailed metadata about a Salesforce object."""
    logger.info(f"Executing tool: describe_object with object_name: {object_name}")
    try:
        sf = get_salesforce_conn()
        sobject = getattr(sf, object_name)
        result = sobject.describe()
        
        if detailed and object_name.endswith('__c'):
            # For custom objects, get additional metadata if requested
            metadata_result = sf.restful(f"sobjects/{object_name}/describe/")
            return {
                "describe": dict(result),
                "metadata": metadata_result
            }
        
        return dict(result)
    except Exception as e:
        logger.exception(f"Error describing object: {e}")
        raise e

async def get_component_source(metadata_type: str, component_names: List[str]) -> Dict[str, Any]:
    """Retrieve metadata components from Salesforce."""
    logger.info(f"Executing tool: get_component_source with type: {metadata_type}")
    try:
        sf = get_salesforce_conn()
        
        # Valid metadata types
        valid_types = [
            'CustomObject', 'Flow', 'FlowDefinition', 'CustomField',
            'ValidationRule', 'ApexClass', 'ApexTrigger', 'WorkflowRule', 'Layout'
        ]
        
        if metadata_type not in valid_types:
            raise ValueError(f"Invalid metadata type: {metadata_type}")
        
        # Use Tooling API for metadata queries
        results = []
        for name in component_names:
            try:
                if metadata_type == 'ApexClass':
                    query = f"SELECT Id, Name, Body FROM ApexClass WHERE Name = '{name}'"
                elif metadata_type == 'ApexTrigger':
                    query = f"SELECT Id, Name, Body FROM ApexTrigger WHERE Name = '{name}'"
                elif metadata_type == 'Flow':
                    query = f"SELECT Id, MasterLabel, Definition FROM Flow WHERE MasterLabel = '{name}'"
                else:
                    # For other types, use general metadata query
                    query = f"SELECT Id, DeveloperName FROM {metadata_type} WHERE DeveloperName = '{name}'"
                
                result = sf.toolingexecute(f"query/?q={query}")
                results.append({
                    "name": name,
                    "type": metadata_type,
                    "data": dict(result)
                })
            except Exception as e:
                results.append({
                    "name": name,
                    "type": metadata_type,
                    "error": str(e)
                })
        
        return {"results": results}
    except Exception as e:
        logger.exception(f"Error retrieving metadata: {e}")
        raise e 