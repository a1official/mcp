"""
Redmine Analytics V2 - Comprehensive Analytics Tools
Direct API queries for accurate, real-time metrics
"""

import os
import httpx
from typing import Dict, Optional, Union, List
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

REDMINE_URL = os.getenv("REDMINE_URL")
REDMINE_KEY = os.getenv("REDMINE_API_KEY")

# Project name to ID mapping
PROJECT_MAP = {
    "ncel": 6,
    "NCEL": 6,
}

# Status mappings (from API exploration)
STATUS_MAP = {
    "new": 1,
    "in_progress": 2,
    "resolved": 3,
    "feedback": 4,
    "closed": 5,
    "rejected": 6,
    "backlog": 7,
    "cancelled": 8,
}

# Tracker mappings
TRACKER_MAP = {
    "bug": 1,
    "feature": 2,
    "support": 3,
    "story": 4,
}

# Priority mappings (typical Redmine setup)
PRIORITY_MAP = {
    "low": 1,
    "normal": 2,
    "high": 3,
    "urgent": 4,
    "immediate": 5,
}


def normalize_project_id(project_id: Optional[Union[int, str]]) -> Optional[int]:
    """Convert project name to ID"""
    if project_id is None:
        return None
    if isinstance(project_id, int):
        return project_id
    if isinstance(project_id, str):
        if project_id in PROJECT_MAP:
            return PROJECT_MAP[project_id]
        try:
            return int(project_id)
        except ValueError:
            return None
    return None


async def get_count(project_id: Optional[int] = None, **filters) -> int:
    """
    Generic count function using Redmine API total_count
    
    Args:
        project_id: Project ID (optional)
        **filters: Additional filters (status_id, tracker_id, assigned_to_id, etc.)
    
    Returns:
        Count as integer
    """
    try:
        params = {"limit": 1}
        
        if project_id:
            params["project_id"] = project_id
        
        params.update(filters)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{REDMINE_URL}/issues.json",
                headers={"X-Redmine-API-Key": REDMINE_KEY},
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data.get("total_count", 0)
    
    except Exception as e:
        print(f"Error in get_count: {e}")
        return 0


# ========================================
# 📊 SPRINT / ITERATION STATUS
# ========================================

