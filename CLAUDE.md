# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## ⚠️ CRITICAL: Accessibility-First Development

**MANDATORY**: Before writing ANY UI code, you MUST:
1. Run `search_accessibility_patterns('[feature]', framework='[framework]')` 
2. Apply WCAG AA standards from cached patterns
3. Include accessibility attributes in EVERY code suggestion
4. Mention which accessibility patterns you applied

**Example**: "I searched accessibility patterns for forms and applied WCAG AA standards including ARIA labels and error handling."

See CLAUDE_ACCESSIBILITY_INSTRUCTIONS.md for detailed workflow.

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

## Accessibility Integration Workflow

This section provides a comprehensive workflow for integrating accessibility scanning and documentation management using both the global accessibility-scanner MCP and the custom docs-mcp server tools.

### Two-System Integration Overview

The accessibility workflow leverages two complementary systems:
1. **Global accessibility-scanner MCP**: Provides detailed WCAG 2.1 AA compliance scanning
2. **Custom docs-mcp server**: Caches patterns and enables quick lookup for token efficiency

### Phase 1: Initial Accessibility Analysis

#### Step 1: Comprehensive Accessibility Scan
Use the global accessibility-scanner MCP for detailed analysis:

```bash
# Scan web interface for accessibility issues
mcp__accessibility_scanner__scan_url --url "http://localhost:3000" --rules "wcag21aa"

# Scan HTML content directly
mcp__accessibility_scanner__scan_html --html_content "<html>...</html>" --rules "wcag21aa"

# Generate detailed accessibility report
mcp__accessibility_scanner__generate_report --scan_results "..." --format "detailed"
```

#### Step 2: Pattern Recognition and Analysis
The accessibility scanner provides:
- **Violation Details**: Specific WCAG failures with impact levels
- **Code Locations**: Exact selectors and line numbers
- **Remediation Steps**: Specific fix recommendations
- **Best Practices**: Accessibility pattern suggestions

### Phase 2: Pattern Caching with docs-mcp

#### Step 3: Cache Common Accessibility Patterns
Store frequently encountered patterns using docs-mcp tools:

```bash
# Cache accessibility patterns for FastAPI backend
add_project_documentation --content "
## Accessibility API Patterns

### ARIA Label Implementation
- Use aria-label for screen reader context
- Implement aria-describedby for detailed descriptions
- Ensure semantic HTML structure

### Error Handling Accessibility
- Provide accessible error messages
- Use role='alert' for critical errors
- Implement focus management for error states
" --doc_type "accessibility_patterns"

# Cache Swift iOS accessibility patterns
add_project_documentation --content "
## iOS Accessibility Implementation

### VoiceOver Support
- Set accessibilityLabel for UI elements
- Use accessibilityHint for complex interactions
- Implement accessibilityTraits appropriately

### Dynamic Type Support
- Use scalable fonts
- Test with largest accessibility sizes
- Ensure layout adapts to text scaling
" --doc_type "ios_accessibility"
```

#### Step 4: Create Accessibility Guidelines Cache
Document project-specific accessibility requirements:

```bash
add_project_documentation --content "
## ResaleAnalyzer Accessibility Standards

### Image Analysis Accessibility
- Alt text generation for analyzed images
- Screen reader support for price predictions
- Keyboard navigation for image upload

### Form Accessibility
- Label association for all inputs
- Error message accessibility
- Progress indicator accessibility for analysis

### Color and Contrast
- WCAG AA contrast ratios (4.5:1 for normal text)
- No color-only information conveyance
- High contrast mode support
" --doc_type "project_accessibility_standards"
```

### Phase 3: Quick Pattern Lookup

#### Step 5: Efficient Pattern Retrieval
Use docs-mcp for fast accessibility pattern lookup:

```bash
# Search for accessibility patterns
search_fastapi_docs --query "accessibility ARIA implementation"
search_swift_ios_docs --query "VoiceOver screen reader support"

# Get specific accessibility guidelines
get_security_guidelines  # Often includes accessibility security considerations
```

#### Step 6: Context-Aware Documentation Search
Leverage semantic search for accessibility solutions:

```bash
# Find accessibility solutions for specific components
search_python_docs --query "form validation accessibility error messages"
search_swift_ios_docs --query "dynamic type font scaling accessibility"
```

### Phase 4: Implementation and Validation

#### Step 7: Apply Accessibility Fixes
Using cached patterns, implement fixes efficiently:

1. **Reference Cached Patterns**: Use docs-mcp to quickly find relevant solutions
2. **Apply Systematic Fixes**: Implement accessibility improvements based on cached best practices
3. **Document New Patterns**: Add newly discovered patterns to the cache

#### Step 8: Validation and Re-scanning
Validate fixes using the accessibility scanner:

```bash
# Re-scan after implementing fixes
mcp__accessibility_scanner__scan_url --url "http://localhost:3000" --rules "wcag21aa"

# Compare before/after results
mcp__accessibility_scanner__generate_report --scan_results "..." --format "comparison"
```

### Token Usage Optimization Benefits

This two-system approach provides significant token efficiency:

1. **Reduced Analysis Tokens**: Cache common patterns instead of re-analyzing
2. **Quick Context Retrieval**: Fast pattern lookup without full re-scanning
3. **Incremental Improvements**: Build on cached knowledge base
4. **Pattern Reuse**: Apply successful patterns across similar components

### Integration Workflow Examples

#### Example 1: Form Accessibility Implementation
```bash
# 1. Initial scan
mcp__accessibility_scanner__scan_html --html_content "form_html" --rules "wcag21aa"

# 2. Cache the solution pattern
add_project_documentation --content "Form accessibility fix for missing labels..."

# 3. Quick retrieval for similar forms
search_fastapi_docs --query "form label accessibility pattern"
```

#### Example 2: iOS VoiceOver Implementation
```bash
# 1. Scan iOS app accessibility
mcp__accessibility_scanner__scan_html --html_content "ios_webview_content" --rules "wcag21aa"

# 2. Cache VoiceOver patterns
add_project_documentation --content "VoiceOver implementation patterns..."

# 3. Quick lookup for similar components
search_swift_ios_docs --query "VoiceOver navigation accessibility"
```

### Best Practices for Accessibility Integration

1. **Progressive Enhancement**: Start with basic accessibility, build up complexity
2. **Pattern Documentation**: Always document successful accessibility solutions
3. **Regular Validation**: Use accessibility scanner for continuous validation
4. **Context Preservation**: Maintain accessibility context in cached patterns
5. **Cross-Platform Consistency**: Ensure accessibility patterns work across web and mobile

### Monitoring and Maintenance

#### Accessibility Metrics Tracking
```bash
# Monitor accessibility improvements over time
get_collection_stats  # Track documentation growth
mcp__accessibility_scanner__generate_report --format "metrics"
```

#### Pattern Evolution
- Regularly update cached patterns based on new accessibility standards
- Refine patterns based on user feedback and testing
- Maintain version history of accessibility implementations

This integrated workflow ensures comprehensive accessibility coverage while maintaining development efficiency through intelligent caching and pattern reuse.