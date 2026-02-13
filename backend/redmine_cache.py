"""
Redmine Cache Module
Implements hybrid caching strategy with pandas for fast analytics
"""

import os
import httpx
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import asyncio
from threading import Lock
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

REDMINE_URL = os.getenv("REDMINE_URL")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY")


class RedmineCache:
    """
    Hybrid caching layer for Redmine data
    - Caches all issues, projects, users in pandas DataFrames
    - Auto-refreshes every 5 minutes
    - Provides instant analytics queries
    - Falls back to API if cache fails
    """
    
    def __init__(self, ttl_seconds: int = 300):
        self.issues_df: Optional[pd.DataFrame] = None
        self.projects_df: Optional[pd.DataFrame] = None
        self.users_df: Optional[pd.DataFrame] = None
        self.versions_df: Optional[pd.DataFrame] = None
        
        self.last_updated: Optional[datetime] = None
        self.ttl_seconds = ttl_seconds
        self.is_refreshing = False
        self.lock = Lock()
        
        self.stats = {
            "total_refreshes": 0,
            "last_refresh_duration": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def is_stale(self) -> bool:
        """Check if cache needs refresh"""
        if not self.last_updated or self.issues_df is None:
            return True
        
        age = (datetime.now() - self.last_updated).total_seconds()
        return age > self.ttl_seconds
    
    def get_cache_age(self) -> Optional[int]:
        """Get cache age in seconds"""
        if not self.last_updated:
            return None
        return int((datetime.now() - self.last_updated).total_seconds())
    
    async def fetch_all_issues(self, limit: int = None) -> List[Dict]:
        """Fetch all issues with pagination (no limit by default)"""
        # Get fresh env vars
        redmine_url = os.getenv("REDMINE_URL")
        redmine_key = os.getenv("REDMINE_API_KEY")
        
        if not redmine_url or not redmine_key:
            raise ValueError("REDMINE_URL and REDMINE_API_KEY must be set in environment")
        
        all_issues = []
        offset = 0
        batch_size = 100
        
        async with httpx.AsyncClient() as client:
            while True:
                response = await client.get(
                    f"{redmine_url}/issues.json",
                    headers={"X-Redmine-API-Key": redmine_key},
                    params={
                        "limit": batch_size,
                        "offset": offset,
                        "status_id": "*"  # All statuses
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()  # Raise error for bad status codes
                data = response.json()
                issues = data.get("issues", [])
                
                if not issues:
                    break
                
                all_issues.extend(issues)
                
                # Check if we've fetched all
                total_count = data.get("total_count", 0)
                if len(all_issues) >= total_count:
                    break
                
                # If limit is set, respect it
                if limit and len(all_issues) >= limit:
                    break
                
                offset += batch_size
        
        return all_issues
    
    async def fetch_all_projects(self) -> List[Dict]:
        """Fetch all projects"""
        try:
            redmine_url = os.getenv("REDMINE_URL")
            redmine_key = os.getenv("REDMINE_API_KEY")
            
            if not redmine_url or not redmine_key:
                raise ValueError("REDMINE_URL and REDMINE_API_KEY must be set in environment")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{redmine_url}/projects.json",
                    headers={"X-Redmine-API-Key": redmine_key},
                    params={"limit": 100},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json().get("projects", [])
        except Exception as e:
            print(f"Warning: Could not fetch projects: {e}")
            return []
    
    async def fetch_all_users(self) -> List[Dict]:
        """Fetch all users (requires admin privileges, returns empty list if fails)"""
        try:
            redmine_url = os.getenv("REDMINE_URL")
            redmine_key = os.getenv("REDMINE_API_KEY")
            
            if not redmine_url or not redmine_key:
                return []
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{redmine_url}/users.json",
                    headers={"X-Redmine-API-Key": redmine_key},
                    params={"limit": 100},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json().get("users", [])
        except Exception as e:
            print(f"Warning: Could not fetch users (may require admin privileges): {e}")
            return []
    
    async def fetch_all_versions(self) -> List[Dict]:
        """Fetch all versions"""
        try:
            redmine_url = os.getenv("REDMINE_URL")
            redmine_key = os.getenv("REDMINE_API_KEY")
            
            if not redmine_url or not redmine_key:
                return []
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{redmine_url}/versions.json",
                    headers={"X-Redmine-API-Key": redmine_key},
                    params={"limit": 100},
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json().get("versions", [])
        except Exception as e:
            print(f"Warning: Could not fetch versions: {e}")
            return []
    
    def normalize_issue(self, issue: Dict) -> Dict:
        """Flatten nested issue structure for DataFrame"""
        return {
            "id": issue.get("id"),
            "subject": issue.get("subject", ""),
            "description": issue.get("description", ""),
            "project_id": issue.get("project", {}).get("id"),
            "project_name": issue.get("project", {}).get("name"),
            "tracker_id": issue.get("tracker", {}).get("id"),
            "tracker_name": issue.get("tracker", {}).get("name"),
            "status_id": issue.get("status", {}).get("id"),
            "status_name": issue.get("status", {}).get("name"),
            "priority_id": issue.get("priority", {}).get("id"),
            "priority_name": issue.get("priority", {}).get("name"),
            "assigned_to_id": issue.get("assigned_to", {}).get("id"),
            "assigned_to_name": issue.get("assigned_to", {}).get("name", "Unassigned"),
            "fixed_version_id": issue.get("fixed_version", {}).get("id"),
            "fixed_version_name": issue.get("fixed_version", {}).get("name"),
            "estimated_hours": issue.get("estimated_hours", 0),
            "spent_hours": issue.get("spent_hours", 0),
            "created_on": pd.to_datetime(issue.get("created_on")),
            "updated_on": pd.to_datetime(issue.get("updated_on")),
            "closed_on": pd.to_datetime(issue.get("closed_on")) if issue.get("closed_on") else None,
            "start_date": pd.to_datetime(issue.get("start_date")) if issue.get("start_date") else None,
            "due_date": pd.to_datetime(issue.get("due_date")) if issue.get("due_date") else None,
        }
    
    async def refresh(self, force: bool = False) -> Dict[str, Any]:
        """
        Refresh cache from Redmine API
        Returns status dict with timing and counts
        """
        if self.is_refreshing:
            return {"status": "already_refreshing"}
        
        if not force and not self.is_stale():
            return {"status": "cache_fresh", "age_seconds": self.get_cache_age()}
        
        self.is_refreshing = True
        start_time = datetime.now()
        
        try:
            # Fetch all data in parallel
            issues_raw, projects_raw, users_raw, versions_raw = await asyncio.gather(
                self.fetch_all_issues(),
                self.fetch_all_projects(),
                self.fetch_all_users(),
                self.fetch_all_versions()
            )
            
            # Normalize and create DataFrames
            issues_normalized = [self.normalize_issue(i) for i in issues_raw]
            self.issues_df = pd.DataFrame(issues_normalized)
            self.projects_df = pd.DataFrame(projects_raw)
            self.users_df = pd.DataFrame(users_raw)
            self.versions_df = pd.DataFrame(versions_raw)
            
            # Update metadata
            self.last_updated = datetime.now()
            duration = (datetime.now() - start_time).total_seconds()
            
            self.stats["total_refreshes"] += 1
            self.stats["last_refresh_duration"] = duration
            
            return {
                "status": "success",
                "issues_count": len(self.issues_df),
                "projects_count": len(self.projects_df),
                "users_count": len(self.users_df),
                "versions_count": len(self.versions_df),
                "duration_seconds": round(duration, 2),
                "timestamp": self.last_updated.isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
        finally:
            self.is_refreshing = False
    
    def get_issues(self, filters: Optional[Dict] = None) -> pd.DataFrame:
        """
        Get issues from cache with optional filters
        Returns DataFrame for fast querying
        """
        if self.issues_df is None:
            self.stats["cache_misses"] += 1
            raise ValueError("Cache not initialized. Call refresh() first.")
        
        self.stats["cache_hits"] += 1
        
        if not filters:
            return self.issues_df.copy()
        
        df = self.issues_df.copy()
        
        # Apply filters
        if "status_name" in filters:
            df = df[df["status_name"] == filters["status_name"]]
        
        if "project_id" in filters:
            df = df[df["project_id"] == filters["project_id"]]
        
        if "assigned_to_id" in filters:
            df = df[df["assigned_to_id"] == filters["assigned_to_id"]]
        
        if "tracker_name" in filters:
            df = df[df["tracker_name"] == filters["tracker_name"]]
        
        if "fixed_version_id" in filters:
            df = df[df["fixed_version_id"] == filters["fixed_version_id"]]
        
        return df
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache status and statistics"""
        return {
            "initialized": self.issues_df is not None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "age_seconds": self.get_cache_age(),
            "is_stale": self.is_stale(),
            "ttl_seconds": self.ttl_seconds,
            "stats": self.stats,
            "counts": {
                "issues": len(self.issues_df) if self.issues_df is not None else 0,
                "projects": len(self.projects_df) if self.projects_df is not None else 0,
                "users": len(self.users_df) if self.users_df is not None else 0,
                "versions": len(self.versions_df) if self.versions_df is not None else 0
            }
        }


# Global cache instance
cache = RedmineCache(ttl_seconds=300)  # 5 minutes TTL
