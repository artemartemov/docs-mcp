# Project Cleanup Plan - docs-mcp

## Current Issues Identified

### 🗂️ File Organization Problems
- Test files scattered in root directory instead of `tests/`
- Extraction scripts mixed with core code
- Temporary/debug files in root
- Multiple similar extraction scripts
- Outdated documentation files
- No clear CLI interface

### 📁 Proposed Directory Structure (Best Practices)

```
docs-mcp/
├── README.md                          # Main project documentation
├── LICENSE                           # License file
├── pyproject.toml                    # Modern Python packaging
├── requirements.txt                  # Core dependencies
├── requirements-dev.txt              # Development dependencies
├── .gitignore                       # Git ignore patterns
├── Makefile                         # Development commands
│
├── src/                             # Source code
│   └── docs_mcp/
│       ├── __init__.py
│       ├── server.py                # MCP server
│       ├── config.py                # Configuration
│       ├── cli.py                   # Command line interface
│       │
│       ├── ingestion/               # Documentation ingestion
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── spa_base.py
│       │   └── adapters/
│       │       ├── __init__.py
│       │       ├── python_docs.py
│       │       ├── fastapi_docs.py
│       │       ├── react_docs.py
│       │       ├── swiftui_docs.py
│       │       ├── tailwind_docs.py
│       │       ├── figma_api_docs.py    # Consolidated Figma API
│       │       ├── figma_plugin_docs.py
│       │       └── mdn_css_docs.py
│       │
│       └── utils/                   # Utility functions
│           ├── __init__.py
│           ├── search.py
│           └── analysis.py
│
├── scripts/                         # Operational scripts
│   ├── extract_all.py              # Main extraction orchestrator
│   ├── extract_framework.py        # Single framework extraction
│   ├── analyze_collection.py       # Collection analysis
│   └── setup_environment.py        # Environment setup
│
├── tests/                          # All tests
│   ├── __init__.py
│   ├── conftest.py                 # Test configuration
│   ├── test_server.py
│   ├── test_ingestion.py
│   ├── integration/                # Integration tests
│   │   ├── __init__.py
│   │   ├── test_figma_integration.py
│   │   ├── test_css_integration.py
│   │   └── test_plugin_integration.py
│   └── unit/                       # Unit tests
│       ├── __init__.py
│       ├── test_adapters.py
│       └── test_config.py
│
├── docs/                           # Documentation
│   ├── getting-started.md
│   ├── configuration.md
│   ├── adding-sources.md
│   ├── accessibility-guide.md
│   └── api-reference.md
│
├── examples/                       # Usage examples
│   ├── basic_search.py
│   └── custom_adapter.py
│
├── data/                          # Data directory
│   ├── chroma_data/               # ChromaDB storage
│   └── logs/                      # Application logs
│
└── .github/                       # GitHub specific
    ├── workflows/                 # CI/CD
    └── ISSUE_TEMPLATE/            # Issue templates
```

## Files to Move/Reorganize

### ✅ Keep (Core Files)
- `server.py` → `src/docs_mcp/server.py`
- `config.py` → `src/docs_mcp/config.py`
- `docs_ingestion/` → `src/docs_mcp/ingestion/`
- `requirements.txt`, `requirements-dev.txt`
- `Makefile`

### 🗂️ Reorganize
- All `test_*.py` → `tests/integration/`
- `extract_*.py` → `scripts/`
- `analyze_all_sources.py` → `scripts/analyze_collection.py`
- Documentation `.md` files → `docs/`
- `chroma_data/` → `data/chroma_data/`
- `logs/` → `data/logs/`

### 🗑️ Remove/Archive
- `debug_figma.py` (debug file)
- `test_figma_timeout.py` (specific debug)
- `convert_figma_html.py` (utility, move to scripts if needed)
- Multiple old `run_*.sh` scripts (replace with CLI)
- Duplicate extraction scripts
- Old documentation files in root

## CLI Interface Design

```bash
# Main interface
docs-mcp --help

# Extract documentation
docs-mcp extract --framework python
docs-mcp extract --framework css  
docs-mcp extract --all

# Analyze collection
docs-mcp analyze --stats
docs-mcp analyze --frameworks

# Test integrations
docs-mcp test --framework figma
docs-mcp test --all

# Server operations
docs-mcp server --start
docs-mcp server --config

# Development
docs-mcp dev --setup
docs-mcp dev --clean
```

## Migration Steps (Safe - Won't Break Running Extraction)

1. ✅ Create new directory structure
2. ✅ Move files to new locations  
3. ✅ Update import paths
4. ✅ Create CLI interface
5. ✅ Update documentation
6. ✅ Clean up old files
7. ✅ Test everything works

**Note**: MDN CSS extraction will continue running unaffected as we're not modifying the running process or its files during execution.