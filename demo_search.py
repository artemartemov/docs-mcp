#!/usr/bin/env python3
"""
Demo script showing sample search outputs from the MCP server
"""

import os
import sys

# Add the docs-mcp directory to Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Also add the virtual environment if needed
VENV_SITE_PACKAGES = os.path.join(SCRIPT_DIR, 'venv', 'lib', 'python3.11', 'site-packages')
if os.path.exists(VENV_SITE_PACKAGES):
    sys.path.insert(0, VENV_SITE_PACKAGES)

def demo_search_functionality():
    """Demonstrate search functionality with sample outputs"""
    
    print("🔍 ResaleAnalyzer Documentation MCP Server - Search Demo")
    print("=" * 70)
    
    from server import initialize_chroma
    
    # Initialize connection
    if not initialize_chroma():
        print("❌ Failed to connect to database")
        return
    
    # Import collection after initialization
    from server import collection
    
    # Add more comprehensive documentation first
    sample_docs = [
        {
            "content": """
# FastAPI Error Handling Best Practices

## Structured Error Responses
```python
from fastapi import HTTPException, status
from app.schemas.errors import ErrorDetail

class AnalysisError(HTTPException):
    def __init__(self, message: str, error_code: str = "ANALYSIS_ERROR"):
        detail = ErrorDetail(
            message=message,
            error_code=error_code,
            timestamp=datetime.utcnow()
        )
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail.dict()
        )

# Usage in endpoints
@router.post("/analyze")
async def analyze_image(file: UploadFile):
    try:
        result = await analysis_service.analyze(file)
        return AnalysisResponse(success=True, data=result)
    except ValidationError as e:
        raise AnalysisError("Invalid image format", "VALIDATION_ERROR")
```

## Custom Exception Handlers
```python
@app.exception_handler(AnalysisError)
async def analysis_exception_handler(request: Request, exc: AnalysisError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )
```
            """,
            "framework": "fastapi",
            "category": "error_handling",
            "source": "ResaleAnalyzer patterns",
            "type": "best_practice"
        },
        {
            "content": """
# Python Async Patterns for Image Analysis

## Concurrent API Calls
```python
import asyncio
import aiohttp

async def analyze_with_multiple_services(image_data: bytes):
    async with aiohttp.ClientSession() as session:
        # Run OpenAI and Google Vision concurrently
        tasks = [
            openai_service.analyze_image(session, image_data),
            google_vision_service.analyze_image(session, image_data),
            product_lookup_service.find_similar(session, image_data)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle results and exceptions
        openai_result = results[0] if not isinstance(results[0], Exception) else None
        vision_result = results[1] if not isinstance(results[1], Exception) else None
        product_result = results[2] if not isinstance(results[2], Exception) else None
        
        return combine_analysis_results(openai_result, vision_result, product_result)
```

## Context Managers for Resources
```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def analysis_session():
    session = aiohttp.ClientSession()
    try:
        yield session
    finally:
        await session.close()

# Usage
async def perform_analysis():
    async with analysis_session() as session:
        result = await call_external_api(session)
        return result
```
            """,
            "framework": "python",
            "category": "async_patterns",
            "source": "ResaleAnalyzer async guide",
            "type": "best_practice"
        },
        {
            "content": """
# SwiftUI MVVM Architecture for ResaleAnalyzer

## ViewModel Structure
```swift
@MainActor
class AnalysisViewModel: BaseViewModel {
    @Published var analysisState: AnalysisState = .idle
    @Published var currentImages: [UIImage] = []
    @Published var analysisResult: AnalysisResult?
    @Published var progressValue: Double = 0.0
    
    private let analysisService: AnalysisService
    private let cacheService: CacheService
    
    init(analysisService: AnalysisService, cacheService: CacheService) {
        self.analysisService = analysisService
        self.cacheService = cacheService
        super.init()
    }
    
    func analyzeImages(_ images: [UIImage]) async {
        await performAsyncOperation {
            self.analysisState = .analyzing
            self.progressValue = 0.0
            
            // Check cache first
            let cacheKey = generateCacheKey(for: images)
            if let cachedResult = await cacheService.getCachedAnalysis(key: cacheKey) {
                self.analysisResult = cachedResult
                self.analysisState = .completed
                return
            }
            
            // Perform analysis with progress updates
            let result = try await analysisService.analyzeImages(images) { progress in
                await MainActor.run {
                    self.progressValue = progress
                }
            }
            
            // Cache result
            await cacheService.cacheAnalysis(result, key: cacheKey)
            
            self.analysisResult = result
            self.analysisState = .completed
        }
    }
}
```

## Dependency Injection Pattern
```swift
class DependencyContainer: ObservableObject {
    lazy var analysisService: AnalysisService = {
        APIAnalysisService(
            networkService: networkService,
            configurationService: configurationService
        )
    }()
    
    lazy var cacheService: CacheService = {
        CoreDataCacheService(context: persistentContainer.viewContext)
    }()
    
    func makeAnalysisViewModel() -> AnalysisViewModel {
        AnalysisViewModel(
            analysisService: analysisService,
            cacheService: cacheService
        )
    }
}
```
            """,
            "framework": "swift_ios",
            "category": "mvvm_architecture",
            "source": "ResaleAnalyzer iOS patterns",
            "type": "best_practice"
        }
    ]
    
    # Add sample documentation
    print("📝 Adding sample documentation...")
    for i, doc in enumerate(sample_docs):
        doc_id = f"demo_doc_{doc['framework']}_{i+1}"
        collection.add(
            documents=[doc["content"]],
            metadatas=[{k: v for k, v in doc.items() if k != "content"}],
            ids=[doc_id]
        )
    
    print(f"✅ Added {len(sample_docs)} sample documents")
    
    # Now demonstrate search functionality
    print("\n" + "=" * 70)
    print("🔍 SEARCH DEMONSTRATIONS")
    print("=" * 70)
    
    # Demo 1: FastAPI search
    print("\n1️⃣  FASTAPI SEARCH DEMO")
    print("-" * 40)
    print("Query: 'error handling patterns'")
    print("Category: 'error_handling'")
    print()
    
    results = collection.query(
        query_texts=["error handling patterns"],
        n_results=1,
        where={"framework": "fastapi"},
        include=["documents", "metadatas", "distances"]
    )
    
    if results["documents"][0]:
        doc = results["documents"][0][0]
        metadata = results["metadatas"][0][0]
        distance = results["distances"][0][0]
        relevance = 1 - distance
        
        print(f"📄 **Result 1** - {metadata.get('category', 'General')}")
        print(f"**Source:** {metadata.get('source', 'Unknown')}")
        print(f"**Relevance:** {relevance:.2f}")
        print()
        print(doc[:400] + "..." if len(doc) > 400 else doc)
    
    # Demo 2: Python search
    print("\n" + "-" * 70)
    print("2️⃣  PYTHON SEARCH DEMO")
    print("-" * 40)
    print("Query: 'async concurrent operations'")
    print("Category: 'async_patterns'")
    print()
    
    results = collection.query(
        query_texts=["async concurrent operations"],
        n_results=1,
        where={"framework": "python"},
        include=["documents", "metadatas", "distances"]
    )
    
    if results["documents"][0]:
        doc = results["documents"][0][0]
        metadata = results["metadatas"][0][0]
        distance = results["distances"][0][0]
        relevance = 1 - distance
        
        print(f"📄 **Result 1** - {metadata.get('category', 'General')}")
        print(f"**Source:** {metadata.get('source', 'Unknown')}")
        print(f"**Relevance:** {relevance:.2f}")
        print()
        print(doc[:400] + "..." if len(doc) > 400 else doc)
    
    # Demo 3: Swift iOS search
    print("\n" + "-" * 70)
    print("3️⃣  SWIFT IOS SEARCH DEMO")
    print("-" * 40)
    print("Query: 'SwiftUI ViewModel dependency injection'")
    print("Category: 'mvvm_architecture'")
    print()
    
    results = collection.query(
        query_texts=["SwiftUI ViewModel dependency injection"],
        n_results=1,
        where={"framework": "swift_ios"},
        include=["documents", "metadatas", "distances"]
    )
    
    if results["documents"][0]:
        doc = results["documents"][0][0]
        metadata = results["metadatas"][0][0]
        distance = results["distances"][0][0]
        relevance = 1 - distance
        
        print(f"📄 **Result 1** - {metadata.get('category', 'General')}")
        print(f"**Source:** {metadata.get('source', 'Unknown')}")
        print(f"**Relevance:** {relevance:.2f}")
        print()
        print(doc[:400] + "..." if len(doc) > 400 else doc)
    
    # Demo 4: Cross-framework search
    print("\n" + "-" * 70)
    print("4️⃣  CROSS-FRAMEWORK SEARCH DEMO")
    print("-" * 40)
    print("Query: 'best practices patterns'")
    print("No framework filter - searches all")
    print()
    
    results = collection.query(
        query_texts=["best practices patterns"],
        n_results=3,
        include=["documents", "metadatas", "distances"]
    )
    
    for i, (doc, metadata, distance) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    )):
        relevance = 1 - distance
        framework = metadata.get('framework', 'Unknown')
        category = metadata.get('category', 'General')
        
        print(f"📄 **Result {i+1}** - {framework.upper()} - {category}")
        print(f"**Relevance:** {relevance:.2f}")
        print(doc[:200] + "..." if len(doc) > 200 else doc)
        print()
    
    # Final stats
    print("\n" + "=" * 70)
    print("📊 COLLECTION STATISTICS")
    print("=" * 70)
    
    data = collection.get()
    total_docs = len(data["ids"])
    
    frameworks = {}
    categories = {}
    for metadata in data["metadatas"]:
        fw = metadata.get("framework", "unknown")
        cat = metadata.get("category", "unknown")
        frameworks[fw] = frameworks.get(fw, 0) + 1
        categories[cat] = categories.get(cat, 0) + 1
    
    print(f"📈 **Total Documents:** {total_docs}")
    print()
    print("**By Framework:**")
    for fw, count in sorted(frameworks.items()):
        print(f"  • {fw}: {count} docs")
    
    print()
    print("**By Category:**")
    for cat, count in sorted(categories.items()):
        print(f"  • {cat}: {count} docs")
    
    print("\n✅ Demo completed! The MCP server is ready for production use.")

if __name__ == "__main__":
    demo_search_functionality()