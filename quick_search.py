#!/usr/bin/env python3
"""
Quick interactive search tool for the documentation database
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

def interactive_search():
    """Interactive search interface"""
    
    print("🔍 ResaleAnalyzer Documentation Search")
    print("=" * 50)
    
    try:
        from server import initialize_chroma
        
        if not initialize_chroma():
            print("❌ Failed to connect to database")
            return
        
        from server import collection
        
        print("✅ Connected to database")
        print("\nAvailable frameworks: fastapi, python, swift_ios")
        print("Available categories: error_handling, async_patterns, mvvm_architecture, best_practices")
        print("\nCommands:")
        print("  'quit' or 'exit' to quit")
        print("  'stats' to show database statistics")
        print("  'list' to show all documents")
        print("\n" + "-" * 50)
        
        while True:
            query = input("\n🔍 Search query (or command): ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if query.lower() == 'stats':
                data = collection.get()
                print(f"\n📊 Database has {len(data['ids'])} documents")
                
                frameworks = {}
                for metadata in data["metadatas"]:
                    fw = metadata.get("framework", "unknown")
                    frameworks[fw] = frameworks.get(fw, 0) + 1
                
                print("Frameworks:")
                for fw, count in sorted(frameworks.items()):
                    print(f"  • {fw}: {count} docs")
                continue
            
            if query.lower() == 'list':
                data = collection.get()
                print(f"\n📋 All Documents:")
                for i, (doc_id, metadata) in enumerate(zip(data["ids"], data["metadatas"])):
                    fw = metadata.get("framework", "N/A")
                    cat = metadata.get("category", "N/A")
                    print(f"  {i+1}. {doc_id} - {fw}/{cat}")
                continue
            
            if not query:
                continue
            
            # Perform search
            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=3,
                    include=["documents", "metadatas", "distances"]
                )
                
                if results["documents"][0]:
                    print(f"\n📄 Search Results for: '{query}'")
                    print("-" * 40)
                    
                    for i, (doc, metadata, distance) in enumerate(zip(
                        results["documents"][0],
                        results["metadatas"][0],
                        results["distances"][0]
                    )):
                        relevance = max(0, 1 - distance)
                        fw = metadata.get("framework", "N/A")
                        cat = metadata.get("category", "N/A")
                        src = metadata.get("source", "N/A")
                        
                        print(f"\n{i+1}. {fw.upper()} - {cat}")
                        print(f"   Source: {src}")
                        print(f"   Relevance: {relevance:.3f}")
                        print(f"   Preview: {doc[:150]}...")
                        
                        if i < len(results["documents"][0]) - 1:
                            print()
                else:
                    print(f"\n❌ No results found for: '{query}'")
                    
            except Exception as e:
                print(f"\n❌ Search error: {e}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    interactive_search()