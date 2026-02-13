# Redmine Analytics Guide

## Quick Start

Run the test suite to see all analytics in action:

```bash
python test_redmine_analytics.py
```

## Available Analytics

### 📅 Sprint / Iteration Status
```python
sprint_status(version_id=None)
```
**Answers:**
- How many stories are committed in the current sprint?
- How many stories are completed vs remaining?
- How many tasks are in "In Progress" state?
- How many tasks are blocked?
- What is the completion percentage?

### 📊 Backlog & Scope
```python
backlog_metrics(project_id=None)
```
**Answers:**
- What is the total backlog size?
- How many high-priority items are still open?
- What percentage of backlog is unestimated?
- What is the backlog aging (how long items stay open)?

### 👥 Team Performance / Workload
```python
team_workload(project_id=None)
cycle_time_metrics(project_id=None)
```
**Answers:**
- How many tasks are assigned per team member?
- Are any team members overloaded?
- What is the average cycle time per ticket?
- What is the average lead time from creation to closure?

### 🐞 Quality & Defects
```python
bug_metrics(project_id=None)
```
**Answers:**
- How many open bugs exist?
- How many critical / high-severity bugs are open?
- What is the bug-to-story ratio?
- What is the average bug resolution time?

### 🚀 Release & Delivery
```python
release_status(version_id=None)
```
**Answers:**
- How many features are completed for the upcoming release?
- What percentage of release scope is done?
- How many unresolved issues are tied to the release?
- What is the release due date?

### 📈 Trends & Predictability
```python
velocity_trend(project_id=None, sprints=5)
throughput_analysis(project_id=None, weeks=4)
```
**Answers:**
- Is velocity stable, increasing, or decreasing?
- Are we closing more tickets than we're creating?
- What is the throughput per week?
- What is the average velocity over last N sprints?

## Example Output

```
============================================================
REDMINE ANALYTICS TEST SUITE
============================================================

📅 SPRINT STATUS
  Committed: 45 stories
  Completed: 32 stories
  Remaining: 13 stories
  In Progress: 8 tasks
  Blocked: 2 tasks
  Completion: 71.1%

📊 BACKLOG METRICS
  Total backlog: 127 items
  High priority: 23 items (18.1%)
  Unestimated: 45 items (35.4%)
  Average age: 42.3 days

👥 TEAM WORKLOAD
  John Doe: 15 tasks
  Jane Smith: 12 tasks
  Bob Johnson: 8 tasks
  Unassigned: 5 tasks
  ⚠️  Overloaded: John Doe

⏱️  CYCLE TIME METRICS
  Average lead time: 12.5 days
  Average cycle time: 3.2 days

🐞 BUG METRICS
  Total bugs: 34
  Open bugs: 12
  Critical/High bugs: 3
  Bug-to-story ratio: 0.42
  Avg resolution time: 5.8 days

🚀 RELEASE STATUS: v2.0
  Total scope: 28 items
  Completed: 19 items
  Unresolved: 9 items
  Progress: 67.9%
  Due date: 2025-02-28

📈 VELOCITY TREND (Last 5 sprints)
  Sprint 5: 45.0 hours
  Sprint 4: 42.0 hours
  Sprint 3: 48.0 hours
  Sprint 2: 40.0 hours
  Sprint 1: 38.0 hours
  Trend: increasing
  Average: 42.6 hours

📊 THROUGHPUT ANALYSIS (Last 4 weeks)
  Created: 32 tickets
  Closed: 45 tickets
  Net: 13 tickets
  Status: ✅ Closing more

============================================================
✅ ALL TESTS COMPLETED
============================================================
```

## Integration with Chat UI

Users can ask natural language questions like:
- "How many stories are in the current sprint?"
- "Show me team workload"
- "What's our bug count?"
- "Is velocity increasing or decreasing?"
- "Are we ahead or behind schedule?"

The LLM will call the appropriate Redmine tools and present the data in the custom UI components.

## Next Steps

To make these available in the chat interface:
1. Add the analytics functions to `backend/server.py`
2. Register them as MCP tools
3. Update the UI to render analytics data beautifully
4. Add charts and visualizations

## Requirements

- Redmine API access
- Python 3.8+
- `requests` library
- `.env` file with REDMINE_URL and REDMINE_API_KEY
