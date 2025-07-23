#!/bin/bash
# Simple script to run documentation ingestion with proper environment

set -e  # Exit on any error

echo "🚀 Documentation Ingestion Runner"
echo "=================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run 'make init' first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
python -c "import chromadb, sphobjinv, aiohttp" 2>/dev/null || {
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
}

echo "✅ Environment ready!"
echo ""

# Run the ingestion with any provided arguments
if [ $# -eq 0 ]; then
    echo "Usage examples:"
    echo "  ./run_ingestion.sh --list-sources"
    echo "  ./run_ingestion.sh --source python --test"
    echo "  ./run_ingestion.sh --source python"
    echo ""
    echo "Available options:"
    python ingest_documentation.py --help
else
    echo "🔥 Running: python ingest_documentation.py $@"
    echo ""
    python ingest_documentation.py "$@"
fi