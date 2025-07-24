#!/usr/bin/env python3
"""
Comprehensive extraction from structured figmaapi_structured.json file.

This script processes the clean, structured JSON file to extract all
Figma API documentation into ChromaDB.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from docs_ingestion.base import DocumentationIngester
from docs_ingestion.adapters.figma_json_docs import FigmaJsonDocsSource

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/figma_json_extraction.log", mode="w"),
    ],
)

logger = logging.getLogger(__name__)


async def main():
    """Run comprehensive Figma API JSON extraction"""

    # Path to the structured JSON file
    json_file_path = "/Users/aartemov/dev/resale-analyzer/figmaapi_structured.json"

    # Verify file exists
    if not Path(json_file_path).exists():
        logger.error(f"❌ Figma API JSON file not found: {json_file_path}")
        return False

    logger.info(
        "🚀 Starting comprehensive Figma API documentation extraction from JSON"
    )
    logger.info(f"📄 Source file: {json_file_path}")

    try:
        # Initialize the documentation ingester
        ingester = DocumentationIngester(collection_name="documentation_collection")

        # Create the Figma JSON source
        figma_source = FigmaJsonDocsSource(
            json_file_path=json_file_path, version="latest"
        )

        # Run the complete extraction
        stats = await ingester.ingest_from_source(figma_source)

        # Log comprehensive results
        logger.info("📊 COMPREHENSIVE EXTRACTION RESULTS:")
        logger.info(f"   🔍 Total sections discovered: {stats.total_discovered}")
        logger.info(f"   ✅ Successfully extracted: {stats.successful_ingestions}")
        logger.info(f"   ❌ Failed extractions: {stats.failed_ingestions}")
        logger.info(f"   ⏭️  Skipped (existing): {stats.skipped_existing}")
        logger.info(f"   📈 Success rate: {stats.success_rate:.1f}%")
        logger.info(f"   ⏱️  Total time: {stats.elapsed_time:.1f}s")

        # Get collection statistics
        collection_stats = ingester.get_collection_stats()
        logger.info("📚 CHROMADB COLLECTION STATS:")
        logger.info(f"   Total documents: {collection_stats.get('total_documents', 0)}")
        logger.info(f"   Framework breakdown: {collection_stats.get('frameworks', {})}")

        # Check for any failures
        if stats.failed_ingestions > 0:
            logger.warning(f"⚠️  {stats.failed_ingestions} sections failed to extract")
            for url, error in stats.failed_details.items():
                logger.warning(f"   Failed: {url} - {error}")

        # Success summary
        if stats.success_rate >= 95:
            logger.info("🎉 EXTRACTION COMPLETED SUCCESSFULLY!")
            logger.info("✅ Figma API documentation is now available in ChromaDB")

            # Test the extracted content
            logger.info("🧪 Testing extracted content...")
            await test_extracted_content(ingester)

            return True
        else:
            logger.warning("⚠️  Extraction completed with some issues")
            return False

    except Exception as e:
        logger.error(f"❌ Fatal error during extraction: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return False


async def test_extracted_content(ingester):
    """Test the extracted content by searching for key terms"""
    try:
        # Test search functionality (if available)
        collection = ingester.collection
        if collection:
            # Test query
            test_results = collection.query(
                query_texts=["How to authenticate with Figma API"], n_results=3
            )

            if test_results.get("documents"):
                logger.info(
                    f"✅ Search test successful - found {len(test_results['documents'][0])} relevant documents"
                )

                # Show a sample
                for i, doc in enumerate(test_results["documents"][0][:2]):
                    logger.info(f"   Sample {i+1}: {doc[:100]}...")
            else:
                logger.warning("⚠️  Search test returned no results")

    except Exception as e:
        logger.warning(f"⚠️  Could not test extracted content: {e}")


if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)

    # Run the extraction
    success = asyncio.run(main())

    if success:
        print("\n🎉 Figma API documentation extraction completed successfully!")
        print("📚 Content is now available through the docs-mcp server")
        print("🔍 You can now search for Figma API documentation using the MCP tools")
    else:
        print("\n❌ Extraction failed or completed with issues")
        print("📋 Check logs/figma_json_extraction.log for details")
        sys.exit(1)
