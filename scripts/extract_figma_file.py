#!/usr/bin/env python3
"""
One-time comprehensive extraction from figmaapi.txt file.

This script processes the local Figma API documentation file and extracts
all content into ChromaDB for the docs-mcp server.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from docs_ingestion.base import DocumentationIngester
from docs_ingestion.adapters.figma_file_docs import FigmaFileDocsSource

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/figma_file_extraction.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Run comprehensive Figma API file extraction"""
    
    # Path to the figmaapi.txt file
    figma_file_path = "/Users/aartemov/dev/resale-analyzer/figmaapi.txt"
    
    # Verify file exists
    if not Path(figma_file_path).exists():
        logger.error(f"❌ Figma API file not found: {figma_file_path}")
        return False
    
    logger.info("🚀 Starting comprehensive Figma API documentation extraction")
    logger.info(f"📄 Source file: {figma_file_path}")
    
    try:
        # Initialize the documentation ingester
        ingester = DocumentationIngester(collection_name="documentation_collection")
        
        # Create the Figma file source
        figma_source = FigmaFileDocsSource(file_path=figma_file_path, version="latest")
        
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
            return True
        else:
            logger.warning("⚠️  Extraction completed with some issues")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fatal error during extraction: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Run the extraction
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 Figma API documentation extraction completed successfully!")
        print("📚 Content is now available through the docs-mcp server")
    else:
        print("\n❌ Extraction failed or completed with issues")
        print("📋 Check logs/figma_file_extraction.log for details")
        sys.exit(1)