import logging
from typing import Any, Dict
from .base import make_graphql_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_projects(team_id: str = None, limit: int = 50) -> Dict[str, Any]:
    """Get projects, optionally filtered by team."""
    logger.info(f"Executing tool: get_projects with team_id: {team_id}")
    try:
        if team_id:
            query = """
            query TeamProjects($teamId: String!, $first: Int) {
              team(id: $teamId) {
                projects(first: $first) {
                  nodes {
                    id
                    name
                    description
                    state
                    progress
                    targetDate
                    lead {
                      id
                      name
                      email
                    }
                    members {
                      nodes {
                        id
                        name
                        email
                      }
                    }
                    createdAt
                    updatedAt
                    url
                  }
                }
              }
            }
            """
            variables = {"teamId": team_id, "first": limit}
        else:
            query = """
            query Projects($first: Int) {
              projects(first: $first) {
                nodes {
                  id
                  name
                  description
                  state
                  progress
                  targetDate
                  lead {
                    id
                    name
                    email
                  }
                  members {
                    nodes {
                      id
                      name
                      email
                    }
                  }
                  teams {
                    nodes {
                      id
                      name
                      key
                    }
                  }
                  createdAt
                  updatedAt
                  url
                }
              }
            }
            """
            variables = {"first": limit}
        
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool get_projects: {e}")
        raise e

async def create_project(name: str, description: str = None, team_ids: list = None, lead_id: str = None, target_date: str = None) -> Dict[str, Any]:
    """Create a new project."""
    logger.info(f"Executing tool: create_project with name: {name}")
    try:
        query = """
        mutation ProjectCreate($input: ProjectCreateInput!) {
          projectCreate(input: $input) {
            success
            project {
              id
              name
              description
              state
              progress
              targetDate
              lead {
                id
                name
                email
              }
              teams {
                nodes {
                  id
                  name
                  key
                }
              }
              createdAt
              url
            }
          }
        }
        """
        
        input_data = {"name": name}
        
        if description:
            input_data["description"] = description
        if team_ids:
            input_data["teamIds"] = team_ids
        if lead_id:
            input_data["leadId"] = lead_id
        if target_date:
            input_data["targetDate"] = target_date
        
        variables = {"input": input_data}
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool create_project: {e}")
        raise e

async def update_project(project_id: str, name: str = None, description: str = None, state: str = None, target_date: str = None, lead_id: str = None) -> Dict[str, Any]:
    """Update an existing project."""
    logger.info(f"Executing tool: update_project with project_id: {project_id}")
    try:
        query = """
        mutation ProjectUpdate($id: String!, $input: ProjectUpdateInput!) {
          projectUpdate(id: $id, input: $input) {
            success
            project {
              id
              name
              description
              state
              progress
              targetDate
              lead {
                id
                name
                email
              }
              teams {
                nodes {
                  id
                  name
                  key
                }
              }
              updatedAt
              url
            }
          }
        }
        """
        
        input_data = {}
        if name:
            input_data["name"] = name
        if description is not None:
            input_data["description"] = description
        if state:
            input_data["state"] = state
        if target_date:
            input_data["targetDate"] = target_date
        if lead_id:
            input_data["leadId"] = lead_id
        
        variables = {"id": project_id, "input": input_data}
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool update_project: {e}")
        raise e 