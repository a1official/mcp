"""
Simple Python Backend Server
Handles HTTP requests and Groq LLM integration with MCP
"""

import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Tool Categories for JSPLIT Architecture
TOOL_CATEGORIES = {
    "music": {
        "description": "Play music, search songs, get artist information from iTunes",
        "keywords": ["music", "song", "play", "artist", "album", "listen", "track", "jazz", "rock", "genre", "spotify", "itunes"],
        "tools": ["play_music", "search_music", "get_artist_info"]
    },
    "web": {
        "description": "Browse websites, search Google/DuckDuckGo, find products online",
        "keywords": ["browse", "website", "search", "google", "web", "product", "blinkit", "amazon", "scrape", "duckduckgo", "url", "link"],
        "tools": ["browse_website", "screenshot_website", "extract_links", "search_google", 
                 "scrape_products", "search_duckduckgo", "search_products_smart"]
    },
    "redmine": {
        "description": "Manage Redmine projects, issues, sprints, team workload, and analytics",
        "keywords": ["redmine", "issue", "project", "task", "ticket", "bug", "feature", "sprint", "story", "stories",
                    "backlog", "velocity", "burndown", "team", "workload", "release", "committed", "completed",
                    "analytics", "metrics", "cycle", "lead", "throughput", "trend", "version", "tracker",
                    "priority", "assigned", "member", "quality", "defect", "reopened", "spillover",
                    "blocked", "overloaded", "unestimated", "aging", "resolution"],
        "tools": ["redmine_list_projects", "redmine_list_versions", "redmine_list_trackers",
                 "redmine_list_statuses", "redmine_list_users",
                 "redmine_list_issues", "redmine_get_issue",
                 "redmine_create_issue", "redmine_update_issue", "redmine_delete_issue",
                 "redmine_sprint_analytics", "redmine_backlog_analytics", "redmine_team_workload",
                 "redmine_quality_metrics", "redmine_cycle_time", "redmine_release_status",
                 "redmine_velocity_trend", "redmine_throughput"]
    }
}

# Category selection tool (meta-tool)
CATEGORY_SELECTOR_TOOL = {
    "type": "function",
    "function": {
        "name": "select_tool_category",
        "description": "Select which category of tools to use based on user's request",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["music", "web", "redmine"],
                    "description": "Tool category: 'music' for playing/searching music, 'web' for browsing/searching websites, 'redmine' for project management"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation of why this category was chosen"
                }
            },
            "required": ["category"]
        }
    }
}


# MCP tools (hardcoded for simplicity)
MCP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "play_music",
            "description": "Play music by query. Returns 30s preview.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Song/artist/genre"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_music",
            "description": "Search iTunes for songs/artists/albums.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "type": {"type": "string", "enum": ["song", "artist", "album"]},
                    "limit": {"type": "number", "description": "Max results (default: 10)"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_artist_info",
            "description": "Get artist info from iTunes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "artist": {"type": "string", "description": "Artist name"}
                },
                "required": ["artist"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browse_website",
            "description": "Browse website. May be blocked. Use search_products_smart for e-commerce.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to browse"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "screenshot_website",
            "description": "Screenshot a website.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL"},
                    "filename": {"type": "string", "description": "Output filename"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_links",
            "description": "Extract links from webpage. May be blocked.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_google",
            "description": "Search Google.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_list_projects",
            "description": "List all Redmine projects.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_list_versions",
            "description": "List versions/sprints for a project. Use to find version IDs for sprint analytics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID or identifier"}
                },
                "required": ["project_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_list_trackers",
            "description": "List available trackers (Bug, Feature, Story, etc.)",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_list_statuses",
            "description": "List available issue statuses (New, In Progress, Closed, etc.)",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_list_users",
            "description": "List users/members. If project_id given, lists project members.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID or identifier (optional)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_list_issues",
            "description": "List Redmine issues with rich filtering (tracker, version, assignee, priority). Returns tracker, version, estimated_hours, done_ratio, dates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID or identifier (optional)"},
                    "status": {"type": "string", "enum": ["open", "closed", "all"], "description": "Filter by status (default: open)"},
                    "tracker_id": {"type": "integer", "description": "Filter by tracker ID (optional)"},
                    "assigned_to_id": {"type": "integer", "description": "Filter by assignee user ID (optional)"},
                    "fixed_version_id": {"type": "integer", "description": "Filter by version/sprint ID (optional)"},
                    "priority_id": {"type": "integer", "description": "Filter by priority (1=Low,2=Normal,3=High,4=Urgent,5=Immediate)"},
                    "limit": {"type": "integer", "description": "Max issues (-1 for ALL, default: 25)"},
                    "sort": {"type": "string", "description": "Sort order (default: updated_on:desc)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_get_issue",
            "description": "Get detailed issue info including journals/history, children, relations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "integer", "description": "Issue ID"}
                },
                "required": ["issue_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_create_issue",
            "description": "Create a new Redmine issue with full field support.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID or identifier"},
                    "subject": {"type": "string", "description": "Issue title"},
                    "description": {"type": "string", "description": "Description"},
                    "tracker_id": {"type": "integer", "description": "Tracker ID (default: 1=Bug)"},
                    "priority_id": {"type": "integer", "description": "Priority (1=Low,2=Normal,3=High, default: 2)"},
                    "assigned_to_id": {"type": "integer", "description": "Assignee user ID"},
                    "fixed_version_id": {"type": "integer", "description": "Version/sprint ID"},
                    "estimated_hours": {"type": "number", "description": "Estimated hours"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "due_date": {"type": "string", "description": "Due date YYYY-MM-DD"},
                    "parent_issue_id": {"type": "integer", "description": "Parent issue ID"}
                },
                "required": ["project_id", "subject"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_update_issue",
            "description": "Update an existing Redmine issue (status, priority, assignee, version, notes, etc.)",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "integer", "description": "Issue ID"},
                    "subject": {"type": "string", "description": "New subject"},
                    "status_id": {"type": "integer", "description": "New status ID"},
                    "priority_id": {"type": "integer", "description": "New priority ID"},
                    "tracker_id": {"type": "integer", "description": "New tracker ID"},
                    "assigned_to_id": {"type": "integer", "description": "New assignee user ID"},
                    "fixed_version_id": {"type": "integer", "description": "New version/sprint ID"},
                    "done_ratio": {"type": "integer", "description": "Completion percentage 0-100"},
                    "estimated_hours": {"type": "number", "description": "Estimated hours"},
                    "notes": {"type": "string", "description": "Comment to add"}
                },
                "required": ["issue_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_delete_issue",
            "description": "Delete a Redmine issue permanently.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "integer", "description": "Issue ID to delete"}
                },
                "required": ["issue_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_products",
            "description": "Scrape products. Use search_products_smart instead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL"},
                    "product_selector": {"type": "string", "description": "CSS selector"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_duckduckgo",
            "description": "Search DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Query"},
                    "max_results": {"type": "integer", "description": "Max results"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_products_smart",
            "description": "Smart product search via DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_name": {"type": "string", "description": "Product name"},
                    "site": {"type": "string", "description": "Site filter"}
                },
                "required": ["product_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_sprint_analytics",
            "description": "Complete sprint analytics: committed, completed, remaining, in-progress, blocked, spillover, burndown status. USE THIS for any sprint/iteration questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID or identifier (required)"},
                    "version_id": {"type": "integer", "description": "Version/sprint ID (optional - auto-detects current)"},
                    "version_name": {"type": "string", "description": "Sprint name to search for (optional)"}
                },
                "required": ["project_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_backlog_analytics",
            "description": "Backlog metrics: total size, high-priority open, unestimated %, aging, monthly created/closed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID or identifier (optional)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_team_workload",
            "description": "Team workload: tasks per member, overloaded members, unassigned issues. Full pagination.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID or identifier (optional)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_quality_metrics",
            "description": "Bug/quality: open bugs, critical bugs, bug-to-story ratio, avg resolution time, recent bugs. USE THIS for bug questions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID or identifier (optional)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_cycle_time",
            "description": "Cycle time (In Progress->Closed) and lead time (Created->Closed) from journal history. Also counts re-opened tickets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID or identifier (optional)"},
                    "sample_size": {"type": "integer", "description": "Number of recent closed issues to analyze (default: 50)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_release_status",
            "description": "Release/version completion: features done, scope %, unresolved issues per release.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID or identifier (required)"},
                    "version_id": {"type": "integer", "description": "Version ID (optional - shows all open if omitted)"},
                    "version_name": {"type": "string", "description": "Version name to search (optional)"}
                },
                "required": ["project_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_velocity_trend",
            "description": "Velocity over last N closed sprints: completed issues & hours per sprint, trend (stable/increasing/decreasing).",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID or identifier (required)"},
                    "sprints": {"type": "integer", "description": "Number of sprints (default: 5)"}
                },
                "required": ["project_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_throughput",
            "description": "Throughput: created vs closed per week, weekly breakdown, trend (positive/negative).",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID or identifier (optional)"},
                    "weeks": {"type": "integer", "description": "Number of weeks (default: 4)"}
                }
            }
        }
    }
]


