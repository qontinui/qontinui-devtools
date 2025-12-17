"""
from typing import Any

from typing import Any

Test module B that creates a circular import with module A.

This module is intentionally designed to have a circular dependency
for testing the ImportTracer's ability to detect such issues.
"""


def function_b() -> Any:
    """Function in module B."""
    return "function_b"


# Import from A creates circular dependency
from fixtures import circular_a  # noqa: E402, F401


def use_a() -> Any:
    """Use something from module A."""
    return circular_a.function_a()
