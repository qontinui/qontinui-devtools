"""
Documentation generation for Python code.

This module provides tools for automatically generating beautiful documentation
from Python source code, including docstrings, type hints, and code structure.
"""

from .doc_generator import (
    ASTDocExtractor,
    DocumentationGenerator,
    DocstringParser,
)
from .models import (
    DocItem,
    DocItemType,
    DocstringStyle,
    DocumentationTree,
    Example,
    OutputFormat,
    Parameter,
)

__all__ = [
    "DocumentationGenerator",
    "DocumentationTree",
    "DocItem",
    "DocItemType",
    "Parameter",
    "Example",
    "OutputFormat",
    "DocstringStyle",
    "DocstringParser",
    "ASTDocExtractor",
]
