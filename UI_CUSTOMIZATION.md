# UI Customization - Tool-Specific Rendering

## Overview

The frontend now automatically detects and renders different tool outputs with custom, beautiful UI components instead of plain text.

## Supported Tool Outputs

### 1. **Redmine Issues List**
When the backend returns a list of issues, the UI displays:
- Card-based layout with hover effects
- Issue ID with purple highlight
- Status badges (Open, In Progress, Resolved, Closed) with color coding
- Priority badges (Low, Normal, High, Urgent) with color coding
- Issue title and metadata (project, assignee, date)
- Responsive grid layout

**Example Response:**
```json
{
  "success": true,
  "count": 10,
  "issues": [
    {
      "id": 123,
      "subject": "Fix login bug",
      "status": "Open",
      "priority": "High",
      "project": "NCEL",
      "assigned_to": "John Doe",
      "updated_on": "2025-01-15T10:30:00Z"
    }
  ]
}
```

**UI Features:**
- 📧 Mail icon header
- Color-coded status badges
- Hover animation (slides right)
- Metadata with emojis (📁 project, 👤 assignee, 📅 date)

### 2. **Redmine Projects List**
Grid layout showing all projects:
- Project name and identifier
- Description preview (first 100 chars)
- Hover effect (lifts up)
- Responsive grid (auto-fit columns)

**Example Response:**
```json
{
  "success": true,
  "count": 5,
  "projects": [
    {
      "id": 1,
      "name": "NCEL Project",
      "identifier": "ncel",
      "description": "Main project for..."
    }
  ]
}
```

### 3. **Single Redmine Issue Detail**
Detailed view for a specific issue:
- Large title with badges
- Full description in styled box
- Metadata grid (project, tracker, assignee, author, dates)
- Progress bar with percentage
- Color-coded status and priority

**Example Response:**
```json
{
  "success": true,
  "issue": {
    "id": 123,
    "subject": "Fix login bug",
    "description": "Users cannot log in...",
    "status": "In Progress",
    "priority": "High",
    "tracker": "Bug",
    "assigned_to": "John Doe",
    "author": "Jane Smith",
    "project": "NCEL",
    "created_on": "2025-01-10T09:00:00Z",
    "updated_on": "2025-01-15T10:30:00Z",
    "done_ratio": 60
  }
}
```

**UI Features:**
- Large header with issue number
- Status and priority badges
- Description in dark box
- Metadata in responsive grid
- Animated progress bar

### 4. **Search Results (Google/DuckDuckGo)**
Clean list of search results:
- Clickable titles (open in new tab)
- Domain/URL display in green
- Snippet preview
- Hover effects

**Example Response:**
```json
{
  "success": true,
  "result_count": 10,
  "results": [
    {
      "title": "Example Page",
      "link": "https://example.com/page",
      "snippet": "This is a preview...",
      "domain": "example.com"
    }
  ]
}
```

### 5. **Music Playback**
Already implemented - floating music player with:
- Album artwork
- Track name and artist
- Play/pause button
- Smooth animations

## Color Coding

