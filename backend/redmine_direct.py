"""
Redmine Direct API Module
Simple, accurate queries using Redmine API total_count
No caching - always returns correct, real-time data
"""

import os
import httpx
from typing import Dict, Optional, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project name to ID mapping
PROJECT_MAP = {
    "ncel": 6,
    "NCEL": 6,
}


def normalize_project_id(project_id: Optional[Union[int, str]]) -> Optional[int]:
    """
    Convert project name to ID if needed
    
    Args:
        project_id: Project ID (int) or name (str)
    
    Returns:
        Project ID as integer, or None if not found
    """
    if project_id is None:
        return None
    
    if isinstance(project_id, int):
        return project_id
    
    if isinstance(project_id, str):
        # Try to look up in mapping
        if project_id in PROJECT_MAP:
            return PROJECT_MAP[project_id]
        
        # Try to parse as integer
        try:
            return int(project_id)
        except ValueError:
            # Unknown project name
            return None
    
    return None


async def get_issue_count(project_id: Optional[int] = None, 
                          status: str = "open", 
                          tracker: Optional[str] = None) -> Dict:
    """
    Get accurate issue count using Redmine API total_count
    
    Args:
        project_id: Project ID (optional)
        status: "open", "closed", or "all"
        tracker: "Bug", "Feature", "Story", etc. (optional)
    
    Returns:
        {"success": True, "count": 123, "query": {...}}
    """
    try:
        # Get fresh env vars
        redmine_url = os.getenv("REDMINE_URL")
        redmine_key = os.getenv("REDMINE_API_KEY")
        
        if not redmine_url or not redmine_key:
            return {
                "success": False,
                "error": "REDMINE_URL and REDMINE_API_KEY must be set"
            }
        
        params = {
            "limit": 1,  # We only need the total_count, not the actual issues
            "status_id": "open" if status == "open" else ("closed" if status == "closed" else "*")
        }
        
        if project_id:
            params["project_id"] = project_id
        
        # Map tracker names to IDs (common Redmine setup)
        tracker_map = {
            "Bug": 1,
            "Feature": 2,
            "Support": 3,
            "Story": 4
        }
        
        if tracker and tracker in tracker_map:
            params["tracker_id"] = tracker_map[tracker]
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{redmine_url}/issues.json",
                headers={"X-Redmine-API-Key": redmine_key},
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "success": True,
                "count": data.get("total_count", 0),
                "query": {
                    "project_id": project_id,
                    "status": status,
                    "tracker": tracker
                }
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def bug_count(project_id: Optional[Union[int, str]] = None, status: str = "open") -> Dict:
    """
    Get bug count for a project
    
    Args:
        project_id: Project ID or name (optional, None = all projects)
        status: "open", "closed", or "all"
    
    Returns:
        {"success": True, "open_bugs": 123, "total_bugs": 456, ...}
    """
    try:
        # Normalize project_id (convert name to ID if needed)
        normalized_id = normalize_project_id(project_id)
        
        if project_id is not None and normalized_id is None:
            return {
                "success": False,
                "error": f"Unknown project: {project_id}. Known projects: {', '.join(PROJECT_MAP.keys())}"
            }
        
        # Get open bugs
        open_result = await get_issue_count(normalized_id, "open", "Bug")
        if not open_result["success"]:
            return open_result
        
        # Get all bugs
        all_result = await get_issue_count(normalized_id, "all", "Bug")
        if not all_result["success"]:
            return all_result
        
        open_count = open_result["count"]
        total_count = all_result["count"]
        closed_count = total_count - open_count
        
        return {
            "success": True,
            "bug_metrics": {
                "open_bugs": open_count,
                "closed_bugs": closed_count,
                "total_bugs": total_count,
                "project_id": normalized_id,
                "project_name": project_id if isinstance(project_id, str) else None
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def sprint_count(project_id: Optional[Union[int, str]] = None, version_name: Optional[str] = None) -> Dict:
    """
    Get sprint/story counts
    
    Returns committed, completed, remaining counts
    """
    try:
        # Normalize project_id
        normalized_id = normalize_project_id(project_id)
        
        if project_id is not None and normalized_id is None:
            return {
                "success": False,
                "error": f"Unknown project: {project_id}"
            }
        
        # For now, just get all open and closed issues
        # TODO: Add version filtering when we know the version ID
        
        open_result = await get_issue_count(normalized_id, "open")
        closed_result = await get_issue_count(normalized_id, "closed")
        
        if not open_result["success"] or not closed_result["success"]:
            return {"success": False, "error": "Failed to get counts"}
        
        open_count = open_result["count"]
        closed_count = closed_result["count"]
        total_count = open_count + closed_count
        
        return {
            "success": True,
            "sprint_status": {
                "committed": total_count,
                "completed": closed_count,
                "remaining": open_count,
                "completion": round((closed_count / total_count * 100) if total_count > 0 else 0, 1)
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


async def backlog_count(project_id: Optional[Union[int, str]] = None) -> Dict:
    """
    Get backlog size (open issues)
    """
    try:
        # Normalize project_id
        normalized_id = normalize_project_id(project_id)
        
        if project_id is not None and normalized_id is None:
            return {
                "success": False,
                "error": f"Unknown project: {project_id}"
            }
        
        result = await get_issue_count(normalized_id, "open")
        
        if not result["success"]:
            return result
        
        return {
            "success": True,
            "backlog_metrics": {
                "total": result["count"],
                "project_id": normalized_id
            }
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
