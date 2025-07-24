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

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Secure application settings with validation"""

    # Server Configuration
    environment: str = "development"
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
    def validate_chroma_dir(cls, v):
        """Validate that Chroma data directory exists and is accessible"""
        path = Path(v)
        if not path.exists():
            raise ValueError(f"Chroma data directory does not exist: {v}")
        if not path.is_dir():
            raise ValueError(f"Chroma data path is not a directory: {v}")
        if not os.access(path, os.R_OK | os.W_OK):
            raise ValueError(f"Insufficient permissions for Chroma data directory: {v}")
        return v

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_key(cls, v):
        """Validate OpenAI API key format"""
        if v and not v.startswith("sk-"):
            raise ValueError("OpenAI API key must start with 'sk-'")
        return v

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
    if len(settings.secret_key) < 32:
        errors.append("Secret key must be at least 32 characters long")

    if errors:
        raise ValueError(
            "Configuration validation failed:\n"
            + "\n".join(f"- {error}" for error in errors)
        )

    return True
