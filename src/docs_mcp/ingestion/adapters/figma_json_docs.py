"""
Figma API Documentation Adapter for Structured JSON.

Processes the structured JSON file created from figmaapi.txt to extract
comprehensive Figma API documentation efficiently.
"""

import asyncio
import json
import logging
from typing import List, Optional
from pathlib import Path

from ..base import BaseDocumentationSource, DocumentContent, DocumentMetadata

logger = logging.getLogger(__name__)


class FigmaJsonDocsSource(BaseDocumentationSource):
    """Figma API documentation source from structured JSON file"""

    def __init__(self, json_file_path: str, version: str = "latest"):
        self.json_file_path = Path(json_file_path)
        self.version = version
        base_url = "https://www.figma.com/developers/api"
        super().__init__(f"Figma API {version} JSON Docs", base_url)

        # JSON data
        self.json_data: Optional[dict] = None
        self.sections: List[dict] = []

        # Configure for fast local processing
        self.rate_limit_delay = 0.0  # No rate limiting for local files
        self.batch_size = 50

    def get_framework_name(self) -> str:
        return "figma"

    async def discover_content(self) -> List[str]:
        """
        Discover content sections from the JSON file.
        Returns section identifiers.
        """
        logger.info(f"🔍 Loading Figma API documentation from {self.json_file_path}")

        try:
            # Read the JSON file
            if not self.json_file_path.exists():
                logger.error(f"File not found: {self.json_file_path}")
                return []

            with open(self.json_file_path, "r", encoding="utf-8") as f:
                self.json_data = json.load(f)

            # Extract sections
            self.sections = self.json_data.get("sections", [])

            logger.info(f"📄 Loaded JSON file with {len(self.sections)} sections")
            logger.info(f"📝 Total words: {self.json_data.get('total_words', 0):,}")

            # Filter and deduplicate sections
            unique_sections = {}
            for section in self.sections:
                section_id = section.get("id")
                word_count = section.get("word_count", 0)

                # Only include sections with meaningful content
                if section_id and word_count >= 25:  # Minimum word count threshold
                    # If we've seen this section before, keep the one with more content
                    if (
                        section_id not in unique_sections
                        or word_count > unique_sections[section_id]["word_count"]
                    ):
                        unique_sections[section_id] = section

            # Convert to list of section IDs
            section_ids = list(unique_sections.keys())
            self.sections = list(unique_sections.values())

            logger.info(f"📋 Found {len(section_ids)} unique sections after filtering")

            # Log section breakdown by type
            section_types = {}
            for section in self.sections:
                section_type = self._categorize_section(section["id"])
                section_types[section_type] = section_types.get(section_type, 0) + 1

            logger.info("📊 Section breakdown by type:")
            for section_type, count in sorted(section_types.items()):
                logger.info(f"   {section_type}: {count} sections")

            return section_ids

        except Exception as e:
            logger.error(f"❌ Failed to load JSON file: {e}")
            return []

    def _categorize_section(self, section_id: str) -> str:
        """Categorize section by type"""
        section_id_lower = section_id.lower()

        if any(
            term in section_id_lower for term in ["intro", "authentication", "auth"]
        ):
            return "getting_started"
        elif any(term in section_id_lower for term in ["file", "node", "image"]):
            return "files_api"
        elif any(term in section_id_lower for term in ["comment", "reaction"]):
            return "comments_api"
        elif any(term in section_id_lower for term in ["user", "team", "project"]):
            return "users_teams"
        elif any(
            term in section_id_lower for term in ["component", "style", "library"]
        ):
            return "design_system"
        elif any(term in section_id_lower for term in ["variable", "token"]):
            return "design_tokens"
        elif any(term in section_id_lower for term in ["webhook", "activity"]):
            return "webhooks_events"
        elif any(term in section_id_lower for term in ["dev-resource", "dev_resource"]):
            return "dev_resources"
        elif any(
            term in section_id_lower
            for term in ["payment", "scim", "discovery", "analytics"]
        ):
            return "enterprise_features"
        elif any(term in section_id_lower for term in ["type", "prop"]):
            return "type_definitions"
        elif any(
            term in section_id_lower
            for term in ["endpoint", "get-", "post-", "put-", "delete-"]
        ):
            return "api_endpoints"
        elif any(term in section_id_lower for term in ["error", "changelog"]):
            return "reference"
        else:
            return "other"

    async def extract_content(self, section_id: str) -> Optional[DocumentContent]:
        """Extract content from a specific section"""
        try:
            # Find the section data
            section_data = None
            for section in self.sections:
                if section.get("id") == section_id:
                    section_data = section
                    break

            if not section_data:
                logger.warning(f"Section not found: {section_id}")
                return None

            # Extract content components
            title = section_data.get(
                "title", section_id.replace("-", " ").replace("_", " ").title()
            )
            main_content = section_data.get("main_content", "")
            subsections = section_data.get("subsections", [])
            code_examples = section_data.get("code_examples", [])
            tables = section_data.get("tables", [])

            # Build comprehensive content
            content_parts = []

            # Add main content
            if main_content.strip():
                content_parts.append(main_content.strip())

            # Add subsections
            for subsection in subsections:
                sub_title = subsection.get("title", "")
                sub_content = subsection.get("content", "")
                if sub_title and sub_content:
                    content_parts.append(f"\n## {sub_title}\n{sub_content}")

            # Add code examples
            if code_examples:
                content_parts.append("\n## Code Examples")
                for example in code_examples:
                    example_content = example.get("content", "")
                    example_type = example.get("type", "code")
                    if example_content:
                        content_parts.append(
                            f"\n### {example_type.title()}\n```\n{example_content}\n```"
                        )

            # Add tables
            if tables:
                content_parts.append("\n## Reference Tables")
                for i, table in enumerate(tables):
                    headers = table.get("headers", [])
                    rows = table.get("rows", [])
                    if headers and rows:
                        content_parts.append(f"\n### Table {i+1}")
                        # Simple table format
                        content_parts.append(" | ".join(headers))
                        content_parts.append(" | ".join(["---"] * len(headers)))
                        for row in rows:
                            if len(row) == len(headers):
                                content_parts.append(" | ".join(row))

            final_content = "\n".join(content_parts).strip()

            # Skip very short content
            if len(final_content) < 50:
                logger.debug(f"Skipping short content for section: {section_id}")
                return None

            # Create metadata
            metadata = self._create_metadata(section_id, title, final_content)

            return DocumentContent(content=final_content, metadata=metadata)

        except Exception as e:
            logger.error(f"Error extracting content from section {section_id}: {e}")
            return None

    def _create_metadata(
        self, section_id: str, title: str, content: str
    ) -> DocumentMetadata:
        """Create metadata for the section"""
        section_category = self._categorize_section(section_id)
        doc_type = self._determine_doc_type(section_id, title, content)
        tags = self._generate_tags(section_id, title, content)

        # Create a synthetic URL for this section
        url = f"{self.base_url}#{section_id}"

        return DocumentMetadata(
            framework="figma",
            source="Figma API Official Documentation (JSON)",
            doc_type=doc_type,
            title=title,
            url=url,
            section=section_category,
            subsection=section_id,
            version=self.version,
            language="en",
            tags=tags,
        )

    def _determine_doc_type(self, section_id: str, title: str, content: str) -> str:
        """Determine document type based on section and content"""
        section_id_lower = section_id.lower()
        title_lower = title.lower()
        content_lower = content.lower()[:1000]

        if "intro" in section_id_lower or "introduction" in title_lower:
            return "introduction"
        elif "auth" in section_id_lower:
            return "authentication_guide"
        elif any(
            method in content_lower for method in ["get ", "post ", "put ", "delete "]
        ):
            return "api_endpoint"
        elif any(term in section_id_lower for term in ["webhook", "activity"]):
            return "webhook_reference"
        elif any(term in section_id_lower for term in ["error", "changelog"]):
            return "reference"
        elif any(term in section_id_lower for term in ["type", "prop"]):
            return "type_definition"
        elif any(term in section_id_lower for term in ["variable", "token"]):
            return "design_tokens"
        elif any(term in section_id_lower for term in ["component", "style"]):
            return "design_system"
        elif "tutorial" in title_lower or "getting started" in title_lower:
            return "tutorial"
        else:
            return "api_reference"

    def _generate_tags(self, section_id: str, title: str, content: str) -> List[str]:
        """Generate relevant tags for the content"""
        tags = ["api", "rest_api", "design_tools", "collaboration", "json_extracted"]

        section_id_lower = section_id.lower()
        content_lower = content.lower()[:1000]

        # Add section-specific tags
        if "auth" in section_id_lower:
            tags.extend(["authentication", "oauth", "tokens", "security"])
        elif "file" in section_id_lower:
            tags.extend(["file_operations", "json", "nodes"])
        elif "comment" in section_id_lower:
            tags.extend(["comments", "collaboration"])
        elif "webhook" in section_id_lower:
            tags.extend(["webhooks", "real_time", "events"])
        elif "component" in section_id_lower or "style" in section_id_lower:
            tags.extend(["design_system", "components", "styles"])
        elif "variable" in section_id_lower:
            tags.extend(["design_tokens", "variables"])
        elif "error" in section_id_lower:
            tags.extend(["error_handling", "troubleshooting"])

        # Add content-based tags
        if any(
            method in content_lower for method in ["get ", "post ", "put ", "delete "]
        ):
            tags.append("http_methods")
        if "json" in content_lower:
            tags.append("json")
        if "curl" in content_lower:
            tags.append("code_examples")
        if "rate limit" in content_lower:
            tags.append("rate_limiting")

        # Add API-specific tags
        if any(
            term in content_lower for term in ["endpoint", "api", "request", "response"]
        ):
            tags.append("api_documentation")
        if any(term in content_lower for term in ["type", "property", "field"]):
            tags.append("data_structures")

        # Add difficulty level
        if any(term in title.lower() for term in ["introduction", "getting started"]):
            tags.append("beginner")
        elif any(
            term in title.lower()
            for term in ["advanced", "webhook", "scim", "enterprise"]
        ):
            tags.append("advanced")
        else:
            tags.append("intermediate")

        return tags

    async def preprocess_content(self, content: str) -> str:
        """Clean content (minimal processing needed since JSON is already clean)"""
        # The JSON extraction already cleaned the content, so minimal processing needed
        lines = content.split("\n")
        filtered_lines = []

        for line in lines:
            line = line.strip()
            # Skip very short lines unless they're headers or important structural elements
            if len(line) > 5 or line.startswith("#") or line.startswith("```"):
                filtered_lines.append(line)

        return "\n".join(filtered_lines)

    async def postprocess_metadata(
        self, metadata: DocumentMetadata
    ) -> DocumentMetadata:
        """Enhance metadata"""
        # Add comprehensive documentation tag
        metadata.tags.append("comprehensive_documentation")
        metadata.tags.append("structured_extraction")

        # Add API version information
        if "v1" in metadata.url or "version 1" in metadata.title.lower():
            metadata.tags.append("api_v1")

        return metadata
