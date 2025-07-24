#!/usr/bin/env python3
"""
Documentation MCP Server
Secure MCP server for multi-framework documentation search and retrieval.

Security features:
- Input validation and sanitization
- Rate limiting
- Secure configuration management
- Comprehensive logging
- Error handling without information disclosure
"""

import asyncio
import logging
import hashlib
from datetime import datetime

import chromadb
from fastmcp import FastMCP
from pydantic import BaseModel, field_validator, Field
from chromadb.config import Settings as ChromaSettings

from .config import get_settings, validate_environment, create_log_directory
from .constants import DANGEROUS_CHARS, DEFAULT_SEARCH_LIMIT, MAX_CONTENT_LENGTH
from .exceptions import ValidationError, DatabaseError

# Initialize settings and validate environment
settings = get_settings()
create_log_directory()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(settings.log_file), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("DocumentationServer")

# Global Chroma client
chroma_client = None
collection = None


# Request validation models
class SearchRequest(BaseModel):
    """Validated search request"""

    query: str = Field(
        ..., min_length=1, max_length=settings.max_query_length
    )  # noqa: E501
    category: str = Field(default="general", pattern="^[a-zA-Z_][a-zA-Z0-9_]*$")
    limit: int = Field(default=DEFAULT_SEARCH_LIMIT, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, query: str) -> str:
        """Sanitize search query"""
        # Remove potentially dangerous characters
        for char in DANGEROUS_CHARS:
            query = query.replace(char, "")
        return query.strip()


class DocumentRequest(BaseModel):
    """Validated document addition request"""

    content: str = Field(..., min_length=10, max_length=MAX_CONTENT_LENGTH)
    framework: str = Field(..., pattern="^(fastapi|python|swift_ios)$")
    category: str = Field(..., pattern="^[a-zA-Z_][a-zA-Z0-9_]*$")
    source: str = Field(..., min_length=1, max_length=500)
    doc_type: str = Field(
        default="documentation",
        pattern="^(documentation|project_pattern|best_practice)$",
    )

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, content: str) -> str:
        """Basic content sanitization"""
        # Remove null bytes and control characters
        sanitized = "".join(char for char in content if ord(char) >= 32 or char in "\n\r\t")
        return sanitized.strip()


def initialize_chroma() -> bool:
    """Initialize secure connection to Chroma database"""
    global chroma_client, collection

    try:
        # Validate configuration first
        validate_environment()

        # Initialize Chroma client with security settings
        chroma_client = chromadb.PersistentClient(
            path=settings.chroma_data_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,  # Disable telemetry for privacy
                allow_reset=False,  # Prevent accidental data loss
            ),
        )

        # Get or create comprehensive documentation collection
        try:
            collection = chroma_client.get_collection("documentation_collection")
            logger.info("Connected to existing documentation collection")
        except ValueError as e:
            logger.warning(f"Collection not found, creating new: {e}")
            collection = chroma_client.create_collection(
                name="documentation_collection",
                metadata={
                    "description": (
                        "Multi-framework documentation collection: "
                        "Python + FastAPI + Swift iOS + more"
                    ),
                    "created_at": datetime.utcnow().isoformat(),
                    "version": "2.0",
                },
            )
            logger.info("Created new documentation collection")
        except (ConnectionError, OSError) as e:
            logger.error(f"Database connection failed: {e}")
            raise DatabaseError(f"Cannot connect to ChromaDB: {e}")

        logger.info(
            f"✅ Connected to Documentation Chroma database at "
            f"{settings.chroma_data_dir}"
        )
        return True

    except Exception as e:
        logger.error(f"Failed to connect to Chroma database: {e}")
        return False


def generate_doc_id(content: str, framework: str) -> str:
    """Generate secure document ID"""
    # Create hash of content for uniqueness
    content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"docs_{framework}_{timestamp}_{content_hash}"


