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
- Access to ResaleAnalyzer's Chroma database
- OpenAI API key (for embeddings)

### Installation

```bash
# Clone the repository
git clone <your-private-repo-url>
cd docs-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your configuration
```

### Configuration

Create a `.env` file with your settings:

```bash
CHROMA_DATA_DIR=/path/to/resale-analyzer/.chroma_data
OPENAI_API_KEY=sk-your-openai-key
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8000
ENVIRONMENT=development
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
- `search_fastapi_docs(query, category, limit)` - Search FastAPI documentation
- `search_python_docs(query, category, limit)` - Search Python best practices  
- `search_swift_ios_docs(query, category, limit)` - Search Swift iOS patterns

### Information Tools
- `get_security_guidelines()` - Get project security guidelines
- `get_collection_stats()` - View documentation database statistics

### Management Tools
- `add_project_documentation(content, framework, category, source)` - Add new documentation

## Integration with Claude Code

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "resale_docs": {
      "command": "python",
      "args": ["/Users/yourname/dev/docs-mcp/server.py"],
      "env": {
        "PYTHONPATH": "/Users/yourname/dev/docs-mcp"
      }
    }
  }
}
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