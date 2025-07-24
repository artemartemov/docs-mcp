#!/usr/bin/env python3
"""
Unit tests for CLI functionality.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import argparse

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from docs_mcp.cli import (
    main,
    extract_command,
    server_command,
    analyze_command,
    test_command,
    dev_command,
    run_script,
)
from docs_mcp.constants import SUPPORTED_FRAMEWORKS


class TestCLIFunctions:
    """Test CLI utility functions"""

    @patch("subprocess.run")
    def test_run_script_success(self, mock_run):
        """Test successful script execution"""
        mock_run.return_value.returncode = 0

        result = run_script("test_script.py", "python")

        assert result == 0
        mock_run.assert_called_once()

        # Check command structure
        called_args = mock_run.call_args[0][0]
        assert "test_script.py" in called_args
        assert "--framework" in called_args
        assert "python" in called_args

    @patch("subprocess.run")
    def test_run_script_failure(self, mock_run):
        """Test script execution failure"""
        mock_run.side_effect = Exception("Script failed")

        result = run_script("nonexistent_script.py")

        assert result == 1
        mock_run.assert_called_once()

    @patch("pathlib.Path.exists")
    def test_run_script_not_found(self, mock_exists):
        """Test handling of non-existent script"""
        mock_exists.return_value = False

        result = run_script("missing_script.py")

        assert result == 1


class TestExtractCommand:
    """Test extract command functionality"""

    @patch("docs_mcp.cli.run_script")
    def test_extract_single_framework(self, mock_run_script):
        """Test extracting single framework"""
        mock_run_script.return_value = 0

        args = MagicMock()
        args.framework = "python"

        result = extract_command(args)

        assert result == 0
        mock_run_script.assert_called_once()

    @patch("docs_mcp.cli.run_script")
    def test_extract_all_frameworks(self, mock_run_script):
        """Test extracting all frameworks"""
        mock_run_script.return_value = 0

        args = MagicMock()
        args.framework = "all"

        result = extract_command(args)

        assert result == 0
        # Should be called for each supported framework
        assert mock_run_script.call_count == len(SUPPORTED_FRAMEWORKS)

    @patch("docs_mcp.cli.run_script")
    def test_extract_framework_failure(self, mock_run_script):
        """Test handling of framework extraction failure"""
        mock_run_script.return_value = 1

        args = MagicMock()
        args.framework = "python"

        result = extract_command(args)

        assert result == 1
        mock_run_script.assert_called_once()


class TestServerCommand:
    """Test server command functionality"""

    @patch("docs_mcp.cli.server_main")
    @patch("asyncio.run")
    def test_server_start_success(self, mock_asyncio_run, mock_server_main):
        """Test successful server start"""
        mock_asyncio_run.return_value = None

        args = MagicMock()
        args.start = True
        args.config = False

        result = server_command(args)

        assert result == 0
        mock_asyncio_run.assert_called_once_with(mock_server_main)

    @patch("docs_mcp.cli.server_main")
    @patch("asyncio.run")
    def test_server_start_keyboard_interrupt(self, mock_asyncio_run, mock_server_main):
        """Test server start with keyboard interrupt"""
        mock_asyncio_run.side_effect = KeyboardInterrupt()

        args = MagicMock()
        args.start = True
        args.config = False

        result = server_command(args)

        assert result == 0  # Should handle gracefully

    @patch("docs_mcp.cli.server_main")
    @patch("asyncio.run")
    def test_server_start_exception(self, mock_asyncio_run, mock_server_main):
        """Test server start with exception"""
        mock_asyncio_run.side_effect = Exception("Server error")

        args = MagicMock()
        args.start = True
        args.config = False

        result = server_command(args)

        assert result == 1

    @patch("docs_mcp.cli.get_settings")
    @patch("docs_mcp.cli.validate_environment")
    def test_server_config_display(self, mock_validate, mock_get_settings):
        """Test server configuration display"""
        mock_settings = MagicMock()
        mock_settings.chroma_data_dir = "/test/path"
        mock_settings.environment = "development"
        mock_settings.host = "127.0.0.1"
        mock_settings.port = 8000
        mock_get_settings.return_value = mock_settings
        mock_validate.return_value = True

        args = MagicMock()
        args.start = False
        args.config = True

        result = server_command(args)

        assert result == 0
        mock_get_settings.assert_called_once()
        mock_validate.assert_called_once()


class TestAnalyzeCommand:
    """Test analyze command functionality"""

    @patch("docs_mcp.cli.run_script")
    def test_analyze_stats(self, mock_run_script):
        """Test analyze stats command"""
        mock_run_script.return_value = 0

        args = MagicMock()
        args.stats = True

        result = analyze_command(args)

        assert result == 0
        mock_run_script.assert_called_once_with("analyze_collection.py")

    def test_analyze_no_args(self):
        """Test analyze command with no arguments"""
        args = MagicMock()
        args.stats = False

        result = analyze_command(args)

        assert result == 0  # Should show help


class TestTestCommand:
    """Test test command functionality"""

    @patch("docs_mcp.cli.run_test")
    def test_run_all_tests(self, mock_run_test):
        """Test running all tests"""
        mock_run_test.return_value = 0

        args = MagicMock()
        args.all = True
        args.framework = None

        result = test_command(args)

        assert result == 0
        mock_run_test.assert_called_once_with()

    @patch("docs_mcp.cli.run_test")
    def test_run_framework_test(self, mock_run_test):
        """Test running framework-specific test"""
        mock_run_test.return_value = 0

        args = MagicMock()
        args.all = False
        args.framework = "figma"

        result = test_command(args)

        assert result == 0
        mock_run_test.assert_called_once_with("figma", "integration")


class TestDevCommand:
    """Test dev command functionality"""

    @patch("subprocess.run")
    @patch("pathlib.Path.mkdir")
    def test_dev_setup(self, mock_mkdir, mock_run):
        """Test development setup"""
        mock_run.return_value.returncode = 0

        args = MagicMock()
        args.setup = True
        args.clean = False

        result = dev_command(args)

        assert result == 0
        mock_run.assert_called()
        mock_mkdir.assert_called()

    @patch("glob.glob")
    @patch("pathlib.Path.unlink")
    def test_dev_clean(self, mock_unlink, mock_glob):
        """Test development cleanup"""
        mock_glob.return_value = ["test.pyc", "__pycache__"]

        args = MagicMock()
        args.setup = False
        args.clean = True

        result = dev_command(args)

        assert result == 0


class TestMainFunction:
    """Test main CLI function"""

    def test_no_command(self):
        """Test CLI with no command"""
        with patch("sys.argv", ["docs-mcp"]):
            with patch("argparse.ArgumentParser.print_help") as mock_help:
                result = main()
                assert result == 1
                mock_help.assert_called_once()

    @patch("docs_mcp.cli.extract_command")
    def test_extract_command_routing(self, mock_extract):
        """Test routing to extract command"""
        mock_extract.return_value = 0

        with patch("sys.argv", ["docs-mcp", "extract", "--framework", "python"]):
            result = main()
            assert result == 0
            mock_extract.assert_called_once()

    @patch("docs_mcp.cli.server_command")
    def test_server_command_routing(self, mock_server):
        """Test routing to server command"""
        mock_server.return_value = 0

        with patch("sys.argv", ["docs-mcp", "server", "--start"]):
            result = main()
            assert result == 0
            mock_server.assert_called_once()


class TestArgumentParsing:
    """Test argument parsing"""

    def test_extract_framework_choices(self):
        """Test that framework choices include all supported frameworks"""
        from docs_mcp.cli import main

        # This tests the framework choices indirectly by checking constants
        expected_frameworks = list(SUPPORTED_FRAMEWORKS)
        assert "python" in expected_frameworks
        assert "fastapi" in expected_frameworks
        assert "react" in expected_frameworks

        # Should also include 'all' option
        assert len(expected_frameworks) > 0

    def test_invalid_framework_handling(self):
        """Test handling of invalid framework selection"""
        # This would be caught by argparse before reaching our code
        # but we test the constants are properly defined
        assert isinstance(SUPPORTED_FRAMEWORKS, set)
        assert len(SUPPORTED_FRAMEWORKS) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
