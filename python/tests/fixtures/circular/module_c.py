"""Module C - Part of a circular dependency test fixture.

This module imports back to module_a, closing the circular dependency loop.
"""

from typing import TYPE_CHECKING

# This import closes the circular dependency loop
from .module_a import ClassA, function_a


class ClassC:
    """A simple class in module C."""

    def __init__(self) -> None:
        self.name = "ClassC"
        self.data: dict[str, int] = {}

    def use_a(self) -> str:
        """Use something from module A."""
        return function_a()


def FunctionC() -> str:
    """A simple function in module C."""
    return "Function C"


def use_class_a() -> ClassA:
    """Create an instance of ClassA."""
    return ClassA()
