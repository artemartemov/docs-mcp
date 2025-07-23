"""
Figma API Documentation Adapter with Browser Automation.

Handles Figma API documentation from figma.com.
Uses browser automation to properly handle React SPA content.
"""

import asyncio
import logging
import aiohttp
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import json

from ..spa_base import SPADocumentationSource
from ..base import DocumentContent, DocumentMetadata

logger = logging.getLogger(__name__)

class FigmaDocsSource(SPADocumentationSource):
    """Figma API official documentation source with browser automation"""
    
    def __init__(self, version: str = "latest", use_browser: bool = True):
        self.version = version
        base_url = "https://www.figma.com/developers/api/"
        super().__init__(f"Figma API {version} Docs", base_url, use_browser=use_browser)
        
        # Configure for respectful scraping
        self.rate_limit_delay = 1.2  # Respectful for Figma
        self.batch_size = 20
        
        # Figma-specific browser automation settings
        self.js_wait_timeout = 12000  # Figma React app can take time
        self.network_idle_timeout = 2500  # Wait for API calls to complete
        
        # Figma API documentation structure
        self.priority_sections = {
            "introduction", "authentication", "files", "comments", 
            "users", "teams", "projects", "components", "styles",
            "variables", "dev-resources", "webhooks", "plugins"
        }
        
        # Skip patterns for cleaner content
        self.skip_patterns = {
            "/community/", "/blog/", "/pricing/", "/templates/",
            "/careers/", "/about/", "/_next/", "/images/", 
            ".png", ".jpg", ".svg", "/assets/"
        }
        
        # Comprehensive Figma API documentation URLs for SPA extraction
        self.core_urls = [
            "",  # Base API docs
            
            # Getting Started
            "introduction/",
            "authentication/", 
            "rate-limiting/",
            "errors/",
            
            # Files API - Core functionality
            "files/",
            "files/images/",
            "files/nodes/",
            
            # Comments API
            "comments/",
            
            # Users & Teams
            "users/",
            "teams/",
            
            # Components & Styles  
            "components/",
            "styles/",
            
            # Variables (Design Tokens)
            "variables/",
            
            # Webhooks
            "webhooks/",
            
            # Plugins
            "plugins/"
        ]
    
    async def __aenter__(self):
        """Initialize browser automation and HTTP session"""
        # Initialize parent SPA functionality (browser automation)
        await super().__aenter__()
        
        # Initialize HTTP session for fallback
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
        """Close HTTP session and browser"""
        if self.session:
            await self.session.close()
        
        # Close parent SPA resources
        await super().__aexit__(exc_type, exc_val, exc_tb)
    
    def get_framework_name(self) -> str:
        return "figma"
    
    async def discover_content(self) -> List[str]:
        """
        Discover Figma API documentation URLs.
        
        Note: Figma uses a React SPA for documentation, which limits our ability to
        extract content via traditional web scraping. We focus on known working URLs.
        """
        logger.info(f"🔍 Discovering Figma API documentation from {self.base_url}")
        logger.warning("⚠️  Figma uses a React SPA - content extraction may be limited")
        
        discovered_urls = set()
        
        # Method 1: Use simplified known working core URLs
        # These are more likely to have extractable content
        simplified_core_urls = [
            "",  # Base API docs
            "introduction/",
            "authentication/", 
            "rate-limiting/",
            "errors/",
            "files/",
            "webhooks/",
            "plugins/"
        ]
        
        for path in simplified_core_urls:
            full_url = urljoin(self.base_url, path)
            discovered_urls.add(full_url)
        
        # Method 2: Check for alternative documentation sources
        logger.info("🔍 Checking for alternative Figma documentation sources...")
        
        # Filter and clean URLs
        filtered_urls = []
        for url in discovered_urls:
            if self._should_include_url(url):
                filtered_urls.append(url)
        
        logger.info(f"📋 Found {len(filtered_urls)} Figma API documentation URLs")
        logger.info("💡 Note: Figma's SPA architecture limits traditional scraping")
        logger.info("💡 For comprehensive API docs, consider using Figma's REST API directly")
        
        # Log section breakdown
        section_counts = {}
        for url in filtered_urls:
            section = self._extract_section_from_url(url)
            section_counts[section] = section_counts.get(section, 0) + 1
        
        logger.info("📊 Section breakdown:")
        for section, count in sorted(section_counts.items()):
            logger.info(f"   {section}: {count} pages")
        
        return sorted(filtered_urls)
    
    async def _framework_specific_wait(self, page, url: str):
        """Figma-specific waiting logic for React SPA content"""
        try:
            # Wait for Figma's documentation-specific elements
            figma_selectors = [
                '[data-testid="documentation"]',
                '.docs-content',
                '.api-docs',
                '.documentation',
                '.content-wrapper',
                'main[role="main"]'
            ]
            
            for selector in figma_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=3000)
                    logger.debug(f"✅ Found Figma doc selector: {selector}")
                    return
                except:
                    continue
            
            # Wait for React to render content
            await page.wait_for_function(
                "document.body.innerText.length > 1000", 
                timeout=self.js_wait_timeout
            )
            
            # Additional wait for dynamic content loading
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.debug(f"⚠️  Figma-specific wait failed for {url}: {e}")
    
    async def _framework_specific_content_extraction(self, page, url: str) -> Optional[str]:
        """Figma-specific content extraction from rendered React SPA"""
        try:
            # Try Figma's specific content selectors
            figma_content_selectors = [
                'main[role="main"]',
                '.docs-content',
                '.api-docs .content',
                '.documentation-content',
                '[data-testid="documentation"]',
                '.content-wrapper'
            ]
            
            for selector in figma_content_selectors:
                try:
                    content = await page.text_content(selector)
                    if content and len(content.strip()) > 300:
                        logger.debug(f"✅ Extracted Figma content using: {selector}")
                        return content.strip()
                except:
                    continue
            
            # Advanced extraction: Remove known navigation/UI elements and get body content
            content = await page.evaluate("""
                () => {
                    // Remove common Figma navigation and UI elements
                    const elementsToRemove = document.querySelectorAll(`
                        nav, .navigation, .sidebar, header, footer, .breadcrumbs,
                        .cookie-banner, .newsletter-signup, script, style,
                        [data-testid="header"], [data-testid="footer"],
                        [data-testid="sidebar"], [data-testid="navigation"]
                    `);
                    elementsToRemove.forEach(el => el.remove());
                    
                    // Get main content from body
                    const body = document.body;
                    return body ? body.innerText : '';
                }
            """)
            
            if content and len(content.strip()) > 300:
                return content.strip()
                
            # Last resort: get any text content that mentions API-related terms
            content = await page.evaluate("""
                () => {
                    const text = document.body.innerText;
                    if (text.includes('API') || text.includes('endpoint') || text.includes('REST')) {
                        return text;
                    }
                    return '';
                }
            """)
            
            if content and len(content.strip()) > 200:
                return content.strip()
                
        except Exception as e:
            logger.debug(f"⚠️  Figma content extraction failed for {url}: {e}")
        
        return None
    
    async def _clean_title(self, title: str) -> str:
        """Clean Figma documentation titles"""
        # Remove Figma suffix variations
        if " | Figma for Developers" in title:
            title = title.split(" | Figma for Developers")[0].strip()
        elif " - Figma" in title:
            title = title.split(" - Figma")[0].strip()
        elif "Figma" == title:
            title = "Figma API Documentation"
        
        return title.strip()
    
    async def _create_metadata(self, url: str, title: str, content: str) -> DocumentMetadata:
        """Create Figma-specific metadata"""
        section = self._extract_section_from_url(url)
        doc_type = self._determine_doc_type(url, title, content)
        subsection = self._extract_subsection(url)
        tags = self._generate_tags(url, title, content)
        
        # Add browser-extracted tag
        tags.append("browser_extracted")
        
        return DocumentMetadata(
            framework="figma",
            source="Figma API Official Documentation",
            doc_type=doc_type,
            title=title,
            url=url,
            section=section,
            subsection=subsection,
            version=self.version,
            language="en",
            tags=tags
        )
    
    async def _discover_from_navigation(self) -> Set[str]:
        """Discover URLs by crawling navigation"""
        nav_urls = set()
        
        try:
            await asyncio.sleep(self.rate_limit_delay)
            
            async with self.session.get(self.base_url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Figma API navigation selectors
                    nav_selectors = [
                        'nav a[href]',
                        '.navigation a[href]',
                        '.sidebar a[href]',
                        '[data-testid="navigation"] a[href]',
                        '.docs-nav a[href]'
                    ]
                    
                    for selector in nav_selectors:
                        links = soup.select(selector)
                        for link in links:
                            href = link.get('href', '')
                            if href.startswith('/developers/api/'):
                                full_url = urljoin('https://www.figma.com', href)
                                nav_urls.add(full_url)
                            elif href.startswith('https://www.figma.com/developers/api/'):
                                nav_urls.add(href)
                    
                    logger.info(f"🧭 Found {len(nav_urls)} URLs from navigation")
                    
        except Exception as e:
            logger.warning(f"Could not crawl navigation: {e}")
        
        return nav_urls
    
    async def _discover_api_endpoints(self) -> Set[str]:
        """Discover API endpoint documentation URLs"""
        api_urls = set()
        
        # Common API endpoint patterns for Figma
        endpoint_patterns = [
            # File operations
            "files/{file_key}",
            "files/{file_key}/images",
            "files/{file_key}/nodes",
            "files/{file_key}/components",
            "files/{file_key}/styles",
            
            # Comments
            "files/{file_key}/comments",
            
            # Team operations  
            "teams/{team_id}/projects",
            "teams/{team_id}/components",
            "teams/{team_id}/styles",
            
            # Component operations
            "components/{component_key}",
            "component_sets/{component_set_key}",
            
            # Style operations
            "styles/{style_key}",
            
            # User operations
            "me",
            
            # Variables
            "files/{file_key}/variables/local",
            "files/{file_key}/variables/published",
        ]
        
        # Convert patterns to documentation URLs
        for pattern in endpoint_patterns:
            # Convert API endpoint pattern to docs URL
            docs_path = pattern.replace("{", "").replace("}", "").replace("_", "-")
            full_url = urljoin(self.base_url, docs_path + "/")
            api_urls.add(full_url)
        
        logger.info(f"🔌 Generated {len(api_urls)} API endpoint URLs")
        return api_urls
    
    def _should_include_url(self, url: str) -> bool:
        """Filter URLs based on relevance and quality"""
        # Skip unwanted patterns
        for pattern in self.skip_patterns:
            if pattern in url:
                return False
        
        # Only include API docs URLs
        if "/developers/api/" not in url:
            return False
        
        # Skip fragments and queries
        if '#' in url or '?' in url:
            return False
        
        return True
    
    def _extract_section_from_url(self, url: str) -> str:
        """Extract main section from URL for organization"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) >= 3 and path_parts[1] == "api":
            section = path_parts[2] if len(path_parts) > 2 else "introduction"
            
            # Group related sections
            if section in ["authentication", "rate-limiting", "errors", "versioning"]:
                return "getting_started"
            elif section.startswith("file") or section in ["nodes", "images"]:
                return "files_api"
            elif section in ["comments", "post", "delete"]:
                return "comments_api"
            elif section in ["users", "me", "teams", "team-projects"]:
                return "users_teams"
            elif section in ["components", "component-sets", "styles"]:
                return "design_system"
            elif section in ["variables", "variable-collections"]:
                return "design_tokens"
            elif section.startswith("dev") or "dev" in section:
                return "dev_mode"
            elif section in ["webhooks", "webhook-events"]:
                return "webhooks"
            elif section in ["plugins", "plugin-api"]:
                return "plugins"
            else:
                return section
        
        return "api_reference"
    
    async def extract_content_fallback(self, url: str) -> Optional[DocumentContent]:
        """
        Fallback content extraction using traditional HTTP + BeautifulSoup.
        This provides a fallback when browser automation is not available.
        """
        try:
            # Rate limiting
            await asyncio.sleep(self.rate_limit_delay)
            
            # Fetch page content using the parent's session
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
            title = await self._clean_title(title)
            
            # For SPAs, we likely won't get much content, so provide informative message
            content_text = "Content not available due to React SPA architecture. Please use browser mode for complete Figma API documentation."
            
            # Create basic metadata
            metadata = await self._create_metadata(url, title, content_text)
            metadata.tags.append("fallback_extraction")
            
            return DocumentContent(content=content_text, metadata=metadata)
            
        except Exception as e:
            logger.error(f"Error in fallback extraction for {url}: {e}")
            return None
    
    def _determine_doc_type(self, url: str, title: str, content: str) -> str:
        """Determine document type based on URL and content"""
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()[:500]
        
        if "introduction" in url_lower or "getting started" in title_lower:
            return "introduction"
        elif "authentication" in url_lower:
            return "authentication_guide"
        elif any(method in content_lower for method in ["get", "post", "put", "delete"]):
            return "api_endpoint"
        elif "webhook" in url_lower:
            return "webhook_reference"
        elif "plugin" in url_lower:
            return "plugin_reference"
        elif "error" in url_lower or "rate limit" in title_lower:
            return "error_reference"
        else:
            return "api_reference"
    
    def _extract_subsection(self, url: str) -> str:
        """Extract subsection from URL structure"""
        parsed = urlparse(url)
        path_parts = [p for p in parsed.path.split('/') if p]
        
        if len(path_parts) >= 3:
            return path_parts[-1] if path_parts[-1] else path_parts[-2]
        else:
            return "overview"
    
    def _generate_tags(self, url: str, title: str, content: str) -> List[str]:
        """Generate relevant tags for Figma content"""
        tags = ["api", "rest_api", "design_tools", "collaboration"]
        
        # Add endpoint-based tags
        content_lower = content.lower()[:1000]
        if any(method in content_lower for method in ["get ", "post ", "put ", "delete "]):
            tags.append("http_methods")
        
        # Add feature-based tags
        if any(term in url.lower() for term in ["file", "node"]):
            tags.append("file_operations")
        if "comment" in url.lower():
            tags.append("comments")
        if any(term in url.lower() for term in ["team", "user", "project"]):
            tags.append("workspace_management")
        if any(term in url.lower() for term in ["component", "style"]):
            tags.append("design_system")
        if "variable" in url.lower():
            tags.append("design_tokens")
        if "webhook" in url.lower():
            tags.append("webhooks")
        if "plugin" in url.lower():
            tags.append("plugins")
        if "dev-resource" in url.lower():
            tags.append("developer_handoff")
        
        # Add data format tags
        if "json" in content_lower:
            tags.append("json")
        if "authentication" in url.lower() or "auth" in content_lower:
            tags.append("authentication")
        if "rate limit" in content_lower:
            tags.append("rate_limiting")
        
        # Add integration tags
        if any(term in content_lower for term in ["react", "javascript", "typescript"]):
            tags.append("frontend_integration")
        if any(term in content_lower for term in ["node", "python", "curl"]):
            tags.append("backend_integration")
        
        # Add difficulty level
        if any(term in title.lower() for term in ["introduction", "getting started", "basics"]):
            tags.append("beginner")
        elif any(term in title.lower() for term in ["advanced", "webhook", "plugin"]):
            tags.append("advanced")
        else:
            tags.append("intermediate")
        
        return tags
    
    async def preprocess_content(self, content: str) -> str:
        """Clean Figma-specific content"""
        lines = content.split('\n')
        
        # Remove common Figma documentation navigation text
        skip_phrases = {
            "figma community", "contact support", "feature requests",
            "developer newsletter", "api changelog", "status page"
        }
        
        filtered_lines = []
        for line in lines:
            line = line.strip()
            if (len(line) > 15 and 
                not any(phrase in line.lower() for phrase in skip_phrases)):
                filtered_lines.append(line)
        
        return ' '.join(filtered_lines)
    
    async def postprocess_metadata(self, metadata: DocumentMetadata) -> DocumentMetadata:
        """Enhance Figma metadata"""
        # Add API version tags based on URL patterns
        url_lower = metadata.url.lower()
        title_lower = metadata.title.lower()
        
        if "v1" in url_lower or "version 1" in title_lower:
            metadata.tags.append("api_v1")
        
        # Add SDK tags if mentioned in URL or title
        if any(sdk in url_lower or sdk in title_lower for sdk in ["js", "api", "sdk"]):
            metadata.tags.append("sdk_integration")
        
        # Add platform tags based on URL patterns
        if any(platform in url_lower or platform in title_lower for platform in ["web", "desktop", "mobile"]):
            metadata.tags.append("cross_platform")
        
        # Add security tags based on URL patterns
        if any(term in url_lower or term in title_lower for term in ["oauth", "token", "security", "permission", "auth"]):
            metadata.tags.append("security")
        
        return metadata