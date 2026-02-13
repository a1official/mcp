"""
Redmine OAuth Agent - Individual User Authentication
Allows users to authenticate with their own Redmine accounts
"""

import os
import json
import httpx
from typing import Optional

# Redmine OAuth configuration
REDMINE_URL = os.getenv("REDMINE_URL", "")
REDMINE_CLIENT_ID = os.getenv("REDMINE_CLIENT_ID", "")
REDMINE_CLIENT_SECRET = os.getenv("REDMINE_CLIENT_SECRET", "")


def register_redmine_oauth_tools(mcp):
    """Register Redmine OAuth tools with the MCP server"""
    
    @mcp.tool()
    async def redmine_oauth_get_auth_url(redirect_uri: str = "http://localhost:3001/api/redmine/callback") -> str:
        """
        Get the OAuth authorization URL for Redmine.
        Users should visit this URL to authorize the application.
        
        Args:
            redirect_uri: The callback URL after authorization
        
        Returns:
            JSON with authorization URL
        """
        if not REDMINE_URL or not REDMINE_CLIENT_ID:
            return json.dumps({
                "success": False,
                "error": "Redmine OAuth not configured. Set REDMINE_URL and REDMINE_CLIENT_ID in .env"
            })
        
        auth_url = (
            f"{REDMINE_URL}/oauth/authorize"
            f"?client_id={REDMINE_CLIENT_ID}"
            f"&redirect_uri={redirect_uri}"
            f"&response_type=code"
            f"&scope=read write"
        )
        
        return json.dumps({
            "success": True,
            "auth_url": auth_url,
            "instructions": "Visit this URL to authorize access to your Redmine account"
        }, indent=2)
    
    @mcp.tool()
    async def redmine_oauth_exchange_code(code: str, redirect_uri: str = "http://localhost:3001/api/redmine/callback") -> str:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code from OAuth callback
            redirect_uri: The same redirect URI used in authorization
        
        Returns:
            JSON with access token
        """
        if not REDMINE_URL or not REDMINE_CLIENT_ID or not REDMINE_CLIENT_SECRET:
            return json.dumps({
                "success": False,
                "error": "Redmine OAuth not configured"
            })
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{REDMINE_URL}/oauth/token",
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": REDMINE_CLIENT_ID,
                        "client_secret": REDMINE_CLIENT_SECRET
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                return json.dumps({
                    "success": True,
                    "access_token": data.get("access_token"),
                    "refresh_token": data.get("refresh_token"),
                    "expires_in": data.get("expires_in"),
                    "token_type": data.get("token_type")
                }, indent=2)
                
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": str(e)
                })
    
    @mcp.tool()
    async def redmine_oauth_list_projects(access_token: str) -> str:
        """
        List Redmine projects using OAuth access token.
        
        Args:
            access_token: OAuth access token for the user
        
        Returns:
            JSON with list of projects
        """
        if not REDMINE_URL:
            return json.dumps({
                "success": False,
                "error": "Redmine URL not configured"
            })
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{REDMINE_URL}/projects.json",
                    headers={"Authorization": f"Bearer {access_token}"},
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
    async def redmine_oauth_list_issues(
        access_token: str,
        project_id: Optional[str] = None,
        status: str = "open",
        limit: int = 25
    ) -> str:
        """
        List Redmine issues using OAuth access token.
        
        Args:
            access_token: OAuth access token for the user
            project_id: Project ID or identifier (optional)
            status: Issue status - 'open', 'closed', or 'all'
            limit: Maximum number of issues to return
        
        Returns:
            JSON with list of issues
        """
        if not REDMINE_URL:
            return json.dumps({
                "success": False,
                "error": "Redmine URL not configured"
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
                    headers={"Authorization": f"Bearer {access_token}"},
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
    async def redmine_oauth_create_issue(
        access_token: str,
        project_id: str,
        subject: str,
        description: str = "",
        priority_id: int = 2,
        tracker_id: int = 1,
        assigned_to_id: Optional[int] = None
    ) -> str:
        """
        Create a new Redmine issue using OAuth access token.
        
        Args:
            access_token: OAuth access token for the user
            project_id: Project ID or identifier
            subject: Issue subject/title
            description: Issue description
            priority_id: Priority ID (1=Low, 2=Normal, 3=High, 4=Urgent, 5=Immediate)
            tracker_id: Tracker ID (1=Bug, 2=Feature, 3=Support)
            assigned_to_id: User ID to assign the issue to
        
        Returns:
            JSON with created issue information
        """
        if not REDMINE_URL:
            return json.dumps({
                "success": False,
                "error": "Redmine URL not configured"
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
                        "Authorization": f"Bearer {access_token}",
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
