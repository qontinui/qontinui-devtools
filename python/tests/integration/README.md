# Phase 3 Runtime Monitoring Integration Tests

Comprehensive integration test suite for Phase 3 runtime monitoring tools.

## Overview

This test suite validates the integration, performance, and reliability of all Phase 3 runtime monitoring tools:

- **ActionProfiler** - Profiles function execution and performance
- **EventTracer** - Traces events and state changes
- **MemoryProfiler** - Monitors memory usage and allocations
- **PerformanceDashboard** - Real-time performance visualization

## Test Modules

### 1. `test_runtime_integration.py`

Tests integration between monitoring tools to ensure they work together correctly.

**Test Classes:**
- `TestProfilerEventTracerIntegration` - Profiler + Event Tracer integration
- `TestMemoryProfilerIntegration` - Memory Profiler with other tools
- `TestDashboardIntegration` - Dashboard integration with all tools
- `TestAllToolsConcurrently` - All tools running together

**Key Tests:**
```python
# Test profiler and tracer together
def test_profiler_and_tracer_together()

# Test all tools without interference
def test_all_tools_no_interference()

# Test dashboard with all monitoring data
def test_dashboard_with_all_tools()
```

**Run:**
```bash
pytest tests/integration/test_runtime_integration.py -v
```

### 2. `test_end_to_end.py`

End-to-end workflow tests from analysis to report generation.

**Test Classes:**
- `TestFullMonitoringWorkflow` - Complete monitoring workflows
- `TestCLIEndToEnd` - CLI command testing
- `TestReportGeneration` - Comprehensive report generation

**Key Tests:**
```python
# Full workflow: analyze + profile + report
def test_analyze_profile_report_workflow()

# Multi-action monitoring
def test_multi_action_monitoring_workflow()

# Generate HTML report with all data
def test_generate_html_report()
```

**Run:**
```bash
pytest tests/integration/test_end_to_end.py -v -m e2e
```

### 3. `test_performance.py`

Performance benchmarks, overhead measurement, and stress testing.

**Test Classes:**
- `TestProfilerPerformance` - Profiler performance tests
- `TestEventTracerPerformance` - Event tracer performance tests
- `TestMemoryProfilerPerformance` - Memory profiler performance tests
- `TestStressTests` - Stress testing all tools
- `TestMemoryLeakDetection` - Memory leak detection
- `TestOverallPerformanceMetrics` - Combined performance metrics

**Key Tests:**
```python
# Measure profiler overhead
def test_profiler_overhead()

# Test event tracer latency
def test_event_tracer_latency()

# Stress test with high volume
def test_event_tracer_stress_high_volume()

# Detect memory leaks
def test_profiler_no_memory_leak()
```

**Performance Thresholds:**
- Maximum overhead: 5%
- Maximum memory usage: 100MB
- Maximum event latency: 1ms
- Maximum startup time: 100ms

**Run:**
```bash
# Run all performance tests
pytest tests/integration/test_performance.py -v -m performance

# Run only stress tests
pytest tests/integration/test_performance.py -v -m stress
```

### 4. `test_concurrent_tools.py`

Tests for thread-safety and concurrent tool usage.

**Test Classes:**
- `TestConcurrentToolAccess` - Thread-safe tool access
- `TestConcurrentToolLifecycle` - Concurrent init/shutdown
- `TestConcurrentDataCollection` - Concurrent data collection
- `TestRaceConditions` - Race condition detection
- `TestAsyncConcurrency` - Async/await patterns

**Key Tests:**
```python
# Test profiler thread safety
def test_profiler_thread_safety()

# Test no race conditions in event ordering
def test_no_race_in_event_ordering()

# Test no deadlocks with all tools
def test_no_deadlock_with_all_tools()

# Test async/await patterns
def test_profiler_with_async_await()
```

**Run:**
```bash
pytest tests/integration/test_concurrent_tools.py -v -m concurrent
```

## Fixtures (`conftest.py`)

Shared fixtures for all integration tests:

