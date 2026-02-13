"""
Redmine Agent - Comprehensive Project Management Integration
Provides CRUD tools + analytics tools for managing Redmine issues, projects, sprints, and team metrics.
All analytics use direct Redmine REST API calls (no cache/pandas dependency).
"""

import os
import json
import httpx
from typing import Optional, Union, List, Dict, Any
from datetime import datetime, timedelta

# Redmine configuration (read fresh each call to support runtime changes)
def _cfg():
    return os.getenv("REDMINE_URL", ""), os.getenv("REDMINE_API_KEY", "")

HEADERS = lambda key: {"X-Redmine-API-Key": key, "Content-Type": "application/json"}
TIMEOUT = 30.0

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

async def _api_get(path: str, params: dict | None = None, timeout: float = TIMEOUT) -> dict:
    """Low-level GET helper. Raises on HTTP errors."""
    url, key = _cfg()
    if not url or not key:
        raise RuntimeError("Redmine URL or API key not configured. Set REDMINE_URL and REDMINE_API_KEY environment variables.")
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{url}{path}", headers={"X-Redmine-API-Key": key}, params=params or {}, timeout=timeout)
        r.raise_for_status()
        return r.json()


async def _api_post(path: str, body: dict) -> dict:
    url, key = _cfg()
    if not url or not key:
        raise RuntimeError("Redmine not configured.")
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{url}{path}", headers=HEADERS(key), json=body, timeout=TIMEOUT)
        r.raise_for_status()
        # POST may return empty body (204)
        return r.json() if r.content else {}


async def _api_put(path: str, body: dict) -> int:
    url, key = _cfg()
    if not url or not key:
        raise RuntimeError("Redmine not configured.")
    async with httpx.AsyncClient() as client:
        r = await client.put(f"{url}{path}", headers=HEADERS(key), json=body, timeout=TIMEOUT)
        r.raise_for_status()
        return r.status_code


async def _api_delete(path: str) -> int:
    url, key = _cfg()
    if not url or not key:
        raise RuntimeError("Redmine not configured.")
    async with httpx.AsyncClient() as client:
        r = await client.delete(f"{url}{path}", headers={"X-Redmine-API-Key": key}, timeout=TIMEOUT)
        r.raise_for_status()
        return r.status_code


