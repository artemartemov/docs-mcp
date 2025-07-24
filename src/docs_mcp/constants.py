"""Constants for docs-mcp."""

# Security - Input sanitization
DANGEROUS_CHARS = [
    "<", ">", '"', "'", "&", ";", "|", "`", "$",
    "{", "}", "[", "]", "(", ")", "\\", 
    "script", "eval", "exec", "__import__", "open"
]

# SQL injection prevention patterns
SQL_INJECTION_PATTERNS = ["'", '"', ";", "--", "/*", "*/", "xp_", "sp_", "union", "select"]

# XSS prevention patterns  
XSS_PATTERNS = ["<script", "</script", "javascript:", "onload=", "onerror=", "onclick="]

# CSS-specific injection patterns
CSS_INJECTION_PATTERNS = [
    "expression(",      # IE CSS expressions can execute JavaScript
    "javascript:",      # JavaScript protocol in CSS
    "@import",          # External imports can load malicious content
    "behavior:",        # IE behavior property can execute code
    "-moz-binding",     # Firefox XBL can execute code
    "filter:",          # IE filters can contain script
    "\\\\u",            # Unicode escapes
    "\\0",              # Null bytes
    "data:text/html",   # Data URIs with HTML
    "vbscript:",        # VBScript protocol
    "expression\\s*\\(", # Spaced CSS expressions
]

# CSS keylogger attack patterns
CSS_KEYLOGGER_PATTERNS = [
    r'input\[type="password"\]\[value\$=".+"\]',  # Password sniffing
    r'input\[value\^=".+"\]',                        # Input value tracking
    r'\[value.*\$=".*"\]',                          # Attribute value tracking
    r'background.*url\(["\']?https?:',               # External resource loading for tracking
]

MIN_SECRET_KEY_LENGTH = 32

# Content limits
MAX_CONTENT_LENGTH = 50000
MIN_CONTENT_LENGTH = 10
MAX_QUERY_LENGTH = 1000

# Defaults
DEFAULT_SEARCH_LIMIT = 3
DEFAULT_RATE_LIMIT = 60
DEFAULT_ENVIRONMENT = "development"

# Security limits for CSS processing
CSS_MAX_REQUESTS_PER_MINUTE = 30
CSS_MAX_TOTAL_REQUESTS = 3000
CSS_CONTENT_MAX_LENGTH = 20000  # Stricter limit for CSS content

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