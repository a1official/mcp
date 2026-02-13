"""
MCP Agents Package
Contains modular tool implementations for different services
"""

from .music import register_music_tools
from .playwright_agent import register_playwright_tools
from .redmine import register_redmine_tools

__all__ = [
    'register_music_tools',
    'register_playwright_tools',
    'register_redmine_tools'
]
