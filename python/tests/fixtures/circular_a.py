"""
Test module A that creates a circular import with module B.

This module is intentionally designed to have a circular dependency
for testing the ImportTracer's ability to detect such issues.
"""


def function_a():
    """Function in module A."""
    return "function_a"


# Import from B creates circular dependency
from fixtures import circular_b  # noqa: E402, F401


def use_b():
    """Use something from module B."""
    return circular_b.function_b()
