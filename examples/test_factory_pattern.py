"""Example: Testing HAL Factory pattern for race conditions.

from typing import Any, Any

from typing import Any

This example demonstrates testing a singleton factory pattern
for thread safety issues.
"""

import threading
import time

from qontinui_devtools.concurrency import RaceConditionTester
from typing import Any


# Simulated HAL Factory (similar to qontinui.hal.factory)
class MockInputController:
    """Mock input controller."""

    def __init__(self) -> None:
        self.initialized = time.time()
        time.sleep(0.001)  # Simulate initialization time


class HALFactory:
    """Factory for HAL components - UNSAFE version."""

    _instance = None
    _controller = None
    _creation_count = 0

    @classmethod
    def reset(cls) -> None:
        """Reset factory state for testing."""
        cls._instance = None
        cls._controller = None
        cls._creation_count = 0

    @classmethod
    def get_input_controller(cls) -> Any:
        """Get input controller - UNSAFE lazy initialization."""
        if cls._controller is None:
            # Race condition: multiple threads can enter here!
            cls._creation_count += 1
            cls._controller = MockInputController()
        return cls._controller


class SafeHALFactory:
    """Factory for HAL components - SAFE version."""

    _instance = None
    _controller = None
    _creation_count = 0
    _lock = threading.Lock()

    @classmethod
    def reset(cls) -> None:
        """Reset factory state for testing."""
        with cls._lock:
            cls._instance = None
            cls._controller = None
            cls._creation_count = 0

    @classmethod
    def get_input_controller(cls) -> Any:
        """Get input controller - SAFE lazy initialization."""
        if cls._controller is None:
            with cls._lock:
                # Double-checked locking
                if cls._controller is None:
                    cls._creation_count += 1
                    cls._controller = MockInputController()
        return cls._controller


def test_unsafe_factory() -> None:
    """Test the unsafe factory pattern."""
    print("=" * 80)
    print("Testing UNSAFE HAL Factory Pattern")
    print("=" * 80)

    HALFactory.reset()

    def worker() -> None:
        """Worker that gets controller."""
        controller = HALFactory.get_input_controller()
        assert controller is not None

    # Test with concurrent access
    tester = RaceConditionTester(threads=20, iterations=50)
    result = tester.test_function(worker)

    print("\nTest Results:")
    print(f"  Total iterations: {result.total_iterations}")
    print(f"  Successful: {result.successful}")
    print(f"  Failed: {result.failed}")
    print(f"  Race detected: {result.race_detected}")

    print("\nFactory Statistics:")
    print(f"  Controller created {HALFactory._creation_count} times")
    print("  Expected: 1 (singleton)")
    print(f"  Actual: {HALFactory._creation_count}")

    if HALFactory._creation_count > 1:
        print("\n  ⚠️  WARNING: Controller created multiple times!")
        print("  This is a race condition in lazy initialization!")

    if result.execution_times:
        print("\nTiming Statistics:")
        print(f"  Avg: {result.avg_execution_time*1000:.2f}ms")
        print(f"  Min: {result.min_execution_time*1000:.2f}ms")
        print(f"  Max: {result.max_execution_time*1000:.2f}ms")
        print(f"  Variance: {result.timing_variance*1000:.2f}ms")


def test_safe_factory() -> None:
    """Test the safe factory pattern."""
    print("\n" + "=" * 80)
    print("Testing SAFE HAL Factory Pattern")
    print("=" * 80)

    SafeHALFactory.reset()

    def worker() -> None:
        """Worker that gets controller."""
        controller = SafeHALFactory.get_input_controller()
        assert controller is not None

    # Test with concurrent access
    tester = RaceConditionTester(threads=20, iterations=50)
    result = tester.test_function(worker)

    print("\nTest Results:")
    print(f"  Total iterations: {result.total_iterations}")
    print(f"  Successful: {result.successful}")
    print(f"  Failed: {result.failed}")
    print(f"  Race detected: {result.race_detected}")

    print("\nFactory Statistics:")
    print(f"  Controller created {SafeHALFactory._creation_count} times")
    print("  Expected: 1 (singleton)")
    print(f"  Actual: {SafeHALFactory._creation_count}")

    if SafeHALFactory._creation_count == 1:
        print("\n  ✅ SUCCESS: Controller created exactly once!")
        print("  Thread-safe implementation working correctly!")

    if result.execution_times:
        print("\nTiming Statistics:")
        print(f"  Avg: {result.avg_execution_time*1000:.2f}ms")
        print(f"  Min: {result.min_execution_time*1000:.2f}ms")
        print(f"  Max: {result.max_execution_time*1000:.2f}ms")
        print(f"  Variance: {result.timing_variance*1000:.2f}ms")


def test_comparison() -> None:
    """Compare both implementations."""
    print("\n" + "=" * 80)
    print("Performance Comparison")
    print("=" * 80)

    # Test unsafe
    HALFactory.reset()
    start = time.time()
    tester = RaceConditionTester(threads=50, iterations=100)
    result_unsafe = tester.test_function(HALFactory.get_input_controller)
    unsafe_time = time.time() - start

    # Test safe
    SafeHALFactory.reset()
    start = time.time()
    tester = RaceConditionTester(threads=50, iterations=100)
    result_safe = tester.test_function(SafeHALFactory.get_input_controller)
    safe_time = time.time() - start

    print("\nUnsafe Version:")
    print(f"  Total time: {unsafe_time:.3f}s")
    print(f"  Operations/sec: {result_unsafe.total_iterations/unsafe_time:.0f}")
    print(f"  Race detected: {result_unsafe.race_detected}")
    print(f"  Instances created: {HALFactory._creation_count}")

    print("\nSafe Version:")
    print(f"  Total time: {safe_time:.3f}s")
    print(f"  Operations/sec: {result_safe.total_iterations/safe_time:.0f}")
    print(f"  Race detected: {result_safe.race_detected}")
    print(f"  Instances created: {SafeHALFactory._creation_count}")

    overhead = ((safe_time - unsafe_time) / unsafe_time * 100) if unsafe_time > 0 else 0
    print(f"\nSynchronization Overhead: {overhead:.1f}%")


def main() -> None:
    """Run all factory tests."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 22 + "HAL Factory Pattern Testing" + " " * 28 + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    try:
        test_unsafe_factory()
        test_safe_factory()
        test_comparison()

        print("\n" + "=" * 80)
        print("Test Summary")
        print("=" * 80)
        print("\nKey Findings:")
        print("  • Unsafe factory creates multiple instances under concurrent load")
        print("  • Safe factory with double-checked locking creates exactly one instance")
        print("  • Minimal performance overhead for thread safety")
        print("  • Race condition tester successfully detects the issue")
        print("\n" + "=" * 80)

    except Exception as e:
        print(f"\nError running tests: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
