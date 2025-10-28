# Architecture Documentation

Deep dive into how Qontinui DevTools works internally, design decisions, and extension points.

## Table of Contents

1. [Overview](#overview)
2. [Import Analysis Architecture](#import-analysis-architecture)
3. [Concurrency Analysis Architecture](#concurrency-analysis-architecture)
4. [Performance Profiling Architecture](#performance-profiling-architecture)
5. [Mock HAL Architecture](#mock-hal-architecture)
6. [CLI Architecture](#cli-architecture)
7. [Extension Points](#extension-points)
8. [Design Decisions](#design-decisions)
9. [Performance Considerations](#performance-considerations)

---

## Overview

Qontinui DevTools is built with a modular architecture that separates concerns and allows for independent development and testing of each component.

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                           │
│                    (Click + Rich UI)                        │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─────────────┬────────────────┬──────────────┐
             │             │                │              │
       ┌─────▼──────┐ ┌───▼────┐  ┌───────▼─────┐  ┌─────▼──────┐
       │   Import   │ │Concur- │  │  Profiling  │  │  Mock HAL  │
       │  Analysis  │ │ rency  │  │             │  │            │
       └─────┬──────┘ └───┬────┘  └──────┬──────┘  └─────┬──────┘
             │            │               │               │
       ┌─────▼────────────▼───────────────▼───────────────▼──────┐
       │                    Core Utilities                        │
       │         (Logging, File Utils, Graph Utils)              │
       └────────────────────────────────────────────────────────┘
```

### Component Interaction

```
User Command
    │
    ▼
CLI Parser (Click)
    │
    ▼
Analyzer Factory
    │
    ├──► CircularDependencyDetector
    │        │
    │        ├──► AST Parser
    │        ├──► Dependency Graph Builder
    │        └──► Cycle Detector (Johnson's Algorithm)
    │
    ├──► RaceConditionDetector
    │        │
    │        ├──► AST Analyzer
    │        ├──► Thread Safety Checker
    │        └──► Pattern Matcher
    │
    └──► Reporter
             │
             ├──► Text Reporter
             ├──► JSON Reporter
             └──► HTML Reporter
```

---

## Import Analysis Architecture

### Components

#### 1. Static Analyzer

Uses Python's AST (Abstract Syntax Tree) to parse import statements.

**Implementation:**

```python
class ImportAnalyzer:
    """Analyzes Python files for import statements."""

    def analyze_file(self, file_path: str) -> list[ImportStatement]:
        """Extract all imports from a Python file."""
        with open(file_path) as f:
            tree = ast.parse(f.read(), filename=file_path)

        visitor = ImportVisitor()
        visitor.visit(tree)
        return visitor.imports

class ImportVisitor(ast.NodeVisitor):
    """AST visitor for import statements."""

    def visit_Import(self, node: ast.Import) -> None:
        """Handle 'import x' statements."""
        for alias in node.names:
            self.imports.append(ImportStatement(
                module=alias.name,
                line_number=node.lineno,
                type='import'
            ))

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Handle 'from x import y' statements."""
        self.imports.append(ImportStatement(
            module=node.module,
            line_number=node.lineno,
            type='from'
        ))
```

**Why AST?**
- Accurate: No false positives from comments or strings
- Fast: Native Python parsing
- Complete: Captures all import types (import, from, as)

#### 2. Dependency Graph Builder

Builds a directed graph of module dependencies using NetworkX.

**Data Structure:**

```python
# Each node represents a module
nodes = {'module_a', 'module_b', 'module_c'}

# Each edge represents an import
edges = [
    ('module_a', 'module_b'),  # module_a imports module_b
    ('module_b', 'module_c'),
    ('module_c', 'module_a'),  # Creates a cycle!
]

graph = nx.DiGraph()
graph.add_nodes_from(nodes)
graph.add_edges_from(edges)
```

**Why NetworkX?**
- Battle-tested graph algorithms
- Efficient cycle detection
- Easy visualization with Graphviz
- Rich analysis capabilities

#### 3. Cycle Detector

Uses Johnson's algorithm to find all elementary cycles efficiently.

**Algorithm:**

```python
def find_cycles(graph: nx.DiGraph) -> list[list[str]]:
    """Find all elementary cycles in the graph.

    Uses Johnson's algorithm:
    - Time complexity: O((n + e)(c + 1))
    - Space complexity: O(n + e)

    where:
    - n = number of nodes
    - e = number of edges
    - c = number of cycles
    """
    cycles = list(nx.simple_cycles(graph))
    return cycles
```

**Why Johnson's Algorithm?**
- Finds ALL cycles (not just one)
- Efficient for large graphs
- Guaranteed to terminate
- Returns minimal cycles only

#### 4. Runtime Import Tracer

Hooks into Python's import system to track imports as they happen.

**Implementation:**

```python
class ImportTracer:
    """Runtime import tracer using import hooks."""

    def __enter__(self):
        """Install import hook."""
        self.original_import = builtins.__import__
        builtins.__import__ = self._traced_import
        return self

    def __exit__(self, *args):
        """Remove import hook."""
        builtins.__import__ = self.original_import

    def _traced_import(self, name, *args, **kwargs):
        """Traced import function."""
        # Record the import event
        self.events.append(ImportEvent(
            importer=self._get_caller_module(),
            imported=name,
            timestamp=time.time()
        ))

        # Call original import
        return self.original_import(name, *args, **kwargs)
```

**How It Works:**

```
Application Import
       │
       ▼
builtins.__import__() ──► Our _traced_import()
       │                          │
       │                          ├──► Record event
       │                          │
       │                          └──► Call original import
       │
       ▼
Module Loaded
```

**Trade-offs:**
- ✅ Accurate runtime behavior
- ✅ Catches dynamic imports
- ❌ Performance overhead
- ❌ May miss lazy imports

### Module Resolution

**Algorithm:**

```python
def resolve_module(import_name: str, current_file: Path) -> Path | None:
    """Resolve import name to file path.

    Resolution order:
    1. Relative imports (., ..)
    2. Package imports (same directory)
    3. Installed packages (site-packages)
    4. Standard library
    """
    # Try relative import
    if import_name.startswith('.'):
        return resolve_relative(import_name, current_file)

    # Try package import
    package_path = find_package_file(import_name, current_file.parent)
    if package_path:
        return package_path

    # Check if it's installed
    try:
        spec = importlib.util.find_spec(import_name)
        return Path(spec.origin) if spec else None
    except (ImportError, ValueError):
        return None
```

### Visualization Pipeline

```
Dependency Graph
      │
      ▼
Graphviz DOT Format
      │
      ├──► Layout Engine (dot)
      │
      ▼
Rendered Image (PNG/SVG/PDF)
```

**Graphviz DOT Generation:**

```python
def generate_dot(graph: nx.DiGraph) -> str:
    """Generate Graphviz DOT representation."""
    dot = graphviz.Digraph(comment='Module Dependencies')

    # Configure appearance
    dot.attr(rankdir='LR')  # Left to right
    dot.attr('node', shape='box', style='rounded')

    # Add nodes with colors
    for node in graph.nodes():
        color = 'red' if is_in_cycle(node) else 'lightblue'
        dot.node(node, fillcolor=color, style='filled')

    # Add edges
    for source, target in graph.edges():
        style = 'bold' if is_cycle_edge(source, target) else 'solid'
        dot.edge(source, target, style=style)

    return dot.source
```

---

## Concurrency Analysis Architecture

### Components

#### 1. Static Analyzer

Analyzes code for thread-safety issues using AST and pattern matching.

**Detection Patterns:**

```python
UNSAFE_PATTERNS = [
    # Pattern 1: Unprotected shared state
    {
        'pattern': 'self.{var} = {value}',
        'context': 'class method',
        'check': 'no lock acquisition before assignment'
    },

    # Pattern 2: Read-modify-write
    {
        'pattern': 'self.{var} += {value}',
        'context': 'class method',
        'check': 'no atomic operation or lock'
    },

    # Pattern 3: Inconsistent locking
    {
        'pattern': 'access to {var}',
        'context': 'multiple methods',
        'check': 'some methods lock, some don\'t'
    }
]
```

**Analysis Flow:**

```
Python File
    │
    ▼
AST Parser
    │
    ▼
Class Analyzer
    │
    ├──► Find shared state (class/instance variables)
    │
    ├──► Find all access points
    │
    ├──► Detect thread-related code (threading, asyncio)
    │
    └──► Check synchronization patterns
         │
         ▼
    Race Condition Report
```

#### 2. Thread Safety Checker

```python
class ThreadSafetyChecker:
    """Checks if shared state is properly synchronized."""

    def check_state(self, state: SharedState) -> list[RaceCondition]:
        """Analyze a shared state variable."""
        races = []

        # Find all access points
        accesses = self.find_accesses(state)

        # Check if any are writes
        writes = [a for a in accesses if a.is_write]
        reads = [a for a in accesses if a.is_read]

        if not writes:
            return []  # Read-only is safe

        # Check each write
        for write in writes:
            if not self.is_protected(write):
                races.append(RaceCondition(
                    shared_state=state,
                    access_point=write,
                    severity=self.calculate_severity(write)
                ))

        # Check for inconsistent locking
        if self.has_inconsistent_locking(accesses):
            races.append(RaceCondition(
                shared_state=state,
                severity='high',
                description='Inconsistent lock usage'
            ))

        return races

    def is_protected(self, access: AccessPoint) -> bool:
        """Check if access is protected by synchronization."""
        # Check for lock acquisition
        if self.has_lock_before(access):
            return True

        # Check for atomic operation
        if self.is_atomic(access):
            return True

        # Check for single-threaded context
        if not self.is_multithreaded_context(access):
            return True

        return False
```

#### 3. Lock Analysis

Tracks lock acquisition and release to detect deadlocks.

**Lock Graph:**

```python
# Nodes: Locks
# Edges: Acquisition order

lock_graph = nx.DiGraph()
lock_graph.add_edge('lock_a', 'lock_b')  # lock_a acquired before lock_b
lock_graph.add_edge('lock_b', 'lock_c')
lock_graph.add_edge('lock_c', 'lock_a')  # Cycle = potential deadlock!
```

**Deadlock Detection:**

```python
def detect_deadlocks(lock_graph: nx.DiGraph) -> list[Deadlock]:
    """Find potential deadlock scenarios.

    A cycle in the lock graph indicates a potential deadlock:
    Thread 1: acquire(A) -> acquire(B)
    Thread 2: acquire(B) -> acquire(A)
    """
    cycles = list(nx.simple_cycles(lock_graph))

    return [
        Deadlock(
            locks=cycle,
            severity='critical',
            description=f'Potential deadlock: {" -> ".join(cycle)}'
        )
        for cycle in cycles
    ]
```

#### 4. Dynamic Tester

Tests functions concurrently to detect actual race conditions.

**Testing Strategy:**

```python
class RaceConditionTester:
    """Dynamic race condition testing."""

    def test_function(self, func: Callable) -> TestResult:
        """Test function for races by concurrent execution.

        Strategy:
        1. Create shared state
        2. Launch multiple threads
        3. Each thread executes function many times
        4. Check for data corruption
        """
        # Shared state for testing
        state = {'counter': 0, 'errors': []}

        def worker():
            for _ in range(self.iterations):
                try:
                    func(state)
                except Exception as e:
                    state['errors'].append(str(e))

        # Launch threads
        threads = [
            threading.Thread(target=worker)
            for _ in range(self.threads)
        ]

        start_time = time.time()

        for t in threads:
            t.start()

        for t in threads:
            t.join(timeout=self.timeout)

        duration = time.time() - start_time

        # Analyze results
        expected = self.threads * self.iterations
        actual = state['counter']

        return TestResult(
            total_iterations=expected,
            successful=actual,
            failed=expected - actual,
            race_detected=(actual != expected or state['errors']),
            failure_details=state['errors'],
            duration=duration
        )
```

### Severity Calculation

```python
def calculate_severity(race: RaceCondition) -> str:
    """Calculate severity of a race condition.

    Factors:
    1. Type of access (read/write/both)
    2. Frequency of access
    3. Data criticality
    4. Existing protections
    """
    score = 0

    # Write access is more critical
    if race.has_writes:
        score += 3

    # High-frequency access is more likely to cause issues
    if race.access_frequency > 10:
        score += 2

    # Critical data (money, security, etc.)
    if race.is_critical_data:
        score += 3

    # No existing protection
    if not race.has_any_protection:
        score += 2

    # Map score to severity
    if score >= 8:
        return 'critical'
    elif score >= 6:
        return 'high'
    elif score >= 4:
        return 'medium'
    else:
        return 'low'
```

---

## Performance Profiling Architecture

### CPU Profiling

Uses `py-spy` for sampling-based profiling without code modification.

**Architecture:**

```
Target Process
      │
      ▼
py-spy (external process)
      │
      ├──► Sample stack trace (100 Hz)
      │
      ├──► Aggregate samples
      │
      └──► Generate flame graph
            │
            ▼
      SVG Visualization
```

**Why py-spy?**
- ✅ No code modification required
- ✅ Low overhead (~3-5%)
- ✅ Works on running processes
- ✅ Beautiful flame graphs
- ❌ Sampling (not deterministic)

### Memory Profiling

Uses `memray` for detailed memory tracking.

**Tracking:**

```
Memory Allocation
       │
       ▼
memray intercepts malloc/free
       │
       ├──► Record allocation size
       ├──► Capture stack trace
       └──► Track lifetime
             │
             ▼
       Memory Timeline
```

**Features:**
- Track allocations by file/function
- Detect memory leaks
- Show allocation timeline
- Generate reports

---

## Mock HAL Architecture

### Design Goals

1. **Transparency**: Drop-in replacement for real HAL
2. **Determinism**: Reproducible test results
3. **Recording**: Capture interactions for replay
4. **Simulation**: Realistic timing and errors

### Architecture

```
┌─────────────────────────────────────────────┐
│           Application Code                  │
└──────────────┬──────────────────────────────┘
               │
               │ HAL Interface
               │
     ┌─────────▼──────────┐
     │    HAL Adapter     │  (Switches between real/mock)
     └─────────┬──────────┘
               │
         ┌─────┴──────┐
         │            │
    ┌────▼───┐   ┌───▼────┐
    │ Real   │   │  Mock  │
    │  HAL   │   │  HAL   │
    └────────┘   └───┬────┘
                     │
              ┌──────┴───────┐
              │              │
         ┌────▼────┐   ┌────▼─────┐
         │ Virtual │   │ Recorder │
         │ Screen  │   │          │
         └─────────┘   └──────────┘
```

### Virtual Screen

Simulates screen using NumPy arrays:

```python
class VirtualScreen:
    """Virtual screen implementation."""

    def __init__(self, width: int, height: int):
        # RGB image buffer
        self.buffer = np.zeros((height, width, 3), dtype=np.uint8)
        self.width = width
        self.height = height

    def draw_pixel(self, x: int, y: int, color: tuple[int, int, int]):
        """Draw a single pixel."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y, x] = color

    def capture(self) -> np.ndarray:
        """Capture current screen state."""
        return self.buffer.copy()
```

### Event Simulation

```python
class EventSimulator:
    """Simulates user input events."""

    def simulate_click(self, x: int, y: int, button: str):
        """Simulate mouse click with realistic timing."""
        # Mouse move (if needed)
        if self.current_position != (x, y):
            self._simulate_mouse_move(x, y)
            time.sleep(0.01)  # Realistic movement time

        # Button down
        self._send_event(MouseDownEvent(x, y, button))
        time.sleep(0.05)  # Typical click duration

        # Button up
        self._send_event(MouseUpEvent(x, y, button))
```

### Recording Format

```python
@dataclass
class HALEvent:
    """Represents a recorded HAL event."""
    timestamp: float
    event_type: str  # 'click', 'type', 'wait', etc.
    parameters: dict[str, Any]
    screen_state: bytes | None  # Optional screenshot

# Example recording
recording = [
    HALEvent(0.0, 'click', {'x': 100, 'y': 200, 'button': 'left'}, None),
    HALEvent(0.5, 'type', {'text': 'Hello'}, None),
    HALEvent(1.0, 'capture', {}, screen_bytes),
]
```

---

## CLI Architecture

### Command Structure

Built with Click's command groups:

```python
@click.group()
def main():
    """Root command."""
    pass

@main.group()
def import_cmd():
    """Import commands."""
    pass

@import_cmd.command('check')
def check_imports():
    """Check imports command."""
    pass

# Results in: qontinui-devtools import check
```

### Rich Output

Uses Rich library for beautiful console output:

```python
from rich.console import Console
from rich.table import Table

console = Console()

# Tables
table = Table(title="Analysis Results")
table.add_column("Check", style="cyan")
table.add_column("Status", style="bold")
console.print(table)

# Panels
console.print(Panel(
    "Error message",
    title="Error",
    border_style="red"
))

# Progress bars
with console.status("Analyzing..."):
    # Long operation
    pass
```

---

## Extension Points

### Custom Analyzers

```python
from qontinui_devtools.core import BaseAnalyzer

class CustomAnalyzer(BaseAnalyzer):
    """Custom analyzer implementation."""

    def analyze(self, path: str) -> list[Issue]:
        """Implement custom analysis logic."""
        issues = []

        # Your analysis code here

        return issues

    def get_name(self) -> str:
        return "custom"

# Register analyzer
from qontinui_devtools.registry import register_analyzer
register_analyzer('custom', CustomAnalyzer)

# Use it
qontinui-devtools analyze ./src --analyzers custom
```

### Custom Reporters

```python
from qontinui_devtools.reporting import BaseReporter

class CustomReporter(BaseReporter):
    """Custom report format."""

    def generate(self, results: AnalysisResults) -> str:
        """Generate custom report."""
        # Your report generation code
        return report_content

# Register reporter
from qontinui_devtools.registry import register_reporter
register_reporter('custom', CustomReporter)

# Use it
qontinui-devtools analyze ./src --format custom
```

---

## Design Decisions

### Why Static Analysis First?

**Rationale:**
- Fast feedback (seconds vs minutes)
- No execution required
- Can analyze any code
- Finds structural issues

**Trade-offs:**
- May have false positives
- Can't catch runtime-only issues
- Limited by static analysis limitations

### Why NetworkX for Graphs?

**Alternatives Considered:**
- Custom graph implementation
- igraph
- graph-tool

**Decision:**
- NetworkX wins on usability
- Rich algorithm library
- Good Python integration
- Acceptable performance for our use case

### Why AST over Regex?

**AST Advantages:**
- Accurate parsing
- Handles all syntax
- Extracts context
- No false positives from strings/comments

**Regex Issues:**
- Fragile
- Can't handle complex syntax
- Many false positives
- Hard to maintain

---

## Performance Considerations

### Caching Strategy

```python
@lru_cache(maxsize=1000)
def resolve_module(import_name: str, base_path: str) -> str | None:
    """Cached module resolution."""
    # Expensive operation cached
    pass
```

### Parallel Processing

```python
from concurrent.futures import ProcessPoolExecutor

def analyze_files_parallel(files: list[str]) -> list[Result]:
    """Analyze files in parallel."""
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(analyze_file, files))
    return results
```

### Memory Management

```python
def analyze_large_codebase(path: str) -> Results:
    """Analyze large codebase efficiently."""
    # Process files in batches
    for batch in chunk_files(find_files(path), batch_size=100):
        # Process batch
        results = analyze_batch(batch)

        # Yield results incrementally
        yield from results

        # Clear memory
        gc.collect()
```

---

**Version:** 0.1.0
**Last Updated:** 2025-10-28
**License:** MIT
