#!/usr/bin/env python3

"""
MindsDB MCP Server

A Model Context Protocol server for interacting with MindsDB's REST API.
MindsDB is an open-source AI layer that integrates with databases to provide
machine learning capabilities through SQL and REST interfaces.

Built with FastMCP for clean, maintainable code with decorator-based tools.
"""

import asyncio
import json
import logging
import os
from typing import Any, Dict

import httpx
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging from environment
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level))
logger = logging.getLogger("mindsdb-mcp-server")

# Default MindsDB API configuration
DEFAULT_BASE_URL = "http://127.0.0.1:47334/api"

# Initialize FastMCP
mcp = FastMCP("MindsDB MCP Server")


class MindsDBClient:
    """HTTP client for MindsDB API operations."""
    
    def __init__(self, base_url: str = DEFAULT_BASE_URL):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            headers={"Content-Type": "application/json"}
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to MindsDB API."""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            response = await self.client.request(
                method=method,
                url=url,
                json=data if data else None
            )
            response.raise_for_status()
            
            # Handle empty responses
            if not response.content:
                return {"status": "success"}
            
            return response.json()
        
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e.response.text}")
            return {
                "error": f"HTTP {e.response.status_code}",
                "message": e.response.text
            }
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            return {
                "error": "Request failed",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {
                "error": "Unexpected error",
                "message": str(e)
            }


# Initialize MindsDB client
mindsdb_client = MindsDBClient(os.getenv("MINDSDB_BASE_URL", DEFAULT_BASE_URL))


# Database Management Tools
@mcp.tool()
async def list_databases() -> str:
    """
    List all database connections in MindsDB.
    
    Returns information about connected data sources.
    """
    result = await mindsdb_client._make_request("GET", "/databases/")
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def create_database_connection(
    name: str,
    engine: str,
    host: str,
    port: str,
    user: str,
    password: str,
    database: str
) -> str:
    """
    Create a new database connection in MindsDB.
    
    Args:
        name: Name for the database connection
        engine: Database engine type (e.g., postgres, mysql, mongodb)
        host: Database host address
        port: Database port number
        user: Database username
        password: Database password
        database: Database name to connect to
    
    Returns:
        JSON response from MindsDB API
    """
    data = {
        "database": {
            "name": name,
            "engine": engine,
            "parameters": {
                "host": host,
                "port": port,
                "user": user,
                "password": password,
                "database": database
            }
        }
    }
    result = await mindsdb_client._make_request("POST", "/databases/", data)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def delete_database_connection(name: str) -> str:
    """
    Delete a database connection from MindsDB.
    
    Args:
        name: Name of the database connection to delete
    
    Returns:
        JSON response from MindsDB API
    """
    # Use SQL format for database deletion
    sql_query = f"DROP DATABASE {name}"
    data = {"query": sql_query}
    result = await mindsdb_client._make_request("POST", "/sql/query", data)
    return json.dumps(result, indent=2, ensure_ascii=False)


# Model Management Tools
@mcp.tool()
async def list_models() -> str:
    """
    List all AI/ML models in MindsDB with their current status.
    
    Returns information about models and their training status:
    - 'generating': Model is currently training
    - 'complete': Model training finished, ready for predictions  
    - 'error': Model training failed
    """
    result = await mindsdb_client._make_request("GET", "/projects/mindsdb/models")
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def create_model(
    name: str,
    predict: str,
    from_table: str,
    project: str = "mindsdb",
    engine: str = "lightwood"
) -> str:
    """
    Create and train a new AI/ML model in MindsDB.
    
    Note: Model training happens asynchronously. After creation, use get_model_details 
    to check training status before making predictions.
    
    Args:
        name: Name for the new model
        predict: Target column to predict
        from_table: Table to select training data from (can include database prefix like 'db.table')
        project: Project name (optional, defaults to "mindsdb")
        engine: ML engine to use - 'lightwood', 'openai', 'huggingface', or specific engine name (defaults to "lightwood")
    
    Returns:
        JSON response from MindsDB API indicating training has started
    """
    # Use correct MindsDB SQL syntax for model creation
    if project and project != "mindsdb":
        model_name = f"{project}.{name}"
    else:
        model_name = name
    
    # Build proper MindsDB CREATE MODEL syntax with engine specification
    sql_query = f"CREATE MODEL {model_name} FROM (SELECT * FROM {from_table}) PREDICT {predict} USING engine = '{engine}';"
    
    data = {"query": sql_query}
    result = await mindsdb_client._make_request("POST", "/sql/query", data)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def get_model_details(name: str, project: str = "mindsdb") -> str:
    """
    Get detailed information about a specific model in MindsDB, including training status.
    
    Args:
        name: Name of the model to get details for
        project: Project name (optional, defaults to "mindsdb")
    
    Returns:
        JSON response with model status, training progress, accuracy, and other details.
        Status can be: 'generating' (training), 'complete' (ready), 'error' (failed)
    """
    result = await mindsdb_client._make_request("GET", f"/projects/{project}/models/{name}")
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def delete_model(name: str, project: str = "mindsdb") -> str:
    """
    Delete a model from MindsDB.
    
    Args:
        name: Name of the model to delete
        project: Project name (optional, defaults to "mindsdb")
    
    Returns:
        JSON response from MindsDB API
    """
    # Use SQL format for model deletion
    sql_query = f"DROP MODEL {project}.{name}"
    data = {"query": sql_query}
    result = await mindsdb_client._make_request("POST", "/sql/query", data)
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def make_prediction(
    model: str,
    data: Dict[str, Any],
    project: str = "mindsdb"
) -> str:
    """
    Make a prediction using a trained model in MindsDB.
    
    Args:
        model: Name of the model to use for prediction
        data: Input data for prediction as key-value pairs
        project: Project name (optional, defaults to "mindsdb")
    
    Returns:
        JSON response with AI predictions
    """
    # Convert data dict to WHERE clause for SQL query
    where_conditions = []
    for key, value in data.items():
        if isinstance(value, str):
            where_conditions.append(f"{key} = '{value}'")
        else:
            where_conditions.append(f"{key} = {value}")
    
    where_clause = " AND ".join(where_conditions)
    query = f"SELECT * FROM {model} WHERE {where_clause}"
    
    query_data = {"query": query}
    result = await mindsdb_client._make_request("POST", "/sql/query", query_data)
    return json.dumps(result, indent=2, ensure_ascii=False)


# Project Management Tools
@mcp.tool()
async def list_projects() -> str:
    """
    List all projects in MindsDB.
    
    Projects are containers that organize databases, models, and other resources.
    """
    result = await mindsdb_client._make_request("GET", "/projects/")
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def create_project(name: str) -> str:
    """
    Create a new project in MindsDB.
    
    Args:
        name: Name for the new project
    
    Returns:
        JSON response from MindsDB API
    """
    # Use SQL format for project creation
    sql_query = f"CREATE DATABASE {name}"
    data = {"query": sql_query}
    result = await mindsdb_client._make_request("POST", "/sql/query", data)
    return json.dumps(result, indent=2, ensure_ascii=False)


# Knowledge Base Management Tools
@mcp.tool()
async def list_knowledge_bases(project: str = "mindsdb") -> str:
    """
    List all knowledge bases in MindsDB.
    
    Args:
        project: Project name (optional, defaults to "mindsdb")
    
    Returns:
        Information about knowledge bases that store embeddings and enable semantic search
    """
    result = await mindsdb_client._make_request("GET", f"/projects/{project}/knowledge_bases")
    return json.dumps(result, indent=2, ensure_ascii=False)


@mcp.tool()
async def create_knowledge_base(
    name: str,
    model: str = "sentence-transformers/all-MiniLM-L6-v2",
    provider: str = "huggingface",
    project: str = "mindsdb"
) -> str:
    """
    Create a new knowledge base in MindsDB using free embedding models.
    
    Args:
        name: Name for the knowledge base
        model: Embedding model to use (defaults to free Hugging Face model 'sentence-transformers/all-MiniLM-L6-v2')
        provider: Model provider - 'huggingface' for free models, 'openai' for paid (defaults to "huggingface")
        project: Project name (optional, defaults to "mindsdb")
    
    Popular free embedding models:
    - sentence-transformers/all-MiniLM-L6-v2 (fast, good quality)
    - sentence-transformers/all-mpnet-base-v2 (higher quality, slower)
    - sentence-transformers/paraphrase-MiniLM-L6-v2 (paraphrase detection)
    
    Returns:
        JSON response from MindsDB API for RAG capabilities
    """
    # Use SQL approach for knowledge base creation with free embeddings
    if project and project != "mindsdb":
        kb_name = f"{project}.{name}"
    else:
        kb_name = name
    
    # Create knowledge base using SQL with free Hugging Face embeddings
    sql_query = f"""
    CREATE OR REPLACE MODEL {kb_name}
    PREDICT embeddings
    USING 
        engine = 'huggingface',
        model_name = '{model}',
        task = 'feature-extraction';
    """
    
    data = {"query": sql_query.strip()}
    result = await mindsdb_client._make_request("POST", "/sql/query", data)
    
    # If successful, also document that this can be used as a knowledge base
    if "error" not in result:
        result["note"] = f"Knowledge base '{name}' created with free embeddings model '{model}'. Use this model for semantic search and RAG applications."
    
    return json.dumps(result, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    """Run the MindsDB MCP server."""
    try:
        # Use FastMCP's built-in run method which handles event loops properly
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        # Clean up the MindsDB client
        try:
            asyncio.run(mindsdb_client.close())
        except RuntimeError:
            # Event loop might be closed already
            pass