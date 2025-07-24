#!/usr/bin/env python3
"""
Test script for ResaleAnalyzer Documentation MCP Server
"""

import os
import sys
import asyncio
from datetime import datetime

# Add the docs-mcp directory to Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Also add the virtual environment if needed
VENV_SITE_PACKAGES = os.path.join(
    SCRIPT_DIR, "venv", "lib", "python3.11", "site-packages"
)
if os.path.exists(VENV_SITE_PACKAGES):
    sys.path.insert(0, VENV_SITE_PACKAGES)


def test_documentation_server():
    """Test the documentation server functionality"""

    print("🧪 Testing ResaleAnalyzer Documentation MCP Server")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # Import after path setup
        from server import (
            initialize_chroma,
            generate_doc_id,
            SearchRequest,
            DocumentRequest,
        )

        # Test 1: Initialize Chroma connection
        print("\n1. Testing Chroma database connection...")
        if initialize_chroma():
            print("✅ Chroma database connected successfully")
        else:
            print("❌ Failed to connect to Chroma database")
            return False

        # Test 2: Test validation models
        print("\n2. Testing input validation...")
        try:
            search_req = SearchRequest(
                query="FastAPI dependency injection", category="testing", limit=3
            )
            print(f"✅ Search request validation: {search_req.query[:30]}...")

            doc_req = DocumentRequest(
                content="Test documentation content for validation testing.",
                framework="fastapi",
                category="testing",
                source="test source",
            )
            print(f"✅ Document request validation: framework={doc_req.framework}")

        except Exception as e:
            print(f"❌ Validation test failed: {e}")
            return False

        # Test 3: Test ID generation
        print("\n3. Testing document ID generation...")
        doc_id = generate_doc_id("test content", "fastapi")
        print(f"✅ Generated document ID: {doc_id}")

        # Test 4: Test direct collection operations
        print("\n4. Testing direct collection operations...")
        from server import collection

        if collection:
            try:
                # Add a test document directly
                test_content = """
FastAPI Best Practices for ResaleAnalyzer Project:

1. **Dependency Injection**: Use FastAPI's Depends() for clean separation
   ```python
   async def get_analysis_service(
       repo: AnalysisRepository = Depends(get_analysis_repository)
   ) -> AnalysisService:
       return AnalysisService(repository=repo)
   ```

2. **Error Handling**: Use HTTPException with proper status codes
   ```python
   if not analysis_result:
       raise HTTPException(
           status_code=404,
           detail="Analysis not found"
       )
   ```

3. **Response Models**: Always use Pydantic models
   ```python
   class AnalysisResponse(BaseModel):
       success: bool
       data: Optional[AnalysisResult]
       message: str
   ```
"""

                collection.add(
                    documents=[test_content],
                    metadatas=[
                        {
                            "framework": "fastapi",
                            "category": "best_practices",
                            "source": "ResaleAnalyzer internal",
                            "type": "documentation",
                            "project": "resale_analyzer",
                        }
                    ],
                    ids=[f"test_doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"],
                )
                print("✅ Successfully added test documentation to collection")

                # Test search
                results = collection.query(
                    query_texts=["FastAPI dependency injection"],
                    n_results=2,
                    include=["documents", "metadatas", "distances"],
                )

                if results["documents"][0]:
                    print(
                        f"✅ Search test successful: Found {len(results['documents'][0])} results"
                    )
                    for i, (doc, metadata) in enumerate(
                        zip(results["documents"][0][:1], results["metadatas"][0][:1])
                    ):
                        print(f"   Result {i+1}: {doc[:100]}...")
                        print(f"   Framework: {metadata.get('framework', 'N/A')}")
                else:
                    print("⚠️  Search returned no results")

            except Exception as e:
                print(f"❌ Collection operations failed: {e}")
                return False
        else:
            print("❌ Collection not available")
            return False

        # Test 5: Collection statistics
        print("\n5. Testing collection statistics...")
        try:
            data = collection.get()
            total_docs = len(data["ids"])
            print(f"✅ Total documents in collection: {total_docs}")

            # Framework breakdown
            frameworks = {}
            for metadata in data["metadatas"]:
                fw = metadata.get("framework", "unknown")
                frameworks[fw] = frameworks.get(fw, 0) + 1

            print("   Framework breakdown:")
            for fw, count in sorted(frameworks.items()):
                print(f"     • {fw}: {count} docs")

        except Exception as e:
            print(f"❌ Statistics test failed: {e}")
            return False

        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED! Server is ready for use.")
        print("\n📋 How to use this MCP server:")
        print("1. Add it to your .mcp.json configuration")
        print(
            "2. Use search_fastapi_docs(), search_python_docs(), search_swift_ios_docs()"
        )
        print("3. Get security guidelines with get_security_guidelines()")
        print("4. Add more documentation with add_project_documentation()")

        return True

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_documentation_server()
    sys.exit(0 if success else 1)
