import logging
from typing import Any, Dict, Optional

from .base import MixpanelAppAPIClient

logger = logging.getLogger(__name__)

async def get_projects() -> Dict[str, Any]:
    """Get all projects that are accessible to the current service account user.
    
    This tool retrieves all projects the service account has access to, 
    allowing users to select a project for operations that require a project_id.
    
    Returns:
        Dict containing list of accessible projects with their details
    """
    try:
        # Use the app API endpoint to get projects
        result = await MixpanelAppAPIClient.make_request(
            "GET",
            "/me"
        )
        
        if isinstance(result, dict):
            # Extract projects information
            projects = []
            if "results" in result:
                # Handle paginated response
                for item in result.get("results", []):
                    projects.append({
                        "project_id": item.get("id"),
                        "name": item.get("name"),
                        "timezone": item.get("timezone"),
                        "created": item.get("created"),
                        "organization_id": item.get("organization_id"),
                        "organization_name": item.get("organization_name"),
                    })
            elif "projects" in result:
                # Handle direct projects response
                for project in result.get("projects", []):
                    projects.append({
                        "project_id": project.get("id"),
                        "name": project.get("name"),
                        "timezone": project.get("timezone"),
                        "created": project.get("created"),
                        "organization_id": project.get("organization_id"),
                        "organization_name": project.get("organization_name"),
                    })
            else:
                # Try to extract project info from the response directly
                if result.get("id"):
                    projects.append({
                        "project_id": result.get("id"),
                        "name": result.get("name"),
                        "timezone": result.get("timezone"),
                        "created": result.get("created"),
                        "organization_id": result.get("organization_id"),
                        "organization_name": result.get("organization_name"),
                    })
            
            return {
                "success": True,
                "projects": projects,
                "total_projects": len(projects),
                "message": f"Found {len(projects)} accessible projects",
                "raw_response": result
            }
        else:
            return {
                "success": False,
                "projects": [],
                "error": f"Unexpected response format: {result}"
            }
            
    except Exception as e:
        logger.exception(f"Error getting projects: {e}")
        return {
            "success": False,
            "projects": [],
            "error": f"Failed to get projects: {str(e)}"
        }

async def get_project_info(
    project_id: str
) -> Dict[str, Any]:
    """Get detailed information about a specific project.
    
    This tool retrieves detailed information about a specific project including 
    workspaces and other metadata that are accessible to the current user.
    
    Args:
        project_id: The Mixpanel project ID to get information for
        
    Returns:
        Dict containing detailed project information
    """
    try:
        if not project_id:
            raise ValueError("project_id is required")
        
        # Use the app API endpoint to get specific project info
        result = await MixpanelAppAPIClient.make_request(
            "GET",
            f"/projects/{project_id}"
        )
        
        if isinstance(result, dict):
            # Extract detailed project information
            project_info = {
                "project_id": result.get("id", project_id),
                "name": result.get("name"),
                "timezone": result.get("timezone"),
                "created": result.get("created"),
                "organization_id": result.get("organization_id"),
                "organization_name": result.get("organization_name"),
                "token": result.get("token"),  # Project token if available
                "api_secret": result.get("api_secret"),  # API secret if available
                "data_retention_days": result.get("data_retention_days"),
                "workspaces": result.get("workspaces", []),
                "features": result.get("features", {}),
                "settings": result.get("settings", {}),
            }
            
            # Clean up None values
            project_info = {k: v for k, v in project_info.items() if v is not None}
            
            return {
                "success": True,
                "project": project_info,
                "message": f"Retrieved information for project: {project_info.get('name', project_id)}",
                "raw_response": result
            }
        else:
            return {
                "success": False,
                "project": None,
                "error": f"Unexpected response format: {result}"
            }
            
    except Exception as e:
        logger.exception(f"Error getting project info: {e}")
        return {
            "success": False,
            "project": None,
            "error": f"Failed to get project info: {str(e)}"
        }
