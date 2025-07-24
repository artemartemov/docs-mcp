"""
Base documentation ingestion framework for ResaleAnalyzer MCP Server.

This module provides the foundation for ingesting documentation from various sources
into ChromaDB with a consistent, reusable pattern. Designed for extensibility and
best practices including rate limiting, error handling, and comprehensive logging.
"""

import asyncio
import logging
import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings

from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class DocumentMetadata:
    """Comprehensive metadata for documentation ingestion"""

    framework: str  # python, fastapi, swift_ios, etc.
    source: str  # Official docs, tutorial, blog, etc.
    doc_type: str  # reference, tutorial, howto, api, etc.
    title: str
    url: str
    section: str
    subsection: str = ""
    version: str = ""
    language: str = "en"
    last_modified: Optional[str] = None
    author: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

    def to_chroma_metadata(self) -> Dict[str, Any]:
        """Convert to ChromaDB-compatible metadata"""
        base_metadata = {
            "framework": self.framework,
            "source": self.source,
            "doc_type": self.doc_type,
            "title": self.title,
            "url": self.url,
            "section": self.section,
            "subsection": self.subsection,
            "version": self.version,
            "language": self.language,
            "ingested_at": datetime.utcnow().isoformat(),
            "last_modified": self.last_modified or "unknown",
            "project": "documentation_server",
        }

        # Add optional fields if present
        if self.author:
            base_metadata["author"] = self.author
        if self.tags:
            base_metadata["tags"] = ",".join(self.tags)

        return base_metadata


@dataclass
class DocumentContent:
    """Complete document content with metadata"""

    content: str
    metadata: DocumentMetadata
    content_hash: Optional[str] = None

    def __post_init__(self):
        if not self.content_hash:
            self.content_hash = hashlib.sha256(self.content.encode()).hexdigest()[:16]

    def generate_id(self) -> str:
        """Generate unique ChromaDB document ID"""
        source_hash = hashlib.sha256(self.metadata.url.encode()).hexdigest()[:12]
        return f"{self.metadata.framework}_{self.metadata.doc_type}_{source_hash}"

    def is_valid(self) -> bool:
        """Validate document content and metadata"""
        return (
            len(self.content.strip()) >= 50  # Minimum content length
            and self.metadata.framework
            and self.metadata.source
            and self.metadata.title
            and self.metadata.url
        )


class IngestionStats:
    """Track ingestion progress and statistics"""

    def __init__(self):
        self.total_discovered = 0
        self.total_processed = 0
        self.successful_ingestions = 0
        self.failed_ingestions = 0
        self.skipped_existing = 0
        self.start_time = datetime.utcnow()
        self.failed_urls: Set[str] = set()
        self.errors: List[str] = []
        self.failed_details: Dict[str, str] = {}  # URL -> error message

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_processed == 0:
            return 0.0
        return (self.successful_ingestions / self.total_processed) * 100

    @property
    def elapsed_time(self) -> float:
        """Calculate elapsed time in seconds"""
        return (datetime.utcnow() - self.start_time).total_seconds()

    def log_progress(self, batch_num: int = None):
        """Log current progress with detailed statistics"""
        batch_info = f" [Batch {batch_num}]" if batch_num else ""

        logger.info(
            f"""
📊 INGESTION PROGRESS{batch_info}:
   Discovered: {self.total_discovered}
   Processed: {self.total_processed}
   Successful: {self.successful_ingestions} ({self.success_rate:.1f}%)
   Failed: {self.failed_ingestions}
   Skipped (existing): {self.skipped_existing}
   Elapsed: {self.elapsed_time:.1f}s
"""
        )


