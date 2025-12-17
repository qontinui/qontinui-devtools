"""
from typing import Any

from typing import Any

Test module C that creates a three-way circular import: C -> D -> E -> C.

This module is intentionally designed to have a more complex circular
dependency for testing the ImportTracer's ability to detect multi-hop cycles.
"""


def function_c() -> Any:
    """Function in module C."""
    return "function_c"


# Import from D, which imports E, which imports C
from fixtures import circular_d  # noqa: E402, F401


def use_d() -> Any:
    """Use something from module D."""
    return circular_d.function_d()
