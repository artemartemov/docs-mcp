"""
React.js Documentation Adapter.

Example implementation for adding React.js documentation support.
React docs don't use Sphinx, so this demonstrates alternative approaches.
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

class ReactDocsSource(BaseDocumentationSource):
    """React.js official documentation source"""
    
    def __init__(self, version: str = "latest"):
        self.version = version
        base_url = "https://react.dev/"
        super().__init__(f"React.js {version} Official Docs", base_url)
        
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Configure for respectful scraping
        self.rate_limit_delay = 1.5  # Be extra respectful to React docs
        self.batch_size = 15
        
        # React documentation structure
        self.priority_sections = {
            "learn", "reference", "community", "blog"
        }
        
        # Skip patterns for cleaner content
        self.skip_patterns = {
            "/images/", "/icons/", ".png", ".jpg", ".svg",
            "/search", "/404", "_next/", "static/"
        }
        
        # Known important React documentation URLs
        self.core_urls = [
            "learn",
            "learn/installation", 
            "learn/start-a-new-react-project",
            "learn/thinking-in-react",
            "learn/describing-the-ui",
            "learn/adding-interactivity", 
            "learn/managing-state",
            "learn/escape-hatches",
            "reference/react",
            "reference/react-dom",
            "reference/rules",
            "reference/legacy"
        ]
    
    async def __aenter__(self):
        """Initialize async HTTP session"""
        connector = aiohttp.TCPConnector(limit_per_host=1)  # Conservative
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
        return "react"
    
    async def discover_content(self) -> List[str]:
        """
        Discover React documentation URLs.
        Since React doesn't use Sphinx and has SPA navigation, we use comprehensive discovery.
        """
        logger.info(f"🔍 Discovering React documentation from {self.base_url}")
        
        discovered_urls = set()
        
        # Method 1: Use known core URLs
        for path in self.core_urls:
            full_url = urljoin(self.base_url, path)
            discovered_urls.add(full_url)
        
        # Method 2: Try to find sitemap.xml (likely won't work but worth trying)
        sitemap_urls = await self._discover_from_sitemap()
        discovered_urls.update(sitemap_urls)
        
        # Method 3: Crawl main sections first
        section_urls = await self._discover_from_navigation()
        discovered_urls.update(section_urls)
        
        # Method 4: Recursive section discovery - crawl each main section
        recursive_urls = await self._discover_from_sections()
        discovered_urls.update(recursive_urls)
        
        # Filter and clean URLs
        filtered_urls = []
        for url in discovered_urls:
            if self._should_include_url(url):
                filtered_urls.append(url)
        
        logger.info(f"📋 Found {len(filtered_urls)} React documentation URLs")
        
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
        """Try to discover URLs from sitemap.xml"""
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
    
    async def _discover_from_navigation(self) -> Set[str]:
        """Discover URLs by crawling main navigation"""
        nav_urls = set()
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            async with self.session.get(self.base_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Find all links in navigation areas
                    nav_selectors = ['nav', '[role="navigation"]', '.navigation', '.nav']
                    
                    for selector in nav_selectors:
                        nav_elements = soup.select(selector)
                        for nav in nav_elements:
                            links = nav.find_all('a', href=True)
                            for link in links:
                                href = link['href']
                                if href.startswith('/'):
                                    full_url = urljoin(self.base_url, href)
                                    nav_urls.add(full_url)
                                elif href.startswith(self.base_url):
                                    nav_urls.add(href)
                    
                    logger.info(f"🧭 Found {len(nav_urls)} URLs from navigation")
                    
        except Exception as e:
            logger.warning(f"Could not crawl navigation: {e}")
        
        return nav_urls
    
    async def _discover_from_sections(self) -> Set[str]:
        """Recursively discover URLs from main sections (learn, reference, etc.)"""
        section_urls = set()
        
        # Main sections to crawl comprehensively
        main_sections = [
            'learn',
            'reference/react',
            'reference/react-dom', 
            'blog',
            'community'
        ]
        
        for section in main_sections:
            try:
                section_url = urljoin(self.base_url, section)
                logger.info(f"🔄 Crawling section: {section}")
                await asyncio.sleep(self.rate_limit_delay)
                
                async with self.session.get(section_url) as response:
                    if response.status == 200:
                        html_content = await response.text()
                        soup = BeautifulSoup(html_content, 'html.parser')
                        
                        # Find all links on this section page
                        all_links = soup.find_all('a', href=True)
                        section_found = 0
                        
                        for link in all_links:
                            href = link['href']
                            
                            # Handle relative links
                            if href.startswith('/'):
                                full_url = urljoin(self.base_url, href)
                            elif href.startswith(self.base_url):
                                full_url = href
                            else:
                                continue
                                
                            # Only add URLs that belong to our target sections
                            if (full_url.startswith(self.base_url) and 
                                any(f'/{sec}/' in full_url or full_url.endswith(f'/{sec}') 
                                    for sec in ['learn', 'reference', 'blog', 'community'])):
                                section_urls.add(full_url)
                                section_found += 1
                        
                        logger.info(f"   Found {section_found} URLs in {section}")
                        
                    else:
                        logger.warning(f"HTTP {response.status} for section {section}")
                        
            except Exception as e:
                logger.warning(f"Could not crawl section {section}: {e}")
        
        logger.info(f"📂 Found {len(section_urls)} URLs from recursive section discovery")
        return section_urls
    
    def _should_include_url(self, url: str) -> bool:
        """Filter URLs based on relevance and quality"""
        # Skip unwanted patterns
        for pattern in self.skip_patterns:
            if pattern in url:
                return False
        
        # Only include pages from the main site
        if not url.startswith(self.base_url):
            return False
        
        # Skip external links and anchors
        if '#' in url or '?' in url:
            return False
        
        parsed_url = urlparse(url)
        path = parsed_url.path.strip('/')
        
        if not path:  # Homepage
            return True
            
        # Include all URLs from priority sections (more permissive now)
        for section in self.priority_sections:
            if path.startswith(section):
                return True
        
        # Also include any other React documentation URLs we might have missed
        if any(section in path for section in ['learn', 'reference', 'blog', 'community']):
            return True
        
        return False
    
    def _extract_section_from_url(self, url: str) -> str:
        """Extract main section from URL for organization"""
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
        """Extract content from a single React documentation page"""
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
            
            # Clean title - remove site suffix
            if " – React" in title:
                title = title.split(" – React")[0].strip()
            elif " | React" in title:
                title = title.split(" | React")[0].strip()
            
            # Extract main content - React uses different structures
            content_selectors = [
                'main',
                '[role="main"]', 
                '.content',
                'article',
                '.markdown',
                '.mdx-content'
            ]
            
            content_div = None
            for selector in content_selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    break
            
            if not content_div:
                # Fallback to body content, removing nav/header/footer
                content_div = soup.find('body')
                if content_div:
                    for element in content_div.find_all(['nav', 'header', 'footer', 'aside']):
                        element.decompose()
            
            if not content_div:
                logger.warning(f"No main content found for {url}")
                return None
            
            # Remove navigation, ads, and non-content elements
            for element in content_div.find_all([
                'nav', 'header', 'footer', 'aside', 'script', 'style',
                '.navigation', '.sidebar', '.ad', '.advertisement'
            ]):
                element.decompose()
            
            # Extract clean text content
            content_text = content_div.get_text()
            content_text = ' '.join(content_text.split())  # Normalize whitespace
            
            # Skip very short content
            if len(content_text) < 300:  # React pages tend to be longer
                logger.debug(f"Skipping short content for {url}")
                return None
            
            # Determine document metadata
            section = self._extract_section_from_url(url)
            doc_type = self._determine_doc_type(url, title, content_text)
            subsection = self._extract_subsection(url)
            
            # Create metadata
            metadata = DocumentMetadata(
                framework="react",
                source="React.js Official Documentation", 
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
        
        if "learn" in url_lower:
            if "tutorial" in title_lower or "getting started" in title_lower:
                return "tutorial"
            else:
                return "guide"
        elif "reference" in url_lower:
            return "api_reference"
        elif "blog" in url_lower:
            return "blog_post"
        elif "community" in url_lower:
            return "community_guide"
        else:
            return "documentation"
    
    def _extract_subsection(self, url: str) -> str:
        """Extract subsection from URL structure"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) >= 2:
            return path_parts[-1]  # Last part of the path
        elif len(path_parts) == 1:
            return path_parts[0]
        else:
            return "home"
    
    def _generate_tags(self, url: str, title: str, content: str) -> List[str]:
        """Generate relevant tags for React content"""
        tags = ["javascript", "frontend", "ui_library"]
        
        # Add section-based tags
        if "hooks" in url.lower() or "hooks" in title.lower():
            tags.append("hooks")
        if "components" in url.lower() or "component" in title.lower():
            tags.append("components")
        if "state" in url.lower() or "state" in title.lower():
            tags.append("state_management")
        if "jsx" in content.lower()[:1000]:  # Check first 1000 chars
            tags.append("jsx")
        if "typescript" in content.lower()[:1000]:
            tags.append("typescript")
        
        return tags
    
    async def preprocess_content(self, content: str) -> str:
        """Clean React-specific content"""
        lines = content.split('\n')
        
        # Remove common React navigation text
        skip_phrases = {
            "edit this page", "improve this page", "next.js", 
            "create react app", "quick start", "installation guide"
        }
        
        filtered_lines = []
        for line in lines:
            line = line.strip()
            if (len(line) > 15 and 
                not any(phrase in line.lower() for phrase in skip_phrases)):
                filtered_lines.append(line)
        
        return ' '.join(filtered_lines)
    
    async def postprocess_metadata(self, metadata: DocumentMetadata) -> DocumentMetadata:
        """Enhance React metadata"""
        # Add React version tag
        if self.version != "latest":
            metadata.tags.append(f"react_{self.version}")
        
        # Add learning level tags
        if metadata.section == "learn":
            if "installation" in metadata.url or "start" in metadata.url:
                metadata.tags.append("beginner")
            elif "advanced" in metadata.url or "escape-hatches" in metadata.url:
                metadata.tags.append("advanced")
            else:
                metadata.tags.append("intermediate")
        
        return metadata