#!/usr/bin/env python3
"""
Unit tests for configuration management.
"""

import os
import tempfile
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from docs_mcp.config import Settings, get_settings, validate_environment
from docs_mcp.exceptions import ConfigurationError


class TestSettings:
    """Test the Settings class"""

    def test_default_settings(self):
        """Test default settings initialization"""
        settings = Settings()

        assert settings.environment == "development"
        assert settings.host == "127.0.0.1"
        assert settings.port == 8000
        assert settings.max_query_length == 1000
        assert settings.rate_limit_requests_per_minute == 60
        assert settings.log_level == "INFO"
        assert len(settings.secret_key) >= 32  # Should generate secure default

    def test_environment_variable_override(self):
        """Test that environment variables override defaults"""
        with patch.dict(
            os.environ,
            {
                "MCP_ENVIRONMENT": "production",
                "MCP_HOST": "0.0.0.0",
                "MCP_PORT": "9000",
                "MCP_MAX_QUERY_LENGTH": "2000",
                "MCP_LOG_LEVEL": "DEBUG",
            },
        ):
            settings = Settings()

            assert settings.environment == "production"
            assert settings.host == "0.0.0.0"
            assert settings.port == 9000
            assert settings.max_query_length == 2000
            assert settings.log_level == "DEBUG"

    def test_chroma_dir_validation(self):
        """Test ChromaDB directory validation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Should work with existing directory
            settings = Settings(chroma_data_dir=temp_dir)
            assert settings.chroma_data_dir == temp_dir

        # Should fail with non-existent directory
        with pytest.raises(ConfigurationError, match="does not exist"):
            Settings(chroma_data_dir="/non/existent/path")

    def test_openai_key_validation(self):
        """Test OpenAI API key validation"""
        # Should work with valid key format
        settings = Settings(openai_api_key="sk-test123456789")
        assert settings.openai_api_key == "sk-test123456789"

        # Should fail with invalid key format
        with pytest.raises(ConfigurationError, match="must start with 'sk-'"):
            Settings(openai_api_key="invalid-key")

        # Should work with None (optional)
        settings = Settings(openai_api_key=None)
        assert settings.openai_api_key is None

    def test_query_length_validation(self):
        """Test query length validation"""
        # Should work with valid values
        settings = Settings(max_query_length=500)
        assert settings.max_query_length == 500

        # Should fail with too small value
        with pytest.raises(ValueError, match="must be between 10 and 10000"):
            Settings(max_query_length=5)

        # Should fail with too large value
        with pytest.raises(ValueError, match="must be between 10 and 10000"):
            Settings(max_query_length=15000)

    def test_rate_limit_validation(self):
        """Test rate limit validation"""
        # Should work with valid values
        settings = Settings(rate_limit_requests_per_minute=120)
        assert settings.rate_limit_requests_per_minute == 120

        # Should fail with too small value
        with pytest.raises(ValueError, match="must be between 1 and 1000"):
            Settings(rate_limit_requests_per_minute=0)

        # Should fail with too large value
        with pytest.raises(ValueError, match="must be between 1 and 1000"):
            Settings(rate_limit_requests_per_minute=1500)


class TestConfigurationFunctions:
    """Test configuration utility functions"""

    def test_get_settings(self):
        """Test get_settings function"""
        settings = get_settings()
        assert isinstance(settings, Settings)
        assert settings.environment in ["development", "production"]

    @patch("docs_mcp.config.settings")
    def test_validate_environment_success(self, mock_settings):
        """Test successful environment validation"""
        # Mock settings for successful validation
        mock_settings.environment = "development"
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.chroma_data_dir = "/tmp"  # Will be mocked
        mock_settings.secret_key = "a" * 32

        with patch("os.access", return_value=True), patch("pathlib.Path.exists", return_value=True):

            # Should not raise exception
            result = validate_environment()
            assert result is True

    @patch("docs_mcp.config.settings")
    def test_validate_environment_missing_openai_key_production(self, mock_settings):
        """Test validation failure with missing OpenAI key in production"""
        mock_settings.environment = "production"
        mock_settings.openai_api_key = None
        mock_settings.chroma_data_dir = "/tmp"
        mock_settings.secret_key = "a" * 32

        with patch("os.access", return_value=True), patch("pathlib.Path.exists", return_value=True):

            with pytest.raises(ConfigurationError, match="OpenAI API key is required"):
                validate_environment()

    @patch("docs_mcp.config.settings")
    def test_validate_environment_missing_chroma_dir(self, mock_settings):
        """Test validation failure with missing ChromaDB directory"""
        mock_settings.environment = "development"
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.chroma_data_dir = "/nonexistent"
        mock_settings.secret_key = "a" * 32

        with patch("pathlib.Path.exists", return_value=False):

            with pytest.raises(ConfigurationError, match="does not exist"):
                validate_environment()

    @patch("docs_mcp.config.settings")
    def test_validate_environment_insufficient_permissions(self, mock_settings):
        """Test validation failure with insufficient permissions"""
        mock_settings.environment = "development"
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.chroma_data_dir = "/tmp"
        mock_settings.secret_key = "a" * 32

        with patch("pathlib.Path.exists", return_value=True), patch(
            "os.access", return_value=False
        ):

            with pytest.raises(ConfigurationError, match="permissions"):
                validate_environment()

    @patch("docs_mcp.config.settings")
    def test_validate_environment_weak_secret_key(self, mock_settings):
        """Test validation failure with weak secret key"""
        mock_settings.environment = "development"
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.chroma_data_dir = "/tmp"
        mock_settings.secret_key = "weak"

        with patch("os.access", return_value=True), patch("pathlib.Path.exists", return_value=True):

            with pytest.raises(ConfigurationError, match="at least.*characters"):
                validate_environment()


class TestEnvironmentIntegration:
    """Test environment-specific configurations"""

    def test_development_defaults(self):
        """Test development environment defaults"""
        with patch.dict(os.environ, {"MCP_ENVIRONMENT": "development"}, clear=True):
            settings = Settings()

            assert settings.environment == "development"
            assert settings.log_level == "INFO"
            # OpenAI key not required in development
            assert settings.openai_api_key is None

    def test_production_requirements(self):
        """Test production environment requirements"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(
                os.environ,
                {
                    "MCP_ENVIRONMENT": "production",
                    "MCP_OPENAI_API_KEY": "sk-prod-key-123",
                    "MCP_CHROMA_DATA_DIR": temp_dir,
                    "MCP_SECRET_KEY": "super-secure-production-key-32-chars",
                    "MCP_LOG_LEVEL": "WARNING",
                },
                clear=True,
            ):
                settings = Settings()

                assert settings.environment == "production"
                assert settings.openai_api_key == "sk-prod-key-123"
                assert settings.log_level == "WARNING"
                assert settings.chroma_data_dir == temp_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
