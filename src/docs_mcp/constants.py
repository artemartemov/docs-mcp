"""Constants for docs-mcp."""

# Security
DANGEROUS_CHARS = ["<", ">", '"', "'", "&", ";", "|", "`", "$"]
MIN_SECRET_KEY_LENGTH = 32

# Content limits
MAX_CONTENT_LENGTH = 50000
MIN_CONTENT_LENGTH = 10
MAX_QUERY_LENGTH = 1000

# Defaults
DEFAULT_SEARCH_LIMIT = 3
DEFAULT_RATE_LIMIT = 60
DEFAULT_ENVIRONMENT = "development"

# Supported frameworks
SUPPORTED_FRAMEWORKS = {
    "python", "fastapi", "react", "swiftui", 
    "tailwind", "figma", "figma_plugin", "css"
}

# Document types
VALID_DOC_TYPES = {
    "documentation", "project_pattern", "best_practice",
    "reference", "tutorial", "guide", "api_reference"
}

# Logging configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_LEVEL = "INFO"