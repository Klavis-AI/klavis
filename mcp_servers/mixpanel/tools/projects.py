import logging
from typing import Any, Dict, Optional

from .base import MixpanelAppAPIClient

logger = logging.getLogger(__name__)

async def get_projects() -> Dict[str, Any]:
    """Get all projects that are accessible to the current service account user.
    
    This tool retrieves all projects the service account has access to, 
    allowing users to select a project for operations that require a project_id.
    
    Returns:
        Dict containing accessible projects in format: {"project_id": {"id": project_id, "name": "project_name"}}
    """
    try:
        # Use the app API endpoint to get projects
        result = await MixpanelAppAPIClient.make_request(
            "GET",
            "/me"
        )
        
        if isinstance(result, dict):
            # Extract projects information
            projects = {}
            
            # Check if response has results.projects structure
            if "results" in result and "projects" in result.get("results", {}):
                # Handle /me endpoint response where projects is a dict
                projects_dict = result["results"]["projects"]
                for project_id, project in projects_dict.items():
                    projects[project_id] = {
                        "id": int(project_id) if project_id.isdigit() else project_id,
                        "name": project.get("name", "")
                    }
            elif "results" in result and isinstance(result.get("results"), list):
                # Handle paginated list response
                for item in result.get("results", []):
                    pid = str(item.get("id"))
                    projects[pid] = {
                        "id": item.get("id"),
                        "name": item.get("name", "")
                    }
            elif "projects" in result and isinstance(result.get("projects"), list):
                # Handle direct projects list response
                for project in result.get("projects", []):
                    pid = str(project.get("id"))
                    projects[pid] = {
                        "id": project.get("id"),
                        "name": project.get("name", "")
                    }
            elif "projects" in result and isinstance(result.get("projects"), dict):
                # Handle projects as dict response
                projects_dict = result["projects"]
                for project_id, project in projects_dict.items():
                    projects[project_id] = {
                        "id": int(project_id) if project_id.isdigit() else project_id,
                        "name": project.get("name", "")
                    }
            else:
                # Try to extract project info from the response directly
                if result.get("id"):
                    pid = str(result.get("id"))
                    projects[pid] = {
                        "id": result.get("id"),
                        "name": result.get("name", "")
                    }
            
            return projects
        else:
            return {}
            
    except Exception as e:
        logger.exception(f"Error getting projects: {e}")
        return {}


