"""
Test module D that creates a three-way circular import: C -> D -> E -> C.

This module is intentionally designed to have a more complex circular
dependency for testing the ImportTracer's ability to detect multi-hop cycles.
"""


def function_d():
    """Function in module D."""
    return "function_d"


# Import from E
from fixtures import circular_e  # noqa: E402, F401


def use_e():
    """Use something from module E."""
    return circular_e.function_e()
