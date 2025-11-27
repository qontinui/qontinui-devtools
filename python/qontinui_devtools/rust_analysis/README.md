# Rust Analysis Tools

Static analysis tools for Rust codebases that work without requiring `rustc` or `cargo`. These tools use regex-based pattern matching to analyze Rust source code.

## Features

### 1. Circular Dependency Detector

Detects circular module dependencies in Rust code by analyzing `mod` and `use` statements.

**Usage:**
```bash
qontinui-devtools rust import check <path>
```

**Example:**
```bash
qontinui-devtools rust import check /path/to/rust/project/src
qontinui-devtools rust import check ./src --verbose
qontinui-devtools rust import check ./src --output report.txt
```

**What it detects:**
- Direct circular dependencies (A -> B -> A)
- Indirect circular dependencies (A -> B -> C -> A)
- Module path cycles

**Output:**
- Severity level (high, medium, low)
- Cycle path
- Files involved
- Statistics on modules and dependencies

### 2. Dead Code Detector

Finds potentially unused code including functions, structs, enums, traits, and constants.

**Usage:**
```bash
qontinui-devtools rust dead-code <path>
```

**Example:**
```bash
qontinui-devtools rust dead-code /path/to/rust/project/src
qontinui-devtools rust dead-code ./src --min-confidence 0.8
qontinui-devtools rust dead-code ./src --output dead_code.txt
```

**What it detects:**
- Unused functions (not called anywhere)
- Unused structs (not instantiated)
- Unused enums (not referenced)
- Unused traits (not implemented)
- Unused constants (not used)

**Features:**
- Confidence scoring (0-1)
- Visibility tracking (pub, pub(crate), private)
- Smart filtering for common patterns (main, new, test functions)

### 3. Unsafe Code Analyzer

Analyzes all `unsafe` code usage in Rust projects.

**Usage:**
```bash
qontinui-devtools rust unsafe <path>
```

**Example:**
```bash
qontinui-devtools rust unsafe /path/to/rust/project/src
qontinui-devtools rust unsafe ./src --verbose
qontinui-devtools rust unsafe ./src --output unsafe_report.txt
```

**What it detects:**
- Unsafe functions
- Unsafe blocks
- Unsafe trait implementations
- Unsafe trait definitions

**Categories:**
- Raw pointers
- FFI calls
- Memory operations (transmute, from_raw, etc.)
- Assembly code
- Union access
- Mutable statics

**Output:**
- Location of each unsafe block
- Category of unsafe operation
- Code context
- Statistics by type and category

### 4. Complexity Analyzer

Measures code complexity to identify areas that may need refactoring.

**Usage:**
```bash
qontinui-devtools rust complexity <path>
```

**Example:**
```bash
qontinui-devtools rust complexity /path/to/rust/project/src
qontinui-devtools rust complexity ./src --threshold 15
qontinui-devtools rust complexity ./src --output complexity.txt
```

**What it measures:**
- Function cyclomatic complexity
- File sizes (lines of code)
- Function sizes
- Complex match statements

**Complexity calculation:**
- Base complexity: 1
- Each `if`, `else if`: +1
- Each match arm (`=>`): +1
- Each loop (`for`, `while`, `loop`): +1
- Each logical operator (`&&`, `||`): +1
- Each `?` operator: +1

**Output:**
- Complexity score for each function
- Line count
- Average metrics
- Top most complex functions

### 5. Comprehensive Analysis

Runs all analyses in one command.

**Usage:**
```bash
qontinui-devtools rust analyze <path>
```

**Example:**
```bash
qontinui-devtools rust analyze /path/to/rust/project/src
qontinui-devtools rust analyze ./src --output-dir ./reports
```

**What it does:**
- Runs all four analyzers
- Generates comprehensive reports
- Provides summary statistics
- Optionally saves all reports to a directory

## Test Results on qontinui-runner

The tools were tested on `/mnt/c/qontinui/qontinui-runner/src-tauri/src`:

