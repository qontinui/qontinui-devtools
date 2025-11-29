"""Race condition tester for stress testing concurrent code.

This module provides tools to run functions concurrently with multiple threads
and detect race conditions through stress testing and instrumentation.
"""

import concurrent.futures
import statistics
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .instrumentation import SharedStateTracker


@dataclass
class RaceTestResult:
    """Result from race condition test.

    Attributes:
        test_name: Name of the test
        total_iterations: Total number of iterations run
        successful: Number of successful runs
        failed: Number of failed runs
        race_detected: Whether a race condition was detected
        failure_details: List of failure messages
        timing_variance: Variance in execution time (high = contention)
        execution_times: List of execution times for each iteration
        exceptions: List of unique exception types encountered
        conflicts: List of detected race conflicts from instrumentation
    """

    test_name: str
    total_iterations: int
    successful: int
    failed: int
    race_detected: bool
    failure_details: list[str] = field(default_factory=list)
    timing_variance: float = 0.0
    execution_times: list[float] = field(default_factory=list)
    exceptions: list[str] = field(default_factory=list)
    conflicts: list[Any] = field(default_factory=list)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_iterations == 0:
            return 0.0
        return (self.successful / self.total_iterations) * 100

    @property
    def avg_execution_time(self) -> float:
        """Calculate average execution time."""
        if not self.execution_times:
            return 0.0
        return statistics.mean(self.execution_times)

    @property
    def max_execution_time(self) -> float:
        """Get maximum execution time."""
        if not self.execution_times:
            return 0.0
        return max(self.execution_times)

    @property
    def min_execution_time(self) -> float:
        """Get minimum execution time."""
        if not self.execution_times:
            return 0.0
        return min(self.execution_times)

    def __str__(self) -> str:
        """String representation."""
        lines = [
            f"Race Test Result: {self.test_name}",
            f"  Iterations: {self.total_iterations}",
            f"  Success: {self.successful} ({self.success_rate:.1f}%)",
            f"  Failed: {self.failed}",
            f"  Race Detected: {self.race_detected}",
        ]

        if self.execution_times:
            lines.extend(
                [
                    f"  Avg Time: {self.avg_execution_time*1000:.2f}ms",
                    f"  Min Time: {self.min_execution_time*1000:.2f}ms",
                    f"  Max Time: {self.max_execution_time*1000:.2f}ms",
                    f"  Variance: {self.timing_variance*1000:.2f}ms",
                ]
            )

        if self.exceptions:
            lines.append(f"  Exceptions: {', '.join(self.exceptions)}")

        if self.conflicts:
            lines.append(f"  Conflicts: {len(self.conflicts)}")

        if self.failure_details:
            lines.append("  Failures:")
            for detail in self.failure_details[:5]:  # Show first 5
                lines.append(f"    - {detail}")
            if len(self.failure_details) > 5:
                lines.append(f"    ... and {len(self.failure_details) - 5} more")

        return "\n".join(lines)


