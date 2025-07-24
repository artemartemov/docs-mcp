"""
Figma Plugin API Documentation Adapter.

Extracts comprehensive documentation from the official Figma Plugin API
documentation website for integration into ChromaDB.
"""

import asyncio
import logging
import aiohttp
import re
from typing import List, Optional, Dict, Set
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag

from ..base import BaseDocumentationSource, DocumentContent, DocumentMetadata

logger = logging.getLogger(__name__)


class FigmaPluginDocsSource(BaseDocumentationSource):
    """Figma Plugin API documentation source from official website"""

    def __init__(self, version: str = "latest"):
        self.version = version
        base_url = "https://www.figma.com/plugin-docs/"
        super().__init__(f"Figma Plugin API {version} Docs", base_url)

        self.session: Optional[aiohttp.ClientSession] = None

        # Configure for respectful scraping
        self.rate_limit_delay = 1.2  # Be respectful to Figma's servers
        self.batch_size = 20

        # Priority sections for comprehensive coverage
        self.priority_sections = {
            "intro",
            "getting-started",
            "quickstart",
            "basics",
            "development",
            "api-reference",
            "plugin-api",
            "widget-api",
            "guides",
            "tutorials",
            "publishing",
            "community",
            "examples",
            "troubleshooting",
        }

        # Skip patterns for cleaner content
        self.skip_patterns = {
            "search",
            "404",
            "error",
            "sitemap",
            "robots.txt",
            "privacy",
            "terms",
            "legal",
        }

        # Section categorization for better organization
        self.section_categories = {
            "getting_started": [
                "intro",
                "getting-started",
                "quickstart",
                "prerequisites",
            ],
            "plugin_development": ["basics", "development", "guides", "how-to"],
            "api_reference": ["api-reference", "plugin-api", "reference"],
            "widget_development": ["widget-api", "widgets"],
            "publishing": ["publishing", "distribution", "store"],
            "tutorials": ["tutorials", "examples", "sample"],
            "troubleshooting": ["troubleshooting", "faq", "common-issues"],
        }

    async def __aenter__(self):
        """Initialize async HTTP session"""
        connector = aiohttp.TCPConnector(limit_per_host=2)
        timeout = aiohttp.ClientTimeout(total=45)

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                "User-Agent": "ResaleAnalyzer-DocsIngester/2.0 (Educational Research)",
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
            },
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Close async HTTP session"""
        if self.session:
            await self.session.close()

    def get_framework_name(self) -> str:
        return "figma_plugin"

    async def discover_content(self) -> List[str]:
        """Discover content by crawling the documentation structure"""
        logger.info(f"🔍 Discovering Figma Plugin documentation from {self.base_url}")

        discovered_urls = set()

        try:
            # Start with the main documentation page
            main_urls = [
                self.base_url,
                f"{self.base_url}getting-started/",
                f"{self.base_url}plugin-api/",
                f"{self.base_url}widget-api/",
                f"{self.base_url}guides/",
                f"{self.base_url}quickstart/",
            ]

            for start_url in main_urls:
                await self._discover_from_page(start_url, discovered_urls)
                await asyncio.sleep(self.rate_limit_delay)

            # Filter and sort URLs - optimize performance
            filtered_urls = list(
                {url for url in discovered_urls if self._should_include_url(url)}
            )
            logger.info(
                f"📋 Discovered {len(filtered_urls)} relevant documentation pages"
            )

            return sorted(filtered_urls)

        except Exception as e:
            logger.error(f"❌ Failed to discover content: {e}")
            return []

    async def _discover_from_page(
        self, url: str, discovered_urls: set, max_depth: int = 3
    ) -> None:
        """Recursively discover URLs from a page"""
        if max_depth <= 0 or url in discovered_urls:
            return

        try:
            async with self.session.get(url) as response:
                if response.status != 200:
                    return

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                discovered_urls.add(url)

                # Find navigation links and content links
                nav_selectors = [
                    "nav a[href]",
                    ".nav a[href]",
                    ".navigation a[href]",
                    ".sidebar a[href]",
                    ".menu a[href]",
                    ".docs-nav a[href]",
                    'a[href*="plugin-docs"]',
                ]

                for selector in nav_selectors:
                    links = soup.select(selector)
                    for link in links:
                        href = link.get("href")
                        if href:
                            full_url = urljoin(url, href)
                            if (
                                self._is_plugin_docs_url(full_url)
                                and full_url not in discovered_urls
                            ):
                                if max_depth > 1:
                                    await self._discover_from_page(
                                        full_url, discovered_urls, max_depth - 1
                                    )
                                else:
                                    discovered_urls.add(full_url)

        except Exception as e:
            logger.debug(f"Error discovering from {url}: {e}")

    def _is_plugin_docs_url(self, url: str) -> bool:
        """Check if URL is part of plugin documentation"""
        parsed = urlparse(url)
        return (
            parsed.netloc == "www.figma.com"
            and "/plugin-docs" in parsed.path
            and not any(skip in url.lower() for skip in self.skip_patterns)
        )

    def _should_include_url(self, url: str) -> bool:
        """Determine if URL should be included in extraction"""
        if not self._is_plugin_docs_url(url):
            return False

        # Skip certain file types and fragments
        if any(
            ext in url.lower()
            for ext in [".pdf", ".jpg", ".png", ".gif", ".css", ".js"]
        ):
            return False

        # Remove fragment identifiers for consistency
        clean_url = url.split("#")[0]

        return True

    async def extract_content(self, url: str) -> Optional[DocumentContent]:
        """Extract content from a specific documentation page"""
        try:
            await asyncio.sleep(self.rate_limit_delay)

            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None

                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")

                # Extract title
                title = self._extract_title(soup, url)
                if not title:
                    return None

                # Extract main content
                content = self._extract_main_content(soup)
                if not content or len(content.strip()) < 100:
                    logger.debug(f"Skipping {url} - insufficient content")
                    return None

                # Create metadata
                metadata = self._create_metadata(url, title, content)

                return DocumentContent(content=content, metadata=metadata)

        except Exception as e:
            logger.error(f"Error extracting content from {url}: {e}")
            return None

    def _extract_title(self, soup: BeautifulSoup, url: str) -> Optional[str]:
        """Extract page title"""
        # Try various title selectors
        title_selectors = ["h1", ".page-title", ".doc-title", ".content-title", "title"]

        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                if title and len(title) > 3:
                    return title

        # Fallback to URL-based title
        path = urlparse(url).path
        return path.split("/")[-2].replace("-", " ").title() if path else None

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main documentation content"""
        # Try multiple content selectors
        content_selectors = [
            "main",
            ".content",
            ".doc-content",
            ".main-content",
            ".documentation",
            ".page-content",
            "article",
            ".container",
        ]

        main_content = None
        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                main_content = content_elem
                break

        if not main_content:
            main_content = soup.find("body")

        if not main_content:
            return ""

        # Remove unwanted elements
        unwanted_selectors = [
            "nav",
            ".nav",
            ".navigation",
            "footer",
            ".footer",
            ".sidebar",
            ".menu",
            "script",
            "style",
            ".breadcrumb",
            ".breadcrumbs",
            ".prev-next",
            ".pagination",
            ".search",
            ".search-box",
        ]

        for selector in unwanted_selectors:
            for elem in main_content.select(selector):
                elem.decompose()

        # Extract text content with some structure preservation
        content_parts = []

        for element in main_content.find_all(
            ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "pre", "code"]
        ):
            if element.name.startswith("h"):
                level = "#" * int(element.name[1])
                content_parts.append(f"\n{level} {element.get_text().strip()}\n")
            elif element.name == "pre":
                content_parts.append(f"\n```\n{element.get_text().strip()}\n```\n")
            elif element.name == "code" and element.parent.name != "pre":
                content_parts.append(f"`{element.get_text().strip()}`")
            else:
                text = element.get_text().strip()
                if text:
                    content_parts.append(text)

        return "\n".join(content_parts).strip()

    def _categorize_url(self, url: str) -> str:
        """Categorize URL into documentation sections"""
        url_lower = url.lower()

        for category, keywords in self.section_categories.items():
            if any(keyword in url_lower for keyword in keywords):
                return category

        return "general"

    def _determine_doc_type(self, url: str, title: str, content: str) -> str:
        """Determine document type based on URL, title, and content"""
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()[:1000]

        if any(term in url_lower for term in ["api-reference", "reference"]):
            return "api_reference"
        elif any(
            term in url_lower for term in ["tutorial", "quickstart", "getting-started"]
        ):
            return "tutorial"
        elif any(term in url_lower for term in ["guide", "how-to"]):
            return "guide"
        elif any(term in url_lower for term in ["example", "sample"]):
            return "example"
        elif any(term in title_lower for term in ["introduction", "overview"]):
            return "introduction"
        elif any(
            term in content_lower
            for term in ["function", "method", "property", "interface"]
        ):
            return "api_documentation"
        elif any(term in url_lower for term in ["troubleshooting", "faq"]):
            return "troubleshooting"
        else:
            return "documentation"

    def _create_metadata(self, url: str, title: str, content: str) -> DocumentMetadata:
        """Create metadata for the document"""
        section = self._categorize_url(url)
        doc_type = self._determine_doc_type(url, title, content)
        tags = self._generate_tags(url, title, content)

        # Extract subsection from URL
        path_parts = urlparse(url).path.strip("/").split("/")
        subsection = path_parts[-1] if len(path_parts) > 1 else "main"

        return DocumentMetadata(
            framework="figma_plugin",
            source="Figma Plugin API Official Documentation",
            doc_type=doc_type,
            title=title,
            url=url,
            section=section,
            subsection=subsection,
            version=self.version,
            language="en",
            tags=tags,
        )

    def _generate_tags(self, url: str, title: str, content: str) -> List[str]:
        """Generate relevant tags for the content"""
        tags = ["plugin_development", "figma_api", "javascript", "web_development"]

        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()[:2000]

        # Add URL-based tags
        if "widget" in url_lower:
            tags.extend(["widget_api", "figma_widgets"])
        if "plugin-api" in url_lower:
            tags.extend(["plugin_api", "core_api"])
        if "getting-started" in url_lower:
            tags.extend(["beginner", "setup", "introduction"])
        if "guide" in url_lower:
            tags.extend(["guide", "tutorial"])

        # Add content-based tags
        if any(term in content_lower for term in ["node", "scenenode", "document"]):
            tags.append("document_model")
        if any(term in content_lower for term in ["async", "promise", "await"]):
            tags.append("asynchronous")
        if any(term in content_lower for term in ["ui", "interface", "html"]):
            tags.append("user_interface")
        if any(term in content_lower for term in ["publish", "store", "community"]):
            tags.append("publishing")
        if any(term in content_lower for term in ["typescript", "javascript", "js"]):
            tags.append("javascript")
        if any(term in content_lower for term in ["canvas", "frame", "layer"]):
            tags.append("canvas_manipulation")
        if any(term in content_lower for term in ["font", "text", "typography"]):
            tags.append("typography")
        if any(term in content_lower for term in ["color", "fill", "stroke"]):
            tags.append("styling")

        # Add difficulty level
        if any(
            term in title_lower
            for term in ["introduction", "getting started", "quickstart"]
        ):
            tags.append("beginner")
        elif any(
            term in title_lower for term in ["advanced", "complex", "optimization"]
        ):
            tags.append("advanced")
        else:
            tags.append("intermediate")

        return tags

    async def preprocess_content(self, content: str) -> str:
        """Clean and structure content"""
        lines = content.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            # Skip very short lines unless they're markdown headers
            if len(line) > 3 or line.startswith("#"):
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines)

    async def postprocess_metadata(
        self, metadata: DocumentMetadata
    ) -> DocumentMetadata:
        """Enhance metadata with additional information"""
        # Add comprehensive documentation tag
        metadata.tags.append("official_documentation")
        metadata.tags.append("web_scraped")

        # Add API version if detectable
        if "v1" in metadata.url or "version 1" in metadata.title.lower():
            metadata.tags.append("api_v1")

        return metadata
