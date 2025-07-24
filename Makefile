# Documentation MCP Server Makefile

.PHONY: install install-dev test lint format security run clean help
.PHONY: list-sources ingest-python ingest-react ingest-swiftui ingest-tailwind ingest-figma ingest-fastapi ingest-all
.PHONY: test-python test-react test-swiftui test-tailwind test-figma test-fastapi test-all weekly-update clean-logs ingest test-doc

# Default Python executable
PYTHON := python3
PIP := $(PYTHON) -m pip

help: ## Show this help message
	@echo "📚 Documentation MCP Server"
	@echo "Available commands:"
	@echo ""
	@echo "🏗️  Setup & Development:"
	@awk 'BEGIN {FS = ":.*?## "} /^(install|init|setup|validate|run|clean):.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "🔍 Documentation Sources:"
	@awk 'BEGIN {FS = ":.*?## "} /^(list-sources|ingest|test-doc):.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "📥 Individual Ingestion:"
	@awk 'BEGIN {FS = ":.*?## "} /^ingest-.*:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "🧪 Test Mode:"
	@awk 'BEGIN {FS = ":.*?## "} /^test-.*:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "🔄 Retry Failed URLs:"
	@awk 'BEGIN {FS = ":.*?## "} /^(retry|retry-.*|list-failed-files):.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "⏰ Maintenance:"
	@awk 'BEGIN {FS = ":.*?## "} /^(weekly-update|clean-logs):.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""
	@echo "🔧 Quality Checks:"
	@awk 'BEGIN {FS = ":.*?## "} /^(test|lint|format|security|all-checks):.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	$(PIP) install -r requirements.txt

install-dev: install ## Install development dependencies
	$(PIP) install -r requirements-dev.txt

test: ## Run tests
	pytest -v --cov=. --cov-report=html

lint: ## Run linting checks
	flake8 src/docs_mcp/
	mypy src/docs_mcp/

format: ## Format code with black
	black src/docs_mcp/ scripts/ tests/

security: ## Run security checks
	bandit -r src/docs_mcp/
	safety check

run: ## Run the MCP server
	PYTHONPATH=src $(PYTHON) -m docs_mcp.server

run-production: ## Run with production settings
	ENVIRONMENT=production PYTHONPATH=src uvicorn docs_mcp.server:mcp --host 127.0.0.1 --port 8000

setup-env: ## Setup environment file from example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from template. Please edit with your settings."; \
	else \
		echo ".env file already exists"; \
	fi

validate-config: ## Validate configuration
	PYTHONPATH=src $(PYTHON) -c "from docs_mcp.config import validate_environment; validate_environment(); print('✅ Configuration valid')"

clean: ## Clean up generated files
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

logs: ## Show recent logs
	tail -f logs/mcp_server.log

check-deps: ## Check for dependency vulnerabilities
	safety check
	pip-audit

all-checks: format lint security test ## Run all quality checks

init: install-dev setup-env ## Initialize development environment
	@echo "Development environment initialized!"
	@echo "Next steps:"
	@echo "1. Edit .env with your configuration"
	@echo "2. Run 'make validate-config' to verify settings"
	@echo "3. Run 'make run' to start the server"

# ============================================================================
# DOCUMENTATION INGESTION COMMANDS
# ============================================================================

list-sources: ## List all available documentation sources
	@echo "🔍 Listing available documentation sources..."
	./run_ingestion.sh --list-sources

# Individual source ingestion targets
ingest-python: ## Ingest Python 3 official documentation
	@echo "🐍 Ingesting Python documentation..."
	./run_ingestion.sh --source python

ingest-react: ## Ingest React.js official documentation
	@echo "⚛️  Ingesting React.js documentation..."
	./run_ingestion.sh --source react

ingest-swiftui: ## Ingest SwiftUI official documentation (with browser automation)
	@echo "🍎 Ingesting SwiftUI documentation with browser automation..."
	./run_ingestion.sh --source swiftui

ingest-tailwind: ## Ingest Tailwind CSS official documentation
	@echo "🎨 Ingesting Tailwind CSS documentation..."
	./run_ingestion.sh --source tailwind

ingest-figma: ## Ingest Figma API official documentation (with browser automation)
	@echo "🎨 Ingesting Figma API documentation with browser automation..."
	./run_ingestion.sh --source figma

ingest-fastapi: ## Ingest FastAPI official documentation
	@echo "🚀 Ingesting FastAPI documentation..."
	./run_ingestion.sh --source fastapi

ingest-all: ## Ingest ALL documentation sources
	@echo "📚 Ingesting ALL documentation sources..."
	./run_ingestion.sh --source all

