#!/usr/bin/env python3
"""
Main documentation ingestion script for ResaleAnalyzer MCP Server.

This script orchestrates the ingestion of documentation from various sources
into ChromaDB using the reusable ingestion framework. Supports multiple
documentation sources with comprehensive progress tracking and error handling.
"""

import asyncio
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any
import json

from docs_ingestion import DocumentationIngester
from docs_ingestion.adapters import PythonDocsSource, FastAPIDocsSource, ReactDocsSource
from config import get_settings, create_log_directory

# Configure logging
create_log_directory()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/documentation_ingestion.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

settings = get_settings()

class IngestionConfig:
    """Configuration for documentation ingestion sources"""
    
    AVAILABLE_SOURCES = {
        "python": {
            "name": "Python Official Documentation",
            "description": "Python 3 official documentation using Sphinx inventory",
            "class": PythonDocsSource,
            "versions": ["3", "3.12", "3.11"],
            "default_version": "3"
        },
        "fastapi": {
            "name": "FastAPI Official Documentation",
            "description": "FastAPI official documentation with tutorials and advanced guides",
            "class": FastAPIDocsSource,
            "versions": ["latest"],
            "default_version": "latest"
        },
        "react": {
            "name": "React.js Official Documentation",
            "description": "React.js official documentation from react.dev",
            "class": ReactDocsSource,
            "versions": ["latest"],
            "default_version": "latest"
        }
        # Future sources to add:
        # "django": {...},
        # "flask": {...},
        # "vue": {...},
        # "typescript": {...},
        # "swift": {...}
    }
    
    @classmethod
    def get_source_info(cls, source_name: str) -> Dict[str, Any]:
        """Get information about a specific source"""
        return cls.AVAILABLE_SOURCES.get(source_name, {})
    
    @classmethod
    def list_available_sources(cls) -> List[str]:
        """List all available documentation sources"""
        return list(cls.AVAILABLE_SOURCES.keys())

async def ingest_python_docs(version: str = "3", test_mode: bool = False) -> Dict[str, Any]:
    """Ingest Python documentation for a specific version"""
    logger.info(f"🐍 Starting Python {version} documentation ingestion...")
    
    ingester = DocumentationIngester()
    
    async with PythonDocsSource(version=version) as source:
        # Test mode: limit to small subset
        if test_mode:
            logger.warning("🧪 Running in TEST MODE - limited content")
            source.batch_size = 5
            # Override discover_content to return only a few URLs for testing
            original_discover = source.discover_content
            async def test_discover():
                all_urls = await original_discover()
                return all_urls[:10]  # Only first 10 URLs
            source.discover_content = test_discover
        
        stats = await ingester.ingest_from_source(source)
    
    # Get final collection statistics
    collection_stats = ingester.get_collection_stats()
    
    result = {
        "source": f"python_{version}",
        "ingestion_stats": {
            "total_discovered": stats.total_discovered,
            "total_processed": stats.total_processed,
            "successful_ingestions": stats.successful_ingestions,
            "failed_ingestions": stats.failed_ingestions,
            "skipped_existing": stats.skipped_existing,
            "success_rate": stats.success_rate,
            "elapsed_time": stats.elapsed_time,
            "errors_count": len(stats.errors)
        },
        "collection_stats": collection_stats
    }
    
    logger.info(f"✅ Python {version} ingestion completed!")
    return result

async def ingest_generic_docs(source_class, source_name: str, version: str = "latest", test_mode: bool = False) -> Dict[str, Any]:
    """Generic ingestion function for any documentation source"""
    logger.info(f"📚 Starting {source_name} {version} documentation ingestion...")
    
    ingester = DocumentationIngester()
    
    async with source_class(version=version) as source:
        # Test mode: limit to small subset
        if test_mode:
            logger.warning("🧪 Running in TEST MODE - limited content")
            source.batch_size = 5
            # Override discover_content to return only a few URLs for testing
            original_discover = source.discover_content
            async def test_discover():
                all_urls = await original_discover()
                return all_urls[:10]  # Only first 10 URLs
            source.discover_content = test_discover
        
        stats = await ingester.ingest_from_source(source)
    
    # Get final collection statistics
    collection_stats = ingester.get_collection_stats()
    
    result = {
        "source": f"{source_name}_{version}",
        "ingestion_stats": {
            "total_discovered": stats.total_discovered,
            "total_processed": stats.total_processed,
            "successful_ingestions": stats.successful_ingestions,
            "failed_ingestions": stats.failed_ingestions,
            "skipped_existing": stats.skipped_existing,
            "success_rate": stats.success_rate,
            "elapsed_time": stats.elapsed_time,
            "errors_count": len(stats.errors)
        },
        "collection_stats": collection_stats
    }
    
    logger.info(f"✅ {source_name} {version} ingestion completed!")
    return result

