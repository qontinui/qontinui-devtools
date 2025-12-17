"""Shared fixtures for integration tests."""

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def temp_test_dir(tmp_path: Path) -> Path:
    """Create a temporary test directory."""
    return tmp_path


@pytest.fixture
def sample_qontinui_action(temp_test_dir: Path) -> Path:
    """Create a sample qontinui action for testing.

    This simulates a real qontinui action with HAL interactions.
    """
    action_file = temp_test_dir / "sample_action.py"
    action_file.write_text(
        """
import time
from typing import Optional


class SampleAction:
    '''Sample action for testing runtime monitoring.'''

    def __init__(self) -> None:
        self.hal = None
        self.state = {}
        self.counter = 0

    def execute(self, iterations: int = 10) -> Dict[str, Any]:
        '''Execute the action.'''
        results = []

        for i in range(iterations):
            # Simulate HAL operations
            result = self._process_iteration(i)
            results.append(result)
            time.sleep(0.01)  # Simulate work

        return {
            'iterations': iterations,
            'results': results,
            'counter': self.counter
        }

    def _process_iteration(self, iteration: int) -> Dict[str, Any]:
        '''Process a single iteration.'''
        self.counter += 1

        # Simulate different types of operations
        if iteration % 3 == 0:
            return self._screen_capture()
        elif iteration % 3 == 1:
            return self._pattern_match()
        else:
            return self._input_action()

    def _screen_capture(self) -> Dict[str, Any]:
        '''Simulate screen capture.'''
        time.sleep(0.005)
        return {'type': 'screen_capture', 'size': (1920, 1080)}

    def _pattern_match(self) -> Dict[str, Any]:
        '''Simulate pattern matching.'''
        time.sleep(0.008)
        return {'type': 'pattern_match', 'confidence': 0.95}

    def _input_action(self) -> Dict[str, Any]:
        '''Simulate input action.'''
        time.sleep(0.003)
        return {'type': 'input', 'action': 'click'}

    def execute_with_error(self) -> None:
        '''Execute action that will raise an error.'''
        self._process_iteration(0)
        raise RuntimeError("Simulated action error")

    async def execute_async(self, iterations: int = 5) -> Dict[str, Any]:
        '''Execute action asynchronously.'''
        results = []

        for i in range(iterations):
            result = await self._process_iteration_async(i)
            results.append(result)
            await asyncio.sleep(0.01)

        return {
            'iterations': iterations,
            'results': results
        }

    async def _process_iteration_async(self, iteration: int) -> Dict[str, Any]:
        '''Process iteration asynchronously.'''
        await asyncio.sleep(0.005)
        return {'type': 'async_operation', 'iteration': iteration}


class MemoryIntensiveAction:
    '''Action that allocates memory for testing memory profiler.'''

    def __init__(self) -> None:
        self.data = []

    def execute(self, size_mb: int = 10) -> int:
        '''Allocate memory.'''
        # Allocate roughly size_mb of memory
        elements = (size_mb * 1024 * 1024) // 8  # 8 bytes per element
        self.data = [i for i in range(elements)]
        return len(self.data)

    def cleanup(self) -> None:
        '''Clean up allocated memory.'''
        self.data.clear()


class ConcurrentAction:
    '''Action for testing concurrent execution.'''

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.shared_counter = 0
        self.thread_results = []

    def execute_threaded(self, thread_id: int, iterations: int = 10) -> Dict[str, Any]:
        '''Execute action in a thread.'''
        results = []

        for i in range(iterations):
            with self.lock:
                self.shared_counter += 1
                local_count = self.shared_counter

            time.sleep(0.001)
            results.append({'thread': thread_id, 'iteration': i, 'count': local_count})

        return {
            'thread_id': thread_id,
            'iterations': iterations,
            'results': results
        }
"""
    )
    return action_file


