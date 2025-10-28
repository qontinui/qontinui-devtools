"""Derived module that imports base - no circular dependency."""

from .base import BaseClass, base_function


class DerivedClass(BaseClass):
    """A derived class."""

    def __init__(self) -> None:
        super().__init__()
        self.name = "Derived"


def derived_function() -> str:
    """A derived function."""
    return f"derived calls {base_function()}"