# Lifespan context manager for startup/shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Backend server starting...")
    print(f"Using Groq LLM with model: llama-3.1-8b-instant")
    print(f"MCP tools available: {len(MCP_TOOLS)}")
    yield
    # Shutdown
    print("Backend server shutting down...")


# Initialize FastAPI with lifespan
app = FastAPI(title="MCP Music Backend", lifespan=lifespan)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    conversationHistory: list[Message] = []
    enabledTools: dict = {"music": True, "playwright": True, "redmine": True}


class ChatResponse(BaseModel):
    response: str
    conversationHistory: list[Message]


# Import MCP tools
import httpx
import asyncio
from playwright.async_api import async_playwright


async def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Call MCP tool directly using iTunes API or Playwright"""
    
    if tool_name == "play_music":
        query = arguments.get("query", "")
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://itunes.apple.com/search",
                params={"term": query, "entity": "song", "limit": 1}
            )
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return json.dumps({"success": False, "error": f"No music found for: {query}"})
            
            track = results[0]
            
            if not track.get("previewUrl"):
                return json.dumps({"success": False, "error": f"No preview available"})
            
            return json.dumps({
                "success": True,
                "action": "PLAY_MUSIC",
                "message": f"Now playing: {track.get('trackName')} by {track.get('artistName')}",
                "track": {
                    "name": track.get("trackName"),
                    "artist": track.get("artistName"),
                    "album": track.get("collectionName"),
                    "previewUrl": track.get("previewUrl"),
                    "artworkUrl": track.get("artworkUrl100"),
                    "genre": track.get("primaryGenreName"),
                    "releaseDate": track.get("releaseDate")
                }
            }, indent=2)
    
    elif tool_name == "search_music":
        query = arguments.get("query", "")
        search_type = arguments.get("type", "song")
        limit = arguments.get("limit", 10)
        
        type_map = {"song": "song", "artist": "musicArtist", "album": "album"}
        entity = type_map.get(search_type, "song")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://itunes.apple.com/search",
                params={"term": query, "entity": entity, "limit": limit}
            )
            data = response.json()
            results = data.get("results", [])
            
            formatted_results = []
            for item in results:
                formatted_results.append({
                    "name": item.get("trackName") or item.get("artistName") or item.get("collectionName"),
                    "artist": item.get("artistName"),
                    "album": item.get("collectionName"),
                    "genre": item.get("primaryGenreName"),
                    "previewUrl": item.get("previewUrl"),
                    "artworkUrl": item.get("artworkUrl100")
                })
            
            return json.dumps({
                "query": query,
                "type": search_type,
                "count": len(formatted_results),
                "results": formatted_results
            }, indent=2)
    
    elif tool_name == "get_artist_info":
        artist = arguments.get("artist", "")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://itunes.apple.com/search",
                params={"term": artist, "entity": "musicArtist", "limit": 1}
            )
            data = response.json()
            results = data.get("results", [])
            
            if not results:
                return json.dumps({"error": f"Artist not found: {artist}"})
            
            artist_data = results[0]
            
            return json.dumps({
                "name": artist_data.get("artistName"),
                "genre": artist_data.get("primaryGenreName"),
                "artistLinkUrl": artist_data.get("artistLinkUrl")
            }, indent=2)
    
    # Playwright tools
    elif tool_name == "browse_website":
        url = arguments.get("url", "")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                title = await page.title()
                text_content = await page.inner_text("body")
                
                # Limit text content
                if len(text_content) > 5000:
                    text_content = text_content[:5000] + "... (truncated)"
                
                await browser.close()
                
                return json.dumps({
                    "success": True,
                    "url": url,
                    "title": title,
                    "content": text_content
                }, indent=2)
                
            except Exception as e:
                await browser.close()
                return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "screenshot_website":
        url = arguments.get("url", "")
        filename = arguments.get("filename", "screenshot.png")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                screenshot_path = f"screenshots/{filename}"
                os.makedirs("screenshots", exist_ok=True)
                await page.screenshot(path=screenshot_path, full_page=True)
                
                await browser.close()
                
                return json.dumps({
                    "success": True,
                    "url": url,
                    "screenshot_path": screenshot_path,
                    "message": f"Screenshot saved to {screenshot_path}"
                }, indent=2)
                
            except Exception as e:
                await browser.close()
                return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "extract_links":
        url = arguments.get("url", "")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                links = await page.evaluate("""
                    () => {
                        const anchors = Array.from(document.querySelectorAll('a'));
                        return anchors.map(a => ({
                            text: a.innerText.trim(),
                            href: a.href
                        })).filter(link => link.href && link.href.startsWith('http'));
                    }
                """)
                
                await browser.close()
                
                if len(links) > 50:
                    links = links[:50]
                
                return json.dumps({
                    "success": True,
                    "url": url,
                    "link_count": len(links),
                    "links": links
                }, indent=2)
                
            except Exception as e:
                await browser.close()
                return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "search_google":
        query = arguments.get("query", "")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                await page.goto(f"https://www.google.com/search?q={query}", wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector("div#search", timeout=10000)
                
                results = await page.evaluate("""
                    () => {
                        const items = [];
                        const resultDivs = document.querySelectorAll('div.g');
                        
                        for (let i = 0; i < Math.min(10, resultDivs.length); i++) {
                            const div = resultDivs[i];
                            const titleEl = div.querySelector('h3');
                            const linkEl = div.querySelector('a');
                            const snippetEl = div.querySelector('div[data-sncf]');
                            
                            if (titleEl && linkEl) {
                                items.push({
                                    title: titleEl.innerText,
                                    link: linkEl.href,
                                    snippet: snippetEl ? snippetEl.innerText : ''
                                });
                            }
                        }
                        
                        return items;
                    }
                """)
                
                await browser.close()
                
                return json.dumps({
                    "success": True,
                    "query": query,
                    "result_count": len(results),
                    "results": results
                }, indent=2)
                
            except Exception as e:
                await browser.close()
                return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "scrape_products":
        url = arguments.get("url", "")
        product_selector = arguments.get("product_selector")
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                locale='en-US',
                extra_http_headers={
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }
            )
            
            page = await context.new_page()
            
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                window.chrome = { runtime: {} };
            """)
            
            try:
                await page.goto(url, wait_until="networkidle", timeout=45000)
                await page.wait_for_timeout(2000)
                
                if product_selector:
                    products = await page.evaluate(f"""
                        () => {{
                            const items = document.querySelectorAll('{product_selector}');
                            return Array.from(items).slice(0, 20).map(item => ({{
                                text: item.innerText.trim(),
                                html: item.innerHTML.substring(0, 500)
                            }}));
                        }}
                    """)
                else:
                    products = await page.evaluate("""
                        () => {
                            const selectors = [
                                '[data-product]', '.product', '.product-item',
                                '[class*="product"]', '[class*="Product"]'
                            ];
                            
                            for (const selector of selectors) {
                                const items = document.querySelectorAll(selector);
                                if (items.length > 0) {
                                    return Array.from(items).slice(0, 20).map(item => ({
                                        text: item.innerText.trim().substring(0, 200),
                                        classes: item.className
                                    }));
                                }
                            }
                            return [];
                        }
                    """)
                
                page_title = await page.title()
                await browser.close()
                
                return json.dumps({
                    "success": True,
                    "url": url,
                    "title": page_title,
                    "products_found": len(products),
                    "products": products
                }, indent=2)
                
            except Exception as e:
                await browser.close()
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "suggestion": "Website may have bot protection. Consider using official APIs."
                })
    
    elif tool_name == "search_duckduckgo":
        query = arguments.get("query", "")
        max_results = arguments.get("max_results", 10)
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            try:
                await page.goto(f"https://duckduckgo.com/?q={query}", wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_selector('article[data-testid="result"]', timeout=10000)
                
                results = await page.evaluate(f"""
                    () => {{
                        const items = [];
                        const resultArticles = document.querySelectorAll('article[data-testid="result"]');
                        
                        for (let i = 0; i < Math.min({max_results}, resultArticles.length); i++) {{
                            const article = resultArticles[i];
                            const titleEl = article.querySelector('h2');
                            const linkEl = article.querySelector('a[data-testid="result-title-a"]');
                            const snippetEl = article.querySelector('[data-result="snippet"]');
                            
                            if (titleEl && linkEl) {{
                                items.push({{
                                    title: titleEl.innerText,
                                    link: linkEl.href,
                                    snippet: snippetEl ? snippetEl.innerText : ''
                                }});
                            }}
                        }}
                        
                        return items;
                    }}
                """)
                
                await browser.close()
                
                return json.dumps({
                    "success": True,
                    "query": query,
                    "result_count": len(results),
                    "results": results,
                    "source": "DuckDuckGo"
                }, indent=2)
                
            except Exception as e:
                await browser.close()
                return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "search_products_smart":
        product_name = arguments.get("product_name", "")
        site = arguments.get("site")
        
        search_query = f"site:{site} {product_name}" if site else f"{product_name} buy online india"
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']
            )
            
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )
            
            page = await context.new_page()
            
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            try:
                await page.goto(f"https://duckduckgo.com/?q={search_query}", wait_until="domcontentloaded", timeout=30000)
                
                # Wait for any results to appear
                await page.wait_for_timeout(3000)
                
                # Try multiple selectors for DuckDuckGo results
                results = await page.evaluate("""
                    () => {
                        const items = [];
                        
                        // Try different selectors
                        let resultElements = document.querySelectorAll('article[data-testid="result"]');
                        if (resultElements.length === 0) {
                            resultElements = document.querySelectorAll('li[data-layout="organic"]');
                        }
                        if (resultElements.length === 0) {
                            resultElements = document.querySelectorAll('.result');
                        }
                        
                        for (let i = 0; i < Math.min(15, resultElements.length); i++) {
                            const element = resultElements[i];
                            
                            // Try to find title and link
                            const titleEl = element.querySelector('h2, h3, .result__title');
                            const linkEl = element.querySelector('a[href]');
                            const snippetEl = element.querySelector('[data-result="snippet"], .result__snippet');
                            
                            if (linkEl && linkEl.href) {
                                try {
                                    const url = new URL(linkEl.href);
                                    items.push({
                                        title: titleEl ? titleEl.innerText : 'No title',
                                        link: linkEl.href,
                                        snippet: snippetEl ? snippetEl.innerText : '',
                                        domain: url.hostname
                                    });
                                } catch (e) {
                                    // Skip invalid URLs
                                }
                            }
                        }
                        
                        return items;
                    }
                """)
                
                await browser.close()
                
                if len(results) == 0:
                    return json.dumps({
                        "success": False,
                        "error": "No results found. DuckDuckGo may have changed its layout or the search returned no results.",
                        "suggestion": "Try a different search query or use search_google instead."
                    })
                
                by_domain = {}
                for result in results:
                    domain = result['domain']
                    if domain not in by_domain:
                        by_domain[domain] = []
                    by_domain[domain].append(result)
                
                return json.dumps({
                    "success": True,
                    "product": product_name,
                    "site_filter": site,
                    "total_results": len(results),
                    "results_by_domain": by_domain,
                    "all_results": results,
                    "tip": "Click the links to visit product pages directly. This avoids bot detection."
                }, indent=2)
                
            except Exception as e:
                await browser.close()
                return json.dumps({
                    "success": False,
                    "error": str(e),
                    "suggestion": "Try using search_google or search_duckduckgo instead."
                })
    
    # ===== REDMINE TOOLS (All use direct API via redmine agent) =====
    
    elif tool_name.startswith("redmine_"):
        # Import the MCP agent's redmine module and call tools directly
        import sys
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))
        from agents.redmine import (
            _api_get, _api_post, _api_put, _api_delete,
            _fetch_all_issues, _get_total_count, _resolve_project_id,
            _list_versions, _find_active_version, _issue_summary, _ok, _err,
        )
        
        try:
            if tool_name == "redmine_list_projects":
                all_projects = []
                offset = 0
                while True:
                    data = await _api_get("/projects.json", {"limit": 100, "offset": offset})
                    for p in data.get("projects", []):
                        all_projects.append({
                            "id": p.get("id"), "name": p.get("name"),
                            "identifier": p.get("identifier"),
                            "description": (p.get("description") or "")[:200],
                            "status": p.get("status"),
                        })
                    if offset + 100 >= data.get("total_count", 0):
                        break
                    offset += 100
                return _ok({"count": len(all_projects), "projects": all_projects})
            
            elif tool_name == "redmine_list_versions":
                pid = await _resolve_project_id(arguments.get("project_id"))
                if pid is None:
                    return _err(f"Could not resolve project: {arguments.get('project_id')}")
                versions = await _list_versions(pid)
                result = [{"id": v.get("id"), "name": v.get("name"), "status": v.get("status"), "due_date": v.get("due_date")} for v in versions]
                return _ok({"project_id": pid, "count": len(result), "versions": result})
            
            elif tool_name == "redmine_list_trackers":
                data = await _api_get("/trackers.json")
                trackers = [{"id": t["id"], "name": t["name"]} for t in data.get("trackers", [])]
                return _ok({"trackers": trackers})
            
            elif tool_name == "redmine_list_statuses":
                data = await _api_get("/issue_statuses.json")
                statuses = [{"id": s["id"], "name": s["name"], "is_closed": s.get("is_closed", False)} for s in data.get("issue_statuses", [])]
                return _ok({"statuses": statuses})
            
            elif tool_name == "redmine_list_users":
                project_id = arguments.get("project_id")
                if project_id:
                    pid = await _resolve_project_id(project_id)
                    if pid is None:
                        return _err(f"Could not resolve project: {project_id}")
                    data = await _api_get(f"/projects/{pid}/memberships.json", {"limit": 100})
                    members = []
                    for m in data.get("memberships", []):
                        user = m.get("user")
                        if user:
                            members.append({"id": user.get("id"), "name": user.get("name")})
                    return _ok({"project_id": pid, "count": len(members), "members": members})
                else:
                    data = await _api_get("/users.json", {"limit": 100, "status": 1})
                    users = [{"id": u["id"], "name": f"{u.get('firstname','')} {u.get('lastname','')}".strip()} for u in data.get("users", [])]
                    return _ok({"count": len(users), "users": users})
            
            elif tool_name == "redmine_list_issues":
                params = {}
                status = arguments.get("status", "open")
                status_map = {"open": "open", "closed": "closed", "all": "*"}
                params["status_id"] = status_map.get(status, "*")
                params["sort"] = arguments.get("sort", "updated_on:desc")
                
                pid_str = arguments.get("project_id")
                if pid_str:
                    pid = await _resolve_project_id(pid_str)
                    if pid:
                        params["project_id"] = pid
                for key in ("tracker_id", "assigned_to_id", "fixed_version_id", "priority_id"):
                    if arguments.get(key):
                        params[key] = arguments[key]
                
                limit = arguments.get("limit", 25)
                if limit == -1:
                    issues = await _fetch_all_issues(params)
                    result_issues = [_issue_summary(i) for i in issues]
                    return _ok({"count": len(result_issues), "total_count": len(result_issues), "issues": result_issues})
                else:
                    params["limit"] = min(limit, 100)
                    data = await _api_get("/issues.json", params)
                    result_issues = [_issue_summary(i) for i in data.get("issues", [])]
                    return _ok({"count": len(result_issues), "total_count": data.get("total_count", 0), "issues": result_issues})
            
            elif tool_name == "redmine_get_issue":
                issue_id = arguments.get("issue_id")
                data = await _api_get(f"/issues/{issue_id}.json", {"include": "journals,children,relations,watchers,attachments"})
                issue = data.get("issue", {})
                journals = []
                for j in issue.get("journals", []):
                    entry = {"id": j.get("id"), "user": (j.get("user") or {}).get("name"), "created_on": j.get("created_on"), "notes": j.get("notes") or None, "details": []}
                    for d in j.get("details", []):
                        entry["details"].append({"property": d.get("property"), "name": d.get("name"), "old_value": d.get("old_value"), "new_value": d.get("new_value")})
                    if entry["notes"] or entry["details"]:
                        journals.append(entry)
                result = {**_issue_summary(issue), "description": issue.get("description"), "children": issue.get("children", []), "relations": issue.get("relations", []), "journals": journals[-10:]}
                return _ok({"issue": result})
            
            elif tool_name == "redmine_create_issue":
                pid = await _resolve_project_id(arguments.get("project_id"))
                issue_fields = {
                    "project_id": pid or arguments.get("project_id"),
                    "subject": arguments.get("subject"),
                    "description": arguments.get("description", ""),
                    "tracker_id": arguments.get("tracker_id", 1),
                    "priority_id": arguments.get("priority_id", 2),
                }
                for key in ("assigned_to_id", "fixed_version_id", "estimated_hours", "start_date", "due_date", "parent_issue_id", "category_id"):
                    if arguments.get(key) is not None:
                        issue_fields[key] = arguments[key]
                data = await _api_post("/issues.json", {"issue": issue_fields})
                issue = data.get("issue", {})
                return _ok({"message": f"Issue #{issue.get('id')} created successfully", "issue": _issue_summary(issue)})
            
            elif tool_name == "redmine_update_issue":
                issue_id = arguments.get("issue_id")
                fields = {}
                for key in ("subject", "description", "status_id", "priority_id", "tracker_id", "assigned_to_id", "fixed_version_id", "done_ratio", "estimated_hours", "start_date", "due_date", "notes"):
                    if arguments.get(key) is not None:
                        fields[key] = arguments[key]
                await _api_put(f"/issues/{issue_id}.json", {"issue": fields})
                return _ok({"message": f"Issue #{issue_id} updated successfully"})
            
            elif tool_name == "redmine_delete_issue":
                issue_id = arguments.get("issue_id")
                await _api_delete(f"/issues/{issue_id}.json")
                return _ok({"message": f"Issue #{issue_id} deleted successfully"})
            
            elif tool_name == "redmine_sprint_analytics":
                from agents.redmine import _find_active_version as _fav
                from datetime import datetime as dt, timedelta as td
                pid = await _resolve_project_id(arguments.get("project_id"))
                if pid is None:
                    return _err(f"Could not resolve project: {arguments.get('project_id')}")
                versions = await _list_versions(pid)
                target = None
                vid_arg = arguments.get("version_id")
                vname_arg = arguments.get("version_name")
                if vid_arg:
                    target = next((v for v in versions if v["id"] == vid_arg), None)
                elif vname_arg:
                    target = next((v for v in versions if vname_arg.lower() in v.get("name", "").lower()), None)
                else:
                    target = await _fav(pid)
                if not target:
                    return _err("No matching version/sprint found. Use redmine_list_versions to see available versions.")
                vid = target["id"]
                issues = await _fetch_all_issues({"project_id": pid, "fixed_version_id": vid, "status_id": "*"})
                sdata = await _api_get("/issue_statuses.json")
                closed_ids = {s["id"] for s in sdata.get("issue_statuses", []) if s.get("is_closed")}
                total = len(issues)
                completed = sum(1 for i in issues if (i.get("status") or {}).get("id") in closed_ids)
                in_prog = sum(1 for i in issues if (i.get("status") or {}).get("name", "").lower() in ("in progress", "in_progress"))
                blocked = sum(1 for i in issues if (i.get("status") or {}).get("name", "").lower() in ("feedback", "blocked"))
                remaining = total - completed
                pct = round((completed / total * 100) if total > 0 else 0, 1)
                est = round(sum(float(i.get("estimated_hours") or 0) for i in issues), 1)
                spent = round(sum(float(i.get("spent_hours") or 0) for i in issues), 1)
                by_status = {}
                for i in issues:
                    sn = (i.get("status") or {}).get("name", "Unknown")
                    by_status[sn] = by_status.get(sn, 0) + 1
                return _ok({
                    "sprint": {"name": target.get("name"), "version_id": vid, "status": target.get("status"), "due_date": target.get("due_date")},
                    "metrics": {"total_committed": total, "completed": completed, "remaining": remaining, "in_progress": in_prog, "blocked": blocked, "completion_percentage": pct, "total_estimated_hours": est, "total_spent_hours": spent},
                    "breakdown_by_status": by_status,
                    "burndown_assessment": "on_track" if pct >= 60 else ("at_risk" if pct >= 30 else "behind"),
                })
            
            elif tool_name == "redmine_backlog_analytics":
                from datetime import datetime as dt
                params_ba = {"status_id": "open"}
                pid = None
                if arguments.get("project_id"):
                    pid = await _resolve_project_id(arguments.get("project_id"))
                    if pid:
                        params_ba["project_id"] = pid
                total_open = await _get_total_count(params_ba)
                high = await _get_total_count({**params_ba, "priority_id": 3})
                urgent = await _get_total_count({**params_ba, "priority_id": 4})
                immediate = await _get_total_count({**params_ba, "priority_id": 5})
                open_issues = await _fetch_all_issues(params_ba, max_issues=2000)
                unest = sum(1 for i in open_issues if not i.get("estimated_hours"))
                pct_unest = round((unest / len(open_issues) * 100) if open_issues else 0, 1)
                now = dt.utcnow()
                ages = []
                for i in open_issues:
                    co = i.get("created_on")
                    if co:
                        try:
                            created = dt.fromisoformat(co.replace("Z", "+00:00")).replace(tzinfo=None)
                            ages.append((now - created).days)
                        except Exception:
                            pass
                avg_age = round(sum(ages) / len(ages), 1) if ages else 0
                ms = now.replace(day=1).strftime("%Y-%m-%d")
                bp = {"project_id": pid} if pid else {}
                created_m = await _get_total_count({**bp, "created_on": f">={ms}", "status_id": "*"})
                closed_m = await _get_total_count({**bp, "closed_on": f">={ms}", "status_id": "*"})
                return _ok({
                    "backlog": {"total_open": total_open, "high_priority_open": high + urgent + immediate, "unestimated_count": unest, "unestimated_percentage": pct_unest},
                    "aging": {"average_days_open": avg_age},
                    "monthly_activity": {"month": now.strftime("%B %Y"), "created_this_month": created_m, "closed_this_month": closed_m, "net_change": created_m - closed_m},
                    "project_id": pid,
                })
            
            elif tool_name == "redmine_team_workload":
                params_tw = {"status_id": "open"}
                pid = None
                if arguments.get("project_id"):
                    pid = await _resolve_project_id(arguments.get("project_id"))
                    if pid:
                        params_tw["project_id"] = pid
                issues = await _fetch_all_issues(params_tw)
                workload = {}
                unassigned = 0
                for i in issues:
                    assignee = i.get("assigned_to")
                    if assignee:
                        name = assignee.get("name", "Unknown")
                        workload[name] = workload.get(name, 0) + 1
                    else:
                        unassigned += 1
                sorted_wl = dict(sorted(workload.items(), key=lambda x: x[1], reverse=True))
                overloaded = {k: v for k, v in sorted_wl.items() if v > 10}
                return _ok({"total_open_issues": len(issues), "unassigned_issues": unassigned, "team_size": len(workload), "workload_by_member": sorted_wl, "overloaded_members": overloaded, "project_id": pid})
            
            elif tool_name == "redmine_quality_metrics":
                base_qm = {}
                pid = None
                if arguments.get("project_id"):
                    pid = await _resolve_project_id(arguments.get("project_id"))
                    if pid:
                        base_qm["project_id"] = pid
                tdata = await _api_get("/trackers.json")
                bug_tid = None
                story_tids = []
                for t in tdata.get("trackers", []):
                    if t["name"].lower() == "bug":
                        bug_tid = t["id"]
                    elif t["name"].lower() in ("story", "user story", "feature"):
                        story_tids.append(t["id"])
                if not bug_tid:
                    return _err("No 'Bug' tracker found.")
                open_bugs = await _get_total_count({**base_qm, "status_id": "open", "tracker_id": bug_tid})
                total_bugs = await _get_total_count({**base_qm, "status_id": "*", "tracker_id": bug_tid})
                high_b = await _get_total_count({**base_qm, "status_id": "open", "tracker_id": bug_tid, "priority_id": 3})
                urgent_b = await _get_total_count({**base_qm, "status_id": "open", "tracker_id": bug_tid, "priority_id": 4})
                imm_b = await _get_total_count({**base_qm, "status_id": "open", "tracker_id": bug_tid, "priority_id": 5})
                total_stories = 0
                for sid in story_tids:
                    total_stories += await _get_total_count({**base_qm, "status_id": "*", "tracker_id": sid})
                ratio = round(total_bugs / total_stories, 2) if total_stories > 0 else None
                return _ok({"bug_metrics": {"open_bugs": open_bugs, "closed_bugs": total_bugs - open_bugs, "total_bugs": total_bugs, "critical_open": {"high": high_b, "urgent": urgent_b, "immediate": imm_b, "total_critical": high_b + urgent_b + imm_b}, "bug_to_story_ratio": ratio, "total_stories_or_features": total_stories}, "project_id": pid})
            
            elif tool_name == "redmine_cycle_time":
                from datetime import datetime as dt
                base_ct = {"status_id": "closed", "sort": "closed_on:desc"}
                pid = None
                if arguments.get("project_id"):
                    pid = await _resolve_project_id(arguments.get("project_id"))
                    if pid:
                        base_ct["project_id"] = pid
                sample = arguments.get("sample_size", 50)
                closed_issues = await _fetch_all_issues(base_ct, max_issues=sample)
                lead_times = []
                cycle_times = []
                reopened = 0
                for issue in closed_issues:
                    co = issue.get("created_on")
                    cl = issue.get("closed_on")
                    if co and cl:
                        try:
                            created = dt.fromisoformat(co.replace("Z", "+00:00")).replace(tzinfo=None)
                            closed = dt.fromisoformat(cl.replace("Z", "+00:00")).replace(tzinfo=None)
                            lead_times.append((closed - created).total_seconds() / 86400)
                        except Exception:
                            pass
                    try:
                        idata = await _api_get(f"/issues/{issue['id']}.json", {"include": "journals"})
                        journals = idata.get("issue", {}).get("journals", [])
                        ip_at = None
                        was_reopen = False
                        for j in journals:
                            for d in j.get("details", []):
                                if d.get("name") == "status_id":
                                    if str(d.get("new_value", "")) == "2" and ip_at is None:
                                        ip_at = j.get("created_on")
                                    if str(d.get("old_value", "")) == "5" and str(d.get("new_value", "")) != "5":
                                        was_reopen = True
                        if was_reopen:
                            reopened += 1
                        if ip_at and cl:
                            ip_dt = dt.fromisoformat(ip_at.replace("Z", "+00:00")).replace(tzinfo=None)
                            cl_dt = dt.fromisoformat(cl.replace("Z", "+00:00")).replace(tzinfo=None)
                            ct = (cl_dt - ip_dt).total_seconds() / 86400
                            if ct >= 0:
                                cycle_times.append(ct)
                    except Exception:
                        pass
                avg_lead = round(sum(lead_times) / len(lead_times), 1) if lead_times else None
                avg_cycle = round(sum(cycle_times) / len(cycle_times), 1) if cycle_times else None
                return _ok({"sample_size": len(closed_issues), "lead_time": {"average_days": avg_lead}, "cycle_time": {"average_days": avg_cycle, "samples": len(cycle_times)}, "reopened_tickets": {"count": reopened, "percentage": round(reopened / len(closed_issues) * 100, 1) if closed_issues else 0}, "project_id": pid})
            
            elif tool_name == "redmine_release_status":
                pid = await _resolve_project_id(arguments.get("project_id"))
                if pid is None:
                    return _err(f"Could not resolve project: {arguments.get('project_id')}")
                versions = await _list_versions(pid)
                targets = []
                if arguments.get("version_id"):
                    targets = [v for v in versions if v["id"] == arguments["version_id"]]
                elif arguments.get("version_name"):
                    needle = arguments["version_name"].lower()
                    targets = [v for v in versions if needle in v.get("name", "").lower()]
                else:
                    targets = [v for v in versions if v.get("status") == "open"]
                if not targets:
                    return _err("No matching versions found.")
                sdata = await _api_get("/issue_statuses.json")
                closed_ids = {s["id"] for s in sdata.get("issue_statuses", []) if s.get("is_closed")}
                results = []
                for v in targets:
                    issues = await _fetch_all_issues({"project_id": pid, "fixed_version_id": v["id"], "status_id": "*"})
                    total = len(issues)
                    closed = sum(1 for i in issues if (i.get("status") or {}).get("id") in closed_ids)
                    pct = round((closed / total * 100) if total > 0 else 0, 1)
                    results.append({"version_name": v.get("name"), "total_issues": total, "closed_issues": closed, "open_issues": total - closed, "completion_percentage": pct})
                return _ok({"project_id": pid, "releases": results})
            
            elif tool_name == "redmine_velocity_trend":
                from datetime import datetime as dt
                pid = await _resolve_project_id(arguments.get("project_id"))
                if pid is None:
                    return _err(f"Could not resolve project: {arguments.get('project_id')}")
                versions = await _list_versions(pid)
                closed_v = [v for v in versions if v.get("status") == "closed"]
                def vdate(v):
                    dd = v.get("due_date") or v.get("updated_on", "")
                    try:
                        return dt.fromisoformat(dd.replace("Z", "+00:00").replace("T", " ").split("+")[0])
                    except Exception:
                        return dt(1970, 1, 1)
                closed_v.sort(key=vdate)
                sprints_n = arguments.get("sprints", 5)
                recent = closed_v[-sprints_n:] if len(closed_v) >= sprints_n else closed_v
                sdata = await _api_get("/issue_statuses.json")
                closed_ids = {s["id"] for s in sdata.get("issue_statuses", []) if s.get("is_closed")}
                vel = []
                for v in recent:
                    issues = await _fetch_all_issues({"project_id": pid, "fixed_version_id": v["id"], "status_id": "*"})
                    completed = [i for i in issues if (i.get("status") or {}).get("id") in closed_ids]
                    est = round(sum(float(i.get("estimated_hours") or 0) for i in completed), 1)
                    vel.append({"sprint": v.get("name"), "completed_issues": len(completed), "total_issues": len(issues), "completed_estimated_hours": est})
                if len(vel) >= 2:
                    vals = [v["completed_issues"] for v in vel]
                    fh = sum(vals[:len(vals)//2]) / max(len(vals)//2, 1)
                    sh = sum(vals[len(vals)//2:]) / max(len(vals) - len(vals)//2, 1)
                    trend = "increasing" if sh > fh * 1.1 else ("decreasing" if sh < fh * 0.9 else "stable")
                    avg = round(sum(vals) / len(vals), 1)
                else:
                    trend = "insufficient_data"
                    avg = vel[0]["completed_issues"] if vel else 0
                return _ok({"project_id": pid, "sprints_analyzed": len(vel), "velocity_trend": trend, "average_velocity": avg, "per_sprint": vel})
            
            elif tool_name == "redmine_throughput":
                from datetime import datetime as dt, timedelta as td
                base_tp = {"status_id": "*"}
                pid = None
                if arguments.get("project_id"):
                    pid = await _resolve_project_id(arguments.get("project_id"))
                    if pid:
                        base_tp["project_id"] = pid
                weeks = arguments.get("weeks", 4)
                now = dt.utcnow()
                weekly = []
                for w in range(weeks):
                    we = now - td(days=w * 7)
                    ws = we - td(days=7)
                    ws_s = ws.strftime("%Y-%m-%d")
                    we_s = we.strftime("%Y-%m-%d")
                    created = await _get_total_count({**base_tp, "created_on": f"><{ws_s}|{we_s}"})
                    closed = await _get_total_count({**base_tp, "closed_on": f"><{ws_s}|{we_s}"})
                    weekly.append({"week": f"{ws_s} to {we_s}", "created": created, "closed": closed, "net": closed - created})
                weekly.reverse()
                tc = sum(w["created"] for w in weekly)
                tl = sum(w["closed"] for w in weekly)
                return _ok({"project_id": pid, "period_weeks": weeks, "total_created": tc, "total_closed": tl, "net_throughput": tl - tc, "trend": "positive" if tl >= tc else "negative", "avg_created_per_week": round(tc / weeks, 1), "avg_closed_per_week": round(tl / weeks, 1), "weekly_breakdown": weekly})
            
            else:
                return json.dumps({"success": False, "error": f"Unknown redmine tool: {tool_name}"})
        
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    return json.dumps({"error": "Unknown tool"})


# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "mcpConnected": True,
        "toolsAvailable": len(MCP_TOOLS)
    }


# Tools list endpoint
@app.get("/api/tools")
async def list_tools():
    return {
        "tools": [
            {
                "name": tool["function"]["name"],
                "description": tool["function"]["description"]
            }
            for tool in MCP_TOOLS
        ]
    }


# Chat endpoint with JSPLIT Architecture (Optimized)
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # JSPLIT Optimization: Try keyword detection first (faster)
        print(f"\n=== Query: '{request.message[:80]}...' ===")
        
        query_lower = request.message.lower()
        selected_category = None
        detection_method = None
        
        # Fast keyword-based category detection
        for cat_name, cat_info in TOOL_CATEGORIES.items():
            # Check if ANY keyword matches (not just top 3)
            if any(kw in query_lower for kw in cat_info["keywords"]):
                selected_category = cat_name
                detection_method = "keyword"
                print(f"✓ Fast detection: '{selected_category}' category (keyword match)")
                break
        
        # Only use LLM for category selection if keywords failed
        if not selected_category:
            print(f"⚠ Keyword detection failed, using LLM...")
            
            category_messages = [
                {
                    "role": "system",
                    "content": """Select ONE category:
- music: playing/searching music
- web: browsing/searching websites  
- redmine: managing projects/issues"""
                },
                {"role": "user", "content": request.message}
            ]
            
            category_response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=category_messages,
                tools=[CATEGORY_SELECTOR_TOOL],
                tool_choice="required",
                max_tokens=50,
                temperature=0.1
            )
            
            if category_response.choices[0].message.tool_calls:
                tool_call = category_response.choices[0].message.tool_calls[0]
                args = json.loads(tool_call.function.arguments)
                selected_category = args.get("category")
                detection_method = "llm"
                print(f"✓ LLM detection: '{selected_category}' category")
        
        # Fallback to first enabled category
        if not selected_category:
            for cat_name in ["music", "web", "redmine"]:
                if request.enabledTools.get(cat_name, True):
                    selected_category = cat_name
                    detection_method = "default"
                    print(f"✓ Default: '{selected_category}' category")
                    break
        
        # Get category-specific tools
        category_tool_names = TOOL_CATEGORIES[selected_category]["tools"]
        enabled_tools = [tool for tool in MCP_TOOLS if tool["function"]["name"] in category_tool_names]
        
        print(f"📦 Tools: {len(enabled_tools)}/{len(MCP_TOOLS)} | Savings: ~{(len(MCP_TOOLS) - len(enabled_tools)) * 150} tokens")
        
        # Build messages for task execution
        messages = [
            {
                "role": "system",
                "content": f"""You are a helpful assistant with {selected_category} tools.

IMPORTANT INSTRUCTIONS:
1. Call the appropriate tool to get data
2. After getting results, provide a CLEAR, FORMATTED answer
3. Use numbers and statistics from the tool results
4. Present data in an easy-to-read format
5. DO NOT show raw function calls to the user

For analytics questions:
- Calculate totals and percentages
- Compare numbers (completed vs remaining)
- Highlight important metrics
- Use bullet points or tables for clarity

Available tools: {', '.join(category_tool_names)}"""
            }
        ]
        
        # Add conversation history (limit to last 1 message only to save tokens)
        if request.conversationHistory:
            last_msg = request.conversationHistory[-1]
            # Only add if it's short
            if len(last_msg.content) < 200:
                messages.append({"role": last_msg.role, "content": last_msg.content})
        
        # Add current message
        messages.append({"role": "user", "content": request.message})
        
        # Execute with category-specific tools
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages[-4:],  # Keep only last 4 messages max
            tools=enabled_tools if enabled_tools else None,
            tool_choice="auto" if enabled_tools else "none",
            max_tokens=400,  # Reduced to 400 for faster, shorter responses
            temperature=0.5
        )
        
        assistant_message = response.choices[0].message
        music_data = None
        
        # Strict limits: Only 1 iteration, max 1 tool call
        max_tool_iterations = 1  # Only ONE round of tool calls
        tool_iteration_count = 0
        
        # Handle tool calls
        while assistant_message.tool_calls and tool_iteration_count < max_tool_iterations:
            tool_iteration_count += 1
            
            # Only process FIRST tool call
            tool_calls_to_process = assistant_message.tool_calls[:1]
            
            if len(assistant_message.tool_calls) > 1:
                print(f"⚠ LLM tried {len(assistant_message.tool_calls)} tools. Using only first one.")
            
            print(f"🔧 Executing: {tool_calls_to_process[0].function.name}")
            
            # Add assistant message to history
            messages.append({
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_calls_to_process
                ]
            })
            
            # Execute each tool call
            for tool_call in tool_calls_to_process:
                print(f"Executing tool: {tool_call.function.name}")
                
                try:
                    # Parse arguments
                    args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    
                    # Fix common type issues and null values for all redmine tools
                    if tool_call.function.name.startswith("redmine_"):
                        # Remove null values
                        args = {k: v for k, v in args.items() if v is not None and v != "null"}
                        
                        # Convert numeric project_id to string (new tools expect string)
                        if "project_id" in args and isinstance(args["project_id"], int):
                            args["project_id"] = str(args["project_id"])
                        
                        # Fix status values for list_issues
                        if tool_call.function.name == "redmine_list_issues" and "status" in args:
                            status_map = {
                                "committed": "all",
                                "in progress": "open",
                                "completed": "closed",
                                "done": "closed",
                                "finished": "closed",
                                "pending": "open",
                                "active": "open"
                            }
                            status_lower = str(args["status"]).lower()
                            if status_lower in status_map:
                                args["status"] = status_map[status_lower]
                                print(f"  Mapped status '{status_lower}' -> '{args['status']}'")
                            elif status_lower not in ["open", "closed", "all"]:
                                args["status"] = "all"
                        
                        # Fix limit type
                        if "limit" in args and isinstance(args["limit"], str):
                            try:
                                args["limit"] = int(args["limit"]) if args["limit"] != "-1" else -1
                            except:
                                args["limit"] = 25
                    
                    # Call MCP tool
                    tool_result = await call_mcp_tool(tool_call.function.name, args)
                    
                    # CRITICAL: Truncate large tool results to prevent token overflow
                    if len(tool_result) > 3000:  # If result is > 3000 chars
                        print(f"⚠ Tool result too large ({len(tool_result)} chars), truncating...")
                        try:
                            # Try to parse and summarize
                            result_data = json.loads(tool_result)
                            if "issues" in result_data and isinstance(result_data["issues"], list):
                                # Keep only first 5 issues
                                result_data["issues"] = result_data["issues"][:5]
                                result_data["note"] = f"Showing first 5 of {result_data.get('count', 'many')} issues (truncated for performance)"
                                tool_result = json.dumps(result_data, indent=2)
                            elif "results" in result_data and isinstance(result_data["results"], list):
                                # Keep only first 5 results
                                result_data["results"] = result_data["results"][:5]
                                tool_result = json.dumps(result_data, indent=2)
                            else:
                                # Generic truncation
                                tool_result = tool_result[:3000] + "\n... [truncated for token efficiency]"
                        except:
                            # If not JSON, just truncate
                            tool_result = tool_result[:3000] + "\n... [truncated for token efficiency]"
                        
                        print(f"✓ Truncated to {len(tool_result)} chars")
                    
                    # Capture music data
                    if tool_call.function.name == "play_music":
                        try:
                            music_data = json.loads(tool_result)
                        except:
                            pass
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": tool_result
                    })
                    
                except Exception as e:
                    print(f"Error executing tool {tool_call.function.name}: {e}")
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": json.dumps({"error": str(e)})
                    })
            
            # Continue conversation - provide final answer based on tool results
            final_prompt = {
                "role": "system",
                "content": """Based on the tool results above, provide a CLEAR, WELL-FORMATTED answer.

FORMATTING RULES:
1. Start with a direct answer to the question
2. Use numbers and statistics from the results
3. Format data clearly (use bullet points, comparisons)
4. Calculate percentages if relevant
5. Highlight key insights
6. DO NOT show raw JSON or function calls

Example good response:
"Based on the data:
• Completed: 32 stories (71%)
• Remaining: 13 stories (29%)
• Total committed: 45 stories

You're making good progress with over 70% completion!"
"""
            }
            
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=messages[-4:] + [final_prompt],
                tools=None,
                tool_choice="none",
                max_tokens=300,
                temperature=0.5
            )
            
            assistant_message = response.choices[0].message
            # Force stop - no more iterations
            break
        
        # Inject music data if available
        text_content = assistant_message.content or "I apologize, but I was unable to generate a response."
        
        if music_data:
            text_content = text_content + "\n\n" + json.dumps(music_data, indent=2)
        
        # Build response with SUMMARIZED history (don't include large JSON)
        # Only keep the user message and a short summary of assistant response
        assistant_summary = text_content
        if len(text_content) > 500:
            # If response is too long, create a summary
            assistant_summary = text_content[:500] + "... [response truncated for token efficiency]"
        
        new_history = request.conversationHistory[-4:] + [  # Keep only last 4 messages
            Message(role="user", content=request.message),
            Message(role="assistant", content=assistant_summary)
        ]
        
        print(f"✅ Done | Category: {selected_category} | Method: {detection_method} | Tools: {len(enabled_tools)}\n")
        
        return ChatResponse(
            response=text_content,  # Send full response to user
            conversationHistory=new_history  # But save summarized version
        )
        
    except Exception as e:
        error_msg = str(e)
        print(f"Chat error: {error_msg}")
        
        # Check if it's a rate limit error
        if "rate_limit" in error_msg.lower() or "429" in error_msg or "413" in error_msg:
            if "request too large" in error_msg.lower() or "413" in error_msg:
                raise HTTPException(
                    status_code=429, 
                    detail="Request too large. Your conversation history is too long. Please refresh the page to start a new conversation."
                )
            raise HTTPException(
                status_code=429, 
                detail="Groq API rate limit reached. Please wait a few minutes or get a new API key from https://console.groq.com/keys"
            )
        
        # Check if it's a tool validation error (Groq LLM issue)
        if "tool call validation failed" in error_msg or "tool_use_failed" in error_msg:
            raise HTTPException(
                status_code=500,
                detail="The AI model generated an invalid function call. This is a known issue with Groq's llama model. Please try rephrasing your question or try again."
            )
        
        raise HTTPException(status_code=500, detail=error_msg)


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 3001))
    uvicorn.run(app, host="0.0.0.0", port=port)
