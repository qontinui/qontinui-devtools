"""Test module D that creates a three-way circular import: C -> D -> E -> C.

This module is intentionally designed to have a more complex circular
dependency for testing the ImportTracer's ability to detect multi-hop cycles.
"""

from typing import Any


def function_d() -> Any:
    """Function in module D."""
    return "function_d"


# Import from E
from . import circular_e  # noqa: E402, F401


def use_e() -> Any:
    """Use something from module E."""
    return circular_e.function_e()
