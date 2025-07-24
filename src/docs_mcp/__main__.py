#!/usr/bin/env python3
"""
Main entry point for docs-mcp package.
Allows running the package as: python -m docs_mcp
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())
