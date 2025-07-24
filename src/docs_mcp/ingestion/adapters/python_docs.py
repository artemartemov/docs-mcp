"""
Python Official Documentation Adapter using Sphinx Inventory API.

Leverages sphobjinv for efficient access to Python documentation metadata
and selective content extraction based on object inventory.
"""

import asyncio
import logging
import aiohttp
from typing import List, Optional, Dict, Set
from urllib.parse import urljoin, urlparse
import sphobjinv as soi
from bs4 import BeautifulSoup

from ..base import BaseDocumentationSource, DocumentContent, DocumentMetadata

logger = logging.getLogger(__name__)

class PythonDocsSource(BaseDocumentationSource):
    """Python official documentation source using Sphinx inventory"""
    
    def __init__(self, version: str = "3"):
        self.version = version
        base_url = f"https://docs.python.org/{version}/"
        super().__init__(f"Python {version} Official Docs", base_url)
        
        self.inventory_url = f"{base_url}objects.inv"
        self.inventory: Optional[soi.Inventory] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Configure for respectful scraping
        self.rate_limit_delay = 0.8  # Slightly faster for official docs
        self.batch_size = 30
        
        # Priority sections to focus on
        self.priority_sections = {
            "tutorial", "library", "reference", "using", "howto", 
            "installing", "distributing", "extending", "c-api"
        }
        
        # Skip patterns for cleaner content
        self.skip_patterns = {
            "genindex", "modindex", "search", "glossary", 
            "_sources", "_static", "bugs", "copyright"
        }
    
    async def __aenter__(self):
        """Initialize async HTTP session"""
        connector = aiohttp.TCPConnector(limit_per_host=2)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'ResaleAnalyzer-DocsIngester/2.0 (Educational Research)',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-US,en;q=0.9',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close async HTTP session"""
        if self.session:
            await self.session.close()
    
    def get_framework_name(self) -> str:
        return "python"
    
    async def discover_content(self) -> List[str]:
        """Discover content using Sphinx inventory file"""
        logger.info(f"🔍 Loading Sphinx inventory from {self.inventory_url}")
        
        try:
            # Load inventory using sphobjinv
            self.inventory = soi.Inventory(url=self.inventory_url)
            logger.info(f"📚 Loaded inventory with {len(self.inventory.objects)} objects")
            
            # Extract unique URLs from inventory
            unique_urls = set()
            
            for obj in self.inventory.objects:
                # Skip certain object types that don't provide good content
                if obj.role in ['data', 'attribute', 'exception'] and obj.domain == 'py':
                    continue
                
                # Build full URL
                if obj.uri and not obj.uri.startswith('$'):
                    # Remove fragment identifier for page-level content
                    clean_uri = obj.uri.split('#')[0] if '#' in obj.uri else obj.uri
                    full_url = urljoin(self.base_url, clean_uri)
                    
                    # Apply filtering
                    if self._should_include_url(full_url):
                        unique_urls.add(full_url)
            
            # Convert to sorted list for consistent processing
            discovered_urls = sorted(list(unique_urls))
            
            # Log section breakdown
            section_counts = {}
            for url in discovered_urls:
                section = self._extract_section_from_url(url)
                section_counts[section] = section_counts.get(section, 0) + 1
            
            logger.info("📊 Section breakdown:")
            for section, count in sorted(section_counts.items()):
                logger.info(f"   {section}: {count} pages")
            
            return discovered_urls
            
        except Exception as e:
            logger.error(f"❌ Failed to load inventory: {e}")
            return []
    
    def _should_include_url(self, url: str) -> bool:
        """Filter URLs based on relevance and quality"""
        # Skip unwanted patterns
        for pattern in self.skip_patterns:
            if pattern in url:
                return False
        
        # Only include HTML pages
        if not url.endswith(('.html', '/')):
            return False
        
        # Prefer priority sections
        url_lower = url.lower()
        has_priority_section = any(section in url_lower for section in self.priority_sections)
        
        # Include if it has priority section or is a main page
        return has_priority_section or url.endswith('index.html')
    
    def _extract_section_from_url(self, url: str) -> str:
        """Extract main section from URL for organization"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p and p != self.version]
        return path_parts[0] if path_parts else "root"
    
    async def should_skip_content(self, url: str) -> bool:
        """Check if content should be skipped"""
        # Skip if URL contains skip patterns
        return any(pattern in url for pattern in self.skip_patterns)
    
    async def extract_content(self, url: str) -> Optional[DocumentContent]:
        """Extract content from a single Python documentation page"""
        try:
            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)
            
            # Fetch page content
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                
                html_content = await response.text()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else ""
            
            # Clean title (remove "Python 3.x documentation" suffix)
            if " — Python " in title:
                title = title.split(" — Python ")[0].strip()
            
            # Extract main content
            content_div = (
                soup.find('div', class_='body') or
                soup.find('div', class_='document') or  
                soup.find('main') or
                soup.find('div', role='main')
            )
            
            if not content_div:
                logger.warning(f"No main content found for {url}")
                return None
            
            # Remove navigation and non-content elements
            for element in content_div.find_all([
                'div', 'nav', 'header', 'footer'
            ], class_=['sphinxsidebar', 'related', 'footer', 'headerlink']):
                element.decompose()
            
            # Remove script and style elements
            for element in content_div.find_all(['script', 'style']):
                element.decompose()
            
            # Extract clean text content
            content_text = content_div.get_text()
            content_text = ' '.join(content_text.split())  # Normalize whitespace
            
            # Skip very short content
            if len(content_text) < 200:
                logger.debug(f"Skipping short content for {url}")
                return None
            
            # Determine document metadata
            section = self._extract_section_from_url(url)
            doc_type = self._determine_doc_type(url, title, content_text)
            subsection = self._extract_subsection(url)
            
            # Create metadata
            metadata = DocumentMetadata(
                framework="python",
                source="Python Official Documentation",
                doc_type=doc_type,
                title=title,
                url=url,
                section=section,
                subsection=subsection,
                version=self.version,
                language="en"
            )
            
            return DocumentContent(content=content_text, metadata=metadata)
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    def _determine_doc_type(self, url: str, title: str, content: str) -> str:
        """Determine document type based on URL and content"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        if "tutorial" in url_lower or "tutorial" in title_lower:
            return "tutorial"
        elif "howto" in url_lower:
            return "howto"
        elif "library" in url_lower:
            return "library_reference"
        elif "reference" in url_lower:
            return "language_reference"
        elif "using" in url_lower:
            return "using_guide"
        elif "c-api" in url_lower:
            return "c_api"
        elif "extending" in url_lower:
            return "extending_guide"
        elif "installing" in url_lower or "distributing" in url_lower:
            return "packaging_guide"
        else:
            return "documentation"
    
    def _extract_subsection(self, url: str) -> str:
        """Extract subsection from URL structure"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p and p != self.version]
        
        if len(path_parts) >= 2:
            # Use filename without extension as subsection
            filename = path_parts[-1].replace('.html', '')
            return filename
        return ""
    
    async def preprocess_content(self, content: str) -> str:
        """Clean and optimize content for vector search"""
        lines = content.split('\n')
        
        # Remove very short lines and common navigation text
        filtered_lines = []
        skip_phrases = {
            "table of contents", "navigation", "quick search",
            "previous topic", "next topic", "this page"
        }
        
        for line in lines:
            line = line.strip()
            if (len(line) > 10 and 
                not any(phrase in line.lower() for phrase in skip_phrases)):
                filtered_lines.append(line)
        
        return ' '.join(filtered_lines)
    
    async def postprocess_metadata(self, metadata: DocumentMetadata) -> DocumentMetadata:
        """Enhance metadata with additional tags and classification"""
        # Add relevant tags based on content
        tags = []
        
        # Add section-based tags
        if metadata.section == "library":
            tags.append("standard_library")
        elif metadata.section == "tutorial":
            tags.append("beginner_friendly")
        elif metadata.section == "reference":
            tags.append("comprehensive")
        
        # Add doc type tags
        if metadata.doc_type in ["tutorial", "howto"]:
            tags.append("learning_resource")
        elif "reference" in metadata.doc_type:
            tags.append("reference_material")
        
        # Add Python version tag
        tags.append(f"python_{metadata.version}")
        
        metadata.tags = tags
        return metadata