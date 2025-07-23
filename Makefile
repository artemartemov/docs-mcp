# ResaleAnalyzer Documentation MCP Server Makefile

.PHONY: install install-dev test lint format security run clean help

# Default Python executable
PYTHON := python3
PIP := $(PYTHON) -m pip

help: ## Show this help message
	@echo "ResaleAnalyzer Documentation MCP Server"
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install production dependencies
	$(PIP) install -r requirements.txt

install-dev: install ## Install development dependencies
	$(PIP) install -r requirements-dev.txt

test: ## Run tests
	pytest -v --cov=. --cov-report=html

lint: ## Run linting checks
	flake8 server.py config.py
	mypy server.py config.py

format: ## Format code with black
	black server.py config.py

security: ## Run security checks
	bandit -r server.py config.py
	safety check

run: ## Run the MCP server
	$(PYTHON) server.py

run-production: ## Run with production settings
	ENVIRONMENT=production uvicorn server:mcp --host 127.0.0.1 --port 8000

setup-env: ## Setup environment file from example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file from template. Please edit with your settings."; \
	else \
		echo ".env file already exists"; \
	fi

validate-config: ## Validate configuration
	$(PYTHON) -c "from config import validate_environment; validate_environment(); print('✅ Configuration valid')"

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