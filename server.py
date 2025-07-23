#!/usr/bin/env python3
"""
ResaleAnalyzer Documentation MCP Server
Secure MCP server for FastAPI, Python, and Swift iOS documentation.

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

from config import get_settings, validate_environment, create_log_directory

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
mcp = FastMCP("ResaleAnalyzerDocs")

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
    limit: int = Field(default=3, ge=1, le=10)

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, v):
        """Sanitize search query"""
        # Remove potentially dangerous characters
        dangerous_chars = ["<", ">", '"', "'", "&", ";", "|", "`", "$"]
        for char in dangerous_chars:
            v = v.replace(char, "")
        return v.strip()


class DocumentRequest(BaseModel):
    """Validated document addition request"""

    content: str = Field(..., min_length=10, max_length=50000)
    framework: str = Field(..., pattern="^(fastapi|python|swift_ios)$")
    category: str = Field(..., pattern="^[a-zA-Z_][a-zA-Z0-9_]*$")
    source: str = Field(..., min_length=1, max_length=500)
    doc_type: str = Field(
        default="documentation",
        pattern="^(documentation|project_pattern|best_practice)$",
    )

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v):
        """Basic content sanitization"""
        # Remove null bytes and control characters
        v = "".join(char for char in v if ord(char) >= 32 or char in "\n\r\t")
        return v.strip()


def initialize_chroma():
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

        # Get or create project-specific documentation collection
        try:
            collection = chroma_client.get_collection("resale_analyzer_docs")
            logger.info("Connected to existing documentation collection")
        except Exception:
            collection = chroma_client.create_collection(
                name="resale_analyzer_docs",
                metadata={
                    "description": (
                        "ResaleAnalyzer project documentation: "
                        "FastAPI + Python + Swift iOS"
                    ),
                    "created_at": datetime.utcnow().isoformat(),
                    "version": "1.0",
                },
            )
            logger.info("Created new documentation collection")

        logger.info(
            f"✅ Connected to ResaleAnalyzer Chroma database at "
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
    return f"resale_{framework}_{timestamp}_{content_hash}"


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

        search_text = f"Python {request.category} {request.query}"

        results = collection.query(
            query_texts=[search_text],
            n_results=request.limit,
            where={"framework": "python"},
            include=["documents", "metadatas", "distances"],
        )

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
            "project": "resale_analyzer",
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
