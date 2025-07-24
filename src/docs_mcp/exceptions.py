"""Custom exceptions for docs-mcp."""

class DocsMCPError(Exception):
    """Base exception for docs-mcp."""
    pass

class ConfigurationError(DocsMCPError):
    """Configuration validation error with actionable context."""
    pass

class DocumentationError(DocsMCPError):
    """Documentation processing error."""
    pass

class DatabaseError(DocsMCPError):
    """ChromaDB operation error."""
    pass

class ValidationError(DocsMCPError):
    """Input validation error."""
    pass

class ExtractionError(DocsMCPError):
    """Content extraction error."""
    pass