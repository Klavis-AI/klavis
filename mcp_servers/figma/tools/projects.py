import logging
from typing import Any, Dict, List, Optional
from .base import make_figma_request

# Configure logging
logger = logging.getLogger(__name__)

async def get_team_projects(team_id: str) -> Dict[str, Any]:
    """Get all projects for a team."""
    logger.info(f"Executing tool: get_team_projects with team_id: {team_id}")
    try:
        endpoint = f"/v1/teams/{team_id}/projects"
        
        projects_data = await make_figma_request("GET", endpoint)
        
        result = {
            "projects": []
        }
        
        for project in projects_data.get("projects", []):
            project_info = {
                "id": project.get("id"),
                "name": project.get("name")
            }
            result["projects"].append(project_info)
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_team_projects: {e}")
        return {
            "error": "Failed to retrieve team projects",
            "team_id": team_id,
            "note": "Make sure the team_id is correct and you have access to this team",
            "exception": str(e)
        }

async def get_project_files(project_id: str, branch_data: Optional[bool] = None) -> Dict[str, Any]:
    """Get all files in a project."""
    logger.info(f"Executing tool: get_project_files with project_id: {project_id}")
    try:
        endpoint = f"/v1/projects/{project_id}/files"
        params = {}
        
        if branch_data is not None:
            params["branch_data"] = branch_data
        
        files_data = await make_figma_request("GET", endpoint, params=params)
        
        result = {
            "files": []
        }
        
        for file in files_data.get("files", []):
            file_info = {
                "key": file.get("key"),
                "name": file.get("name"),
                "thumbnail_url": file.get("thumbnail_url"),
                "last_modified": file.get("last_modified"),
                "branches": file.get("branches", [])
            }
            result["files"].append(file_info)
        
        return result
    except Exception as e:
        logger.exception(f"Error executing tool get_project_files: {e}")
        return {
            "error": "Failed to retrieve project files",
            "project_id": project_id,
            "note": "Make sure the project_id is correct and you have access to this project",
            "exception": str(e)
        }