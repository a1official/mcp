"""
MCP Server using FastMCP
Modular architecture with separate agent files for different services
"""

import os
from fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("music-server")

# Import and register all agent tools
from agents.music import register_music_tools
from agents.playwright_agent import register_playwright_tools
from agents.redmine import register_redmine_tools

# Register all tools
register_music_tools(mcp)
register_playwright_tools(mcp)
register_redmine_tools(mcp)

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
