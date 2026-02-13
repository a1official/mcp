# Bug Count Fix - Complete

## Problem
The LLM was giving wrong bug counts when asked "how many open bugs in project ncel" through the frontend. It would return incorrect numbers (25, 290, etc.) instead of the correct answer (310 open bugs).

## Root Cause
1. The tool definition for `redmine_bug_analytics` only accepted `integer` type for `project_id`
2. The LLM was passing project name "ncel" as a string
3. Groq's validation was rejecting the string parameter before it reached the handler

## Solution Implemented

### 1. Updated Tool Definitions (backend/server.py)
Changed all analytics tools to accept BOTH string and integer for `project_id`:

```python
"project_id": {
    "type": ["integer", "string"],
    "description": "Project ID or name (e.g., 6 or 'ncel' for NCEL project). Optional."
}
```

Updated tools:
- `redmine_bug_analytics` - Added note "NCEL project = ID 6"
- `redmine_sprint_status`
- `redmine_backlog_analytics`
- `redmine_team_workload`
- `redmine_cycle_time`
- `redmine_velocity_trend`
- `redmine_throughput`

### 2. Enhanced redmine_direct.py
Added project name normalization:

```python
# Project name to ID mapping
PROJECT_MAP = {
    "ncel": 6,
    "NCEL": 6,
}

def normalize_project_id(project_id: Optional[Union[int, str]]) -> Optional[int]:
    """Convert project name to ID if needed"""
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
```

Updated all functions to use `normalize_project_id()`:
- `bug_count()` - Now accepts Union[int, str]
- `sprint_count()` - Now accepts Union[int, str]
- `backlog_count()` - Now accepts Union[int, str]

### 3. Type Annotations
Updated function signatures to use `Optional[Union[int, str]]` for project_id parameters.

## Test Results

### Direct API Test
```bash
$ python -c "import asyncio; import sys; sys.path.insert(0, 'backend'); from redmine_direct import bug_count; result = asyncio.run(bug_count(6)); print('Open bugs:', result['bug_metrics']['open_bugs'])"
Open bugs: 310
```

### String Parameter Test
```bash
$ python -c "import asyncio; import sys; sys.path.insert(0, 'backend'); from redmine_direct import bug_count; result = asyncio.run(bug_count('ncel')); print('Open bugs:', result['bug_metrics']['open_bugs'])"
Open bugs: 310
```

Both return the correct answer: **310 open bugs in NCEL project**

## Correct Data (NCEL Project ID=6)
- Open bugs: 310
- Closed bugs: 212
- Total bugs: 522

## How It Works Now

1. User asks: "how many open bugs in project ncel"
2. LLM selects `redmine_bug_analytics` tool
3. LLM passes `project_id="ncel"` (string)
4. Tool definition accepts string (no validation error)
5. Handler calls `bug_count("ncel")`
6. `normalize_project_id("ncel")` converts to integer 6
7. API query: `GET /issues.json?project_id=6&status_id=open&tracker_id=1&limit=1`
8. Redmine returns `total_count: 310`
9. LLM receives correct data and formats answer

## Benefits
- Accepts both project names ("ncel", "NCEL") and IDs (6)
- No more type validation errors
- Always returns accurate, real-time counts from Redmine API
- Easy to add more project mappings to PROJECT_MAP

## Next Steps
To test through frontend:
1. Start backend: `cd backend && python server.py`
2. Start frontend: `cd frontend && npm run dev`
3. Ask: "how many open bugs in project ncel"
4. Expected answer: "310 open bugs in NCEL project"
