"""
Tests for ResaleAnalyzer Documentation MCP Server
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from server import SearchRequest, DocumentRequest, format_results, generate_doc_id


class TestValidationModels:
    """Test input validation models"""

    def test_search_request_valid(self):
        request = SearchRequest(query="FastAPI testing patterns", category="testing", limit=5)
        assert request.query == "FastAPI testing patterns"
        assert request.category == "testing"
        assert request.limit == 5

    def test_search_request_sanitization(self):
        request = SearchRequest(query="SELECT * FROM users; DROP TABLE users;", category="general")
        # Dangerous characters should be removed
        assert ";" not in request.query
        assert "DROP" in request.query  # Content preserved, only dangerous chars removed

    def test_search_request_invalid_category(self):
        with pytest.raises(ValueError):
            SearchRequest(query="test", category="invalid-category")  # Hyphens not allowed

    def test_document_request_valid(self):
        request = DocumentRequest(
            content="This is test documentation content for FastAPI patterns.",
            framework="fastapi",
            category="testing",
            source="https://example.com/docs",
        )
        assert request.framework == "fastapi"
        assert len(request.content) > 10

    def test_document_request_invalid_framework(self):
        with pytest.raises(ValueError):
            DocumentRequest(
                content="Test content",
                framework="invalid_framework",
                category="testing",
                source="test",
            )


class TestUtilityFunctions:
    """Test utility functions"""

    def test_generate_doc_id(self):
        content = "Test documentation content"
        framework = "fastapi"

        doc_id = generate_doc_id(content, framework)

        assert doc_id.startswith("resale_fastapi_")
        assert len(doc_id.split("_")) == 4  # resale_framework_timestamp_hash

    def test_format_results_empty(self):
        results = {"documents": [[]], "metadatas": [[]], "distances": [[]]}

        formatted = format_results(results, "FastAPI")
        assert "No FastAPI documentation found" in formatted

    def test_format_results_with_data(self):
        results = {
            "documents": [["Test documentation content"]],
            "metadatas": [[{"source": "test.com", "category": "testing"}]],
            "distances": [[0.1]],
        }

        formatted = format_results(results, "FastAPI")

        assert "FastAPI Documentation Results" in formatted
        assert "Test documentation content" in formatted
        assert "testing" in formatted
        assert "0.90" in formatted  # 1 - 0.1 = 0.90 relevance


class TestServerIntegration:
    """Integration tests for server functionality"""

    @patch("server.collection")
    def test_search_fastapi_docs_success(self, mock_collection):
        from server import search_fastapi_docs

        # Mock Chroma response
        mock_collection.query.return_value = {
            "documents": [["FastAPI dependency injection pattern"]],
            "metadatas": [[{"source": "fastapi.com", "category": "patterns"}]],
            "distances": [[0.2]],
        }

        result = search_fastapi_docs("dependency injection", "patterns", 1)

        assert "FastAPI Documentation Results" in result
        assert "dependency injection pattern" in result
        mock_collection.query.assert_called_once()

    @patch("server.collection", None)
    def test_search_with_no_database(self):
        from server import search_fastapi_docs

        result = search_fastapi_docs("test query")
        assert "Documentation database not available" in result

    @patch("server.collection")
    def test_add_project_documentation_success(self, mock_collection):
        from server import add_project_documentation

        # Mock collection.get() for ID generation
        mock_collection.get.return_value = {"ids": ["existing_doc_1"]}

        result = add_project_documentation(
            content="Test FastAPI documentation with examples and best practices.",
            framework="fastapi",
            category="testing",
            source="internal",
            doc_type="best_practice",
        )

        assert "Added fastapi documentation" in result
        mock_collection.add.assert_called_once()

        # Verify the call arguments
        call_args = mock_collection.add.call_args
        assert len(call_args[1]["documents"]) == 1
        assert call_args[1]["metadatas"][0]["framework"] == "fastapi"
        assert call_args[1]["metadatas"][0]["category"] == "testing"


class TestSecurity:
    """Test security features"""

    def test_query_length_validation(self):
        # Test maximum query length enforcement
        long_query = "x" * 1001  # Exceeds default max of 1000

        with pytest.raises(ValueError):
            SearchRequest(query=long_query)

    def test_content_sanitization(self):
        request = DocumentRequest(
            content="Normal content\x00with null bytes\x01and control chars",
            framework="python",
            category="security",
            source="test",
        )

        # Null bytes and control characters should be removed
        assert "\x00" not in request.content
        assert "\x01" not in request.content
        assert "Normal content" in request.content

    def test_metadata_sanitization_in_format_results(self):
        # Test that extremely long metadata is truncated
        long_source = "x" * 200  # Longer than 100 char limit

        results = {
            "documents": [["Test content"]],
            "metadatas": [[{"source": long_source, "category": "test"}]],
            "distances": [[0.1]],
        }

        formatted = format_results(results, "Test")

        # Source should be truncated to 100 characters
        lines = formatted.split("\n")
        source_line = [line for line in lines if "Source:" in line][0]
        source_value = source_line.split("Source: ")[1]
        assert len(source_value) <= 100


@pytest.fixture
def mock_chroma_settings():
    """Mock Chroma settings for testing"""
    with patch("server.settings") as mock_settings:
        mock_settings.chroma_data_dir = "/tmp/test_chroma"
        mock_settings.max_query_length = 1000
        mock_settings.log_level = "INFO"
        mock_settings.log_file = "/tmp/test.log"
        yield mock_settings


class TestConfiguration:
    """Test configuration and environment validation"""

    def test_config_validation(self, mock_chroma_settings):
        from config import Settings

        # Test that settings can be instantiated
        settings = Settings()
        assert hasattr(settings, "chroma_data_dir")
        assert hasattr(settings, "max_query_length")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
