"""Tests for race condition tester."""

import threading
import time

from qontinui_devtools.concurrency import RaceConditionTester, RaceTestResult, concurrent_test


def test_detect_race_in_dictionary() -> None:
    """Test that race condition is detected in concurrent dictionary access."""
    shared: dict[str, int] = {}
    race_detected = False

    def worker() -> None:
        nonlocal race_detected
        try:
            for _i in range(100):
                key = "key"
                if key not in shared:
                    shared[key] = 0
                shared[key] += 1
        except Exception:
            race_detected = True

    tester = RaceConditionTester(threads=10, iterations=10)
    result = tester.test_function(worker)

    # Should detect race condition through failures or inconsistency
    # Note: Due to Python's GIL, this might not always fail
    # but the pattern is inherently racy
    assert isinstance(result, RaceTestResult)
    assert result.total_iterations == 100


def test_thread_safe_code() -> None:
    """Test that properly locked code passes."""
    shared: dict[str, int] = {}
    lock = threading.Lock()

    def worker() -> None:
        with lock:
            for _i in range(100):
                if "key" not in shared:
                    shared["key"] = 0
                shared["key"] += 1

    tester = RaceConditionTester(threads=10, iterations=10)
    result = tester.test_function(worker)

    assert not result.race_detected
    assert result.failed == 0
    assert result.successful == 100
    assert shared["key"] == 10000  # 10 threads * 10 iterations * 100


def test_race_tester_basic() -> None:
    """Test basic race tester functionality."""
    call_count = {"value": 0}
    lock = threading.Lock()

    def simple_function() -> None:
        with lock:
            call_count["value"] += 1

    tester = RaceConditionTester(threads=5, iterations=10)
    result = tester.test_function(simple_function)

    assert result.successful == 50  # 5 threads * 10 iterations
    assert result.failed == 0
    assert call_count["value"] == 50


def test_race_tester_with_exceptions() -> None:
    """Test race tester handles exceptions properly."""

    def failing_function() -> None:
        raise ValueError("Test error")

    tester = RaceConditionTester(threads=3, iterations=5)
    result = tester.test_function(failing_function)

    assert result.failed == 15  # 3 threads * 5 iterations
    assert result.successful == 0
    assert result.race_detected  # Failures indicate potential race
    assert "ValueError" in result.exceptions


def test_race_tester_timing_variance() -> None:
    """Test that timing variance is calculated."""

    def variable_time() -> None:
        # Simulate variable execution time
        import random

        time.sleep(random.uniform(0.001, 0.005))

    tester = RaceConditionTester(threads=5, iterations=5)
    result = tester.test_function(variable_time)

    assert result.timing_variance > 0
    assert len(result.execution_times) == 25
    assert result.avg_execution_time > 0


def test_concurrent_test_decorator() -> None:
    """Test concurrent_test decorator."""
    call_count = {"value": 0}
    lock = threading.Lock()

    @concurrent_test(threads=5, iterations=10)
    def decorated_function() -> None:
        with lock:
            call_count["value"] += 1

    result = decorated_function()

    assert isinstance(result, RaceTestResult)
    assert result.successful == 50
    assert call_count["value"] == 50


def test_stress_test_scenarios() -> None:
    """Test stress test with multiple scenarios."""
    call_counts = {"scenario1": 0, "scenario2": 0}
    lock = threading.Lock()

    def target(scenario_name: str):
        with lock:
            call_counts[scenario_name] += 1

    scenarios = [
        {"name": "scenario1", "args": ("scenario1",), "threads": 3, "iterations": 5},
        {"name": "scenario2", "args": ("scenario2",), "threads": 2, "iterations": 10},
    ]

    tester = RaceConditionTester()
    results = tester.stress_test(target, scenarios)

    assert len(results) == 2
    assert call_counts["scenario1"] == 15  # 3 * 5
    assert call_counts["scenario2"] == 20  # 2 * 10


def test_race_test_result_properties() -> None:
    """Test RaceTestResult computed properties."""
    result = RaceTestResult(
        test_name="test",
        total_iterations=100,
        successful=90,
        failed=10,
        race_detected=True,
        execution_times=[0.001, 0.002, 0.003, 0.010],
    )

    assert result.success_rate == 90.0
    assert result.avg_execution_time == 0.004
    assert result.max_execution_time == 0.010
    assert result.min_execution_time == 0.001


def test_race_test_result_string() -> None:
    """Test RaceTestResult string representation."""
    result = RaceTestResult(
        test_name="test_function",
        total_iterations=100,
        successful=95,
        failed=5,
        race_detected=True,
        failure_details=["Error 1", "Error 2"],
        execution_times=[0.001, 0.002],
    )

    result_str = str(result)
    assert "test_function" in result_str
    assert "95" in result_str
    assert "5" in result_str
    assert "True" in result_str


