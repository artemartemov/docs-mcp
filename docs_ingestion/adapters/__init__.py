"""
Documentation source adapters for various frameworks and platforms.
"""

from .python_docs import PythonDocsSource
from .fastapi_docs import FastAPIDocsSource
from .react_docs import ReactDocsSource
from .swiftui_docs import SwiftUIDocsSource
from .tailwind_docs import TailwindDocsSource
from .figma_docs import FigmaDocsSource

__all__ = [
    "PythonDocsSource", 
    "FastAPIDocsSource", 
    "ReactDocsSource",
    "SwiftUIDocsSource",
    "TailwindDocsSource", 
    "FigmaDocsSource"
]