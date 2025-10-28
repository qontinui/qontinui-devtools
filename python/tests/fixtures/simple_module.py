"""
Simple test module without circular dependencies.

This module is used to test that the ImportTracer correctly reports
when there are no circular dependencies.
"""


def simple_function():
    """A simple function."""
    return "simple"


class SimpleClass:
    """A simple class."""

    def method(self):
        """A simple method."""
        return "method"