### Sample Data Fixtures
- `sample_qontinui_action` - Sample action for testing
- `sample_qontinui_project` - Complete project structure
- `sample_action_instance` - Action instance for execution
- `memory_intensive_action` - Memory allocation action
- `concurrent_action` - Concurrent execution action

### Configuration Fixtures
- `profiler_config` - Default profiler configuration
- `event_tracer_config` - Default event tracer configuration
- `memory_profiler_config` - Default memory profiler configuration
- `dashboard_config` - Default dashboard configuration

### Test Utilities
- `performance_thresholds` - Performance test thresholds
- `stress_test_config` - Stress test configuration
- `overhead_measurer` - Overhead measurement utility

## Running Tests

### Run All Integration Tests
```bash
pytest tests/integration/ -v
```

### Run Specific Test Module
```bash
pytest tests/integration/test_runtime_integration.py -v
```

### Run by Marker
```bash
# Integration tests only
pytest tests/integration/ -m integration

# End-to-end tests
pytest tests/integration/ -m e2e

# Performance tests
pytest tests/integration/ -m performance

# Stress tests
pytest tests/integration/ -m stress

# Concurrent tests
pytest tests/integration/ -m concurrent
```

### Run with Coverage
```bash
pytest tests/integration/ --cov=qontinui_devtools.runtime --cov-report=html
```

### Run in Parallel
```bash
pytest tests/integration/ -n auto
```

## Test Markers

The test suite uses the following pytest markers:

- `@pytest.mark.integration` - Integration test
- `@pytest.mark.e2e` - End-to-end test
- `@pytest.mark.performance` - Performance test
- `@pytest.mark.stress` - Stress test
- `@pytest.mark.concurrent` - Concurrency test

Configure markers in `pyproject.toml`:
```toml
[tool.pytest.ini_options]
markers = [
    "integration: Integration tests",
    "e2e: End-to-end tests",
    "performance: Performance tests",
    "stress: Stress tests",
    "concurrent: Concurrency tests",
]
```

## Performance Metrics

### Success Criteria

All tests must meet these criteria:

1. **Overhead** < 5%
   - Combined overhead of all monitoring tools
   - Measured against baseline execution

2. **Memory Usage** < 100MB
   - Peak memory usage during monitoring
   - Includes all tool buffers and data structures

3. **Event Latency** < 1ms
   - Average time to trace an event
   - P95 latency for event tracing

4. **Startup Time** < 100ms
   - Time to initialize all monitoring tools
   - Ready to start monitoring

5. **No Memory Leaks**
   - Memory growth < 10% over extended runs
   - Proper cleanup on tool shutdown

### Measuring Performance

Example output from performance tests:

```
Profiler Overhead: 2.34%
Baseline: 45.23ms
Profiled: 46.29ms

Event Tracer Overhead: 1.87%
Baseline: 50.12ms
Traced: 51.06ms

Combined Overhead: 4.21%
✓ PASS - Below 5% threshold

Memory Usage:
  Profiler: 12.5MB
  Event Tracer: 8.3MB
  Memory Profiler: 5.2MB
  Dashboard: 3.1MB
  Total: 29.1MB
✓ PASS - Below 100MB threshold
```

## Expected Test Results

### Integration Tests
- **Total Tests**: ~40
- **Expected Pass Rate**: 100%
- **Typical Duration**: 30-60 seconds

### Performance Tests
- **Total Tests**: ~25
- **Expected Pass Rate**: 100%
- **Typical Duration**: 60-120 seconds

### Stress Tests
- **Total Tests**: ~10
- **Expected Pass Rate**: 100%
- **Typical Duration**: 120-180 seconds

### Concurrent Tests
- **Total Tests**: ~20
- **Expected Pass Rate**: 100%
- **Typical Duration**: 45-90 seconds

## Troubleshooting

### Tests Timing Out

If tests timeout, increase the timeout threshold:
```bash
pytest tests/integration/ --timeout=300
```

### Performance Tests Failing

Performance tests are sensitive to system load:
1. Close other applications
2. Run tests in isolation
3. Check system resources
4. Adjust thresholds if needed

### Concurrent Tests Failing

