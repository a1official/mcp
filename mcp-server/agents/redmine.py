"""
Redmine Agent - Project Management Integration
Provides tools for managing Redmine issues, projects, and tasks
"""

import os
import json
import httpx
from typing import Optional

# Redmine configuration
REDMINE_URL = os.getenv("REDMINE_URL", "")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY", "")


def register_redmine_tools(mcp):
    """Register all Redmine-related tools with the MCP server"""
    
    @mcp.tool()
    async def redmine_list_projects() -> str:
        """
        List all Redmine projects you have access to.
        
        Returns:
            JSON with list of projects
        """
        if not REDMINE_URL or not REDMINE_API_KEY:
            return json.dumps({
                "success": False,
                "error": "Redmine URL or API key not configured. Set REDMINE_URL and REDMINE_API_KEY environment variables."
            })
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{REDMINE_URL}/projects.json",
                    headers={"X-Redmine-API-Key": REDMINE_API_KEY},
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                projects = []
                for project in data.get("projects", []):
                    projects.append({
                        "id": project.get("id"),
                        "name": project.get("name"),
                        "identifier": project.get("identifier"),
                        "description": project.get("description"),
                        "status": project.get("status")
                    })
                
                return json.dumps({
                    "success": True,
                    "count": len(projects),
                    "projects": projects
                }, indent=2)
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })

    @mcp.tool()
    async def redmine_list_issues(project_id: Optional[str] = None, status: str = "open", limit: int = 25) -> str:
        """
        List Redmine issues with optional filtering.
        
        Args:
            project_id: Project ID or identifier (optional, shows all projects if not specified)
            status: Issue status - 'open', 'closed', or 'all' (default: 'open')
            limit: Maximum number of issues to return (default: 25)
        
        Returns:
            JSON with list of issues
        """
        if not REDMINE_URL or not REDMINE_API_KEY:
            return json.dumps({
                "success": False,
                "error": "Redmine URL or API key not configured."
            })
        
        params = {
            "limit": limit,
            "status_id": "open" if status == "open" else ("closed" if status == "closed" else "*")
        }
        
        if project_id:
            params["project_id"] = project_id
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{REDMINE_URL}/issues.json",
                    headers={"X-Redmine-API-Key": REDMINE_API_KEY},
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                issues = []
                for issue in data.get("issues", []):
                    issues.append({
                        "id": issue.get("id"),
                        "subject": issue.get("subject"),
                        "description": issue.get("description"),
                        "status": issue.get("status", {}).get("name"),
                        "priority": issue.get("priority", {}).get("name"),
                        "assigned_to": issue.get("assigned_to", {}).get("name"),
                        "author": issue.get("author", {}).get("name"),
                        "project": issue.get("project", {}).get("name"),
                        "created_on": issue.get("created_on"),
                        "updated_on": issue.get("updated_on")
                    })
                
                return json.dumps({
                    "success": True,
                    "count": len(issues),
                    "total_count": data.get("total_count"),
                    "issues": issues
                }, indent=2)
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })

    @mcp.tool()
    async def redmine_get_issue(issue_id: int) -> str:
        """
        Get detailed information about a specific Redmine issue.
        
        Args:
            issue_id: The issue ID number
        
        Returns:
            JSON with detailed issue information
        """
        if not REDMINE_URL or not REDMINE_API_KEY:
            return json.dumps({
                "success": False,
                "error": "Redmine URL or API key not configured."
            })
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{REDMINE_URL}/issues/{issue_id}.json",
                    headers={"X-Redmine-API-Key": REDMINE_API_KEY},
                    params={"include": "journals,attachments"},
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                issue = data.get("issue", {})
                
                return json.dumps({
                    "success": True,
                    "issue": {
                        "id": issue.get("id"),
                        "subject": issue.get("subject"),
                        "description": issue.get("description"),
                        "status": issue.get("status", {}).get("name"),
                        "priority": issue.get("priority", {}).get("name"),
                        "tracker": issue.get("tracker", {}).get("name"),
                        "assigned_to": issue.get("assigned_to", {}).get("name"),
                        "author": issue.get("author", {}).get("name"),
                        "project": issue.get("project", {}).get("name"),
                        "created_on": issue.get("created_on"),
                        "updated_on": issue.get("updated_on"),
                        "done_ratio": issue.get("done_ratio"),
                        "estimated_hours": issue.get("estimated_hours"),
                        "spent_hours": issue.get("spent_hours")
                    }
                }, indent=2)
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })

    @mcp.tool()
    async def redmine_create_issue(
        project_id: str,
        subject: str,
        description: str = "",
        priority_id: int = 2,
        tracker_id: int = 1,
        assigned_to_id: Optional[int] = None
    ) -> str:
        """
        Create a new Redmine issue.
        
        Args:
            project_id: Project ID or identifier
            subject: Issue subject/title
            description: Issue description (optional)
            priority_id: Priority ID (1=Low, 2=Normal, 3=High, 4=Urgent, 5=Immediate, default: 2)
            tracker_id: Tracker ID (1=Bug, 2=Feature, 3=Support, default: 1)
            assigned_to_id: User ID to assign the issue to (optional)
        
        Returns:
            JSON with created issue information
        """
        if not REDMINE_URL or not REDMINE_API_KEY:
            return json.dumps({
                "success": False,
                "error": "Redmine URL or API key not configured."
            })
        
        issue_data = {
            "issue": {
                "project_id": project_id,
                "subject": subject,
                "description": description,
                "priority_id": priority_id,
                "tracker_id": tracker_id
            }
        }
        
        if assigned_to_id:
            issue_data["issue"]["assigned_to_id"] = assigned_to_id
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{REDMINE_URL}/issues.json",
                    headers={
                        "X-Redmine-API-Key": REDMINE_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json=issue_data,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                issue = data.get("issue", {})
                
                return json.dumps({
                    "success": True,
                    "message": f"Issue #{issue.get('id')} created successfully",
                    "issue": {
                        "id": issue.get("id"),
                        "subject": issue.get("subject"),
                        "project": issue.get("project", {}).get("name"),
                        "status": issue.get("status", {}).get("name")
                    }
                }, indent=2)
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })

    @mcp.tool()
    async def redmine_update_issue(
        issue_id: int,
        subject: Optional[str] = None,
        description: Optional[str] = None,
        status_id: Optional[int] = None,
        priority_id: Optional[int] = None,
        assigned_to_id: Optional[int] = None,
        done_ratio: Optional[int] = None,
        notes: Optional[str] = None
    ) -> str:
        """
        Update an existing Redmine issue.
        
        Args:
            issue_id: The issue ID to update
            subject: New subject (optional)
            description: New description (optional)
            status_id: New status ID (1=New, 2=In Progress, 3=Resolved, 5=Closed, optional)
            priority_id: New priority ID (1=Low, 2=Normal, 3=High, 4=Urgent, 5=Immediate, optional)
            assigned_to_id: New assignee user ID (optional)
            done_ratio: Completion percentage 0-100 (optional)
            notes: Comment/note to add to the issue (optional)
        
        Returns:
            JSON with update status
        """
        if not REDMINE_URL or not REDMINE_API_KEY:
            return json.dumps({
                "success": False,
                "error": "Redmine URL or API key not configured."
            })
        
        issue_data = {"issue": {}}
        
        if subject:
            issue_data["issue"]["subject"] = subject
        if description:
            issue_data["issue"]["description"] = description
        if status_id:
            issue_data["issue"]["status_id"] = status_id
        if priority_id:
            issue_data["issue"]["priority_id"] = priority_id
        if assigned_to_id:
            issue_data["issue"]["assigned_to_id"] = assigned_to_id
        if done_ratio is not None:
            issue_data["issue"]["done_ratio"] = done_ratio
        if notes:
            issue_data["issue"]["notes"] = notes
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(
                    f"{REDMINE_URL}/issues/{issue_id}.json",
                    headers={
                        "X-Redmine-API-Key": REDMINE_API_KEY,
                        "Content-Type": "application/json"
                    },
                    json=issue_data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                return json.dumps({
                    "success": True,
                    "message": f"Issue #{issue_id} updated successfully"
                }, indent=2)
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
