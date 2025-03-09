"""Mocked AI tools implementation."""
from typing import Dict, List, Optional, Union
import uuid

from core.logger import log_tool_execution

# In-memory storage for projects
PROJECTS: Dict[str, Dict[str, str]] = {}
ACTIVE_PROJECT_ID: Optional[str] = None


def list_projects() -> Union[str, None]:
    """
    List all available projects.
    
    Returns:
        Formatted string with project list or None if no projects
    """
    log_tool_execution("list_projects", {}, str(PROJECTS) if PROJECTS else None)
    
    if not PROJECTS:
        return None
    
    projects_list = []
    for project_id, project in PROJECTS.items():
        active_marker = " (ACTIVE)" if project_id == ACTIVE_PROJECT_ID else ""
        projects_list.append(f"ID: {project_id}{active_marker}\nName: {project['name']}\nDescription: {project['description']}\n")
    
    return "\n".join(projects_list)


def delete_project(project_id: str) -> Union[str, None]:
    """
    Delete a project by ID.
    
    Args:
        project_id: ID of the project to delete
        
    Returns:
        Success message or None if project not found
    """
    global ACTIVE_PROJECT_ID
    
    log_tool_execution("delete_project", {"project_id": project_id}, f"Deleting project {project_id}")
    
    if project_id not in PROJECTS:
        return None
    
    project_name = PROJECTS[project_id]["name"]
    del PROJECTS[project_id]
    
    # Reset active project if it was deleted
    if ACTIVE_PROJECT_ID == project_id:
        ACTIVE_PROJECT_ID = None
    
    return f"Project '{project_name}' (ID: {project_id}) has been deleted"


def switch_project(project_id: str) -> Union[str, None]:
    """
    Switch to a project by ID.
    
    Args:
        project_id: ID of the project to switch to
        
    Returns:
        Success message or None if project not found
    """
    global ACTIVE_PROJECT_ID
    
    log_tool_execution("switch_project", {"project_id": project_id}, f"Switching to project {project_id}")
    
    if project_id not in PROJECTS:
        return None
    
    ACTIVE_PROJECT_ID = project_id
    project_name = PROJECTS[project_id]["name"]
    
    return f"Switched to project '{project_name}' (ID: {project_id})"


def create_project(name: str, description: str) -> str:
    """
    Create a new project.
    
    Args:
        name: Project name
        description: Project description
        
    Returns:
        ID of the created project
    """
    project_id = str(uuid.uuid4())
    PROJECTS[project_id] = {
        "name": name,
        "description": description
    }
    
    log_tool_execution(
        "create_project", 
        {"name": name, "description": description}, 
        f"Created project {project_id}"
    )
    
    return project_id


def get_project_details(project_id: str) -> Union[Dict[str, str], None]:
    """
    Get project details by ID.
    
    Args:
        project_id: ID of the project
        
    Returns:
        Project details or None if project not found
    """
    log_tool_execution("get_project_details", {"project_id": project_id}, f"Getting details for project {project_id}")
    
    if project_id not in PROJECTS:
        return None
    
    return {
        "id": project_id,
        "name": PROJECTS[project_id]["name"],
        "description": PROJECTS[project_id]["description"],
        "is_active": project_id == ACTIVE_PROJECT_ID
    }


def get_active_project() -> Union[Dict[str, str], None]:
    """
    Get active project details.
    
    Returns:
        Active project details or None if no active project
    """
    log_tool_execution("get_active_project", {}, f"Getting active project {ACTIVE_PROJECT_ID}")
    
    if ACTIVE_PROJECT_ID is None:
        return None
    
    return get_project_details(ACTIVE_PROJECT_ID)


# Dictionary mapping tool names to their functions for easy access
TOOLS = {
    "list_projects": list_projects,
    "delete_project": delete_project,
    "switch_project": switch_project,
    "create_project": create_project,
    "get_project_details": get_project_details,
    "get_active_project": get_active_project
}
