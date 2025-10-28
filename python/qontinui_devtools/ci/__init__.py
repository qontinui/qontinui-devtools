"""CI/CD integration utilities for qontinui-devtools.

This package provides tools for integrating qontinui-devtools into
continuous integration and continuous deployment pipelines.

Modules:
    quality_gates: Enforce quality thresholds in CI/CD
    pr_comment: Generate PR comments with analysis results
    pre_commit_hooks: Pre-commit hooks for local development
"""

from qontinui_devtools.ci.quality_gates import check_gates, QualityGateChecker
from qontinui_devtools.ci.pr_comment import generate_pr_comment, generate_comment

__all__ = [
    "check_gates",
    "QualityGateChecker",
    "generate_pr_comment",
    "generate_comment",
]
