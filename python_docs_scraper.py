#!/usr/bin/env python3
"""
Python Documentation Scraper for ResaleAnalyzer MCP Server
Safely scrapes Python 3 documentation and populates ChromaDB with comprehensive content.

Features:
- Rate limiting and respectful scraping
- Sitemap-based URL discovery
- Comprehensive content extraction
- Batch processing for ChromaDB
- Verbose progress tracking
- Error handling and recovery
"""

import asyncio
import aiohttp
import time
import hashlib
import logging
from urllib.parse import urljoin, urlparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import chromadb
from chromadb.config import Settings as ChromaSettings

from config import get_settings, validate_environment

# Configure logging for verbose progress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/python_docs_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

settings = get_settings()

@dataclass
class DocumentContent:
    """Structured document content for ChromaDB storage"""
    url: str
    title: str
    content: str
    section: str
    subsection: str
    doc_type: str
    last_modified: Optional[str] = None
    
    def generate_id(self) -> str:
        """Generate unique document ID"""
        url_hash = hashlib.sha256(self.url.encode()).hexdigest()[:12]
        return f"python3_docs_{url_hash}"
    
    def to_metadata(self) -> Dict:
        """Convert to ChromaDB metadata"""
        return {
            "framework": "python",
            "category": "official_docs",
            "doc_type": self.doc_type,
            "section": self.section,
            "subsection": self.subsection,
            "url": self.url,
            "title": self.title,
            "scraped_at": datetime.utcnow().isoformat(),
            "last_modified": self.last_modified or "unknown",
            "source": "Python 3 Official Documentation"
        }