async def _fetch_all_issues(params: dict, max_issues: int = 5000) -> List[dict]:
    """Paginate through ALL issues matching *params*. Returns list of raw issue dicts."""
    url, key = _cfg()
    if not url or not key:
        raise RuntimeError("Redmine not configured.")
    all_issues: List[dict] = []
    offset = 0
    limit = 100  # Redmine max per page
    async with httpx.AsyncClient() as client:
        while True:
            p = {**params, "limit": limit, "offset": offset}
            r = await client.get(f"{url}/issues.json", headers={"X-Redmine-API-Key": key}, params=p, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            issues = data.get("issues", [])
            all_issues.extend(issues)
            total = data.get("total_count", 0)
            offset += limit
            if offset >= total or offset >= max_issues or not issues:
                break
    return all_issues


async def _get_total_count(params: dict) -> int:
    """Return total_count for a query without fetching issue bodies."""
    data = await _api_get("/issues.json", {**params, "limit": 1})
    return data.get("total_count", 0)


async def _resolve_project_id(project: Optional[Union[int, str]]) -> Optional[int]:
    """Resolve a project name/identifier/id to a numeric project id."""
    if project is None:
        return None
    if isinstance(project, int):
        return project
    # Try int parse
    try:
        return int(project)
    except (ValueError, TypeError):
        pass
    # Search by identifier or name
    try:
        data = await _api_get(f"/projects/{project}.json")
        return data.get("project", {}).get("id")
    except Exception:
        pass
    # Fallback: search all projects
    try:
        data = await _api_get("/projects.json", {"limit": 100})
        needle = project.lower()
        for p in data.get("projects", []):
            if p.get("identifier", "").lower() == needle or p.get("name", "").lower() == needle:
                return p["id"]
    except Exception:
        pass
    return None


async def _list_versions(project_id: int) -> List[dict]:
    """Return all versions for a project."""
    data = await _api_get(f"/projects/{project_id}/versions.json")
    return data.get("versions", [])


async def _find_active_version(project_id: int) -> Optional[dict]:
    """Return the most likely 'current sprint' version (status=open, nearest due_date)."""
    versions = await _list_versions(project_id)
    open_versions = [v for v in versions if v.get("status") == "open"]
    if not open_versions:
        return None
    # Sort by due_date ascending; versions without due_date go last
    def sort_key(v):
        dd = v.get("due_date")
        if dd:
            try:
                return datetime.strptime(dd, "%Y-%m-%d")
            except Exception:
                pass
        return datetime(9999, 1, 1)
    open_versions.sort(key=sort_key)
    return open_versions[0]


def _issue_summary(issue: dict) -> dict:
    """Extract a rich summary dict from a raw Redmine issue dict."""
    return {
        "id": issue.get("id"),
        "subject": issue.get("subject"),
        "tracker": (issue.get("tracker") or {}).get("name"),
        "status": (issue.get("status") or {}).get("name"),
        "priority": (issue.get("priority") or {}).get("name"),
        "assigned_to": (issue.get("assigned_to") or {}).get("name"),
        "author": (issue.get("author") or {}).get("name"),
        "project": (issue.get("project") or {}).get("name"),
        "fixed_version": (issue.get("fixed_version") or {}).get("name"),
        "done_ratio": issue.get("done_ratio"),
        "estimated_hours": issue.get("estimated_hours"),
        "spent_hours": issue.get("spent_hours"),
        "start_date": issue.get("start_date"),
        "due_date": issue.get("due_date"),
        "created_on": issue.get("created_on"),
        "updated_on": issue.get("updated_on"),
        "closed_on": issue.get("closed_on"),
    }


def _ok(payload: dict) -> str:
    return json.dumps({"success": True, **payload}, indent=2, default=str)


def _err(msg: str) -> str:
    return json.dumps({"success": False, "error": msg})


# ---------------------------------------------------------------------------
# Register all tools
# ---------------------------------------------------------------------------

def register_redmine_tools(mcp):
    """Register all Redmine-related tools with the MCP server"""

    # ===================================================================
    # DISCOVERY TOOLS
    # ===================================================================

    @mcp.tool()
    async def redmine_list_projects() -> str:
        """
        List all Redmine projects you have access to.
        Returns project id, name, identifier, description and status.
        """
        try:
            all_projects = []
            offset = 0
            while True:
                data = await _api_get("/projects.json", {"limit": 100, "offset": offset})
                projects = data.get("projects", [])
                for p in projects:
                    all_projects.append({
                        "id": p.get("id"),
                        "name": p.get("name"),
                        "identifier": p.get("identifier"),
                        "description": (p.get("description") or "")[:200],
                        "status": p.get("status"),
                        "created_on": p.get("created_on"),
                    })
                if offset + 100 >= data.get("total_count", 0):
                    break
                offset += 100
            return _ok({"count": len(all_projects), "projects": all_projects})
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_list_versions(project_id: str) -> str:
        """
        List all versions (sprints/releases) for a project.
        Use this to find version IDs needed for sprint analytics.

        Args:
            project_id: Project ID or identifier (e.g. '6' or 'ncel')
        """
        try:
            pid = await _resolve_project_id(project_id)
            if pid is None:
                return _err(f"Could not resolve project: {project_id}")
            versions = await _list_versions(pid)
            result = []
            for v in versions:
                result.append({
                    "id": v.get("id"),
                    "name": v.get("name"),
                    "status": v.get("status"),
                    "due_date": v.get("due_date"),
                    "description": (v.get("description") or "")[:200],
                    "sharing": v.get("sharing"),
                    "created_on": v.get("created_on"),
                    "updated_on": v.get("updated_on"),
                })
            return _ok({"project_id": pid, "count": len(result), "versions": result})
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_list_trackers() -> str:
        """
        List all available trackers (Bug, Feature, Story, Support, etc.)
        Returns tracker id and name.
        """
        try:
            data = await _api_get("/trackers.json")
            trackers = [{"id": t["id"], "name": t["name"]} for t in data.get("trackers", [])]
            return _ok({"trackers": trackers})
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_list_statuses() -> str:
        """
        List all available issue statuses (New, In Progress, Closed, etc.)
        Returns status id, name, and whether it is a closed status.
        """
        try:
            data = await _api_get("/issue_statuses.json")
            statuses = [{"id": s["id"], "name": s["name"], "is_closed": s.get("is_closed", False)} for s in data.get("issue_statuses", [])]
            return _ok({"statuses": statuses})
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_list_users(project_id: Optional[str] = None) -> str:
        """
        List users/members. If project_id is given, lists project members.
        Otherwise lists all visible users (requires admin or appropriate permissions).

        Args:
            project_id: Project ID or identifier (optional)
        """
        try:
            if project_id:
                pid = await _resolve_project_id(project_id)
                if pid is None:
                    return _err(f"Could not resolve project: {project_id}")
                data = await _api_get(f"/projects/{pid}/memberships.json", {"limit": 100})
                members = []
                for m in data.get("memberships", []):
                    user = m.get("user")
                    if user:
                        roles = [r.get("name") for r in m.get("roles", [])]
                        members.append({"id": user.get("id"), "name": user.get("name"), "roles": roles})
                return _ok({"project_id": pid, "count": len(members), "members": members})
            else:
                data = await _api_get("/users.json", {"limit": 100, "status": 1})  # status=1 = active
                users = [{"id": u["id"], "login": u.get("login"), "name": f"{u.get('firstname','')} {u.get('lastname','')}".strip(), "mail": u.get("mail")} for u in data.get("users", [])]
                return _ok({"count": len(users), "users": users})
        except Exception as e:
            return _err(str(e))

    # ===================================================================
    # CRUD TOOLS
    # ===================================================================

    @mcp.tool()
    async def redmine_list_issues(
        project_id: Optional[str] = None,
        status: str = "open",
        tracker_id: Optional[int] = None,
        assigned_to_id: Optional[int] = None,
        fixed_version_id: Optional[int] = None,
        priority_id: Optional[int] = None,
        limit: int = 25,
        sort: str = "updated_on:desc",
    ) -> str:
        """
        List Redmine issues with flexible filtering. Returns rich issue data including
        tracker, version, estimated_hours, done_ratio, dates.

        Args:
            project_id: Project ID or identifier (optional)
            status: 'open', 'closed', or 'all' (default: 'open')
            tracker_id: Filter by tracker ID (optional, use redmine_list_trackers to find IDs)
            assigned_to_id: Filter by assignee user ID (optional)
            fixed_version_id: Filter by version/sprint ID (optional, use redmine_list_versions to find IDs)
            priority_id: Filter by priority ID (optional: 1=Low,2=Normal,3=High,4=Urgent,5=Immediate)
            limit: Max issues to return, -1 for ALL (default: 25)
            sort: Sort order (default: 'updated_on:desc')
        """
        try:
            params: dict[str, Any] = {}
            status_map = {"open": "open", "closed": "closed", "all": "*"}
            params["status_id"] = status_map.get(status, "*")
            params["sort"] = sort

            if project_id:
                pid = await _resolve_project_id(project_id)
                if pid is not None:
                    params["project_id"] = pid
                else:
                    params["project_id"] = project_id  # let Redmine try raw value
            if tracker_id:
                params["tracker_id"] = tracker_id
            if assigned_to_id:
                params["assigned_to_id"] = assigned_to_id
            if fixed_version_id:
                params["fixed_version_id"] = fixed_version_id
            if priority_id:
                params["priority_id"] = priority_id

            if limit == -1:
                issues = await _fetch_all_issues(params)
            else:
                params["limit"] = min(limit, 100)
                data = await _api_get("/issues.json", params)
                issues = data.get("issues", [])
                total_count = data.get("total_count", 0)

            result_issues = [_issue_summary(i) for i in issues]

            payload = {
                "count": len(result_issues),
                "issues": result_issues,
            }
            if limit != -1:
                payload["total_count"] = total_count
            else:
                payload["total_count"] = len(result_issues)
            return _ok(payload)
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_get_issue(issue_id: int) -> str:
        """
        Get detailed information about a specific Redmine issue.
        Includes journals (history), children, relations, and watchers.

        Args:
            issue_id: The issue ID number
        """
        try:
            data = await _api_get(f"/issues/{issue_id}.json", {"include": "journals,children,relations,watchers,attachments"})
            issue = data.get("issue", {})

            # Build journal summaries
            journals = []
            for j in issue.get("journals", []):
                entry = {
                    "id": j.get("id"),
                    "user": (j.get("user") or {}).get("name"),
                    "created_on": j.get("created_on"),
                    "notes": j.get("notes") or None,
                    "details": [],
                }
                for d in j.get("details", []):
                    entry["details"].append({
                        "property": d.get("property"),
                        "name": d.get("name"),
                        "old_value": d.get("old_value"),
                        "new_value": d.get("new_value"),
                    })
                if entry["notes"] or entry["details"]:
                    journals.append(entry)

            children = [{"id": c.get("id"), "subject": c.get("subject"), "tracker": (c.get("tracker") or {}).get("name")} for c in issue.get("children", [])]
            relations = issue.get("relations", [])

            result = {
                **_issue_summary(issue),
                "description": issue.get("description"),
                "parent": issue.get("parent"),
                "children": children,
                "relations": relations,
                "journals": journals[-20:],  # last 20 journal entries
                "journals_total": len(journals),
            }
            return _ok({"issue": result})
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_create_issue(
        project_id: str,
        subject: str,
        description: str = "",
        tracker_id: int = 1,
        priority_id: int = 2,
        assigned_to_id: Optional[int] = None,
        fixed_version_id: Optional[int] = None,
        estimated_hours: Optional[float] = None,
        start_date: Optional[str] = None,
        due_date: Optional[str] = None,
        parent_issue_id: Optional[int] = None,
        category_id: Optional[int] = None,
    ) -> str:
        """
        Create a new Redmine issue with full field support.

        Args:
            project_id: Project ID or identifier
            subject: Issue subject/title
            description: Issue description (optional)
            tracker_id: Tracker ID (use redmine_list_trackers, default: 1=Bug)
            priority_id: Priority (1=Low,2=Normal,3=High,4=Urgent,5=Immediate, default: 2)
            assigned_to_id: User ID to assign to (optional)
            fixed_version_id: Version/sprint ID (optional)
            estimated_hours: Estimated hours (optional)
            start_date: Start date YYYY-MM-DD (optional)
            due_date: Due date YYYY-MM-DD (optional)
            parent_issue_id: Parent issue ID (optional)
            category_id: Category ID (optional)
        """
        try:
            pid = await _resolve_project_id(project_id)
            issue_data: dict[str, Any] = {
                "project_id": pid or project_id,
                "subject": subject,
                "description": description,
                "tracker_id": tracker_id,
                "priority_id": priority_id,
            }
            if assigned_to_id:
                issue_data["assigned_to_id"] = assigned_to_id
            if fixed_version_id:
                issue_data["fixed_version_id"] = fixed_version_id
            if estimated_hours is not None:
                issue_data["estimated_hours"] = estimated_hours
            if start_date:
                issue_data["start_date"] = start_date
            if due_date:
                issue_data["due_date"] = due_date
            if parent_issue_id:
                issue_data["parent_issue_id"] = parent_issue_id
            if category_id:
                issue_data["category_id"] = category_id

            data = await _api_post("/issues.json", {"issue": issue_data})
            issue = data.get("issue", {})
            return _ok({
                "message": f"Issue #{issue.get('id')} created successfully",
                "issue": _issue_summary(issue),
            })
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_update_issue(
        issue_id: int,
        subject: Optional[str] = None,
        description: Optional[str] = None,
        status_id: Optional[int] = None,
        priority_id: Optional[int] = None,
        tracker_id: Optional[int] = None,
        assigned_to_id: Optional[int] = None,
        fixed_version_id: Optional[int] = None,
        done_ratio: Optional[int] = None,
        estimated_hours: Optional[float] = None,
        start_date: Optional[str] = None,
        due_date: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> str:
        """
        Update an existing Redmine issue.

        Args:
            issue_id: The issue ID to update
            subject: New subject (optional)
            description: New description (optional)
            status_id: New status ID (use redmine_list_statuses to find IDs, optional)
            priority_id: New priority ID (optional)
            tracker_id: New tracker ID (optional)
            assigned_to_id: New assignee user ID (optional)
            fixed_version_id: New version/sprint ID (optional)
            done_ratio: Completion percentage 0-100 (optional)
            estimated_hours: Estimated hours (optional)
            start_date: Start date YYYY-MM-DD (optional)
            due_date: Due date YYYY-MM-DD (optional)
            notes: Comment/note to add (optional)
        """
        try:
            fields: dict[str, Any] = {}
            if subject is not None:
                fields["subject"] = subject
            if description is not None:
                fields["description"] = description
            if status_id is not None:
                fields["status_id"] = status_id
            if priority_id is not None:
                fields["priority_id"] = priority_id
            if tracker_id is not None:
                fields["tracker_id"] = tracker_id
            if assigned_to_id is not None:
                fields["assigned_to_id"] = assigned_to_id
            if fixed_version_id is not None:
                fields["fixed_version_id"] = fixed_version_id
            if done_ratio is not None:
                fields["done_ratio"] = done_ratio
            if estimated_hours is not None:
                fields["estimated_hours"] = estimated_hours
            if start_date is not None:
                fields["start_date"] = start_date
            if due_date is not None:
                fields["due_date"] = due_date
            if notes is not None:
                fields["notes"] = notes

            await _api_put(f"/issues/{issue_id}.json", {"issue": fields})
            return _ok({"message": f"Issue #{issue_id} updated successfully"})
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_delete_issue(issue_id: int) -> str:
        """
        Delete a Redmine issue permanently.

        Args:
            issue_id: The issue ID to delete
        """
        try:
            await _api_delete(f"/issues/{issue_id}.json")
            return _ok({"message": f"Issue #{issue_id} deleted successfully"})
        except Exception as e:
            return _err(str(e))

    # ===================================================================
    # ANALYTICS TOOLS
    # ===================================================================

    @mcp.tool()
    async def redmine_sprint_analytics(
        project_id: str,
        version_id: Optional[int] = None,
        version_name: Optional[str] = None,
    ) -> str:
        """
        Complete sprint/iteration analytics. Answers: How many stories committed,
        completed, remaining, in-progress, blocked? Sprint burndown status?
        Sprint spillover from last sprint?

        Args:
            project_id: Project ID or identifier (e.g. '6' or 'ncel')
            version_id: Specific version/sprint ID (optional - auto-detects current sprint if omitted)
            version_name: Sprint name to search for (optional, used if version_id not given)
        """
        try:
            pid = await _resolve_project_id(project_id)
            if pid is None:
                return _err(f"Could not resolve project: {project_id}")

            # Resolve version
            target_version = None
            versions = await _list_versions(pid)

            if version_id:
                target_version = next((v for v in versions if v["id"] == version_id), None)
            elif version_name:
                needle = version_name.lower()
                target_version = next((v for v in versions if needle in v.get("name", "").lower()), None)
            else:
                # Auto-detect: find the open version with nearest due date
                target_version = await _find_active_version(pid)

            if not target_version:
                return _err(f"No matching version/sprint found. Use redmine_list_versions to see available versions for project {pid}.")

            vid = target_version["id"]
            vname = target_version.get("name", "Unknown")

            # Fetch ALL issues in this sprint
            issues = await _fetch_all_issues({"project_id": pid, "fixed_version_id": vid, "status_id": "*"})

            # Fetch statuses to know which are "closed"
            status_data = await _api_get("/issue_statuses.json")
            closed_status_ids = {s["id"] for s in status_data.get("issue_statuses", []) if s.get("is_closed")}

            total = len(issues)
            completed = 0
            in_progress = 0
            blocked = 0
            new_count = 0
            total_estimated = 0.0
            total_spent = 0.0

            by_tracker: dict[str, int] = {}
            by_status: dict[str, int] = {}
            by_priority: dict[str, int] = {}

            for i in issues:
                sid = (i.get("status") or {}).get("id", 0)
                sname = (i.get("status") or {}).get("name", "Unknown")
                tname = (i.get("tracker") or {}).get("name", "Unknown")
                pname = (i.get("priority") or {}).get("name", "Unknown")

                by_status[sname] = by_status.get(sname, 0) + 1
                by_tracker[tname] = by_tracker.get(tname, 0) + 1
                by_priority[pname] = by_priority.get(pname, 0) + 1

                if sid in closed_status_ids:
                    completed += 1
                elif sname.lower() in ("in progress", "in_progress"):
                    in_progress += 1
                elif sname.lower() in ("new", "backlog"):
                    new_count += 1
                elif sname.lower() in ("feedback", "blocked"):
                    blocked += 1

                eh = i.get("estimated_hours")
                if eh:
                    total_estimated += float(eh)
                sh = i.get("spent_hours")
                if sh:
                    total_spent += float(sh)

            remaining = total - completed
            pct = round((completed / total * 100) if total > 0 else 0, 1)

            # Spillover: find the previous version (closed, most recent)
            closed_versions = [v for v in versions if v.get("status") == "closed"]
            closed_versions.sort(key=lambda v: v.get("updated_on", ""), reverse=True)
            spillover_count = 0
            prev_version_name = None
            if closed_versions:
                prev_v = closed_versions[0]
                prev_version_name = prev_v.get("name")
                # Count issues from prev version that are still open
                prev_issues = await _fetch_all_issues({
                    "project_id": pid,
                    "fixed_version_id": prev_v["id"],
                    "status_id": "open",
                })
                spillover_count = len(prev_issues)

            return _ok({
                "sprint": {
                    "name": vname,
                    "version_id": vid,
                    "status": target_version.get("status"),
                    "due_date": target_version.get("due_date"),
                },
                "metrics": {
                    "total_committed": total,
                    "completed": completed,
                    "remaining": remaining,
                    "in_progress": in_progress,
                    "blocked": blocked,
                    "new": new_count,
                    "completion_percentage": pct,
                    "total_estimated_hours": round(total_estimated, 1),
                    "total_spent_hours": round(total_spent, 1),
                },
                "breakdown_by_status": by_status,
                "breakdown_by_tracker": by_tracker,
                "breakdown_by_priority": by_priority,
                "spillover": {
                    "from_previous_sprint": prev_version_name,
                    "open_issues_from_previous": spillover_count,
                },
                "burndown_assessment": (
                    "on_track" if pct >= 60 else ("at_risk" if pct >= 30 else "behind")
                ),
            })
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_backlog_analytics(project_id: Optional[str] = None) -> str:
        """
        Backlog metrics: total size, high-priority open items, percentage unestimated,
        items added/closed this month, backlog aging.

        Args:
            project_id: Project ID or identifier (optional, all projects if omitted)
        """
        try:
            params: dict[str, Any] = {"status_id": "open"}
            pid = None
            if project_id:
                pid = await _resolve_project_id(project_id)
                if pid:
                    params["project_id"] = pid

            # Total open
            total_open = await _get_total_count(params)

            # High priority open (priority_id >= 3)
            high = await _get_total_count({**params, "priority_id": 3})
            urgent = await _get_total_count({**params, "priority_id": 4})
            immediate = await _get_total_count({**params, "priority_id": 5})
            total_high = high + urgent + immediate

            # Fetch open issues to compute unestimated % and aging
            open_issues = await _fetch_all_issues(params, max_issues=2000)
            unestimated = sum(1 for i in open_issues if not i.get("estimated_hours"))
            pct_unestimated = round((unestimated / len(open_issues) * 100) if open_issues else 0, 1)

            # Aging (days since creation)
            now = datetime.utcnow()
            ages = []
            for i in open_issues:
                co = i.get("created_on")
                if co:
                    try:
                        created = datetime.fromisoformat(co.replace("Z", "+00:00")).replace(tzinfo=None)
                        ages.append((now - created).days)
                    except Exception:
                        pass
            avg_age = round(sum(ages) / len(ages), 1) if ages else 0
            max_age = max(ages) if ages else 0

            # Monthly trends
            month_start = now.replace(day=1).strftime("%Y-%m-%d")
            base = {"project_id": pid} if pid else {}
            created_this_month = await _get_total_count({**base, "created_on": f">={month_start}", "status_id": "*"})
            closed_this_month = await _get_total_count({**base, "closed_on": f">={month_start}", "status_id": "*"})

            return _ok({
                "backlog": {
                    "total_open": total_open,
                    "high_priority_open": total_high,
                    "high": high,
                    "urgent": urgent,
                    "immediate": immediate,
                    "unestimated_count": unestimated,
                    "unestimated_percentage": pct_unestimated,
                },
                "aging": {
                    "average_days_open": avg_age,
                    "max_days_open": max_age,
                },
                "monthly_activity": {
                    "month": now.strftime("%B %Y"),
                    "created_this_month": created_this_month,
                    "closed_this_month": closed_this_month,
                    "net_change": created_this_month - closed_this_month,
                },
                "project_id": pid,
            })
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_team_workload(project_id: Optional[str] = None) -> str:
        """
        Team workload distribution: tasks assigned per member, overloaded members,
        unassigned issues. Uses full pagination for accurate counts.

        Args:
            project_id: Project ID or identifier (optional)
        """
        try:
            params: dict[str, Any] = {"status_id": "open"}
            pid = None
            if project_id:
                pid = await _resolve_project_id(project_id)
                if pid:
                    params["project_id"] = pid

            # Fetch ALL open issues (full pagination)
            issues = await _fetch_all_issues(params)

            workload: dict[str, dict] = {}
            unassigned = 0

            for i in issues:
                assignee = i.get("assigned_to")
                if assignee:
                    name = assignee.get("name", "Unknown")
                    aid = assignee.get("id")
                    if name not in workload:
                        workload[name] = {"user_id": aid, "total": 0, "high_priority": 0, "trackers": {}}
                    workload[name]["total"] += 1
                    p_id = (i.get("priority") or {}).get("id", 2)
                    if p_id >= 3:
                        workload[name]["high_priority"] += 1
                    tname = (i.get("tracker") or {}).get("name", "Other")
                    workload[name]["trackers"][tname] = workload[name]["trackers"].get(tname, 0) + 1
                else:
                    unassigned += 1

            # Sort by total descending
            sorted_workload = dict(sorted(workload.items(), key=lambda x: x[1]["total"], reverse=True))

            # Detect overloaded (>10 open tasks)
            overloaded = {k: v["total"] for k, v in sorted_workload.items() if v["total"] > 10}

            return _ok({
                "total_open_issues": len(issues),
                "unassigned_issues": unassigned,
                "team_size": len(workload),
                "workload_by_member": sorted_workload,
                "overloaded_members": overloaded,
                "project_id": pid,
            })
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_quality_metrics(project_id: Optional[str] = None) -> str:
        """
        Bug/quality analytics: open bugs, critical bugs, bug-to-story ratio,
        average bug resolution time, recent bugs.

        Args:
            project_id: Project ID or identifier (optional)
        """
        try:
            base: dict[str, Any] = {}
            pid = None
            if project_id:
                pid = await _resolve_project_id(project_id)
                if pid:
                    base["project_id"] = pid

            # Get tracker IDs dynamically
            tracker_data = await _api_get("/trackers.json")
            bug_tracker_id = None
            story_tracker_ids = []
            feature_tracker_ids = []
            for t in tracker_data.get("trackers", []):
                tname = t["name"].lower()
                if tname == "bug":
                    bug_tracker_id = t["id"]
                elif tname in ("story", "user story"):
                    story_tracker_ids.append(t["id"])
                elif tname == "feature":
                    feature_tracker_ids.append(t["id"])

            if not bug_tracker_id:
                return _err("No 'Bug' tracker found in Redmine. Check your tracker configuration.")

            # Open bugs
            open_bugs = await _get_total_count({**base, "status_id": "open", "tracker_id": bug_tracker_id})
            total_bugs = await _get_total_count({**base, "status_id": "*", "tracker_id": bug_tracker_id})
            closed_bugs = total_bugs - open_bugs

            # Critical / high severity bugs
            high_bugs = await _get_total_count({**base, "status_id": "open", "tracker_id": bug_tracker_id, "priority_id": 3})
            urgent_bugs = await _get_total_count({**base, "status_id": "open", "tracker_id": bug_tracker_id, "priority_id": 4})
            immediate_bugs = await _get_total_count({**base, "status_id": "open", "tracker_id": bug_tracker_id, "priority_id": 5})

            # Bug-to-story ratio
            total_stories = 0
            for sid in story_tracker_ids:
                total_stories += await _get_total_count({**base, "status_id": "*", "tracker_id": sid})
            # If no story tracker, try feature
            if total_stories == 0:
                for fid in feature_tracker_ids:
                    total_stories += await _get_total_count({**base, "status_id": "*", "tracker_id": fid})
            ratio = round(total_bugs / total_stories, 2) if total_stories > 0 else None

            # Average bug resolution time (from recently closed bugs)
            closed_bug_issues = await _fetch_all_issues(
                {**base, "status_id": "closed", "tracker_id": bug_tracker_id, "sort": "closed_on:desc"},
                max_issues=200,
            )
            resolution_times = []
            for b in closed_bug_issues:
                co = b.get("created_on")
                cl = b.get("closed_on")
                if co and cl:
                    try:
                        created = datetime.fromisoformat(co.replace("Z", "+00:00")).replace(tzinfo=None)
                        closed = datetime.fromisoformat(cl.replace("Z", "+00:00")).replace(tzinfo=None)
                        resolution_times.append((closed - created).total_seconds() / 86400)
                    except Exception:
                        pass
            avg_resolution_days = round(sum(resolution_times) / len(resolution_times), 1) if resolution_times else None

            # Recent bugs (last 7 days)
            week_ago = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%d")
            recent_bugs = await _get_total_count({**base, "tracker_id": bug_tracker_id, "created_on": f">={week_ago}", "status_id": "*"})

            return _ok({
                "bug_metrics": {
                    "open_bugs": open_bugs,
                    "closed_bugs": closed_bugs,
                    "total_bugs": total_bugs,
                    "critical_open": {
                        "high": high_bugs,
                        "urgent": urgent_bugs,
                        "immediate": immediate_bugs,
                        "total_critical": high_bugs + urgent_bugs + immediate_bugs,
                    },
                    "bug_to_story_ratio": ratio,
                    "total_stories_or_features": total_stories,
                    "avg_resolution_time_days": avg_resolution_days,
                    "bugs_created_last_7_days": recent_bugs,
                },
                "project_id": pid,
            })
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_cycle_time(project_id: Optional[str] = None, sample_size: int = 50) -> str:
        """
        Cycle time and lead time metrics. Uses journal history for accurate
        'In Progress -> Closed' cycle time. Also detects re-opened tickets.

        Args:
            project_id: Project ID or identifier (optional)
            sample_size: Number of recently closed issues to analyze (default: 50)
        """
        try:
            base: dict[str, Any] = {"status_id": "closed", "sort": "closed_on:desc"}
            pid = None
            if project_id:
                pid = await _resolve_project_id(project_id)
                if pid:
                    base["project_id"] = pid

            # Fetch recently closed issues
            closed_issues = await _fetch_all_issues(base, max_issues=sample_size)

            lead_times = []  # created -> closed
            cycle_times = []  # in_progress -> closed
            reopened_count = 0
            url, key = _cfg()

            for issue in closed_issues:
                co = issue.get("created_on")
                cl = issue.get("closed_on")

                # Lead time
                if co and cl:
                    try:
                        created = datetime.fromisoformat(co.replace("Z", "+00:00")).replace(tzinfo=None)
                        closed = datetime.fromisoformat(cl.replace("Z", "+00:00")).replace(tzinfo=None)
                        lead_times.append((closed - created).total_seconds() / 86400)
                    except Exception:
                        pass

                # Fetch journals for cycle time and re-open detection
                try:
                    idata = await _api_get(f"/issues/{issue['id']}.json", {"include": "journals"})
                    journals = idata.get("issue", {}).get("journals", [])
                    in_progress_at = None
                    was_reopened = False

                    for j in journals:
                        for d in j.get("details", []):
                            if d.get("name") == "status_id":
                                new_val = str(d.get("new_value", ""))
                                old_val = str(d.get("old_value", ""))
                                # Detect transition TO in-progress (status 2 commonly)
                                if new_val == "2" and in_progress_at is None:
                                    in_progress_at = j.get("created_on")
                                # Detect re-open: moving from a closed status back to open
                                if old_val == "5" and new_val != "5":
                                    was_reopened = True

                    if was_reopened:
                        reopened_count += 1

                    if in_progress_at and cl:
                        try:
                            ip = datetime.fromisoformat(in_progress_at.replace("Z", "+00:00")).replace(tzinfo=None)
                            closed_dt = datetime.fromisoformat(cl.replace("Z", "+00:00")).replace(tzinfo=None)
                            ct = (closed_dt - ip).total_seconds() / 86400
                            if ct >= 0:
                                cycle_times.append(ct)
                        except Exception:
                            pass
                except Exception:
                    pass  # Skip journal fetch failures

            avg_lead = round(sum(lead_times) / len(lead_times), 1) if lead_times else None
            avg_cycle = round(sum(cycle_times) / len(cycle_times), 1) if cycle_times else None
            median_lead = round(sorted(lead_times)[len(lead_times)//2], 1) if lead_times else None
            median_cycle = round(sorted(cycle_times)[len(cycle_times)//2], 1) if cycle_times else None

            return _ok({
                "sample_size": len(closed_issues),
                "lead_time": {
                    "average_days": avg_lead,
                    "median_days": median_lead,
                    "description": "Time from issue creation to closure",
                },
                "cycle_time": {
                    "average_days": avg_cycle,
                    "median_days": median_cycle,
                    "samples": len(cycle_times),
                    "description": "Time from In Progress to Closed (based on journal history)",
                },
                "reopened_tickets": {
                    "count": reopened_count,
                    "percentage": round(reopened_count / len(closed_issues) * 100, 1) if closed_issues else 0,
                },
                "project_id": pid,
            })
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_release_status(
        project_id: str,
        version_id: Optional[int] = None,
        version_name: Optional[str] = None,
    ) -> str:
        """
        Release/version completion status. Shows features completed, scope done %,
        unresolved issues tied to the release.

        Args:
            project_id: Project ID or identifier
            version_id: Specific version ID (optional - shows all open versions if omitted)
            version_name: Version name to search for (optional)
        """
        try:
            pid = await _resolve_project_id(project_id)
            if pid is None:
                return _err(f"Could not resolve project: {project_id}")

            versions = await _list_versions(pid)

            targets = []
            if version_id:
                targets = [v for v in versions if v["id"] == version_id]
            elif version_name:
                needle = version_name.lower()
                targets = [v for v in versions if needle in v.get("name", "").lower()]
            else:
                targets = [v for v in versions if v.get("status") == "open"]

            if not targets:
                return _err("No matching versions found.")

            # Fetch statuses for closed detection
            status_data = await _api_get("/issue_statuses.json")
            closed_status_ids = {s["id"] for s in status_data.get("issue_statuses", []) if s.get("is_closed")}

            results = []
            for v in targets:
                vid = v["id"]
                issues = await _fetch_all_issues({"project_id": pid, "fixed_version_id": vid, "status_id": "*"})
                total = len(issues)
                closed = sum(1 for i in issues if (i.get("status") or {}).get("id") in closed_status_ids)
                open_count = total - closed
                pct = round((closed / total * 100) if total > 0 else 0, 1)

                # Count by tracker
                by_tracker: dict[str, dict] = {}
                for i in issues:
                    tname = (i.get("tracker") or {}).get("name", "Other")
                    if tname not in by_tracker:
                        by_tracker[tname] = {"total": 0, "closed": 0}
                    by_tracker[tname]["total"] += 1
                    if (i.get("status") or {}).get("id") in closed_status_ids:
                        by_tracker[tname]["closed"] += 1

                results.append({
                    "version_id": vid,
                    "version_name": v.get("name"),
                    "version_status": v.get("status"),
                    "due_date": v.get("due_date"),
                    "total_issues": total,
                    "closed_issues": closed,
                    "open_issues": open_count,
                    "completion_percentage": pct,
                    "by_tracker": by_tracker,
                })

            return _ok({"project_id": pid, "releases": results})
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_velocity_trend(
        project_id: str,
        sprints: int = 5,
    ) -> str:
        """
        Velocity trend over last N closed sprints. Shows completed issues
        and estimated hours per sprint in chronological order.
        Indicates if velocity is stable, increasing, or decreasing.

        Args:
            project_id: Project ID or identifier
            sprints: Number of recent sprints to analyze (default: 5)
        """
        try:
            pid = await _resolve_project_id(project_id)
            if pid is None:
                return _err(f"Could not resolve project: {project_id}")

            versions = await _list_versions(pid)
            # Get closed versions sorted by due_date or updated_on (most recent last)
            closed_versions = [v for v in versions if v.get("status") == "closed"]

            def version_date(v):
                dd = v.get("due_date") or v.get("updated_on", "")
                try:
                    return datetime.fromisoformat(dd.replace("Z", "+00:00").replace("T", " ").split("+")[0])
                except Exception:
                    return datetime(1970, 1, 1)

            closed_versions.sort(key=version_date)
            recent = closed_versions[-sprints:] if len(closed_versions) >= sprints else closed_versions

            # Also include current open sprint if there is one
            open_versions = [v for v in versions if v.get("status") == "open"]

            # Fetch statuses for closed detection
            status_data = await _api_get("/issue_statuses.json")
            closed_status_ids = {s["id"] for s in status_data.get("issue_statuses", []) if s.get("is_closed")}

            velocity_data = []
            for v in recent:
                issues = await _fetch_all_issues({"project_id": pid, "fixed_version_id": v["id"], "status_id": "*"})
                completed = [i for i in issues if (i.get("status") or {}).get("id") in closed_status_ids]
                total_est = sum(float(i.get("estimated_hours") or 0) for i in completed)
                velocity_data.append({
                    "sprint": v.get("name"),
                    "version_id": v["id"],
                    "due_date": v.get("due_date"),
                    "completed_issues": len(completed),
                    "total_issues": len(issues),
                    "completed_estimated_hours": round(total_est, 1),
                })

            # Trend analysis
            if len(velocity_data) >= 2:
                vals = [v["completed_issues"] for v in velocity_data]
                first_half = sum(vals[:len(vals)//2]) / max(len(vals)//2, 1)
                second_half = sum(vals[len(vals)//2:]) / max(len(vals) - len(vals)//2, 1)
                if second_half > first_half * 1.1:
                    trend = "increasing"
                elif second_half < first_half * 0.9:
                    trend = "decreasing"
                else:
                    trend = "stable"
                avg = round(sum(vals) / len(vals), 1)
            else:
                trend = "insufficient_data"
                avg = velocity_data[0]["completed_issues"] if velocity_data else 0

            return _ok({
                "project_id": pid,
                "sprints_analyzed": len(velocity_data),
                "velocity_trend": trend,
                "average_velocity": avg,
                "per_sprint": velocity_data,
            })
        except Exception as e:
            return _err(str(e))

    @mcp.tool()
    async def redmine_throughput(
        project_id: Optional[str] = None,
        weeks: int = 4,
    ) -> str:
        """
        Throughput analysis: created vs closed tickets per week.
        Shows if you're closing more than creating, weekly breakdown.

        Args:
            project_id: Project ID or identifier (optional)
            weeks: Number of weeks to analyze (default: 4)
        """
        try:
            base: dict[str, Any] = {"status_id": "*"}
            pid = None
            if project_id:
                pid = await _resolve_project_id(project_id)
                if pid:
                    base["project_id"] = pid

            now = datetime.utcnow()
            weekly_data = []

            for w in range(weeks):
                week_end = now - timedelta(days=w * 7)
                week_start = week_end - timedelta(days=7)
                ws = week_start.strftime("%Y-%m-%d")
                we = week_end.strftime("%Y-%m-%d")

                created = await _get_total_count({
                    **base,
                    "created_on": f"><{ws}|{we}",
                })
                closed = await _get_total_count({
                    **base,
                    "closed_on": f"><{ws}|{we}",
                })

                weekly_data.append({
                    "week": f"{ws} to {we}",
                    "created": created,
                    "closed": closed,
                    "net": closed - created,
                })

            # Reverse so oldest is first
            weekly_data.reverse()

            total_created = sum(w["created"] for w in weekly_data)
            total_closed = sum(w["closed"] for w in weekly_data)

            return _ok({
                "project_id": pid,
                "period_weeks": weeks,
                "total_created": total_created,
                "total_closed": total_closed,
                "net_throughput": total_closed - total_created,
                "trend": "positive" if total_closed >= total_created else "negative",
                "avg_created_per_week": round(total_created / weeks, 1),
                "avg_closed_per_week": round(total_closed / weeks, 1),
                "weekly_breakdown": weekly_data,
            })
        except Exception as e:
            return _err(str(e))