async def sprint_committed_stories(
    project_id: Optional[Union[int, str]] = None,
    version_id: Optional[int] = None
) -> Dict:
    """
    How many issues are committed in the current sprint?
    Note: Counts ALL issues in sprint, not just stories
    """
    try:
        normalized_id = normalize_project_id(project_id)
        
        # Get all issues in the version (sprint) - no tracker filter
        filters = {}
        if version_id:
            filters["fixed_version_id"] = version_id
        
        total = await get_count(normalized_id, **filters)
        
        return {
            "success": True,
            "committed_issues": total,  # Changed from committed_stories
            "version_id": version_id,
            "project_id": normalized_id,
            "note": "Counts all issues (bugs, features, stories, etc.)"
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


async def sprint_completion_status(
    project_id: Optional[Union[int, str]] = None,
    version_id: Optional[int] = None
) -> Dict:
    """
    How many issues are completed vs remaining?
    What is the current sprint burndown status?
    Note: Counts ALL issues in sprint, not just stories
    """
    try:
        normalized_id = normalize_project_id(project_id)
        
        base_filters = {}  # No tracker filter - count all issues
        if version_id:
            base_filters["fixed_version_id"] = version_id
        
        # Get completed issues (closed status)
        completed = await get_count(
            normalized_id,
            status_id=STATUS_MAP["closed"],
            **base_filters
        )
        
        # Get total issues
        total = await get_count(normalized_id, **base_filters)
        
        remaining = total - completed
        completion_pct = round((completed / total * 100) if total > 0 else 0, 1)
        
        return {
            "success": True,
            "sprint_status": {
                "total_committed": total,
                "completed": completed,
                "remaining": remaining,
                "completion_percentage": completion_pct,
                "burndown_status": "on_track" if completion_pct >= 50 else "behind"
            }
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


async def tasks_in_progress(
    project_id: Optional[Union[int, str]] = None
) -> Dict:
    """
    How many tasks are in "In Progress" state?
    """
    try:
        normalized_id = normalize_project_id(project_id)
        
        count = await get_count(
            normalized_id,
            status_id=STATUS_MAP["in_progress"]
        )
        
        return {
            "success": True,
            "in_progress_count": count,
            "project_id": normalized_id
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


async def blocked_tasks(
    project_id: Optional[Union[int, str]] = None
) -> Dict:
    """
    How many tasks are blocked?
    Note: Redmine doesn't have built-in "blocked" status
    Using custom field or specific status if configured
    """
    try:
        normalized_id = normalize_project_id(project_id)
        
        # Assuming "Feedback" status indicates blocked
        # Adjust based on your Redmine configuration
        count = await get_count(
            normalized_id,
            status_id=STATUS_MAP["feedback"]
        )
        
        return {
            "success": True,
            "blocked_count": count,
            "project_id": normalized_id,
            "note": "Using 'Feedback' status as blocked indicator"
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========================================
# 📊 BACKLOG & SCOPE
# ========================================

async def backlog_size(
    project_id: Optional[Union[int, str]] = None
) -> Dict:
    """
    What is the total backlog size (stories / points)?
    """
    try:
        normalized_id = normalize_project_id(project_id)
        
        # Backlog = open issues in "Backlog" status or without version
        backlog_status_count = await get_count(
            normalized_id,
            status_id=STATUS_MAP["backlog"]
        )
        
        # Also count open issues without fixed_version
        open_count = await get_count(
            normalized_id,
            status_id="open"
        )
        
        return {
            "success": True,
            "backlog_metrics": {
                "backlog_status_count": backlog_status_count,
                "total_open_issues": open_count,
                "project_id": normalized_id
            }
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


async def high_priority_open(
    project_id: Optional[Union[int, str]] = None
) -> Dict:
    """
    How many high-priority items are still open?
    """
    try:
        normalized_id = normalize_project_id(project_id)
        
        high = await get_count(
            normalized_id,
            status_id="open",
            priority_id=PRIORITY_MAP["high"]
        )
        
        urgent = await get_count(
            normalized_id,
            status_id="open",
            priority_id=PRIORITY_MAP["urgent"]
        )
        
        immediate = await get_count(
            normalized_id,
            status_id="open",
            priority_id=PRIORITY_MAP["immediate"]
        )
        
        total_high_priority = high + urgent + immediate
        
        return {
            "success": True,
            "high_priority_open": {
                "high": high,
                "urgent": urgent,
                "immediate": immediate,
                "total": total_high_priority
            }
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


async def monthly_activity(
    project_id: Optional[Union[int, str]] = None
) -> Dict:
    """
    How many items were added this month?
    How many items were closed this month?
    """
    try:
        normalized_id = normalize_project_id(project_id)
        
        # Calculate date range for current month
        now = datetime.now()
        month_start = now.replace(day=1).strftime("%Y-%m-%d")
        
        # Items created this month (use >= for created_on)
        created = await get_count(
            normalized_id,
            **{"created_on": f">={month_start}"}
        )
        
        # Items closed this month (use >= for closed_on)
        closed = await get_count(
            normalized_id,
            **{"closed_on": f">={month_start}"}
        )
        
        return {
            "success": True,
            "monthly_activity": {
                "created_this_month": created,
                "closed_this_month": closed,
                "net_change": created - closed,
                "month": now.strftime("%B %Y")
            }
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========================================
# 🐞 QUALITY & DEFECTS
# ========================================

async def bug_metrics(
    project_id: Optional[Union[int, str]] = None
) -> Dict:
    """
    How many open bugs exist?
    How many critical / high-severity bugs are open?
    What is the bug-to-story ratio?
    """
    try:
        normalized_id = normalize_project_id(project_id)
        
        # Open bugs
        open_bugs = await get_count(
            normalized_id,
            status_id="open",
            tracker_id=TRACKER_MAP["bug"]
        )
        
        # Total bugs (for context)
        total_bugs = await get_count(
            normalized_id,
            tracker_id=TRACKER_MAP["bug"]
        )
        
        # Critical/high bugs
        high_bugs = await get_count(
            normalized_id,
            status_id="open",
            tracker_id=TRACKER_MAP["bug"],
            priority_id=PRIORITY_MAP["high"]
        )
        
        urgent_bugs = await get_count(
            normalized_id,
            status_id="open",
            tracker_id=TRACKER_MAP["bug"],
            priority_id=PRIORITY_MAP["urgent"]
        )
        
        # Total stories for ratio
        total_stories = await get_count(
            normalized_id,
            tracker_id=TRACKER_MAP["story"]
        )
        
        # Calculate ratio (bugs per story)
        if total_stories > 0:
            bug_to_story_ratio = round(open_bugs / total_stories, 2)
        else:
            bug_to_story_ratio = None
        
        return {
            "success": True,
            "bug_metrics": {
                "open_bugs": open_bugs,
                "total_bugs": total_bugs,
                "closed_bugs": total_bugs - open_bugs,
                "high_severity_bugs": high_bugs,
                "urgent_bugs": urgent_bugs,
                "total_critical": high_bugs + urgent_bugs,
                "bug_to_story_ratio": bug_to_story_ratio,
                "total_stories": total_stories,
                "note": "bug_to_story_ratio is null if no stories exist" if bug_to_story_ratio is None else None
            }
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========================================
# 👥 TEAM PERFORMANCE / WORKLOAD
# ========================================

async def team_workload(
    project_id: Optional[Union[int, str]] = None
) -> Dict:
    """
    How many tasks are assigned per team member?
    Are any team members overloaded?
    """
    try:
        normalized_id = normalize_project_id(project_id)
        
        # Get all open issues with assignees
        params = {
            "project_id": normalized_id,
            "status_id": "open",
            "limit": 100  # Get actual issues to count by assignee
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{REDMINE_URL}/issues.json",
                headers={"X-Redmine-API-Key": REDMINE_KEY},
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            # Count by assignee
            workload = {}
            for issue in data.get("issues", []):
                if "assigned_to" in issue:
                    assignee = issue["assigned_to"]["name"]
                    workload[assignee] = workload.get(assignee, 0) + 1
            
            # Find overloaded (>10 tasks)
            overloaded = {k: v for k, v in workload.items() if v > 10}
            
            return {
                "success": True,
                "team_workload": {
                    "workload_by_member": workload,
                    "overloaded_members": overloaded,
                    "total_assigned": sum(workload.values()),
                    "team_size": len(workload)
                }
            }
    
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========================================
# 📈 TRENDS & PREDICTABILITY
# ========================================

async def throughput_analysis(
    project_id: Optional[Union[int, str]] = None,
    weeks: int = 4
) -> Dict:
    """
    Are we closing more tickets than we're creating?
    What is the throughput per week?
    """
    try:
        normalized_id = normalize_project_id(project_id)
        
        # Simplified: just get totals for last N weeks
        now = datetime.now()
        weeks_ago = (now - timedelta(days=weeks*7)).strftime("%Y-%m-%d")
        
        # Total created in period
        created = await get_count(
            normalized_id,
            **{"created_on": f">={weeks_ago}"}
        )
        
        # Total closed in period
        closed = await get_count(
            normalized_id,
            **{"closed_on": f">={weeks_ago}"}
        )
        
        avg_created_per_week = round(created / weeks, 1)
        avg_closed_per_week = round(closed / weeks, 1)
        
        return {
            "success": True,
            "throughput": {
                "period_weeks": weeks,
                "total_created": created,
                "total_closed": closed,
                "net_change": closed - created,
                "avg_created_per_week": avg_created_per_week,
                "avg_closed_per_week": avg_closed_per_week,
                "trend": "positive" if closed > created else "negative"
            }
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}
