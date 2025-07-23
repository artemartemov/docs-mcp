# Documentation MCP Server

A secure, production-ready Model Context Protocol (MCP) server providing intelligent documentation search across multiple programming languages and frameworks: **Python**, **FastAPI**, **Swift iOS**, and more.

## Features

- 🔍 **Semantic Documentation Search** - Vector-based search across frameworks
- 🔒 **Security-First** - Input validation, sanitization, and secure configuration
- 🔧 **Multi-Framework** - Supports multiple programming languages and frameworks
- 🚀 **Production-Ready** - Comprehensive logging, error handling, and monitoring
- 🧠 **ChromaDB Integration** - Advanced vector database for semantic search
- 📚 **Extensible** - Plugin-based architecture for adding new documentation sources

## Tech Stack Support

### FastAPI
- API design patterns and best practices
- Dependency injection and middleware
- Testing strategies and validation
- Async patterns and database integration

### Python  
- Security patterns and error handling
- Testing frameworks and patterns
- Performance optimization techniques
- Async/await best practices

### Swift iOS
- SwiftUI architecture and MVVM patterns
- Dependency injection and service layer design
- CoreData integration and memory management
- Testing patterns and protocol-oriented programming

## Quick Start

### Prerequisites
- Python 3.9+
- Internet connection for documentation ingestion
- OpenAI API key (optional, for advanced embeddings)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd docs-mcp

# Initialize development environment (recommended)
make init

# Or manual setup:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Configuration

The server works with minimal configuration. For advanced features:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings (optional)
CHROMA_DATA_DIR=./chroma_data
OPENAI_API_KEY=sk-your-openai-key  # Optional for advanced embeddings
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8000
ENVIRONMENT=development
```

### First Time Setup

1. **Start the MCP server:**
   ```bash
   make run
   # or: python server.py
   ```

2. **Populate the documentation database:**
   ```bash
   # Test with limited content first
   python ingest_documentation.py --source python --test
   
   # Full Python documentation ingestion
   python ingest_documentation.py --source python
   ```

3. **Verify the setup:**
   ```bash
   # Check collection statistics
   python -c "
   from docs_ingestion import DocumentationIngester
   ingester = DocumentationIngester()
   print(ingester.get_collection_stats())
   "
   ```

### Running the Server

```bash
# Development mode
python server.py

# Or with uvicorn for production
uvicorn server:mcp --host 127.0.0.1 --port 8000
```

## MCP Tools Available

### Search Tools
- `search_python_docs(query, category, limit)` - Search Python official documentation with intelligent prioritization
- `search_fastapi_docs(query, category, limit)` - Search FastAPI documentation  
- `search_swift_ios_docs(query, category, limit)` - Search Swift iOS patterns

### Documentation Management
- `ingest_documentation_source(source, test_mode)` - Populate database from documentation sources
- `list_documentation_sources()` - List all available documentation sources
- `add_project_documentation(content, framework, category, source)` - Add custom documentation

### Information Tools
- `get_security_guidelines()` - Get comprehensive security guidelines
- `get_collection_stats()` - View detailed database statistics

## Integration with Claude Code

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "documentation_server": {
      "command": "python",
      "args": ["/path/to/docs-mcp/server.py"],
      "env": {
        "PYTHONPATH": "/path/to/docs-mcp"
      }
    }
  }
}
```

## Documentation Ingestion

### Available Sources

Currently supported documentation sources:

- **Python**: Official Python 3 documentation using Sphinx inventory API
- **FastAPI**: (Coming soon) - FastAPI official documentation  
- **Swift iOS**: (Coming soon) - Apple's Swift and iOS documentation

### Adding New Documentation Sources

The framework is designed for easy extension:

```bash
# List available sources
python ingest_documentation.py --list-sources

# Ingest specific source
python ingest_documentation.py --source python

# Test mode for safe development
python ingest_documentation.py --source python --test

# Ingest all available sources
python ingest_documentation.py --source all
```

### Creating Custom Adapters

To add support for new documentation sources, create an adapter in `docs_ingestion/adapters/`:

```python
from docs_ingestion.base import BaseDocumentationSource, DocumentContent, DocumentMetadata

class MyFrameworkSource(BaseDocumentationSource):
    def get_framework_name(self) -> str:
        return "myframework"
    
    async def discover_content(self) -> List[str]:
        # Implement content discovery logic
        pass
    
    async def extract_content(self, identifier: str) -> Optional[DocumentContent]:
        # Implement content extraction logic
        pass
```

## Usage Examples

### Basic Search

```python
# Through MCP tools (recommended)
search_python_docs("asyncio patterns", "async", 5)
search_fastapi_docs("dependency injection", "patterns", 3)

# Direct database access
from docs_ingestion import DocumentationIngester
ingester = DocumentationIngester()
stats = ingester.get_collection_stats()
```

### Adding Custom Documentation

```python
add_project_documentation(
    content="Custom documentation content...",
    framework="python",
    category="custom_patterns",
    source="Internal Team Knowledge",
    doc_type="best_practice"
)
```

## Security Features

- **Input Validation** - Pydantic models with strict validation
- **Query Sanitization** - Removes potentially dangerous characters
- **Rate Limiting** - Configurable request throttling
- **Secure Logging** - No sensitive data in logs
- **Environment Validation** - Comprehensive startup checks
- **Content Length Limits** - Prevents memory exhaustion attacks

## Development

### Running Tests

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run security checks
bandit -r server.py config.py
safety check
```

### Code Quality

```bash
# Format code
black server.py config.py

# Lint code  
flake8 server.py config.py

# Type checking
mypy server.py config.py
```

## Project Structure

```
docs-mcp/
├── server.py              # Main MCP server implementation
├── config.py              # Secure configuration management
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── .env.example           # Environment configuration template
├── .gitignore            # Git ignore patterns
├── README.md             # This file
└── logs/                 # Application logs (created automatically)
```

## Contributing

1. Follow security best practices
2. Add tests for new features
3. Update documentation as needed
4. Run security scans before committing

## License

Private repository for ResaleAnalyzer project.