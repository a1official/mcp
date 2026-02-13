# Quick Start: Redmine Analytics

## Setup (One-Time)

1. **Enable Cache**
   ```
   Turn on Redmine DB cache
   ```
   Response: ✓ Cache enabled. Loaded 1000 issues in 4.6s

2. **Verify Status**
   ```
   Check Redmine DB status
   ```
   Response: Cache enabled. 1000 issues cached.

## Analytics Queries

### Sprint Status
```
How many stories are committed in the current sprint?
How many stories are completed vs remaining?
What is the sprint progress?
How many tasks are blocked?
```

### Backlog
```
What is the total backlog size?
How many high-priority items are open?
What percentage of backlog is unestimated?
How many items were added this month?
```

### Team Workload
```
Show me team workload
How many tasks are assigned per team member?
Are any team members overloaded?
Who has the most tasks?
```

### Cycle Time
```
What is the average cycle time?
What is the average lead time?
How many tickets were reopened?
```

### Bugs
```
How many bugs are open?
How many critical bugs do we have?
What is the bug-to-story ratio?
What is the average bug resolution time?
```

### Release
```
What is the release progress?
How many features are completed for the upcoming release?
What percentage of release scope is done?
```

### Velocity
```
What is the velocity trend?
Is velocity increasing or decreasing?
What is the average velocity over last 5 sprints?
```

### Throughput
```
Are we closing more tickets than we're creating?
What is the throughput per week?
How many tickets were created vs closed?
```

## Cache Management

### Refresh Cache
```
Refresh Redmine cache
```
Use when you want fresh data immediately (otherwise auto-refreshes every 5 min)

### Check Status
```
Check cache status
```
Shows last updated time, cache age, and statistics

### Disable Cache
```
Turn off Redmine DB
```
Falls back to direct API calls (slower)

## Tips

- Cache refreshes automatically every 5 minutes
- All analytics queries run in <10ms (instant)
- You can ask multiple questions in one message
- Natural language works - no need for exact phrasing
- Cache must be enabled for analytics to work

## Example Conversation

```
User: Turn on Redmine DB cache

Bot: ✓ Redmine DB cache enabled and initialized
     - 1000 issues loaded
     - 1 project
     - Duration: 4.6 seconds

User: How many stories are completed vs remaining?

Bot: Based on the current sprint data:
     
     Completed: 472 stories (47.2%)
     Remaining: 528 stories (52.8%)
     In Progress: 50 stories
     Blocked: 0 stories
     
     You're making good progress! Almost halfway through.

User: Show me team workload and bug status

Bot: Team Workload:
     - Siddharth Chakravarty: 124 tasks
     - Harsh Tomar: 104 tasks
     - Abhishek Tiwari: 88 tasks
     - [7 more members...]
     
     ⚠ Warning: 7 team members are overloaded (>10 tasks each)
     
     Bug Status:
     - Total bugs: 466
     - Open bugs: 272 (58%)
     - Critical bugs: 26
     - Bug-to-story ratio: 13.71
     
     You have a high number of open bugs. Consider prioritizing bug fixes.
```

## Troubleshooting

### "Cache is disabled" error
- Run: `Turn on Redmine DB cache`

### Slow first query
- First query loads cache (4-5 seconds)
- All subsequent queries are instant

### Stale data
- Run: `Refresh Redmine cache`
- Or wait for auto-refresh (every 5 min)

### Network errors
- Check `.env` file has correct REDMINE_URL and REDMINE_API_KEY
- Verify Redmine server is accessible

## Performance

- Cache load: 4.6 seconds (one-time)
- Query time: 4.4 milliseconds
- Speedup: 1000x faster than direct API
- Rate limits: Never hit (1 API call per 5 min)
