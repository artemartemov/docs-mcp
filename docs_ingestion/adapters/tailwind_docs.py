"""
Tailwind CSS Documentation Adapter.

Handles Tailwind CSS documentation from tailwindcss.com.
Tailwind has excellent structured documentation with clear sections.
"""

import asyncio
import logging
import aiohttp
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import json

from ..base import BaseDocumentationSource, DocumentContent, DocumentMetadata

logger = logging.getLogger(__name__)

class TailwindDocsSource(BaseDocumentationSource):
    """Tailwind CSS official documentation source"""
    
    def __init__(self, version: str = "latest"):
        self.version = version
        base_url = "https://tailwindcss.com/docs/"
        super().__init__(f"Tailwind CSS {version} Docs", base_url)
        
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Configure for respectful scraping
        self.rate_limit_delay = 1.0  # Tailwind is generally fast
        self.batch_size = 25
        
        # Tailwind documentation structure
        self.priority_sections = {
            "installation", "core-concepts", "customization", "base-styles",
            "layout", "flexbox-grid", "spacing", "sizing", "typography", 
            "backgrounds", "borders", "effects", "filters", "tables",
            "transitions-animation", "transforms", "interactivity", "svg",
            "accessibility", "plugins", "functions-directives"
        }
        
        # Skip patterns for cleaner content
        self.skip_patterns = {
            "/playground", "/resources", "/brand", "/changelog",
            "/blog", "/_next/", "/images/", ".png", ".jpg", ".svg"
        }
        
        # Known important Tailwind documentation URLs
        self.core_urls = [
            "installation",
            "editor-setup", 
            "using-with-preprocessors",
            "optimizing-for-production",
            "browser-support",
            
            # Core Concepts
            "utility-first",
            "hover-focus-and-other-states",
            "responsive-design", 
            "dark-mode",
            "adding-custom-styles",
            "functions-and-directives",
            
            # Layout
            "aspect-ratio",
            "container",
            "columns",
            "break-after",
            "break-before",
            "break-inside",
            "box-decoration-break",
            "box-sizing",
            "display",
            "floats",
            "clear",
            "isolation",
            "object-fit",
            "object-position",
            "overflow",
            "overscroll-behavior",
            "position",
            "top-right-bottom-left",
            "visibility",
            "z-index",
            
            # Flexbox & Grid
            "flex-basis",
            "flex-direction",
            "flex-wrap",
            "flex",
            "flex-grow",
            "flex-shrink",
            "order",
            "grid-template-columns",
            "grid-column",
            "grid-template-rows",
            "grid-row",
            "grid-auto-flow",
            "grid-auto-columns",
            "grid-auto-rows",
            "gap",
            "justify-content",
            "justify-items", 
            "justify-self",
            "align-content",
            "align-items",
            "align-self",
            "place-content",
            "place-items",
            "place-self",
            
            # Spacing
            "padding",
            "margin",
            "space",
            
            # Sizing
            "width",
            "min-width",
            "max-width", 
            "height",
            "min-height",
            "max-height",
            
            # Typography
            "font-family",
            "font-size",
            "font-smoothing",
            "font-style",
            "font-weight",
            "font-variant-numeric",
            "letter-spacing",
            "line-height",
            "list-style-image",
            "list-style-position",
            "list-style-type",
            "text-align",
            "text-color",
            "text-decoration",
            "text-decoration-color",
            "text-decoration-style",
            "text-decoration-thickness",
            "text-underline-offset",
            "text-transform",
            "text-overflow",
            "text-indent",
            "vertical-align",
            "whitespace",
            "word-break",
            "content"
        ]
    
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
        return "tailwind"
    
    async def discover_content(self) -> List[str]:
        """
        Discover Tailwind CSS documentation URLs.
        Uses sitemap and navigation crawling for comprehensive coverage.
        """
        logger.info(f"🔍 Discovering Tailwind CSS documentation from {self.base_url}")
        
        discovered_urls = set()
        
        # Method 1: Use known core URLs
        for path in self.core_urls:
            full_url = urljoin(self.base_url, path)
            discovered_urls.add(full_url)
        
        # Method 2: Try sitemap
        sitemap_urls = await self._discover_from_sitemap()
        discovered_urls.update(sitemap_urls)
        
        # Method 3: Parse navigation from main docs page
        nav_urls = await self._discover_from_navigation()
        discovered_urls.update(nav_urls)
        
        # Filter and clean URLs
        filtered_urls = []
        for url in discovered_urls:
            if self._should_include_url(url):
                filtered_urls.append(url)
        
        logger.info(f"📋 Found {len(filtered_urls)} Tailwind CSS documentation URLs")
        
        # Log section breakdown
        section_counts = {}
        for url in filtered_urls:
            section = self._extract_section_from_url(url)
            section_counts[section] = section_counts.get(section, 0) + 1
        
        logger.info("📊 Section breakdown:")
        for section, count in sorted(section_counts.items()):
            logger.info(f"   {section}: {count} pages")
        
        return sorted(filtered_urls)
    
    async def _discover_from_sitemap(self) -> Set[str]:
        """Try to discover URLs from sitemap"""
        sitemap_urls = set()
        
        try:
            sitemap_url = "https://tailwindcss.com/sitemap.xml"
            await asyncio.sleep(self.rate_limit_delay)
            
            async with self.session.get(sitemap_url) as response:
                if response.status == 200:
                    sitemap_content = await response.text()
                    from xml.etree import ElementTree as ET
                    root = ET.fromstring(sitemap_content)
                    
                    for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                        loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                        if loc_elem is not None and loc_elem.text:
                            if "/docs/" in loc_elem.text:
                                sitemap_urls.add(loc_elem.text)
                    
                    logger.info(f"📄 Found {len(sitemap_urls)} URLs from sitemap")
                    
        except Exception as e:
            logger.warning(f"Could not load sitemap: {e}")
        
        return sitemap_urls
    
    async def _discover_from_navigation(self) -> Set[str]:
        """Discover URLs by crawling navigation"""
        nav_urls = set()
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            async with self.session.get(self.base_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Tailwind navigation is usually in sidebar
                    nav_selectors = [
                        'nav a[href]',
                        '.navigation a[href]',
                        '[data-testid="sidebar"] a[href]',
                        '.sidebar a[href]'
                    ]
                    
                    for selector in nav_selectors:
                        links = soup.select(selector)
                        for link in links:
                            href = link.get('href', '')
                            if href.startswith('/docs/'):
                                full_url = urljoin('https://tailwindcss.com', href)
                                nav_urls.add(full_url)
                            elif href.startswith('https://tailwindcss.com/docs/'):
                                nav_urls.add(href)
                    
                    logger.info(f"🧭 Found {len(nav_urls)} URLs from navigation")
                    
        except Exception as e:
            logger.warning(f"Could not crawl navigation: {e}")
        
        return nav_urls
    
    def _should_include_url(self, url: str) -> bool:
        """Filter URLs based on relevance and quality"""
        # Skip unwanted patterns
        for pattern in self.skip_patterns:
            if pattern in url:
                return False
        
        # Only include docs URLs
        if "/docs/" not in url:
            return False
        
        # Skip fragments and queries
        if '#' in url or '?' in url:
            return False
        
        return True
    
    def _extract_section_from_url(self, url: str) -> str:
        """Extract main section from URL for organization"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) >= 2 and path_parts[0] == "docs":
            section = path_parts[1]
            
            # Group related sections
            if section in ["width", "height", "min-width", "max-width", "min-height", "max-height"]:
                return "sizing"
            elif section in ["padding", "margin", "space"]:
                return "spacing"
            elif section.startswith("font-") or section in ["text-align", "text-color", "text-decoration", "letter-spacing", "line-height"]:
                return "typography"
            elif section.startswith("bg-") or section in ["background-color", "background-image", "background-size"]:
                return "backgrounds"
            elif section.startswith("border") or section in ["outline", "ring"]:
                return "borders"
            elif section in ["flex", "grid", "justify-content", "align-items"] or section.startswith("flex-") or section.startswith("grid-"):
                return "flexbox_grid"
            else:
                return section
        
        return "general"
    
    async def extract_content(self, url: str) -> Optional[DocumentContent]:
        """Extract content from a single Tailwind CSS documentation page"""
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
            
            # Clean title - remove Tailwind CSS suffix
            if " - Tailwind CSS" in title:
                title = title.split(" - Tailwind CSS")[0].strip()
            
            # Extract main content - Tailwind uses specific structure
            content_selectors = [
                'main',
                '[role="main"]',
                '.prose',
                '.documentation',
                'article',
                '.content'
            ]
            
            content_div = None
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    break
            
            if not content_div:
                logger.warning(f"No main content found for {url}")
                return None
            
            # Remove navigation, ads, and non-content elements
            for element in content_div.find_all([
                'nav', 'header', 'footer', 'aside', 'script', 'style',
                '.navigation', '.sidebar', '.header', '.footer',
                '[data-docsearch-ignore]', '.search'
            ]):
                element.decompose()
            
            # Extract clean text content
            content_text = content_div.get_text()
            content_text = ' '.join(content_text.split())  # Normalize whitespace
            
            # Skip very short content
            if len(content_text) < 150:
                logger.debug(f"Skipping short content for {url}")
                return None
            
            # Determine document metadata
            section = self._extract_section_from_url(url)
            doc_type = self._determine_doc_type(url, title, content_text)
            subsection = self._extract_subsection(url)
            
            # Create metadata
            metadata = DocumentMetadata(
                framework="tailwind",
                source="Tailwind CSS Official Documentation",
                doc_type=doc_type,
                title=title,
                url=url,
                section=section,
                subsection=subsection,
                version=self.version,
                language="en",
                tags=self._generate_tags(url, title, content_text)
            )
            
            return DocumentContent(content=content_text, metadata=metadata)
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    def _determine_doc_type(self, url: str, title: str, content: str) -> str:
        """Determine document type based on URL and content"""
        url_lower = url.lower()
        title_lower = title.lower()
        
        if "installation" in url_lower or "setup" in title_lower:
            return "installation_guide"
        elif any(concept in url_lower for concept in ["utility-first", "responsive", "dark-mode", "hover-focus"]):
            return "core_concept"
        elif any(term in url_lower for term in ["customization", "configuration", "plugins"]):
            return "customization_guide"
        elif any(term in title_lower for term in ["utility", "class"]):
            return "utility_reference"
        else:
            return "documentation"
    
    def _extract_subsection(self, url: str) -> str:
        """Extract subsection from URL structure"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) >= 2:
            return path_parts[-1]  # Last part of path
        else:
            return "overview"
    
    def _generate_tags(self, url: str, title: str, content: str) -> List[str]:
        """Generate relevant tags for Tailwind content"""
        tags = ["css", "utility_first", "responsive_design", "frontend"]
        
        # Add section-based tags
        section = self._extract_section_from_url(url)
        if section in ["layout", "flexbox_grid"]:
            tags.append("layout")
        elif section in ["typography", "text"]:
            tags.append("typography")
        elif section in ["spacing", "sizing"]:
            tags.append("spacing")
        elif section in ["backgrounds", "borders"]:
            tags.append("styling")
        elif section in ["transitions", "animations", "transforms"]:
            tags.append("motion")
        
        # Add feature-based tags
        if "responsive" in content.lower()[:500]:
            tags.append("responsive")
        if "dark mode" in content.lower()[:500]:
            tags.append("dark_mode")
        if "hover" in content.lower()[:500] or "focus" in content.lower()[:500]:
            tags.append("interactive_states")
        if "grid" in title.lower() or "flexbox" in title.lower():
            tags.append("css_grid")
        
        # Add difficulty level
        if any(term in title.lower() for term in ["installation", "getting started", "basics"]):
            tags.append("beginner")
        elif any(term in title.lower() for term in ["advanced", "custom", "plugin"]):
            tags.append("advanced")
        else:
            tags.append("intermediate")
        
        return tags
    
    async def preprocess_content(self, content: str) -> str:
        """Clean Tailwind-specific content"""
        lines = content.split('\n')
        
        # Remove common Tailwind navigation text and code editor references
        skip_phrases = {
            "play cdn", "tailwind ui", "headless ui", "hero icons",
            "copy to clipboard", "edit on github", "improve this page"
        }
        
        filtered_lines = []
        for line in lines:
            line = line.strip()
            if (len(line) > 10 and 
                not any(phrase in line.lower() for phrase in skip_phrases)):
                filtered_lines.append(line)
        
        return ' '.join(filtered_lines)
    
    async def postprocess_metadata(self, metadata: DocumentMetadata) -> DocumentMetadata:
        """Enhance Tailwind metadata"""
        # Add version-specific tags if mentioned
        content_lower = metadata.content.lower()[:800]
        if "tailwind css v3" in content_lower or "version 3" in content_lower:
            metadata.tags.append("v3")
        elif "tailwind css v2" in content_lower or "version 2" in content_lower:
            metadata.tags.append("v2")
        
        # Add framework integration tags
        if "react" in content_lower:
            metadata.tags.append("react_integration")
        if "vue" in content_lower:
            metadata.tags.append("vue_integration")
        if "angular" in content_lower:
            metadata.tags.append("angular_integration")
        if "next.js" in content_lower or "nextjs" in content_lower:
            metadata.tags.append("nextjs_integration")
        
        return metadata