#!/usr/bin/env python3
"""
Quick test for Figma timeout fixes
"""

import asyncio
import logging
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.error("Playwright not available")
    sys.exit(1)

async def test_figma_timeout():
    """Test Figma with the new timeout handling"""
    logger.info("🚀 Testing Figma with improved timeout handling...")
    
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("❌ Playwright not available")
        return False
    
    playwright = None
    browser = None
    context = None
    page = None
    
    try:
        # Initialize browser
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox', 
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=VizDisplayCompositor'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        
        # Test URL
        test_url = "https://www.figma.com/developers/api/"
        logger.info(f"🌐 Loading page: {test_url}")
        
        # Enhanced headers to avoid bot detection
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
        
        # Multiple timeout strategies
        response = None
        
        # Strategy 1: Quick load
        try:
            logger.info("🔄 Trying quick load strategy...")
            response = await asyncio.wait_for(
                page.goto(test_url, wait_until='domcontentloaded'),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            logger.warning("⚠️  Quick load timeout, trying fallback...")
            
            # Strategy 2: Fallback with minimal wait
            try:
                response = await asyncio.wait_for(
                    page.goto(test_url, wait_until='commit'),
                    timeout=8.0
                )
            except asyncio.TimeoutError:
                logger.error("❌ Both load strategies timed out")
                return False
        
        if not response:
            logger.error("❌ No response received")
            return False
            
        logger.info(f"✅ Page loaded with status: {response.status}")
        
        # Wait for content with timeout
        try:
            await asyncio.wait_for(
                page.wait_for_function("document.body.innerText.length > 500", timeout=5000),
                timeout=6.0
            )
            logger.info("✅ Content loaded successfully")
        except asyncio.TimeoutError:
            logger.warning("⚠️  Content load timeout, proceeding anyway")
        
        # Extract content with timeout
        try:
            content = await asyncio.wait_for(
                page.text_content('body'),
                timeout=3.0
            )
            
            if content:
                logger.info(f"✅ Extracted {len(content)} characters")
                if len(content) > 1000:
                    logger.info(f"📝 Content preview: {content[:200]}...")
                    return True
                else:
                    logger.warning(f"⚠️  Content too short: {len(content)} chars")
                    return False
            else:
                logger.error("❌ No content extracted")
                return False
                
        except asyncio.TimeoutError:
            logger.error("❌ Content extraction timeout")
            return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return False
        
    finally:
        # Cleanup with timeouts
        if page:
            try:
                await asyncio.wait_for(page.close(), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("⚠️  Page close timeout")
        
        if context:
            try:
                await asyncio.wait_for(context.close(), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("⚠️  Context close timeout")
        
        if browser:
            try:
                await asyncio.wait_for(browser.close(), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("⚠️  Browser close timeout")
        
        if playwright:
            try:
                await asyncio.wait_for(playwright.stop(), timeout=2.0)
            except asyncio.TimeoutError:
                logger.warning("⚠️  Playwright stop timeout")

async def main():
    """Run the test"""
    logger.info("🎯 Starting Figma timeout test...")
    
    success = await test_figma_timeout()
    
    if success:
        logger.info("🎉 Test passed! Figma timeout handling improved.")
        return 0
    else:
        logger.error("❌ Test failed.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)