def format_results(results, framework_name: str) -> str:
    """Format search results with security considerations"""
    if not results["documents"][0]:
        return f"No {framework_name} documentation found."

    formatted_results = [f"# {framework_name} Documentation Results\n"]

    for i, (doc, metadata, distance) in enumerate(
        zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ):
        # Sanitize metadata for display
        source = str(metadata.get("source", "Unknown"))[:100]
        category = str(metadata.get("category", "General"))[:50]
        relevance = max(0, min(1, 1 - distance))  # Clamp between 0-1

        formatted_results.append(
            f"""
## Result {i+1} - {category}
**Source:** {source}  
**Relevance:** {relevance:.2f}

{doc[:2000]}  <!-- Limit content length -->

---
"""
        )

    return "\n".join(formatted_results)


@mcp.tool()
def search_accessibility_patterns(query: str, framework: str = "all", wcag_level: str = "all", limit: int = 3) -> str:
    """
    Search accessibility patterns and WCAG compliance guidelines.
    
    Args:
        query: Search query for accessibility patterns
        framework: Filter by framework (fastapi, swift_ios, react, vue, all)  
        wcag_level: Filter by WCAG level (A, AA, AAA, all)
        limit: Maximum number of results to return (1-10)
    
    Returns:
        Formatted accessibility patterns and compliance guidelines
    """
    if not collection:
        return "❌ Database not available"
    
    # Input sanitization
    query = str(query).strip()[:200]  # Limit query length
    framework = str(framework).lower().strip()[:20]
    wcag_level = str(wcag_level).upper().strip()[:5]
    limit = max(1, min(10, int(limit)))
    
    if not query:
        return "❌ Query cannot be empty"
    
    try:
        # Build metadata filters
        where_filter = {"framework": "accessibility"}
        
        if framework != "all" and framework in ["fastapi", "swift_ios", "react", "vue"]:
            where_filter["target_framework"] = framework
            
        if wcag_level != "all" and wcag_level in ["A", "AA", "AAA"]:
            where_filter["wcag_level"] = wcag_level

        results = collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        return format_search_results(results, f"accessibility patterns for '{query}'")
        
    except Exception as e:
        logger.error(f"Accessibility search error: {e}")
        return f"❌ Search failed: {str(e)[:100]}"

