# 🧪 Analytics Testing Guide

## Quick Test Commands

Copy and paste these into the chat to test each analytics feature:

### 1. Sprint Status 📅
```
What is the current sprint status?
```
**Expected**: Dashboard with metric cards showing committed, completed, remaining, in progress, and blocked tasks, plus a progress bar.

---

### 2. Team Workload 👥
```
Show team workload distribution
```
**Expected**: Horizontal bar chart showing tasks per team member with overload indicators.

---

### 3. Bug Metrics 🐞
```
Show bug metrics
```
**Expected**: Grid of metric cards showing total bugs, open bugs, critical bugs, bug ratio, and average resolution time.

---

### 4. Velocity Trend 📈
```
Show velocity trend for last 5 sprints
```
**Expected**: Vertical bar chart with velocity per sprint and trend badge (increasing/decreasing/stable).

---

### 5. Release Status 🚀
```
What is the release status?
```
**Expected**: Circular progress ring showing completion percentage with release details.

---

### 6. Backlog Metrics 📊
```
Show backlog metrics
```
**Expected**: Metric cards + donut charts for priority and estimation distribution + monthly trends.

---

### 7. Cycle Time ⏱️
```
What is the average cycle time?
```
**Expected**: Horizontal comparison bars showing lead time vs cycle time.

---

### 8. Throughput 📊
```
Show throughput analysis
```
**Expected**: Comparison bars for created vs closed tickets with net change badge.

---

## Combined Queries

Try asking multiple questions:

```
Give me a complete sprint overview including status, team workload, and bug metrics
```

```
Show me all release metrics: status, velocity trend, and throughput
```

```
What's the health of our project? Show backlog, bugs, and cycle time
```

---

## Debugging

### Check Backend Logs
```powershell
# In PowerShell
Get-Content backend/server.log -Tail 50 -Wait
```

### Check Frontend Console
1. Open browser (http://localhost:5173)
2. Press F12 to open DevTools
3. Go to Console tab
4. Look for JSON parsing messages

### Verify Tools Available
```
List all available Redmine tools
```

---

## Expected JSON Structures

### Sprint Status
```json
{
  "success": true,
  "sprint_status": {
    "committed": 45,
    "completed": 32,
    "remaining": 13,
    "in_progress": 8,
    "blocked": 2,
    "completion": 71.1,
    "estimated_hours": 180,
    "spent_hours": 165,
    "ahead_behind": "on track"
  }
}
```

### Team Workload
```json
{
  "success": true,
  "team_workload": {
    "John Doe": 15,
    "Jane Smith": 12,
    "Bob Johnson": 8,
    "Unassigned": 5
  },
  "overloaded_members": ["John Doe"]
}
```

### Bug Metrics
```json
{
  "success": true,
  "bug_metrics": {
    "total_bugs": 34,
    "open_bugs": 12,
    "critical_bugs": 3,
    "bug_ratio": 0.42,
    "avg_resolution": 5.8,
    "post_release_bugs": 7
  }
}
```

---

## Troubleshooting

### Issue: LLM returns plain text instead of JSON
**Solution**: The query might not have triggered the analytics tool. Try being more specific:
- ❌ "How are we doing?"
- ✅ "Show sprint status"

### Issue: Visualization doesn't appear
**Solution**: Check browser console for JSON parsing errors. The JSON structure might not match expected format.

### Issue: "Tool not found" error
**Solution**: Restart backend server:
```powershell
# Stop backend
Stop-Process -Name python -Force

# Start backend
cd backend
..\.venv\Scripts\python.exe server.py
```

### Issue: No data returned
**Solution**: Check Redmine connection:
```
List Redmine projects
```
If this fails, verify `.env` file has correct `REDMINE_URL` and `REDMINE_API_KEY`.

---

## Success Indicators

✅ Backend shows: "MCP tools available: 23"
✅ Query triggers keyword detection: "✓ Fast detection: 'redmine' category"
✅ Tool execution logged: "🔧 Executing: redmine_sprint_status"
✅ Frontend renders visualization (not plain text)
✅ Charts and graphs appear with colors and animations

---

## Performance Notes

- **Keyword Detection**: ~50ms (fast path)
- **LLM Detection**: ~500ms (fallback)
- **Tool Execution**: ~1-3 seconds (Redmine API call)
- **Total Response Time**: ~2-4 seconds

---

**Ready to test!** Open http://localhost:5173 and start asking questions! 🚀
