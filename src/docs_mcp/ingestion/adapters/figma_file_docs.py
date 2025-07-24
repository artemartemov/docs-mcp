"""
Figma API Documentation Adapter for Local HTML File Processing.

Processes the figmaapi.txt file directly to extract comprehensive Figma API documentation
without relying on web scraping. Follows the same patterns as other working adapters.
"""

import asyncio
import logging
import re
from typing import List, Optional, Dict, Set
from pathlib import Path
from bs4 import BeautifulSoup, Tag

from ..base import BaseDocumentationSource, DocumentContent, DocumentMetadata

logger = logging.getLogger(__name__)

class FigmaFileDocsSource(BaseDocumentationSource):
    """Figma API documentation source from local HTML file"""
    
    def __init__(self, file_path: str, version: str = "latest"):
        self.file_path = Path(file_path)
        self.version = version
        base_url = "https://www.figma.com/developers/api"
        super().__init__(f"Figma API {version} File Docs", base_url)
        
        # HTML content and parsed sections
        self.html_content: Optional[str] = None
        self.soup: Optional[BeautifulSoup] = None
        self.sections: Dict[str, Tag] = {}
        
        # Configure for fast local processing
        self.rate_limit_delay = 0.0  # No rate limiting for local files
        self.batch_size = 50
        
        # Figma API documentation sections mapping
        self.section_mapping = {
            "intro": "introduction",
            "authentication": "authentication", 
            "files": "files_api",
            "comments": "comments_api",
            "users": "users_api",
            "version-history": "version_history",
            "projects": "projects_api",
            "library-items": "components_styles",
            "webhooks_v2": "webhooks",
            "activity_logs": "activity_logs",
            "discovery": "discovery_api",
            "payments": "payments_api",
            "variables": "variables_api",
            "dev-resources": "dev_resources",
            "library-analytics": "library_analytics",
            "errors": "error_handling",
            "scim-api-guide": "scim_api",
            "changelog": "changelog"
        }
        
        # Skip patterns for cleaner content
        self.skip_patterns = {
            "Get personal access token", "What's this?", "My apps",
            "Create a new app", "cookie-banner", "newsletter-signup"
        }
    
    def get_framework_name(self) -> str:
        return "figma"
    
    async def discover_content(self) -> List[str]:
        """
        Discover content sections from the HTML file.
        Returns section identifiers instead of URLs.
        """
        logger.info(f"🔍 Loading Figma API documentation from {self.file_path}")
        
        try:
            # Read the HTML file
            if not self.file_path.exists():
                logger.error(f"File not found: {self.file_path}")
                return []
            
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.html_content = f.read()
            
            logger.info(f"📄 Loaded HTML file ({len(self.html_content):,} characters)")
            
            # Parse with BeautifulSoup
            self.soup = BeautifulSoup(self.html_content, 'html.parser')
            
            # Extract main sections
            sections = self._extract_sections()
            
            logger.info(f"📋 Found {len(sections)} documentation sections")
            
            # Log section breakdown
            section_counts = {}
            for section_id in sections:
                section_name = self.section_mapping.get(section_id, section_id)
                section_counts[section_name] = section_counts.get(section_name, 0) + 1
            
            logger.info("📊 Section breakdown:")
            for section, count in sorted(section_counts.items()):
                logger.info(f"   {section}: {count} sections")
            
            return sections
            
        except Exception as e:
            logger.error(f"❌ Failed to load HTML file: {e}")
            return []
    
    def _extract_sections(self) -> List[str]:
        """Extract all meaningful sections from the HTML"""
        sections = []
        
        if not self.soup:
            return sections
        
        # Method 1: Find all major documentation sections by ID
        section_elements = self.soup.find_all('div', id=True)
        for element in section_elements:
            section_id = element.get('id')
            if section_id and (section_id in self.section_mapping or 
                              any(known_id in section_id for known_id in self.section_mapping.keys())):
                # Normalize section ID to our mapping
                normalized_id = section_id
                if section_id not in self.section_mapping:
                    # Find best match
                    for known_id in self.section_mapping.keys():
                        if known_id in section_id or section_id.startswith(known_id):
                            normalized_id = known_id
                            break
                
                self.sections[normalized_id] = element
                sections.append(normalized_id)
                logger.debug(f"Found section by ID: {section_id} -> {normalized_id}")
        
        # Method 2: Find specific div.developer_docs--section elements
        doc_sections = self.soup.find_all('div', class_=re.compile(r'developer_docs--section'))
        for element in doc_sections:
            section_id = element.get('id')
            if section_id and section_id not in self.sections:
                # Check if this is a known section
                if section_id in self.section_mapping or any(known in section_id for known in self.section_mapping.keys()):
                    self.sections[section_id] = element
                    sections.append(section_id)
                    logger.debug(f"Found doc section: {section_id}")
        
        # Method 3: Extract sections from sidebar navigation
        sidebar_links = self.soup.find_all('a', href=re.compile(r'^#'))
        for link in sidebar_links:
            href = link.get('href', '').lstrip('#')
            if href and href in self.section_mapping:
                # Find the corresponding content section
                content_element = self.soup.find(id=href)
                if content_element and href not in self.sections:
                    self.sections[href] = content_element
                    sections.append(href)
                    logger.debug(f"Found section from sidebar: {href}")
        
        # Method 4: Look for major content blocks that might be missing IDs
        if len(sections) < 10:  # We expect more sections
            # Look for divs with section headers
            headers = self.soup.find_all(class_=re.compile(r'sectionHeader'))
            for header in headers:
                header_text = header.get_text().strip().lower()
                section_id = self._map_header_to_section_id(header_text)
                if section_id and section_id not in self.sections:
                    # Find parent section
                    parent = header.find_parent('div', class_=re.compile(r'section'))
                    if parent:
                        self.sections[section_id] = parent
                        sections.append(section_id)
                        logger.debug(f"Found section by header text: {header_text} -> {section_id}")
        
        return sections
    
    def _extract_section_id_from_element(self, element: Tag) -> Optional[str]:
        """Extract section ID from element"""
        # Check for ID attribute
        if element.get('id'):
            return element.get('id')
        
        # Check for nearby anchor elements
        anchors = element.find_all('a', href=True)
        for anchor in anchors:
            href = anchor.get('href')
            if href and href.startswith('#'):
                section_id = href[1:]  # Remove the #
                if section_id in self.section_mapping:
                    return section_id
        
        return None
    
    def _extract_section_id_from_header(self, header: Tag) -> Optional[str]:
        """Extract section ID from header text"""
        header_text = header.get_text().strip().lower()
        
        # Map common header texts to section IDs
        header_mappings = {
            "introduction": "intro",
            "authentication": "authentication",
            "figma files": "files",
            "comments": "comments", 
            "users": "users",
            "version history": "version-history",
            "projects": "projects",
            "components and styles": "library-items",
            "webhooks v2": "webhooks_v2",
            "activity logs": "activity_logs",
            "discovery": "discovery",
            "payments": "payments",
            "variables": "variables",
            "dev resources": "dev-resources",
            "library analytics": "library-analytics",
            "errors": "errors",
            "scim api reference": "scim-api-guide",
            "changelog": "changelog"
        }
        
        for text, section_id in header_mappings.items():
            if text in header_text:
                return section_id
        
        return None
    
    async def extract_content(self, section_id: str) -> Optional[DocumentContent]:
        """Extract content from a specific section"""
        try:
            # Get the section element
            section_element = self.sections.get(section_id)
            if not section_element:
                logger.warning(f"Section not found: {section_id}")
                return None
            
            # Extract title
            title = self._extract_section_title(section_element, section_id)
            
            # Extract and clean content
            content_text = self._extract_clean_content(section_element)
            
            # Skip very short content
            if len(content_text) < 100:
                logger.debug(f"Skipping short content for section: {section_id}")
                return None
            
            # Create metadata
            metadata = self._create_metadata(section_id, title, content_text)
            
            return DocumentContent(content=content_text, metadata=metadata)
            
        except Exception as e:
            logger.error(f"Error extracting content from section {section_id}: {e}")
            return None
    
    def _extract_section_title(self, section_element: Tag, section_id: str) -> str:
        """Extract title from section element"""
        # Try to find header elements
        for tag in ['h1', 'h2', 'h3']:
            header = section_element.find(tag, class_=re.compile(r'sectionHeader|subsectionHeader'))
            if header:
                title = header.get_text().strip()
                if title:
                    return self._clean_title(title)
        
        # Try to find title in child elements
        title_elem = section_element.find(class_=re.compile(r'title|header'))
        if title_elem:
            title = title_elem.get_text().strip()
            if title:
                return self._clean_title(title)
        
        # Fallback to section mapping
        section_name = self.section_mapping.get(section_id, section_id)
        return section_name.replace('_', ' ').title()
    
    def _extract_clean_content(self, section_element: Tag) -> str:
        """Extract and clean content from section element"""
        # Create a copy to avoid modifying the original
        content_elem = BeautifulSoup(str(section_element), 'html.parser')
        
        # Remove unwanted elements
        for unwanted in content_elem.find_all([
            'script', 'style', 'nav', 'header', 'footer', 'button', 'input'
        ]):
            unwanted.decompose()
        
        # Remove unwanted classes and UI elements
        for unwanted in content_elem.find_all(class_=re.compile(
            r'sidebar|navigation|breadcrumb|cookie|newsletter|explorerInput|personalToken|button'
        )):
            unwanted.decompose()
        
        # Extract text content
        text_content = content_elem.get_text(separator=' ', strip=True)
        
        # Clean and normalize text - be more aggressive about keeping content
        words = text_content.split()
        cleaned_words = []
        
        for word in words:
            word = word.strip()
            # Keep most words unless they're obvious UI artifacts
            if (len(word) > 1 and 
                not any(pattern in word for pattern in self.skip_patterns) and
                not word.startswith('http') and  # Skip URLs for now
                word not in {'Get', 'What\'s', 'this?', 'My', 'apps', 'Create', 'new', 'app'}):
                cleaned_words.append(word)
        
        content = ' '.join(cleaned_words)
        
        # Additional cleanup - remove excessive whitespace and fix formatting
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        content = re.sub(r'\s*\.\s*', '. ', content)  # Fix periods
        content = re.sub(r'\s*,\s*', ', ', content)  # Fix commas
        
        return content.strip()
    
    def _clean_title(self, title: str) -> str:
        """Clean section titles"""
        # Remove common Figma suffixes
        title = title.replace(' | Figma for Developers', '')
        title = title.replace(' - Figma', '')
        title = title.replace('Figma API ', '')
        
        return title.strip()
    
    def _create_metadata(self, section_id: str, title: str, content: str) -> DocumentMetadata:
        """Create metadata for the section"""
        section_name = self.section_mapping.get(section_id, section_id)
        doc_type = self._determine_doc_type(section_id, title, content)
        tags = self._generate_tags(section_id, title, content)
        
        # Create a synthetic URL for this section
        url = f"{self.base_url}#{section_id}"
        
        return DocumentMetadata(
            framework="figma",
            source="Figma API Official Documentation (File)",
            doc_type=doc_type,
            title=title,
            url=url,
            section=section_name,
            subsection=section_id,
            version=self.version,
            language="en",
            tags=tags
        )
    
    def _determine_doc_type(self, section_id: str, title: str, content: str) -> str:
        """Determine document type based on section and content"""
        title_lower = title.lower()
        content_lower = content.lower()[:1000]
        
        if section_id == "intro" or "introduction" in title_lower:
            return "introduction"
        elif section_id == "authentication":
            return "authentication_guide"
        elif "endpoint" in content_lower or any(method in content_lower for method in ["get ", "post ", "put ", "delete "]):
            return "api_endpoint"
        elif "webhook" in section_id or "webhook" in title_lower:
            return "webhook_reference"
        elif "error" in section_id or "error" in title_lower:
            return "error_reference"
        elif "variable" in section_id or "token" in content_lower:
            return "design_tokens"
        elif "component" in content_lower or "style" in content_lower:
            return "design_system"
        elif "tutorial" in title_lower or "getting started" in title_lower:
            return "tutorial"
        else:
            return "api_reference"
    
    def _generate_tags(self, section_id: str, title: str, content: str) -> List[str]:
        """Generate relevant tags for the content"""
        tags = ["api", "rest_api", "design_tools", "collaboration", "file_extracted"]
        
        # Add section-specific tags
        if section_id == "authentication":
            tags.extend(["authentication", "oauth", "tokens", "security"])
        elif section_id == "files":
            tags.extend(["file_operations", "json", "nodes"])
        elif section_id == "comments":
            tags.extend(["comments", "collaboration"])
        elif section_id == "webhooks_v2":
            tags.extend(["webhooks", "real_time", "events"])
        elif "library" in section_id:
            tags.extend(["design_system", "components", "styles"])
        elif section_id == "variables":
            tags.extend(["design_tokens", "variables"])
        elif section_id == "errors":
            tags.extend(["error_handling", "troubleshooting"])
        
        # Add content-based tags
        content_lower = content.lower()[:1000]
        if any(method in content_lower for method in ["get ", "post ", "put ", "delete "]):
            tags.append("http_methods")
        if "json" in content_lower:
            tags.append("json")
        if "curl" in content_lower:
            tags.append("code_examples")
        if "rate limit" in content_lower:
            tags.append("rate_limiting")
        
        # Add difficulty level
        if any(term in title.lower() for term in ["introduction", "getting started"]):
            tags.append("beginner")
        elif any(term in title.lower() for term in ["advanced", "webhook", "scim"]):
            tags.append("advanced")
        else:
            tags.append("intermediate")
        
        return tags
    
    async def preprocess_content(self, content: str) -> str:
        """Clean Figma-specific content"""
        lines = content.split(' ')
        
        # Remove very short fragments and common UI text
        filtered_words = []
        for word in lines:
            word = word.strip()
            if (len(word) > 2 and 
                word not in {"Get", "What's", "this?", "My", "apps", "Create", "new", "app"}):
                filtered_words.append(word)
        
        return ' '.join(filtered_words)
    
    async def postprocess_metadata(self, metadata: DocumentMetadata) -> DocumentMetadata:
        """Enhance metadata"""
        # Add API version information
        if "v1" in metadata.url or "version 1" in metadata.title.lower():
            metadata.tags.append("api_v1")
        
        # Add comprehensive content tag
        metadata.tags.append("comprehensive_documentation")
        
        return metadata