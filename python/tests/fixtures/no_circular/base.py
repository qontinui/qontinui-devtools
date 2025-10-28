"""Base module with no circular dependencies."""


class BaseClass:
    """A base class."""

    def __init__(self) -> None:
        self.name = "Base"


def base_function() -> str:
    """A base function."""
    return "base"
