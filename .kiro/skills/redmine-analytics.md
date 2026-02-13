---
name: Redmine Analytics Expert
trigger_keywords: [redmine, sprint, backlog, velocity, bugs, team, workload, analytics, metrics, release, throughput]
when_to_use: User asks about Redmine project metrics, sprint status, team performance, bug analytics, or any data analysis questions about issues/tasks
when_not_to_use: User wants to create/update individual issues, browse Redmine UI, or perform CRUD operations
---

# Redmine Analytics Expert Skill

## Quick Decision (First 50 Words)
Use this skill when user asks analytical questions about Redmine data: sprint progress, team workload, bug metrics, velocity trends, backlog health, release status, or throughput. Don't use for creating/updating single issues or basic CRUD operations - those use standard Redmine tools.

## Prerequisites
1. Redmine DB cache MUST be enabled first
2. Check cache status: `redmine_db_control` with action="status"
3. If disabled, enable it: `redmine_db_control` with action="on"
4. Cache loads 1000 issues in ~4 seconds (one-time cost)

## Available Analytics Tools

### 1. Sprint Status (`redmine_sprint_status`)
**When to use:** Questions about current sprint, committed stories, completion rate, blocked tasks

**Parameters:**
- `version_name` (optional): Specific sprint/version name
- `project_id` (optional): Filter by project

**Returns:**
- committed: Total stories in sprint
- completed: Finished stories
- remaining: Incomplete stories
- in_progress: Currently active
- blocked: Blocked tasks
- completion: Percentage complete
- estimated_hours: Planned effort
- spent_hours: Actual effort
- ahead_behind: "ahead" | "behind" | "on track"

**Example queries:**
- "How many stories are committed in the current sprint?"
- "What is the sprint completion percentage?"
- "Are we ahead or behind schedule?"
- "How many tasks are blocked?"

### 2. Backlog Analytics (`redmine_backlog_analytics`)
**When to use:** Questions about backlog size, priority distribution, aging, monthly trends

**Parameters:**
- `project_id` (optional): Filter by project

**Returns:**
- total: Total open items
- high_priority: High/urgent items count
- high_priority_percent: Percentage
- unestimated: Items without estimates
- unestimated_percent: Percentage
- avg_age_days: Average age of backlog items
- added_this_month: New items this month
- closed_this_month: Completed items this month

**Example queries:**
- "What is the total backlog size?"
- "How many high-priority items are open?"
- "What percentage of backlog is unestimated?"
- "How old is the average backlog item?"

### 3. Team Workload (`redmine_team_workload`)
**When to use:** Questions about task distribution, overloaded members, team capacity

**Parameters:**
- `project_id` (optional): Filter by project

**Returns:**
- team_workload: Dictionary of {member_name: task_count}
- overloaded_members: List of members with >10 tasks

**Example queries:**
- "Show me team workload distribution"
- "Who has the most tasks?"
- "Are any team members overloaded?"
- "How many tasks does each person have?"

### 4. Cycle Time (`redmine_cycle_time`)
**When to use:** Questions about lead time, cycle time, process efficiency, reopened tickets

**Parameters:**
- `project_id` (optional): Filter by project

**Returns:**
- avg_lead_time_days: Created to closed (full lifecycle)
- avg_cycle_time_days: Started to closed (active work time)
- reopened_tickets: Count of reopened issues

**Example queries:**
- "What is the average cycle time?"
- "What is the average lead time?"
- "How many tickets were reopened?"
- "How long does it take to close a ticket?"

### 5. Bug Analytics (`redmine_bug_analytics`)
**When to use:** Questions about bugs, defects, quality metrics

**Parameters:**
- `project_id` (optional): Filter by project

**Returns:**
- total_bugs: All bugs ever created
- open_bugs: Currently open bugs
- critical_bugs: High/urgent open bugs
- bug_ratio: Bugs per story (quality indicator)
- avg_resolution: Average days to fix
- post_release_bugs: Bugs found in last 30 days

**Example queries:**
- "How many bugs are open?"
- "How many critical bugs do we have?"
- "What is the bug-to-story ratio?"
- "What is the average bug resolution time?"

### 6. Release Status (`redmine_release_status`)
**When to use:** Questions about release progress, version completion, scope

**Parameters:**
- `version_name` (optional): Specific release/version name

**Returns:**
- name: Release name
- total: Total issues in release
- completed: Finished issues
- unresolved: Remaining issues
- progress: Percentage complete
- due_date: Target date

**Example queries:**
- "What is the release progress?"
- "How many features are completed for the upcoming release?"
- "What percentage of release scope is done?"
- "When is the release due?"

### 7. Velocity Trend (`redmine_velocity_trend`)
**When to use:** Questions about velocity trends, sprint performance over time

**Parameters:**
- `project_id` (optional): Filter by project
- `sprints` (optional): Number of sprints to analyze (default: 5)

**Returns:**
- velocities: Array of {name, value} for each sprint
- trend: "increasing" | "decreasing" | "stable"
- average: Average velocity across sprints

**Example queries:**
- "What is the velocity trend?"
- "Is velocity increasing or decreasing?"
- "What is the average velocity over last 5 sprints?"
- "Show me sprint velocity history"

### 8. Throughput (`redmine_throughput`)
**When to use:** Questions about ticket creation vs closure rate, flow efficiency

**Parameters:**
- `project_id` (optional): Filter by project
- `weeks` (optional): Time period to analyze (default: 4)

**Returns:**
- created: Tickets created in period
- closed: Tickets closed in period
- net: Difference (positive = closing faster than creating)
- weeks: Time period analyzed

**Example queries:**
- "Are we closing more tickets than we're creating?"
- "What is the throughput per week?"
- "How many tickets were created vs closed?"
- "Is the backlog growing or shrinking?"

