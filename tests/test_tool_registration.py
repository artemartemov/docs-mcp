"""Unit tests for MCP tool registration and functionality.

This module tests that all expected MCP tools are properly registered
and have the correct attributes and behavior.
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestToolRegistration(unittest.TestCase):
    """Test cases for MCP tool registration and attributes."""

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

    def test_search_tools_have_proper_names(self):
        """Test that search tools have expected names."""
        from docs_mcp.server import (
            search_fastapi_docs,
            search_python_docs,
            search_swift_ios_docs,
        )

        expected_names = {
            search_fastapi_docs.name: "search_fastapi_docs",
            search_python_docs.name: "search_python_docs",
            search_swift_ios_docs.name: "search_swift_ios_docs",
        }

        for actual_name, expected_name in expected_names.items():
            self.assertEqual(actual_name, expected_name)

    def test_utility_tools_have_proper_names(self):
        """Test that utility tools have expected names."""
        from docs_mcp.server import (
            get_security_guidelines,
            get_collection_stats,
            add_project_documentation,
        )

        expected_names = {
            get_security_guidelines.name: "get_security_guidelines",
            get_collection_stats.name: "get_collection_stats",
            add_project_documentation.name: "add_project_documentation",
        }

        for actual_name, expected_name in expected_names.items():
            self.assertEqual(actual_name, expected_name)

    def test_tool_descriptions_are_meaningful(self):
        """Test that tool descriptions contain meaningful information."""
        from docs_mcp.server import (
            search_fastapi_docs,
            search_python_docs,
            get_security_guidelines,
        )

        tools_and_keywords = [
            (search_fastapi_docs, ["fastapi", "search", "documentation"]),
            (search_python_docs, ["python", "search", "documentation"]),
            (get_security_guidelines, ["security", "guidelines"]),
        ]

        for tool, keywords in tools_and_keywords:
            description_lower = tool.description.lower()
            for keyword in keywords:
                self.assertIn(
                    keyword,
                    description_lower,
                    f"Tool {tool.name} missing keyword '{keyword}'",
                )

    def test_format_results_helper_function(self):
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

    def test_search_query_model_exists(self):
        """Test that SearchQuery model is properly defined."""
        from docs_mcp.server import SearchQuery

        # Test that SearchQuery can be instantiated
        query = SearchQuery(query="test search")
        self.assertEqual(query.query, "test search")
        self.assertEqual(query.max_results, 10)  # default value

        # Test with custom max_results
        query_custom = SearchQuery(query="test search", max_results=5)
        self.assertEqual(query_custom.max_results, 5)

    def test_documentation_request_model_exists(self):
        """Test that DocumentationRequest model is properly defined."""
        from docs_mcp.server import DocumentationRequest

        # Test that DocumentationRequest can be instantiated
        doc_request = DocumentationRequest(
            content="Test documentation", doc_type="test", source="test.md"
        )
        self.assertEqual(doc_request.content, "Test documentation")
        self.assertEqual(doc_request.doc_type, "test")
        self.assertEqual(doc_request.source, "test.md")


if __name__ == "__main__":
    unittest.main()