### Status Colors
- **Open/New**: Blue (#60a5fa)
- **In Progress**: Yellow (#fbbf24)
- **Resolved/Closed**: Green (#4ade80)

### Priority Colors
- **Low**: Gray (#9ca3af)
- **Normal**: Blue (#60a5fa)
- **High/Urgent**: Red (#f87171)

## How It Works

### 1. Response Detection
```javascript
const renderMessageContent = (content) => {
  // Try to parse JSON from response
  const jsonMatch = content.match(/\{[\s\S]*?"success"\s*:\s*true[\s\S]*?\}/);
  
  if (jsonMatch) {
    const data = JSON.parse(jsonMatch[0]);
    
    // Detect data type and render accordingly
    if (data.issues) return <IssuesList />;
    if (data.projects) return <ProjectsGrid />;
    if (data.issue) return <IssueDetail />;
    if (data.results) return <SearchResults />;
  }
  
  // Fallback to plain text
  return <PlainText />;
}
```

### 2. Automatic Rendering
The UI automatically detects the tool output type and renders the appropriate component:
- No manual configuration needed
- Works with any tool that returns JSON with `"success": true`
- Falls back to plain text if parsing fails

### 3. Responsive Design
All components are fully responsive:
- Grid layouts adapt to screen size
- Cards stack on mobile
- Metadata wraps appropriately

## Adding New Tool Renderers

To add a custom renderer for a new tool:

1. **Add detection logic** in `renderMessageContent`:
```javascript
// Detect your tool's response
if (data.myToolData && Array.isArray(data.myToolData)) {
  return <MyCustomComponent data={data.myToolData} />;
}
```

2. **Create the component**:
```javascript
const MyCustomComponent = ({ data }) => (
  <div className="structured-content">
    <div className="content-header">
      <Icon size={20} className="content-icon" />
      <h3>My Tool Results</h3>
    </div>
    <div className="my-custom-layout">
      {data.map(item => (
        <div key={item.id} className="my-item-card">
          {/* Your custom rendering */}
        </div>
      ))}
    </div>
  </div>
);
```

3. **Add CSS styles** in `App.css`:
```css
.my-custom-layout {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: var(--spacing-md);
}

.my-item-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--card-border);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    transition: all var(--transition-base);
}

.my-item-card:hover {
    background: rgba(255, 255, 255, 0.05);
    border-color: var(--accent-purple);
}
```

## Backend Requirements

For custom rendering to work, the backend must return JSON with:
- `"success": true` field
- Structured data (issues, projects, results, etc.)

**Example backend response:**
```python
return json.dumps({
    "success": True,
    "count": len(items),
    "items": [
        {
            "id": item.id,
            "title": item.title,
            # ... more fields
        }
        for item in items
    ]
}, indent=2)
```

## Benefits

1. **Better UX**: Visual, scannable information instead of text walls
2. **Professional Look**: Polished, modern UI components
3. **Automatic**: No user configuration needed
4. **Extensible**: Easy to add new tool renderers
5. **Responsive**: Works on all screen sizes
6. **Accessible**: Proper semantic HTML and ARIA labels

## Future Enhancements

- [ ] Add charts/graphs for analytics data
- [ ] Add inline actions (edit, delete, comment)
- [ ] Add filtering and sorting for lists
- [ ] Add pagination for large datasets
- [ ] Add export functionality (CSV, PDF)
- [ ] Add dark/light theme toggle
- [ ] Add keyboard shortcuts
- [ ] Add real-time updates (WebSocket)

## Screenshots

### Redmine Issues List
```
┌─────────────────────────────────────────┐
│ 📧 Redmine Issues (10)                  │
├─────────────────────────────────────────┤
│ ┌─────────────────────────────────────┐ │
│ │ #123 [Open] [High]                  │ │
│ │ Fix login bug                       │ │
│ │ 📁 NCEL  👤 John  📅 Jan 15        │ │
│ └─────────────────────────────────────┘ │
│ ┌─────────────────────────────────────┐ │
│ │ #124 [In Progress] [Normal]         │ │
│ │ Add new feature                     │ │
│ │ 📁 NCEL  👤 Jane  📅 Jan 14        │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Issue Detail
```
┌─────────────────────────────────────────┐
│ 📧 Issue #123                           │
├─────────────────────────────────────────┤
│ Fix login bug                           │
│ [In Progress] [High]                    │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ Users cannot log in after update... │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Project: NCEL        Tracker: Bug      │
│ Assigned: John       Author: Jane      │
│ Created: Jan 10      Updated: Jan 15   │
│                                         │
│ Progress: [████████░░] 60%             │
└─────────────────────────────────────────┘
```

## Conclusion

The custom UI rendering transforms raw tool outputs into beautiful, professional interfaces that make the application feel polished and production-ready.
