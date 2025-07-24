#!/usr/bin/env python3
"""
Comprehensive extraction from MDN CSS documentation.

This script processes the official Mozilla Developer Network CSS documentation
to extract all CSS properties, selectors, concepts, and guides into ChromaDB.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from docs_ingestion.base import DocumentationIngester
from docs_ingestion.adapters.mdn_css_docs import MDNCSSDocsSource

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/mdn_css_extraction.log', mode='w')
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Run comprehensive MDN CSS documentation extraction"""
    
    logger.info("🚀 Starting comprehensive MDN CSS documentation extraction")
    logger.info("📄 Source: https://developer.mozilla.org/en-US/docs/Web/CSS/")
    
    try:
        # Initialize the documentation ingester
        ingester = DocumentationIngester(collection_name="documentation_collection")
        
        # Create the MDN CSS source with async context manager
        async with MDNCSSDocsSource(version="latest") as mdn_css_source:
            # Run the complete extraction
            stats = await ingester.ingest_from_source(mdn_css_source)
        
        # Log comprehensive results
        logger.info("📊 COMPREHENSIVE EXTRACTION RESULTS:")
        logger.info(f"   🔍 Total pages discovered: {stats.total_discovered}")
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
        
        # Count CSS specific documents
        css_count = collection_stats.get('frameworks', {}).get('css', 0)
        logger.info(f"   🎨 CSS docs: {css_count}")
        
        # Check for any failures
        if stats.failed_ingestions > 0:
            logger.warning(f"⚠️  {stats.failed_ingestions} pages failed to extract")
            for url, error in stats.failed_details.items():
                logger.warning(f"   Failed: {url} - {error}")
        
        # Success summary
        if stats.success_rate >= 85:
            logger.info("🎉 EXTRACTION COMPLETED SUCCESSFULLY!")
            logger.info("✅ MDN CSS documentation is now available in ChromaDB")
            
            # Test the extracted content
            logger.info("🧪 Testing extracted content...")
            await test_extracted_content(ingester)
            
            return True
        elif stats.success_rate >= 70:
            logger.warning("⚠️  Extraction completed with some issues")
            return True
        else:
            logger.error("❌ Extraction failed - low success rate")
            return False
            
    except Exception as e:
        logger.error(f"❌ Fatal error during extraction: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def test_extracted_content(ingester):
    """Test the extracted content by searching for key CSS terms"""
    try:
        collection = ingester.collection
        if collection:
            # Test queries for CSS development
            test_queries = [
                "CSS flexbox layout properties",
                "CSS grid layout guide", 
                "CSS selectors pseudo-classes",
                "CSS animations transitions",
                "CSS box model properties",
                "CSS color values functions",
                "CSS responsive design media queries"
            ]
            
            for query in test_queries:
                test_results = collection.query(
                    query_texts=[query],
                    where={"framework": "css"},
                    n_results=3
                )
                
                if test_results.get('documents') and test_results['documents'][0]:
                    logger.info(f"✅ Search test '{query}' - found {len(test_results['documents'][0])} relevant documents")
                    
                    # Show a sample
                    for i, doc in enumerate(test_results['documents'][0][:2]):
                        sample = doc[:150].replace('\n', ' ')
                        logger.info(f"   Sample {i+1}: {sample}...")
                else:
                    logger.warning(f"⚠️  Search test '{query}' returned no results")
                
                await asyncio.sleep(0.1)  # Brief pause between tests
        
    except Exception as e:
        logger.warning(f"⚠️  Could not test extracted content: {e}")

if __name__ == "__main__":
    # Ensure logs directory exists
    Path("logs").mkdir(exist_ok=True)
    
    # Run the extraction
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 MDN CSS documentation extraction completed successfully!")
        print("📚 Content is now available through the docs-mcp server")
        print("🔍 You can now search for CSS documentation using:")
        print("   - search_fastapi_docs('css flexbox properties')")
        print("   - search_python_docs('css grid layout')")
        print("   - Or use the specific css framework searches")
        print("\n📖 Coverage includes:")
        print("   • All CSS properties and values")
        print("   • CSS selectors and pseudo-classes")
        print("   • Layout systems (Flexbox, Grid, etc.)")
        print("   • Animations and transitions")
        print("   • Responsive design concepts")
        print("   • CSS guides and tutorials")
    else:
        print("\n❌ Extraction failed or completed with issues")
        print("📋 Check logs/mdn_css_extraction.log for details")
        sys.exit(1)