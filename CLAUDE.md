# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a secure Model Context Protocol (MCP) server providing intelligent documentation search for the ResaleAnalyzer project. It provides semantic search across FastAPI, Python, and Swift iOS documentation using ChromaDB vector storage.

## Essential Commands

### Setup and Installation
```bash
# Initialize development environment
make init

# Install production dependencies only
make install

# Install with dev dependencies
make install-dev

# Setup environment configuration
make setup-env  # Creates .env from template
```

### Development Commands
```bash
# Run the MCP server (development)
make run
python server.py

# Run in production mode
make run-production
uvicorn server:mcp --host 127.0.0.1 --port 8000
```

### Testing and Quality Assurance
```bash
# Run all tests with coverage
make test
pytest -v --cov=. --cov-report=html

# Run all quality checks (format, lint, security, test)
make all-checks

# Individual checks
make format     # Format code with black
make lint      # flake8 and mypy checks
make security  # bandit security scan and safety vulnerability check
```

### Configuration Management
```bash
# Validate environment configuration
make validate-config

# Check for dependency vulnerabilities
make check-deps
```

## Architecture

### Core Components
- **server.py**: Main MCP server using FastMCP framework with security-focused design
- **config.py**: Pydantic-based configuration management with environment validation
- **ChromaDB Integration**: Vector database for semantic documentation search

### Security Architecture
- Input validation using Pydantic models with strict validation
- Query sanitization to prevent injection attacks
- Rate limiting and content length restrictions
- Comprehensive logging without sensitive data exposure
- Environment-based configuration with validation

### MCP Tools Provided
- `search_fastapi_docs()` - FastAPI documentation search
- `search_python_docs()` - Python best practices search  
- `search_swift_ios_docs()` - Swift iOS patterns search
- `get_security_guidelines()` - Project security guidelines
- `get_collection_stats()` - Database statistics
- `add_project_documentation()` - Add new documentation

## Configuration Requirements

Must have `.env` file with:
- `CHROMA_DATA_DIR`: Path to ResaleAnalyzer's ChromaDB data
- `OPENAI_API_KEY`: Required for embeddings
- `ENVIRONMENT`: development/production
- `MCP_SERVER_HOST`/`MCP_SERVER_PORT`: Server configuration

## Integration with Claude Code

Add to `.mcp.json`:
```json
{
  "mcpServers": {
    "resale_docs": {
      "command": "python",
      "args": ["/path/to/docs-mcp/server.py"],
      "env": {
        "PYTHONPATH": "/path/to/docs-mcp"
      }
    }
  }
}
```

## Development Workflow

1. Use `make init` for initial setup
2. Configure `.env` with your specific paths and API keys
3. Run `make validate-config` to verify configuration
4. Use `make all-checks` before committing changes
5. The Makefile provides comprehensive development commands

## Key Dependencies

- **fastmcp**: MCP server framework
- **chromadb**: Vector database for semantic search
- **pydantic**: Data validation and settings management
- **uvicorn**: ASGI server for production deployment

## Project-Specific Requirements

### Logging and Monitoring
- **CRITICAL**: Ensure Serena logs project is activated for this project
- Use dedicated logging for all operations and debugging
- Monitor memory usage and performance metrics
- Log all vector database operations and search queries

### Memory Management
- Utilize Claude Code's memory capabilities to the fullest extent
- Store project context, patterns, and learned optimizations in memory
- Remember user preferences and frequently used configurations
- Cache vector database queries and results when appropriate

### Code Quality Standards
- **Human Readable Code**: Prioritize code clarity over excessive commenting
- Write self-documenting code with clear variable and function names
- Add comments only when business logic is complex or non-obvious
- Avoid comment overload - let the code speak for itself
- Use type hints consistently for better code understanding

### Documentation Management
- **Vector Database Integration**: If documentation doesn't exist, add it to ChromaDB
- Use the `add_project_documentation()` MCP tool to enhance the knowledge base
- Cache frequently accessed documentation locally
- Ensure all new patterns and solutions are documented in the vector store
- Follow best documentation practices: clear, concise, actionable

### Repository Management
- **Micro-commits Required**: Make small, atomic commits throughout development
- Each commit should represent a single logical change
- Use descriptive commit messages following conventional commit format
- Maintain clean repository structure with organized file hierarchy
- Run `make all-checks` before every commit
- Keep the working directory clean with no uncommitted changes

### Development Process
1. Always check current repository status before starting work
2. Create focused, single-purpose commits
3. Update vector database with new documentation as you work
4. Use memory to track patterns and optimizations discovered
5. Ensure Serena logs are capturing all development activities
6. Validate all changes with comprehensive testing