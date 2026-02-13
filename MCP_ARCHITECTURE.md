# MCP Music Server Architecture Summary

## Executive Overview

MCP Music Server is a **modular AI assistant platform** that integrates music playback, web automation, project management (Redmine), and custom tools through a unified FastMCP server. The architecture emphasizes modularity, extensibility, and clean separation of concerns with agent-based tool organization.

## Core Architecture Pattern: Modular Agent System

### Central Hub: FastMCP Server
- **Location**: `mcp-server/server.py`
- **Framework**: FastMCP (Python)
- **Protocol**: Model Context Protocol (MCP)
- **Clients**: Claude Desktop, Kiro IDE, Custom web app

The MCP Server is the **single source of truth** for:
- Tool registration and discovery
- Agent module loading
- Environment configuration
- Tool execution coordination

### Key Design Decision: Agent-Based Modularity
```
Frontend (React) ←→ Backend (FastAPI) ←→ Groq LLM
                         ↓
                   Tool Execution
                         ↓
        ┌────────────────┼────────────────┐
        │                │                │
    Music Agent    Playwright Agent   Redmine Agent
    (iTunes API)   (Web Automation)   (Project Mgmt)
```

## 1. Modular Agent Architecture

### Agent Plugin System

**Registry**: `mcp-server/agents/__init__.py`
- Core agents: Music, Playwright, Redmine
- Extension pattern: OAuth variants (redmine_oauth)

**Agent Module Interface**:
```python
def register_{agent}_tools(mcp: FastMCP):
    """Register all tools for this agent"""
    
    @mcp.tool()
    async def tool_name(param: str) -> str:
        """Tool implementation"""
        return json.dumps(result)
```

**Agent Loading Pattern**:
1. Create agent module in `mcp-server/agents/`
2. Implement `register_*_tools(mcp)` function
3. Import and call in `mcp-server/server.py`
4. Tools auto-register at server startup

### Agent Modules

#### Music Agent (`agents/music.py`)
**Purpose**: iTunes API integration for music search and playback
**Tools**:
- `play_music` - Search and play 30-second previews
- `search_music` - Search songs/artists/albums
- `get_artist_info` - Get artist details

**Key Features**:
- Natural language music queries
- JSON response with track metadata
- Frontend auto-detection for playback

#### Playwright Agent (`agents/playwright_agent.py`)
**Purpose**: Web automation and scraping
**Tools**:
- `browse_website` - Extract page content
- `screenshot_website` - Capture screenshots
- `extract_links` - Get all page links
- `search_google` - Google search results
- `scrape_products` - E-commerce product extraction
- `search_duckduckgo` - Privacy-focused search
- `search_products_smart` - Smart product search (avoids bot detection)

**Anti-Detection Features**:
- Stealth mode browser launch
- Custom user agents
- WebDriver property masking
- Realistic viewport and headers

#### Redmine Agent (`agents/redmine.py`)
**Purpose**: Project management integration
**Tools**:
- `redmine_list_projects` - List accessible projects
- `redmine_list_issues` - List issues with filters
- `redmine_get_issue` - Get detailed issue info
- `redmine_create_issue` - Create new issues
- `redmine_update_issue` - Update existing issues

**Authentication**: API key-based (single user)

#### Redmine OAuth Agent (`agents/redmine_oauth.py`)
**Purpose**: Multi-user Redmine authentication
**Tools**:
- `redmine_oauth_get_auth_url` - Get OAuth URL
- `redmine_oauth_exchange_code` - Exchange code for token
- `redmine_oauth_list_projects` - List projects (OAuth)
- `redmine_oauth_list_issues` - List issues (OAuth)
- `redmine_oauth_create_issue` - Create issue (OAuth)

**Authentication**: OAuth 2.0 (per-user tokens)

## 2. Backend Architecture

### FastAPI Backend (`backend/server.py`)

**Purpose**: HTTP API layer between frontend and LLM
**Port**: 3001
**Framework**: FastAPI with CORS middleware

**Key Components**:
1. **Tool Definitions**: JSON schema for LLM function calling
2. **Tool Implementations**: Async functions that execute tools
3. **Chat Endpoint**: `/api/chat` - Main conversation endpoint
4. **Health Endpoint**: `/api/health` - Service health check

**Request Flow**:
```
Frontend → POST /api/chat
    ↓
Parse message + history
    ↓
Call Groq LLM with tools
    ↓
LLM returns tool calls
    ↓
Execute tools locally
    ↓
Send results back to LLM
    ↓
Return final response
    ↓
Frontend renders response
```

