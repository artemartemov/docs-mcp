"""
FastAPI Documentation Adapter using Sphinx Inventory API.

Example implementation for adding FastAPI documentation support.
"""

import asyncio
import logging
from typing import List, Optional
from urllib.parse import urljoin

import aiohttp
import sphobjinv as soi
from bs4 import BeautifulSoup

from ..base import BaseDocumentationSource, DocumentContent, DocumentMetadata

logger = logging.getLogger(__name__)

class FastAPIDocsSource(BaseDocumentationSource):
    """FastAPI official documentation source using Sphinx inventory"""
    
    def __init__(self, version: str = "latest"):
        self.version = version
        base_url = "https://fastapi.tiangolo.com/"
        super().__init__(f"FastAPI {version} Official Docs", base_url)
        
        self.inventory_url = f"{base_url}objects.inv"
        self.inventory: Optional[soi.Inventory] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Configure for respectful scraping
        self.rate_limit_delay = 1.0  # Respectful rate limiting
        self.batch_size = 20
        
        # Priority sections for FastAPI
        self.priority_sections = {
            "tutorial", "advanced", "deployment", "features", 
            "reference", "help", "benchmarks"
        }
        
        # Skip patterns for cleaner content
        self.skip_patterns = {
            "genindex", "modindex", "search", "sitemap"
        }
    
    async def __aenter__(self):
        """Initialize async HTTP session"""
        connector = aiohttp.TCPConnector(limit_per_host=2)
        timeout = aiohttp.ClientTimeout(total=30)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'DocumentationServer-Ingester/1.0 (Educational Research)',
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
        return "fastapi"
    
    async def discover_content(self) -> List[str]:
        """
        Discover FastAPI content using both Sphinx inventory and sitemap.
        FastAPI's inventory only covers API reference, but sitemap has tutorial/advanced guides.
        """
        logger.info(f"🔍 Discovering FastAPI documentation using multiple methods")
        
        discovered_urls = set()
        
        # Method 1: Load Sphinx inventory for API reference
        try:
            logger.info(f"📚 Loading Sphinx inventory from {self.inventory_url}")
            self.inventory = soi.Inventory(url=self.inventory_url)
            logger.info(f"   Found {len(self.inventory.objects)} inventory objects")
            
            for obj in self.inventory.objects:
                # Skip certain object types that don't provide good content
                if obj.role in ['data', 'attribute'] and obj.domain == 'py':
                    continue
                
                # Build full URL
                if obj.uri and not obj.uri.startswith('$'):
                    # Remove fragment identifier for page-level content
                    clean_uri = obj.uri.split('#')[0] if '#' in obj.uri else obj.uri
                    full_url = urljoin(self.base_url, clean_uri)
                    
                    # Apply filtering
                    if self._should_include_url(full_url):
                        discovered_urls.add(full_url)
            
            logger.info(f"   Added {len([u for u in discovered_urls if '/reference/' in u])} reference URLs from inventory")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to load Sphinx inventory: {e}")
        
        # Method 2: Load sitemap.xml for comprehensive coverage
        try:
            logger.info(f"🗺️  Loading sitemap from {self.base_url}sitemap.xml")
            sitemap_urls = await self._discover_from_sitemap()
            initial_count = len(discovered_urls)
            discovered_urls.update(sitemap_urls)
            logger.info(f"   Added {len(discovered_urls) - initial_count} URLs from sitemap")
            
        except Exception as e:
            logger.warning(f"⚠️  Failed to load sitemap: {e}")
        
        # Filter and clean URLs
        filtered_urls = []
        for url in discovered_urls:
            if self._should_include_url(url):
                filtered_urls.append(url)
        
        logger.info(f"📋 Found {len(filtered_urls)} FastAPI documentation URLs")
        
        # Log section breakdown
        section_counts = {}
        for url in filtered_urls:
            section = self._extract_section_from_url(url)
            section_counts[section] = section_counts.get(section, 0) + 1
        
        logger.info("📊 Section breakdown:")
        for section, count in sorted(section_counts.items()):
            logger.info(f"   {section}: {count} pages")
        
        return sorted(filtered_urls)
    
    def _should_include_url(self, url: str) -> bool:
        """Filter URLs based on relevance and quality"""
        # Skip unwanted patterns
        for pattern in self.skip_patterns:
            if pattern in url:
                return False
        
        # Only include HTML pages
        if not url.endswith(('.html', '/')):
            return False
        
        return True
    
    async def _fallback_discovery(self) -> List[str]:
        """Fallback method if Sphinx inventory isn't available"""
        logger.info("Using fallback discovery method for FastAPI")
        
        # Common FastAPI documentation URLs
        fallback_urls = [
            f"{self.base_url}",
            f"{self.base_url}tutorial/",
            f"{self.base_url}tutorial/first-steps/",
            f"{self.base_url}tutorial/path-params/",
            f"{self.base_url}tutorial/query-params/",
            f"{self.base_url}tutorial/body/",
            f"{self.base_url}advanced/",
            f"{self.base_url}deployment/",
        ]
        
        return fallback_urls
    
    async def _discover_from_sitemap(self) -> set:
        """Discover URLs from FastAPI sitemap.xml"""
        sitemap_urls = set()
        
        try:
            sitemap_url = urljoin(self.base_url, "sitemap.xml")
            await asyncio.sleep(self.rate_limit_delay)
            
            async with self.session.get(sitemap_url) as response:
                if response.status == 200:
                    sitemap_content = await response.text()
                    # Parse sitemap XML
                    from xml.etree import ElementTree as ET
                    root = ET.fromstring(sitemap_content)
                    
                    for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                        loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                        if loc_elem is not None and loc_elem.text:
                            if loc_elem.text.startswith(self.base_url):
                                sitemap_urls.add(loc_elem.text)
                    
                    logger.info(f"📄 Found {len(sitemap_urls)} URLs from sitemap")
                    
        except Exception as e:
            logger.warning(f"Could not load sitemap: {e}")
        
        return sitemap_urls
    
    def _extract_section_from_url(self, url: str) -> str:
        """Extract main section from URL for organization"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if not path_parts:
            return "home"
        
        section = path_parts[0]
        if section in self.priority_sections:
            return section
        else:
            return "other"
    
    async def extract_content(self, url: str) -> Optional[DocumentContent]:
        """Extract content from a single FastAPI documentation page"""
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
            
            # Clean title
            if " - FastAPI" in title:
                title = title.split(" - FastAPI")[0].strip()
            
            # Extract main content - FastAPI uses different structure
            content_div = (
                soup.find('article') or
                soup.find('div', class_='content') or
                soup.find('main') or
                soup.find('div', role='main')
            )
            
            if not content_div:
                logger.warning(f"No main content found for {url}")
                return None
            
            # Remove navigation and non-content elements
            for element in content_div.find_all([
                'nav', 'header', 'footer', 'aside'
            ]):
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
                framework="fastapi",
                source="FastAPI Official Documentation",
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
    
    def _extract_section_from_url(self, url: str) -> str:
        """Extract main section from URL for organization"""
        if "tutorial" in url:
            return "tutorial"
        elif "advanced" in url:
            return "advanced"
        elif "deployment" in url:
            return "deployment"
        elif "features" in url:
            return "features"
        else:
            return "general"
    
    def _determine_doc_type(self, url: str, title: str, content: str) -> str:
        """Determine document type based on URL and content"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        if "tutorial" in url_lower:
            return "tutorial"
        elif "advanced" in url_lower:
            return "advanced_guide"
        elif "deployment" in url_lower:
            return "deployment_guide"
        elif "reference" in url_lower:
            return "api_reference"
        else:
            return "documentation"
    
    def _extract_subsection(self, url: str) -> str:
        """Extract subsection from URL structure"""
        parts = [p for p in url.split('/') if p and not p.startswith('http')]
        return parts[-1].replace('.html', '') if parts else ""