# Test mode targets (limited content)
test-python: ## Test Python ingestion (10 docs max)
	@echo "🧪 Testing Python documentation (limited)..."
	./run_ingestion.sh --source python --test

test-react: ## Test React.js ingestion (10 docs max)
	@echo "🧪 Testing React.js documentation (limited)..."
	./run_ingestion.sh --source react --test

test-swiftui: ## Test SwiftUI ingestion (10 docs max)
	@echo "🧪 Testing SwiftUI documentation (limited)..."
	./run_ingestion.sh --source swiftui --test

test-tailwind: ## Test Tailwind CSS ingestion (10 docs max)
	@echo "🧪 Testing Tailwind CSS documentation (limited)..."
	./run_ingestion.sh --source tailwind --test

test-figma: ## Test Figma API ingestion (10 docs max)
	@echo "🧪 Testing Figma API documentation (limited)..."
	./run_ingestion.sh --source figma --test

test-fastapi: ## Test FastAPI ingestion (10 docs max)
	@echo "🧪 Testing FastAPI documentation (limited)..."
	./run_ingestion.sh --source fastapi --test

test-all: ## Test ALL sources (10 docs each)
	@echo "🧪 Testing ALL documentation sources (limited)..."
	./run_ingestion.sh --source all --test

# Weekly update target (perfect for cron jobs)
weekly-update: ## Update all documentation sources (for cron jobs)
	@echo "⏰ Weekly Documentation Update Started"
	@echo "============================"
	@echo "📅 $(shell date)"
	@echo ""
	@echo "🧹 Cleaning old logs..."
	@$(MAKE) clean-logs
	@echo ""
	@echo "📚 Updating all documentation sources..."
	./run_ingestion.sh --source all --output logs/weekly_update_$(shell date +%Y%m%d_%H%M%S).json
	@echo ""
	@echo "✅ Weekly update completed: $(shell date)"

# Clean old log files (keep last 10)
clean-logs: ## Clean old log files (keep last 10)
	@echo "🧹 Cleaning old log files (keeping last 10)..."
	@find logs/ -name "*.log" -type f 2>/dev/null | sort | head -n -10 | xargs -r rm -f || true
	@find logs/ -name "*.json" -type f 2>/dev/null | sort | head -n -10 | xargs -r rm -f || true
	@echo "✅ Log cleanup completed"

# Dynamic source ingestion (make ingest SOURCE=python)
ingest: ## Ingest specific source (make ingest SOURCE=python)
ifndef SOURCE
	@echo "❌ Please specify a SOURCE. Example: make ingest SOURCE=python"
	@echo "Available sources: python, react, swiftui, tailwind, figma, fastapi, all"
else
	@echo "📥 Ingesting $(SOURCE) documentation..."
	./run_ingestion.sh --source $(SOURCE)
endif

# Dynamic test ingestion (make test-doc SOURCE=python)
test-doc: ## Test specific source (make test-doc SOURCE=python)
ifndef SOURCE
	@echo "❌ Please specify a SOURCE. Example: make test-doc SOURCE=python"
	@echo "Available sources: python, react, swiftui, tailwind, figma, fastapi, all"
else
	@echo "🧪 Testing $(SOURCE) documentation (limited)..."
	./run_ingestion.sh --source $(SOURCE) --test
endif

# ============================================================================
# RETRY FAILED URLS COMMANDS
# ============================================================================

# Individual retry targets
retry-python: ## Retry failed Python URLs (make retry-python FAILED_FILE=path/to/file.json)
ifndef FAILED_FILE
	@echo "❌ Please specify FAILED_FILE. Example: make retry-python FAILED_FILE=logs/failed_urls_python_20240723_123456.json"
	@echo "💡 Check logs/ directory for available failed URL files"
	@ls -la logs/failed_urls_python_*.json 2>/dev/null || echo "No Python failed URL files found"
else
	@echo "🔄 Retrying failed Python URLs from: $(FAILED_FILE)"
	./run_ingestion.sh --source python --retry $(FAILED_FILE)
endif

retry-react: ## Retry failed React URLs (make retry-react FAILED_FILE=path/to/file.json)
ifndef FAILED_FILE
	@echo "❌ Please specify FAILED_FILE. Example: make retry-react FAILED_FILE=logs/failed_urls_react_20240723_123456.json"
	@echo "💡 Check logs/ directory for available failed URL files"
	@ls -la logs/failed_urls_react_*.json 2>/dev/null || echo "No React failed URL files found"
else
	@echo "🔄 Retrying failed React URLs from: $(FAILED_FILE)"
	./run_ingestion.sh --source react --retry $(FAILED_FILE)
