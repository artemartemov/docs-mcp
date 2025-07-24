#!/usr/bin/env python3
"""
Comprehensive analysis of all documentation sources in ChromaDB.

This script provides detailed statistics about all frameworks, sources,
and document types currently stored in the documentation collection.
"""

import sys
from pathlib import Path
from collections import defaultdict

import chromadb
from chromadb.config import Settings as ChromaSettings

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from docs_mcp.config import get_settings

settings = get_settings()

def analyze_all_sources():
    """Analyze all documentation sources and provide comprehensive statistics"""
    
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
        
        # Get all documents with metadata
        all_docs = collection.get(include=["metadatas"])
        total_count = len(all_docs['ids'])
        
        print("📚 COMPREHENSIVE DOCUMENTATION SOURCE ANALYSIS")
        print("=" * 60)
        print(f"Total Documents in Collection: {total_count:,}")
        print()
        
        # Analyze by framework
        frameworks = defaultdict(int)
        sources = defaultdict(int)
        doc_types = defaultdict(int)
        framework_sources = defaultdict(lambda: defaultdict(int))
        framework_doc_types = defaultdict(lambda: defaultdict(int))
        
        for metadata in all_docs['metadatas']:
            framework = metadata.get('framework', 'unknown')
            source = metadata.get('source', 'unknown')
            doc_type = metadata.get('doc_type', 'unknown')
            
            frameworks[framework] += 1
            sources[source] += 1
            doc_types[doc_type] += 1
            framework_sources[framework][source] += 1
            framework_doc_types[framework][doc_type] += 1
        
        # Framework breakdown
        print("🏗️  FRAMEWORK BREAKDOWN:")
        print("-" * 40)
        for framework, count in sorted(frameworks.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_count) * 100
            print(f"   {framework:<20} {count:>6} docs ({percentage:>5.1f}%)")
        print()
        
        # Detailed source breakdown by framework
        print("📖 DETAILED SOURCE BREAKDOWN:")
        print("-" * 40)
        
        for framework in sorted(frameworks.keys()):
            print(f"\n📁 {framework.upper()} Framework ({frameworks[framework]} docs):")
            
            # Sources for this framework
            fw_sources = framework_sources[framework]
            for source, count in sorted(fw_sources.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / frameworks[framework]) * 100
                print(f"   └── {source}")
                print(f"       {count} docs ({percentage:.1f}% of {framework})")
            
            # Document types for this framework
            fw_doc_types = framework_doc_types[framework]
            if len(fw_doc_types) > 1:
                print(f"   📄 Document Types:")
                for doc_type, count in sorted(fw_doc_types.items(), key=lambda x: x[1], reverse=True):
                    print(f"       • {doc_type}: {count}")
        
        print("\n" + "=" * 60)
        
        # Summary of unique sources
        print("🌐 ALL UNIQUE SOURCES:")
        print("-" * 40)
        for i, (source, count) in enumerate(sorted(sources.items(), key=lambda x: x[1], reverse=True), 1):
            percentage = (count / total_count) * 100
            print(f"{i:>2}. {source}")
            print(f"    {count:>4} docs ({percentage:>5.1f}%)")
        
        print(f"\nTotal unique sources: {len(sources)}")
        
        # Document type summary
        print("\n📄 DOCUMENT TYPE DISTRIBUTION:")
        print("-" * 40)
        for doc_type, count in sorted(doc_types.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_count) * 100
            print(f"   {doc_type:<25} {count:>6} docs ({percentage:>5.1f}%)")
        
        print(f"\nTotal unique document types: {len(doc_types)}")
        
        # Coverage analysis
        print("\n🎯 COVERAGE ANALYSIS:")
        print("-" * 40)
        
        # Check for recent additions
        figma_docs = frameworks.get('figma', 0)
        figma_plugin_docs = frameworks.get('figma_plugin', 0)
        
        print(f"   Figma Coverage:")
        print(f"   • REST API docs: {figma_docs}")
        print(f"   • Plugin API docs: {figma_plugin_docs}")
        print(f"   • Total Figma docs: {figma_docs + figma_plugin_docs}")
        
        # Top frameworks
        top_3_frameworks = sorted(frameworks.items(), key=lambda x: x[1], reverse=True)[:3]
        print(f"\n   Top 3 Frameworks:")
        for i, (framework, count) in enumerate(top_3_frameworks, 1):
            print(f"   {i}. {framework}: {count} docs")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing sources: {e}")
        return False

def check_extraction_status():
    """Check if any extractions are currently running"""
    try:
        from pathlib import Path
        
        log_files = [
            "logs/figma_plugin_extraction.log",
            "logs/figma_json_extraction.log"
        ]
        
        print("\n🔄 EXTRACTION STATUS:")
        print("-" * 40)
        
        for log_file in log_files:
            if Path(log_file).exists():
                # Get last few lines to check status
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    if lines:
                        last_line = lines[-1].strip()
                        if "COMPLETED SUCCESSFULLY" in last_line:
                            print(f"   ✅ {log_file}: Completed")
                        elif "Processing" in last_line or "Batch" in last_line:
                            print(f"   🔄 {log_file}: In Progress")
                        else:
                            print(f"   ⏸️  {log_file}: Status unclear")
                    else:
                        print(f"   📄 {log_file}: Empty log")
            else:
                print(f"   ❌ {log_file}: Not found")
        
    except Exception as e:
        print(f"⚠️  Could not check extraction status: {e}")

if __name__ == "__main__":
    success = analyze_all_sources()
    
    if success:
        check_extraction_status()
        print("\n✅ Analysis completed successfully!")
        print("📊 All documentation sources have been analyzed and reported")
    else:
        print("\n❌ Analysis failed")