#!/usr/bin/env python3
"""
Quick test to check Figma Plugin documentation extraction progress.
"""

import chromadb
from chromadb.config import Settings as ChromaSettings
from config import get_settings

settings = get_settings()

def check_progress():
    """Check current progress of Figma Plugin documentation extraction"""
    
    try:
        # Connect to ChromaDB
        chroma_client = chromadb.PersistentClient(
            path=settings.chroma_data_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=False
            )
        )
        
        collection = chroma_client.get_collection("documentation_collection")
        
        # Check Figma Plugin documents
        figma_plugin_docs = collection.get(
            where={"framework": "figma_plugin"},
            include=["metadatas"]
        )
        
        plugin_count = len(figma_plugin_docs['ids'])
        print(f"📱 Figma Plugin documents currently in ChromaDB: {plugin_count}")
        
        if plugin_count > 0:
            # Show sample documents
            print("\n📋 Sample plugin documentation topics:")
            for i, metadata in enumerate(figma_plugin_docs['metadatas'][:10]):
                title = metadata.get('title', 'Untitled')
                doc_type = metadata.get('doc_type', 'unknown')
                section = metadata.get('section', 'general')
                print(f"   {i+1}. {title} ({doc_type}) - {section}")
            
            # Test search functionality
            print("\n🔍 Testing search functionality:")
            search_queries = [
                "plugin development",
                "figma widget api",
                "plugin quickstart"
            ]
            
            for query in search_queries:
                results = collection.query(
                    query_texts=[query],
                    where={"framework": "figma_plugin"},
                    n_results=2
                )
                
                if results['documents'] and results['documents'][0]:
                    print(f"   ✅ '{query}' - found {len(results['documents'][0])} results")
                else:
                    print(f"   ❌ '{query}' - no results")
        
        # Check total documents
        all_docs = collection.get(include=["metadatas"])
        total_count = len(all_docs['ids'])
        print(f"\n📚 Total documents in collection: {total_count}")
        
        # Framework breakdown
        frameworks = {}
        for metadata in all_docs['metadatas']:
            framework = metadata.get('framework', 'unknown')
            frameworks[framework] = frameworks.get(framework, 0) + 1
        
        print("\n📊 Framework breakdown:")
        for framework, count in sorted(frameworks.items()):
            print(f"   {framework}: {count}")
        
        return plugin_count > 0
        
    except Exception as e:
        print(f"❌ Error checking progress: {e}")
        return False

if __name__ == "__main__":
    success = check_progress()
    
    if success:
        print("\n✅ Figma Plugin documentation extraction is working!")
    else:
        print("\n❌ No plugin documents found yet")