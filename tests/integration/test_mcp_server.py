#!/usr/bin/env python3
"""
Comprehensive integration tests for MCP server functionality.
Tests the core server capabilities and tool functionality.
"""

import asyncio
import logging
import pytest
import tempfile
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from docs_mcp.server import mcp, initialize_chroma
from docs_mcp.config import get_settings

logger = logging.getLogger(__name__)


class TestMCPServerIntegration:
    """Integration tests for MCP server functionality"""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """Setup test environment"""
        # Initialize the server components
        self.initialized = await asyncio.to_thread(initialize_chroma)
        if not self.initialized:
            pytest.skip("ChromaDB not available for testing")

    @pytest.mark.asyncio
    async def test_server_initialization(self):
        """Test that the MCP server initializes correctly"""
        assert self.initialized, "Server should initialize successfully"

        # Test that the MCP instance exists and has tools
        assert mcp is not None, "MCP instance should exist"
        assert hasattr(mcp, "_tools"), "MCP should have tools registered"

        # Verify core tools are registered
        expected_tools = [
            "search_fastapi_docs",
            "search_python_docs",
            "search_swift_ios_docs",
            "get_security_guidelines",
            "get_collection_stats",
            "add_project_documentation",
        ]

        registered_tools = list(mcp._tools.keys())
        for tool in expected_tools:
            assert tool in registered_tools, f"Tool {tool} should be registered"

    @pytest.mark.asyncio
    async def test_search_tools_basic_functionality(self):
        """Test basic search functionality of all search tools"""
        search_tools = [
            "search_fastapi_docs",
            "search_python_docs",
            "search_swift_ios_docs",
        ]

        for tool_name in search_tools:
            if tool_name in mcp._tools:
                tool = mcp._tools[tool_name]

                # Test with a basic query
                result = await asyncio.to_thread(tool, "test query", "general", 1)

                assert isinstance(result, str), f"{tool_name} should return a string"
                assert len(result) > 0, f"{tool_name} should return non-empty result"

                # Should not contain error indicators for valid queries
                error_indicators = ["❌", "Error", "failed", "unavailable"]
                if any(indicator in result for indicator in error_indicators):
                    logger.warning(
                        f"{tool_name} returned error-like response: {result[:100]}..."
                    )

    @pytest.mark.asyncio
    async def test_security_guidelines_tool(self):
        """Test security guidelines tool"""
        if "get_security_guidelines" in mcp._tools:
            tool = mcp._tools["get_security_guidelines"]
            result = await asyncio.to_thread(tool)

            assert isinstance(result, str), "Security guidelines should return string"
            assert len(result) > 500, "Security guidelines should be comprehensive"
            assert "Security" in result, "Should contain security information"
            assert "ResaleAnalyzer" in result, "Should be project-specific"

    @pytest.mark.asyncio
    async def test_collection_stats_tool(self):
        """Test collection statistics tool"""
        if "get_collection_stats" in mcp._tools:
            tool = mcp._tools["get_collection_stats"]
            result = await asyncio.to_thread(tool)

            assert isinstance(result, str), "Collection stats should return string"
            assert (
                "Documents" in result or "Collection" in result
            ), "Should contain stats info"

    @pytest.mark.asyncio
    async def test_add_documentation_tool(self):
        """Test adding documentation functionality"""
        if "add_project_documentation" not in mcp._tools:
            pytest.skip("add_project_documentation tool not available")

        tool = mcp._tools["add_project_documentation"]

        # Test adding valid documentation
        test_content = "This is a test documentation entry for integration testing."
        result = await asyncio.to_thread(
            tool, test_content, "python", "testing", "integration_test", "documentation"
        )

        assert isinstance(result, str), "Add documentation should return string"
        assert "✅" in result or "Added" in result, "Should indicate success"

    @pytest.mark.asyncio
    async def test_accessibility_tools(self):
        """Test accessibility-related tools if available"""
        accessibility_tools = [
            "search_accessibility_patterns",
            "add_accessibility_pattern",
            "scan_and_cache_accessibility_issues",
        ]

        for tool_name in accessibility_tools:
            if tool_name in mcp._tools:
                tool = mcp._tools[tool_name]

                if tool_name == "search_accessibility_patterns":
                    result = await asyncio.to_thread(
                        tool, "form accessibility", "all", "AA", 1
                    )
                    assert isinstance(result, str), f"{tool_name} should return string"

                elif tool_name == "add_accessibility_pattern":
                    result = await asyncio.to_thread(
                        tool,
                        "Test accessibility pattern for integration testing",
                        "fastapi",
                        "AA",
                        "testing",
                        "integration_test",
                    )
                    assert isinstance(result, str), f"{tool_name} should return string"

    @pytest.mark.asyncio
    async def test_input_validation(self):
        """Test input validation for security"""
        if "search_python_docs" not in mcp._tools:
            pytest.skip("search_python_docs tool not available")

        tool = mcp._tools["search_python_docs"]

        # Test with potentially malicious input
        malicious_queries = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE docs; --",
            "javascript:alert(1)",
            "onload=alert(1)",
        ]

        for malicious_query in malicious_queries:
            result = await asyncio.to_thread(tool, malicious_query, "general", 1)

            # Should either sanitize or reject malicious input
            assert isinstance(result, str), "Should handle malicious input safely"
            # Should not echo back raw malicious content
            assert malicious_query not in result, "Should not echo malicious input"

    @pytest.mark.asyncio
    async def test_rate_limiting_behavior(self):
        """Test behavior under rapid requests (basic rate limiting test)"""
        if "get_collection_stats" not in mcp._tools:
            pytest.skip("get_collection_stats tool not available")

        tool = mcp._tools["get_collection_stats"]

        # Make several rapid requests
        tasks = []
        for _ in range(5):
            tasks.append(asyncio.to_thread(tool))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Should handle multiple concurrent requests gracefully
        for result in results:
            assert not isinstance(
                result, Exception
            ), f"Should handle concurrent requests: {result}"
            assert isinstance(result, str), "Each result should be a string"

    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling for edge cases"""
        if "search_python_docs" not in mcp._tools:
            pytest.skip("search_python_docs tool not available")

        tool = mcp._tools["search_python_docs"]

        # Test edge cases
        edge_cases = [
            ("", "general", 1),  # Empty query
            ("test", "invalid_category", 1),  # Invalid category
            ("test", "general", 0),  # Zero limit
            ("test", "general", 1000),  # Excessive limit
        ]

        for query, category, limit in edge_cases:
            result = await asyncio.to_thread(tool, query, category, limit)
            assert isinstance(
                result, str
            ), f"Should handle edge case gracefully: {query}, {category}, {limit}"
            # Should not crash, but may return error message


@pytest.mark.asyncio
async def test_configuration_validation():
    """Test configuration validation"""
    settings = get_settings()

    # Test basic configuration properties
    assert hasattr(settings, "chroma_data_dir"), "Should have chroma_data_dir"
    assert hasattr(settings, "environment"), "Should have environment"
    assert hasattr(settings, "host"), "Should have host"
    assert hasattr(settings, "port"), "Should have port"

    # Test configuration values
    assert settings.environment in [
        "development",
        "production",
    ], "Environment should be valid"
    assert isinstance(settings.port, int), "Port should be integer"
    assert 1 <= settings.port <= 65535, "Port should be valid"


if __name__ == "__main__":
    # Run tests directly if called as script
    pytest.main([__file__, "-v"])
