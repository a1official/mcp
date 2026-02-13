# Python FastMCP Music Server Setup

The MCP server has been converted to Python using FastMCP for better reliability and performance.

## Prerequisites

- **Python 3.8+** installed
- **pip** (Python package manager)

## Quick Setup

### Windows

Run the setup script:
```bash
setup-python-mcp.bat
```

### Manual Setup

1. **Install Python dependencies:**
   ```bash
   pip install fastmcp httpx
   ```

2. **Test the MCP server:**
   ```bash
   python mcp-server/server.py
   ```

3. **Start the application:**
   ```bash
   npm run dev
   ```

## What Changed?

### Old (Node.js)
- MCP server in JavaScript (`mcp-server/index.js`)
- 17 tools including Spotify, Gmail, GitHub
- Complex OAuth setup required

### New (Python FastMCP)
- MCP server in Python (`mcp-server/server.py`)
- 3 focused music tools (no authentication needed)
- Simple, reliable, fast

## Available Tools

### 1. play_music
Play music instantly based on natural language query.

**Usage:**
- "Play Bohemian Rhapsody"
- "Play some jazz"
- "Play The Weeknd"

**Returns:** 30-second preview with track info

### 2. search_music
Search for songs, artists, or albums.

**Parameters:**
- `query`: Search term
- `type`: 'song', 'artist', or 'album' (default: 'song')
- `limit`: Max results (default: 10)

### 3. get_artist_info
Get information about an artist.

**Parameters:**
- `artist`: Artist name

## How It Works

```
User: "Play some jazz"
    ↓
Backend (Node.js + Groq LLM)
    ↓
MCP Client
    ↓
Python FastMCP Server
    ↓
iTunes API (no auth needed)
    ↓
Returns track with preview URL
    ↓
Frontend plays music automatically
```

## Advantages of Python FastMCP

✅ **Simpler** - Less code, easier to understand  
✅ **Faster** - Python async is very efficient  
✅ **More Reliable** - FastMCP handles edge cases  
✅ **No Authentication** - Uses free iTunes API  
✅ **Easy to Extend** - Add new tools easily  

## Troubleshooting

### "Python not found"
Install Python from https://www.python.org/downloads/

### "fastmcp not found"
Run: `pip install fastmcp httpx`

### "Module not found"
Make sure you're in the project root directory

### Music not playing
1. Check browser console (F12) for errors
2. Make sure backend is running: `npm run dev:server`
3. Check Python MCP server is running (should start automatically)

## Adding More Tools

Edit `mcp-server/server.py` and add new functions with the `@mcp.tool()` decorator:

```python
@mcp.tool()
async def my_new_tool(param: str) -> str:
    """
    Description of what this tool does.
    
    Args:
        param: Description of parameter
    
    Returns:
        JSON string with results
    """
    # Your code here
    return json.dumps({"result": "data"})
```

## Next Steps

1. Run `setup-python-mcp.bat` (Windows) or install dependencies manually
2. Start the app: `npm run dev`
3. Try: "Play some jazz" in the chat
4. Enjoy your music! 🎵

---

For the old Node.js MCP server, see `mcp-server/index.js` (deprecated).
