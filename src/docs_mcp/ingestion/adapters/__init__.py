"""
Documentation source adapters for various frameworks and platforms.
"""

from .python_docs import PythonDocsSource
from .fastapi_docs import FastAPIDocsSource
from .react_docs import ReactDocsSource
from .swiftui_docs import SwiftUIDocsSource
from .tailwind_docs import TailwindDocsSource
from .figma_docs import FigmaDocsSource
from .figma_screenshot_docs import FigmaScreenshotDocsSource
from .figma_file_docs import FigmaFileDocsSource
from .figma_json_docs import FigmaJsonDocsSource
from .figma_plugin_docs import FigmaPluginDocsSource
from .mdn_css_docs import MDNCSSDocsSource

__all__ = [
    "PythonDocsSource",
    "FastAPIDocsSource",
    "ReactDocsSource",
    "SwiftUIDocsSource",
    "TailwindDocsSource",
    "FigmaDocsSource",
    "FigmaScreenshotDocsSource",
    "FigmaFileDocsSource",
    "FigmaJsonDocsSource",
    "FigmaPluginDocsSource",
    "MDNCSSDocsSource",
]