class BaseDocumentationSource(ABC):
    """Abstract base class for documentation sources"""

    def __init__(self, name: str, base_url: str):
        self.name = name
        self.base_url = base_url
        self.stats = IngestionStats()
        self.rate_limit_delay = 1.0  # Default 1 second between requests
        self.max_retries = 3
        self.batch_size = 50

    @abstractmethod
    async def discover_content(self) -> List[str]:
        """Discover all available content URLs/identifiers"""
        pass

    @abstractmethod
    async def extract_content(self, identifier: str) -> Optional[DocumentContent]:
        """Extract content and metadata from a single source"""
        pass

    @abstractmethod
    def get_framework_name(self) -> str:
        """Return the framework name for this source"""
        pass

    async def should_skip_content(self, identifier: str) -> bool:
        """Check if content should be skipped (already exists, etc.)"""
        return False

    async def preprocess_content(self, content: str) -> str:
        """Optional preprocessing of content before ingestion"""
        return content.strip()

    async def postprocess_metadata(
        self, metadata: DocumentMetadata
    ) -> DocumentMetadata:
        """Optional postprocessing of metadata before ingestion"""
        return metadata


class DocumentationIngester:
    """Main orchestrator for documentation ingestion"""

    def __init__(self, collection_name: str = "documentation_collection"):
        self.collection_name = collection_name
        self.chroma_client: Optional[chromadb.PersistentClient] = None
        self.collection = None
        self._initialize_chromadb()

    def _initialize_chromadb(self):
        """Initialize ChromaDB connection"""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=settings.chroma_data_dir,
                settings=ChromaSettings(anonymized_telemetry=False, allow_reset=False),
            )

            # Get or create collection
            try:
                self.collection = self.chroma_client.get_collection(
                    self.collection_name
                )
                logger.info(f"Connected to existing collection: {self.collection_name}")
            except Exception:
                self.collection = self.chroma_client.create_collection(
                    name=self.collection_name,
                    metadata={
                        "description": "Multi-framework comprehensive documentation collection",
                        "created_at": datetime.utcnow().isoformat(),
                        "version": "2.0",
                        "ingestion_framework": "docs_ingestion",
                    },
                )
                logger.info(f"Created new collection: {self.collection_name}")

        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise

    async def ingest_from_source(
        self, source: BaseDocumentationSource
    ) -> IngestionStats:
        """Ingest documentation from a specific source"""
        logger.info(f"🚀 Starting ingestion from {source.name}")

        # Discover all content
        logger.info("🔍 Discovering available content...")
        identifiers = await source.discover_content()
        source.stats.total_discovered = len(identifiers)

        logger.info(f"📋 Found {len(identifiers)} items to process")

        # Process in batches
        batch_size = source.batch_size
        total_batches = (len(identifiers) + batch_size - 1) // batch_size

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(identifiers))
            batch_identifiers = identifiers[start_idx:end_idx]

            await self._process_batch(
                source, batch_identifiers, batch_idx + 1, total_batches
            )

            # Small delay between batches
            await asyncio.sleep(0.1)

        # Final statistics
        source.stats.log_progress()
        logger.info(f"✅ Completed ingestion from {source.name}")

        # Save failed URLs if any
        if source.stats.failed_urls:
            failed_file = self.save_failed_urls(source)
            logger.info(
                f"""
🔄 RETRY INSTRUCTIONS:
   Failed URLs have been saved to: {failed_file}
   
   To retry only the failed URLs, run:
   ./run_ingestion.sh --source {source.get_framework_name()} --retry {failed_file}
   
   Or use make commands:
   make retry-{source.get_framework_name()} FAILED_FILE={failed_file}
"""
            )

        return source.stats

    async def _process_batch(
        self,
        source: BaseDocumentationSource,
        identifiers: List[str],
        batch_num: int,
        total_batches: int,
    ):
        """Process a batch of identifiers"""
        logger.info(
            f"[Batch {batch_num}/{total_batches}] Processing {len(identifiers)} items..."
        )

        documents_to_add = []

        for identifier in identifiers:
            source.stats.total_processed += 1

            try:
                # Check if should skip
                if await source.should_skip_content(identifier):
                    source.stats.skipped_existing += 1
                    continue

                # Extract content
                document = await source.extract_content(identifier)
                if not document or not document.is_valid():
                    source.stats.failed_ingestions += 1
                    source.stats.failed_urls.add(identifier)
                    source.stats.failed_details[identifier] = (
                        "Invalid or empty content extracted"
                    )
                    continue

                # Preprocess content and postprocess metadata
                document.content = await source.preprocess_content(document.content)
                document.metadata = await source.postprocess_metadata(document.metadata)

                documents_to_add.append(document)
                source.stats.successful_ingestions += 1

            except Exception as e:
                error_msg = f"Error processing {identifier}: {e}"
                logger.error(error_msg)
                source.stats.errors.append(error_msg)
                source.stats.failed_ingestions += 1
                source.stats.failed_urls.add(identifier)
                source.stats.failed_details[identifier] = str(e)

        # Batch insert to ChromaDB
        if documents_to_add:
            await self._batch_insert_chromadb(documents_to_add)

        # Log progress
        source.stats.log_progress(batch_num)

    async def _batch_insert_chromadb(self, documents: List[DocumentContent]):
        """Insert a batch of documents into ChromaDB"""
        if not documents:
            return

        try:
            # Prepare batch data
            ids = [doc.generate_id() for doc in documents]
            contents = [doc.content for doc in documents]
            metadatas = [doc.metadata.to_chroma_metadata() for doc in documents]

            # Check for existing documents
            existing_docs = []
            try:
                existing_result = self.collection.get(ids=ids)
                existing_docs = existing_result.get("ids", [])
            except Exception:
                pass  # No existing documents

            # Filter out existing documents
            new_ids = []
            new_contents = []
            new_metadatas = []

            for i, doc_id in enumerate(ids):
                if doc_id not in existing_docs:
                    new_ids.append(doc_id)
                    new_contents.append(contents[i])
                    new_metadatas.append(metadatas[i])

            # Insert new documents
            if new_ids:
                self.collection.add(
                    ids=new_ids, documents=new_contents, metadatas=new_metadatas
                )
                logger.debug(f"✅ Inserted {len(new_ids)} new documents")

            if len(existing_docs) > 0:
                logger.debug(f"⏭️  Skipped {len(existing_docs)} existing documents")

        except Exception as e:
            logger.error(f"❌ Failed to insert batch: {e}")
            raise

    def get_collection_stats(self) -> Dict[str, Any]:
        """Get comprehensive collection statistics"""
        if not self.collection:
            return {"error": "Collection not initialized"}

        try:
            total_count = self.collection.count()

            # Get sample for framework breakdown
            sample_size = min(1000, total_count)
            sample_data = self.collection.get(limit=sample_size)

            framework_counts = {}
            doc_type_counts = {}

            for metadata in sample_data.get("metadatas", []):
                framework = metadata.get("framework", "unknown")
                doc_type = metadata.get("doc_type", "unknown")

                framework_counts[framework] = framework_counts.get(framework, 0) + 1
                doc_type_counts[doc_type] = doc_type_counts.get(doc_type, 0) + 1

            return {
                "total_documents": total_count,
                "frameworks": framework_counts,
                "document_types": doc_type_counts,
                "collection_name": self.collection_name,
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {"error": str(e)}

    def save_failed_urls(
        self, source: BaseDocumentationSource, output_path: Optional[str] = None
    ) -> str:
        """Save failed URLs to a JSON file for retry functionality"""
        if not output_path:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            framework = source.get_framework_name()
            output_path = f"logs/failed_urls_{framework}_{timestamp}.json"

        # Ensure logs directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        failed_data = {
            "framework": source.get_framework_name(),
            "source_name": source.name,
            "base_url": source.base_url,
            "timestamp": datetime.utcnow().isoformat(),
            "total_failed": len(source.stats.failed_urls),
            "failed_urls": {
                url: source.stats.failed_details.get(url, "Unknown error")
                for url in source.stats.failed_urls
            },
            "ingestion_stats": {
                "total_discovered": source.stats.total_discovered,
                "total_processed": source.stats.total_processed,
                "successful_ingestions": source.stats.successful_ingestions,
                "failed_ingestions": source.stats.failed_ingestions,
                "skipped_existing": source.stats.skipped_existing,
                "success_rate": source.stats.success_rate,
                "elapsed_time": source.stats.elapsed_time,
            },
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(failed_data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"💾 Saved {len(source.stats.failed_urls)} failed URLs to: {output_path}"
        )
        return output_path

    def load_failed_urls(self, failed_urls_file: str) -> List[str]:
        """Load failed URLs from a JSON file"""
        try:
            with open(failed_urls_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            failed_urls = list(data.get("failed_urls", {}).keys())
            logger.info(
                f"📂 Loaded {len(failed_urls)} failed URLs from: {failed_urls_file}"
            )

            # Log some stats about the failures
            if "ingestion_stats" in data:
                stats = data["ingestion_stats"]
                logger.info(
                    f"""
📊 ORIGINAL INGESTION STATS:
   Framework: {data.get('framework', 'unknown')}
   Total Processed: {stats.get('total_processed', 0)}
   Failed: {stats.get('failed_ingestions', 0)}
   Success Rate: {stats.get('success_rate', 0):.1f}%
   Original Date: {data.get('timestamp', 'unknown')}
"""
                )

            return failed_urls

        except Exception as e:
            logger.error(f"❌ Failed to load failed URLs from {failed_urls_file}: {e}")
            return []

    async def retry_failed_urls(
        self,
        source: BaseDocumentationSource,
        failed_urls: List[str],
        test_mode: bool = False,
    ) -> IngestionStats:
        """Retry ingestion for specific failed URLs"""
        logger.info(
            f"🔄 Starting retry ingestion for {len(failed_urls)} failed URLs..."
        )

        if test_mode:
            logger.info("🧪 Running in test mode (limited URLs)")
            failed_urls = failed_urls[:10]  # Limit to 10 URLs in test mode

        # Reset stats for retry attempt
        source.stats = IngestionStats()
        source.stats.total_discovered = len(failed_urls)

        # Run the ingestion with only the failed URLs
        await self.ingest_with_urls(source, failed_urls, test_mode)

        return source.stats

    async def ingest_with_urls(
        self, source: BaseDocumentationSource, urls: List[str], test_mode: bool = False
    ):
        """Run ingestion with a specific list of URLs (used for retries)"""
        logger.info(f"📥 Starting targeted ingestion for {len(urls)} URLs...")

        if test_mode:
            logger.info("🧪 Test mode enabled")
            urls = urls[:10]

        # Process in batches
        total_batches = (len(urls) + source.batch_size - 1) // source.batch_size

        for i in range(0, len(urls), source.batch_size):
            batch_urls = urls[i : i + source.batch_size]
            batch_num = (i // source.batch_size) + 1

            await self._process_batch(source, batch_urls, batch_num, total_batches)

            # Rate limiting between batches
            if i + source.batch_size < len(urls):
                await asyncio.sleep(source.rate_limit_delay)

        # Final statistics
        logger.info(
            f"""
🎯 RETRY INGESTION COMPLETED:
   URLs Attempted: {len(urls)}
   Successful: {source.stats.successful_ingestions}
   Failed: {source.stats.failed_ingestions}
   Success Rate: {source.stats.success_rate:.1f}%
   Total Time: {source.stats.elapsed_time:.1f}s
"""
        )

        # Save any new failures
        if source.stats.failed_urls:
            failed_file = self.save_failed_urls(source)
            logger.info(f"💾 New failures saved to: {failed_file}")
        else:
            logger.info("🎉 All retry URLs succeeded!")
