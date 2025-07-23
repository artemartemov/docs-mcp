#!/usr/bin/env python3
"""
View and explore data stored in the Chroma database
"""

import os
import sys
import json
from datetime import datetime

# Add the docs-mcp directory to Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

# Also add the virtual environment if needed
VENV_SITE_PACKAGES = os.path.join(SCRIPT_DIR, 'venv', 'lib', 'python3.11', 'site-packages')
if os.path.exists(VENV_SITE_PACKAGES):
    sys.path.insert(0, VENV_SITE_PACKAGES)

def view_chroma_database():
    """View all data stored in the Chroma database"""
    
    print("🔍 Chroma Database Explorer - ResaleAnalyzer Documentation")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        from server import initialize_chroma
        
        # Initialize connection
        if not initialize_chroma():
            print("❌ Failed to connect to Chroma database")
            return False
        
        from server import chroma_client, collection
        
        if not collection:
            print("❌ No collection available")
            return False
        
        print(f"✅ Connected to collection: {collection.name}")
        
        # Get all data
        print("\n📊 COLLECTION OVERVIEW")
        print("-" * 50)
        
        data = collection.get(include=["documents", "metadatas", "embeddings"])
        total_docs = len(data["ids"])
        
        print(f"Total Documents: {total_docs}")
        
        if total_docs == 0:
            print("📭 Collection is empty")
            return True
        
        # Framework breakdown
        frameworks = {}
        categories = {}
        sources = {}
        doc_types = {}
        
        for metadata in data["metadatas"]:
            fw = metadata.get("framework", "unknown")
            cat = metadata.get("category", "unknown")
            src = metadata.get("source", "unknown")
            dtype = metadata.get("type", "unknown")
            
            frameworks[fw] = frameworks.get(fw, 0) + 1
            categories[cat] = categories.get(cat, 0) + 1
            sources[src] = sources.get(src, 0) + 1
            doc_types[dtype] = doc_types.get(dtype, 0) + 1
        
        print(f"\n📈 STATISTICS")
        print("-" * 30)
        print("By Framework:")
        for fw, count in sorted(frameworks.items()):
            print(f"  • {fw}: {count} docs")
        
        print("\nBy Category:")
        for cat, count in sorted(categories.items()):
            print(f"  • {cat}: {count} docs")
        
        print("\nBy Source:")
        for src, count in sorted(sources.items()):
            print(f"  • {src}: {count} docs")
        
        print("\nBy Type:")
        for dtype, count in sorted(doc_types.items()):
            print(f"  • {dtype}: {count} docs")
        
        # Show all documents with details
        print(f"\n📄 ALL DOCUMENTS ({total_docs})")
        print("=" * 70)
        
        for i, (doc_id, document, metadata) in enumerate(zip(
            data["ids"], 
            data["documents"], 
            data["metadatas"]
        )):
            print(f"\n📋 Document {i+1}: {doc_id}")
            print("-" * 50)
            
            # Metadata
            print("📊 Metadata:")
            print(f"  Framework: {metadata.get('framework', 'N/A')}")
            print(f"  Category: {metadata.get('category', 'N/A')}")
            print(f"  Source: {metadata.get('source', 'N/A')}")
            print(f"  Type: {metadata.get('type', 'N/A')}")
            print(f"  Project: {metadata.get('project', 'N/A')}")
            if 'added_at' in metadata:
                print(f"  Added: {metadata['added_at']}")
            if 'content_hash' in metadata:
                print(f"  Hash: {metadata['content_hash']}")
            
            # Content preview
            print(f"\n📝 Content ({len(document)} chars):")
            
            # Show first 300 characters nicely formatted
            preview = document[:300]
            if len(document) > 300:
                preview += "..."
            
            # Format the preview nicely
            lines = preview.split('\n')
            for line in lines[:10]:  # Show first 10 lines max
                print(f"    {line}")
            
            if len(lines) > 10:
                print("    ... (content continues)")
        
        # Show collection metadata
        print(f"\n🏷️  COLLECTION METADATA")
        print("-" * 40)
        try:
            collection_metadata = collection.metadata
            if collection_metadata:
                for key, value in collection_metadata.items():
                    print(f"  {key}: {value}")
            else:
                print("  No collection metadata available")
        except Exception as e:
            print(f"  Error retrieving collection metadata: {e}")
        
        # Show some sample searches
        print(f"\n🔍 SAMPLE SEARCH RESULTS")
        print("-" * 40)
        
        sample_queries = [
            "FastAPI best practices",
            "Python async patterns", 
            "SwiftUI architecture",
            "error handling"
        ]
        
        for query in sample_queries:
            try:
                results = collection.query(
                    query_texts=[query],
                    n_results=1,
                    include=["documents", "metadatas", "distances"]
                )
                
                if results["documents"][0]:
                    doc = results["documents"][0][0]
                    metadata = results["metadatas"][0][0]
                    distance = results["distances"][0][0]
                    relevance = 1 - distance
                    
                    print(f"\nQuery: '{query}'")
                    print(f"  Best match: {metadata.get('framework', 'N/A')} - {metadata.get('category', 'N/A')}")
                    print(f"  Relevance: {relevance:.3f}")
                    print(f"  Preview: {doc[:80]}...")
                else:
                    print(f"\nQuery: '{query}' - No results")
                    
            except Exception as e:
                print(f"\nQuery: '{query}' - Error: {e}")
        
        print(f"\n" + "=" * 70)
        print("✅ Database exploration complete!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error exploring database: {e}")
        import traceback
        traceback.print_exc()
        return False

def export_chroma_data():
    """Export all Chroma data to JSON for backup/analysis"""
    
    print("\n💾 EXPORTING DATA TO JSON")
    print("-" * 40)
    
    try:
        from server import collection
        
        if not collection:
            print("❌ No collection available for export")
            return False
        
        # Get all data
        data = collection.get(include=["documents", "metadatas"])
        
        # Prepare export data
        export_data = {
            "collection_name": collection.name,
            "export_timestamp": datetime.now().isoformat(),
            "total_documents": len(data["ids"]),
            "documents": []
        }
        
        for doc_id, document, metadata in zip(
            data["ids"], 
            data["documents"], 
            data["metadatas"]
        ):
            export_data["documents"].append({
                "id": doc_id,
                "content": document,
                "metadata": metadata
            })
        
        # Save to file
        export_file = f"chroma_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Data exported to: {export_file}")
        print(f"   {len(export_data['documents'])} documents exported")
        
        return True
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return False

if __name__ == "__main__":
    print("Choose an option:")
    print("1. View database contents")
    print("2. Export to JSON")
    print("3. Both")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice in ['1', '3']:
        success = view_chroma_database()
    
    if choice in ['2', '3']:
        if choice == '3':
            print("\n" + "=" * 70)
        export_chroma_data()