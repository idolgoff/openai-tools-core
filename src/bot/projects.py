"""Project management domain logic for the bot.

This module contains the core business logic for managing projects,
implemented as part of the bot's functionality.

It also registers these functions as tools that can be used with OpenAI's
function calling API.
"""
import uuid
from typing import Dict, List, Optional, Union

from core.tools import ToolRegistry

# Create a tool registry for project management
tool_registry = ToolRegistry()


# In-memory storage for projects
PROJECTS: Dict[str, Dict[str, str]] = {}
ACTIVE_PROJECT_ID: Optional[str] = None


@tool_registry.register()
def list_projects_tool() -> Union[str, None]:
    """List all available projects."""
    if not PROJECTS:
        return None
    
    projects_list = []
    for project_id, project in PROJECTS.items():
        active_marker = " (ACTIVE)" if project_id == ACTIVE_PROJECT_ID else ""
        projects_list.append(f"ID: {project_id}{active_marker}\nName: {project['name']}\nDescription: {project['description']}\n")
    
    return "\n".join(projects_list)


@tool_registry.register()
def delete_project_tool(project_id: str) -> Union[str, None]:
    """Delete a project by ID.
    
    Args:
        project_id: ID of the project to delete
    """
    global ACTIVE_PROJECT_ID
    
    if project_id not in PROJECTS:
        return None
    
    project_name = PROJECTS[project_id]["name"]
    del PROJECTS[project_id]
    
    # Reset active project if it was deleted
    if ACTIVE_PROJECT_ID == project_id:
        ACTIVE_PROJECT_ID = None
    
    return f"Project '{project_name}' (ID: {project_id}) has been deleted"


@tool_registry.register()
def switch_project_tool(project_id: str) -> Union[str, None]:
    """Switch to a project by ID.
    
    Args:
        project_id: ID of the project to switch to
    """
    global ACTIVE_PROJECT_ID
    
    if project_id not in PROJECTS:
        return None
    
    ACTIVE_PROJECT_ID = project_id
    project_name = PROJECTS[project_id]["name"]
    
    return f"Switched to project '{project_name}' (ID: {project_id})"


@tool_registry.register()
def create_project_tool(name: str, description: str) -> str:
    """Create a new project.
    
    Args:
        name: Project name
        description: Project description
    """
    project_id = str(uuid.uuid4())
    PROJECTS[project_id] = {
        "name": name,
        "description": description
    }
    
    return project_id


@tool_registry.register()
def get_project_details_tool(project_id: str) -> Union[Dict[str, str], None]:
    """Get project details by ID.
    
    Args:
        project_id: ID of the project
    """
    if project_id not in PROJECTS:
        return None
    
    return {
        "id": project_id,
        "name": PROJECTS[project_id]["name"],
        "description": PROJECTS[project_id]["description"],
        "is_active": project_id == ACTIVE_PROJECT_ID
    }


@tool_registry.register()
def get_active_project_tool() -> Union[Dict[str, str], None]:
    """Get active project details."""
    if ACTIVE_PROJECT_ID is None:
        return None
    
    if ACTIVE_PROJECT_ID not in PROJECTS:
        return None
        
    project = PROJECTS[ACTIVE_PROJECT_ID]
    return {
        "id": ACTIVE_PROJECT_ID,
        "name": project["name"],
        "description": project["description"],
        "is_active": True
    }


# Helper functions (not exposed as tools)
def list_projects() -> Union[str, None]:
    """List all available projects (internal helper)."""
    return list_projects_tool()

def delete_project(project_id: str) -> Union[str, None]:
    """Delete a project by ID (internal helper)."""
    return delete_project_tool(project_id)

def switch_project(project_id: str) -> Union[str, None]:
    """Switch to a project by ID (internal helper)."""
    return switch_project_tool(project_id)

def create_project(name: str, description: str) -> str:
    """Create a new project (internal helper)."""
    return create_project_tool(name, description)

def get_project_details(project_id: str) -> Union[Dict[str, str], None]:
    """Get project details by ID (internal helper)."""
    return get_project_details_tool(project_id)

def get_active_project() -> Union[Dict[str, str], None]:
    """Get active project details (internal helper)."""
    return get_active_project_tool()


# Export the tools for use in other modules
PROJECT_TOOLS = {
    "list_projects_tool": list_projects_tool,
    "delete_project_tool": delete_project_tool,
    "switch_project_tool": switch_project_tool,
    "create_project_tool": create_project_tool,
    "get_project_details_tool": get_project_details_tool,
    "get_active_project_tool": get_active_project_tool
}

# Export the tool schemas for OpenAI API
def get_project_tool_schemas():
    """Get OpenAI-compatible schemas for all project tools."""
    return tool_registry.get_tool_schemas()
