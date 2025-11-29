"""Decorator API for race condition testing.

This module provides convenient decorators for marking functions to be
tested concurrently for race conditions.
"""

from collections.abc import Callable
from typing import Any

from .race_tester import RaceConditionTester, RaceTestResult


def concurrent_test(
    threads: int = 10, iterations: int = 100, timeout: float = 30.0, track_state: bool = False
) -> Callable:
    """Decorator to run test concurrently.

    This decorator wraps a function to run it concurrently with multiple
    threads and detect race conditions.

    Args:
        threads: Number of concurrent threads
        iterations: Number of iterations per thread
        timeout: Maximum time to wait for all threads (seconds)
        track_state: Whether to use instrumentation to track state access

    Returns:
        Decorator function

    Example:
        @concurrent_test(threads=20, iterations=200)
        def test_my_function():
            # Test code
            cache.get("key")
            cache.set("key", "value")

        result = test_my_function()
        if result.race_detected:
            print("Race condition found!")
    """

    def decorator(func: Callable) -> Callable:
        def wrapper(*args: Any, **kwargs: Any) -> RaceTestResult:
            tester = RaceConditionTester(
                threads=threads, iterations=iterations, timeout=timeout, track_state=track_state
            )
            return tester.test_function(func, *args, **kwargs)

        # Preserve function metadata
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__module__ = func.__module__

        return wrapper

    return decorator


def stress_test(threads: int = 50, iterations: int = 1000, timeout: float = 60.0) -> Callable:
    """Decorator for heavy stress testing.

    Similar to concurrent_test but with higher defaults for more
    aggressive testing.

    Args:
        threads: Number of concurrent threads (default: 50)
        iterations: Number of iterations per thread (default: 1000)
        timeout: Maximum time to wait for all threads (default: 60s)

    Returns:
        Decorator function

    Example:
        @stress_test(threads=100, iterations=10000)
        def test_high_load():
            # Test code under heavy load
            pass
    """
    return concurrent_test(
        threads=threads, iterations=iterations, timeout=timeout, track_state=False
    )


def tracked_test(threads: int = 10, iterations: int = 100, timeout: float = 30.0) -> Callable:
    """Decorator for concurrent test with state tracking.

    This decorator enables state instrumentation to detect race conditions
    at the access level.

    Args:
        threads: Number of concurrent threads
        iterations: Number of iterations per thread
        timeout: Maximum time to wait for all threads (seconds)

    Returns:
        Decorator function

    Example:
        @tracked_test(threads=10, iterations=50)
        def test_with_tracking():
            # Test code with state tracking enabled
            pass
    """
    return concurrent_test(
        threads=threads, iterations=iterations, timeout=timeout, track_state=True
    )
