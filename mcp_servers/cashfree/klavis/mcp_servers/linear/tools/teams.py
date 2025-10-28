import logging
from typing import Any, Dict
from .base import make_graphql_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_teams() -> Dict[str, Any]:
    """Get all teams in the Linear workspace including workflow states and team members."""
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
              states {
                nodes {
                  id
                  name
                  type
                  color
                }
              }
              members {
                nodes {
                  id
                  name
                  displayName
                  email
                }
              }
            }
          }
        }
        """
        return await make_graphql_request(query)
    except Exception as e:
        logger.exception(f"Error executing tool get_teams: {e}")
        raise e 