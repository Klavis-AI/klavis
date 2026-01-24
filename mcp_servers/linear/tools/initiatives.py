import logging
from typing import Any, Dict
from .base import make_graphql_request, clean_filter_object

# Configure logging
logger = logging.getLogger(__name__)


async def get_initiatives(limit: int = 50, filter: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get initiatives with optional filtering by timestamps."""
    logger.info(f"Executing tool: get_initiatives with limit: {limit}, filter: {filter}")
    try:
        # Build the filter object
        initiative_filter = {}
        
        # Add timestamp filters if provided (clean empty values first)
        if filter:
            cleaned_filter = clean_filter_object(filter)
            if "updatedAt" in cleaned_filter:
                initiative_filter["updatedAt"] = cleaned_filter["updatedAt"]
            if "createdAt" in cleaned_filter:
                initiative_filter["createdAt"] = cleaned_filter["createdAt"]
            if "name" in cleaned_filter:
                initiative_filter["name"] = cleaned_filter["name"]
            if "status" in cleaned_filter:
                initiative_filter["status"] = cleaned_filter["status"]
        
        # Use filtered query if we have any filters
        if initiative_filter:
            query = """
            query FilteredInitiatives($filter: InitiativeFilter, $first: Int) {
              initiatives(filter: $filter, first: $first) {
                nodes {
                  id
                  name
                  description
                  status
                  targetDate
                  sortOrder
                  color
                  icon
                  slugId
                  creator {
                    id
                    name
                    email
                  }
                  owner {
                    id
                    name
                    email
                  }
                  projects {
                    nodes {
                      id
                      name
                      state
                      progress
                    }
                  }
                  createdAt
                  updatedAt
                  archivedAt
                }
              }
            }
            """
            variables = {"filter": initiative_filter, "first": limit}
        else:
            # No filters, use simple query
            query = """
            query Initiatives($first: Int) {
              initiatives(first: $first) {
                nodes {
                  id
                  name
                  description
                  status
                  targetDate
                  sortOrder
                  color
                  icon
                  slugId
                  creator {
                    id
                    name
                    email
                  }
                  owner {
                    id
                    name
                    email
                  }
                  projects {
                    nodes {
                      id
                      name
                      state
                      progress
                    }
                  }
                  createdAt
                  updatedAt
                  archivedAt
                }
              }
            }
            """
            variables = {"first": limit}
        
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool get_initiatives: {e}")
        raise e


async def get_initiative_by_id(initiative_id: str) -> Dict[str, Any]:
    """Get a specific initiative by its ID."""
    logger.info(f"Executing tool: get_initiative_by_id with initiative_id: {initiative_id}")
    try:
        query = """
        query Initiative($id: String!) {
          initiative(id: $id) {
            id
            name
            description
            status
            targetDate
            sortOrder
            color
            icon
            slugId
            creator {
              id
              name
              email
            }
            owner {
              id
              name
              email
            }
            projects {
              nodes {
                id
                name
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
              }
            }
            createdAt
            updatedAt
            archivedAt
          }
        }
        """
        variables = {"id": initiative_id}
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool get_initiative_by_id: {e}")
        raise e


async def create_initiative(name: str, description: str = None, owner_id: str = None, 
                           target_date: str = None, status: str = None, 
                           color: str = None, icon: str = None) -> Dict[str, Any]:
    """Create a new initiative."""
    logger.info(f"Executing tool: create_initiative with name: {name}")
    try:
        query = """
        mutation InitiativeCreate($input: InitiativeCreateInput!) {
          initiativeCreate(input: $input) {
            success
            initiative {
              id
              name
              description
              status
              targetDate
              sortOrder
              color
              icon
              slugId
              creator {
                id
                name
                email
              }
              owner {
                id
                name
                email
              }
              createdAt
            }
          }
        }
        """
        
        input_data = {"name": name}
        
        if description:
            input_data["description"] = description
        if owner_id:
            input_data["ownerId"] = owner_id
        if target_date:
            input_data["targetDate"] = target_date
        if status:
            input_data["status"] = status
        if color:
            input_data["color"] = color
        if icon:
            input_data["icon"] = icon
        
        variables = {"input": input_data}
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool create_initiative: {e}")
        raise e


async def update_initiative(initiative_id: str, name: str = None, description: str = None,
                           owner_id: str = None, target_date: str = None, 
                           status: str = None, color: str = None, 
                           icon: str = None) -> Dict[str, Any]:
    """Update an existing initiative."""
    logger.info(f"Executing tool: update_initiative with initiative_id: {initiative_id}")
    try:
        query = """
        mutation InitiativeUpdate($id: String!, $input: InitiativeUpdateInput!) {
          initiativeUpdate(id: $id, input: $input) {
            success
            initiative {
              id
              name
              description
              status
              targetDate
              sortOrder
              color
              icon
              slugId
              creator {
                id
                name
                email
              }
              owner {
                id
                name
                email
              }
              projects {
                nodes {
                  id
                  name
                  state
                  progress
                }
              }
              updatedAt
            }
          }
        }
        """
        
        input_data = {}
        if name:
            input_data["name"] = name
        if description is not None:
            input_data["description"] = description
        if owner_id:
            input_data["ownerId"] = owner_id
        if target_date:
            input_data["targetDate"] = target_date
        if status:
            input_data["status"] = status
        if color:
            input_data["color"] = color
        if icon:
            input_data["icon"] = icon
        
        variables = {"id": initiative_id, "input": input_data}
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool update_initiative: {e}")
        raise e


async def add_project_to_initiative(initiative_id: str, project_id: str) -> Dict[str, Any]:
    """Add a project to an initiative."""
    logger.info(f"Executing tool: add_project_to_initiative with initiative_id: {initiative_id}, project_id: {project_id}")
    try:
        query = """
        mutation InitiativeToProjectCreate($input: InitiativeToProjectCreateInput!) {
          initiativeToProjectCreate(input: $input) {
            success
            initiativeToProject {
              id
              initiative {
                id
                name
              }
              project {
                id
                name
                state
                progress
              }
              createdAt
            }
          }
        }
        """
        
        input_data = {
            "initiativeId": initiative_id,
            "projectId": project_id
        }
        
        variables = {"input": input_data}
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool add_project_to_initiative: {e}")
        raise e


async def remove_project_from_initiative(initiative_to_project_id: str) -> Dict[str, Any]:
    """Remove a project from an initiative by deleting the initiative-to-project link."""
    logger.info(f"Executing tool: remove_project_from_initiative with initiative_to_project_id: {initiative_to_project_id}")
    try:
        query = """
        mutation InitiativeToProjectDelete($id: String!) {
          initiativeToProjectDelete(id: $id) {
            success
          }
        }
        """
        
        variables = {"id": initiative_to_project_id}
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool remove_project_from_initiative: {e}")
        raise e
