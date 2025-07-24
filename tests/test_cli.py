"""Unit tests for CLI functionality.

This module tests the command-line interface entry points
and basic CLI operations.
"""

import unittest
from unittest.mock import patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestCLI(unittest.TestCase):
    """Test cases for CLI functionality."""

    def test_cli_entry_point_exists(self):
        """Test that the CLI main entry point exists and is callable."""
        from docs_mcp.cli import main

        self.assertIsNotNone(main)
        self.assertTrue(callable(main))

    def test_cli_module_imports(self):
        """Test that CLI module can be imported successfully."""
        try:
            import docs_mcp.cli
        except ImportError as e:
            self.fail(f"Failed to import CLI module: {e}")

    @patch("sys.argv", ["docs-mcp", "--help"])
    @patch("docs_mcp.cli.sys.exit")
    def test_cli_help_command(self, mock_exit):
        """Test that CLI responds to help command."""
        from docs_mcp.cli import main

        # Help command should exit with 0
        try:
            main()
        except SystemExit:
            pass

        # Verify help was called (this would exit with 0)
        mock_exit.assert_called()

    def test_cli_has_expected_structure(self):
        """Test that CLI module has expected structure."""
        import docs_mcp.cli

        # Check that module has expected attributes
        self.assertTrue(hasattr(docs_mcp.cli, "main"))

        # Check that main function exists
        main_func = getattr(docs_mcp.cli, "main")
        self.assertTrue(callable(main_func))


if __name__ == "__main__":
    unittest.main()
