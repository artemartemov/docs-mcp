"""Unit tests for MCP server initialization.

This module tests the basic server startup, instance creation,
and import functionality.
"""

import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestServerInitialization(unittest.TestCase):
    """Test cases for server initialization and basic functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_env = {
            "MCP_ENVIRONMENT": "development",
            "MCP_SECRET_KEY": "test-secret-key-32-characters-long",
        }

    def test_import_server_module(self):
        """Test that the server module can be imported successfully."""
        try:
            import docs_mcp.server
            import docs_mcp.config
            import docs_mcp.cli
        except ImportError as e:
            self.fail(f"Failed to import required modules: {e}")

    def test_mcp_server_instance_created(self):
        """Test that the MCP server instance is properly created."""
        from docs_mcp.server import mcp

        self.assertIsNotNone(mcp)
        self.assertEqual(mcp.name, "DocumentationServer")
        # FastMCP instance has a name attribute

    def test_server_has_expected_attributes(self):
        """Test that the server instance has expected attributes."""
        from docs_mcp.server import mcp

        # Check that server has required methods/attributes
        self.assertTrue(hasattr(mcp, "name"))
        self.assertTrue(hasattr(mcp, "tool"))
        self.assertTrue(hasattr(mcp, "run"))

    def test_server_initialization_with_environment(self):
        """Test that server initializes properly with environment variables."""
        import os
        from unittest.mock import patch

        with patch.dict(
            os.environ,
            {
                "MCP_ENVIRONMENT": "development",
                "MCP_SECRET_KEY": "test-secret-key-32-characters-long",
                "MCP_CHROMA_DATA_DIR": "./chroma_data",
            },
        ):
            # Re-import to test with environment variables
            try:
                import importlib
                import docs_mcp.server

                importlib.reload(docs_mcp.server)
                from docs_mcp.server import mcp

                self.assertIsNotNone(mcp)
            except Exception as e:
                # Server should initialize even if ChromaDB is not available
                self.assertIn(
                    "chroma", str(e).lower(), "Unexpected initialization error"
                )


if __name__ == "__main__":
    unittest.main()