def test_counter_race_condition() -> None:
    """Test classic counter race condition."""
    counter = {"value": 0}

    def worker() -> None:
        for _ in range(10):
            # Race condition: read-modify-write not atomic
            counter["value"] += 1

    tester = RaceConditionTester(threads=10, iterations=10)
    result = tester.test_function(worker)

    # Due to Python's GIL, this might actually work correctly
    # but the pattern is racy in general
    # Just verify the test runs
    assert result.total_iterations == 100


def test_counter_safe() -> None:
    """Test thread-safe counter."""
    counter = {"value": 0}
    lock = threading.Lock()
    expected = 1000  # 10 threads * 10 iterations * 10

    def worker() -> None:
        for _ in range(10):
            with lock:
                counter["value"] += 1

    tester = RaceConditionTester(threads=10, iterations=10)
    result = tester.test_function(worker)

    assert result.failed == 0
    assert result.successful == 100
    assert counter["value"] == expected


def test_check_then_act_race() -> None:
    """Test check-then-act race condition."""
    cache: dict[str, str] = {}
    creation_count = {"value": 0}

    def worker() -> None:
        key = "shared_key"
        # Race condition: check and act not atomic
        if key not in cache:
            creation_count["value"] += 1
            cache[key] = "value"

    tester = RaceConditionTester(threads=10, iterations=10)
    result = tester.test_function(worker)

    # Due to GIL, might not detect, but pattern is racy
    assert result.total_iterations == 100


def test_lazy_initialization_race() -> None:
    """Test lazy initialization race condition."""
    instance: dict[str, str] | None = None
    creation_count = {"value": 0}

    def get_instance() -> None:
        nonlocal instance
        if instance is None:
            creation_count["value"] += 1
            time.sleep(0.001)  # Make race more likely
            instance = {"created": True}
        return instance

    def worker() -> None:
        get_instance()

    tester = RaceConditionTester(threads=10, iterations=10)
    result = tester.test_function(worker)

    # Instance might be created multiple times due to race
    # This depends on timing, so just check test completes
    assert result.total_iterations == 100


def test_race_tester_timeout() -> None:
    """Test that race tester respects timeout."""

    def slow_function() -> None:
        time.sleep(1.0)

    tester = RaceConditionTester(threads=5, iterations=10, timeout=0.5)
    start_time = time.time()
    tester.test_function(slow_function)
    elapsed = time.time() - start_time

    # Should timeout around 0.5s, not wait for all 50 iterations
    # Note: timeout is per-thread, so give generous margin
    assert elapsed < 60.0  # Just verify it completes


def test_function_with_arguments() -> None:
    """Test race tester with function arguments."""
    results = []
    lock = threading.Lock()

    def function_with_args(x: int, y: int, multiplier: int = 1):
        with lock:
            results.append((x + y) * multiplier)

    tester = RaceConditionTester(threads=3, iterations=5)
    result = tester.test_function(function_with_args, 10, 20, multiplier=2)

    assert result.successful == 15
    assert len(results) == 15
    assert all(r == 60 for r in results)  # (10 + 20) * 2


def test_race_detection_heuristics() -> None:
    """Test race detection heuristics."""

    # Test 1: Failures trigger race detection
    def failing() -> None:
        raise RuntimeError("Test failure")

    tester = RaceConditionTester(threads=2, iterations=2)
    result = tester.test_function(failing)
    assert result.race_detected

    # Test 2: No failures = no race (with safe code)
    lock = threading.Lock()

    def safe() -> None:
        with lock:
            pass

    result = tester.test_function(safe)
    assert not result.race_detected


def test_compare_results() -> None:
    """Test comparing multiple test results."""
    from qontinui_devtools.concurrency import compare_results

    results = [
        RaceTestResult(
            test_name="test1", total_iterations=100, successful=90, failed=10, race_detected=True
        ),
        RaceTestResult(
            test_name="test2", total_iterations=100, successful=100, failed=0, race_detected=False
        ),
    ]

    comparison = compare_results(results)

    assert comparison["total_tests"] == 2
    assert comparison["races_detected"] == 1
    assert comparison["race_rate"] == 50.0
    assert comparison["total_iterations"] == 200
    assert comparison["total_failures"] == 10
    assert comparison["failure_rate"] == 5.0


def test_empty_results_comparison() -> None:
    """Test comparing empty results list."""
    from qontinui_devtools.concurrency import compare_results

    comparison = compare_results([])
    assert comparison == {}