### Tool Execution Pattern

**Tool Call Detection**:
```python
if assistant_message.tool_calls:
    for tool_call in assistant_message.tool_calls:
        tool_name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)
        
        # Execute tool
        result = await call_mcp_tool(tool_name, arguments)
        
        # Add to conversation
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })
```

**Tool Implementation Pattern**:
```python
async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    if tool_name == "play_music":
        query = arguments.get("query", "")
        # ... implementation
        return json.dumps(result)
    
    elif tool_name == "browse_website":
        url = arguments.get("url", "")
        # ... implementation
        return json.dumps(result)
    
    # ... more tools
    
    return json.dumps({"error": "Unknown tool"})
```

### System Prompt Strategy

**Music Playback Instructions**:
- MUST copy entire JSON response from tool
- DO NOT modify or summarize JSON
- Include exact structure for frontend parsing

**E-Commerce Instructions**:
- ALWAYS use `search_products_smart` for e-commerce
- NEVER use direct scraping tools (will be blocked)
- Use DuckDuckGo search to avoid bot detection

**Example System Prompt**:
```python
"""You are a helpful AI assistant with music playback and web automation capabilities.

CRITICAL MUSIC PLAYBACK INSTRUCTIONS:
When a user asks to play music:
1. Call the "play_music" tool
2. You MUST copy the ENTIRE JSON response from the tool into your reply
3. DO NOT modify, summarize, or paraphrase the JSON

E-COMMERCE & PRODUCT SEARCH INSTRUCTIONS:
When users ask about products on e-commerce sites:
1. ALWAYS use "search_products_smart" tool
2. NEVER use "browse_website", "extract_links", or "scrape_products"
3. These sites have strong bot protection and will block direct scraping
"""
```

## 3. Frontend Architecture

### React Application (`frontend/src/`)

**Framework**: React 18 with Vite
**Port**: 5173/5174
**Key Features**:
- Real-time chat interface
- Automatic music playback
- Floating music player
- Conversation history

**Component Structure**:
```
App.jsx
├── Chat Interface
│   ├── Message List
│   ├── Input Field
│   └── Send Button
└── Music Player (conditional)
    ├── Album Art
    ├── Track Info
    ├── Play/Pause Controls
    └── Progress Bar
```

### Music Playback Flow

**Detection Pattern**:
```javascript
// Check if response contains music JSON
if (response.includes('"action": "PLAY_MUSIC"')) {
    const musicMatch = response.match(/\{[\s\S]*?"action":\s*"PLAY_MUSIC"[\s\S]*?\}/);
    if (musicMatch) {
        const musicData = JSON.parse(musicMatch[0]);
        setCurrentTrack(musicData.track);
        // Auto-play
    }
}
```

**Music Player State**:
```javascript
const [currentTrack, setCurrentTrack] = useState(null);
const [isPlaying, setIsPlaying] = useState(false);
const audioRef = useRef(new Audio());

useEffect(() => {
    if (currentTrack?.previewUrl) {
        audioRef.current.src = currentTrack.previewUrl;
        audioRef.current.play();
        setIsPlaying(true);
    }
}, [currentTrack]);
```

## 4. Configuration & Environment

### Environment Variables (`.env`)

**LLM Configuration**:
```env
GROQ_API_KEY=your_groq_key_here
```

**Redmine Configuration** (API Key):
```env
REDMINE_URL=https://redmine.example.com
REDMINE_API_KEY=your_api_key
```

**Redmine Configuration** (OAuth):
```env
REDMINE_URL=https://redmine.example.com
REDMINE_CLIENT_ID=your_client_id
REDMINE_CLIENT_SECRET=your_secret
```

**Server Configuration**:
```env
PORT=3001
FRONTEND_URL=http://localhost:5173
```

### Configuration Loading Pattern

**Backend**:
```python
from dotenv import load_dotenv
load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
REDMINE_URL = os.getenv("REDMINE_URL", "")
```

**MCP Server**:
```python
from dotenv import load_dotenv
load_dotenv()

REDMINE_URL = os.getenv("REDMINE_URL", "")
REDMINE_API_KEY = os.getenv("REDMINE_API_KEY", "")
```

## 5. Tool Policy & Security

### Tool Availability

**Backend Tools** (15 total):
- 3 Music tools
- 7 Playwright tools (including smart search)
- 5 Redmine tools

**MCP Server Tools** (13+ total):
- Same as backend + OAuth variants
- Extensible via agent modules

### Security Considerations

