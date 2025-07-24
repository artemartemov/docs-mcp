"""
docs-mcp: Model Context Protocol server for intelligent documentation search.

A secure MCP server providing semantic search across FastAPI, Python, Swift iOS,
and other framework documentation using ChromaDB vector storage.
"""

__version__ = "1.0.0"
__author__ = "Claude"
__description__ = "MCP server for intelligent documentation search"

from .server import mcp
from .config import get_settings

__all__ = ["mcp", "get_settings"]