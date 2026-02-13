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

# Redmine DB Cache Toggle (Global State)
REDMINE_DB_ENABLED = False

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
        "description": "Manage Redmine projects, issues, and tasks",
        "keywords": ["redmine", "issue", "project", "task", "ticket", "bug", "feature", "sprint", "story", "stories", 
                    "backlog", "velocity", "burndown", "team", "workload", "release", "committed", "completed", "cache", "db",
                    "analytics", "metrics", "cycle", "lead", "throughput", "trend"],
        "tools": ["redmine_list_projects", "redmine_list_issues", "redmine_get_issue", 
                 "redmine_create_issue", "redmine_update_issue", "redmine_db_control",
                 "redmine_sprint_status", "redmine_backlog_analytics", "redmine_team_workload",
                 "redmine_cycle_time", "redmine_bug_analytics", "redmine_release_status",
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
            "description": "List Redmine projects.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_list_issues",
            "description": "List Redmine issues (basic list only). For counts/metrics/analytics use analytics tools instead.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string", 
                        "enum": ["open", "closed", "all"],
                        "description": "Filter by status (default: open)"
                    },
                    "limit": {
                        "type": "integer", 
                        "description": "Max issues to return (default: 25)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_get_issue",
            "description": "Get Redmine issue details.",
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
            "description": "Create Redmine issue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {"type": "string", "description": "Project ID"},
                    "subject": {"type": "string", "description": "Title"},
                    "description": {"type": "string", "description": "Description"}
                },
                "required": ["project_id", "subject"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_update_issue",
            "description": "Update Redmine issue.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "integer", "description": "Issue ID"},
                    "notes": {"type": "string", "description": "Comment to add"}
                },
                "required": ["issue_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_db_control",
            "description": "Control Redmine DB cache (on/off/refresh/status). Cache enables fast analytics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["on", "off", "refresh", "status"],
                        "description": "Action: 'on' to enable cache, 'off' to disable, 'refresh' to update data, 'status' to check cache info"
                    }
                },
                "required": ["action"]
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
            "name": "redmine_sprint_status",
            "description": "Get sprint status analytics (committed, completed, remaining, blocked, progress)",
            "parameters": {
                "type": "object",
                "properties": {
                    "version_name": {"type": "string", "description": "Sprint/version name (optional)"},
                    "project_id": {
                        "type": ["integer", "string"],
                        "description": "Project ID or name (e.g., 6 or 'ncel'). Optional."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_backlog_analytics",
            "description": "Get backlog metrics (size, priority, aging, monthly trends)",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": ["integer", "string"],
                        "description": "Project ID or name (e.g., 6 or 'ncel'). Optional."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_team_workload",
            "description": "Get team workload distribution and overloaded members",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": ["integer", "string"],
                        "description": "Project ID or name (e.g., 6 or 'ncel'). Optional."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_cycle_time",
            "description": "Get cycle time and lead time metrics",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": ["integer", "string"],
                        "description": "Project ID or name (e.g., 6 or 'ncel'). Optional."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_bug_analytics",
            "description": "Get bug counts and metrics. USE THIS for questions about bugs (how many bugs, bug status, bug ratio). Returns total bugs, open bugs, critical bugs. NCEL project = ID 6.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": ["integer", "string"],
                        "description": "Project ID or name (e.g., 6 or 'ncel' for NCEL project). Optional - omit for all projects."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_release_status",
            "description": "Get release progress and completion status",
            "parameters": {
                "type": "object",
                "properties": {
                    "version_name": {"type": "string", "description": "Release/version name (optional)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_velocity_trend",
            "description": "Get velocity trend over last N sprints",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": ["integer", "string"],
                        "description": "Project ID or name (e.g., 6 or 'ncel'). Optional."
                    },
                    "sprints": {"type": "integer", "description": "Number of sprints (default: 5)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "redmine_throughput",
            "description": "Get throughput (created vs closed tickets over time)",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": ["integer", "string"],
                        "description": "Project ID or name (e.g., 6 or 'ncel'). Optional."
                    },
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
    
    # Redmine tools
    elif tool_name == "redmine_list_projects":
        if not os.getenv("REDMINE_URL") or not os.getenv("REDMINE_API_KEY"):
            return json.dumps({
                "success": False,
                "error": "Redmine not configured. Set REDMINE_URL and REDMINE_API_KEY in .env file."
            })
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{os.getenv('REDMINE_URL')}/projects.json",
                    headers={"X-Redmine-API-Key": os.getenv("REDMINE_API_KEY")},
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                projects = []
                for project in data.get("projects", []):
                    projects.append({
                        "id": project.get("id"),
                        "name": project.get("name"),
                        "identifier": project.get("identifier"),
                        "description": project.get("description"),
                        "status": project.get("status")
                    })
                
                return json.dumps({
                    "success": True,
                    "count": len(projects),
                    "projects": projects
                }, indent=2)
                
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "redmine_list_issues":
        if not os.getenv("REDMINE_URL") or not os.getenv("REDMINE_API_KEY"):
            return json.dumps({
                "success": False,
                "error": "Redmine not configured."
            })
        
        project_id = arguments.get("project_id")
        status = arguments.get("status", "open")
        limit = arguments.get("limit", 100)  # Increased from 25 to 100
        
        params = {
            "limit": min(limit, 100),  # Cap at 100 per request
            "status_id": "open" if status == "open" else ("closed" if status == "closed" else "*")
        }
        
        if project_id:
            params["project_id"] = project_id
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{os.getenv('REDMINE_URL')}/issues.json",
                    headers={"X-Redmine-API-Key": os.getenv("REDMINE_API_KEY")},
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                issues = []
                for issue in data.get("issues", []):
                    status_obj = issue.get("status") or {}
                    priority_obj = issue.get("priority") or {}
                    assigned_to_obj = issue.get("assigned_to") or {}
                    author_obj = issue.get("author") or {}
                    project_obj = issue.get("project") or {}
                    
                    issues.append({
                        "id": issue.get("id"),
                        "subject": issue.get("subject"),
                        "description": issue.get("description"),
                        "status": status_obj.get("name"),
                        "priority": priority_obj.get("name"),
                        "assigned_to": assigned_to_obj.get("name"),
                        "author": author_obj.get("name"),
                        "project": project_obj.get("name"),
                        "created_on": issue.get("created_on"),
                        "updated_on": issue.get("updated_on")
                    })
                
                return json.dumps({
                    "success": True,
                    "count": len(issues),
                    "total_count": data.get("total_count"),
                    "issues": issues
                }, indent=2)
                
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "redmine_get_issue":
        if not os.getenv("REDMINE_URL") or not os.getenv("REDMINE_API_KEY"):
            return json.dumps({
                "success": False,
                "error": "Redmine not configured."
            })
        
        issue_id = arguments.get("issue_id")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{os.getenv('REDMINE_URL')}/issues/{issue_id}.json",
                    headers={"X-Redmine-API-Key": os.getenv("REDMINE_API_KEY")},
                    params={"include": "journals,attachments"},
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                issue = data.get("issue", {})
                
                return json.dumps({
                    "success": True,
                    "issue": {
                        "id": issue.get("id"),
                        "subject": issue.get("subject"),
                        "description": issue.get("description"),
                        "status": issue.get("status", {}).get("name"),
                        "priority": issue.get("priority", {}).get("name"),
                        "tracker": issue.get("tracker", {}).get("name"),
                        "assigned_to": issue.get("assigned_to", {}).get("name"),
                        "author": issue.get("author", {}).get("name"),
                        "project": issue.get("project", {}).get("name"),
                        "created_on": issue.get("created_on"),
                        "updated_on": issue.get("updated_on"),
                        "done_ratio": issue.get("done_ratio"),
                        "estimated_hours": issue.get("estimated_hours"),
                        "spent_hours": issue.get("spent_hours")
                    }
                }, indent=2)
                
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "redmine_create_issue":
        if not os.getenv("REDMINE_URL") or not os.getenv("REDMINE_API_KEY"):
            return json.dumps({
                "success": False,
                "error": "Redmine not configured."
            })
        
        project_id = arguments.get("project_id")
        subject = arguments.get("subject")
        description = arguments.get("description", "")
        priority_id = arguments.get("priority_id", 2)
        tracker_id = arguments.get("tracker_id", 1)
        assigned_to_id = arguments.get("assigned_to_id")
        
        issue_data = {
            "issue": {
                "project_id": project_id,
                "subject": subject,
                "description": description,
                "priority_id": priority_id,
                "tracker_id": tracker_id
            }
        }
        
        if assigned_to_id:
            issue_data["issue"]["assigned_to_id"] = assigned_to_id
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{os.getenv('REDMINE_URL')}/issues.json",
                    headers={
                        "X-Redmine-API-Key": os.getenv("REDMINE_API_KEY"),
                        "Content-Type": "application/json"
                    },
                    json=issue_data,
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                
                issue = data.get("issue", {})
                
                return json.dumps({
                    "success": True,
                    "message": f"Issue #{issue.get('id')} created successfully",
                    "issue": {
                        "id": issue.get("id"),
                        "subject": issue.get("subject"),
                        "project": issue.get("project", {}).get("name"),
                        "status": issue.get("status", {}).get("name")
                    }
                }, indent=2)
                
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "redmine_update_issue":
        if not os.getenv("REDMINE_URL") or not os.getenv("REDMINE_API_KEY"):
            return json.dumps({
                "success": False,
                "error": "Redmine not configured."
            })
        
        issue_id = arguments.get("issue_id")
        issue_data = {"issue": {}}
        
        if arguments.get("subject"):
            issue_data["issue"]["subject"] = arguments.get("subject")
        if arguments.get("description"):
            issue_data["issue"]["description"] = arguments.get("description")
        if arguments.get("status_id"):
            issue_data["issue"]["status_id"] = arguments.get("status_id")
        if arguments.get("priority_id"):
            issue_data["issue"]["priority_id"] = arguments.get("priority_id")
        if arguments.get("assigned_to_id"):
            issue_data["issue"]["assigned_to_id"] = arguments.get("assigned_to_id")
        if arguments.get("done_ratio") is not None:
            issue_data["issue"]["done_ratio"] = arguments.get("done_ratio")
        if arguments.get("notes"):
            issue_data["issue"]["notes"] = arguments.get("notes")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(
                    f"{os.getenv('REDMINE_URL')}/issues/{issue_id}.json",
                    headers={
                        "X-Redmine-API-Key": os.getenv("REDMINE_API_KEY"),
                        "Content-Type": "application/json"
                    },
                    json=issue_data,
                    timeout=30.0
                )
                response.raise_for_status()
                
                return json.dumps({
                    "success": True,
                    "message": f"Issue #{issue_id} updated successfully"
                }, indent=2)
                
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "redmine_db_control":
        global REDMINE_DB_ENABLED
        
        action = arguments.get("action", "status")
        
        if action == "on":
            if REDMINE_DB_ENABLED:
                return json.dumps({
                    "success": True,
                    "message": "Redmine DB cache is already enabled",
                    "status": "enabled"
                })
            
            # Enable cache and trigger initial refresh
            REDMINE_DB_ENABLED = True
            
            try:
                from redmine_cache import cache
                refresh_result = await cache.refresh(force=True)
                
                return json.dumps({
                    "success": True,
                    "message": "Redmine DB cache enabled and initialized",
                    "status": "enabled",
                    "cache_info": refresh_result
                }, indent=2)
            except Exception as e:
                REDMINE_DB_ENABLED = False
                return json.dumps({
                    "success": False,
                    "error": f"Failed to initialize cache: {str(e)}"
                })
        
        elif action == "off":
            if not REDMINE_DB_ENABLED:
                return json.dumps({
                    "success": True,
                    "message": "Redmine DB cache is already disabled",
                    "status": "disabled"
                })
            
            REDMINE_DB_ENABLED = False
            return json.dumps({
                "success": True,
                "message": "Redmine DB cache disabled. Analytics will use direct API calls.",
                "status": "disabled"
            }, indent=2)
        
        elif action == "refresh":
            if not REDMINE_DB_ENABLED:
                return json.dumps({
                    "success": False,
                    "error": "Cache is disabled. Enable it first with action='on'"
                })
            
            try:
                from redmine_cache import cache
                refresh_result = await cache.refresh(force=True)
                
                return json.dumps({
                    "success": True,
                    "message": "Cache refreshed successfully",
                    "cache_info": refresh_result
                }, indent=2)
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": f"Failed to refresh cache: {str(e)}"
                })
        
        elif action == "status":
            if not REDMINE_DB_ENABLED:
                return json.dumps({
                    "success": True,
                    "status": "disabled",
                    "message": "Redmine DB cache is currently disabled"
                }, indent=2)
            
            try:
                from redmine_cache import cache
                cache_info = cache.get_cache_info()
                
                return json.dumps({
                    "success": True,
                    "status": "enabled",
                    "cache_info": cache_info
                }, indent=2)
            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": f"Failed to get cache status: {str(e)}"
                })
        
        else:
            return json.dumps({
                "success": False,
                "error": f"Unknown action: {action}. Use 'on', 'off', 'refresh', or 'status'"
            })
    
    # ===== ANALYTICS TOOLS (Cache-Powered) =====
    
    elif tool_name == "redmine_sprint_status":
        # Use direct API for accurate counts
        try:
            from redmine_direct import sprint_count
            version_name = arguments.get("version_name")
            project_id = arguments.get("project_id")
            result = await sprint_count(project_id, version_name)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "redmine_backlog_analytics":
        # Use direct API for accurate counts
        try:
            from redmine_direct import backlog_count
            project_id = arguments.get("project_id")
            result = await backlog_count(project_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "redmine_team_workload":
        if not REDMINE_DB_ENABLED:
            return json.dumps({
                "success": False,
                "error": "Redmine DB cache is disabled. Enable it first with 'redmine_db_control' action='on'"
            })
        
        try:
            from redmine_analytics import team_workload_analytics
            project_id = arguments.get("project_id")
            result = team_workload_analytics(project_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "redmine_cycle_time":
        if not REDMINE_DB_ENABLED:
            return json.dumps({
                "success": False,
                "error": "Redmine DB cache is disabled. Enable it first with 'redmine_db_control' action='on'"
            })
        
        try:
            from redmine_analytics import cycle_time_analytics
            project_id = arguments.get("project_id")
            result = cycle_time_analytics(project_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "redmine_bug_analytics":
        # Use direct API for accurate counts
        try:
            from redmine_direct import bug_count
            project_id = arguments.get("project_id")
            result = await bug_count(project_id)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "redmine_release_status":
        if not REDMINE_DB_ENABLED:
            return json.dumps({
                "success": False,
                "error": "Redmine DB cache is disabled. Enable it first with 'redmine_db_control' action='on'"
            })
        
        try:
            from redmine_analytics import release_analytics
            version_name = arguments.get("version_name")
            result = release_analytics(version_name)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "redmine_velocity_trend":
        if not REDMINE_DB_ENABLED:
            return json.dumps({
                "success": False,
                "error": "Redmine DB cache is disabled. Enable it first with 'redmine_db_control' action='on'"
            })
        
        try:
            from redmine_analytics import velocity_trend_analytics
            project_id = arguments.get("project_id")
            sprints = arguments.get("sprints", 5)
            result = velocity_trend_analytics(project_id, sprints)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    elif tool_name == "redmine_throughput":
        if not REDMINE_DB_ENABLED:
            return json.dumps({
                "success": False,
                "error": "Redmine DB cache is disabled. Enable it first with 'redmine_db_control' action='on'"
            })
        
        try:
            from redmine_analytics import throughput_analytics
            project_id = arguments.get("project_id")
            weeks = arguments.get("weeks", 4)
            result = throughput_analytics(project_id, weeks)
            return json.dumps(result, indent=2)
        except Exception as e:
            return json.dumps({"success": False, "error": str(e)})
    
    return json.dumps({"error": "Unknown tool"})


# Direct Redmine DB Cache Control Endpoint (for UI toggle)
@app.post("/api/redmine-cache")
async def redmine_cache_control(request: dict):
    global REDMINE_DB_ENABLED
    
    action = request.get("action", "status")
    
    if action == "on":
        if REDMINE_DB_ENABLED:
            return {
                "success": True,
                "message": "Redmine DB cache is already enabled",
                "status": "enabled"
            }
        
        # Enable cache and trigger initial refresh
        REDMINE_DB_ENABLED = True
        
        try:
            from redmine_cache import cache
            refresh_result = await cache.refresh(force=True)
            
            return {
                "success": True,
                "message": "Redmine DB cache enabled and initialized",
                "status": "enabled",
                "cache_info": refresh_result
            }
        except Exception as e:
            REDMINE_DB_ENABLED = False
            return {
                "success": False,
                "error": f"Failed to initialize cache: {str(e)}"
            }
    
    elif action == "off":
        if not REDMINE_DB_ENABLED:
            return {
                "success": True,
                "message": "Redmine DB cache is already disabled",
                "status": "disabled"
            }
        
        REDMINE_DB_ENABLED = False
        return {
            "success": True,
            "message": "Redmine DB cache disabled",
            "status": "disabled"
        }
    
    elif action == "status":
        if not REDMINE_DB_ENABLED:
            return {
                "success": True,
                "status": "disabled",
                "message": "Redmine DB cache is currently disabled"
            }
        
        try:
            from redmine_cache import cache
            cache_info = cache.get_cache_info()
            
            return {
                "success": True,
                "status": "enabled",
                "cache_info": cache_info
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to get cache status: {str(e)}"
            }
    
    else:
        return {
            "success": False,
            "error": f"Unknown action: {action}. Use 'on', 'off', or 'status'"
        }


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
                    
                    # Fix common type issues and null values
                    if tool_call.function.name == "redmine_list_issues":
                        # Remove null values
                        args = {k: v for k, v in args.items() if v is not None and v != "null"}
                        
                        # Fix status - map invalid values to valid ones
                        if "status" in args:
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
                                args["status"] = "all"  # Default to all if invalid
                        
                        # Fix limit type
                        if "limit" in args and isinstance(args["limit"], str):
                            try:
                                args["limit"] = int(args["limit"]) if args["limit"] != "-1" else 25
                            except:
                                args["limit"] = 25
                        
                        # Remove invalid project_id (like 12345 which doesn't exist)
                        if "project_id" in args and isinstance(args["project_id"], int):
                            args.pop("project_id")
                            print(f"  Removed invalid numeric project_id")
                    
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
