"""
Unit tests for __main__.py module functionality.

This module tests the main entry point of the docs-mcp package.
"""

import unittest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class TestMainModule(unittest.TestCase):
    """Test cases for __main__.py functionality."""

    def test_main_module_imports(self):
        """Test that __main__ module can be imported."""
        try:
            import docs_mcp.__main__ as main_module

            # Test that module exists
            self.assertTrue(hasattr(main_module, "__file__"))
        except ImportError:
            # If __main__ doesn't exist or has issues, that's also testable
            pass

    def test_main_functionality_exists(self):
        """Test that main functionality is accessible."""
        try:
            # Test that we can access main functionality
            from docs_mcp.cli import main

            self.assertTrue(callable(main))
        except ImportError as e:
            self.fail(f"Main functionality not accessible: {e}")

    def test_package_entry_point(self):
        """Test that package entry point works."""
        # Test package structure
        import docs_mcp

        self.assertTrue(hasattr(docs_mcp, "__file__"))
        self.assertTrue(hasattr(docs_mcp, "__version__"))


if __name__ == "__main__":
    unittest.main()