**API Key Protection**:
- Environment variables only
- Never committed to git
- `.env.example` for templates

**Bot Detection Avoidance**:
- Stealth browser configuration
- Smart search via DuckDuckGo
- Avoid direct e-commerce scraping
- Realistic user agents and headers

**Rate Limiting**:
- Groq API rate limits handled
- 429 errors with helpful messages
- Automatic retry suggestions

## 6. Error Handling

### Backend Error Handling

**Rate Limit Errors**:
```python
except Exception as e:
    error_msg = str(e)
    if "rate_limit" in error_msg.lower() or "429" in error_msg:
        raise HTTPException(
            status_code=429,
            detail="Groq API rate limit reached. Please wait or get new API key."
        )
    raise HTTPException(status_code=500, detail=error_msg)
```

**Tool Execution Errors**:
```python
try:
    result = await execute_tool(tool_name, arguments)
except Exception as e:
    return json.dumps({
        "success": False,
        "error": str(e),
        "suggestion": "Try alternative approach..."
    })
```

### Frontend Error Handling

**Network Errors**:
```javascript
try {
    const response = await fetch('/api/chat', { ... });
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
} catch (error) {
    setError('Failed to get response');
    console.error('Error:', error);
}
```

## 7. Development Workflow

### Project Structure
```
mcp/
├── backend/
│   ├── server.py          # FastAPI backend
│   └── requirements.txt   # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── App.jsx       # Main React component
│   │   ├── App.css       # Styles
│   │   └── main.jsx      # Entry point
│   ├── package.json      # Node dependencies
│   └── vite.config.js    # Vite configuration
├── mcp-server/
│   ├── agents/
│   │   ├── __init__.py           # Agent exports
│   │   ├── music.py              # Music agent
│   │   ├── playwright_agent.py   # Web automation
│   │   ├── redmine.py            # Redmine (API key)
│   │   └── redmine_oauth.py      # Redmine (OAuth)
│   ├── server.py         # FastMCP server
│   └── requirements.txt  # Python dependencies
├── .env                  # Environment variables
├── .env.example          # Template
└── README.md            # Documentation
```

### Running the Application

**Start Backend**:
```bash
cd backend
python server.py
# Runs on http://localhost:3001
```

**Start Frontend**:
```bash
cd frontend
npm run dev
# Runs on http://localhost:5173
```

**Start MCP Server** (for Claude Desktop/Kiro):
```bash
cd mcp-server
python -m fastmcp run server.py
```

### Development Commands

**Install Dependencies**:
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install

# MCP Server
cd mcp-server
pip install -r requirements.txt
```

**Install Playwright**:
```bash
playwright install chromium
```

## 8. Key Design Patterns

### 1. Agent Module Pattern
Each agent is a self-contained module:
```python
# agents/my_agent.py
def register_my_agent_tools(mcp):
    @mcp.tool()
    async def my_tool(param: str) -> str:
        return json.dumps({"result": "..."})
```

### 2. Tool Registration Pattern
Tools register at server startup:
```python
# server.py
from agents.music import register_music_tools
from agents.playwright_agent import register_playwright_tools
from agents.redmine import register_redmine_tools

register_music_tools(mcp)
register_playwright_tools(mcp)
register_redmine_tools(mcp)
```

### 3. JSON Response Pattern
All tools return JSON strings:
```python
return json.dumps({
    "success": True,
    "data": result,
    "message": "Operation completed"
}, indent=2)
```

### 4. Frontend Detection Pattern
Frontend detects special JSON in responses:
```javascript
if (response.includes('"action": "PLAY_MUSIC"')) {
    // Extract and handle music data
}
```

### 5. Async Tool Execution
All tools are async for non-blocking I/O:
```python
async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        # ... process
```

### 6. Environment-Based Configuration
Configuration via environment variables:
```python
REDMINE_URL = os.getenv("REDMINE_URL", "")
if not REDMINE_URL:
    return json.dumps({
        "success": False,
        "error": "Redmine not configured"
    })
```

## 9. Extensibility Points

### 1. Add New Agent
Create new agent module:
```python
# agents/my_new_agent.py
def register_my_new_agent_tools(mcp):
    @mcp.tool()
    async def my_tool(param: str) -> str:
        # Implementation
        return json.dumps(result)
```

Register in server:
```python
# server.py
from agents.my_new_agent import register_my_new_agent_tools
register_my_new_agent_tools(mcp)
```

### 2. Add New Tool to Existing Agent
Add function to agent module:
```python
# agents/music.py
@mcp.tool()
async def new_music_tool(query: str) -> str:
    # Implementation
    return json.dumps(result)
