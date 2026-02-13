"""
Redmine Analytics Module (Cache-Powered)
Provides comprehensive analytics using cached data for instant responses
"""

import os
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional
from redmine_cache import cache

REDMINE_URL = os.getenv("REDMINE_URL")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY")


# ===== SPRINT / ITERATION STATUS =====

def sprint_status_analytics(version_name: Optional[str] = None, project_id: Optional[int] = None) -> Dict:
    """Complete sprint status with all metrics using cache"""
    try:
        df = cache.get_issues()
        
        # Filter by project if provided
        if project_id:
            df = df[df['project_id'] == project_id]
        
        # Filter by version if provided
        if version_name:
            df = df[df['fixed_version_name'] == version_name]
        
        committed = len(df)
        completed = len(df[df['status_name'].isin(['Closed', 'Resolved'])])
        remaining = committed - completed
        in_progress = len(df[df['status_name'] == 'In Progress'])
        
        # Check for blocked issues (in subject or description)
        blocked = len(df[df['subject'].str.contains('block', case=False, na=False)])
        
        # Calculate estimated vs actual
        estimated_hours = df['estimated_hours'].sum()
        spent_hours = df['spent_hours'].sum()
        
        completion_pct = (completed / committed * 100) if committed > 0 else 0
        
        if spent_hours < estimated_hours:
            ahead_behind = "ahead"
        elif spent_hours > estimated_hours:
            ahead_behind = "behind"
        else:
            ahead_behind = "on track"
        
        return {
            "success": True,
            "sprint_status": {
                "committed": int(committed),
                "completed": int(completed),
                "remaining": int(remaining),
                "in_progress": int(in_progress),
                "blocked": int(blocked),
                "completion": round(completion_pct, 1),
                "estimated_hours": float(estimated_hours),
                "spent_hours": float(spent_hours),
                "ahead_behind": ahead_behind
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== BACKLOG & SCOPE =====

def backlog_analytics(project_id: Optional[int] = None) -> Dict:
    """Backlog metrics and health using cache"""
    try:
        df = cache.get_issues()
        
        # Filter by project if provided
        if project_id:
            df = df[df['project_id'] == project_id]
        
        # Open issues only
        open_df = df[~df['status_name'].isin(['Closed', 'Resolved'])]
        
        total = len(open_df)
        high_priority = len(open_df[open_df['priority_name'].isin(['High', 'Urgent', 'Immediate'])])
        unestimated = len(open_df[open_df['estimated_hours'] == 0])
        
        # Calculate aging (remove timezone for comparison)
        now = pd.Timestamp.now(tz='UTC')
        ages = (now - open_df['created_on']).dt.days
        avg_age = ages.mean() if len(ages) > 0 else 0
        
        # Monthly trends
        one_month_ago = now - pd.Timedelta(days=30)
        added_this_month = len(df[df['created_on'] > one_month_ago])
        closed_this_month = len(df[(df['closed_on'].notna()) & (df['closed_on'] > one_month_ago)])
        
        return {
            "success": True,
            "backlog_metrics": {
                "total": int(total),
                "high_priority": int(high_priority),
                "high_priority_percent": round((high_priority / total * 100) if total > 0 else 0, 1),
                "unestimated": int(unestimated),
                "unestimated_percent": round((unestimated / total * 100) if total > 0 else 0, 1),
                "avg_age_days": round(avg_age, 1),
                "added_this_month": int(added_this_month),
                "closed_this_month": int(closed_this_month)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== TEAM PERFORMANCE / WORKLOAD =====

def team_workload_analytics(project_id: Optional[int] = None) -> Dict:
    """Team workload distribution using cache"""
    try:
        df = cache.get_issues()
        
        # Filter by project if provided
        if project_id:
            df = df[df['project_id'] == project_id]
        
        # Open issues only
        open_df = df[~df['status_name'].isin(['Closed', 'Resolved'])]
        
        # Group by assigned_to_name
        workload = open_df.groupby('assigned_to_name').size().to_dict()
        
        # Find overloaded members (more than 10 tasks)
        overloaded = [name for name, count in workload.items() 
                     if count > 10 and name != "Unassigned"]
        
        return {
            "success": True,
            "team_workload": workload,
            "overloaded_members": overloaded
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def cycle_time_analytics(project_id: Optional[int] = None) -> Dict:
    """Cycle time and lead time metrics using cache"""
    try:
        df = cache.get_issues()
        
        # Filter by project if provided
        if project_id:
            df = df[df['project_id'] == project_id]
        
        # Closed issues only
        closed_df = df[df['status_name'].isin(['Closed', 'Resolved'])].copy()
        
        # Take last 100 closed issues
        closed_df = closed_df.sort_values('closed_on', ascending=False).head(100)
        
        # Calculate lead time (created to closed) - handle timezone
        lead_times = []
        cycle_times = []
        
        for idx, row in closed_df.iterrows():
            if pd.notna(row['closed_on']):
                lead_time = (row['closed_on'] - row['created_on']).days
                cycle_time = abs((row['closed_on'] - row['updated_on']).days)
                lead_times.append(lead_time)
                cycle_times.append(cycle_time)
        
        avg_lead = sum(lead_times) / len(lead_times) if lead_times else 0
        avg_cycle = sum(cycle_times) / len(cycle_times) if cycle_times else 0
        
        # Count reopened tickets (contains "reopen" in subject)
        reopened = len(df[df['subject'].str.contains('reopen', case=False, na=False)])
        
        return {
            "success": True,
            "cycle_metrics": {
                "avg_lead_time_days": round(avg_lead, 1),
                "avg_cycle_time_days": round(avg_cycle, 1),
                "reopened_tickets": int(reopened)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== QUALITY & DEFECTS =====

def bug_analytics(project_id: Optional[int] = None) -> Dict:
    """Bug metrics and quality stats using cache"""
    try:
        df = cache.get_issues()
        
        # Filter by project if provided
        if project_id:
            df = df[df['project_id'] == project_id]
        
        # Filter bugs
        bugs_df = df[df['tracker_name'] == 'Bug']
        open_bugs_df = bugs_df[~bugs_df['status_name'].isin(['Closed', 'Resolved'])]
        critical_bugs_df = open_bugs_df[open_bugs_df['priority_name'].isin(['High', 'Urgent', 'Immediate'])]
        
        # Filter stories
        stories_df = df[df['tracker_name'].isin(['Feature', 'Story'])]
        
        bug_ratio = len(bugs_df) / len(stories_df) if len(stories_df) > 0 else 0
        
        # Resolution time for closed bugs
        closed_bugs_df = bugs_df[bugs_df['status_name'].isin(['Closed', 'Resolved'])].head(50)
        resolution_times = []
        for idx, bug in closed_bugs_df.iterrows():
            if pd.notna(bug['closed_on']):
                days = (bug['closed_on'] - bug['created_on']).days
                resolution_times.append(days)
        
        avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        # Post-release bugs (last 30 days)
        thirty_days_ago = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=30)
        post_release_bugs = len(bugs_df[bugs_df['created_on'] > thirty_days_ago])
        
        return {
            "success": True,
            "bug_metrics": {
                "total_bugs": int(len(bugs_df)),
                "open_bugs": int(len(open_bugs_df)),
                "critical_bugs": int(len(critical_bugs_df)),
                "bug_ratio": round(bug_ratio, 2),
                "avg_resolution": round(avg_resolution, 1),
                "post_release_bugs": int(post_release_bugs)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== RELEASE & DELIVERY =====

def release_analytics(version_name: Optional[str] = None) -> Dict:
    """Release status and progress using cache"""
    try:
        df = cache.get_issues()
        
        # If no version specified, find the most common open version
        if not version_name:
            open_df = df[~df['status_name'].isin(['Closed', 'Resolved'])]
            if len(open_df) > 0:
                version_counts = open_df['fixed_version_name'].value_counts()
                if len(version_counts) > 0:
                    version_name = version_counts.index[0]
        
        if not version_name or pd.isna(version_name):
            return {"success": False, "error": "No release/version found"}
        
        # Filter by version
        release_df = df[df['fixed_version_name'] == version_name]
        
        total = len(release_df)
        completed = len(release_df[release_df['status_name'].isin(['Closed', 'Resolved'])])
        unresolved = total - completed
        progress = (completed / total * 100) if total > 0 else 0
        
        # Get due date if available
        due_dates = release_df['due_date'].dropna()
        due_date = due_dates.iloc[0].strftime('%Y-%m-%d') if len(due_dates) > 0 else "Not set"
        
        return {
            "success": True,
            "release_status": {
                "name": version_name,
                "total": int(total),
                "completed": int(completed),
                "unresolved": int(unresolved),
                "progress": round(progress, 1),
                "due_date": due_date
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ===== TRENDS & PREDICTABILITY =====

def velocity_trend_analytics(project_id: Optional[int] = None, sprints: int = 5) -> Dict:
    """Velocity trend analysis using cache"""
    try:
        df = cache.get_issues()
        
        # Filter by project if provided
        if project_id:
            df = df[df['project_id'] == project_id]
        
        # Get closed issues only
        closed_df = df[df['status_name'].isin(['Closed', 'Resolved'])]
        
        # Group by version and calculate velocity
        version_velocity = closed_df.groupby('fixed_version_name')['estimated_hours'].sum()
        
        # Take top N versions by velocity
        top_versions = version_velocity.nlargest(sprints)
        
        velocities = [
            {"name": name, "value": float(value)}
            for name, value in top_versions.items()
            if pd.notna(name)
        ]
        
        # Determine trend
        if len(velocities) >= 2:
            if velocities[0]["value"] > velocities[-1]["value"]:
                trend = "increasing"
            elif velocities[0]["value"] < velocities[-1]["value"]:
                trend = "decreasing"
            else:
                trend = "stable"
            avg_velocity = sum(v["value"] for v in velocities) / len(velocities)
        else:
            trend = "stable"
            avg_velocity = velocities[0]["value"] if velocities else 0
        
        return {
            "success": True,
            "velocity_trend": {
                "velocities": velocities,
                "trend": trend,
                "average": round(avg_velocity, 1)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def throughput_analytics(project_id: Optional[int] = None, weeks: int = 4) -> Dict:
    """Throughput analysis using cache"""
    try:
        df = cache.get_issues()
        
        # Filter by project if provided
        if project_id:
            df = df[df['project_id'] == project_id]
        
        cutoff = pd.Timestamp.now(tz='UTC') - pd.Timedelta(weeks=weeks)
        
        created_recent = len(df[df['created_on'] > cutoff])
        closed_recent = len(df[(df['closed_on'].notna()) & (df['closed_on'] > cutoff)])
        
        return {
            "success": True,
            "throughput": {
                "created": int(created_recent),
                "closed": int(closed_recent),
                "net": int(closed_recent - created_recent),
                "weeks": weeks
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