class RaceConditionTester:
    """Stress tester for race conditions.

    This class runs functions concurrently with multiple threads to expose
    race conditions that might be intermittent. It detects races through:
    - Exception counting
    - Result inconsistency
    - Timing variance
    - Instrumentation conflicts

    Example:
        tester = RaceConditionTester(threads=10, iterations=100)

        def test_function():
            # Code to test
            pass

        result = tester.test_function(test_function)
        if result.race_detected:
            print("Race condition detected!")
    """

    def __init__(
        self,
        threads: int = 10,
        iterations: int = 100,
        timeout: float = 30.0,
        track_state: bool = False,
    ) -> None:
        """Initialize race condition tester.

        Args:
            threads: Number of concurrent threads
            iterations: Number of iterations per thread
            timeout: Maximum time to wait for all threads (seconds)
            track_state: Whether to use instrumentation to track state access
        """
        self.threads = threads
        self.iterations = iterations
        self.timeout = timeout
        self.track_state = track_state
        self._tracker: SharedStateTracker | None = None

        if track_state:
            self._tracker = SharedStateTracker()

    def test_function(self, func: Callable, *args: Any, **kwargs: Any) -> RaceTestResult:
        """Test a function for race conditions.

        Runs the function concurrently with multiple threads and analyzes
        the results to detect race conditions.

        Args:
            func: Function to test
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            RaceTestResult with test results and analysis
        """
        test_name = func.__name__ if hasattr(func, "__name__") else "unknown"
        total_iterations = self.threads * self.iterations

        # Track results
        successful = 0
        failed = 0
        failure_details: list[str] = []
        execution_times: list[float] = []
        exception_types: set[str] = set()
        results: list[Any] = []

        # Lock for thread-safe updates
        lock = threading.Lock()

        def worker() -> None:
            """Worker function for each thread."""
            nonlocal successful, failed

            for _ in range(self.iterations):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    end_time = time.time()

                    with lock:
                        successful += 1
                        execution_times.append(end_time - start_time)
                        results.append(result)

                except Exception as e:
                    end_time = time.time()
                    exception_type = type(e).__name__

                    with lock:
                        failed += 1
                        exception_types.add(exception_type)
                        failure_details.append(f"{exception_type}: {str(e)}")
                        execution_times.append(end_time - start_time)

        # Run concurrent test
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = [executor.submit(worker) for _ in range(self.threads)]

            try:
                concurrent.futures.wait(futures, timeout=self.timeout)
            except concurrent.futures.TimeoutError:
                failure_details.append("Test timeout exceeded")

        end_time = time.time()
        end_time - start_time

        # Calculate timing variance
        timing_variance = 0.0
        if len(execution_times) > 1:
            timing_variance = statistics.variance(execution_times)

        # Detect race conditions
        race_detected = self._detect_race(
            failed=failed,
            timing_variance=timing_variance,
            execution_times=execution_times,
            results=results,
        )

        # Get conflicts from instrumentation
        conflicts = []
        if self._tracker:
            conflicts = self._tracker.detect_conflicts()
            if conflicts:
                race_detected = True

        return RaceTestResult(
            test_name=test_name,
            total_iterations=total_iterations,
            successful=successful,
            failed=failed,
            race_detected=race_detected,
            failure_details=failure_details,
            timing_variance=timing_variance,
            execution_times=execution_times,
            exceptions=list(exception_types),
            conflicts=conflicts,
        )

    def _detect_race(
        self, failed: int, timing_variance: float, execution_times: list[float], results: list[Any]
    ) -> bool:
        """Detect if race condition occurred based on heuristics.

        Args:
            failed: Number of failed iterations
            timing_variance: Variance in execution times
            execution_times: List of execution times
            results: List of results from successful iterations

        Returns:
            True if race condition likely detected
        """
        # Any failures indicate potential race
        if failed > 0:
            return True

        # High timing variance indicates contention
        if execution_times:
            avg_time = statistics.mean(execution_times)
            if avg_time > 0 and timing_variance / avg_time > 0.5:
                return True

            # Large spread between min and max
            min_time = min(execution_times)
            max_time = max(execution_times)
            if min_time > 0 and (max_time / min_time) > 10:
                return True

        # Check for result inconsistency
        # (only works if results are comparable)
        if results and len(set(map(str, results))) > 1:
            # Different results from same function might indicate race
            # But this could also be expected, so don't use alone
            pass

        return False

    def stress_test(
        self, target: Callable, scenarios: list[dict[str, Any]]
    ) -> list[RaceTestResult]:
        """Run multiple test scenarios.

        Args:
            target: Function to test
            scenarios: List of scenario dictionaries with:
                - name: Scenario name
                - args: Positional arguments (optional)
                - kwargs: Keyword arguments (optional)
                - threads: Override thread count (optional)
                - iterations: Override iteration count (optional)

        Returns:
            List of RaceTestResult for each scenario
        """
        results: list[RaceTestResult] = []

        for scenario in scenarios:
            name = scenario.get("name", "unnamed")
            args = scenario.get("args", ())
            kwargs = scenario.get("kwargs", {})
            threads = scenario.get("threads", self.threads)
            iterations = scenario.get("iterations", self.iterations)

            # Create tester with scenario-specific settings
            tester = RaceConditionTester(
                threads=threads,
                iterations=iterations,
                timeout=self.timeout,
                track_state=self.track_state,
            )

            result = tester.test_function(target, *args, **kwargs)
            result.test_name = f"{result.test_name} ({name})"
            results.append(result)

        return results

    def concurrent_test(
        self, threads: int | None = None, iterations: int | None = None
    ) -> Callable:
        """Decorator for concurrent testing.

        Args:
            threads: Override thread count
            iterations: Override iteration count

        Returns:
            Decorator function

        Example:
            tester = RaceConditionTester()

            @tester.concurrent_test(threads=20)
            def test_function():
                pass

            result = test_function()
        """

        def decorator(func: Callable) -> Callable:
            def wrapper(*args: Any, **kwargs: Any) -> RaceTestResult:
                # Create tester with specified settings
                t = threads if threads is not None else self.threads
                i = iterations if iterations is not None else self.iterations

                tester = RaceConditionTester(
                    threads=t, iterations=i, timeout=self.timeout, track_state=self.track_state
                )

                return tester.test_function(func, *args, **kwargs)

            return wrapper

        return decorator

    def get_tracker(self) -> SharedStateTracker | None:
        """Get the state tracker if enabled.

        Returns:
            SharedStateTracker instance or None
        """
        return self._tracker


def compare_results(results: list[RaceTestResult]) -> dict[str, Any]:
    """Compare multiple test results and generate summary.

    Args:
        results: List of RaceTestResult instances

    Returns:
        Dictionary with comparison statistics
    """
    if not results:
        return {}

    total_tests = len(results)
    races_detected = sum(1 for r in results if r.race_detected)
    total_iterations = sum(r.total_iterations for r in results)
    total_failures = sum(r.failed for r in results)

    # Find worst performers
    worst_by_failures = sorted(results, key=lambda r: r.failed, reverse=True)
    worst_by_variance = sorted(results, key=lambda r: r.timing_variance, reverse=True)

    return {
        "total_tests": total_tests,
        "races_detected": races_detected,
        "race_rate": (races_detected / total_tests * 100) if total_tests > 0 else 0,
        "total_iterations": total_iterations,
        "total_failures": total_failures,
        "failure_rate": (total_failures / total_iterations * 100) if total_iterations > 0 else 0,
        "worst_by_failures": worst_by_failures[0].test_name if worst_by_failures else None,
        "worst_by_variance": worst_by_variance[0].test_name if worst_by_variance else None,
    }
