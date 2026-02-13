# How Sprint Calculation Works in Redmine

## What is a Sprint in Redmine?

In Redmine, sprints are represented by **Versions** (also called "Target Versions" or "Fixed Versions"). Each issue can be assigned to a version using the `fixed_version_id` field.

## Your Project Structure (NCEL)

### Current Sprint
- **Name**: Week - 7
- **ID**: 30
- **Due Date**: 2026-02-15
- **Total Issues**: 200 issues

### Previous Sprint
- **Name**: Week - 4
- **ID**: (need to find)
- **Issues**: 50 issues

## How Sprint Metrics Are Calculated

### 1. Sprint Committed (Total Issues in Sprint)
```python
# API Query
GET /issues.json?project_id=6&fixed_version_id=30&limit=1

# Returns
{
  "total_count": 200,  # This is the committed count
  "issues": [...]
}
```

**What it means**: All issues assigned to this version/sprint

### 2. Sprint Completion Status
```python
# Get completed issues (closed status)
GET /issues.json?project_id=6&fixed_version_id=30&status_id=5&limit=1

# Get total issues
GET /issues.json?project_id=6&fixed_version_id=30&limit=1

# Calculate
completed = closed_count
remaining = total_count - closed_count
completion_percentage = (completed / total) * 100
```

**Status Mapping**:
- **Open statuses**: New (1), In Progress (2), Resolved (3), Feedback (4), Backlog (7)
- **Closed statuses**: Closed (5), Rejected (6), Cancelled (8)

### 3. Sprint Burndown
The burndown shows how many issues remain over time:
- **Day 1**: 200 issues remaining
- **Day 5**: 150 issues remaining (50 completed)
- **Day 10**: 100 issues remaining (100 completed)
- **End**: 0 issues remaining (200 completed)

## Current Implementation Issue

The current `sprint_committed_stories()` function filters by `tracker_id=4` (Story tracker), but your sprint has mostly **Bugs** (tracker_id=1).

### Fix Needed

```python
# CURRENT (Wrong - only counts stories)
async def sprint_committed_stories(project_id, version_id):
    filters = {"tracker_id": TRACKER_MAP["story"]}  # Only stories!
    if version_id:
        filters["fixed_version_id"] = version_id
    total = await get_count(normalized_id, **filters)
    return {"committed_stories": total}

# FIXED (Correct - counts all issues)
async def sprint_committed_issues(project_id, version_id):
    filters = {}  # No tracker filter - count ALL issues
    if version_id:
        filters["fixed_version_id"] = version_id
    total = await get_count(normalized_id, **filters)
    return {"committed_issues": total}
```

## Correct Sprint Metrics for Week - 7

Based on the data:

### Total Committed
```
GET /issues.json?project_id=6&fixed_version_id=30&limit=1
Result: 200 issues
```

### By Status
```
New: X issues
In Progress: Y issues
Resolved: Z issues
Closed: W issues
```

### By Tracker
```
Bug: ~200 issues
Feature: 0 issues
Story: 1 issue
Support: 0 issues
```

### Completion Calculation
```
Open = New + In Progress + Resolved + Feedback + Backlog
Closed = Closed + Rejected + Cancelled

Completed = Closed count
Remaining = Open count
Completion % = (Closed / Total) * 100
```

## How to Use Sprint Analytics

### Option 1: Specify Version ID
```python
# Get metrics for specific sprint
result = await sprint_completion_status("ncel", version_id=30)
# Returns metrics for Week - 7 only
```

### Option 2: Auto-detect Current Sprint
```python
# Find current sprint by due date
versions = get_versions(project_id=6)
current = find_closest_due_date(versions)
result = await sprint_completion_status("ncel", version_id=current.id)
```

### Option 3: Use Sprint Name
```python
# Look up version by name
version_id = find_version_by_name("Week - 7")
result = await sprint_completion_status("ncel", version_id=version_id)
```

## Recommended Sprint Functions

### 1. Get Current Sprint
```python
async def get_current_sprint(project_id):
    """Find the active sprint (closest due date in future)"""
    versions = await get_versions(project_id)
    today = datetime.now().date()
    
    future = [v for v in versions if v.due_date >= today]
    if future:
        return min(future, key=lambda v: v.due_date)
    return None
```

### 2. Sprint Summary
```python
async def sprint_summary(project_id, version_id=None):
    """Complete sprint overview"""
    if not version_id:
        sprint = await get_current_sprint(project_id)
        version_id = sprint.id
    
    total = await get_count(project_id, fixed_version_id=version_id)
    closed = await get_count(project_id, fixed_version_id=version_id, status_id=5)
    in_progress = await get_count(project_id, fixed_version_id=version_id, status_id=2)
    
    return {
        "sprint_name": sprint.name,
        "total_committed": total,
        "completed": closed,
        "in_progress": in_progress,
        "remaining": total - closed,
        "completion_pct": (closed / total * 100) if total > 0 else 0
    }
```

### 3. Sprint Velocity
```python
async def sprint_velocity(project_id, num_sprints=5):
    """Average completion rate over last N sprints"""
    versions = await get_versions(project_id)
    completed_sprints = [v for v in versions if v.status == "closed"][-num_sprints:]
    
    velocities = []
    for sprint in completed_sprints:
        total = await get_count(project_id, fixed_version_id=sprint.id)
        closed = await get_count(project_id, fixed_version_id=sprint.id, status_id=5)
        velocities.append(closed)
    
    return {
        "avg_velocity": sum(velocities) / len(velocities),
        "velocities": velocities
    }
```

## Key Takeaways

1. **Sprint = Version** in Redmine
2. **Use `fixed_version_id`** to filter issues by sprint
3. **Don't filter by tracker** unless specifically needed (your sprints have bugs, not stories)
4. **Closed status** (id=5) indicates completion
5. **Current sprint** = version with closest future due date
6. **Sprint velocity** = average issues completed per sprint

## Next Steps

1. Update `sprint_committed_stories()` to count ALL issues, not just stories
2. Add `get_current_sprint()` helper function
3. Add sprint name lookup (by name instead of ID)
4. Test with Week - 7 (200 issues)
5. Validate completion calculations
