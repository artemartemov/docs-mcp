#!/usr/bin/env python3
"""
Debug script to see what's actually happening with Figma pages
"""

import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.error("Playwright not available")
    exit(1)

async def debug_figma_page():
    """Debug what's happening with Figma documentation pages"""
    
    if not PLAYWRIGHT_AVAILABLE:
        logger.error("Playwright not available")
        return
    
    playwright = None
    browser = None
    context = None
    page = None
    
    try:
        # Initialize browser
        logger.info("Starting browser...")
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
        
        # Test URLs
        test_urls = [
            "https://www.figma.com/developers/",
            "https://www.figma.com/developers/api/"
        ]
        
        for url in test_urls:
            logger.info(f"🌐 Testing URL: {url}")
            
            try:
                # Navigate to page
                response = await page.goto(url, wait_until='networkidle', timeout=30000)
                logger.info(f"✅ Page loaded with status: {response.status}")
                
                # Wait for content to load
                await asyncio.sleep(5)
                
                # Get page info
                page_info = await page.evaluate("""
                    () => {
                        return {
                            title: document.title,
                            url: window.location.href,
                            bodyTextLength: document.body.innerText?.length || 0,
                            bodyHTML: document.body.innerHTML.length,
                            hasMain: !!document.querySelector('main'),
                            hasArticle: !!document.querySelector('article'),
                            hasContent: !!document.querySelector('.content, .docs, .documentation'),
                            allText: (document.body.innerText || '').substring(0, 500)
                        };
                    }
                """)
                
                logger.info(f"📄 Page Info:")
                logger.info(f"   Title: {page_info['title']}")
                logger.info(f"   URL: {page_info['url']}")
                logger.info(f"   Body text length: {page_info['bodyTextLength']}")
                logger.info(f"   Body HTML length: {page_info['bodyHTML']}")
                logger.info(f"   Has main: {page_info['hasMain']}")
                logger.info(f"   Has article: {page_info['hasArticle']}")
                logger.info(f"   Has content divs: {page_info['hasContent']}")
                logger.info(f"   Text preview: {page_info['allText'][:200]}...")
                
                # Take screenshot for debugging
                screenshot_path = f"debug_figma_{url.replace('https://', '').replace('/', '_')}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                logger.info(f"📸 Screenshot saved: {screenshot_path}")
                
                # Try to extract content with different methods
                methods = [
                    ("main", "document.querySelector('main')?.innerText"),
                    ("body", "document.body.innerText"),
                    ("all_divs", "[...document.querySelectorAll('div')].map(d => d.innerText).join(' ')"),
                    ("visible_text", "[...document.querySelectorAll('*')].filter(el => el.offsetParent !== null && el.innerText).map(el => el.innerText).join(' ')")
                ]
                
                for method_name, js_code in methods:
                    try:
                        content = await page.evaluate(f"() => {js_code}")
                        if content:
                            logger.info(f"   {method_name}: {len(content)} chars")
                            if len(content) > 100:
                                logger.info(f"   {method_name} preview: {content[:150]}...")
                        else:
                            logger.info(f"   {method_name}: No content")
                    except Exception as e:
                        logger.warning(f"   {method_name}: Error - {e}")
                
                logger.info("-" * 60)
                
            except Exception as e:
                logger.error(f"❌ Failed to process {url}: {e}")
        
    except Exception as e:
        logger.error(f"❌ Debug failed: {e}")
        
    finally:
        # Cleanup
        if page:
            try:
                await page.close()
            except:
                pass
        
        if context:
            try:
                await context.close()
            except:
                pass
        
        if browser:
            try:
                await browser.close()
            except:
                pass
        
        if playwright:
            try:
                await playwright.stop()
            except:
                pass

if __name__ == "__main__":
    asyncio.run(debug_figma_page())