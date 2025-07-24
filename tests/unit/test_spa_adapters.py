#!/usr/bin/env python3
"""
Test script for SPA-enhanced documentation adapters.

Tests both SwiftUI and Figma adapters with browser automation capabilities.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from docs_ingestion.adapters.swiftui_docs import SwiftUIDocsSource
from docs_ingestion.adapters.figma_docs import FigmaDocsSource

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_swiftui_spa():
    """Test SwiftUI adapter with browser automation"""
    logger.info("🍎 Testing SwiftUI adapter with browser automation...")

    try:
        # Test with browser automation enabled
        async with SwiftUIDocsSource(use_browser=True) as source:
            if not source.is_browser_enabled():
                logger.warning(
                    "⚠️  Browser automation not available, testing fallback mode"
                )

            # Test URL discovery
            urls = await source.discover_content()
            logger.info(f"📋 SwiftUI URLs discovered: {len(urls)}")

            # Test content extraction with a few URLs
            test_urls = urls[:3] if urls else []

            for i, url in enumerate(test_urls):
                logger.info(f"\n🔍 Testing SwiftUI URL {i+1}: {url}")

                content = await source.extract_content(url)
                if content:
                    logger.info(f"  ✅ Content extracted successfully")
                    logger.info(f"  📄 Title: {content.metadata.title}")
                    logger.info(f"  📊 Content length: {len(content.content)} chars")
                    logger.info(f"  🏷️  Tags: {content.metadata.tags}")
                    logger.info(f"  📝 Content preview: {content.content[:200]}...")

                    # Check if browser was used
                    if "browser_extracted" in content.metadata.tags:
                        logger.info("  🌐 Content extracted using browser automation")
                    elif "fallback_extraction" in content.metadata.tags:
                        logger.info("  🔄 Content extracted using fallback method")
                else:
                    logger.warning(f"  ❌ Failed to extract content")

        return True

    except Exception as e:
        logger.error(f"❌ SwiftUI test failed: {e}")
        return False


async def test_figma_spa():
    """Test Figma adapter with browser automation"""
    logger.info("🎨 Testing Figma adapter with browser automation...")

    try:
        # Test with browser automation enabled
        async with FigmaDocsSource(use_browser=True) as source:
            if not source.is_browser_enabled():
                logger.warning(
                    "⚠️  Browser automation not available, testing fallback mode"
                )

            # Test URL discovery
            urls = await source.discover_content()
            logger.info(f"📋 Figma URLs discovered: {len(urls)}")

            # Test content extraction with a few URLs
            test_urls = urls[:3] if urls else []

            for i, url in enumerate(test_urls):
                logger.info(f"\n🔍 Testing Figma URL {i+1}: {url}")

                content = await source.extract_content(url)
                if content:
                    logger.info(f"  ✅ Content extracted successfully")
                    logger.info(f"  📄 Title: {content.metadata.title}")
                    logger.info(f"  📊 Content length: {len(content.content)} chars")
                    logger.info(f"  🏷️  Tags: {content.metadata.tags}")
                    logger.info(f"  📝 Content preview: {content.content[:200]}...")

                    # Check if browser was used
                    if "browser_extracted" in content.metadata.tags:
                        logger.info("  🌐 Content extracted using browser automation")
                    elif "fallback_extraction" in content.metadata.tags:
                        logger.info("  🔄 Content extracted using fallback method")
                else:
                    logger.warning(f"  ❌ Failed to extract content")

        return True

    except Exception as e:
        logger.error(f"❌ Figma test failed: {e}")
        return False


async def test_comparison():
    """Compare browser vs fallback extraction"""
    logger.info("🔍 Testing browser vs fallback extraction comparison...")

    test_url = "https://developer.apple.com/documentation/swiftui/text"

    try:
        # Test with browser automation
        logger.info("Testing with browser automation...")
        async with SwiftUIDocsSource(use_browser=True) as browser_source:
            browser_content = await browser_source.extract_content(test_url)

        # Test with fallback only
        logger.info("Testing with fallback extraction...")
        async with SwiftUIDocsSource(use_browser=False) as fallback_source:
            fallback_content = await fallback_source.extract_content(test_url)

        # Compare results
        if browser_content and fallback_content:
            logger.info("\n📊 COMPARISON RESULTS:")
            logger.info(f"Browser content length: {len(browser_content.content)} chars")
            logger.info(
                f"Fallback content length: {len(fallback_content.content)} chars"
            )

            browser_tags = set(browser_content.metadata.tags)
            fallback_tags = set(fallback_content.metadata.tags)

            logger.info(f"Browser-specific tags: {browser_tags - fallback_tags}")
            logger.info(f"Fallback-specific tags: {fallback_tags - browser_tags}")

        return True

    except Exception as e:
        logger.error(f"❌ Comparison test failed: {e}")
        return False


async def main():
    """Run all SPA adapter tests"""
    logger.info("🚀 Starting SPA adapter tests...")
    logger.info("=" * 60)

    results = []

    # Test individual adapters
    results.append(await test_swiftui_spa())
    logger.info("=" * 60)

    results.append(await test_figma_spa())
    logger.info("=" * 60)

    # Test comparison
    results.append(await test_comparison())
    logger.info("=" * 60)

    # Summary
    passed = sum(results)
    total = len(results)

    logger.info(f"🎯 TEST SUMMARY:")
    logger.info(f"   Passed: {passed}/{total}")
    logger.info(f"   Success rate: {(passed/total)*100:.1f}%")

    if passed == total:
        logger.info("🎉 All SPA adapter tests passed!")
        return 0
    else:
        logger.warning("⚠️  Some tests failed. Check logs above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