async def ingest_multiple_sources(sources: List[str], test_mode: bool = False) -> Dict[str, Any]:
    """Ingest documentation from multiple sources"""
    logger.info(f"🚀 Starting multi-source ingestion: {', '.join(sources)}")
    
    results = {}
    
    for source_name in sources:
        try:
            if source_name == "python":
                config = IngestionConfig.get_source_info("python")
                version = config.get("default_version", "3")
                result = await ingest_python_docs(version=version, test_mode=test_mode)
                results[source_name] = result
            elif source_name == "fastapi":
                config = IngestionConfig.get_source_info("fastapi")
                version = config.get("default_version", "latest")
                result = await ingest_generic_docs(FastAPIDocsSource, source_name, version, test_mode)
                results[source_name] = result
            elif source_name == "react":
                config = IngestionConfig.get_source_info("react")
                version = config.get("default_version", "latest")
                result = await ingest_generic_docs(ReactDocsSource, source_name, version, test_mode)
                results[source_name] = result
            else:
                logger.warning(f"⚠️  Source '{source_name}' not yet implemented")
                results[source_name] = {"error": "Not yet implemented"}
                
        except Exception as e:
            logger.error(f"❌ Failed to ingest {source_name}: {e}")
            results[source_name] = {"error": str(e)}
    
    return results

def save_ingestion_report(results: Dict[str, Any], output_file: str = None):
    """Save detailed ingestion report to file"""
    if not output_file:
        from datetime import datetime
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        output_file = f"logs/ingestion_report_{timestamp}.json"
    
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"📊 Ingestion report saved to: {output_path}")

def print_summary(results: Dict[str, Any]):
    """Print a comprehensive summary of ingestion results"""
    logger.info("="* 60)
    logger.info("📊 INGESTION SUMMARY")
    logger.info("="* 60)
    
    total_discovered = 0
    total_successful = 0
    total_failed = 0
    
    for source_name, result in results.items():
        if "ingestion_stats" in result:
            stats = result["ingestion_stats"]
            total_discovered += stats["total_discovered"]
            total_successful += stats["successful_ingestions"]
            total_failed += stats["failed_ingestions"]
            
            logger.info(f"""
📚 {source_name.upper()}:
   Discovered: {stats['total_discovered']}
   Successful: {stats['successful_ingestions']} ({stats['success_rate']:.1f}%)
   Failed: {stats['failed_ingestions']}
   Time: {stats['elapsed_time']:.1f}s
""")
    
    overall_success_rate = (total_successful / max(1, total_discovered)) * 100
    
    logger.info(f"""
🎯 OVERALL TOTALS:
   Total Discovered: {total_discovered}
   Total Successful: {total_successful} ({overall_success_rate:.1f}%)
   Total Failed: {total_failed}
""")
    
    # Collection statistics
    for source_name, result in results.items():
        if "collection_stats" in result:
            stats = result["collection_stats"]
            if "total_documents" in stats:
                logger.info(f"📚 ChromaDB Collection: {stats['total_documents']} total documents")
                if "frameworks" in stats:
                    logger.info("Framework breakdown:")
                    for fw, count in stats["frameworks"].items():
                        logger.info(f"   {fw}: {count}")
                break

async def check_prerequisites():
    """Check that all prerequisites are met before ingestion"""
    logger.info("🔍 Checking prerequisites...")
    
    # Check ChromaDB connection
    try:
        ingester = DocumentationIngester()
        stats = ingester.get_collection_stats()
        logger.info(f"✅ ChromaDB connected: {stats.get('total_documents', 0)} existing documents")
    except Exception as e:
        logger.error(f"❌ ChromaDB connection failed: {e}")
        return False
    
    # Check internet connectivity for inventory files
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get("https://docs.python.org/3/objects.inv") as response:
                if response.status == 200:
                    logger.info("✅ Internet connectivity confirmed")
                else:
                    logger.warning(f"⚠️  Unexpected response from Python docs: {response.status}")
    except Exception as e:
        logger.error(f"❌ Internet connectivity check failed: {e}")
        return False
    
    return True

async def main():
    """Main function with comprehensive CLI interface"""
    parser = argparse.ArgumentParser(
        description="Ingest documentation into ChromaDB for ResaleAnalyzer MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest Python documentation (default)
  python ingest_documentation.py --source python
  
  # Test mode with limited content
  python ingest_documentation.py --source python --test
  
  # List available sources
  python ingest_documentation.py --list-sources
  
  # Ingest all available sources
  python ingest_documentation.py --source all
        """
    )
    
    parser.add_argument(
        "--source", "-s",
        choices=IngestionConfig.list_available_sources() + ["all"],
        default="python",
        help="Documentation source to ingest"
    )
    
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Run in test mode with limited content"
    )
    
    parser.add_argument(
        "--list-sources", "-l",
        action="store_true",
        help="List all available documentation sources"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file for ingestion report (default: auto-generated)"
    )
    
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip prerequisite checks"
    )
    
    args = parser.parse_args()
    
    # Handle list sources command
    if args.list_sources:
        logger.info("📚 Available documentation sources:")
        for source_name in IngestionConfig.list_available_sources():
            config = IngestionConfig.get_source_info(source_name)
            logger.info(f"  {source_name}: {config.get('description', 'No description')}")
        return
    
    # Check prerequisites unless skipped
    if not args.skip_checks:
        if not await check_prerequisites():
            logger.error("❌ Prerequisites not met. Exiting.")
            return
    
    try:
        # Determine sources to ingest
        if args.source == "all":
            sources = IngestionConfig.list_available_sources()
        else:
            sources = [args.source]
        
        # Run ingestion
        results = await ingest_multiple_sources(sources, test_mode=args.test)
        
        # Save report and print summary
        save_ingestion_report(results, args.output)
        print_summary(results)
        
        logger.info("🎉 Documentation ingestion completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Ingestion failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())