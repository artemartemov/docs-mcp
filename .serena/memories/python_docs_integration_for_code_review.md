# Python Documentation Integration for Code Review

## Critical Reminder: Use Internal Python Documentation

**ALWAYS** use the Python documentation from our docs-mcp server for all Python-related code reviewing, suggestions, and analysis.

## Available Python Documentation Resources

### Current Python Docs Coverage in ChromaDB
- **465+ Python documents** extracted from official Python documentation
- **Complete coverage** including:
  - Library reference (319 docs)
  - C API documentation (70 docs)
  - How-to guides (25 docs)
  - Tutorials (19 docs)
  - Language reference (11 docs)
  - Using guides (9 docs)
  - Extending guides (7 docs)
  - Packaging guides (2 docs)

### How to Access Python Documentation

```bash
# Search Python docs via MCP tools
search_python_docs("asyncio event loop")
search_python_docs("pathlib file operations")
search_python_docs("dataclasses field validation")
search_python_docs("typing annotations")

# Direct ChromaDB queries
collection.query(
    query_texts=["Python async await patterns"],
    where={"framework": "python"},
    n_results=5
)
```

### Code Review Integration Strategy

**When reviewing Python code, ALWAYS:**

1. **Search Relevant Python Docs First**
   - Before making suggestions, query our Python documentation
   - Reference official Python patterns and best practices
   - Use actual Python documentation examples

2. **Provide Documentation-Backed Suggestions**
   - Quote from official Python docs when possible
   - Reference specific Python modules and functions
   - Include links to internal documentation

3. **Leverage Comprehensive Coverage**
   - Use library reference docs for standard library suggestions
   - Reference Python tutorials for beginner-friendly explanations
   - Use how-to guides for practical implementation patterns
   - Reference C API docs for performance-critical code

### Example Code Review Workflow

```python
# Instead of general suggestions, use our Python docs:

# 1. Search for relevant documentation
search_python_docs("pathlib vs os.path best practices")

# 2. Reference specific Python documentation
"According to our Python documentation, pathlib is preferred over os.path 
for new code because it provides object-oriented path handling..."

# 3. Provide documentation-backed examples
"The Python docs show this pattern for file operations:
from pathlib import Path
path = Path('file.txt')
if path.exists():
    content = path.read_text()"
```

### Framework-Specific Integration

**For Different Code Types:**

- **FastAPI Code**: Use both `search_python_docs()` and `search_fastapi_docs()`
- **Async Code**: Query our Python docs for asyncio patterns
- **Data Structures**: Reference Python collections and dataclasses docs
- **File Operations**: Use pathlib documentation from our collection
- **Error Handling**: Reference Python exception handling docs
- **Testing**: Use Python unittest/pytest documentation

### Benefits of Using Internal Documentation

1. **Consistency**: All reviews based on same authoritative source
2. **Completeness**: 465+ documents cover virtually all Python topics
3. **Accuracy**: Official Python documentation, not third-party interpretations
4. **Integration**: Seamless access via MCP tools
5. **Context**: Documentation is optimized for our specific use cases

### MCP Tools for Python Code Review

```python
# Available tools for Python documentation
search_python_docs(query)           # Search Python-specific docs
search_fastapi_docs(query)          # For FastAPI + Python patterns
get_security_guidelines()           # Python security best practices
add_project_documentation()         # Add custom Python patterns
```

### Action Items for Code Review

**Before every Python code review:**
1. Search relevant Python documentation topics
2. Reference official Python patterns and examples
3. Provide documentation-backed suggestions
4. Include internal documentation links where helpful
5. Use authoritative Python terminology and concepts

**Remember**: We have 465+ Python documents at our disposal - use them to provide the most accurate, comprehensive, and authoritative Python code reviews possible.

## Integration with docs-mcp CLI

Use the CLI to test and validate Python documentation access:

```bash
# Test Python documentation search
./docs-mcp test --framework python

# Analyze Python docs coverage
./docs-mcp analyze --stats

# Extract additional Python docs if needed
./docs-mcp extract --framework python
```

This ensures all Python code reviews are grounded in official, comprehensive documentation rather than general knowledge.