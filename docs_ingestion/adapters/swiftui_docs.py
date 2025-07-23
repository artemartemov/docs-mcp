"""
SwiftUI Documentation Adapter.

Handles Apple's SwiftUI documentation from developer.apple.com.
Apple docs have a specific structure and require careful handling.
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

class SwiftUIDocsSource(BaseDocumentationSource):
    """SwiftUI official documentation source from Apple Developer"""
    
    def __init__(self, version: str = "latest"):
        self.version = version
        base_url = "https://developer.apple.com/documentation/swiftui/"
        super().__init__(f"SwiftUI {version} Official Docs", base_url)
        
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Configure for very respectful scraping (Apple is strict)
        self.rate_limit_delay = 2.0  # Extra respectful for Apple
        self.batch_size = 10
        
        # SwiftUI documentation structure
        self.priority_sections = {
            "views", "controls", "layout", "navigation", "data", 
            "drawing", "animation", "gestures", "previews", "app-structure"
        }
        
        # Skip patterns for cleaner content
        self.skip_patterns = {
            "/videos/", "/images/", "/graphics/", "/sample-code/",
            "/downloads/", "wwdc", "/beta/", "/release-notes/"
        }
        
        # Known important SwiftUI documentation URLs
        self.core_urls = [
            "",  # Base SwiftUI docs
            "text",
            "button", 
            "image",
            "vstack",
            "hstack",
            "list",
            "navigationview",
            "tabview",
            "form",
            "picker",
            "toggle",
            "slider",
            "stepper",
            "textfield",
            "securefield",
            "state",
            "binding",
            "observedobject",
            "environmentobject",
            "view",
            "app",
            "scene"
        ]
    
    async def __aenter__(self):
        """Initialize async HTTP session with Apple-friendly headers"""
        connector = aiohttp.TCPConnector(limit_per_host=1)  # Very conservative
        timeout = aiohttp.ClientTimeout(total=45)  # Apple can be slow
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close async HTTP session"""
        if self.session:
            await self.session.close()
    
    def get_framework_name(self) -> str:
        return "swiftui"
    
    async def discover_content(self) -> List[str]:
        """
        Discover SwiftUI documentation URLs.
        Apple doesn't provide easy programmatic access, so we use multiple methods.
        """
        logger.info(f"🔍 Discovering SwiftUI documentation from {self.base_url}")
        
        discovered_urls = set()
        
        # Method 1: Use known core URLs
        for path in self.core_urls:
            full_url = urljoin(self.base_url, path)
            discovered_urls.add(full_url)
        
        # Method 2: Try to parse the main SwiftUI page structure
        main_page_urls = await self._discover_from_main_page()
        discovered_urls.update(main_page_urls)
        
        # Method 3: Try common SwiftUI patterns
        pattern_urls = await self._discover_from_patterns()
        discovered_urls.update(pattern_urls)
        
        # Filter and clean URLs
        filtered_urls = []
        for url in discovered_urls:
            if self._should_include_url(url):
                filtered_urls.append(url)
        
        logger.info(f"📋 Found {len(filtered_urls)} SwiftUI documentation URLs")
        
        # Log section breakdown
        section_counts = {}
        for url in filtered_urls:
            section = self._extract_section_from_url(url)
            section_counts[section] = section_counts.get(section, 0) + 1
        
        logger.info("📊 Section breakdown:")
        for section, count in sorted(section_counts.items()):
            logger.info(f"   {section}: {count} pages")
        
        return sorted(filtered_urls)
    
    async def _discover_from_main_page(self) -> Set[str]:
        """Discover URLs from the main SwiftUI documentation page"""
        discovered_urls = set()
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            async with self.session.get(self.base_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Look for documentation links in the main content
                    content_selectors = [
                        '.content a[href]',
                        '.documentation-topic a[href]',
                        '.topic-list a[href]',
                        'main a[href]'
                    ]
                    
                    for selector in content_selectors:
                        links = soup.select(selector)
                        for link in links:
                            href = link.get('href', '')
                            if href.startswith('/documentation/swiftui/'):
                                full_url = urljoin('https://developer.apple.com', href)
                                discovered_urls.add(full_url)
                    
                    logger.info(f"🏠 Found {len(discovered_urls)} URLs from main page")
                    
        except Exception as e:
            logger.warning(f"Could not crawl main SwiftUI page: {e}")
        
        return discovered_urls
    
    async def _discover_from_patterns(self) -> Set[str]:
        """Discover URLs using common SwiftUI naming patterns"""
        pattern_urls = set()
        
        # Common SwiftUI view and modifier patterns
        common_views = [
            "text", "button", "image", "label", "link",
            "vstack", "hstack", "zstack", "lazystack",
            "list", "foreach", "scrollview", "grid",
            "navigationview", "navigationlink", "tabview",
            "sheet", "alert", "actionsheet", "popover",
            "form", "section", "picker", "toggle", "slider",
            "textfield", "securefield", "texteditor",
            "progressview", "gauge", "menu", "menubutton"
        ]
        
        common_modifiers = [
            "foregroundcolor", "background", "padding", "frame",
            "clipshape", "cornerradius", "shadow", "overlay",
            "scaledtofit", "scaledtofill", "aspectratio",
            "animation", "transition", "gesture", "onappear"
        ]
        
        # Add view URLs
        for view in common_views:
            url = urljoin(self.base_url, view.lower())
            pattern_urls.add(url)
        
        # Add modifier URLs (they often have different paths)
        for modifier in common_modifiers:
            url = urljoin(self.base_url, f"view/{modifier.lower()}")
            pattern_urls.add(url)
        
        logger.info(f"🎯 Generated {len(pattern_urls)} pattern-based URLs")
        return pattern_urls
    
    def _should_include_url(self, url: str) -> bool:
        """Filter URLs based on relevance and quality"""
        # Skip unwanted patterns
        for pattern in self.skip_patterns:
            if pattern in url:
                return False
        
        # Only include SwiftUI documentation
        if "/documentation/swiftui" not in url:
            return False
        
        # Skip fragments and query parameters
        if '#' in url or '?' in url:
            return False
        
        return True
    
    def _extract_section_from_url(self, url: str) -> str:
        """Extract main section from URL for organization"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) >= 3 and path_parts[1] == "swiftui":
            return path_parts[2] if len(path_parts) > 2 else "core"
        else:
            return "swiftui"
    
    async def extract_content(self, url: str) -> Optional[DocumentContent]:
        """Extract content from a single SwiftUI documentation page"""
        try:
            # Rate limiting - extra careful with Apple
            await asyncio.sleep(self.rate_limit_delay)
            
            # Fetch page content
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
                
                html_content = await response.text()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract title - Apple has specific title structure
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else ""
            
            # Clean title - remove Apple developer suffix
            if " | Apple Developer Documentation" in title:
                title = title.split(" | Apple Developer Documentation")[0].strip()
            
            # Extract main content - Apple uses specific classes
            content_selectors = [
                '.documentation-content',
                '.content',
                'main[role="main"]',
                '.main-content',
                'article'
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
                '.navigation', '.breadcrumbs', '.sidebar', 
                '.developer-tools', '.download-sample'
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
                framework="swiftui",
                source="Apple Developer Documentation",
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
        
        if "struct" in title_lower or "protocol" in title_lower:
            return "type_reference"
        elif "modifier" in title_lower or "/view/" in url_lower:
            return "modifier_reference"
        elif "tutorial" in url_lower or "getting started" in title_lower:
            return "tutorial"
        elif "guide" in url_lower:
            return "guide"
        else:
            return "api_reference"
    
    def _extract_subsection(self, url: str) -> str:
        """Extract subsection from URL structure"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) >= 4:
            return path_parts[-1]  # Last part of the path
        elif len(path_parts) >= 3:
            return path_parts[2]
        else:
            return "core"
    
    def _generate_tags(self, url: str, title: str, content: str) -> List[str]:
        """Generate relevant tags for SwiftUI content"""
        tags = ["ios", "macos", "watchos", "tvos", "apple", "ui_framework"]
        
        # Add component-based tags
        if any(term in title.lower() for term in ["button", "text", "image", "label"]):
            tags.append("ui_components")
        if any(term in title.lower() for term in ["stack", "grid", "list"]):
            tags.append("layout")
        if any(term in title.lower() for term in ["navigation", "tab", "sheet"]):
            tags.append("navigation")
        if any(term in title.lower() for term in ["state", "binding", "observed"]):
            tags.append("data_flow")
        if any(term in title.lower() for term in ["animation", "transition"]):
            tags.append("animation")
        if any(term in title.lower() for term in ["gesture", "drag", "tap"]):
            tags.append("interaction")
        
        # Add iOS version tags if mentioned
        content_lower = content.lower()[:1000]  # Check first 1000 chars
        if "ios 17" in content_lower:
            tags.append("ios_17")
        elif "ios 16" in content_lower:
            tags.append("ios_16")
        elif "ios 15" in content_lower:
            tags.append("ios_15")
        
        return tags
    
    async def preprocess_content(self, content: str) -> str:
        """Clean SwiftUI-specific content"""
        lines = content.split('\n')
        
        # Remove common Apple documentation navigation text
        skip_phrases = {
            "developer documentation", "apple developer", "download xcode",
            "beta software", "sdk", "framework", "sample code",
            "tech talks", "wwdc", "app store"
        }
        
        filtered_lines = []
        for line in lines:
            line = line.strip()
            if (len(line) > 20 and 
                not any(phrase in line.lower() for phrase in skip_phrases)):
                filtered_lines.append(line)
        
        return ' '.join(filtered_lines)
    
    async def postprocess_metadata(self, metadata: DocumentMetadata) -> DocumentMetadata:
        """Enhance SwiftUI metadata"""
        # Add platform-specific tags based on URL patterns
        url_lower = metadata.url.lower()
        title_lower = metadata.title.lower()
        
        if "macos" in url_lower or "macos" in title_lower:
            metadata.tags.append("macos_specific")
        if "watchos" in url_lower or "watchos" in title_lower:
            metadata.tags.append("watchos_specific")
        if "tvos" in url_lower or "tvos" in title_lower:
            metadata.tags.append("tvos_specific")
        
        # Add complexity level
        if any(term in title_lower for term in ["getting started", "basics", "introduction"]):
            metadata.tags.append("beginner")
        elif any(term in title_lower for term in ["advanced", "custom", "complex"]):
            metadata.tags.append("advanced")
        else:
            metadata.tags.append("intermediate")
        
        return metadata