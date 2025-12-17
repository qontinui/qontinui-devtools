"""Pre-built test scenarios for common race conditions.

This module provides ready-to-use test scenarios for detecting common
race condition patterns.
"""

import threading
from typing import Any

from .race_tester import RaceConditionTester, RaceTestResult


def test_dictionary_concurrent_access(threads: int = 10, iterations: int = 10) -> RaceTestResult:
    """Test concurrent dictionary access.

    Tests if concurrent reads and writes to a dictionary without
    synchronization cause race conditions.

    Args:
        threads: Number of concurrent threads
        iterations: Number of iterations per thread

    Returns:
        RaceTestResult with test results
    """
    shared_dict: dict[str, int] = {}

    def worker(thread_id: int) -> None:
        for i in range(100):
            key = f"key_{thread_id}_{i}"
            shared_dict[key] = i
            value = shared_dict.get(key)
            if value != i:
                raise ValueError(f"Expected {i}, got {value}")

    tester = RaceConditionTester(threads=threads, iterations=iterations)
    return tester.test_function(worker, 0)


def test_check_then_act(threads: int = 10, iterations: int = 100) -> RaceTestResult:
    """Test classic check-then-act race condition.

    This is the classic "if not exists, then create" pattern that
    commonly causes race conditions.

    Args:
        threads: Number of concurrent threads
        iterations: Number of iterations per thread

    Returns:
        RaceTestResult with test results
    """
    cache: dict[str, str] = {}

    def worker() -> None:
        key = "shared_key"
        # Race condition: check and act are not atomic
        if key not in cache:
            cache[key] = "value"

    tester = RaceConditionTester(threads=threads, iterations=iterations)
    return tester.test_function(worker)


def test_check_then_act_safe(threads: int = 10, iterations: int = 100) -> RaceTestResult:
    """Test thread-safe check-then-act pattern.

    Same as test_check_then_act but with proper synchronization.

    Args:
        threads: Number of concurrent threads
        iterations: Number of iterations per thread

    Returns:
        RaceTestResult with test results (should pass)
    """
    cache: dict[str, str] = {}
    lock = threading.Lock()

    def worker() -> None:
        key = "shared_key"
        with lock:
            if key not in cache:
                cache[key] = "value"

    tester = RaceConditionTester(threads=threads, iterations=iterations)
    return tester.test_function(worker)


def test_counter_increment(
    threads: int = 10, iterations: int = 100, expected_total: int | None = None
) -> RaceTestResult:
    """Test concurrent counter increment.

    Tests if incrementing a counter without synchronization loses updates
    due to race conditions.

    Args:
        threads: Number of concurrent threads
        iterations: Number of iterations per thread
        expected_total: Expected final counter value

    Returns:
        RaceTestResult with test results
    """
    counter = {"value": 0}

    if expected_total is None:
        expected_total = threads * iterations * 100

    def worker() -> None:
        for _ in range(100):
            # Race condition: read-modify-write is not atomic
            counter["value"] += 1

    tester = RaceConditionTester(threads=threads, iterations=iterations)
    result = tester.test_function(worker)

    # Check if final count is correct
    if counter["value"] != expected_total:
        result.race_detected = True
        result.failure_details.append(
            f"Counter mismatch: expected {expected_total}, got {counter['value']}"
        )

    return result


def test_counter_increment_safe(
    threads: int = 10, iterations: int = 100, expected_total: int | None = None
) -> RaceTestResult:
    """Test thread-safe counter increment.

    Same as test_counter_increment but with proper synchronization.

    Args:
        threads: Number of concurrent threads
        iterations: Number of iterations per thread
        expected_total: Expected final counter value

    Returns:
        RaceTestResult with test results (should pass)
    """
    counter = {"value": 0}
    lock = threading.Lock()

    if expected_total is None:
        expected_total = threads * iterations * 100

    def worker() -> None:
        for _ in range(100):
            with lock:
                counter["value"] += 1

    tester = RaceConditionTester(threads=threads, iterations=iterations)
    result = tester.test_function(worker)

    # Check if final count is correct
    if counter["value"] != expected_total:
        result.failure_details.append(
            f"Counter mismatch: expected {expected_total}, got {counter['value']}"
        )

    return result


