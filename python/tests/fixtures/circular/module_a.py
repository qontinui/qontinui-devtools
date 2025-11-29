"""Module A - Part of a circular dependency test fixture.

This module imports module_b, which imports module_c, which imports back to module_a,
creating a circular dependency: a -> b -> c -> a
"""


# This import creates a circular dependency
from .module_b import ClassB, FunctionB


class ClassA:
    """A simple class in module A."""

    def __init__(self) -> None:
        self.name = "ClassA"
        self.value = 42

    def use_b(self) -> str:
        """Use something from module B."""
        return FunctionB()


def function_a() -> str:
    """A simple function in module A."""
    return "Function A"


def use_class_b() -> ClassB:
    """Create an instance of ClassB."""
    return ClassB()