## Response Strategy

### 1. Always Check Cache First
```
If cache not enabled:
  "I need to enable the Redmine DB cache first to provide instant analytics. This will take about 4 seconds to load 1000 issues. Should I proceed?"
  
If user agrees:
  Call redmine_db_control with action="on"
  Then proceed with analytics
```

### 2. Format Responses Clearly
- Use bullet points for lists
- Show percentages for completion/progress
- Highlight warnings (overloaded members, high bug counts)
- Provide context and interpretation
- Suggest actions when appropriate

### 3. Multi-Metric Queries
When user asks compound questions, call multiple tools:
- "Show me sprint status and team workload" → Call both tools
- "What's the bug situation and release progress?" → Call both tools

### 4. Provide Insights
Don't just return numbers - interpret them:
- "You're 47% complete - good progress!"
- "⚠ 7 team members are overloaded - consider redistributing tasks"
- "Bug ratio of 13.71 is high - prioritize quality"
- "Velocity is increasing - team is improving!"

## Performance Notes
- Cache queries: 4-5ms per analytics call
- Multiple queries can run in parallel
- Cache auto-refreshes every 5 minutes
- Manual refresh: `redmine_db_control` with action="refresh"

## Common Patterns

### Pattern 1: Sprint Health Check
```
User: "How is the sprint going?"

Response:
1. Call redmine_sprint_status
2. Call redmine_team_workload
3. Call redmine_bug_analytics
4. Synthesize into sprint health summary
```

### Pattern 2: Release Readiness
```
User: "Are we ready for release?"

Response:
1. Call redmine_release_status
2. Call redmine_bug_analytics (critical bugs)
3. Call redmine_sprint_status (blocked items)
4. Provide go/no-go recommendation
```

### Pattern 3: Team Performance Review
```
User: "How is the team performing?"

Response:
1. Call redmine_team_workload
2. Call redmine_velocity_trend
3. Call redmine_cycle_time
4. Provide performance summary with trends
```

## Error Handling

### Cache Not Enabled
```json
{
  "success": false,
  "error": "Redmine DB cache is disabled..."
}
```
**Action:** Offer to enable cache for user

### No Data Found
```json
{
  "success": false,
  "error": "No release found"
}
```
**Action:** Explain no data available, suggest alternatives

### Query Error
```json
{
  "success": false,
  "error": "Cannot subtract tz-naive..."
}
```
**Action:** Report error, suggest manual refresh or retry

## Best Practices

1. **Always enable cache first** - Analytics require cache
2. **Batch related queries** - Call multiple tools for comprehensive answers
3. **Interpret results** - Don't just show numbers, explain what they mean
4. **Highlight issues** - Call out overloaded members, high bug counts, blocked tasks
5. **Suggest actions** - "Consider redistributing tasks", "Prioritize bug fixes"
6. **Show trends** - "Velocity is increasing", "Backlog is growing"
7. **Use visualizations** - The UI has custom components for metrics
8. **Refresh when needed** - If data seems stale, offer to refresh cache

## UI Integration

The frontend has custom rendering for analytics results:
- Sprint status → Card with progress bar
- Team workload → Horizontal bar chart
- Bug metrics → Grid with badges
- Velocity trend → Vertical bar chart
- Release status → Circular progress ring
- Throughput → Comparison bars
- Backlog → Donut charts

Results with `"success": true` automatically trigger custom rendering.

## Example Conversations

### Example 1: Sprint Status
```
User: How many stories are completed vs remaining?

Agent: Let me check the current sprint status...
[Calls redmine_sprint_status]

Response: Based on the current sprint:
- Completed: 472 stories (47.2%)
- Remaining: 528 stories (52.8%)
- In Progress: 50 stories
- Blocked: 0 stories

You're making good progress! Almost halfway through the sprint.
```

### Example 2: Team Workload
```
User: Show me team workload

Agent: [Calls redmine_team_workload]

Response: Current team workload distribution:
- Siddharth Chakravarty: 124 tasks
- Harsh Tomar: 104 tasks
- Abhishek Tiwari: 88 tasks
- [7 more members...]

⚠ Warning: 7 team members are overloaded (>10 tasks each)
Consider redistributing tasks to balance the workload.
```

### Example 3: Comprehensive Analysis
```
User: Give me a complete project health check

Agent: Let me analyze multiple metrics...
[Calls: sprint_status, backlog_analytics, team_workload, bug_analytics]

Response: Project Health Report:

Sprint Status:
- 47.2% complete (472/1000 stories)
- 50 stories in progress
- No blocked tasks ✓

Backlog Health:
- 528 open items
- 32 high priority (6.1%)
- Average age: 21 days

Team Status:
- 10 active members
- 7 overloaded (>10 tasks) ⚠
- Recommend task redistribution

Quality Metrics:
- 272 open bugs ⚠
- 26 critical bugs ⚠
- Bug ratio: 13.71 (high)
- Recommend prioritizing bug fixes

Overall: Project is progressing but has quality and workload concerns.
```

## Troubleshooting

### Slow First Query
- Expected: Cache initialization takes 4-5 seconds
- Solution: Explain to user this is one-time cost

### Stale Data
- Issue: Data is up to 5 minutes old
- Solution: Offer manual refresh

### Missing Data
- Issue: Some fields may be null (closed_on, due_date)
- Solution: Handle gracefully, show "Not set" or calculate alternatives

### Network Errors
- Issue: Cannot reach Redmine API
- Solution: Check .env configuration, verify server accessibility

## Summary

This skill enables instant, comprehensive Redmine analytics through a cache-powered system. Always enable cache first, call appropriate analytics tools, interpret results meaningfully, and provide actionable insights. The system is 1000x faster than direct API calls and provides rich, formatted responses with custom UI rendering.
