# Adding New Documentation Sources

This guide shows you exactly how to add new documentation sources to the system.

## 🚀 Quick Start: Adding React.js

Now you can add React documentation with:

```bash
# List all available sources (now includes react!)
./run_ingestion.sh --list-sources

# Test React ingestion
./run_ingestion.sh --source react --test

# Full React ingestion  
./run_ingestion.sh --source react
```

## 📋 Step-by-Step Guide for Any Framework

### Step 1: Create the Adapter

Create a new file: `docs_ingestion/adapters/your_framework_docs.py`

```python
"""
YourFramework Documentation Adapter
"""

import asyncio
import logging
import aiohttp
from typing import List, Optional
from urllib.parse import urljoin
import sphobjinv as soi  # For Sphinx-based docs
from bs4 import BeautifulSoup

from ..base import BaseDocumentationSource, DocumentContent, DocumentMetadata

logger = logging.getLogger(__name__)

class YourFrameworkDocsSource(BaseDocumentationSource):
    """Your framework documentation source"""
    
    def __init__(self, version: str = "latest"):
        self.version = version
        base_url = "https://docs.yourframework.com/" 
        super().__init__(f"YourFramework {version} Docs", base_url)
        
        # Configure for respectful scraping
        self.rate_limit_delay = 1.0  # Seconds between requests
        self.batch_size = 20
        
        # Your framework's documentation structure
        self.priority_sections = {
            "tutorial", "guide", "reference", "api"
        }
        
        # Skip unwanted content
        self.skip_patterns = {
            "/search", "/404", "/_static/", "/images/"
        }
    
    def get_framework_name(self) -> str:
        return "yourframework"
    
    async def discover_content(self) -> List[str]:
        """Discover all documentation URLs"""
        # Choose your discovery method:
        
        # Option A: Sphinx inventory (like Python/FastAPI)
        if hasattr(self, 'inventory_url'):
            return await self._discover_from_sphinx_inventory()
        
        # Option B: Sitemap.xml (like React)  
        return await self._discover_from_sitemap()
        
        # Option C: Manual URL list
        return await self._discover_from_known_urls()
    
    async def extract_content(self, url: str) -> Optional[DocumentContent]:
        """Extract content from a documentation page"""
        # Your extraction logic here
        pass
```

### Step 2: Choose Your Discovery Method

#### **Option A: Sphinx-Based (Python, FastAPI, Django)**
```python
async def discover_content(self) -> List[str]:
    self.inventory_url = f"{self.base_url}objects.inv"
    self.inventory = soi.Inventory(url=self.inventory_url)
    
    unique_urls = set()
    for obj in self.inventory.objects:
        if obj.uri and not obj.uri.startswith('$'):
            clean_uri = obj.uri.split('#')[0]
            full_url = urljoin(self.base_url, clean_uri)
            if self._should_include_url(full_url):
                unique_urls.add(full_url)
    
    return sorted(list(unique_urls))
```

#### **Option B: Sitemap-Based (React, Vue, Angular)**
```python
async def discover_content(self) -> List[str]:
    sitemap_url = urljoin(self.base_url, "sitemap.xml")
    async with self.session.get(sitemap_url) as response:
        if response.status == 200:
            sitemap_content = await response.text()
            # Parse XML and extract URLs
            # (See react_docs.py for full implementation)
```

#### **Option C: Known URLs (Smaller frameworks)**
```python
async def discover_content(self) -> List[str]:
    known_urls = [
        f"{self.base_url}getting-started",
        f"{self.base_url}tutorials/",
        f"{self.base_url}api-reference/",
        # Add your known important URLs
    ]
    return known_urls
```

### Step 3: Register the Adapter

1. **Add to `docs_ingestion/adapters/__init__.py`:**
```python
from .your_framework_docs import YourFrameworkDocsSource

__all__ = [..., "YourFrameworkDocsSource"]
```

2. **Add to `ingest_documentation.py`:**
```python
# Import section
from docs_ingestion.adapters import ..., YourFrameworkDocsSource

# Configuration section
AVAILABLE_SOURCES = {
    # ... existing sources ...
    "yourframework": {
        "name": "YourFramework Official Documentation",
        "description": "Description of your framework docs",
        "class": YourFrameworkDocsSource,
        "versions": ["latest"],
        "default_version": "latest"
    }
}

# Processing section
elif source_name == "yourframework":
    config = IngestionConfig.get_source_info("yourframework")
    version = config.get("default_version", "latest")
    result = await ingest_generic_docs(YourFrameworkDocsSource, source_name, version, test_mode)
    results[source_name] = result
```

### Step 4: Test Your Adapter

```bash
# List sources (should now include yourframework)
./run_ingestion.sh --list-sources

# Test with limited content
./run_ingestion.sh --source yourframework --test

# Full ingestion
./run_ingestion.sh --source yourframework
```

## 🎯 Framework-Specific Tips

### **React/Vue/Angular (Modern JS Frameworks)**
- Often don't use Sphinx, use sitemap or navigation crawling
- Look for `<main>`, `<article>`, or `[role="main"]` selectors
- Check for MDX content areas
- Higher rate limiting recommended (1.5s+)

### **Django/Flask (Python Web Frameworks)**  
- Usually Sphinx-based, use inventory method
- Similar patterns to Python docs
- Look for `div.body` or `div.document` selectors

### **Ruby on Rails/Laravel (Web Frameworks)**
- Mixed approaches, often custom sites
- May need navigation crawling + known URLs
- Check for framework-specific CSS classes

### **Swift/Kotlin (Mobile Frameworks)**
- Apple/Google docs have specific structures
- May require specialized parsing
- Higher rate limiting for respect

## 🔧 Common Patterns

### **Content Extraction**
```python
# Try multiple selectors for content
content_selectors = [
    'main', '[role="main"]', 'article', 
    '.content', '.documentation', '.markdown'
]

content_div = None
for selector in content_selectors:
    content_div = soup.select_one(selector)
    if content_div:
        break
```

### **Metadata Enhancement**
```python
def _determine_doc_type(self, url: str, title: str, content: str) -> str:
    url_lower = url.lower()
    
    if "tutorial" in url_lower:
        return "tutorial"
    elif "api" in url_lower or "reference" in url_lower:
        return "api_reference"
    elif "guide" in url_lower:
        return "guide"
    else:
        return "documentation"
```

### **Smart Filtering**
```python
def _should_include_url(self, url: str) -> bool:
    # Skip unwanted patterns
    for pattern in self.skip_patterns:
        if pattern in url:
            return False
    
    # Only include priority sections
    for section in self.priority_sections:
        if section in url.lower():
            return True
    
    return url.endswith('index.html')  # Include main pages
```

## 🎉 You're Done!

Your new documentation source is now ready to use. The system will:

- ✅ Discover content intelligently
- ✅ Extract clean, searchable text  
- ✅ Add rich metadata for better search
- ✅ Handle rate limiting respectfully
- ✅ Integrate with the MCP server automatically

**Example usage after setup:**
```bash
./run_ingestion.sh --source yourframework --test
./run_server.sh
# Then use search_yourframework_docs() in your MCP client!
```