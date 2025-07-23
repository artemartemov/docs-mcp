#!/bin/bash
# Simple script to run the MCP server with proper environment

set -e  # Exit on any error

echo "🚀 Documentation MCP Server"
echo "============================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run 'make init' first."
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
python -c "import chromadb, fastmcp" 2>/dev/null || {
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
}

# Check if ChromaDB has data
if [ -d "chroma_data" ]; then
    echo "📚 ChromaDB data found"
else
    echo "⚠️  No ChromaDB data found. You may want to run ingestion first:"
    echo "   ./run_ingestion.sh --source python --test"
fi

echo "✅ Environment ready!"
echo "🌐 Starting MCP server..."
echo ""

# Run the server
python server.py