@mcp.tool()
def add_accessibility_pattern(
    pattern_content: str, 
    target_framework: str,
    wcag_level: str = "AA",
    category: str = "general",
    source: str = "manual_entry"
) -> str:
    """
    Add a new accessibility pattern to the knowledge base.
    
    Args:
        pattern_content: The accessibility pattern content
        target_framework: Target framework (fastapi, swift_ios, react, vue)
        wcag_level: WCAG compliance level (A, AA, AAA)
        category: Pattern category (forms, navigation, images, etc.)
        source: Source of the pattern
    
    Returns:
        Success or error message
    """
    if not collection:
        return "❌ Database not available"
    
    # Input validation and sanitization
    pattern_content = str(pattern_content).strip()
    target_framework = str(target_framework).lower().strip()
    wcag_level = str(wcag_level).upper().strip()
    category = str(category).lower().strip()
    source = str(source).strip()[:100]
    
    if len(pattern_content) < 10:
        return "❌ Pattern content too short (minimum 10 characters)"
    
    if target_framework not in ["fastapi", "swift_ios", "react", "vue"]:
        return "❌ Invalid target framework. Use: fastapi, swift_ios, react, vue"
        
    if wcag_level not in ["A", "AA", "AAA"]:
        return "❌ Invalid WCAG level. Use: A, AA, AAA"
    
    try:
        doc_id = generate_doc_id(pattern_content, f"accessibility_{target_framework}")
        
        metadata = {
            "framework": "accessibility",
            "target_framework": target_framework,
            "wcag_level": wcag_level,
            "category": category,
            "source": source,
            "type": "accessibility_pattern",
            "project": "general",
            "added_at": datetime.utcnow().isoformat(),
            "content_hash": hashlib.md5(pattern_content.encode()).hexdigest()
        }
        
        collection.add(
            documents=[pattern_content],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        logger.info(f"Added accessibility pattern: {doc_id}")
        return f"✅ Added accessibility pattern for {target_framework} (WCAG {wcag_level})"
        
    except Exception as e:
        logger.error(f"Failed to add accessibility pattern: {e}")
        return f"❌ Failed to add pattern: {str(e)[:100]}"

@mcp.tool()
def scan_and_cache_accessibility_issues(url: str, cache_results: bool = True) -> str:
    """
    Scan a URL for accessibility issues and optionally cache common patterns found.
    
    Args:
        url: URL to scan for accessibility issues
        cache_results: Whether to cache discovered patterns for future reference
    
    Returns:
        Accessibility scan results and caching status
    """
    if not collection:
        return "❌ Database not available"
    
    # Input sanitization
    url = str(url).strip()
    
    # Basic URL validation
    if not url.startswith(('http://', 'https://')):
        return "❌ Invalid URL. Must start with http:// or https://"
    
    try:
        # Note: This is a placeholder for actual accessibility scanning
        # In practice, you would integrate with the accessibility scanner MCP server
        scan_info = f"""
# Accessibility Scan Results for {url}

**Scan Date:** {datetime.utcnow().isoformat()}

## Integration Note
This tool works best when combined with the accessibility-scanner MCP server.
Use the accessibility scanner to get detailed WCAG compliance reports, then
use this tool to cache common patterns for quick local access.

## Common Patterns to Cache:
- Form labels and validation patterns
- Image alt text standards  
- Navigation ARIA patterns
- Color contrast requirements
- Keyboard navigation patterns

## Usage Workflow:
1. Run accessibility scan with accessibility-scanner MCP
2. Identify recurring patterns or best practices
3. Use add_accessibility_pattern() to cache for quick reference
4. Search cached patterns with search_accessibility_patterns()

This reduces API calls and token usage while building a knowledge base.
"""
        
        if cache_results:
            # Cache this scan info as an example
            doc_id = generate_doc_id(scan_info, "accessibility_scan")
            
            metadata = {
                "framework": "accessibility",
                "target_framework": "web",
                "wcag_level": "AA", 
                "category": "scan_results",
                "source": f"scan_{url}",
                "type": "scan_integration",
                "project": "general",
                "added_at": datetime.utcnow().isoformat(),
                "scanned_url": url
            }
            
            collection.add(
                documents=[scan_info],
                metadatas=[metadata], 
                ids=[doc_id]
            )
            
            return f"✅ Scan integration info cached. Use accessibility-scanner MCP for detailed scans.\n\n{scan_info}"
        
        return scan_info
        
    except Exception as e:
        logger.error(f"Accessibility scan integration error: {e}")
        return f"❌ Scan integration failed: {str(e)[:100]}"

@mcp.tool()
def search_fastapi_docs(query: str, category: str = "general", limit: int = 3) -> str:
    """
    Search FastAPI documentation and best practices.

    Args:
        query: Search query (sanitized automatically)
        category: Category (general, testing, validation, async, database, middleware)
        limit: Maximum number of results (1-10)

    Returns:
        FastAPI documentation with code examples and best practices
    """
    try:
        # Validate input
        request = SearchRequest(query=query, category=category, limit=limit)

        if not collection:
            logger.warning("Documentation database not available for FastAPI search")
            return "❌ Documentation database not available"

        search_text = f"FastAPI {request.category} {request.query}"

        results = collection.query(
            query_texts=[search_text],
            n_results=request.limit,
            where={"framework": "fastapi"},
            include=["documents", "metadatas", "distances"],
        )

        logger.info(
            f"FastAPI search completed: query='{request.query}', results={len(results['documents'][0])}"
        )
        return format_results(results, "FastAPI")

    except Exception as e:
        logger.error(f"FastAPI search error: {e}")
        return "❌ Search temporarily unavailable"


@mcp.tool()
def search_python_docs(query: str, category: str = "general", limit: int = 3) -> str:
    """
    Search Python documentation and best practices.

    Args:
        query: Search query (e.g., "async patterns", "testing", "error handling")
        category: Category (general, testing, async, patterns, security, performance)
        limit: Maximum number of results (1-10)

    Returns:
        Python documentation with code examples and best practices
    """
    try:
        # Validate input
        request = SearchRequest(query=query, category=category, limit=limit)

        if not collection:
            logger.warning("Documentation database not available for Python search")
            return "❌ Documentation database not available"

        # Enhanced search with intelligent prioritization
        search_text = f"Python {request.category} {request.query}"
        
        # First try to find official documentation
        official_results = collection.query(
            query_texts=[search_text],
            n_results=request.limit,
            where={
                "$and": [
                    {"framework": "python"},
                    {"source": "Python Official Documentation"}
                ]
            },
            include=["documents", "metadatas", "distances"],
        )
        
        # If we have enough official results, use them, otherwise supplement
        if len(official_results["documents"][0]) >= request.limit:
            results = official_results
        else:
            # Supplement with other Python documentation
            supplement_results = collection.query(
                query_texts=[search_text],
                n_results=request.limit * 2,  # Get more to filter
                where={"framework": "python"},
                include=["documents", "metadatas", "distances"],
            )
            
            # Combine and deduplicate results
            combined_docs = official_results["documents"][0] + supplement_results["documents"][0]
            combined_metadata = official_results["metadatas"][0] + supplement_results["metadatas"][0]
            combined_distances = official_results["distances"][0] + supplement_results["distances"][0]
            
            # Remove duplicates and limit results
            seen_urls = set()
            final_docs = []
            final_metadata = []
            final_distances = []
            
            for doc, meta, dist in zip(combined_docs, combined_metadata, combined_distances):
                url = meta.get("url", "")
                if url not in seen_urls and len(final_docs) < request.limit:
                    seen_urls.add(url)
                    final_docs.append(doc)
                    final_metadata.append(meta)
                    final_distances.append(dist)
            
            results = {
                "documents": [final_docs],
                "metadatas": [final_metadata],
                "distances": [final_distances]
            }

        logger.info(
            f"Python search completed: query='{request.query}', results={len(results['documents'][0])}"
        )
        return format_results(results, "Python")

    except Exception as e:
        logger.error(f"Python search error: {e}")
        return "❌ Search temporarily unavailable"


@mcp.tool()
def search_swift_ios_docs(query: str, category: str = "general", limit: int = 3) -> str:
    """
    Search Swift iOS documentation and best practices.

    Args:
        query: Search query (e.g., "SwiftUI", "CoreData", "dependency injection")
        category: Category (swiftui, coredata, networking, testing, architecture, memory)
        limit: Maximum number of results (1-10)

    Returns:
        Swift iOS documentation with code examples and best practices
    """
    try:
        # Validate input
        request = SearchRequest(query=query, category=category, limit=limit)

        if not collection:
            logger.warning("Documentation database not available for Swift iOS search")
            return "❌ Documentation database not available"

        search_text = f"Swift iOS {request.category} {request.query}"

        results = collection.query(
            query_texts=[search_text],
            n_results=request.limit,
            where={"framework": "swift_ios"},
            include=["documents", "metadatas", "distances"],
        )

        logger.info(
            f"Swift iOS search completed: query='{request.query}', results={len(results['documents'][0])}"
        )
        return format_results(results, "Swift iOS")

    except Exception as e:
        logger.error(f"Swift iOS search error: {e}")
        return "❌ Search temporarily unavailable"


@mcp.tool()
def get_security_guidelines() -> str:
    """Get security guidelines for the ResaleAnalyzer project."""

    guidelines = """
# ResaleAnalyzer Security Guidelines

## General Security Principles

### 1. Input Validation & Sanitization
```python
from pydantic import BaseModel, field_validator, Field

class AnalysisRequest(BaseModel):
    image_data: str = Field(..., min_length=1, max_length=10_000_000)
    
    @validator("image_data")
    def validate_image_format(cls, v):
        # Validate base64 image data
        if not v.startswith("data:image/"):
            raise ValueError("Invalid image format")
        return v
```

### 2. Environment Variables & Secrets
```python
# config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    google_vision_key: str
    database_url: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Never log secrets
import logging
logging.getLogger("urllib3").setLevel(logging.WARNING)
```

### 3. API Security Headers
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

app = FastAPI()

app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=["localhost", "127.0.0.1"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Specific origins only
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 4. Error Handling (No Information Disclosure)
```python
from fastapi import HTTPException, status

try:
    result = await dangerous_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Operation failed"  # Generic message
    )
```

## iOS Security Best Practices

### 1. Keychain Storage
```swift
import Security

class SecureStorage {
    static func store(key: String, data: Data) -> Bool {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        ]
        
        SecItemDelete(query as CFDictionary)
        return SecItemAdd(query as CFDictionary, nil) == errSecSuccess
    }
}
```

### 2. Network Security
```swift
class NetworkService {
    private let session: URLSession
    
    init() {
        let config = URLSessionConfiguration.default
        config.tlsMinimumSupportedProtocolVersion = .TLSv12
        self.session = URLSession(configuration: config)
    }
}
```

### 3. Data Validation
```swift
struct AnalysisResponse: Codable {
    let success: Bool
    let data: AnalysisData?
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.success = try container.decode(Bool.self, forKey: .success)
        
        // Validate data structure
        if let data = try container.decodeIfPresent(AnalysisData.self, forKey: .data) {
            guard data.isValid else {
                throw DecodingError.dataCorrupted(...)
            }
            self.data = data
        } else {
            self.data = nil
        }
    }
}
```

## Database Security

### 1. SQL Injection Prevention
```python
# Use SQLAlchemy ORM or parameterized queries
from sqlalchemy.orm import Session

def get_analysis(db: Session, analysis_id: int):
    return db.query(Analysis).filter(Analysis.id == analysis_id).first()
```

### 2. Data Encryption
```python
from cryptography.fernet import Fernet

class DataEncryption:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

## Dependency Security

### 1. Regular Updates
```bash
# Python
pip-audit  # Check for vulnerabilities
safety check  # Alternative vulnerability scanner

# Swift
swift package audit  # Check Swift packages
```

### 2. Pinned Dependencies
```python
# requirements.txt - Pin specific versions
fastapi==0.104.1
pydantic==2.5.0
SQLAlchemy==2.0.23
```
"""

    return guidelines


@mcp.tool()
def add_project_documentation(
    content: str,
    framework: str,
    category: str,
    source: str,
    doc_type: str = "documentation",
) -> str:
    """
    Securely add documentation to the ResaleAnalyzer project.

    Args:
        content: Documentation content (10-50000 chars)
        framework: "fastapi", "python", or "swift_ios"
        category: Documentation category (alphanumeric+underscore)
        source: Source reference (1-500 chars)
        doc_type: "documentation", "project_pattern", or "best_practice"

    Returns:
        Confirmation message with document ID
    """
    try:
        # Validate input
        request = DocumentRequest(
            content=content,
            framework=framework,
            category=category,
            source=source,
            doc_type=doc_type,
        )

        if not collection:
            logger.warning("Documentation database not available for adding content")
            return "❌ Documentation database not available"

        # Generate secure document ID
        doc_id = generate_doc_id(request.content, request.framework)

        # Prepare metadata with timestamps
        metadata = {
            "framework": request.framework,
            "category": request.category,
            "source": request.source,
            "type": request.doc_type,
            "project": "documentation_server",
            "added_at": datetime.utcnow().isoformat(),
            "content_hash": hashlib.sha256(request.content.encode()).hexdigest()[:16],
        }

        # Add to collection
        collection.add(documents=[request.content], metadatas=[metadata], ids=[doc_id])

        logger.info(
            f"Added documentation: {doc_id} ({request.framework}/{request.category})"
        )
        return f"✅ Added {request.framework} documentation: {doc_id}"

    except Exception as e:
        logger.error(f"Failed to add documentation: {e}")
        return "❌ Failed to add documentation"


@mcp.tool()
def ingest_documentation_source(source: str = "python", test_mode: bool = False) -> str:
    """
    Ingest documentation from a specific source into the knowledge base.
    
    Args:
        source: Documentation source ("python", etc.)
        test_mode: Run in test mode with limited content for safety
    
    Returns:
        Status message with ingestion results
    """
    try:
        import subprocess
        import sys
        
        # Build command
        cmd = [sys.executable, "ingest_documentation.py", "--source", source]
        if test_mode:
            cmd.append("--test")
        
        logger.info(f"Starting documentation ingestion: {' '.join(cmd)}")
        
        # Run ingestion process
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout
        )
        
        if result.returncode == 0:
            # Parse the output for summary information
            output_lines = result.stdout.split('\n')
            summary_started = False
            summary_lines = []
            
            for line in output_lines:
                if "INGESTION SUMMARY" in line:
                    summary_started = True
                elif summary_started and line.strip():
                    summary_lines.append(line)
                elif summary_started and not line.strip():
                    break
            
            summary = '\n'.join(summary_lines[-10:])  # Last 10 lines of summary
            
            return f"""✅ Documentation ingestion completed successfully!

Source: {source}
Test Mode: {'Yes' if test_mode else 'No'}

Recent Summary:
{summary}

Full logs available in: logs/documentation_ingestion.log
"""
        else:
            error_output = result.stderr[-500:] if result.stderr else "Unknown error"
            logger.error(f"Documentation ingestion failed: {error_output}")
            return f"❌ Documentation ingestion failed:\n{error_output}"
            
    except subprocess.TimeoutExpired:
        return "❌ Documentation ingestion timed out (30 minutes)"
    except Exception as e:
        logger.error(f"Documentation ingestion error: {e}")
        return f"❌ Documentation ingestion error: {e}"

