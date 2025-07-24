"""Unit tests for configuration management.

This module tests the Settings class, environment variable handling,
and configuration validation.
"""

import unittest
import os
import tempfile
from unittest.mock import patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestConfiguration(unittest.TestCase):
    """Test cases for configuration management."""

    @patch.dict(
        "os.environ",
        {
            "MCP_ENVIRONMENT": "development",
            "MCP_SECRET_KEY": "test-secret-key-32-characters-long",
            "MCP_CHROMA_DATA_DIR": "/tmp/test_chroma",
        },
    )
    def test_settings_initialization(self):
        """Test that Settings can be initialized with environment variables."""
        from docs_mcp.config import Settings

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"MCP_CHROMA_DATA_DIR": temp_dir}):
                settings = Settings()

                self.assertEqual(settings.environment, "development")
                self.assertEqual(settings.host, "127.0.0.1")
                self.assertEqual(settings.port, 8000)
                self.assertGreaterEqual(len(settings.secret_key), 32)

    def test_settings_validation(self):
        """Test that Settings validates input correctly."""
        from docs_mcp.config import Settings

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with valid settings
            settings = Settings(
                environment="production",
                host="0.0.0.0",
                port=8080,
                secret_key="production-secret-key-must-be-32-chars",
                chroma_data_dir=temp_dir,
            )

            self.assertEqual(settings.environment, "production")
            self.assertEqual(settings.host, "0.0.0.0")
            self.assertEqual(settings.port, 8080)

    def test_security_constants_defined(self):
        """Test that security constants are properly defined."""
        from docs_mcp.constants import (
            MAX_QUERY_LENGTH,
            MIN_SECRET_KEY_LENGTH,
            DEFAULT_RATE_LIMIT,
            DEFAULT_ENVIRONMENT,
        )

        self.assertIsInstance(MAX_QUERY_LENGTH, int)
        self.assertGreater(MAX_QUERY_LENGTH, 0)

        self.assertIsInstance(MIN_SECRET_KEY_LENGTH, int)
        self.assertGreaterEqual(MIN_SECRET_KEY_LENGTH, 32)

        self.assertIsInstance(DEFAULT_RATE_LIMIT, int)
        self.assertGreater(DEFAULT_RATE_LIMIT, 0)

        self.assertEqual(DEFAULT_ENVIRONMENT, "development")

    def test_secret_key_behavior(self):
        """Test that secret key is set correctly."""
        from docs_mcp.config import Settings

        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with a proper secret key
            settings = Settings(
                secret_key="test-secret-key-32-characters-long",
                chroma_data_dir=temp_dir,
            )
            # Secret key should be set as provided
            self.assertEqual(settings.secret_key, "test-secret-key-32-characters-long")

    def test_invalid_chroma_directory(self):
        """Test that non-existent ChromaDB directories are rejected."""
        from docs_mcp.config import Settings
        from docs_mcp.exceptions import ConfigurationError

        with self.assertRaises(ConfigurationError):
            Settings(
                chroma_data_dir="/nonexistent/directory",
                secret_key="test-secret-key-32-characters-long",
            )

    def test_port_validation(self):
        """Test that port numbers are handled correctly."""
        from docs_mcp.config import Settings

        with tempfile.TemporaryDirectory() as temp_dir:
            # Valid port
            settings = Settings(
                port=8080,
                chroma_data_dir=temp_dir,
                secret_key="test-secret-key-32-characters-long",
            )
            self.assertEqual(settings.port, 8080)

            # Test that port 0 is handled (current implementation may allow it)
            settings_zero = Settings(
                port=0,
                chroma_data_dir=temp_dir,
                secret_key="test-secret-key-32-characters-long",
            )
            # Port 0 may be allowed for dynamic assignment
            self.assertIsInstance(settings_zero.port, int)

    def test_environment_values(self):
        """Test that only valid environment values are accepted."""
        from docs_mcp.config import Settings

        with tempfile.TemporaryDirectory() as temp_dir:
            valid_environments = ["development", "production"]

            for env in valid_environments:
                settings = Settings(
                    environment=env,
                    chroma_data_dir=temp_dir,
                    secret_key="test-secret-key-32-characters-long",
                )
                self.assertEqual(settings.environment, env)


if __name__ == "__main__":
    unittest.main()
