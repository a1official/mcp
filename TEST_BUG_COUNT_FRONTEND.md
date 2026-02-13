# Testing Bug Count Fix Through Frontend

## Quick Test Steps

### 1. Start Backend Server
```bash
cd backend
python server.py
```

Expected output:
```
Backend server starting...
Using Groq LLM with model: llama-3.1-8b-instant
MCP tools available: 24
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:3001
```

### 2. Start Frontend (in new terminal)
```bash
cd frontend
npm run dev
```

Expected output:
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

### 3. Test Queries

Open http://localhost:5173/ and try these queries:

#### Test 1: Project name (lowercase)
```
how many open bugs in project ncel
```
Expected answer: **310 open bugs**

#### Test 2: Project name (uppercase)
```
how many open bugs in project NCEL
```
Expected answer: **310 open bugs**

#### Test 3: Project ID
```
how many open bugs in project 6
```
Expected answer: **310 open bugs**

#### Test 4: All projects
```
how many open bugs total
```
Expected answer: **522 open bugs** (across all projects)

#### Test 5: Detailed metrics
```
give me bug metrics for ncel project
```
Expected answer:
- Open bugs: 310
- Closed bugs: 212
- Total bugs: 522

## What Changed

### Before (Broken)
- Tool only accepted integer project_id
- LLM passed "ncel" as string
- Groq validation rejected the call
- Got error or wrong data

### After (Fixed)
- Tool accepts both string and integer
- "ncel" → automatically converted to 6
- API query uses correct project ID
- Returns accurate count: 310

## Troubleshooting

### If you get wrong count:
1. Check backend logs for errors
2. Verify .env has correct REDMINE_URL and REDMINE_API_KEY
3. Test direct API: `python test_bug_count_fix.py`

### If you get "unknown project" error:
1. Check PROJECT_MAP in backend/redmine_direct.py
2. Add your project name mapping if needed

### If LLM doesn't call the tool:
1. Check that "redmine" tools are enabled in UI settings
2. Try more explicit query: "use redmine_bug_analytics for ncel"
3. Check backend logs to see which tool was selected

## Success Criteria
✅ Query "how many open bugs in project ncel" returns 310
✅ No type validation errors in backend logs
✅ Response time < 3 seconds
✅ Answer is formatted clearly with numbers
