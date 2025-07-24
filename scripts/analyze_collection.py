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


def analyze_all_sources() -> bool:
    """Main analysis orchestrator for documentation sources."""
    try:
        client = connect_to_chromadb()
        documents = fetch_all_documents(client)

        print_header(len(documents["ids"]))
        print_framework_stats(documents)
        print_detailed_source_breakdown(documents)
        print_unique_sources_summary(documents)
        print_document_type_distribution(documents)
        print_coverage_analysis(documents)

        return True
    except Exception as e:
        print(f"❌ Error analyzing sources: {e}")
        return False


def connect_to_chromadb():
    """Connect to ChromaDB and return collection."""
    chroma_client = chromadb.PersistentClient(
        path=settings.chroma_data_dir,
        settings=ChromaSettings(anonymized_telemetry=False, allow_reset=False),
    )
    return chroma_client.get_collection("documentation_collection")


def fetch_all_documents(collection):
    """Fetch all documents with metadata from collection."""
    return collection.get(include=["metadatas"])


def print_header(total_count: int) -> None:
    """Print analysis header with total document count."""
    print("📚 COMPREHENSIVE DOCUMENTATION SOURCE ANALYSIS")
    print("=" * 60)
    print(f"Total Documents in Collection: {total_count:,}")
    print()


def print_framework_stats(documents) -> None:
    """Print framework breakdown statistics."""
    frameworks = _analyze_frameworks(documents)
    total_count = len(documents["ids"])

    print("🏗️  FRAMEWORK BREAKDOWN:")
    print("-" * 40)
    for framework, count in sorted(
        frameworks.items(), key=lambda x: x[1], reverse=True
    ):
        percentage = (count / total_count) * 100
        print(f"   {framework:<20} {count:>6} docs ({percentage:>5.1f}%)")
    print()


def print_detailed_source_breakdown(documents) -> None:
    """Print detailed source breakdown by framework."""
    frameworks, framework_sources, framework_doc_types = _analyze_detailed_breakdown(
        documents
    )

    print("📖 DETAILED SOURCE BREAKDOWN:")
    print("-" * 40)

    for framework in sorted(frameworks.keys()):
        print(f"\n📁 {framework.upper()} Framework ({frameworks[framework]} docs):")

        # Sources for this framework
        fw_sources = framework_sources[framework]
        for source, count in sorted(
            fw_sources.items(), key=lambda x: x[1], reverse=True
        ):
            percentage = (count / frameworks[framework]) * 100
            print(f"   └── {source}")
            print(f"       {count} docs ({percentage:.1f}% of {framework})")

        # Document types for this framework
        fw_doc_types = framework_doc_types[framework]
        if len(fw_doc_types) > 1:
            print(f"   📄 Document Types:")
            for doc_type, count in sorted(
                fw_doc_types.items(), key=lambda x: x[1], reverse=True
            ):
                print(f"       • {doc_type}: {count}")

    print("\n" + "=" * 60)


def print_unique_sources_summary(documents) -> None:
    """Print summary of all unique sources."""
    sources = _analyze_sources(documents)
    total_count = len(documents["ids"])

    print("🌐 ALL UNIQUE SOURCES:")
    print("-" * 40)
    for i, (source, count) in enumerate(
        sorted(sources.items(), key=lambda x: x[1], reverse=True), 1
    ):
        percentage = (count / total_count) * 100
        print(f"{i:>2}. {source}")
        print(f"    {count:>4} docs ({percentage:>5.1f}%)")

    print(f"\nTotal unique sources: {len(sources)}")


def print_document_type_distribution(documents) -> None:
    """Print document type distribution statistics."""
    doc_types = _analyze_doc_types(documents)
    total_count = len(documents["ids"])

    print("\n📄 DOCUMENT TYPE DISTRIBUTION:")
    print("-" * 40)
    for doc_type, count in sorted(doc_types.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_count) * 100
        print(f"   {doc_type:<25} {count:>6} docs ({percentage:>5.1f}%)")

    print(f"\nTotal unique document types: {len(doc_types)}")


def print_coverage_analysis(documents) -> None:
    """Print coverage analysis for key frameworks."""
    frameworks = _analyze_frameworks(documents)

    print("\n🎯 COVERAGE ANALYSIS:")
    print("-" * 40)

    # Check for recent additions
    figma_docs = frameworks.get("figma", 0)
    figma_plugin_docs = frameworks.get("figma_plugin", 0)

    print(f"   Figma Coverage:")
    print(f"   • REST API docs: {figma_docs}")
    print(f"   • Plugin API docs: {figma_plugin_docs}")
    print(f"   • Total Figma docs: {figma_docs + figma_plugin_docs}")

    # Top frameworks
    top_3_frameworks = sorted(frameworks.items(), key=lambda x: x[1], reverse=True)[:3]
    print(f"\n   Top 3 Frameworks:")
    for i, (framework, count) in enumerate(top_3_frameworks, 1):
        print(f"   {i}. {framework}: {count} docs")


def _analyze_frameworks(documents) -> defaultdict:
    """Analyze framework distribution."""
    frameworks = defaultdict(int)
    for metadata in documents["metadatas"]:
        framework = metadata.get("framework", "unknown")
        frameworks[framework] += 1
    return frameworks


def _analyze_sources(documents) -> defaultdict:
    """Analyze source distribution."""
    sources = defaultdict(int)
    for metadata in documents["metadatas"]:
        source = metadata.get("source", "unknown")
        sources[source] += 1
    return sources


def _analyze_doc_types(documents) -> defaultdict:
    """Analyze document type distribution."""
    doc_types = defaultdict(int)
    for metadata in documents["metadatas"]:
        doc_type = metadata.get("doc_type", "unknown")
        doc_types[doc_type] += 1
    return doc_types


def _analyze_detailed_breakdown(documents) -> tuple:
    """Analyze detailed breakdown by framework."""
    frameworks = defaultdict(int)
    framework_sources = defaultdict(lambda: defaultdict(int))
    framework_doc_types = defaultdict(lambda: defaultdict(int))

    for metadata in documents["metadatas"]:
        framework = metadata.get("framework", "unknown")
        source = metadata.get("source", "unknown")
        doc_type = metadata.get("doc_type", "unknown")

        frameworks[framework] += 1
        framework_sources[framework][source] += 1
        framework_doc_types[framework][doc_type] += 1

    return frameworks, framework_sources, framework_doc_types


def check_extraction_status():
    """Check if any extractions are currently running"""
    try:
        from pathlib import Path

        log_files = [
            "logs/figma_plugin_extraction.log",
            "logs/figma_json_extraction.log",
        ]

        print("\n🔄 EXTRACTION STATUS:")
        print("-" * 40)

        for log_file in log_files:
            if Path(log_file).exists():
                # Get last few lines to check status
                with open(log_file, "r") as f:
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
