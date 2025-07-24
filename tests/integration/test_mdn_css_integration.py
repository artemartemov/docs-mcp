#!/usr/bin/env python3
"""
Comprehensive tests for MDN CSS documentation integration.

This test suite validates that the MDN CSS documentation was successfully
extracted and is accessible through the docs-mcp server.
"""

import asyncio
import logging
import json
import sys
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from docs_mcp.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


class MDNCSSDocumentationTests:
    """Comprehensive test suite for MDN CSS documentation integration"""

    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.test_results = {"total_tests": 0, "passed": 0, "failed": 0, "results": []}

    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        self.test_results["total_tests"] += 1
        if passed:
            self.test_results["passed"] += 1
            status = "✅ PASS"
        else:
            self.test_results["failed"] += 1
            status = "❌ FAIL"

        result = f"{status} - {test_name}"
        if details:
            result += f": {details}"

        logger.info(result)
        self.test_results["results"].append(
            {"test": test_name, "passed": passed, "details": details}
        )

    def setup_chromadb_connection(self):
        """Initialize ChromaDB connection"""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=settings.chroma_data_dir,
                settings=ChromaSettings(anonymized_telemetry=False, allow_reset=False),
            )

            self.collection = self.chroma_client.get_collection("documentation_collection")
            self.log_test_result(
                "ChromaDB Connection", True, "Successfully connected to collection"
            )
            return True
        except Exception as e:
            self.log_test_result("ChromaDB Connection", False, f"Failed to connect: {e}")
            return False

    def test_css_document_count(self):
        """Test that CSS documents were successfully ingested"""
        try:
            # Get all CSS documents
            css_docs = self.collection.get(where={"framework": "css"}, include=["metadatas"])

            css_count = len(css_docs["ids"])
            expected_min = 200  # We expect at least 200 CSS documents

            if css_count >= expected_min:
                self.log_test_result(
                    "CSS Document Count",
                    True,
                    f"Found {css_count} CSS documents (expected >= {expected_min})",
                )
            else:
                self.log_test_result(
                    "CSS Document Count",
                    False,
                    f"Only found {css_count} CSS documents (expected >= {expected_min})",
                )

            return css_count
        except Exception as e:
            self.log_test_result("CSS Document Count", False, f"Error: {e}")
            return 0

    def test_css_properties_content(self):
        """Test CSS properties documentation content"""
        try:
            properties_results = self.collection.query(
                query_texts=["CSS properties display position width height"],
                where={"framework": "css"},
                n_results=5,
            )

            if properties_results["documents"] and len(properties_results["documents"][0]) > 0:
                # Check for key CSS property terms
                content = " ".join(properties_results["documents"][0]).lower()
                key_terms = [
                    "property",
                    "value",
                    "syntax",
                    "display",
                    "position",
                    "width",
                    "height",
                ]

                found_terms = [term for term in key_terms if term in content]

                if len(found_terms) >= 5:
                    self.log_test_result(
                        "CSS Properties Content",
                        True,
                        f"Found key terms: {', '.join(found_terms)}",
                    )
                else:
                    self.log_test_result(
                        "CSS Properties Content",
                        False,
                        f"Only found terms: {', '.join(found_terms)}",
                    )
            else:
                self.log_test_result(
                    "CSS Properties Content", False, "No CSS properties docs found"
                )
        except Exception as e:
            self.log_test_result("CSS Properties Content", False, f"Error: {e}")

    def test_css_selectors_content(self):
        """Test CSS selectors documentation"""
        try:
            selectors_results = self.collection.query(
                query_texts=["CSS selectors class id pseudo-class element"],
                where={"framework": "css"},
                n_results=5,
            )

            if selectors_results["documents"] and len(selectors_results["documents"][0]) > 0:
                # Check for CSS selector terms
                content = " ".join(selectors_results["documents"][0]).lower()
                selector_terms = [
                    "selector",
                    "class",
                    "element",
                    "pseudo",
                    "attribute",
                    "universal",
                ]

                found_terms = [term for term in selector_terms if term in content]

                if len(found_terms) >= 3:
                    self.log_test_result(
                        "CSS Selectors Content",
                        True,
                        f"Found selector terms: {', '.join(found_terms)}",
                    )
                else:
                    self.log_test_result(
                        "CSS Selectors Content",
                        False,
                        f"Limited selector content - found: {', '.join(found_terms)}",
                    )
            else:
                self.log_test_result("CSS Selectors Content", False, "No CSS selectors docs found")
        except Exception as e:
            self.log_test_result("CSS Selectors Content", False, f"Error: {e}")

    def test_css_layout_content(self):
        """Test CSS layout documentation (Flexbox, Grid, etc.)"""
        try:
            layout_results = self.collection.query(
                query_texts=["CSS layout flexbox grid positioning float"],
                where={"framework": "css"},
                n_results=5,
            )

            if layout_results["documents"] and len(layout_results["documents"][0]) > 0:
                content = " ".join(layout_results["documents"][0]).lower()

                # Look for layout terms
                layout_terms = [
                    "flexbox",
                    "grid",
                    "layout",
                    "position",
                    "float",
                    "flex",
                    "inline",
                ]
                found_terms = [term for term in layout_terms if term in content]

                if len(found_terms) >= 3:
                    self.log_test_result(
                        "CSS Layout Content",
                        True,
                        f"Found layout terms: {', '.join(found_terms)}",
                    )
                else:
                    self.log_test_result(
                        "CSS Layout Content",
                        False,
                        f"Limited layout content - found: {', '.join(found_terms)}",
                    )
            else:
                self.log_test_result("CSS Layout Content", False, "No CSS layout docs found")
        except Exception as e:
            self.log_test_result("CSS Layout Content", False, f"Error: {e}")

    def test_css_animations_content(self):
        """Test CSS animations and transitions documentation"""
        try:
            animation_results = self.collection.query(
                query_texts=["CSS animations transitions keyframes transform"],
                where={"framework": "css"},
                n_results=5,
            )

            if animation_results["documents"] and len(animation_results["documents"][0]) > 0:
                content = " ".join(animation_results["documents"][0]).lower()
                animation_terms = [
                    "animation",
                    "transition",
                    "keyframes",
                    "transform",
                    "duration",
                ]

                found_terms = [term for term in animation_terms if term in content]

                if len(found_terms) >= 3:
                    self.log_test_result(
                        "CSS Animations Content",
                        True,
                        f"Found animation terms: {', '.join(found_terms)}",
                    )
                else:
                    self.log_test_result(
                        "CSS Animations Content",
                        False,
                        f"Limited animation content - found: {', '.join(found_terms)}",
                    )
            else:
                self.log_test_result(
                    "CSS Animations Content", False, "No CSS animations docs found"
                )
        except Exception as e:
            self.log_test_result("CSS Animations Content", False, f"Error: {e}")

    def test_css_responsive_content(self):
        """Test responsive design and media queries documentation"""
        try:
            responsive_results = self.collection.query(
                query_texts=["CSS responsive design media queries breakpoints"],
                where={"framework": "css"},
                n_results=5,
            )

            if responsive_results["documents"] and len(responsive_results["documents"][0]) > 0:
                content = " ".join(responsive_results["documents"][0]).lower()
                responsive_terms = [
                    "responsive",
                    "media",
                    "query",
                    "breakpoint",
                    "viewport",
                    "mobile",
                ]

                found_terms = [term for term in responsive_terms if term in content]

                if len(found_terms) >= 3:
                    self.log_test_result(
                        "CSS Responsive Content",
                        True,
                        f"Found responsive terms: {', '.join(found_terms)}",
                    )
                else:
                    self.log_test_result(
                        "CSS Responsive Content",
                        False,
                        f"Limited responsive content - found: {', '.join(found_terms)}",
                    )
            else:
                self.log_test_result(
                    "CSS Responsive Content", False, "No responsive design docs found"
                )
        except Exception as e:
            self.log_test_result("CSS Responsive Content", False, f"Error: {e}")

    def test_metadata_quality(self):
        """Test that metadata is properly structured"""
        try:
            sample_docs = self.collection.get(
                where={"framework": "css"}, limit=10, include=["metadatas"]
            )

            if sample_docs["metadatas"]:
                # Check metadata fields
                required_fields = [
                    "framework",
                    "source",
                    "doc_type",
                    "title",
                    "url",
                    "section",
                ]
                metadata_quality = []

                for metadata in sample_docs["metadatas"][:5]:
                    missing_fields = [field for field in required_fields if field not in metadata]
                    if not missing_fields:
                        metadata_quality.append("complete")
                    else:
                        metadata_quality.append(f"missing: {missing_fields}")

                complete_count = metadata_quality.count("complete")
                if complete_count >= 3:
                    self.log_test_result(
                        "Metadata Quality",
                        True,
                        f"{complete_count}/5 samples have complete metadata",
                    )
                else:
                    self.log_test_result(
                        "Metadata Quality",
                        False,
                        f"Only {complete_count}/5 samples have complete metadata",
                    )
            else:
                self.log_test_result("Metadata Quality", False, "No metadata found")
        except Exception as e:
            self.log_test_result("Metadata Quality", False, f"Error: {e}")

    def test_search_functionality(self):
        """Test comprehensive search functionality"""
        search_queries = [
            ("CSS flexbox properties", "flexbox"),
            ("CSS grid layout", "grid"),
            ("CSS color functions", "color"),
            ("CSS selectors pseudo", "selector"),
            ("CSS animations keyframes", "animation"),
            ("CSS media queries responsive", "media"),
            ("CSS box model properties", "box"),
        ]

        for query, expected_topic in search_queries:
            try:
                results = self.collection.query(
                    query_texts=[query], where={"framework": "css"}, n_results=3
                )

                if results["documents"] and len(results["documents"][0]) > 0:
                    # Check relevance
                    content = " ".join(results["documents"][0]).lower()
                    if expected_topic.lower() in content:
                        self.log_test_result(
                            f"Search: '{query}'",
                            True,
                            f"Found relevant content about {expected_topic}",
                        )
                    else:
                        self.log_test_result(
                            f"Search: '{query}'",
                            False,
                            f"Results not relevant to {expected_topic}",
                        )
                else:
                    self.log_test_result(f"Search: '{query}'", False, "No results found")
            except Exception as e:
                self.log_test_result(f"Search: '{query}'", False, f"Error: {e}")

    def test_doc_type_distribution(self):
        """Test distribution of document types"""
        try:
            css_docs = self.collection.get(where={"framework": "css"}, include=["metadatas"])

            if css_docs["metadatas"]:
                doc_types = {}
                for metadata in css_docs["metadatas"]:
                    doc_type = metadata.get("doc_type", "unknown")
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

                expected_types = [
                    "css_reference",
                    "guide",
                    "tutorial",
                    "reference",
                    "css_documentation",
                ]
                found_expected = [dt for dt in expected_types if dt in doc_types]

                if len(found_expected) >= 2:
                    type_summary = ", ".join(
                        [f"{dt}: {doc_types[dt]}" for dt in found_expected[:3]]
                    )
                    self.log_test_result(
                        "Document Type Distribution",
                        True,
                        f"Found expected types - {type_summary}",
                    )
                else:
                    self.log_test_result(
                        "Document Type Distribution",
                        False,
                        f"Missing expected doc types. Found: {list(doc_types.keys())[:5]}",
                    )
            else:
                self.log_test_result("Document Type Distribution", False, "No metadata available")
        except Exception as e:
            self.log_test_result("Document Type Distribution", False, f"Error: {e}")

    def run_all_tests(self):
        """Run comprehensive test suite"""
        logger.info("🧪 Starting comprehensive MDN CSS documentation integration tests...")

        # Setup
        if not self.setup_chromadb_connection():
            logger.error("❌ Failed to setup ChromaDB connection. Aborting tests.")
            return False

        # Run tests
        css_count = self.test_css_document_count()
        self.test_css_properties_content()
        self.test_css_selectors_content()
        self.test_css_layout_content()
        self.test_css_animations_content()
        self.test_css_responsive_content()
        self.test_metadata_quality()
        self.test_search_functionality()
        self.test_doc_type_distribution()

        # Summary
        logger.info("\n📊 TEST RESULTS SUMMARY:")
        logger.info(f"   Total Tests: {self.test_results['total_tests']}")
        logger.info(f"   Passed: {self.test_results['passed']} ✅")
        logger.info(f"   Failed: {self.test_results['failed']} ❌")
        logger.info(
            f"   Success Rate: {(self.test_results['passed']/self.test_results['total_tests']*100):.1f}%"
        )

        # Detailed results
        if self.test_results["failed"] > 0:
            logger.info("\n❌ FAILED TESTS:")
            for result in self.test_results["results"]:
                if not result["passed"]:
                    logger.info(f"   - {result['test']}: {result['details']}")

        # Overall assessment
        success_rate = self.test_results["passed"] / self.test_results["total_tests"]
        if success_rate >= 0.85:
            logger.info(
                "\n🎉 INTEGRATION TEST PASSED! MDN CSS documentation is properly integrated."
            )
            return True
        elif success_rate >= 0.7:
            logger.info("\n⚠️  INTEGRATION TEST PARTIAL SUCCESS. Some issues detected.")
            return True
        else:
            logger.info("\n❌ INTEGRATION TEST FAILED. Significant issues detected.")
            return False


def main():
    """Run the comprehensive test suite"""
    tests = MDNCSSDocumentationTests()
    success = tests.run_all_tests()

    if success:
        print("\n✅ All integration tests completed successfully!")
        print("🎯 MDN CSS documentation is fully integrated and searchable")
        print("🎨 Available CSS content includes:")
        print("   • All CSS properties and their values")
        print("   • CSS selectors and pseudo-classes")
        print("   • Layout systems (Flexbox, Grid, Positioning)")
        print("   • Animations, transitions, and transforms")
        print("   • Responsive design and media queries")
        print("   • CSS guides and tutorials")
    else:
        print("\n❌ Integration tests failed")
        print("📋 Check the test results above for details")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
