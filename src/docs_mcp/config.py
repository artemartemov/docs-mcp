"""
Secure configuration management for ResaleAnalyzer Documentation MCP Server
"""

import os
import secrets
from typing import Optional
from pathlib import Path
from pydantic import field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

from .constants import MIN_SECRET_KEY_LENGTH, DEFAULT_ENVIRONMENT
from .exceptions import ConfigurationError

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Secure application settings with validation"""

    # Server Configuration
    environment: str = DEFAULT_ENVIRONMENT
    secret_key: str = secrets.token_urlsafe(32)  # Generate secure default

    # Chroma Database Configuration  
    chroma_data_dir: str = "./chroma_data"
    openai_api_key: Optional[str] = None

    # Server Configuration
    host: str = "127.0.0.1"
    port: int = 8000

    # Security Configuration
    max_query_length: int = 1000
    rate_limit_requests_per_minute: int = 60
    allowed_origins: list = ["http://localhost", "http://127.0.0.1"]

    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "logs/mcp_server.log"

    # GitHub Integration (optional)
    github_token: Optional[str] = None

    @field_validator("chroma_data_dir")
    @classmethod
    def validate_chroma_dir(cls, chroma_dir: str) -> str:
        """Validate that Chroma data directory exists and is accessible"""
        path = Path(chroma_dir)
        if not path.exists():
            raise ConfigurationError(
                f"Chroma data directory does not exist: {chroma_dir}. "
                f"Create it with: mkdir -p {chroma_dir}"
            )
        if not path.is_dir():
            raise ConfigurationError(
                f"Chroma data path is not a directory: {chroma_dir}. "
                f"Ensure {chroma_dir} is a directory, not a file."
            )
        if not os.access(path, os.R_OK | os.W_OK):
            raise ConfigurationError(
                f"Insufficient permissions for Chroma data directory: {chroma_dir}. "
                f"Fix with: chmod 755 {chroma_dir}"
            )
        return chroma_dir

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, api_key: Optional[str]) -> Optional[str]:
        """Validate OpenAI API key format"""
        if api_key and not api_key.startswith("sk-"):
            raise ConfigurationError(
                "OpenAI API key must start with 'sk-'. "
                "Get your API key from https://platform.openai.com/api-keys"
            )
        return api_key

    @field_validator("max_query_length")
    @classmethod
    def validate_query_length(cls, v):
        """Validate query length limits"""
        if v < 10 or v > 10000:
            raise ValueError("max_query_length must be between 10 and 10000")
        return v

    @field_validator("rate_limit_requests_per_minute")
    @classmethod
    def validate_rate_limit(cls, v):
        """Validate rate limiting configuration"""
        if v < 1 or v > 1000:
            raise ValueError(
                "rate_limit_requests_per_minute must be between 1 and 1000"
            )
        return v

    model_config = {
        "env_file": ".env",
        "env_prefix": "MCP_",
        "case_sensitive": False,
        "extra": "ignore",
    }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings


def create_log_directory():
    """Create log directory if it doesn't exist"""
    log_path = Path(settings.log_file).parent
    log_path.mkdir(parents=True, exist_ok=True)


def validate_environment():
    """Validate critical environment variables and settings"""
    errors = []

    # Check OpenAI API key in production
    if settings.environment == "production" and not settings.openai_api_key:
        errors.append("OpenAI API key is required in production")

    # Check Chroma directory permissions
    chroma_path = Path(settings.chroma_data_dir)
    if not chroma_path.exists():
        errors.append(
            f"Chroma data directory does not exist: {settings.chroma_data_dir}"
        )
    elif not os.access(chroma_path, os.R_OK | os.W_OK):
        errors.append(
            f"Insufficient permissions for Chroma directory: {settings.chroma_data_dir}"
        )

    # Check secret key strength
    if len(settings.secret_key) < MIN_SECRET_KEY_LENGTH:
        errors.append(f"Secret key must be at least {MIN_SECRET_KEY_LENGTH} characters long")

    if errors:
        raise ConfigurationError(
            "Configuration validation failed:\n"
            + "\n".join(f"- {error}" for error in errors)
        )

    return True
