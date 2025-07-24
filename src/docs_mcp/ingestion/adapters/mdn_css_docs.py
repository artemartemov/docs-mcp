"""
MDN CSS Documentation Adapter.

Extracts comprehensive CSS documentation from Mozilla Developer Network
covering all CSS properties, selectors, concepts, and guides.
"""

import asyncio
import logging
import aiohttp
import re
from typing import List, Optional, Dict, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag

from ..base import BaseDocumentationSource, DocumentContent, DocumentMetadata

logger = logging.getLogger(__name__)

class MDNCSSDocsSource(BaseDocumentationSource):
    """MDN CSS documentation source from official Mozilla docs"""
    
    def __init__(self, version: str = "latest"):
        self.version = version
        base_url = "https://developer.mozilla.org/en-US/docs/Web/CSS/"
        super().__init__(f"MDN CSS {version} Docs", base_url)
        
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Configure for respectful scraping
        self.rate_limit_delay = 1.0  # Be respectful to MDN's servers
        self.batch_size = 25
        
        # Priority sections for comprehensive CSS coverage
        self.priority_sections = {
            "reference", "properties", "selectors", "concepts", "layout",
            "guides", "tutorials", "cookbook", "modules", "at-rules",
            "functions", "types", "values", "units"
        }
        
        # Skip patterns for cleaner content
        self.skip_patterns = {
            "search", "404", "error", "sitemap", "robots.txt",
            "privacy", "terms", "legal", "talk:", "user:",
            "template:", "category:", "special:"
        }
        
        # Section categorization for better organization
        self.section_categories = {
            "fundamentals": ["basics", "getting-started", "first-steps", "building-blocks"],
            "properties": ["properties", "property"],
            "selectors": ["selectors", "selector", "pseudo-class", "pseudo-element"],
            "layout": ["layout", "flexbox", "grid", "positioning", "float"],
            "styling": ["styling", "colors", "fonts", "text", "backgrounds", "borders"],
            "advanced": ["transforms", "animations", "transitions", "filters"],
            "concepts": ["concepts", "cascade", "inheritance", "box-model", "stacking"],
            "reference": ["reference", "syntax", "specification"],
            "guides": ["guides", "how-to", "cookbook", "recipes"],
            "modules": ["modules", "module"]
        }
    
    async def __aenter__(self):
        """Initialize async HTTP session"""
        connector = aiohttp.TCPConnector(limit_per_host=3)
        timeout = aiohttp.ClientTimeout(total=45)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'ResaleAnalyzer-DocsIngester/2.0 (Educational Research)',
                'Accept': 'text/html,application/xhtml+xml',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close async HTTP session"""
        if self.session:
            await self.session.close()
    
    def get_framework_name(self) -> str:
        return "css"
    
    async def discover_content(self) -> List[str]:
        """Discover content by crawling the CSS documentation structure"""
        logger.info(f"🔍 Discovering MDN CSS documentation from {self.base_url}")
        
        discovered_urls = set()
        
        try:
            # Start with key entry points
            entry_points = [
                self.base_url,  # Main CSS page
                f"{self.base_url}Reference/",  # CSS Reference
                f"{self.base_url}CSS_Properties_Reference/",  # Properties
                f"{self.base_url}CSS_Selectors/",  # Selectors
                f"{self.base_url}Layout_cookbook/",  # Layout cookbook
                f"{self.base_url}Tutorials/",  # Tutorials
                f"{self.base_url}Using_CSS/",  # Using CSS guides
                f"{self.base_url}CSS_Flexible_Box_Layout/",  # Flexbox
                f"{self.base_url}CSS_Grid_Layout/",  # Grid
                f"{self.base_url}CSS_Transitions/",  # Transitions
                f"{self.base_url}CSS_Animations/",  # Animations
                f"{self.base_url}CSS_Transforms/",  # Transforms
            ]
            
            for entry_url in entry_points:
                await self._discover_from_page(entry_url, discovered_urls)
                await asyncio.sleep(self.rate_limit_delay)
            
            # Special discovery for CSS properties index
            await self._discover_css_properties(discovered_urls)
            
            # Filter and sort URLs - optimize with set comprehension
            filtered_urls = list({url for url in discovered_urls if self._should_include_url(url)})
            logger.info(f"📋 Discovered {len(filtered_urls)} relevant CSS documentation pages")
            
            return sorted(filtered_urls)
            
        except Exception as e:
            logger.error(f"❌ Failed to discover content: {e}")
            return []
    
    async def _discover_from_page(self, url: str, discovered_urls: set, max_depth: int = 2) -> None:
        """Recursively discover URLs from a page"""
        if max_depth <= 0 or url in discovered_urls:
            return
        
        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                discovered_urls.add(url)
                
                # Find CSS documentation links
                css_links = set()
                
                # Main content links
                for link in soup.select('a[href]'):
                    href = link.get('href')
                    if href:
                        full_url = urljoin(url, href)
                        if self._is_css_docs_url(full_url):
                            css_links.add(full_url)
                
                # Navigation and sidebar links
                nav_selectors = [
                    '.sidebar a[href]',
                    '.document-toc a[href]',
                    '.page-menu a[href]',
                    '.quick-links a[href]',
                    'nav a[href]'
                ]
                
                for selector in nav_selectors:
                    for link in soup.select(selector):
                        href = link.get('href')
                        if href:
                            full_url = urljoin(url, href)
                            if self._is_css_docs_url(full_url):
                                css_links.add(full_url)
                
                # Process discovered links
                for css_url in css_links:
                    if css_url not in discovered_urls:
                        if max_depth > 1:
                            await self._discover_from_page(css_url, discovered_urls, max_depth - 1)
                        else:
                            discovered_urls.add(css_url)
                
        except Exception as e:
            logger.debug(f"Error discovering from {url}: {e}")
    
    async def _discover_css_properties(self, discovered_urls: set):
        """Special discovery for CSS properties from reference pages"""
        try:
            # CSS Reference page often has comprehensive property lists
            reference_url = f"{self.base_url}Reference/"
            
            async with self.session.get(reference_url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for property links
                    for link in soup.select('a[href*="/CSS/"]'):
                        href = link.get('href')
                        if href:
                            full_url = urljoin(reference_url, href)
                            if self._is_css_docs_url(full_url):
                                discovered_urls.add(full_url)
                
        except Exception as e:
            logger.debug(f"Error discovering CSS properties: {e}")
    
    def _is_css_docs_url(self, url: str) -> bool:
        """Check if URL is part of CSS documentation"""
        parsed = urlparse(url)
        return (
            parsed.netloc == "developer.mozilla.org" and
            "/docs/Web/CSS" in parsed.path and
            not any(skip in url.lower() for skip in self.skip_patterns)
        )
    
    def _should_include_url(self, url: str) -> bool:
        """Determine if URL should be included in extraction"""
        if not self._is_css_docs_url(url):
            return False
        
        # Skip certain file types and fragments
        if any(ext in url.lower() for ext in ['.pdf', '.jpg', '.png', '.gif', '.css', '.js']):
            return False
        
        # Remove fragment identifiers for consistency
        clean_url = url.split('#')[0]
        
        return True
    
    async def extract_content(self, url: str) -> Optional[DocumentContent]:
        """Extract content from a specific CSS documentation page"""
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Extract title
                title = self._extract_title(soup, url)
                if not title:
                    return None
                
                # Extract main content
                content = self._extract_main_content(soup)
                if not content or len(content.strip()) < 100:
                    logger.debug(f"Skipping {url} - insufficient content")
                    return None
                
                # Create metadata
                metadata = self._create_metadata(url, title, content)
                
                return DocumentContent(content=content, metadata=metadata)
                
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract page title"""
        # Try various title selectors specific to MDN
        title_selectors = [
            'h1.page-title',
            '.main-page-content h1',
            '.article-header h1',
            'h1',
            '.document-head h1',
            'title'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                if title and len(title) > 3:
                    # Clean up MDN-specific title patterns
                    title = re.sub(r'\s*-\s*CSS[:\s]*.*$', '', title)
                    title = re.sub(r'\s*\|\s*MDN$', '', title)
                    return title
        
        # Fallback to URL-based title
        path = urlparse(url).path
        path_parts = [p for p in path.split('/') if p]
        if path_parts:
            return path_parts[-1].replace('_', ' ').replace('-', ' ').title()
        
        return None
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main CSS documentation content"""
        # Try MDN-specific content selectors
        content_selectors = [
            '.main-page-content',
            '#content .article',
            '.document-content',
            'main',
            '.content',
            '#wikiArticle',
            '.wiki-article'
        ]
        
        main_content = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                main_content = content_elem
                break
        
        if not main_content:
            main_content = soup.find('body')
        
        if not main_content:
            return ""
        
        # Remove unwanted elements specific to MDN
        unwanted_selectors = [
            'nav', '.navigation', '.page-menu',
            'footer', '.page-footer',
            '.sidebar', '.quick-links',
            'script', 'style',
            '.breadcrumbs', '.document-head',
            '.prev-next', '.page-buttons',
            '.contributors', '.metadata',
            '.bc-table', '.bc-support',  # Browser compatibility tables
            '.notecard', '.warning', '.note'  # Keep these for now, they have useful info
        ]
        
        for selector in unwanted_selectors:
            for elem in main_content.select(selector):
                elem.decompose()
        
        # Extract structured content
        content_parts = []
        
        # Process elements in order
        for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'pre', 'code', 'dt', 'dd']):
            if element.name.startswith('h'):
                level = '#' * int(element.name[1])
                content_parts.append(f"\n{level} {element.get_text().strip()}\n")
            elif element.name == 'pre':
                code_content = element.get_text().strip()
                if code_content:
                    content_parts.append(f"\n```css\n{code_content}\n```\n")
            elif element.name == 'code' and element.parent.name != 'pre':
                content_parts.append(f"`{element.get_text().strip()}`")
            elif element.name == 'dt':
                content_parts.append(f"\n**{element.get_text().strip()}**")
            elif element.name == 'dd':
                content_parts.append(f": {element.get_text().strip()}")
            else:
                text = element.get_text().strip()
                if text and len(text) > 5:
                    content_parts.append(text)
        
        return '\n'.join(content_parts).strip()
    
    def _categorize_url(self, url: str) -> str:
        """Categorize URL into CSS documentation sections"""
        url_lower = url.lower()
        
        for category, keywords in self.section_categories.items():
            if any(keyword in url_lower for keyword in keywords):
                return category
        
        # Check for specific CSS features
        if any(term in url_lower for term in ['property', 'properties']):
            return "properties"
        elif any(term in url_lower for term in ['selector', 'pseudo']):
            return "selectors"
        elif any(term in url_lower for term in ['layout', 'flexbox', 'grid']):
            return "layout"
        elif any(term in url_lower for term in ['animation', 'transition', 'transform']):
            return "advanced"
        elif any(term in url_lower for term in ['color', 'font', 'text', 'background']):
            return "styling"
        
        return "general"
    
    def _determine_doc_type(self, url: str, title: str, content: str) -> str:
        """Determine document type based on URL, title, and content"""
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()[:2000]
        
        if any(term in url_lower for term in ['reference', 'specification']):
            return "reference"
        elif any(term in url_lower for term in ['tutorial', 'getting-started', 'first-steps']):
            return "tutorial"
        elif any(term in url_lower for term in ['guide', 'how-to', 'cookbook']):
            return "guide"
        elif any(term in url_lower for term in ['concept', 'understanding']):
            return "concept"
        elif any(term in title_lower for term in ['property', 'selector', 'function']):
            return "css_reference"
        elif any(term in content_lower for term in ['syntax:', 'values:', 'example']):
            return "css_documentation"
        elif any(term in url_lower for term in ['module', 'specification']):
            return "specification"
        else:
            return "documentation"
    
    def _create_metadata(self, url: str, title: str, content: str) -> DocumentMetadata:
        """Create metadata for the CSS document"""
        section = self._categorize_url(url)
        doc_type = self._determine_doc_type(url, title, content)
        tags = self._generate_tags(url, title, content)
        
        # Extract subsection from URL
        path_parts = urlparse(url).path.strip('/').split('/')
        subsection = path_parts[-1] if len(path_parts) > 3 else "main"
        
        return DocumentMetadata(
            framework="css",
            source="MDN CSS Official Documentation",
            doc_type=doc_type,
            title=title,
            url=url,
            section=section,
            subsection=subsection,
            version=self.version,
            language="en",
            tags=tags
        )
    
    def _generate_tags(self, url: str, title: str, content: str) -> List[str]:
        """Generate relevant tags for the CSS content"""
        tags = ["css", "web_development", "styling", "mdn_official"]
        
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()[:3000]
        
        # Add URL-based tags
        if "property" in url_lower or "properties" in url_lower:
            tags.extend(["css_properties", "styling_properties"])
        if "selector" in url_lower:
            tags.extend(["css_selectors", "targeting"])
        if "layout" in url_lower:
            tags.extend(["css_layout", "positioning"])
        if "flexbox" in url_lower:
            tags.extend(["flexbox", "flexible_layout"])
        if "grid" in url_lower:
            tags.extend(["css_grid", "grid_layout"])
        if "animation" in url_lower:
            tags.extend(["css_animations", "motion"])
        if "transition" in url_lower:
            tags.extend(["css_transitions", "effects"])
        
        # Add content-based tags
        if any(term in content_lower for term in ["property", "value", "inherit"]):
            tags.append("css_properties")
        if any(term in content_lower for term in ["selector", "element", "class", "id"]):
            tags.append("css_selectors")
        if any(term in content_lower for term in ["layout", "position", "display"]):
            tags.append("layout_properties")
        if any(term in content_lower for term in ["color", "background", "border"]):
            tags.append("visual_styling")
        if any(term in content_lower for term in ["font", "text", "typography"]):
            tags.append("typography")
        if any(term in content_lower for term in ["responsive", "media", "breakpoint"]):
            tags.append("responsive_design")
        if any(term in content_lower for term in ["browser", "support", "compatibility"]):
            tags.append("browser_support")
        
        # Add difficulty level
        if any(term in title_lower for term in ["introduction", "basic", "getting started"]):
            tags.append("beginner")
        elif any(term in title_lower for term in ["advanced", "complex", "specification"]):
            tags.append("advanced")
        else:
            tags.append("intermediate")
        
        return tags
    
    async def preprocess_content(self, content: str) -> str:
        """Clean and structure CSS content"""
        lines = content.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip very short lines unless they're markdown headers or code
            if len(line) > 3 or line.startswith('#') or line.startswith('```'):
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    async def postprocess_metadata(self, metadata: DocumentMetadata) -> DocumentMetadata:
        """Enhance metadata with additional CSS-specific information"""
        # Add comprehensive documentation tag
        metadata.tags.append("official_documentation")
        metadata.tags.append("web_scraped")
        metadata.tags.append("mozilla_mdn")
        
        # Add CSS version if detectable
        if any(term in metadata.url.lower() for term in ["css3", "css-3"]):
            metadata.tags.append("css3")
        elif any(term in metadata.url.lower() for term in ["css2", "css-2"]):
            metadata.tags.append("css2")
        
        return metadata