```

### 3. Add Backend Tool Implementation
Add to backend tool definitions:
```python
# backend/server.py
MCP_TOOLS.append({
    "type": "function",
    "function": {
        "name": "my_new_tool",
        "description": "...",
        "parameters": { ... }
    }
})
```

Add implementation:
```python
elif tool_name == "my_new_tool":
    # Implementation
    return json.dumps(result)
```

### 4. Add Frontend Feature
Detect special response patterns:
```javascript
// App.jsx
if (response.includes('"action": "MY_ACTION"')) {
    const data = extractData(response);
    handleMyAction(data);
}
```

## 10. Deployment Considerations

### Local Development
- Backend: `python backend/server.py`
- Frontend: `npm run dev` in frontend/
- MCP Server: For IDE integration only

### Production Deployment
1. **Backend**: Deploy FastAPI with uvicorn
2. **Frontend**: Build and serve static files
3. **Environment**: Set production environment variables
4. **HTTPS**: Use reverse proxy (nginx, Caddy)
5. **CORS**: Update allowed origins

### FastMCP Cloud Deployment
**Preparation**:
- Remove Playwright dependencies (not cloud-compatible)
- Keep only API-based tools (music, Redmine)
- Test with `fastmcp dev server.py`
- Deploy with `fastmcp deploy`

**Cloud-Compatible Tools**:
- ✅ Music tools (iTunes API)
- ✅ Redmine tools (HTTP API)
- ✅ DuckDuckGo search (HTTP)
- ❌ Playwright tools (requires browser)

## 11. Testing Strategy

### Manual Testing
1. **Music Playback**: "Play some jazz music"
2. **Web Search**: "Search for Python tutorials"
3. **Redmine**: "List my Redmine projects"
4. **Error Handling**: Test with invalid inputs

### Integration Testing
- Test backend → LLM → tool execution flow
- Test frontend → backend communication
- Test music player auto-play
- Test error messages

## 12. Common Pitfalls & Solutions

### Pitfall 1: LLM Uses Wrong Tool
**Problem**: LLM calls `browse_website` instead of `search_products_smart`
**Solution**: Strong system prompt with MANDATORY/FORBIDDEN language

### Pitfall 2: Music JSON Not Detected
**Problem**: Frontend doesn't play music
**Solution**: Backend injects music JSON into response

### Pitfall 3: Rate Limit Errors
**Problem**: Groq API rate limit reached
**Solution**: Better error handling with helpful messages

### Pitfall 4: CORS Errors
**Problem**: Frontend can't connect to backend
**Solution**: Add frontend URL to CORS allowed origins

### Pitfall 5: Bot Detection
**Problem**: E-commerce sites block scraping
**Solution**: Use smart search via DuckDuckGo

## 13. Future Enhancements

### Planned Features
1. **Token Storage**: Database for OAuth tokens
2. **Session Management**: User sessions and history
3. **More Agents**: Spotify, GitHub, Jira, etc.
4. **Voice Input**: Speech-to-text integration
5. **Image Generation**: DALL-E, Stable Diffusion
6. **Database Tools**: PostgreSQL, MongoDB integration

### Architecture Improvements
1. **Agent Discovery**: Dynamic agent loading
2. **Tool Marketplace**: Community-contributed tools
3. **Multi-LLM Support**: OpenAI, Anthropic, local models
4. **Caching Layer**: Redis for performance
5. **Queue System**: Background job processing

## 14. Summary: What Makes This Architecture Unique

### Architectural Strengths
1. **Modular agents**: Clean separation of concerns
2. **Dual deployment**: Web app + MCP server
3. **Smart tool selection**: LLM guided to use correct tools
4. **Auto-play music**: Frontend detects and plays automatically
5. **Bot detection avoidance**: Smart search strategies
6. **OAuth support**: Multi-user authentication
7. **Extensible**: Easy to add new agents and tools

### Key Innovations
1. **Agent-based modularity**: Each service is a separate agent
2. **JSON injection**: Backend ensures frontend gets playable data
3. **Smart search**: Avoids bot detection via search engines
4. **Dual auth**: API key + OAuth for different use cases
5. **Tool policy guidance**: System prompts guide LLM tool selection

### Technology Choices
- **FastMCP**: Modern MCP server framework
- **FastAPI**: High-performance async Python backend
- **React**: Component-based frontend
- **Groq**: Fast LLM inference
- **Playwright**: Powerful web automation
