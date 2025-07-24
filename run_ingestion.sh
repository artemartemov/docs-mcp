#!/bin/bash
"""
Documentation ingestion wrapper script.
Routes commands to the appropriate Python ingestion scripts.
"""

set -e  # Exit on any error

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS_DIR="$SCRIPT_DIR/scripts"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_help() {
    cat << EOF
Usage: $0 [OPTIONS]

Documentation ingestion script for docs-mcp.

OPTIONS:
    --source SOURCE     Specify documentation source to ingest
                       (python, fastapi, react, swiftui, tailwind, figma, css, all)
    --test             Run in test mode (limited docs for testing)
    --retry FILE       Retry failed URLs from the specified JSON file
    --list-sources     List all available documentation sources
    --output FILE      Specify output file for ingestion results
    --help, -h         Show this help message

EXAMPLES:
    $0 --source python
    $0 --source all --test
    $0 --retry logs/failed_urls_python_20240723_123456.json
    $0 --list-sources

EOF
}

# Function to list available sources
list_sources() {
    print_status "Available documentation sources:"
    echo ""
    echo "  python      - Python 3 official documentation"
    echo "  fastapi     - FastAPI official documentation"
    echo "  react       - React.js official documentation"
    echo "  swiftui     - SwiftUI Apple documentation (browser automation)"
    echo "  tailwind    - Tailwind CSS official documentation"
    echo "  figma       - Figma API official documentation (browser automation)"
    echo "  figma_plugin - Figma Plugin API documentation"
    echo "  css         - MDN CSS documentation"
    echo "  all         - All available sources"
    echo ""
    echo "Use --test flag to limit ingestion for testing purposes."
}

# Function to run Python ingestion script
run_ingestion() {
    local source="$1"
    local test_mode="$2"
    local retry_file="$3"
    local output_file="$4"
    
    print_status "Starting documentation ingestion for: $source"
    
    # Determine which script to use
    local script_name=""
    local extra_args=()
    
    case "$source" in
        "python"|"fastapi"|"react"|"swiftui"|"tailwind"|"all")
            script_name="ingest_documentation.py"
            extra_args+=(--source "$source")
            ;;
        "figma")
            script_name="extract_figma_json.py"
            ;;
        "figma_plugin")
            script_name="extract_figma_plugin.py"
            ;;
        "css")
            script_name="extract_mdn_css.py"
            ;;
        *)
            print_error "Unknown source: $source"
            print_warning "Available sources: python, fastapi, react, swiftui, tailwind, figma, figma_plugin, css, all"
            exit 1
            ;;
    esac
    
    local script_path="$SCRIPTS_DIR/$script_name"
    
    if [[ ! -f "$script_path" ]]; then
        print_error "Script not found: $script_path"
        exit 1
    fi
    
    # Build command
    local cmd=(python3 "$script_path")
    cmd+=("${extra_args[@]}")
    
    if [[ "$test_mode" == "true" ]]; then
        cmd+=(--test)
    fi
    
    if [[ -n "$retry_file" ]]; then
        if [[ ! -f "$retry_file" ]]; then
            print_error "Retry file not found: $retry_file"
            exit 1
        fi
        cmd+=(--retry "$retry_file")
    fi
    
    if [[ -n "$output_file" ]]; then
        cmd+=(--output "$output_file")
    fi
    
    print_status "Running: ${cmd[*]}"
    
    # Run the command
    if "${cmd[@]}"; then
        print_success "Documentation ingestion completed for: $source"
    else
        print_error "Documentation ingestion failed for: $source"
        exit 1
    fi
}

# Parse command line arguments
SOURCE=""
TEST_MODE="false"
RETRY_FILE=""
OUTPUT_FILE=""
LIST_SOURCES="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        --source)
            SOURCE="$2"
            shift 2
            ;;
        --test)
            TEST_MODE="true"
            shift
            ;;
        --retry)
            RETRY_FILE="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --list-sources)
            LIST_SOURCES="true"
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Handle list sources
if [[ "$LIST_SOURCES" == "true" ]]; then
    list_sources
    exit 0
fi

# Validate required arguments
if [[ -z "$SOURCE" ]]; then
    print_error "Source is required"
    show_help
    exit 1
fi

# Ensure scripts directory exists
if [[ ! -d "$SCRIPTS_DIR" ]]; then
    print_error "Scripts directory not found: $SCRIPTS_DIR"
    exit 1
fi

# Run the ingestion
run_ingestion "$SOURCE" "$TEST_MODE" "$RETRY_FILE" "$OUTPUT_FILE"