### Circular Dependencies
- Files scanned: 35
- Modules: 35
- Dependencies: 69
- Cycles found: 6

**Example cycles detected:**
1. `display -> display::profile -> display` (HIGH severity)
2. `display -> display::processor -> display` (HIGH severity)
3. `executor -> executor::output -> executor::events -> commands -> executor` (MEDIUM severity)

### Dead Code
- Total items found: 44
- Functions: 27
- Constants: 17
- Structs: 0

**Examples:**
- Unused constants: `SETTINGS_FILE`, `HEALTH_CHECK_INTERVAL`
- Unused functions: `greet`, `run_app`, `default_auto_load_last_config`

### Unsafe Code
- Total unsafe blocks: 0
- The qontinui-runner codebase has no unsafe code blocks

### Complexity
- Complex elements: 28
- Avg function complexity: 18.3
- Avg function lines: 87.55

**Most complex functions:**
1. `process` in `action_log.rs`: Complexity 47, 230 lines
2. `handle_message` in `lifecycle.rs`: Complexity 31, 113 lines
3. `delete_old_sessions` in `mod.rs`: Complexity 27, 71 lines

## Implementation Details

### No External Dependencies for Core Functionality

The tools are designed to work without requiring:
- `rustc` compiler
- `cargo` build system
- Rust toolchain installation

They use Python's built-in `re` module for pattern matching.

### Optional Dependencies

- `networkx`: For advanced graph algorithms (optional, falls back to simple DFS)
- `rich`: For colored console output (required for CLI)

### Architecture

Each analyzer follows a similar pattern:

```python
class Analyzer:
    def __init__(self, root_path: str, verbose: bool = False):
        # Initialize with project path

    def analyze(self) -> list[Result]:
        # Perform analysis

    def get_statistics(self) -> dict:
        # Return statistics

    def generate_report(self) -> str:
        # Generate text report

    def generate_rich_report(self) -> None:
        # Generate rich console report
```

### Regex Patterns Used

**Function definitions:**
```python
r"(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+(\w+)\s*[<(]"
```

**Struct definitions:**
```python
r"(?:pub(?:\([^)]*\))?\s+)?struct\s+(\w+)"
```

**Enum definitions:**
```python
r"(?:pub(?:\([^)]*\))?\s+)?enum\s+(\w+)"
```

**Unsafe blocks:**
```python
r"unsafe\s*\{"
```

**Module declarations:**
```python
r"(?:pub(?:\([^)]*\))?\s+)?mod\s+(\w+)\s*;"
```

**Use statements:**
```python
r"use\s+(?:crate::)?(?:super::)?(?:self::)?([a-zA-Z_][\w:]*)"
```

## Limitations

### Circular Dependency Detector
- May not detect all cycle types (e.g., cycles through external crates)
- Module resolution is heuristic-based
- Relative imports (`super::`, `self::`) have limited resolution

### Dead Code Detector
- Static analysis only - doesn't track dynamic dispatch
- May flag pub items that are used by external crates
- Macros can create false positives
- Tests and benchmarks may be flagged

### Unsafe Analyzer
- Only finds explicit `unsafe` keywords
- Doesn't analyze what unsafe operations actually do
- Can't verify safety properties

### Complexity Analyzer
- Cyclomatic complexity is an approximation
- Doesn't consider cognitive complexity
- May overcount in some macro-heavy code

## Best Practices

1. **Use with version control**: Run before commits to catch issues early
2. **Set appropriate thresholds**: Adjust complexity thresholds for your team
3. **Review confidence scores**: Focus on high-confidence dead code first
4. **Track over time**: Monitor trends in complexity and unsafe usage
5. **Combine with cargo tools**: Use alongside `cargo clippy` and `cargo audit`

## Future Enhancements

Potential improvements:
- Better macro handling
- More accurate module resolution
- Integration with `rust-analyzer` LSP
- Support for workspace analysis
- HTML report generation
- Historical trend tracking
- Git blame integration

## License

Part of the Qontinui DevTools suite.