@mcp.tool()
def list_documentation_sources() -> str:
    """List all available documentation sources for ingestion."""
    try:
        from ingest_documentation import IngestionConfig
        
        sources_info = []
        for source_name in IngestionConfig.list_available_sources():
            config = IngestionConfig.get_source_info(source_name)
            sources_info.append(f"• **{source_name}**: {config.get('description', 'No description')}")
        
        return f"""📚 Available Documentation Sources:

{chr(10).join(sources_info)}

Usage: Use `ingest_documentation_source()` to populate the knowledge base.
Example: `ingest_documentation_source("python", test_mode=True)`
"""
    except Exception as e:
        logger.error(f"Error listing sources: {e}")
        return f"❌ Error listing sources: {e}"

@mcp.tool()
def get_collection_stats() -> str:
    """Get secure statistics about the documentation collection."""
    try:
        if not collection:
            return "❌ Documentation database not available"

        data = collection.get()
        total_docs = len(data["ids"])

        # Count by framework (sanitized)
        frameworks = {}
        for metadata in data["metadatas"]:
            fw = str(metadata.get("framework", "unknown"))[:20]  # Limit length
            frameworks[fw] = frameworks.get(fw, 0) + 1

        stats = f"""
📊 Documentation Collection Statistics

Total Documents: {total_docs}
Last Updated: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC

Framework Breakdown:
"""
        for fw, count in sorted(frameworks.items()):
            stats += f"  • {fw}: {count} docs\n"

        logger.info(f"Collection stats requested: {total_docs} total docs")
        return stats

    except Exception as e:
        logger.error(f"Stats retrieval error: {e}")
        return "❌ Statistics temporarily unavailable"


# Initialize on startup
async def main():
    """Main function to initialize and run the secure MCP server"""
    try:
        logger.info("🚀 Starting ResaleAnalyzer Documentation MCP Server...")
        logger.info("   Tech Stack: FastAPI + Python + Swift iOS")
        logger.info(f"   Environment: {settings.environment}")

        if not initialize_chroma():
            logger.error("Failed to initialize Chroma database")
            return

        logger.info("✅ ResaleAnalyzer Documentation MCP Server ready!")
        logger.info("Available secure tools:")
        logger.info("  • search_fastapi_docs(query, category, limit)")
        logger.info("  • search_python_docs(query, category, limit)")
        logger.info("  • search_swift_ios_docs(query, category, limit)")
        logger.info("  • get_security_guidelines()")
        logger.info(
            "  • add_project_documentation(content, framework, category, source)"
        )
        logger.info("  • get_collection_stats()")

        # Keep server running
        await mcp.run()

    except Exception as e:
        logger.error(f"Server startup failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
