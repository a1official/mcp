# Sprint Analytics - Fixed and Explained

## How Sprints Work in Your Redmine

### Sprint = Version (Fixed Version)
In Redmine, sprints are called "Versions". Issues are assigned to sprints using the `fixed_version_id` field.

### Your Current Sprint
- **Name**: Week - 7
- **ID**: 30
- **Due Date**: 2026-02-15
- **Total Issues**: 40 issues
- **Status**: 100% complete (all 40 closed)

## Sprint Calculation Method

### 1. Total Committed Issues
```
API: GET /issues.json?project_id=6&fixed_version_id=30&limit=1
Returns: {"total_count": 40}
```
This counts ALL issues assigned to the sprint (bugs, features, stories, etc.)

### 2. Completed Issues
```
API: GET /issues.json?project_id=6&fixed_version_id=30&status_id=5&limit=1
Returns: {"total_count": 40}
```
Status ID 5 = "Closed" status

### 3. Remaining Issues
```
Remaining = Total - Completed
Remaining = 40 - 40 = 0
```

### 4. Completion Percentage
```
Completion % = (Completed / Total) * 100
Completion % = (40 / 40) * 100 = 100%
```

### 5. Burndown Status
```
if completion_pct >= 50:
    status = "on_track"
else:
    status = "behind"
```

## What Was Fixed

### Before (Wrong)
```python
# Only counted "Story" tracker
filters = {"tracker_id": 4}  # Story tracker only
total = await get_count(project_id, **filters)
# Result: 1 story (missed 39 other issues!)
```

### After (Correct)
```python
# Counts ALL issues in sprint
filters = {}  # No tracker filter
if version_id:
    filters["fixed_version_id"] = version_id
total = await get_count(project_id, **filters)
# Result: 40 issues (correct!)
```

## Test Results

### Week - 7 Sprint (ID: 30)
```
Committed Issues: 40
Completed: 40
Remaining: 0
Completion: 100%
Status: on_track
```

## How to Use

### Get Sprint Metrics
```python
from redmine_analytics_v2 import sprint_completion_status

# By version ID
result = await sprint_completion_status("ncel", version_id=30)

# Result
{
    "success": True,
    "sprint_status": {
        "total_committed": 40,
        "completed": 40,
        "remaining": 0,
        "completion_percentage": 100.0,
        "burndown_status": "on_track"
    }
}
```

### Through LLM
Ask: "What is the sprint status for Week - 7?"

The LLM will:
1. Look up version ID for "Week - 7" (ID: 30)
2. Call `sprint_completion_status("ncel", version_id=30)`
3. Format the response: "Week - 7 sprint is 100% complete with all 40 issues closed"

## Sprint Status Meanings

### Burndown Status
- **on_track**: >= 50% complete
- **behind**: < 50% complete

### Issue States
- **Open**: New, In Progress, Resolved, Feedback, Backlog
- **Closed**: Closed, Rejected, Cancelled

### Completion Calculation
Only issues with status "Closed" (ID: 5) count as completed. "Resolved" (ID: 3) is still considered open until it's closed.

## Additional Sprint Metrics

### Issues by Status
```python
new = await get_count(project_id, fixed_version_id=30, status_id=1)
in_progress = await get_count(project_id, fixed_version_id=30, status_id=2)
resolved = await get_count(project_id, fixed_version_id=30, status_id=3)
closed = await get_count(project_id, fixed_version_id=30, status_id=5)
```

### Issues by Tracker
```python
bugs = await get_count(project_id, fixed_version_id=30, tracker_id=1)
features = await get_count(project_id, fixed_version_id=30, tracker_id=2)
stories = await get_count(project_id, fixed_version_id=30, tracker_id=4)
```

### Issues by Priority
```python
high = await get_count(project_id, fixed_version_id=30, priority_id=3)
urgent = await get_count(project_id, fixed_version_id=30, priority_id=4)
```

## Summary

✅ Sprint = Redmine Version
✅ Use `fixed_version_id` to filter by sprint
✅ Count ALL issues (not just stories)
✅ Closed status (ID: 5) = completed
✅ Week - 7 has 40 issues, 100% complete
✅ Functions updated and tested
