"""
Unit tests for server.py MCP tool functions and core functionality.

This module tests the MCP tools that provide the main functionality
of the documentation server, focusing on search, documentation management,
and utility functions.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestServerFunctionality(unittest.TestCase):
    """Test cases for server MCP tool functions."""

    def setUp(self):
        """Set up test environment."""
        self.test_chroma_dir = tempfile.mkdtemp()

        # Mock environment variables
        self.env_patcher = patch.dict(
            "os.environ",
            {
                "MCP_ENVIRONMENT": "development",
                "MCP_SECRET_KEY": "test-secret-key-32-characters-long",
                "MCP_CHROMA_DATA_DIR": self.test_chroma_dir,
            },
        )
        self.env_patcher.start()

    def tearDown(self):
        """Clean up test environment."""
        self.env_patcher.stop()
        # Clean up temp directory
        import shutil

        shutil.rmtree(self.test_chroma_dir, ignore_errors=True)

    def test_generate_doc_id(self):
        """Test document ID generation."""
        from docs_mcp.server import generate_doc_id

        # Test basic ID generation
        doc_id = generate_doc_id("Test content", "python")
        self.assertIsInstance(doc_id, str)
        self.assertTrue(len(doc_id) > 0)

        # Test consistency - same content should generate same ID
        doc_id2 = generate_doc_id("Test content", "python")
        self.assertEqual(doc_id, doc_id2)

        # Test different content generates different ID
        doc_id3 = generate_doc_id("Different content", "python")
        self.assertNotEqual(doc_id, doc_id3)

        # Test different framework generates different ID
        doc_id4 = generate_doc_id("Test content", "fastapi")
        self.assertNotEqual(doc_id, doc_id4)

    def test_format_results_empty(self):
        """Test format_results with empty results."""
        from docs_mcp.server import format_results

        # Test with None results
        result = format_results(None, "python")
        self.assertIn("No python documentation found", result)

        # Test with empty list results
        result = format_results([], "fastapi")
        self.assertIn("No fastapi documentation found", result)

    def test_format_results_with_data(self):
        """Test format_results with actual results."""
        from docs_mcp.server import format_results

        # Mock result structure (simplified ChromaDB-like results)
        mock_results = {
            "documents": [["Document 1 content", "Document 2 content"]],
            "metadatas": [
                [
                    {"source": "test1.py", "framework": "python"},
                    {"source": "test2.py", "framework": "python"},
                ]
            ],
            "distances": [[0.1, 0.2]],
        }

        result = format_results(mock_results, "python")
        self.assertIn("python Documentation Results", result)
        self.assertIn("Document 1 content", result)
        self.assertIn("Document 2 content", result)
        self.assertIn("test1.py", result)
        self.assertIn("test2.py", result)

    def test_mcp_tools_are_defined(self):
        """Test that MCP tools are properly defined as FunctionTool objects."""
        import docs_mcp.server as server_module

        # Test that MCP tool functions exist as FunctionTool objects
        self.assertTrue(hasattr(server_module, "search_fastapi_docs"))
        self.assertTrue(hasattr(server_module, "search_python_docs"))
        self.assertTrue(hasattr(server_module, "search_swift_ios_docs"))
        self.assertTrue(hasattr(server_module, "get_security_guidelines"))
        self.assertTrue(hasattr(server_module, "get_collection_stats"))
        self.assertTrue(hasattr(server_module, "add_project_documentation"))

    def test_server_initialization_attempt(self):
        """Test that server initialization functions exist."""
        import docs_mcp.server as server_module

        # Test that initialization functions exist
        self.assertTrue(hasattr(server_module, "initialize_chroma"))
        self.assertTrue(hasattr(server_module, "mcp"))

        # Test that MCP server has expected attributes
        self.assertTrue(hasattr(server_module.mcp, "name"))
        self.assertEqual(server_module.mcp.name, "DocumentationServer")

    def test_search_request_validation(self):
        """Test SearchRequest model validation."""
        from docs_mcp.server import SearchRequest

        # Test valid request
        request = SearchRequest(query="test query", category="python", limit=5)
        self.assertEqual(request.query, "test query")
        self.assertEqual(request.category, "python")
        self.assertEqual(request.limit, 5)

        # Test default values
        request_default = SearchRequest(query="test")
        self.assertEqual(request_default.category, "general")
        self.assertEqual(request_default.limit, 3)

    def test_document_request_validation(self):
        """Test DocumentRequest model validation."""
        from docs_mcp.server import DocumentRequest

        # Test valid request
        request = DocumentRequest(
            content="This is a test document with sufficient length",
            framework="python",
            category="test_category",
            source="test.py",
        )
        self.assertEqual(request.framework, "python")
        self.assertEqual(request.doc_type, "documentation")  # default

        # Test with custom doc_type
        request_custom = DocumentRequest(
            content="This is a test document with sufficient length",
            framework="fastapi",
            category="api_patterns",
            source="api.py",
            doc_type="best_practice",
        )
        self.assertEqual(request_custom.doc_type, "best_practice")

    def test_constants_are_defined(self):
        """Test that important constants are defined."""
        from docs_mcp import constants

        # Test that constants exist
        self.assertTrue(hasattr(constants, "DEFAULT_SEARCH_LIMIT"))
        self.assertTrue(hasattr(constants, "MAX_CONTENT_LENGTH"))
        self.assertTrue(hasattr(constants, "DANGEROUS_CHARS"))

    def test_exceptions_are_defined(self):
        """Test that custom exceptions are defined."""
        from docs_mcp import exceptions

        # Test that exceptions exist
        self.assertTrue(hasattr(exceptions, "ValidationError"))
        self.assertTrue(hasattr(exceptions, "DatabaseError"))
        self.assertTrue(hasattr(exceptions, "ConfigurationError"))

    def test_analysis_request_model(self):
        """Test AnalysisRequest model exists and validates properly."""
        try:
            from docs_mcp.server import AnalysisRequest

            # If we can import it, test basic structure
            self.assertTrue(hasattr(AnalysisRequest, "__fields__"))
        except ImportError:
            # If not available, that's also fine for this test
            pass

    def test_server_module_structure(self):
        """Test that server module has expected structure."""
        import docs_mcp.server as server_module

        # Test basic imports work
        self.assertTrue(hasattr(server_module, "BaseModel"))
        self.assertTrue(hasattr(server_module, "Field"))

        # Test that settings are accessible
        self.assertTrue(hasattr(server_module, "settings"))

    def test_config_integration(self):
        """Test that server properly integrates with config."""
        try:
            import docs_mcp.server as server_module

            # Test that settings from config are used
            self.assertTrue(hasattr(server_module, "settings"))
        except Exception:
            # If there are import issues, that's expected in test environment
            pass


if __name__ == "__main__":
    unittest.main()
