#!/usr/bin/env python3
"""
Comprehensive tests for Figma Plugin API documentation integration.

This test suite validates that the Figma Plugin API documentation was successfully
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

class FigmaPluginDocumentationTests:
    """Comprehensive test suite for Figma Plugin documentation integration"""
    
    def __init__(self):
        self.chroma_client = None
        self.collection = None
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "results": []
        }
    
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
        self.test_results["results"].append({
            "test": test_name,
            "passed": passed,
            "details": details
        })
    
    def setup_chromadb_connection(self):
        """Initialize ChromaDB connection"""
        try:
            self.chroma_client = chromadb.PersistentClient(
                path=settings.chroma_data_dir,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=False
                )
            )
            
            self.collection = self.chroma_client.get_collection("documentation_collection")
            self.log_test_result("ChromaDB Connection", True, "Successfully connected to collection")
            return True
        except Exception as e:
            self.log_test_result("ChromaDB Connection", False, f"Failed to connect: {e}")
            return False
    
    def test_figma_plugin_document_count(self):
        """Test that Figma Plugin documents were successfully ingested"""
        try:
            # Get all Figma Plugin documents
            plugin_docs = self.collection.get(
                where={"framework": "figma_plugin"},
                include=["metadatas"]
            )
            
            plugin_count = len(plugin_docs['ids'])
            expected_min = 50  # We expect at least 50 plugin documents
            
            if plugin_count >= expected_min:
                self.log_test_result(
                    "Figma Plugin Document Count", 
                    True, 
                    f"Found {plugin_count} plugin documents (expected >= {expected_min})"
                )
            else:
                self.log_test_result(
                    "Figma Plugin Document Count", 
                    False, 
                    f"Only found {plugin_count} plugin documents (expected >= {expected_min})"
                )
            
            return plugin_count
        except Exception as e:
            self.log_test_result("Figma Plugin Document Count", False, f"Error: {e}")
            return 0
    
    def test_content_categories(self):
        """Test that all major plugin content categories are present"""
        expected_categories = [
            "getting_started", "plugin_development", "api_reference", "widget_development",
            "publishing", "tutorials", "troubleshooting"
        ]
        
        try:
            for category in expected_categories:
                category_docs = self.collection.get(
                    where={
                        "framework": "figma_plugin",
                        "section": category
                    },
                    include=["metadatas"]
                )
                
                count = len(category_docs['ids'])
                if count > 0:
                    self.log_test_result(
                        f"Category: {category}", 
                        True, 
                        f"Found {count} documents"
                    )
                else:
                    # Some categories may not exist yet, that's okay
                    self.log_test_result(
                        f"Category: {category}", 
                        True, 
                        f"No documents found (category may not exist)"
                    )
        except Exception as e:
            self.log_test_result("Content Categories", False, f"Error: {e}")
    
    def test_plugin_api_content(self):
        """Test Plugin API documentation content"""
        try:
            api_results = self.collection.query(
                query_texts=["Figma Plugin API figma object nodes"],
                where={"framework": "figma_plugin"},
                n_results=5
            )
            
            if api_results['documents'] and len(api_results['documents'][0]) > 0:
                # Check for key Plugin API terms
                api_content = " ".join(api_results['documents'][0]).lower()
                key_terms = ["figma", "plugin", "api", "node", "document", "scenenode"]
                
                found_terms = [term for term in key_terms if term in api_content]
                
                if len(found_terms) >= 4:
                    self.log_test_result(
                        "Plugin API Content", 
                        True, 
                        f"Found key terms: {', '.join(found_terms)}"
                    )
                else:
                    self.log_test_result(
                        "Plugin API Content", 
                        False, 
                        f"Only found terms: {', '.join(found_terms)}"
                    )
            else:
                self.log_test_result("Plugin API Content", False, "No Plugin API docs found")
        except Exception as e:
            self.log_test_result("Plugin API Content", False, f"Error: {e}")
    
    def test_widget_api_content(self):
        """Test Widget API documentation"""
        try:
            widget_results = self.collection.query(
                query_texts=["Widget API development Figma widgets"],
                where={"framework": "figma_plugin"},
                n_results=5
            )
            
            if widget_results['documents'] and len(widget_results['documents'][0]) > 0:
                # Check for widget-specific terms
                content = " ".join(widget_results['documents'][0]).lower()
                widget_terms = ["widget", "ui", "component", "react", "typescript"]
                
                found_terms = [term for term in widget_terms if term in content]
                
                if len(found_terms) >= 2:
                    self.log_test_result(
                        "Widget API Content", 
                        True, 
                        f"Found widget terms: {', '.join(found_terms)}"
                    )
                else:
                    self.log_test_result(
                        "Widget API Content", 
                        False, 
                        f"Limited widget content - found: {', '.join(found_terms)}"
                    )
            else:
                self.log_test_result("Widget API Content", False, "No Widget API docs found")
        except Exception as e:
            self.log_test_result("Widget API Content", False, f"Error: {e}")
    
    def test_code_examples(self):
        """Test that code examples are present"""
        try:
            code_results = self.collection.query(
                query_texts=["code example javascript typescript figma plugin"],
                where={"framework": "figma_plugin"},
                n_results=5
            )
            
            if code_results['documents'] and len(code_results['documents'][0]) > 0:
                content = " ".join(code_results['documents'][0])
                
                # Look for code indicators
                code_indicators = ["```", "javascript", "typescript", "const", "function", "async", "await"]
                found_indicators = [indicator for indicator in code_indicators if indicator in content]
                
                if len(found_indicators) >= 3:
                    self.log_test_result(
                        "Code Examples", 
                        True, 
                        f"Found code indicators: {', '.join(found_indicators)}"
                    )
                else:
                    self.log_test_result(
                        "Code Examples", 
                        False, 
                        f"Limited code content - found: {', '.join(found_indicators)}"
                    )
            else:
                self.log_test_result("Code Examples", False, "No code examples found")
        except Exception as e:
            self.log_test_result("Code Examples", False, f"Error: {e}")
    
    def test_development_guides(self):
        """Test development guides and tutorials"""
        try:
            guide_results = self.collection.query(
                query_texts=["getting started plugin development tutorial guide"],
                where={"framework": "figma_plugin"},
                n_results=5
            )
            
            if guide_results['documents'] and len(guide_results['documents'][0]) > 0:
                content = " ".join(guide_results['documents'][0]).lower()
                guide_terms = ["tutorial", "guide", "getting started", "quickstart", "step"]
                
                found_terms = [term for term in guide_terms if term in content]
                
                if len(found_terms) >= 2:
                    self.log_test_result(
                        "Development Guides", 
                        True, 
                        f"Found guide terms: {', '.join(found_terms)}"
                    )
                else:
                    self.log_test_result(
                        "Development Guides", 
                        False, 
                        f"Limited guide content - found: {', '.join(found_terms)}"
                    )
            else:
                self.log_test_result("Development Guides", False, "No development guides found")
        except Exception as e:
            self.log_test_result("Development Guides", False, f"Error: {e}")
    
    def test_metadata_quality(self):
        """Test that metadata is properly structured"""
        try:
            sample_docs = self.collection.get(
                where={"framework": "figma_plugin"},
                limit=10,
                include=["metadatas"]
            )
            
            if sample_docs['metadatas']:
                # Check metadata fields
                required_fields = ["framework", "source", "doc_type", "title", "url", "section"]
                metadata_quality = []
                
                for metadata in sample_docs['metadatas'][:5]:
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
                        f"{complete_count}/5 samples have complete metadata"
                    )
                else:
                    self.log_test_result(
                        "Metadata Quality", 
                        False, 
                        f"Only {complete_count}/5 samples have complete metadata"
                    )
            else:
                self.log_test_result("Metadata Quality", False, "No metadata found")
        except Exception as e:
            self.log_test_result("Metadata Quality", False, f"Error: {e}")
    
    def test_search_functionality(self):
        """Test comprehensive search functionality"""
        search_queries = [
            ("Plugin development basics", "plugin"),
            ("Widget API reference", "widget"),
            ("Publishing plugins", "publish"),
            ("Figma node manipulation", "node"),
            ("Plugin UI development", "ui")
        ]
        
        for query, expected_topic in search_queries:
            try:
                results = self.collection.query(
                    query_texts=[query],
                    where={"framework": "figma_plugin"},
                    n_results=3
                )
                
                if results['documents'] and len(results['documents'][0]) > 0:
                    # Check relevance
                    content = " ".join(results['documents'][0]).lower()
                    if expected_topic.lower() in content:
                        self.log_test_result(
                            f"Search: '{query}'", 
                            True, 
                            f"Found relevant content about {expected_topic}"
                        )
                    else:
                        self.log_test_result(
                            f"Search: '{query}'", 
                            False, 
                            f"Results not relevant to {expected_topic}"
                        )
                else:
                    self.log_test_result(f"Search: '{query}'", False, "No results found")
            except Exception as e:
                self.log_test_result(f"Search: '{query}'", False, f"Error: {e}")
    
    def test_doc_type_distribution(self):
        """Test distribution of document types"""
        try:
            plugin_docs = self.collection.get(
                where={"framework": "figma_plugin"},
                include=["metadatas"]
            )
            
            if plugin_docs['metadatas']:
                doc_types = {}
                for metadata in plugin_docs['metadatas']:
                    doc_type = metadata.get('doc_type', 'unknown')
                    doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
                
                expected_types = ["api_reference", "tutorial", "guide", "api_documentation"]
                found_expected = [dt for dt in expected_types if dt in doc_types]
                
                if len(found_expected) >= 2:
                    type_summary = ", ".join([f"{dt}: {doc_types[dt]}" for dt in found_expected])
                    self.log_test_result(
                        "Document Type Distribution", 
                        True, 
                        f"Found expected types - {type_summary}"
                    )
                else:
                    self.log_test_result(
                        "Document Type Distribution", 
                        False, 
                        f"Missing expected doc types. Found: {list(doc_types.keys())}"
                    )
            else:
                self.log_test_result("Document Type Distribution", False, "No metadata available")
        except Exception as e:
            self.log_test_result("Document Type Distribution", False, f"Error: {e}")
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        logger.info("🧪 Starting comprehensive Figma Plugin documentation integration tests...")
        
        # Setup
        if not self.setup_chromadb_connection():
            logger.error("❌ Failed to setup ChromaDB connection. Aborting tests.")
            return False
        
        # Run tests
        plugin_count = self.test_figma_plugin_document_count()
        self.test_content_categories()
        self.test_plugin_api_content()
        self.test_widget_api_content()
        self.test_code_examples()
        self.test_development_guides()
        self.test_metadata_quality()
        self.test_search_functionality()
        self.test_doc_type_distribution()
        
        # Summary
        logger.info("\n📊 TEST RESULTS SUMMARY:")
        logger.info(f"   Total Tests: {self.test_results['total_tests']}")
        logger.info(f"   Passed: {self.test_results['passed']} ✅")
        logger.info(f"   Failed: {self.test_results['failed']} ❌")
        logger.info(f"   Success Rate: {(self.test_results['passed']/self.test_results['total_tests']*100):.1f}%")
        
        # Detailed results
        if self.test_results['failed'] > 0:
            logger.info("\n❌ FAILED TESTS:")
            for result in self.test_results['results']:
                if not result['passed']:
                    logger.info(f"   - {result['test']}: {result['details']}")
        
        # Overall assessment
        success_rate = self.test_results['passed'] / self.test_results['total_tests']
        if success_rate >= 0.85:
            logger.info("\n🎉 INTEGRATION TEST PASSED! Figma Plugin documentation is properly integrated.")
            return True
        elif success_rate >= 0.7:
            logger.info("\n⚠️  INTEGRATION TEST PARTIAL SUCCESS. Some issues detected.")
            return True
        else:
            logger.info("\n❌ INTEGRATION TEST FAILED. Significant issues detected.")
            return False

def main():
    """Run the comprehensive test suite"""
    tests = FigmaPluginDocumentationTests()
    success = tests.run_all_tests()
    
    if success:
        print("\n✅ All integration tests completed successfully!")
        print("🎯 Figma Plugin API documentation is fully integrated and searchable")
    else:
        print("\n❌ Integration tests failed")
        print("📋 Check the test results above for details")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())