def test_lazy_initialization(threads: int = 10, iterations: int = 100) -> RaceTestResult:
    """Test lazy initialization pattern.

    Tests if lazy initialization without double-checked locking
    causes race conditions.

    Args:
        threads: Number of concurrent threads
        iterations: Number of iterations per thread

    Returns:
        RaceTestResult with test results
    """
    instance: dict[str, Any] | None = None
    creation_count = {"value": 0}

    def get_instance() -> dict[str, Any]:
        nonlocal instance
        # Race condition: multiple threads might create instance
        if instance is None:
            creation_count["value"] += 1
            instance = {"created": True}
        return instance

    def worker() -> None:
        get_instance()

    tester = RaceConditionTester(threads=threads, iterations=iterations)
    result = tester.test_function(worker)

    # Check if instance was created multiple times
    if creation_count["value"] > 1:
        result.race_detected = True
        result.failure_details.append(
            f"Instance created {creation_count['value']} times (expected 1)"
        )

    return result


def test_lazy_initialization_safe(threads: int = 10, iterations: int = 100) -> RaceTestResult:
    """Test thread-safe lazy initialization.

    Same as test_lazy_initialization but with proper double-checked locking.

    Args:
        threads: Number of concurrent threads
        iterations: Number of iterations per thread

    Returns:
        RaceTestResult with test results (should pass)
    """
    instance: dict[str, Any] | None = None
    creation_count = {"value": 0}
    lock = threading.Lock()

    def get_instance() -> dict[str, Any]:
        nonlocal instance
        if instance is None:
            with lock:
                # Double-checked locking
                if instance is None:
                    creation_count["value"] += 1
                    instance = {"created": True}
        return instance

    def worker() -> None:
        get_instance()

    tester = RaceConditionTester(threads=threads, iterations=iterations)
    result = tester.test_function(worker)

    # Check if instance was created exactly once
    if creation_count["value"] != 1:
        result.failure_details.append(
            f"Instance created {creation_count['value']} times (expected 1)"
        )

    return result


def test_list_append(threads: int = 10, iterations: int = 100) -> RaceTestResult:
    """Test concurrent list append.

    Tests if concurrent appends to a list cause race conditions.
    Note: Python's list.append() is actually thread-safe due to GIL,
    but this tests the general pattern.

    Args:
        threads: Number of concurrent threads
        iterations: Number of iterations per thread

    Returns:
        RaceTestResult with test results
    """
    shared_list: list[int] = []
    expected_length = threads * iterations * 100

    def worker(thread_id: int) -> None:
        for i in range(100):
            shared_list.append(thread_id * 1000 + i)

    tester = RaceConditionTester(threads=threads, iterations=iterations)
    result = tester.test_function(worker, 0)

    # Check if all items were added
    if len(shared_list) != expected_length:
        result.race_detected = True
        result.failure_details.append(
            f"List length mismatch: expected {expected_length}, got {len(shared_list)}"
        )

    return result


def run_all_scenarios() -> dict[str, RaceTestResult]:
    """Run all test scenarios.

    Returns:
        Dictionary mapping scenario name to result
    """
    scenarios: dict[str, Any] = {
        "dictionary_access": test_dictionary_concurrent_access,
        "check_then_act": test_check_then_act,
        "check_then_act_safe": test_check_then_act_safe,
        "counter_increment": test_counter_increment,
        "counter_increment_safe": test_counter_increment_safe,
        "lazy_initialization": test_lazy_initialization,
        "lazy_initialization_safe": test_lazy_initialization_safe,
        "list_append": test_list_append,
    }

    results: dict[Any, Any] = {}
    for name, scenario_func in scenarios.items():
        print(f"Running scenario: {name}...")
        results[name] = scenario_func()

    return results
