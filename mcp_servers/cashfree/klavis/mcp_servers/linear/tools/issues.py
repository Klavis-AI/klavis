import logging
from typing import Any, Dict
from .base import make_graphql_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_issues(team_id: str = None, limit: int = 50, filter: Dict[str, Any] = None) -> Dict[str, Any]:
    """Get issues with optional filtering by team and timestamps."""
    logger.info(f"Executing tool: get_issues with team_id: {team_id}, limit: {limit}, filter: {filter}")
    try:
        # Build the filter object
        issue_filter = {}
        
        # Add team filter if specified
        if team_id:
            issue_filter["team"] = {"id": {"eq": team_id}}
        
        # Add timestamp filters if provided
        if filter:
            if "updatedAt" in filter:
                issue_filter["updatedAt"] = filter["updatedAt"]
            if "createdAt" in filter:
                issue_filter["createdAt"] = filter["createdAt"]
            if "priority" in filter:
                issue_filter["priority"] = {"eq": filter["priority"]}
        
        # Use filtered query if we have any filters
        if issue_filter:
            query = """
            query FilteredIssues($filter: IssueFilter, $first: Int) {
              issues(filter: $filter, first: $first) {
                nodes {
                  id
                  identifier
                  title
                  description
                  priority
                  state {
                    id
                    name
                    type
                  }
                  assignee {
                    id
                    name
                    email
                  }
                  creator {
                    id
                    name
                    email
                  }
                  team {
                    id
                    name
                    key
                  }
                  project {
                    id
                    name
                  }
                  createdAt
                  updatedAt
                  url
                }
              }
            }
            """
            variables = {"filter": issue_filter, "first": limit}
        else:
            # No filters, use simple query
            query = """
            query Issues($first: Int) {
              issues(first: $first) {
                nodes {
                  id
                  identifier
                  title
                  description
                  priority
                  state {
                    id
                    name
                    type
                  }
                  assignee {
                    id
                    name
                    email
                  }
                  creator {
                    id
                    name
                    email
                  }
                  team {
                    id
                    name
                    key
                  }
                  project {
                    id
                    name
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
        logger.exception(f"Error executing tool get_issues: {e}")
        raise e

async def get_issue_by_id(issue_id: str) -> Dict[str, Any]:
    """Get a specific issue by ID."""
    logger.info(f"Executing tool: get_issue_by_id with issue_id: {issue_id}")
    try:
        query = """
        query Issue($id: String!) {
          issue(id: $id) {
            id
            identifier
            title
            description
            priority
            priorityLabel
            state {
              id
              name
              type
            }
            assignee {
              id
              name
              email
            }
            creator {
              id
              name
              email
            }
            team {
              id
              name
              key
            }
            project {
              id
              name
            }
            comments {
              nodes {
                id
                body
                user {
                  id
                  name
                }
                createdAt
                updatedAt
              }
            }
            createdAt
            updatedAt
            url
          }
        }
        """
        variables = {"id": issue_id}
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool get_issue_by_id: {e}")
        raise e

async def create_issue(team_id: str, title: str, description: str = None, assignee_id: str = None, priority: int = None, state_id: str = None, project_id: str = None) -> Dict[str, Any]:
    """Create a new issue."""
    logger.info(f"Executing tool: create_issue with title: {title}")
    try:
        query = """
        mutation IssueCreate($input: IssueCreateInput!) {
          issueCreate(input: $input) {
            success
            issue {
              id
              identifier
              title
              description
              priority
              priorityLabel
              state {
                id
                name
                type
              }
              assignee {
                id
                name
                email
              }
              team {
                id
                name
                key
              }
              project {
                id
                name
              }
              createdAt
              url
            }
          }
        }
        """
        
        input_data = {
            "teamId": team_id,
            "title": title
        }
        
        if description:
            input_data["description"] = description
        if assignee_id:
            input_data["assigneeId"] = assignee_id
        if priority is not None:
            input_data["priority"] = priority
        if state_id:
            input_data["stateId"] = state_id
        if project_id:
            input_data["projectId"] = project_id
        
        variables = {"input": input_data}
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool create_issue: {e}")
        raise e

async def update_issue(issue_id: str, title: str = None, description: str = None, assignee_id: str = None, priority: int = None, state_id: str = None, project_id: str = None) -> Dict[str, Any]:
    """Update an existing issue."""
    logger.info(f"Executing tool: update_issue with issue_id: {issue_id}")
    try:
        query = """
        mutation IssueUpdate($id: String!, $input: IssueUpdateInput!) {
          issueUpdate(id: $id, input: $input) {
            success
            issue {
              id
              identifier
              title
              description
              priority
              priorityLabel
              state {
                id
                name
                type
              }
              assignee {
                id
                name
                email
              }
              team {
                id
                name
                key
              }
              project {
                id
                name
              }
              updatedAt
              url
            }
          }
        }
        """
        
        input_data = {}
        if title:
            input_data["title"] = title
        if description is not None:
            input_data["description"] = description
        if assignee_id:
            input_data["assigneeId"] = assignee_id
        if priority is not None:
            input_data["priority"] = priority
        if state_id:
            input_data["stateId"] = state_id
        if project_id:
            input_data["projectId"] = project_id
        
        variables = {"id": issue_id, "input": input_data}
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool update_issue: {e}")
        raise e

async def search_issues(query_text: str, team_id: str = None, limit: int = 20) -> Dict[str, Any]:
    """Search for issues by text."""
    logger.info(f"Executing tool: search_issues with query: {query_text}")
    try:
        if team_id:
            query = """
            query SearchIssues($filter: IssueFilter, $first: Int) {
              issues(filter: $filter, first: $first) {
                nodes {
                  id
                  identifier
                  title
                  description
                  priority
                  state {
                    id
                    name
                    type
                  }
                  assignee {
                    id
                    name
                    email
                  }
                  team {
                    id
                    name
                    key
                  }
                  project {
                    id
                    name
                  }
                  createdAt
                  updatedAt
                  url
                }
              }
            }
            """
            variables = {
                "filter": {
                    "team": {"id": {"eq": team_id}},
                    "title": {"containsIgnoreCase": query_text}
                },
                "first": limit
            }
        else:
            query = """
            query SearchIssues($filter: IssueFilter, $first: Int) {
              issues(filter: $filter, first: $first) {
                nodes {
                  id
                  identifier
                  title
                  description
                  priority
                  state {
                    id
                    name
                    type
                  }
                  assignee {
                    id
                    name
                    email
                  }
                  team {
                    id
                    name
                    key
                  }
                  project {
                    id
                    name
                  }
                  createdAt
                  updatedAt
                  url
                }
              }
            }
            """
            variables = {
                "filter": {
                    "title": {"containsIgnoreCase": query_text}
                },
                "first": limit
            }
        
        return await make_graphql_request(query, variables)
    except Exception as e:
        logger.exception(f"Error executing tool search_issues: {e}")
        raise e 