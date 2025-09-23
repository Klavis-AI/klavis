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

async def get_team_by_id(team_id: str) -> Dict[str, Any]:
    """Get a specific team by ID with detailed information including states and members."""
    logger.info(f"Executing tool: get_team_by_id with team_id: {team_id}")
    try:
        query = """
        query Team($id: String!) {
            team(id: $id) {
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
        """
        variables = {"id": team_id}
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool get_team_by_id: {e}")
        raise e 