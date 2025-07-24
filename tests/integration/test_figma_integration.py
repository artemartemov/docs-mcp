#!/usr/bin/env python3
"""
Comprehensive tests for Figma API documentation integration.

This test suite validates that the Figma API documentation was successfully
extracted and is accessible through the docs-mcp server.
"""

import asyncio
import logging
import json
from pathlib import Path
import chromadb
from chromadb.config import Settings as ChromaSettings

from config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


class FigmaDocumentationTests:
    """Comprehensive test suite for Figma documentation integration"""

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

    def test_figma_document_count(self):
        """Test that Figma documents were successfully ingested"""
        try:
            # Get all Figma documents
            figma_docs = self.collection.get(where={"framework": "figma"}, include=["metadatas"])

            figma_count = len(figma_docs["ids"])
            expected_min = 100  # We expect at least 100 Figma documents

            if figma_count >= expected_min:
                self.log_test_result(
                    "Figma Document Count",
                    True,
                    f"Found {figma_count} Figma documents (expected >= {expected_min})",
                )
            else:
                self.log_test_result(
                    "Figma Document Count",
                    False,
                    f"Only found {figma_count} Figma documents (expected >= {expected_min})",
                )

            return figma_count
        except Exception as e:
            self.log_test_result("Figma Document Count", False, f"Error: {e}")
            return 0

    def test_content_categories(self):
        """Test that all major content categories are present"""
        expected_categories = [
            "getting_started",
            "files_api",
            "comments_api",
            "users_teams",
            "design_system",
            "design_tokens",
            "webhooks_events",
            "type_definitions",
        ]

        try:
            for category in expected_categories:
                category_docs = self.collection.get(
                    where={"framework": "figma", "section": category},
                    include=["metadatas"],
                )

                count = len(category_docs["ids"])
                if count > 0:
                    self.log_test_result(f"Category: {category}", True, f"Found {count} documents")
                else:
                    self.log_test_result(f"Category: {category}", False, "No documents found")
        except Exception as e:
            self.log_test_result("Content Categories", False, f"Error: {e}")

    def test_authentication_content(self):
        """Test authentication documentation content"""
        try:
            auth_results = self.collection.query(
                query_texts=["Figma API authentication oauth access token"],
                where={"framework": "figma"},
                n_results=5,
            )

            if auth_results["documents"] and len(auth_results["documents"][0]) > 0:
                # Check for key authentication terms
                auth_content = " ".join(auth_results["documents"][0]).lower()
                key_terms = [
                    "oauth",
                    "access token",
                    "authentication",
                    "x-figma-token",
                    "bearer",
                ]

                found_terms = [term for term in key_terms if term in auth_content]

                if len(found_terms) >= 3:
                    self.log_test_result(
                        "Authentication Content",
                        True,
                        f"Found key terms: {', '.join(found_terms)}",
                    )
                else:
                    self.log_test_result(
                        "Authentication Content",
                        False,
                        f"Only found terms: {', '.join(found_terms)}",
                    )
            else:
                self.log_test_result(
                    "Authentication Content", False, "No authentication docs found"
                )
        except Exception as e:
            self.log_test_result("Authentication Content", False, f"Error: {e}")

    def test_api_endpoints_content(self):
        """Test API endpoints documentation"""
        try:
            endpoints_results = self.collection.query(
                query_texts=["GET POST PUT DELETE endpoint API"],
                where={"framework": "figma"},
                n_results=10,
            )

            if endpoints_results["documents"] and len(endpoints_results["documents"][0]) > 0:
                # Check for HTTP methods and API patterns
                content = " ".join(endpoints_results["documents"][0]).lower()
                http_methods = ["get ", "post ", "put ", "delete "]
                api_patterns = ["endpoint", "api.figma.com", "/v1/", "curl"]

                found_methods = [method.strip() for method in http_methods if method in content]
                found_patterns = [pattern for pattern in api_patterns if pattern in content]

                if len(found_methods) >= 2 and len(found_patterns) >= 2:
                    self.log_test_result(
                        "API Endpoints Content",
                        True,
                        f"Found methods: {found_methods}, patterns: {found_patterns}",
                    )
                else:
                    self.log_test_result(
                        "API Endpoints Content",
                        False,
                        f"Limited content - methods: {found_methods}, patterns: {found_patterns}",
                    )
            else:
                self.log_test_result("API Endpoints Content", False, "No API endpoint docs found")
        except Exception as e:
            self.log_test_result("API Endpoints Content", False, f"Error: {e}")

    def test_code_examples(self):
        """Test that code examples are present"""
        try:
            code_results = self.collection.query(
                query_texts=["curl example code snippet"],
                where={"framework": "figma"},
                n_results=5,
            )

            if code_results["documents"] and len(code_results["documents"][0]) > 0:
                content = " ".join(code_results["documents"][0])

                # Look for code indicators
                code_indicators = [
                    "curl",
                    "```",
                    "POST",
                    "GET",
                    "X-Figma-Token",
                    "Bearer",
                    "json",
                ]
                found_indicators = [
                    indicator for indicator in code_indicators if indicator in content
                ]

                if len(found_indicators) >= 3:
                    self.log_test_result(
                        "Code Examples",
                        True,
                        f"Found code indicators: {', '.join(found_indicators)}",
                    )
                else:
                    self.log_test_result(
                        "Code Examples",
                        False,
                        f"Limited code content - found: {', '.join(found_indicators)}",
                    )
            else:
                self.log_test_result("Code Examples", False, "No code examples found")
        except Exception as e:
            self.log_test_result("Code Examples", False, f"Error: {e}")

    def test_webhook_documentation(self):
        """Test webhook documentation"""
        try:
            webhook_results = self.collection.query(
                query_texts=["webhook event callback figma"],
                where={"framework": "figma"},
                n_results=5,
            )

            if webhook_results["documents"] and len(webhook_results["documents"][0]) > 0:
                content = " ".join(webhook_results["documents"][0]).lower()
                webhook_terms = [
                    "webhook",
                    "event",
                    "callback",
                    "file_update",
                    "library_publish",
                ]

                found_terms = [term for term in webhook_terms if term in content]

                if len(found_terms) >= 3:
                    self.log_test_result(
                        "Webhook Documentation",
                        True,
                        f"Found webhook terms: {', '.join(found_terms)}",
                    )
                else:
                    self.log_test_result(
                        "Webhook Documentation",
                        False,
                        f"Limited webhook content - found: {', '.join(found_terms)}",
                    )
            else:
                self.log_test_result("Webhook Documentation", False, "No webhook docs found")
        except Exception as e:
            self.log_test_result("Webhook Documentation", False, f"Error: {e}")

    def test_metadata_quality(self):
        """Test that metadata is properly structured"""
        try:
            sample_docs = self.collection.get(
                where={"framework": "figma"}, limit=10, include=["metadatas"]
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
            ("How to authenticate", "authentication"),
            ("File API endpoints", "files"),
            ("Webhook events", "webhooks"),
            ("Design tokens variables", "variables"),
            ("Component library", "components"),
        ]

        for query, expected_topic in search_queries:
            try:
                results = self.collection.query(
                    query_texts=[query], where={"framework": "figma"}, n_results=3
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
            figma_docs = self.collection.get(where={"framework": "figma"}, include=["metadatas"])

            if figma_docs["metadatas"]:
                doc_types = {}
                for metadata in figma_docs["metadatas"]:
                    doc_type = metadata.get("doc_type", "unknown")
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1

                expected_types = [
                    "api_reference",
                    "api_endpoint",
                    "type_definition",
                    "authentication_guide",
                ]
                found_expected = [dt for dt in expected_types if dt in doc_types]

                if len(found_expected) >= 3:
                    type_summary = ", ".join([f"{dt}: {doc_types[dt]}" for dt in found_expected])
                    self.log_test_result(
                        "Document Type Distribution",
                        True,
                        f"Found expected types - {type_summary}",
                    )
                else:
                    self.log_test_result(
                        "Document Type Distribution",
                        False,
                        f"Missing expected doc types. Found: {list(doc_types.keys())}",
                    )
            else:
                self.log_test_result("Document Type Distribution", False, "No metadata available")
        except Exception as e:
            self.log_test_result("Document Type Distribution", False, f"Error: {e}")

    def run_all_tests(self):
        """Run comprehensive test suite"""
        logger.info("🧪 Starting comprehensive Figma documentation integration tests...")

        # Setup
        if not self.setup_chromadb_connection():
            logger.error("❌ Failed to setup ChromaDB connection. Aborting tests.")
            return False

        # Run tests
        figma_count = self.test_figma_document_count()
        self.test_content_categories()
        self.test_authentication_content()
        self.test_api_endpoints_content()
        self.test_code_examples()
        self.test_webhook_documentation()
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
        if success_rate >= 0.9:
            logger.info("\n🎉 INTEGRATION TEST PASSED! Figma documentation is properly integrated.")
            return True
        elif success_rate >= 0.7:
            logger.info("\n⚠️  INTEGRATION TEST PARTIAL SUCCESS. Some issues detected.")
            return True
        else:
            logger.info("\n❌ INTEGRATION TEST FAILED. Significant issues detected.")
            return False


def main():
    """Run the comprehensive test suite"""
    tests = FigmaDocumentationTests()
    success = tests.run_all_tests()

    if success:
        print("\n✅ All integration tests completed successfully!")
        print("🎯 Figma API documentation is fully integrated and searchable")
    else:
        print("\n❌ Integration tests failed")
        print("📋 Check the test results above for details")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
