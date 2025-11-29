"""Module B - Part of a circular dependency test fixture.

This module imports module_c, completing the circular chain.
"""


# This import continues the circular dependency chain
from .module_c import ClassC, FunctionC


class ClassB:
    """A simple class in module B."""

    def __init__(self) -> None:
        self.name = "ClassB"
        self.items: list[str] = []

    def use_c(self) -> str:
        """Use something from module C."""
        return FunctionC()


def FunctionB() -> str:
    """A simple function in module B."""
    return "Function B"


def use_class_c() -> ClassC:
    """Create an instance of ClassC."""
    return ClassC()
