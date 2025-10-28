# API Reference

Complete API documentation for Qontinui DevTools Python library.

## Table of Contents

1. [Import Analysis](#import-analysis)
2. [Concurrency Analysis](#concurrency-analysis)
3. [Performance Profiling](#performance-profiling)
4. [Mock HAL](#mock-hal)
5. [Core Types](#core-types)
6. [Utilities](#utilities)

---

## Import Analysis

### CircularDependencyDetector

Detects circular dependencies in Python codebases through static analysis.

```python
from qontinui_devtools.import_analysis import CircularDependencyDetector

detector = CircularDependencyDetector(path: str, exclude_patterns: list[str] = None)
cycles = detector.analyze() -> list[CircularDependency]
```

**Parameters:**
- `path` (str): Path to directory or file to analyze
- `exclude_patterns` (list[str], optional): Glob patterns to exclude from analysis

**Returns:**
- `list[CircularDependency]`: List of detected circular dependencies

**Example:**

```python
detector = CircularDependencyDetector(
    "./src",
    exclude_patterns=["test_*.py", "*_test.py"]
)

cycles = detector.analyze()
for cycle in cycles:
    print(f"Cycle: {' → '.join(cycle.cycle)}")
    print(f"Suggestion: {cycle.suggestion}")
```

**Methods:**

#### `analyze() -> list[CircularDependency]`

Performs the dependency analysis and returns all detected cycles.

**Returns:** List of `CircularDependency` objects

**Raises:**
- `FileNotFoundError`: If the specified path doesn't exist
- `ValueError`: If the path is not a valid Python file or directory

#### `get_dependency_graph() -> nx.DiGraph`

Returns the full dependency graph as a NetworkX directed graph.

**Returns:** `networkx.DiGraph` object representing dependencies

**Example:**

```python
graph = detector.get_dependency_graph()
print(f"Modules: {graph.number_of_nodes()}")
print(f"Dependencies: {graph.number_of_edges()}")
```

#### `visualize(output_path: str, format: str = "png") -> None`

Generates a visual representation of the dependency graph.

**Parameters:**
- `output_path` (str): Path to save the visualization
- `format` (str): Output format ("png", "svg", "pdf")

**Example:**

```python
detector.visualize("deps.svg", format="svg")
```

---

### ImportTracer

Runtime import tracer that hooks into Python's import system to track imports as they happen.

```python
from qontinui_devtools.import_analysis import ImportTracer

with ImportTracer() as tracer:
    import mymodule

events = tracer.get_events()
cycles = tracer.find_circular_dependencies()
```

**Context Manager Usage:**

The tracer must be used as a context manager to ensure proper cleanup:

```python
with ImportTracer() as tracer:
    # All imports here will be traced
    import module1
    from module2 import something
```

**Methods:**

#### `get_events() -> list[ImportEvent]`

Returns all import events that occurred during tracing.

**Returns:** List of `ImportEvent` objects with fields:
- `importer` (str): Module doing the import
- `imported` (str): Module being imported
- `timestamp` (float): When the import occurred
- `depth` (int): Import depth level

**Example:**

```python
events = tracer.get_events()
for event in events:
    print(f"{event.importer} → {event.imported} ({event.depth})")
```

#### `find_circular_dependencies() -> list[list[str]]`

Analyzes traced imports to find circular dependencies.

**Returns:** List of cycles, where each cycle is a list of module names

**Example:**

```python
cycles = tracer.find_circular_dependencies()
for cycle in cycles:
    print(f"Circular: {' → '.join(cycle)}")
```

#### `visualize(output_path: str, include_stdlib: bool = False) -> None`

Creates a visual graph of traced imports.

**Parameters:**
- `output_path` (str): Path to save visualization
- `include_stdlib` (bool): Whether to include standard library modules

**Example:**

```python
tracer.visualize("imports.png", include_stdlib=False)
```

#### `get_import_time(module: str) -> float`

Returns the time taken to import a specific module.

**Parameters:**
- `module` (str): Module name

**Returns:** Import time in seconds

**Raises:**
- `KeyError`: If module was not imported during tracing

---

### DependencyGraph

Represents module dependencies as a directed graph.

```python
from qontinui_devtools.import_analysis import DependencyGraph

graph = DependencyGraph()
graph.add_dependency("module_a", "module_b")
```

**Methods:**

#### `add_dependency(from_module: str, to_module: str) -> None`

Adds a dependency edge to the graph.

**Parameters:**
- `from_module` (str): Module that imports
- `to_module` (str): Module being imported

#### `find_cycles() -> list[list[str]]`

Finds all cycles in the dependency graph.

**Returns:** List of cycles (each cycle is a list of module names)

**Algorithm:** Uses Johnson's algorithm for cycle detection

#### `get_shortest_path(source: str, target: str) -> list[str] | None`

Finds the shortest import path between two modules.

**Parameters:**
- `source` (str): Starting module
- `target` (str): Target module

**Returns:** List of modules in the path, or None if no path exists

#### `get_transitive_dependencies(module: str) -> set[str]`

Gets all modules that a module depends on (directly or indirectly).

**Parameters:**
- `module` (str): Module name

**Returns:** Set of all dependency module names

---

## Concurrency Analysis

### RaceConditionDetector

Static analyzer for detecting potential race conditions in multi-threaded code.

```python
from qontinui_devtools.concurrency import RaceConditionDetector

detector = RaceConditionDetector(path: str)
races = detector.analyze() -> list[RaceCondition]
```

**Parameters:**
- `path` (str): Path to analyze

**Returns:**
- `list[RaceCondition]`: Detected race conditions

**Example:**

```python
detector = RaceConditionDetector("./src")
races = detector.analyze()

for race in races:
    print(f"Severity: {race.severity}")
    print(f"State: {race.shared_state.name}")
    print(f"Location: {race.shared_state.file_path}:{race.shared_state.line_number}")
    print(f"Fix: {race.suggestion}")
```

**Methods:**

#### `analyze() -> list[RaceCondition]`

Performs static analysis to detect race conditions.

**Returns:** List of `RaceCondition` objects

**Detection Strategies:**
1. Shared state without synchronization
2. Lock-free modifications to shared data
3. Inconsistent lock usage
4. Read-modify-write sequences

#### `check_file(file_path: str) -> list[RaceCondition]`

Analyzes a single file for race conditions.

**Parameters:**
- `file_path` (str): Path to Python file

**Returns:** List of race conditions found in the file

#### `get_shared_state() -> list[SharedState]`

Returns all detected shared state variables.

**Returns:** List of `SharedState` objects with fields:
- `name` (str): Variable name
- `file_path` (str): File containing the variable
- `line_number` (int): Line number
- `access_type` (str): "read", "write", or "both"
- `protected` (bool): Whether it's protected by locks

---

### RaceConditionTester

Dynamic testing tool for detecting race conditions at runtime.

```python
from qontinui_devtools.concurrency import RaceConditionTester

tester = RaceConditionTester(
    threads: int = 10,
    iterations: int = 100,
    timeout: float = 30.0
)

result = tester.test_function(func: Callable) -> TestResult
```

**Parameters:**
- `threads` (int): Number of concurrent threads
- `iterations` (int): Iterations per thread
- `timeout` (float): Maximum test duration in seconds

**Example:**

```python
def increment_counter(counter_dict):
    counter_dict['value'] += 1

tester = RaceConditionTester(threads=50, iterations=1000)
result = tester.test_function(
    lambda: increment_counter(shared_dict)
)

if result.race_detected:
    print(f"Race detected! Failed: {result.failed}")
else:
    print("No race detected")
```

**Methods:**

#### `test_function(func: Callable, *args, **kwargs) -> TestResult`

Tests a function for race conditions by executing it concurrently.

**Parameters:**
- `func` (Callable): Function to test
- `*args`: Positional arguments to pass to function
- `**kwargs`: Keyword arguments to pass to function

**Returns:** `TestResult` object with fields:
- `total_iterations` (int): Total test iterations
- `successful` (int): Successful executions
- `failed` (int): Failed executions
- `race_detected` (bool): Whether race was detected
- `failure_details` (list[str]): Details of failures
- `duration` (float): Test duration in seconds

#### `test_class(cls: type, method_name: str) -> TestResult`

Tests a method of a class for race conditions.

**Parameters:**
- `cls` (type): Class to test
- `method_name` (str): Name of method to test

**Returns:** `TestResult` object

**Example:**

```python
class Counter:
    def __init__(self):
        self.value = 0

    def increment(self):
        self.value += 1

result = tester.test_class(Counter, "increment")
```

#### `stress_test(func: Callable, duration: float) -> TestResult`

Runs a sustained stress test for a specified duration.

**Parameters:**
- `func` (Callable): Function to test
- `duration` (float): Test duration in seconds

**Returns:** `TestResult` with additional metrics:
- `operations_per_second` (float): Throughput
- `peak_memory_mb` (float): Peak memory usage

---

### DeadlockDetector

Detects potential deadlock scenarios in multi-threaded code.

```python
from qontinui_devtools.concurrency import DeadlockDetector

detector = DeadlockDetector(path: str)
deadlocks = detector.analyze() -> list[DeadlockScenario]
```

**Methods:**

#### `analyze() -> list[DeadlockScenario]`

Analyzes code for potential deadlock scenarios.

**Returns:** List of `DeadlockScenario` objects

**Detection Techniques:**
1. Lock ordering violations
2. Cyclic lock dependencies
3. Lock acquisition in callbacks
4. Lock waiting while holding locks

#### `visualize_lock_graph(output_path: str) -> None`

Creates a visual representation of lock dependencies.

**Parameters:**
- `output_path` (str): Path to save visualization

---

## Performance Profiling

### CPUProfiler

CPU profiling using py-spy integration.

```python
from qontinui_devtools.profiling import CPUProfiler

profiler = CPUProfiler(sample_rate: int = 100)
```

**Parameters:**
- `sample_rate` (int): Sampling frequency in Hz

**Methods:**

#### `profile_function(func: Callable, *args, **kwargs) -> ProfileResult`

Profiles a function execution.

**Parameters:**
- `func` (Callable): Function to profile
- `*args, **kwargs`: Function arguments

**Returns:** `ProfileResult` with timing data and hotspots

**Example:**

```python
profiler = CPUProfiler(sample_rate=100)
result = profiler.profile_function(my_slow_function, arg1, arg2)

print(f"Total time: {result.total_time:.2f}s")
for hotspot in result.hotspots:
    print(f"  {hotspot.function}: {hotspot.time:.2f}s")
```

#### `profile_script(script_path: str, duration: float = None) -> ProfileResult`

Profiles a Python script.

**Parameters:**
- `script_path` (str): Path to script
- `duration` (float, optional): Profile for specific duration

**Returns:** `ProfileResult`

#### `generate_flamegraph(output_path: str) -> None`

Generates a flame graph visualization.

**Parameters:**
- `output_path` (str): Path to save SVG flame graph

---

### MemoryProfiler

Memory profiling using memray integration.

```python
from qontinui_devtools.profiling import MemoryProfiler

profiler = MemoryProfiler(track_allocations: bool = True)
```

**Parameters:**
- `track_allocations` (bool): Whether to track individual allocations

**Methods:**

#### `profile_function(func: Callable) -> MemoryResult`

Profiles memory usage of a function.

**Returns:** `MemoryResult` with fields:
- `peak_memory_mb` (float): Peak memory usage
- `allocations` (int): Number of allocations
- `leaked_mb` (float): Potential memory leaks

**Example:**

```python
profiler = MemoryProfiler()
result = profiler.profile_function(memory_intensive_function)

print(f"Peak memory: {result.peak_memory_mb:.2f} MB")
print(f"Allocations: {result.allocations}")
if result.leaked_mb > 0:
    print(f"Potential leak: {result.leaked_mb:.2f} MB")
```

#### `track_allocations(func: Callable) -> list[Allocation]`

Tracks individual memory allocations.

**Returns:** List of `Allocation` objects with:
- `size_bytes` (int): Allocation size
- `location` (str): Code location
- `timestamp` (float): When allocated

---

## Mock HAL

### MockHAL

Mock Hardware Abstraction Layer for testing without hardware.

```python
from qontinui_devtools.hal import MockHAL

hal = MockHAL(config: HALConfig = None)
```

**Parameters:**
- `config` (HALConfig, optional): Configuration object

**Example:**

```python
from qontinui_devtools.hal import MockHAL, HALConfig

config = HALConfig(
    screen_size=(1920, 1080),
    simulate_latency=True,
    latency_ms=10
)

hal = MockHAL(config)

# Use like real HAL
hal.click(100, 200)
screenshot = hal.capture_screen()
```

**Methods:**

#### `click(x: int, y: int, button: str = "left") -> None`

Simulates a mouse click.

**Parameters:**
- `x` (int): X coordinate
- `y` (int): Y coordinate
- `button` (str): Mouse button ("left", "right", "middle")

#### `type_text(text: str, delay_ms: float = 50) -> None`

Simulates typing text.

**Parameters:**
- `text` (str): Text to type
- `delay_ms` (float): Delay between keystrokes

#### `capture_screen() -> np.ndarray`

Captures the current screen state.

**Returns:** NumPy array with screen image data (height, width, 3)

#### `wait_for_element(locator: str, timeout: float = 10) -> bool`

Waits for an element to appear.

**Parameters:**
- `locator` (str): Element locator
- `timeout` (float): Maximum wait time

**Returns:** True if element found, False if timeout

---

### HALRecorder

Records HAL interactions for playback.

```python
from qontinui_devtools.hal import HALRecorder

recorder = HALRecorder(output_path: str)
```

**Methods:**

#### `start_recording() -> None`

Starts recording HAL interactions.

#### `stop_recording() -> None`

Stops recording and saves to file.

#### `record_session(duration: float) -> None`

Records for a specific duration.

**Parameters:**
- `duration` (float): Recording duration in seconds

**Example:**

```python
recorder = HALRecorder("session.hal")
recorder.start_recording()

# Perform actions...
hal.click(100, 200)
hal.type_text("Hello")

recorder.stop_recording()
```

---

### HALPlayer

Plays back recorded HAL sessions.

```python
from qontinui_devtools.hal import HALPlayer

player = HALPlayer(session_path: str)
```

**Methods:**

#### `play(speed: float = 1.0, verify: bool = False) -> PlaybackResult`

Plays back the recorded session.

**Parameters:**
- `speed` (float): Playback speed multiplier
- `verify` (bool): Whether to verify expected outcomes

**Returns:** `PlaybackResult` with:
- `success` (bool): Whether playback succeeded
- `events_played` (int): Number of events replayed
- `errors` (list[str]): Any errors encountered

**Example:**

```python
player = HALPlayer("session.hal")
result = player.play(speed=2.0, verify=True)

if result.success:
    print(f"Played {result.events_played} events")
else:
    print(f"Errors: {result.errors}")
```

#### `step() -> bool`

Plays next event in session.

**Returns:** True if more events remain, False if finished

---

## Core Types

### CircularDependency

Represents a circular import dependency.

```python
@dataclass
class CircularDependency:
    cycle: list[str]          # Module names in cycle
    severity: str             # "high", "medium", "low"
    suggestion: str           # How to fix
    file_paths: list[str]     # Full file paths involved
```

### RaceCondition

Represents a potential race condition.

```python
@dataclass
class RaceCondition:
    shared_state: SharedState  # The shared state variable
    severity: str              # "critical", "high", "medium", "low"
    description: str           # What the issue is
    suggestion: str            # How to fix
    access_points: list[AccessPoint]  # Where state is accessed
```

### SharedState

Represents shared mutable state.

```python
@dataclass
class SharedState:
    name: str                  # Variable name
    file_path: str             # File containing variable
    line_number: int           # Line number
    access_type: str           # "read", "write", "both"
    protected: bool            # Whether protected by locks
    lock_name: str | None      # Name of protecting lock if any
```

### TestResult

Results from race condition testing.

```python
@dataclass
class TestResult:
    total_iterations: int
    successful: int
    failed: int
    race_detected: bool
    failure_details: list[str]
    duration: float
    operations_per_second: float
```

### HALConfig

Configuration for Mock HAL.

```python
@dataclass
class HALConfig:
    screen_size: tuple[int, int] = (1920, 1080)
    simulate_latency: bool = False
    latency_ms: float = 0.0
    error_rate: float = 0.0           # Simulate random errors
    recording_enabled: bool = False
```

---

## Utilities

### Logger

Structured logging for DevTools.

```python
from qontinui_devtools.utils import get_logger

logger = get_logger(__name__)
logger.info("Analysis started", path="/src")
logger.error("Analysis failed", error=str(e))
```

**Methods:**
- `debug(msg, **kwargs)` - Debug level logging
- `info(msg, **kwargs)` - Info level logging
- `warning(msg, **kwargs)` - Warning level logging
- `error(msg, **kwargs)` - Error level logging

### ProgressBar

Progress tracking for long operations.

```python
from qontinui_devtools.utils import ProgressBar

with ProgressBar(total=100, description="Analyzing") as progress:
    for i in range(100):
        # Do work
        progress.update(1)
```

### FileUtils

File system utilities.

```python
from qontinui_devtools.utils import find_python_files, read_file_safe

# Find all Python files
files = find_python_files("./src", exclude_patterns=["test_*"])

# Safely read file
content = read_file_safe("/path/to/file.py")
```

**Functions:**

#### `find_python_files(path: str, exclude_patterns: list[str] = None) -> list[str]`

Finds all Python files in a directory.

**Parameters:**
- `path` (str): Directory path
- `exclude_patterns` (list[str]): Glob patterns to exclude

**Returns:** List of file paths

#### `read_file_safe(file_path: str) -> str | None`

Safely reads a file, handling errors gracefully.

**Parameters:**
- `file_path` (str): Path to file

**Returns:** File content or None if error

#### `is_test_file(file_path: str) -> bool`

Checks if a file is a test file.

**Parameters:**
- `file_path` (str): Path to file

**Returns:** True if test file, False otherwise

---

## Error Handling

### Exceptions

DevTools defines custom exceptions:

```python
from qontinui_devtools.exceptions import (
    AnalysisError,
    CircularDependencyError,
    RaceConditionError,
    ProfileError
)
```

**Exception Hierarchy:**

```
DevToolsError
├── AnalysisError
│   ├── CircularDependencyError
│   └── RaceConditionError
├── ProfileError
│   ├── CPUProfileError
│   └── MemoryProfileError
└── HALError
    ├── HALRecordError
    └── HALPlaybackError
```

**Example Usage:**

```python
from qontinui_devtools import CircularDependencyDetector
from qontinui_devtools.exceptions import AnalysisError

try:
    detector = CircularDependencyDetector("./src")
    cycles = detector.analyze()
except AnalysisError as e:
    print(f"Analysis failed: {e}")
    # Handle error
```

---

## Type Hints

DevTools is fully typed and includes type stubs for all public APIs.

```python
from qontinui_devtools import CircularDependencyDetector
from typing import reveal_type

detector = CircularDependencyDetector("./src")
cycles = detector.analyze()

# Type checkers will understand:
reveal_type(cycles)  # list[CircularDependency]
```

**Type Checking:**

```bash
# Run mypy on your code using DevTools
mypy --strict your_code.py
```

---

## Best Practices

### Memory Management

```python
# Use context managers for cleanup
with ImportTracer() as tracer:
    import mymodule

# Or explicit cleanup
profiler = CPUProfiler()
try:
    result = profiler.profile_function(func)
finally:
    profiler.cleanup()
```

### Error Handling

```python
from qontinui_devtools import RaceConditionDetector
from qontinui_devtools.exceptions import AnalysisError

try:
    detector = RaceConditionDetector("./src")
    races = detector.analyze()

    if races:
        # Handle detected races
        pass

except AnalysisError as e:
    # Handle analysis errors
    logger.error("Analysis failed", error=str(e))
except Exception as e:
    # Handle unexpected errors
    logger.error("Unexpected error", error=str(e))
```

### Performance

```python
# For large codebases, use exclusion patterns
detector = CircularDependencyDetector(
    "./src",
    exclude_patterns=[
        "test_*",
        "*/tests/*",
        "*/migrations/*",
        "*/vendor/*"
    ]
)

# Limit analysis depth for faster results
detector.set_max_depth(5)
```

---

## Examples

### Complete Analysis Pipeline

```python
from qontinui_devtools import (
    CircularDependencyDetector,
    RaceConditionDetector,
    CPUProfiler
)

def analyze_project(path: str) -> dict:
    """Run comprehensive project analysis."""
    results = {}

    # Check imports
    import_detector = CircularDependencyDetector(path)
    cycles = import_detector.analyze()
    results['circular_dependencies'] = len(cycles)

    # Check concurrency
    race_detector = RaceConditionDetector(path)
    races = race_detector.analyze()
    results['race_conditions'] = len(races)

    # Profile main module
    profiler = CPUProfiler()
    profile_result = profiler.profile_script(f"{path}/main.py")
    results['hotspots'] = profile_result.hotspots

    return results

# Use it
results = analyze_project("./src")
print(f"Found {results['circular_dependencies']} import cycles")
print(f"Found {results['race_conditions']} race conditions")
```

### Custom Testing Framework Integration

```python
import pytest
from qontinui_devtools import RaceConditionTester

@pytest.fixture
def race_tester():
    return RaceConditionTester(threads=20, iterations=500)

def test_counter_thread_safety(race_tester):
    """Test counter for race conditions."""
    counter = Counter()

    result = race_tester.test_class(Counter, "increment")

    assert not result.race_detected, \
        f"Race condition detected: {result.failure_details}"
    assert counter.value == result.total_iterations, \
        "Counter value mismatch"
```

---

**Version:** 0.1.0
**Last Updated:** 2025-10-28
**License:** MIT
