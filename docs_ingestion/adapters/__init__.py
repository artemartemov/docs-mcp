"""
Documentation source adapters for various frameworks and platforms.
"""

from .python_docs import PythonDocsSource
from .fastapi_docs import FastAPIDocsSource
from .react_docs import ReactDocsSource

__all__ = ["PythonDocsSource", "FastAPIDocsSource", "ReactDocsSource"]