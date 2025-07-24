"""
Base SPA Documentation Adapter with Browser Automation.

Provides enhanced content extraction for Single Page Applications (SPAs) 
that require JavaScript rendering to display documentation content.
"""

import asyncio
import logging
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod
from urllib.parse import urljoin, urlparse
import contextlib

from .base import BaseDocumentationSource, DocumentContent, DocumentMetadata

logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("Playwright not available. SPA adapters will have limited functionality.")


class SPADocumentationSource(BaseDocumentationSource, ABC):
    """
    Base class for SPA documentation sources that require browser automation.
    
    Provides both fallback HTML parsing and enhanced browser rendering modes.
    """
    
    def __init__(self, name: str, base_url: str, use_browser: bool = True):
        super().__init__(name, base_url)
        self.use_browser = use_browser and PLAYWRIGHT_AVAILABLE
        
        # Browser configuration
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.browser_options = {
            'headless': True,
            'args': [
                '--no-sandbox',
                '--disable-setuid-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        }
        
        # SPA-specific configuration
        self.js_wait_timeout = 10000  # 10 seconds
        self.network_idle_timeout = 2000  # 2 seconds
        self.content_wait_selectors = [
            'main', '[role="main"]', '.documentation', '.content',
            '.docs-content', '.api-docs', 'article'
        ]
        
        if not self.use_browser:
            logger.warning(f"🌐 {name}: Browser automation disabled - using fallback HTML parsing only")
        else:
            logger.info(f"🚀 {name}: Browser automation enabled for complete SPA support")
    
    async def __aenter__(self):
        """Initialize browser and HTTP session"""
        # No parent __aenter__ to call for BaseDocumentationSource
        
        # Initialize browser if enabled
        if self.use_browser and PLAYWRIGHT_AVAILABLE:
            try:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(**self.browser_options)
                self.context = await self.browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                logger.info("🌐 Browser context initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize browser: {e}")
                self.use_browser = False
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Clean up browser and HTTP session"""
        # Clean up browser resources
        if self.browser:
            try:
                await self.context.close()
                await self.browser.close()
                await self.playwright.stop()
                logger.info("🌐 Browser resources cleaned up")
            except Exception as e:
                logger.warning(f"⚠️  Error cleaning up browser: {e}")
        
        # No parent __aexit__ to call for BaseDocumentationSource
    
    async def extract_content_with_browser(self, url: str) -> Optional[DocumentContent]:
        """
        Extract content using browser automation for JavaScript-rendered content.
        """
        if not self.use_browser or not self.browser:
            logger.warning(f"Browser not available for {url}, falling back to HTML parsing")
            return await self.extract_content_fallback(url)
        
        page = None
        try:
            page = await self.context.new_page()
            
            # Set up enhanced request/response monitoring
            page.on('response', lambda response: 
                logger.debug(f"🌐 {response.status} {response.url}") if response.status >= 400 else None)
            
            # Anti-bot detection: Set more realistic headers and behavior
            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # Navigate with multiple timeout strategies
            logger.info(f"🌐 Loading page with browser: {url}")
            
            # Strategy 1: Quick load with shorter timeout
            try:
                response = await page.goto(url, wait_until='domcontentloaded', timeout=10000)
            except Exception as e:
                logger.warning(f"⚠️  Quick load failed, trying fallback load: {e}")
                
                # Strategy 2: Fallback with no wait condition
                try:
                    response = await page.goto(url, wait_until='commit', timeout=8000)
                except Exception as e2:
                    logger.error(f"❌ Both load strategies failed: {e2}")
                    return await self.extract_content_fallback(url)
            
            if not response:
                logger.warning(f"❌ No response received for {url}")
                return await self.extract_content_fallback(url)
                
            if response.status >= 400:
                logger.warning(f"❌ HTTP error {response.status} for {url}")
                return await self.extract_content_fallback(url)
            
            # Wait for JavaScript content to load with timeout protection
            try:
                await asyncio.wait_for(
                    self._wait_for_spa_content(page, url), 
                    timeout=12.0  # Overall timeout for SPA content loading
                )
            except asyncio.TimeoutError:
                logger.warning(f"⚠️  SPA content loading timeout for {url}, proceeding with available content")
            
            # Extract title with timeout protection
            try:
                title = await asyncio.wait_for(page.title(), timeout=3.0)
                title = await self._clean_title(title)
            except asyncio.TimeoutError:
                logger.warning(f"⚠️  Title extraction timeout for {url}")
                title = "Documentation Page"
            
            # Extract main content using selectors with timeout protection
            try:
                content_text = await asyncio.wait_for(
                    self._extract_main_content(page, url), 
                    timeout=8.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"⚠️  Content extraction timeout for {url}")
                content_text = ""
            
            if not content_text or len(content_text.strip()) < 100:
                logger.warning(f"⚠️  Insufficient content extracted from {url} ({len(content_text) if content_text else 0} chars)")
                return await self.extract_content_fallback(url)
            
            # Create metadata
            metadata = await self._create_metadata(url, title, content_text)
            
            logger.info(f"✅ Successfully extracted {len(content_text)} chars from {url}")
            return DocumentContent(content=content_text, metadata=metadata)
            
        except Exception as e:
            logger.error(f"❌ Browser extraction failed for {url}: {e}")
            return await self.extract_content_fallback(url)
        
        finally:
            if page:
                try:
                    await asyncio.wait_for(page.close(), timeout=2.0)
                except asyncio.TimeoutError:
                    logger.warning(f"⚠️  Page close timeout for {url}")
                except Exception as e:
                    logger.debug(f"Page close error: {e}")
    
    async def _wait_for_spa_content(self, page: Page, url: str):
        """Wait for SPA content to load"""
        try:
            logger.debug(f"⏳ Waiting for SPA content to load: {url}")
            
            # Method 1: Wait for network to be idle
            await page.wait_for_load_state('networkidle', timeout=self.network_idle_timeout)
            
            # Method 2: Wait for main content selectors to appear
            for selector in self.content_wait_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=2000)
                    logger.debug(f"✅ Found content selector: {selector}")
                    break
                except:
                    continue
            
            # Method 3: Additional wait for SPA frameworks
            await asyncio.sleep(1)  # Give React/Vue time to render
            
            # Method 4: Framework-specific waits
            await self._framework_specific_wait(page, url)
            
        except Exception as e:
            logger.debug(f"⚠️  SPA wait timeout for {url}: {e}")
    
    async def _framework_specific_wait(self, page: Page, url: str):
        """Override in subclasses for framework-specific waiting logic"""
        pass
    
    async def _extract_main_content(self, page: Page, url: str) -> str:
        """Extract main content from the rendered page"""
        content_text = ""
        
        # Try different content extraction strategies
        strategies = [
            # Strategy 1: Main content areas
            lambda: page.text_content('main'),
            lambda: page.text_content('[role="main"]'),
            lambda: page.text_content('article'),
            
            # Strategy 2: Documentation-specific areas  
            lambda: page.text_content('.documentation'),
            lambda: page.text_content('.docs-content'),
            lambda: page.text_content('.api-docs'),
            lambda: page.text_content('.content'),
            
            # Strategy 3: Framework-specific extraction
            lambda: self._framework_specific_content_extraction(page, url),
        ]
        
        for strategy in strategies:
            try:
                result = await strategy()
                if result and len(result.strip()) > 100:
                    content_text = result.strip()
                    break
            except Exception as e:
                logger.debug(f"🔍 Content extraction strategy failed: {e}")
                continue
        
        # Clean up the extracted content
        if content_text:
            content_text = await self._clean_extracted_content(content_text, url)
        
        return content_text
    
    async def _framework_specific_content_extraction(self, page: Page, url: str) -> Optional[str]:
        """Override in subclasses for framework-specific content extraction"""
        return None
    
    async def _clean_extracted_content(self, content: str, url: str) -> str:
        """Clean up extracted content"""
        # Normalize whitespace
        content = ' '.join(content.split())
        
        # Remove common navigation/footer text
        common_removals = [
            'Skip to main content',
            'Toggle navigation',
            'Search documentation',
            'Edit this page',
            'Report an issue',
            'Cookie Settings',
            'Privacy Policy'
        ]
        
        for removal in common_removals:
            content = content.replace(removal, '')
        
        return content.strip()
    
    async def _clean_title(self, title: str) -> str:
        """Clean page title - override in subclasses"""
        return title.strip()
    
    @abstractmethod 
    async def _create_metadata(self, url: str, title: str, content: str) -> DocumentMetadata:
        """Create document metadata - must be implemented by subclasses"""
        pass
    
    async def extract_content_fallback(self, url: str) -> Optional[DocumentContent]:
        """
        Fallback content extraction using traditional HTTP + BeautifulSoup.
        Override this in subclasses to customize fallback behavior.
        """
        logger.info(f"🔄 Using fallback extraction for {url}")
        
        # Use the parent class's extract_content method as fallback
        return await super().extract_content(url)
    
    async def extract_content(self, url: str) -> Optional[DocumentContent]:
        """
        Main content extraction method that tries browser first, then fallback.
        """
        if self.use_browser:
            result = await self.extract_content_with_browser(url)
            if result and len(result.content.strip()) > 100:
                return result
        
        # Fallback to traditional extraction
        return await self.extract_content_fallback(url)
    
    def is_browser_enabled(self) -> bool:
        """Check if browser automation is available and enabled"""
        return self.use_browser and PLAYWRIGHT_AVAILABLE and self.browser is not None