class PythonDocsScraper:
    """Safe and comprehensive Python documentation scraper"""
    
    def __init__(self):
        self.base_url = "https://docs.python.org/3/"
        self.session: Optional[aiohttp.ClientSession] = None
        self.scraped_urls: Set[str] = set()
        self.failed_urls: Set[str] = set()
        self.rate_limit_delay = 1.0  # 1 second between requests
        self.last_request_time = 0.0
        self.max_retries = 3
        self.timeout = 30
        
        # Progress tracking
        self.total_urls = 0
        self.processed_urls = 0
        self.successful_scrapes = 0
        self.failed_scrapes = 0
        
    async def __aenter__(self):
        """Async context manager entry"""
        connector = aiohttp.TCPConnector(limit_per_host=1)  # Limit concurrent connections
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'ResaleAnalyzer-DocsScraper/1.0 (Educational/Research Purpose)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def respect_rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            await asyncio.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def fetch_with_retry(self, url: str) -> Optional[str]:
        """Fetch URL content with retry logic and error handling"""
        for attempt in range(self.max_retries):
            try:
                await self.respect_rate_limit()
                
                async with self.session.get(url) as response:
                    if response.status == 200:
                        content = await response.text()
                        logger.debug(f"Successfully fetched: {url}")
                        return content
                    elif response.status == 429:  # Too Many Requests
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Rate limited on {url}, waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        logger.warning(f"HTTP {response.status} for {url}")
                        
            except asyncio.TimeoutError:
                logger.warning(f"Timeout for {url} (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Error fetching {url} (attempt {attempt + 1}): {e}")
            
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
        return None
    
    async def discover_urls_from_sitemap(self) -> List[str]:
        """Discover URLs from Python docs sitemap"""
        sitemap_urls = [
            f"{self.base_url}sitemap.xml",
            f"{self.base_url}objects.inv",  # Sphinx inventory
        ]
        
        discovered_urls = set()
        
        # Try sitemap first
        sitemap_content = await self.fetch_with_retry(f"{self.base_url}sitemap.xml")
        if sitemap_content:
            try:
                root = ET.fromstring(sitemap_content)
                for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                    loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc_elem is not None and loc_elem.text:
                        if loc_elem.text.startswith(self.base_url):
                            discovered_urls.add(loc_elem.text)
                
                logger.info(f"Discovered {len(discovered_urls)} URLs from sitemap")
            except ET.ParseError as e:
                logger.warning(f"Failed to parse sitemap: {e}")
        
        # Fallback: discover from main page navigation
        if not discovered_urls:
            discovered_urls = await self.discover_urls_from_navigation()
        
        return list(discovered_urls)
    
    async def discover_urls_from_navigation(self) -> Set[str]:
        """Fallback: discover URLs by crawling navigation structure"""
        logger.info("Fallback: discovering URLs from navigation structure")
        discovered_urls = set()
        
        main_content = await self.fetch_with_retry(self.base_url)
        if not main_content:
            return discovered_urls
        
        soup = BeautifulSoup(main_content, 'html.parser')
        
        # Find all links in navigation and content areas
        for link in soup.find_all('a', href=True):
            href = link['href']
            if not href.startswith('http'):
                full_url = urljoin(self.base_url, href)
            else:
                full_url = href
            
            # Only include Python 3 docs URLs
            if (full_url.startswith(self.base_url) and 
                not any(skip in full_url for skip in ['#', 'mailto:', 'javascript:', '.pdf', '.zip'])):
                discovered_urls.add(full_url)
        
        logger.info(f"Discovered {len(discovered_urls)} URLs from navigation")
        return discovered_urls
    
    def extract_content(self, html: str, url: str) -> Optional[DocumentContent]:
        """Extract structured content from HTML"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else "Untitled"
            
            # Remove navigation and header elements for cleaner content
            for element in soup.find_all(['nav', 'header', 'footer', '.headerlink']):
                element.decompose()
            
            # Extract main content
            main_content = soup.find('div', class_='body') or soup.find('main') or soup.find('div', class_='document')
            if not main_content:
                main_content = soup.find('body')
            
            if not main_content:
                logger.warning(f"No main content found for {url}")
                return None
            
            # Clean and extract text
            content_text = main_content.get_text()
            content_text = ' '.join(content_text.split())  # Normalize whitespace
            
            if len(content_text) < 100:  # Skip very short content
                logger.debug(f"Skipping short content for {url}")
                return None
            
            # Determine section and subsection from URL structure
            parsed_url = urlparse(url)
            path_parts = [p for p in parsed_url.path.split('/') if p and p != '3']
            
            section = path_parts[0] if path_parts else "general"
            subsection = path_parts[1] if len(path_parts) > 1 else "overview"
            
            # Determine document type
            doc_type = "reference"
            if "tutorial" in url.lower():
                doc_type = "tutorial"
            elif "howto" in url.lower():
                doc_type = "howto"
            elif "library" in url.lower():
                doc_type = "library"
            elif "reference" in url.lower():
                doc_type = "reference"
            
            return DocumentContent(
                url=url,
                title=title,
                content=content_text,
                section=section,
                subsection=subsection,
                doc_type=doc_type
            )
            
        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None
    
    def print_progress(self):
        """Print detailed progress information"""
        if self.total_urls > 0:
            progress_pct = (self.processed_urls / self.total_urls) * 100
            success_rate = (self.successful_scrapes / max(1, self.processed_urls)) * 100
            
            logger.info(f"""
📊 SCRAPING PROGRESS:
   Total URLs: {self.total_urls}
   Processed: {self.processed_urls} ({progress_pct:.1f}%)
   Successful: {self.successful_scrapes} ({success_rate:.1f}% success rate)
   Failed: {self.failed_scrapes}
   Remaining: {self.total_urls - self.processed_urls}
""")
    
    async def scrape_documentation(self) -> List[DocumentContent]:
        """Main scraping function with comprehensive progress tracking"""
        logger.info("🚀 Starting Python 3 documentation scraping...")
        
        # Discover all URLs
        logger.info("🔍 Discovering URLs from documentation structure...")
        urls = await self.discover_urls_from_sitemap()
        
        # Filter and deduplicate URLs
        unique_urls = list(set(url for url in urls if self.should_scrape_url(url)))
        self.total_urls = len(unique_urls)
        
        logger.info(f"📋 Found {self.total_urls} unique URLs to scrape")
        
        documents = []
        batch_size = 10  # Process in batches for better progress tracking
        
        for i in range(0, len(unique_urls), batch_size):
            batch_urls = unique_urls[i:i + batch_size]
            batch_docs = await self.process_batch(batch_urls)
            documents.extend(batch_docs)
            
            # Print progress every batch
            self.print_progress()
            
            # Small delay between batches to be extra respectful
            await asyncio.sleep(0.5)
        
        # Final progress report
        logger.info(f"""
✅ SCRAPING COMPLETE!
   Total documents extracted: {len(documents)}
   Success rate: {(self.successful_scrapes / self.total_urls) * 100:.1f}%
   Failed URLs: {len(self.failed_urls)}