If concurrent tests fail intermittently:
1. Check for race conditions
2. Verify thread-safety of tools
3. Increase timeout for thread operations
4. Run tests multiple times to confirm

### Memory Tests Failing

If memory tests fail:
1. Run garbage collection before tests
2. Check for memory leaks in test code
3. Verify proper cleanup in fixtures
4. Monitor system memory during tests

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install poetry
          poetry install

      - name: Run integration tests
        run: |
          poetry run pytest tests/integration/ \
            -v \
            --cov=qontinui_devtools.runtime \
            --cov-report=xml \
            --junit-xml=test-results.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml

      - name: Publish test results
        uses: EnricoMi/publish-unit-test-result-action@v2
        if: always()
        with:
          files: test-results.xml
```

## Development Workflow

### Adding New Tests

1. **Determine test type:**
   - Integration: Tool interaction tests
   - E2E: Full workflow tests
   - Performance: Overhead/benchmark tests
   - Concurrent: Thread-safety tests

2. **Create test function:**
   ```python
   @pytest.mark.integration
   def test_new_feature(
       sample_action_instance,
       profiler_config,
       event_tracer_config
   ):
       """Test description."""
       # Setup
       profiler = ActionProfiler(profiler_config)
       tracer = EventTracer(event_tracer_config)

       # Execute
       profiler.start()
       tracer.start()
       # ... test code ...
       tracer.stop()
       profiler.stop()

       # Assert
       assert profiler.get_profile_data()['total_calls'] > 0
   ```

3. **Add fixtures if needed:**
   ```python
   @pytest.fixture
   def custom_fixture():
       """Custom fixture for specific tests."""
       # Setup
       yield data
       # Teardown
   ```

4. **Run and verify:**
   ```bash
   pytest tests/integration/test_module.py::test_new_feature -v
   ```

### Test Best Practices

1. **Use descriptive names**
   - `test_profiler_captures_all_events()` ✓
   - `test_profiler()` ✗

2. **Test one thing at a time**
   - Focus on specific integration point
   - Keep tests simple and focused

3. **Clean up resources**
   - Always stop tools in `finally` blocks
   - Use fixtures for automatic cleanup

4. **Assert meaningful checks**
   - Verify data integrity
   - Check error conditions
   - Validate performance metrics

5. **Add docstrings**
   - Explain what is being tested
   - Document expected behavior
   - Note any special conditions

## Example Test Session

```bash
$ pytest tests/integration/ -v

tests/integration/test_runtime_integration.py::TestProfilerEventTracerIntegration::test_profiler_and_tracer_together PASSED [ 5%]
tests/integration/test_runtime_integration.py::TestProfilerEventTracerIntegration::test_profiler_captures_tracer_overhead PASSED [ 10%]
tests/integration/test_runtime_integration.py::TestMemoryProfilerIntegration::test_memory_profiler_with_action_profiler PASSED [ 15%]
tests/integration/test_runtime_integration.py::TestDashboardIntegration::test_dashboard_with_all_tools PASSED [ 20%]
tests/integration/test_end_to_end.py::TestFullMonitoringWorkflow::test_analyze_profile_report_workflow PASSED [ 25%]
tests/integration/test_end_to_end.py::TestCLIEndToEnd::test_runtime_monitor_command PASSED [ 30%]
tests/integration/test_performance.py::TestProfilerPerformance::test_profiler_overhead PASSED [ 35%]
tests/integration/test_performance.py::TestEventTracerPerformance::test_event_tracer_latency PASSED [ 40%]
tests/integration/test_concurrent_tools.py::TestConcurrentToolAccess::test_profiler_thread_safety PASSED [ 45%]
...

==================== 95 passed in 180.23s ====================
```

## Contributing

When adding new runtime monitoring features:

1. Add integration tests to verify tool interactions
2. Add performance tests to ensure overhead is acceptable
3. Add concurrent tests if feature involves threading
4. Update this README with new test information
5. Ensure all tests pass before submitting PR

## Support

For issues with integration tests:
- Check test output for specific failures
- Review test logs for error details
- Consult troubleshooting section above
- Open issue with test output and environment details

## License

MIT License - Same as qontinui-devtools main project