@pytest.fixture
def sample_qontinui_project(temp_test_dir: Path) -> Path:
    """Create a sample qontinui project structure for testing.

    This creates a realistic project structure with multiple modules.
    """
    project_dir = temp_test_dir / "sample_project"
    project_dir.mkdir()

    # Create main module
    main_file = project_dir / "main.py"
    main_file.write_text(
        """
from actions import action_a, action_b
from utils import helper


def main() -> Any:
    '''Main entry point.'''
    helper.setup()
    result_a = action_a.execute()
    result_b = action_b.execute()
    return result_a, result_b


if __name__ == '__main__':
    main()
"""
    )

    # Create actions module
    actions_dir = project_dir / "actions"
    actions_dir.mkdir()
    (actions_dir / "__init__.py").write_text("")

    (actions_dir / "action_a.py").write_text(
        """
import time


def execute() -> Any:
    '''Execute action A.'''
    time.sleep(0.01)
    return {'status': 'success', 'action': 'A'}
"""
    )

    (actions_dir / "action_b.py").write_text(
        """
import time


def execute() -> Any:
    '''Execute action B.'''
    time.sleep(0.02)
    return {'status': 'success', 'action': 'B'}
"""
    )

    # Create utils module
    utils_dir = project_dir / "utils"
    utils_dir.mkdir()
    (utils_dir / "__init__.py").write_text("")

    (utils_dir / "helper.py").write_text(
        """
def setup() -> Any:
    '''Setup helper.'''
    print("Setup complete")
"""
    )

    return project_dir


@pytest.fixture
def profiler_config() -> dict[str, Any]:
    """Default configuration for profiler."""
    return {
        "enabled": True,
        "sampling_interval": 0.001,
        "include_stdlib": False,
        "max_stack_depth": 10,
        "output_format": "json",
    }


@pytest.fixture
def event_tracer_config() -> dict[str, Any]:
    """Default configuration for event tracer."""
    return {
        "enabled": True,
        "trace_hal_calls": True,
        "trace_actions": True,
        "trace_state_changes": True,
        "buffer_size": 1000,
        "output_format": "json",
    }


@pytest.fixture
def memory_profiler_config() -> dict[str, Any]:
    """Default configuration for memory profiler."""
    return {
        "enabled": True,
        "sampling_interval": 0.01,
        "track_allocations": True,
        "track_deallocations": True,
        "threshold_mb": 100,
        "output_format": "json",
    }


@pytest.fixture
def dashboard_config() -> dict[str, Any]:
    """Default configuration for performance dashboard."""
    return {
        "enabled": True,
        "port": 8050,
        "host": "127.0.0.1",
        "update_interval": 0.1,
        "retention_seconds": 60,
    }


@pytest.fixture
def sample_action_instance(sample_qontinui_action: Path):
    """Create an instance of the sample action."""
    # Import the action dynamically
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location("sample_action", sample_qontinui_action)
    module = importlib.util.module_from_spec(spec)
    sys.modules["sample_action"] = module
    spec.loader.exec_module(module)

    return module.SampleAction()


@pytest.fixture
def memory_intensive_action(sample_qontinui_action: Path):
    """Create an instance of the memory intensive action."""
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location("sample_action", sample_qontinui_action)
    module = importlib.util.module_from_spec(spec)
    sys.modules["sample_action_mem"] = module
    spec.loader.exec_module(module)

    return module.MemoryIntensiveAction()


@pytest.fixture
def concurrent_action(sample_qontinui_action: Path):
    """Create an instance of the concurrent action."""
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location("sample_action", sample_qontinui_action)
    module = importlib.util.module_from_spec(spec)
    sys.modules["sample_action_concurrent"] = module
    spec.loader.exec_module(module)

    return module.ConcurrentAction()


@pytest.fixture
def performance_thresholds() -> dict[str, float]:
    """Performance thresholds for integration tests."""
    return {
        "max_overhead_percent": 5.0,  # Maximum 5% overhead
        "max_memory_mb": 100,  # Maximum 100MB memory usage
        "max_startup_time_ms": 100,  # Maximum 100ms startup time
        "max_event_latency_ms": 1,  # Maximum 1ms event latency
    }


@pytest.fixture
def stress_test_config() -> dict[str, int]:
    """Configuration for stress testing."""
    return {
        "num_threads": 10,
        "iterations_per_thread": 100,
        "num_actions": 50,
        "duration_seconds": 10,
    }


def measure_overhead(func: Callable, *args, **kwargs) -> dict[str, float]:
    """Measure execution overhead of a function.

    Returns:
        Dictionary with timing information including overhead percentage.
    """
    # Measure baseline without instrumentation
    baseline_times = []
    for _ in range(5):
        start = time.perf_counter()
        func(*args, **kwargs)
        baseline_times.append(time.perf_counter() - start)

    baseline_avg = sum(baseline_times) / len(baseline_times)

    return {
        "baseline_ms": baseline_avg * 1000,
        "min_ms": min(baseline_times) * 1000,
        "max_ms": max(baseline_times) * 1000,
    }


@pytest.fixture
def overhead_measurer() -> Any:
    """Fixture that provides overhead measurement utility."""
    return measure_overhead
