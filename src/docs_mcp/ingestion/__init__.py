"""
Documentation Ingestion Framework for ResaleAnalyzer MCP Server.

A comprehensive, reusable system for ingesting documentation from various sources
into ChromaDB with consistent patterns, rate limiting, and error handling.
"""

from .base import (
    DocumentMetadata,
    DocumentContent,
    IngestionStats,
    BaseDocumentationSource,
    DocumentationIngester,
)

__all__ = [
    "DocumentMetadata",
    "DocumentContent",
    "IngestionStats",
    "BaseDocumentationSource",
    "DocumentationIngester",
]
