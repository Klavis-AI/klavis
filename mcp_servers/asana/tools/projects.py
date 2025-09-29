from typing import Annotated, Any, Dict
import logging
from datetime import datetime, timezone

from .constants import PROJECT_OPT_FIELDS
from .base import (
    get_asana_client,
    get_next_page,
    get_unique_workspace_id_or_raise_error,
    remove_none_values,
    AsanaToolExecutionError,
)

logger = logging.getLogger(__name__)


def parse_timestamp(timestamp_str: str) -> datetime:
    """Parse ISO 8601 timestamp string to datetime object. Always returns timezone-aware datetime."""
    try:
        # Handle both with and without timezone info
        if timestamp_str.endswith('Z'):
            timestamp_str = timestamp_str[:-1] + '+00:00'
        
        dt = datetime.fromisoformat(timestamp_str)
        
        # If the datetime is naive (no timezone), assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return dt
    except (ValueError, AttributeError):
        return None


def filter_projects_by_timestamps(projects: list, filter_dict: Dict[str, Any]) -> list:
    """Filter projects based on timestamp criteria."""
    if not filter_dict:
        return projects
    
    filtered_projects = []
    
    for project in projects:
        include_project = True
        
        # Filter by created_at
        if "created_at" in filter_dict:
            project_created = parse_timestamp(project.get("created_at", ""))
            if project_created:
                created_filter = filter_dict["created_at"]
                
                # Support both gt (greater than) and gte (greater than or equal)
                if "gt" in created_filter:
                    filter_date = parse_timestamp(created_filter["gt"])
                    if filter_date and project_created <= filter_date:
                        include_project = False
                elif "gte" in created_filter:
                    filter_date = parse_timestamp(created_filter["gte"])
                    if filter_date and project_created < filter_date:
                        include_project = False
                
                # Support both lt (less than) and lte (less than or equal)
                if "lt" in created_filter:
                    filter_date = parse_timestamp(created_filter["lt"])
                    if filter_date and project_created >= filter_date:
                        include_project = False
                elif "lte" in created_filter:
                    filter_date = parse_timestamp(created_filter["lte"])
                    if filter_date and project_created > filter_date:
                        include_project = False
        
        # Filter by modified_at
        if include_project and "modified_at" in filter_dict:
            project_modified = parse_timestamp(project.get("modified_at", ""))
            if project_modified:
                modified_filter = filter_dict["modified_at"]
                
                # Support both gt (greater than) and gte (greater than or equal)
                if "gt" in modified_filter:
                    filter_date = parse_timestamp(modified_filter["gt"])
                    if filter_date and project_modified <= filter_date:
                        include_project = False
                elif "gte" in modified_filter:
                    filter_date = parse_timestamp(modified_filter["gte"])
                    if filter_date and project_modified < filter_date:
                        include_project = False
                
                # Support both lt (less than) and lte (less than or equal)
                if "lt" in modified_filter:
                    filter_date = parse_timestamp(modified_filter["lt"])
                    if filter_date and project_modified >= filter_date:
                        include_project = False
                elif "lte" in modified_filter:
                    filter_date = parse_timestamp(modified_filter["lte"])
                    if filter_date and project_modified > filter_date:
                        include_project = False
        
        if include_project:
            filtered_projects.append(project)
    
    return filtered_projects


async def get_project_by_id(
    project_id: str,
) -> Dict[str, Any]:
    """Get a project by its ID"""
    try:
        client = get_asana_client()
        response = await client.get(
            f"/projects/{project_id}",
            params={"opt_fields": ",".join(PROJECT_OPT_FIELDS)},
        )
        return {"project": response["data"]}

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing get_project_by_id: {e}")
        raise e


async def list_projects(
    team_id: str | None = None,
    workspace_id: str | None = None,
    limit: int = 100,
    next_page_token: str | None = None,
    filter: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """List projects in Asana with optional filtering by timestamps.
    
    Args:
        team_id: Optional team ID to filter projects
        workspace_id: Optional workspace ID (defaults to unique workspace if not provided)
        limit: Maximum number of projects to return (1-100)
        next_page_token: Token for pagination
        filter: Optional filter dictionary with timestamp filters:
            - created_at: Filter by creation date with gt/gte/lt/lte operators
            - modified_at: Filter by modification date with gt/gte/lt/lte operators
            Example: {"modified_at": {"gte": "2024-01-01T00:00:00Z"}}
    
    Returns:
        Dictionary containing filtered projects, count, and pagination info
    """
    try:
        # Note: Asana recommends filtering by team to avoid timeout in large domains.
        # Ref: https://developers.asana.com/reference/getprojects
        limit = max(1, min(100, limit))

        workspace_id = workspace_id or await get_unique_workspace_id_or_raise_error()

        client = get_asana_client()

        # If filtering is requested and pagination is involved, we need to fetch more data
        # to ensure we have enough filtered results
        fetch_limit = limit if not filter else min(100, limit * 3)

        response = await client.get(
            "/projects",
            params=remove_none_values({
                "limit": fetch_limit,
                "offset": next_page_token,
                "team": team_id,
                "workspace": workspace_id,
                "opt_fields": ",".join(PROJECT_OPT_FIELDS),
            }),
        )

        projects = response["data"]
        
        # Apply client-side filtering if filter is provided
        if filter:
            projects = filter_projects_by_timestamps(projects, filter)
            # Trim to requested limit after filtering
            projects = projects[:limit]
        
        return {
            "projects": projects,
            "count": len(projects),
            "next_page": get_next_page(response) if not filter else None,  # Pagination is complex with filtering
        }

    except AsanaToolExecutionError as e:
        logger.error(f"Asana API error: {e}")
        raise RuntimeError(f"Asana API Error: {e}")
    except Exception as e:
        logger.exception(f"Error executing list_projects: {e}")
        raise e
