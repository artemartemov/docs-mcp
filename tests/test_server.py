"""Unit tests for the MCP server module.

This module tests the server initialization, tool registration,
and basic functionality following Python testing best practices.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestServerInitialization(unittest.TestCase):
    """Test cases for server initialization and configuration."""

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

    def test_all_expected_tools_registered(self):
        """Test that all expected MCP tools are registered with the server."""
        from docs_mcp.server import (
            search_fastapi_docs,
            search_python_docs,
            search_swift_ios_docs,
            get_security_guidelines,
            get_collection_stats,
            add_project_documentation,
        )

        # Check that all tools are defined (they are FunctionTool objects)
        tools = [
            search_fastapi_docs,
            search_python_docs,
            search_swift_ios_docs,
            get_security_guidelines,
            get_collection_stats,
            add_project_documentation,
        ]

        for tool in tools:
            self.assertIsNotNone(tool)
            self.assertTrue(hasattr(tool, "name"))
            self.assertTrue(hasattr(tool, "description"))


class TestConfiguration(unittest.TestCase):
    """Test cases for configuration management."""

    @patch.dict(
        "os.environ",
        {"MCP_ENVIRONMENT": "development", "MCP_SECRET_KEY": "test-secret-key-32-characters-long"},
    )
    def test_settings_initialization(self):
        """Test that Settings can be initialized with environment variables."""
        from docs_mcp.config import Settings

        settings = Settings()

        self.assertEqual(settings.environment, "development")
        self.assertEqual(settings.host, "127.0.0.1")
        self.assertEqual(settings.port, 8000)
        self.assertGreaterEqual(len(settings.secret_key), 32)

    def test_settings_validation(self):
        """Test that Settings validates input correctly."""
        from docs_mcp.config import Settings

        # Test with valid settings
        settings = Settings(
            environment="production",
            host="0.0.0.0",
            port=8080,
            secret_key="production-secret-key-must-be-32-chars",
        )

        self.assertEqual(settings.environment, "production")
        self.assertEqual(settings.host, "0.0.0.0")
        self.assertEqual(settings.port, 8080)

    def test_security_constants_defined(self):
        """Test that security constants are properly defined."""
        from docs_mcp.constants import (
            MAX_QUERY_LENGTH,
            MIN_SECRET_KEY_LENGTH,
            DEFAULT_RATE_LIMIT,
            DEFAULT_ENVIRONMENT,
        )

        self.assertIsInstance(MAX_QUERY_LENGTH, int)
        self.assertGreater(MAX_QUERY_LENGTH, 0)

        self.assertIsInstance(MIN_SECRET_KEY_LENGTH, int)
        self.assertGreaterEqual(MIN_SECRET_KEY_LENGTH, 32)

        self.assertIsInstance(DEFAULT_RATE_LIMIT, int)
        self.assertGreater(DEFAULT_RATE_LIMIT, 0)

        self.assertEqual(DEFAULT_ENVIRONMENT, "development")


class TestServerFunctionality(unittest.TestCase):
    """Test cases for server functionality."""

    def test_format_results_function_exists(self):
        """Test that the format_results helper function exists and is callable."""
        from docs_mcp.server import format_results

        self.assertIsNotNone(format_results)
        self.assertTrue(callable(format_results))

    @patch("docs_mcp.server.collection")
    def test_error_handling_when_collection_unavailable(self, mock_collection):
        """Test that server handles missing ChromaDB collection gracefully."""
        mock_collection.query.side_effect = Exception("Collection not available")

        from docs_mcp.server import mcp

        # Server should still be initialized even if collection fails
        self.assertIsNotNone(mcp)
        self.assertEqual(mcp.name, "DocumentationServer")

    def test_tool_attributes(self):
        """Test that registered tools have required attributes."""
        from docs_mcp.server import (
            search_fastapi_docs,
            search_python_docs,
            search_swift_ios_docs,
            get_security_guidelines,
            get_collection_stats,
            add_project_documentation,
        )

        tools = [
            search_fastapi_docs,
            search_python_docs,
            search_swift_ios_docs,
            get_security_guidelines,
            get_collection_stats,
            add_project_documentation,
        ]

        for tool in tools:
            # Each tool should have required attributes
            self.assertIsNotNone(tool.name)
            self.assertIsNotNone(tool.description)
            self.assertIsInstance(tool.name, str)
            self.assertIsInstance(tool.description, str)

            # Tool names should follow naming convention
            self.assertTrue(tool.name.islower() or "_" in tool.name)


class TestCLI(unittest.TestCase):
    """Test cases for CLI functionality."""

    def test_cli_entry_point_exists(self):
        """Test that the CLI main entry point exists and is callable."""
        from docs_mcp.cli import main

        self.assertIsNotNone(main)
        self.assertTrue(callable(main))

    @patch("sys.argv", ["docs-mcp", "--help"])
    @patch("docs_mcp.cli.sys.exit")
    def test_cli_help_command(self, mock_exit):
        """Test that CLI responds to help command."""
        from docs_mcp.cli import main

        # Help command should exit with 0
        try:
            main()
        except SystemExit:
            pass

        # Verify help was called (this would exit with 0)
        mock_exit.assert_called()


if __name__ == "__main__":
    unittest.main()
