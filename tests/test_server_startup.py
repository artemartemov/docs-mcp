#!/usr/bin/env python3
"""
Test that the MCP server can start up properly.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_server_imports():
    """Test that server modules can be imported without errors"""
    try:
        import docs_mcp.server
        import docs_mcp.config
        import docs_mcp.cli
        assert True
    except ImportError as e:
        assert False, f"Failed to import server modules: {e}"


def test_config_creation():
    """Test that configuration can be created with test values"""
    from docs_mcp.config import Settings
    
    # Create settings with test values
    settings = Settings(
        environment="development",
        secret_key="test-secret-key-32-characters-long"
    )
    
    assert settings.environment == "development"
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000
    assert len(settings.secret_key) >= 32


def test_server_initialization():
    """Test that the MCP server can be initialized"""
    from docs_mcp.server import mcp
    
    # Verify server object exists and has expected attributes
    assert mcp is not None
    assert hasattr(mcp, 'tool')
    assert hasattr(mcp, 'run')


def test_server_tools_defined():
    """Test that all expected MCP tools are defined"""
    from docs_mcp.server import (
        search_fastapi_docs,
        search_python_docs,
        search_swift_ios_docs,
        get_security_guidelines,
        get_collection_stats,
        add_project_documentation
    )
    
    # Verify all tools are callable
    assert callable(search_fastapi_docs)
    assert callable(search_python_docs)
    assert callable(search_swift_ios_docs)
    assert callable(get_security_guidelines)
    assert callable(get_collection_stats)
    assert callable(add_project_documentation)


def test_cli_entry_point():
    """Test that CLI entry point exists"""
    from docs_mcp.cli import main
    
    assert callable(main)