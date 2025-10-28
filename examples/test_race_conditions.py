"""Example usage of race condition tester.

This script demonstrates various ways to use the RaceConditionTester
to detect race conditions in concurrent code.
"""

import threading
import time
from typing import Any

from qontinui_devtools.concurrency import (
    RaceConditionTester,
    concurrent_test,
    stress_test,
)


def example_1_basic_usage():
    """Example 1: Basic usage of RaceConditionTester."""
    print("=" * 80)
    print("Example 1: Basic Usage")
    print("=" * 80)

    # Create a tester
    tester = RaceConditionTester(threads=10, iterations=100)

    # Test a simple function
    shared_dict: dict[str, int] = {}

    def test_function():
        """Function to test - has a race condition."""
        key = "counter"
        if key not in shared_dict:
            shared_dict[key] = 0
        shared_dict[key] += 1

    # Run the test
    result = tester.test_function(test_function)

    # Check results
    print(f"\nResults:")
    print(f"  Total iterations: {result.total_iterations}")
    print(f"  Successful: {result.successful}")
    print(f"  Failed: {result.failed}")
    print(f"  Race detected: {result.race_detected}")

    if result.race_detected:
        print("\n  Failure details:")
        for detail in result.failure_details[:3]:  # Show first 3
            print(f"    - {detail}")

    # Check if final count is correct
    expected = result.successful
    actual = shared_dict.get("counter", 0)
    print(f"\n  Expected counter: {expected}")
    print(f"  Actual counter: {actual}")
    if actual != expected:
        print("  WARNING: Counter mismatch indicates lost updates!")


def example_2_decorator_usage():
    """Example 2: Using the @concurrent_test decorator."""
    print("\n" + "=" * 80)
    print("Example 2: Decorator Usage")
    print("=" * 80)

    call_count = {"value": 0}
    lock = threading.Lock()

    @concurrent_test(threads=20, iterations=50)
    def test_with_lock():
        """Thread-safe function using lock."""
        with lock:
            call_count["value"] += 1
            time.sleep(0.0001)  # Simulate some work

    # Run test (automatically tested concurrently)
    result = test_with_lock()

    print(f"\nResults:")
    print(f"  Total iterations: {result.total_iterations}")
    print(f"  Successful: {result.successful}")
    print(f"  Failed: {result.failed}")
    print(f"  Race detected: {result.race_detected}")
    print(f"  Final count: {call_count['value']}")

    if not result.race_detected:
        print("\n  SUCCESS: Thread-safe code passed!")


def example_3_stress_test():
    """Example 3: Heavy stress testing."""
    print("\n" + "=" * 80)
    print("Example 3: Stress Test")
    print("=" * 80)

    cache: dict[str, Any] = {}
    lock = threading.Lock()

    @stress_test(threads=50, iterations=1000)
    def test_cache_operations():
        """Test cache with high concurrency."""
        key = f"key_{threading.get_ident()}"

        with lock:
            # Thread-safe cache operations
            if key not in cache:
                cache[key] = []
            cache[key].append(time.time())

    print("\nRunning stress test with 50 threads x 1000 iterations...")
    print("(This may take a moment...)")

    start_time = time.time()
    result = test_cache_operations()
    elapsed = time.time() - start_time

    print(f"\nResults:")
    print(f"  Total iterations: {result.total_iterations}")
    print(f"  Successful: {result.successful}")
    print(f"  Failed: {result.failed}")
    print(f"  Elapsed time: {elapsed:.2f}s")
    print(f"  Operations/sec: {result.total_iterations/elapsed:.0f}")
    print(f"  Race detected: {result.race_detected}")

    if result.execution_times:
        print(f"\n  Timing statistics:")
        print(f"    Avg: {result.avg_execution_time*1000:.2f}ms")
        print(f"    Min: {result.min_execution_time*1000:.2f}ms")
        print(f"    Max: {result.max_execution_time*1000:.2f}ms")