endif

retry-swiftui: ## Retry failed SwiftUI URLs (make retry-swiftui FAILED_FILE=path/to/file.json)
ifndef FAILED_FILE
	@echo "❌ Please specify FAILED_FILE. Example: make retry-swiftui FAILED_FILE=logs/failed_urls_swiftui_20240723_123456.json"
	@echo "💡 Check logs/ directory for available failed URL files"
	@ls -la logs/failed_urls_swiftui_*.json 2>/dev/null || echo "No SwiftUI failed URL files found"
else
	@echo "🔄 Retrying failed SwiftUI URLs from: $(FAILED_FILE)"
	./run_ingestion.sh --source swiftui --retry $(FAILED_FILE)
endif

retry-tailwind: ## Retry failed Tailwind URLs (make retry-tailwind FAILED_FILE=path/to/file.json)
ifndef FAILED_FILE
	@echo "❌ Please specify FAILED_FILE. Example: make retry-tailwind FAILED_FILE=logs/failed_urls_tailwind_20240723_123456.json"
	@echo "💡 Check logs/ directory for available failed URL files"
	@ls -la logs/failed_urls_tailwind_*.json 2>/dev/null || echo "No Tailwind failed URL files found"
else
	@echo "🔄 Retrying failed Tailwind URLs from: $(FAILED_FILE)"
	./run_ingestion.sh --source tailwind --retry $(FAILED_FILE)
endif

retry-figma: ## Retry failed Figma URLs (make retry-figma FAILED_FILE=path/to/file.json)
ifndef FAILED_FILE
	@echo "❌ Please specify FAILED_FILE. Example: make retry-figma FAILED_FILE=logs/failed_urls_figma_20240723_123456.json"
	@echo "💡 Check logs/ directory for available failed URL files"
	@ls -la logs/failed_urls_figma_*.json 2>/dev/null || echo "No Figma failed URL files found"
else
	@echo "🔄 Retrying failed Figma URLs from: $(FAILED_FILE)"
	./run_ingestion.sh --source figma --retry $(FAILED_FILE)
endif

retry-fastapi: ## Retry failed FastAPI URLs (make retry-fastapi FAILED_FILE=path/to/file.json)
ifndef FAILED_FILE
	@echo "❌ Please specify FAILED_FILE. Example: make retry-fastapi FAILED_FILE=logs/failed_urls_fastapi_20240723_123456.json"
	@echo "💡 Check logs/ directory for available failed URL files"
	@ls -la logs/failed_urls_fastapi_*.json 2>/dev/null || echo "No FastAPI failed URL files found"
else
	@echo "🔄 Retrying failed FastAPI URLs from: $(FAILED_FILE)"
	./run_ingestion.sh --source fastapi --retry $(FAILED_FILE)
endif

# Dynamic retry command (make retry SOURCE=python FAILED_FILE=path/to/file.json)
retry: ## Retry failed URLs for specific source (make retry SOURCE=python FAILED_FILE=path/to/file.json)
ifndef SOURCE
	@echo "❌ Please specify SOURCE and FAILED_FILE"
	@echo "Example: make retry SOURCE=python FAILED_FILE=logs/failed_urls_python_20240723_123456.json"
	@echo "Available sources: python, react, swiftui, tailwind, figma, fastapi"
else ifndef FAILED_FILE
	@echo "❌ Please specify FAILED_FILE"
	@echo "Example: make retry SOURCE=$(SOURCE) FAILED_FILE=logs/failed_urls_$(SOURCE)_20240723_123456.json"
	@echo "💡 Available failed URL files for $(SOURCE):"
	@ls -la logs/failed_urls_$(SOURCE)_*.json 2>/dev/null || echo "No $(SOURCE) failed URL files found"
else
	@echo "🔄 Retrying failed $(SOURCE) URLs from: $(FAILED_FILE)"
	./run_ingestion.sh --source $(SOURCE) --retry $(FAILED_FILE)
endif

# List all failed URL files
list-failed-files: ## List all available failed URL files
	@echo "📂 Available failed URL files:"
	@echo ""
	@for framework in python react swiftui tailwind figma fastapi; do \
		echo "🔍 $$framework:"; \
		ls -la logs/failed_urls_$$framework_*.json 2>/dev/null | awk '{print "   " $$9 " (" $$5 " bytes, " $$6 " " $$7 " " $$8 ")"}' || echo "   No failed URL files found"; \
		echo ""; \
	done
	@echo "💡 To retry: make retry-<framework> FAILED_FILE=<file_path>"