""")
        
        return documents
    
    async def process_batch(self, urls: List[str]) -> List[DocumentContent]:
        """Process a batch of URLs"""
        batch_documents = []
        
        for url in urls:
            self.processed_urls += 1
            
            logger.info(f"[{self.processed_urls}/{self.total_urls}] Scraping: {url}")
            
            html_content = await self.fetch_with_retry(url)
            if html_content:
                doc = self.extract_content(html_content, url)
                if doc:
                    batch_documents.append(doc)
                    self.successful_scrapes += 1
                    self.scraped_urls.add(url)
                else:
                    self.failed_scrapes += 1
                    self.failed_urls.add(url)
            else:
                self.failed_scrapes += 1
                self.failed_urls.add(url)
        
        return batch_documents
    
    def should_scrape_url(self, url: str) -> bool:
        """Determine if URL should be scraped"""
        # Skip non-documentation URLs
        skip_patterns = [
            '_sources/', '_static/', '.pdf', '.zip', '.tar.gz',
            'download.html', 'bugs.html', 'genindex.html',
            'py-modindex.html', 'search.html', '#'
        ]
        
        return not any(pattern in url for pattern in skip_patterns)

async def populate_chromadb(documents: List[DocumentContent], batch_size: int = 50):
    """Populate ChromaDB with scraped documents"""
    logger.info(f"📚 Populating ChromaDB with {len(documents)} documents...")
    
    # Initialize ChromaDB
    validate_environment()
    chroma_client = chromadb.PersistentClient(
        path=settings.chroma_data_dir,
        settings=ChromaSettings(
            anonymized_telemetry=False,
            allow_reset=False
        )
    )
    
    # Get or create collection
    try:
        collection = chroma_client.get_collection("resale_analyzer_docs")
    except Exception:
        collection = chroma_client.create_collection(
            name="resale_analyzer_docs",
            metadata={
                "description": "ResaleAnalyzer project documentation: FastAPI + Python + Swift iOS",
                "created_at": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
        )
    
    # Process documents in batches
    total_batches = (len(documents) + batch_size - 1) // batch_size
    added_count = 0
    skipped_count = 0
    
    for batch_idx in range(total_batches):
        start_idx = batch_idx * batch_size
        end_idx = min(start_idx + batch_size, len(documents))
        batch_docs = documents[start_idx:end_idx]
        
        logger.info(f"[Batch {batch_idx + 1}/{total_batches}] Adding {len(batch_docs)} documents to ChromaDB...")
        
        batch_ids = []
        batch_contents = []
        batch_metadatas = []
        
        for doc in batch_docs:
            doc_id = doc.generate_id()
            
            # Check if document already exists
            try:
                existing = collection.get(ids=[doc_id])
                if existing['ids']:
                    logger.debug(f"Skipping existing document: {doc_id}")
                    skipped_count += 1
                    continue
            except Exception:
                pass  # Document doesn't exist, proceed to add
            
            batch_ids.append(doc_id)
            batch_contents.append(doc.content)
            batch_metadatas.append(doc.to_metadata())
        
        # Add batch to collection
        if batch_ids:
            try:
                collection.add(
                    ids=batch_ids,
                    documents=batch_contents,
                    metadatas=batch_metadatas
                )
                added_count += len(batch_ids)
                logger.info(f"✅ Added {len(batch_ids)} documents (Total: {added_count})")
            except Exception as e:
                logger.error(f"❌ Failed to add batch {batch_idx + 1}: {e}")
        
        # Small delay between batches
        await asyncio.sleep(0.1)
    
    logger.info(f"""
📊 CHROMADB POPULATION COMPLETE:
   Documents added: {added_count}
   Documents skipped (existing): {skipped_count}
   Total collection size: {collection.count()}
""")

async def main():
    """Main function to scrape Python docs and populate ChromaDB"""
    try:
        async with PythonDocsScraper() as scraper:
            # Scrape all documentation
            documents = await scraper.scrape_documentation()
            
            if documents:
                # Populate ChromaDB
                await populate_chromadb(documents)
                
                logger.info("🎉 Python documentation scraping and population completed successfully!")
            else:
                logger.warning("No documents were scraped")
                
    except Exception as e:
        logger.error(f"❌ Scraping failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())