def example_4_compare_safe_vs_unsafe():
    """Example 4: Compare safe vs unsafe implementations."""
    print("\n" + "=" * 80)
    print("Example 4: Safe vs Unsafe Comparison")
    print("=" * 80)

    # Unsafe version
    counter_unsafe = {"value": 0}

    def unsafe_increment():
        """Unsafe counter increment."""
        for _ in range(100):
            counter_unsafe["value"] += 1

    # Safe version
    counter_safe = {"value": 0}
    lock = threading.Lock()

    def safe_increment():
        """Safe counter increment with lock."""
        for _ in range(100):
            with lock:
                counter_safe["value"] += 1

    # Test both
    tester = RaceConditionTester(threads=10, iterations=10)

    print("\nTesting UNSAFE version...")
    result_unsafe = tester.test_function(unsafe_increment)

    print("\nTesting SAFE version...")
    result_safe = tester.test_function(safe_increment)

    # Compare results
    print("\n" + "-" * 80)
    print("Comparison:")
    print("-" * 80)

    print("\nUnsafe version:")
    print(f"  Race detected: {result_unsafe.race_detected}")
    print(f"  Failed: {result_unsafe.failed}")
    print(f"  Expected counter: {10 * 10 * 100}")
    print(f"  Actual counter: {counter_unsafe['value']}")
    print(f"  Lost updates: {10 * 10 * 100 - counter_unsafe['value']}")

    print("\nSafe version:")
    print(f"  Race detected: {result_safe.race_detected}")
    print(f"  Failed: {result_safe.failed}")
    print(f"  Expected counter: {10 * 10 * 100}")
    print(f"  Actual counter: {counter_safe['value']}")
    print(f"  Lost updates: {10 * 10 * 100 - counter_safe['value']}")


def example_5_multiple_scenarios():
    """Example 5: Testing multiple scenarios."""
    print("\n" + "=" * 80)
    print("Example 5: Multiple Scenarios")
    print("=" * 80)

    results_dict: dict[str, int] = {}
    lock = threading.Lock()

    def target_function(scenario: str, count: int):
        """Target function for scenarios."""
        with lock:
            if scenario not in results_dict:
                results_dict[scenario] = 0
            results_dict[scenario] += count

    scenarios = [
        {
            "name": "Light load",
            "args": ("light", 1),
            "threads": 5,
            "iterations": 10
        },
        {
            "name": "Medium load",
            "args": ("medium", 10),
            "threads": 10,
            "iterations": 50
        },
        {
            "name": "Heavy load",
            "args": ("heavy", 100),
            "threads": 20,
            "iterations": 100
        }
    ]

    tester = RaceConditionTester()
    results = tester.stress_test(target_function, scenarios)

    print("\nScenario results:")
    for result in results:
        print(f"\n  {result.test_name}:")
        print(f"    Iterations: {result.total_iterations}")
        print(f"    Success rate: {result.success_rate:.1f}%")
        print(f"    Race detected: {result.race_detected}")

    print("\n  Final counts:")
    for key, value in sorted(results_dict.items()):
        print(f"    {key}: {value}")


def example_6_with_exceptions():
    """Example 6: Testing code that raises exceptions."""
    print("\n" + "=" * 80)
    print("Example 6: Exception Handling")
    print("=" * 80)

    shared_list: list[int] = []

    def buggy_function():
        """Function with a bug that sometimes raises."""
        # Intentional race condition
        index = len(shared_list)
        shared_list.append(index)

        # This will sometimes fail due to race
        if shared_list[index] != index:
            raise ValueError(f"Expected {index}, got {shared_list[index]}")

    tester = RaceConditionTester(threads=10, iterations=10)
    result = tester.test_function(buggy_function)

    print(f"\nResults:")
    print(f"  Total iterations: {result.total_iterations}")
    print(f"  Successful: {result.successful}")
    print(f"  Failed: {result.failed}")
    print(f"  Race detected: {result.race_detected}")

    if result.exceptions:
        print(f"\n  Exception types encountered:")
        for exc_type in result.exceptions:
            print(f"    - {exc_type}")

    if result.failure_details:
        print(f"\n  Sample failures:")
        for detail in result.failure_details[:3]:
            print(f"    - {detail}")


def main():
    """Run all examples."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "Race Condition Tester Examples" + " " * 28 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    try:
        example_1_basic_usage()
        example_2_decorator_usage()
        example_3_stress_test()
        example_4_compare_safe_vs_unsafe()
        example_5_multiple_scenarios()
        example_6_with_exceptions()

        print("\n" + "=" * 80)
        print("All examples completed!")
        print("=" * 80)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
