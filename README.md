# docs-mcp

[![CI](https://github.com/artemartemov/docs-mcp/actions/workflows/test.yml/badge.svg)](https://github.com/artemartemov/docs-mcp/actions/workflows/test.yml)
[![Tests](https://img.shields.io/badge/tests-24%20passing-green.svg)](https://github.com/artemartemov/docs-mcp/actions)
[![Coverage](https://img.shields.io/badge/coverage-75%25%2B-brightgreen.svg)](https://github.com/artemartemov/docs-mcp/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A secure Model Context Protocol (MCP) server providing intelligent documentation search across multiple frameworks using ChromaDB vector storage.

## Features

- **Semantic Search** across documentation using vector embeddings
- **Multiple Frameworks** supported: Python, FastAPI, React, SwiftUI, Tailwind CSS, Figma API, Figma Plugins, MDN CSS
- **ChromaDB Storage** for fast, persistent vector search
- **MCP Protocol** integration for Claude Code and other AI tools
- **CLI Interface** for easy management and extraction

## Quick Start

1. **Setup Environment**
   ```bash
   ./docs-mcp dev --setup
   ```

2. **Extract Documentation** (choose one or more)
   ```bash
   ./docs-mcp extract --framework python
   ./docs-mcp extract --framework css
   ./docs-mcp extract --all
   ```

3. **Start MCP Server**
   ```bash
   ./docs-mcp server --start
   ```

4. **Test Integration**
   ```bash
   ./docs-mcp test --framework figma
   ```

## Available Commands

### Extract Documentation
```bash
./docs-mcp extract --framework python     # Python official docs
./docs-mcp extract --framework fastapi    # FastAPI documentation  
./docs-mcp extract --framework react      # React.js documentation
./docs-mcp extract --framework swiftui    # SwiftUI Apple docs
./docs-mcp extract --framework tailwind   # Tailwind CSS docs
./docs-mcp extract --framework figma      # Figma REST API docs
./docs-mcp extract --framework figma_plugin # Figma Plugin API docs
./docs-mcp extract --framework css        # MDN CSS documentation
./docs-mcp extract --all                  # Extract all frameworks
```

### Analyze Collection
```bash
./docs-mcp analyze --stats                # Show documentation statistics
```

### Test Integrations
```bash
./docs-mcp test --framework figma         # Test Figma integration
./docs-mcp test --all                     # Run all tests
```

### Server Operations
```bash
./docs-mcp server --start                 # Start MCP server
./docs-mcp server --config               # Show configuration
```

### Development
```bash
./docs-mcp dev --setup                    # Setup development environment
./docs-mcp dev --clean                    # Clean temporary files
```

## Configuration

Set environment variables in `.env`:

```env
CHROMA_DATA_DIR=/path/to/chroma/data
OPENAI_API_KEY=your_openai_key
ENVIRONMENT=development
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=8000
```

## MCP Integration

Add to your `.mcp.json`:

```json
{
  "mcpServers": {
    "docs": {
      "command": "python",
      "args": ["src/docs_mcp/server.py"],
      "env": {
        "PYTHONPATH": "src"
      }
    }
  }
}
```

## Available MCP Tools

- `search_fastapi_docs()` - Search FastAPI documentation
- `search_python_docs()` - Search Python documentation  
- `search_swift_ios_docs()` - Search Swift/iOS documentation
- `get_security_guidelines()` - Get security best practices
- `get_collection_stats()` - View database statistics
- `add_project_documentation()` - Add custom documentation

## Framework Coverage

| Framework | Documents | Status |
|-----------|-----------|--------|
| Python | 465+ | ✅ Complete |
| Tailwind CSS | 195+ | ✅ Complete |
| Figma API | 144+ | ✅ Complete |
| Figma Plugins | 60+ | ✅ Complete |
| SwiftUI | 39+ | ✅ Complete |
| FastAPI | 21+ | ✅ Complete |
| React | 15+ | ✅ Complete |
| CSS (MDN) | 2,400+ | 🔄 In Progress |

## Requirements

- Python 3.8+
- OpenAI API key (for embeddings)
- 2GB+ disk space (for ChromaDB)

## License

MIT License - see LICENSE file for details.

## Testing

This project maintains high test coverage with organized test suites:

- **Server Initialization Tests** (4 tests): Verify server startup and imports
- **Configuration Tests** (7 tests): Validate settings and environment handling  
- **Tool Registration Tests** (9 tests): Ensure all MCP tools are properly registered
- **CLI Tests** (4 tests): Test command-line interface functionality

### Running Tests Locally

```bash
# Run all tests
make test

# Run specific test categories
python -m pytest tests/test_server_initialization.py -v
python -m pytest tests/test_configuration.py -v
python -m pytest tests/test_tool_registration.py -v
python -m pytest tests/test_cli.py -v

# Run with coverage
python -m pytest tests/ --cov=src/docs_mcp --cov-report=html
```

### Coverage Requirements

- **Minimum Coverage**: 75%
- **Coverage Reports**: Generated automatically in CI/CD
- **Coverage Artifacts**: Available in GitHub Actions builds
- **PR Comments**: Automatic coverage reporting on pull requests

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure coverage: `make test`
5. Submit a pull request

All pull requests must pass:
- ✅ Server initialization tests
- ✅ Configuration validation tests  
- ✅ Tool registration tests
- ✅ CLI functionality tests
- ✅ Code formatting (Black)
- ✅ Code linting (flake8)
- ✅ 75%+ test coverage

## Support

For issues and questions, please open an issue on GitHub.