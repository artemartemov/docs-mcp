#!/usr/bin/env python3
"""
Test core server functions.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_search_query_validation():
    """Test that search queries are validated properly"""
    from docs_mcp.server import SearchQuery
    
    # Valid query
    query = SearchQuery(query="test search", max_results=5)
    assert query.query == "test search"
    assert query.max_results == 5
    
    # Test defaults
    query = SearchQuery(query="test")
    assert query.max_results == 10  # default


def test_security_guidelines_format():
    """Test that security guidelines are returned in expected format"""
    from docs_mcp.server import get_security_guidelines
    
    result = get_security_guidelines()
    
    assert isinstance(result, str)
    assert "Security Guidelines" in result
    assert len(result) > 100  # Should have substantial content


@patch('docs_mcp.server.collection')
def test_get_collection_stats(mock_collection):
    """Test collection stats retrieval"""
    from docs_mcp.server import get_collection_stats
    
    # Mock the collection count
    mock_collection.count.return_value = 100
    
    result = get_collection_stats()
    
    assert isinstance(result, str)
    assert "Collection Statistics" in result
    mock_collection.count.assert_called_once()


@patch('docs_mcp.server.collection')
def test_search_with_mock_results(mock_collection):
    """Test search functionality with mocked results"""
    from docs_mcp.server import search_fastapi_docs, format_results
    
    # Mock search results
    mock_results = {
        'documents': [['Test document content']],
        'metadatas': [[{'source': 'test.md', 'type': 'test'}]],
        'distances': [[0.1]]
    }
    mock_collection.query.return_value = mock_results
    
    # Test search
    result = search_fastapi_docs("test query")
    
    assert isinstance(result, str)
    assert "Search Results" in result
    mock_collection.query.assert_called_once()


def test_format_results():
    """Test result formatting function"""
    from docs_mcp.server import format_results
    
    # Test with valid results
    results = {
        'documents': [['Document 1', 'Document 2']],
        'metadatas': [[
            {'source': 'file1.md', 'type': 'docs'},
            {'source': 'file2.md', 'type': 'api'}
        ]],
        'distances': [[0.1, 0.2]]
    }
    
    formatted = format_results("test query", results, "Test Docs")
    
    assert isinstance(formatted, str)
    assert "Search Results" in formatted
    assert "test query" in formatted
    assert "Test Docs" in formatted
    assert "file1.md" in formatted
    assert "file2.md" in formatted
    
    # Test with empty results
    empty_results = {
        'documents': [[]],
        'metadatas': [[]],
        'distances': [[]]
    }
    
    formatted_empty = format_results("test query", empty_results, "Test Docs")
    assert "No results found" in formatted_empty


def test_error_handling():
    """Test that functions handle errors gracefully"""
    from docs_mcp.server import search_python_docs
    
    # This should not raise an exception even without ChromaDB
    with patch('docs_mcp.server.collection', None):
        result = search_python_docs("test query")
        assert isinstance(result, str)
        assert "Error" in result or "not available" in result.lower()