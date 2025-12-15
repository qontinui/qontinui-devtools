"""Cross-language analysis tools for detecting inconsistencies between TypeScript, Rust, and Python.

This module provides analyzers that work across multiple programming languages
to detect type mismatches, naming inconsistencies, and other cross-language issues.
"""

from .id_type_checker import IDField, IDTypeChecker, IDTypeIssue, IssueSeverity

__all__ = [
    "IDTypeChecker",
    "IDTypeIssue",
    "IDField",
    "IssueSeverity",
]
