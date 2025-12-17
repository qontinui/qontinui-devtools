"""
Test module E that creates a three-way circular import: C -> D -> E -> C.

This module is intentionally designed to have a more complex circular
dependency for testing the ImportTracer's ability to detect multi-hop cycles.
"""


def function_e() -> None:
    """Function in module E."""
    return "function_e"


# Import from C to complete the cycle
from fixtures import circular_c  # noqa: E402, F401


def use_c() -> None:
    """Use something from module C."""
    return circular_c.function_c()
