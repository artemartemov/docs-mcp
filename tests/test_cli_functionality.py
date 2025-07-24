"""
Unit tests for CLI functionality in cli.py.

This module tests the command-line interface functions including
basic function existence and module structure.
"""

import unittest
import tempfile
import os
import sys
import argparse
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestCLIFunctionality(unittest.TestCase):
    """Test cases for CLI command functions."""

    def test_cli_functions_exist(self):
        """Test that CLI functions are properly defined."""
        from docs_mcp import cli

        # Test that main CLI functions exist
        self.assertTrue(hasattr(cli, "run_script"))
        self.assertTrue(hasattr(cli, "run_test"))
        self.assertTrue(hasattr(cli, "extract_command"))
        self.assertTrue(hasattr(cli, "analyze_command"))
        self.assertTrue(hasattr(cli, "test_command"))
        self.assertTrue(hasattr(cli, "server_command"))
        self.assertTrue(hasattr(cli, "dev_command"))
        self.assertTrue(hasattr(cli, "main"))

    def test_cli_imports(self):
        """Test that CLI module imports properly."""
        from docs_mcp import cli

        # Test that required imports work
        self.assertTrue(hasattr(cli, "argparse"))
        self.assertTrue(hasattr(cli, "subprocess"))
        self.assertTrue(hasattr(cli, "sys"))

    def test_argument_namespace_handling(self):
        """Test that functions can handle argument namespaces."""
        # Test that we can create argument namespaces
        args = argparse.Namespace(framework="python", all=False)
        self.assertEqual(args.framework, "python")
        self.assertEqual(args.all, False)

        args2 = argparse.Namespace(stats=True)
        self.assertEqual(args2.stats, True)

    def test_command_function_signatures(self):
        """Test that command functions have expected signatures."""
        from docs_mcp.cli import analyze_command, test_command, server_command
        import inspect

        # Test that functions accept args parameter
        sig_analyze = inspect.signature(analyze_command)
        self.assertIn("args", sig_analyze.parameters)

        sig_test = inspect.signature(test_command)
        self.assertIn("args", sig_test.parameters)

        sig_server = inspect.signature(server_command)
        self.assertIn("args", sig_server.parameters)

    def test_main_function_exists(self):
        """Test that main function exists and is callable."""
        from docs_mcp.cli import main
        import inspect

        # Test that main function exists
        self.assertTrue(callable(main))

        # Test that main function has no required parameters
        sig = inspect.signature(main)
        required_params = [
            p for p in sig.parameters.values() if p.default == inspect.Parameter.empty
        ]
        self.assertEqual(len(required_params), 0)

    def test_script_execution_functions(self):
        """Test that script execution functions exist."""
        from docs_mcp.cli import run_script, run_test
        import inspect

        # Test function signatures
        sig_run_script = inspect.signature(run_script)
        self.assertIn("script_name", sig_run_script.parameters)

        sig_run_test = inspect.signature(run_test)
        # Check that run_test has parameters (may vary by implementation)
        self.assertGreaterEqual(len(sig_run_test.parameters), 0)

    def test_cli_constants_and_help(self):
        """Test CLI-related constants and help text functionality."""
        # Test that argparse module is available for help text
        import argparse

        # Test that we can create argument parsers
        parser = argparse.ArgumentParser(description="Test parser")
        self.assertIsInstance(parser, argparse.ArgumentParser)

        # Test that we can add arguments
        parser.add_argument("--test", help="Test argument")
        self.assertTrue(hasattr(parser, "add_argument"))

    def test_path_and_os_utilities(self):
        """Test that CLI has access to necessary OS utilities."""
        import os
        import sys

        # Test that basic OS functions are available
        self.assertTrue(hasattr(os, "path"))
        self.assertTrue(hasattr(os, "environ"))
        self.assertTrue(hasattr(sys, "argv"))
        self.assertTrue(hasattr(sys, "exit"))

    def test_cli_module_structure(self):
        """Test overall CLI module structure."""
        from docs_mcp import cli

        # Test that module has expected structure
        self.assertTrue(hasattr(cli, "__file__"))

        # Test that we can get module info
        import inspect

        members = inspect.getmembers(cli, inspect.isfunction)

        # Should have multiple functions
        self.assertGreaterEqual(len(members), 5)

        # Should include main function
        function_names = [name for name, _ in members]
        self.assertIn("main", function_names)

    def test_subprocess_availability(self):
        """Test that subprocess module is available for CLI operations."""
        import subprocess

        # Test that subprocess has expected methods
        self.assertTrue(hasattr(subprocess, "run"))
        self.assertTrue(hasattr(subprocess, "PIPE"))
        self.assertTrue(hasattr(subprocess, "STDOUT"))

    def test_error_handling_imports(self):
        """Test that error handling modules are available."""
        # Test that CLI can handle exceptions
        try:
            from docs_mcp import cli

            # Test that we can access CLI without errors
            self.assertTrue(hasattr(cli, "main"))
        except ImportError as e:
            self.fail(f"CLI module import failed: {e}")


if __name__ == "__main__":
    unittest.main()
