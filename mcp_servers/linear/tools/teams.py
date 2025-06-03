import logging
from typing import Any, Dict
from .base import make_graphql_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_teams() -> Dict[str, Any]:
    """Get all teams."""
    logger.info("Executing tool: get_teams")
    try:
        query = """
        query Teams {
          teams {
            nodes {
              id
              name
              key
              description
              private
              createdAt
              updatedAt
            }
          }
        }
        """
        return await make_graphql_request(query)
    except Exception as e:
        logger.exception(f"Error executing tool get_teams: {e}")
        raise e 