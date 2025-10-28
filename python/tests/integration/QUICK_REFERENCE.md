# Integration Tests Quick Reference

## Quick Start

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=qontinui_devtools.runtime --cov-report=html

# Run in parallel
pytest tests/integration/ -n auto
```

## Test Markers

```bash
pytest tests/integration/ -m integration    # All integration tests
pytest tests/integration/ -m e2e           # End-to-end tests
pytest tests/integration/ -m performance   # Performance tests
pytest tests/integration/ -m stress        # Stress tests only
pytest tests/integration/ -m concurrent    # Concurrency tests
```

## Run Specific Tests

```bash
# Specific file
pytest tests/integration/test_runtime_integration.py -v

# Specific class
pytest tests/integration/test_runtime_integration.py::TestProfilerEventTracerIntegration -v

# Specific test
pytest tests/integration/test_runtime_integration.py::TestProfilerEventTracerIntegration::test_profiler_and_tracer_together -v
```

## Test Files

| File | Tests | Purpose |
|------|-------|---------|
| `test_runtime_integration.py` | ~14 | Tool integration |
| `test_end_to_end.py` | ~11 | Full workflows |
| `test_performance.py` | ~16 | Performance/stress |
| `test_concurrent_tools.py` | ~14 | Concurrency |

## Performance Thresholds

```python
max_overhead_percent: 5.0      # Combined overhead
max_memory_mb: 100             # Peak memory usage
max_startup_time_ms: 100       # Tool initialization
max_event_latency_ms: 1        # Event tracing latency
```

## Key Test Classes

### Integration Tests
- `TestProfilerEventTracerIntegration` - Profiler + Tracer
- `TestMemoryProfilerIntegration` - Memory monitoring
- `TestDashboardIntegration` - Dashboard + all tools
- `TestAllToolsConcurrently` - All tools together

### End-to-End Tests
- `TestFullMonitoringWorkflow` - Complete workflows
- `TestCLIEndToEnd` - CLI commands
- `TestReportGeneration` - Report generation

### Performance Tests
- `TestProfilerPerformance` - Profiler overhead
- `TestEventTracerPerformance` - Event tracer overhead
- `TestMemoryProfilerPerformance` - Memory profiler overhead
- `TestStressTests` - High load testing
- `TestMemoryLeakDetection` - Memory leak detection

### Concurrency Tests
- `TestConcurrentToolAccess` - Thread safety
- `TestConcurrentToolLifecycle` - Init/shutdown
- `TestRaceConditions` - Race detection
- `TestAsyncConcurrency` - Async/await

## Fixtures

### Sample Data
- `sample_qontinui_action` - Action code file
- `sample_qontinui_project` - Project structure
- `sample_action_instance` - Action instance
- `memory_intensive_action` - Memory test action
- `concurrent_action` - Thread-safe action

### Configurations
- `profiler_config` - Profiler settings
- `event_tracer_config` - Event tracer settings
- `memory_profiler_config` - Memory profiler settings
- `dashboard_config` - Dashboard settings

### Utilities
- `performance_thresholds` - Performance limits
- `stress_test_config` - Stress test settings
- `overhead_measurer` - Overhead measurement

## Expected Results

### Performance
```
Profiler Overhead: ~2-3%
Event Tracer Overhead: ~1-2%
Combined Overhead: ~4-5%
Memory Usage: ~25-35MB
Event Latency: ~0.5ms average
```

### Coverage
```
Total Tests: 55+
Expected Pass Rate: 100%
Total Duration: 3-5 minutes
Coverage Target: >90%
```

## Common Commands

```bash
# Quick test run
pytest tests/integration/ -x  # Stop on first failure

# Verbose output
pytest tests/integration/ -vv -s

# Show slowest tests
pytest tests/integration/ --durations=10

# Run only failed tests
pytest tests/integration/ --lf

# Run with timeout
pytest tests/integration/ --timeout=300

# Generate JUnit XML
pytest tests/integration/ --junit-xml=test-results.xml
```

## Debugging Tests

```bash
# Drop into debugger on failure
pytest tests/integration/ --pdb

# Show local variables on failure
pytest tests/integration/ -l

# Capture output
pytest tests/integration/ -s --capture=no
```

## CI/CD Integration

```yaml
- name: Run Integration Tests
  run: |
    poetry run pytest tests/integration/ \
      -v \
      --cov=qontinui_devtools.runtime \
      --cov-report=xml \
      --junit-xml=test-results.xml
```

## Success Criteria Checklist

- [ ] All integration tests pass
- [ ] Performance overhead < 5%
- [ ] No memory leaks detected
- [ ] Thread-safe concurrent usage verified
- [ ] Clean error handling confirmed
- [ ] Reports generate correctly
- [ ] CLI commands work end-to-end

## Tool APIs (Quick Reference)

### ActionProfiler
```python
profiler = ActionProfiler(config)
profiler.start()
@profiler.profile
def my_function(): ...
profiler.stop()
data = profiler.get_profile_data()
profiler.export(path, format='json')
```

### EventTracer
```python
tracer = EventTracer(config)
tracer.start()
tracer.trace_event('event_type', {'data': 'value'})
events = tracer.get_events('event_type')
tracer.stop()
tracer.export(path, format='json')
```

### MemoryProfiler
```python
mem_profiler = MemoryProfiler(config)
mem_profiler.start()
# ... code execution ...
mem_profiler.stop()
usage = mem_profiler.get_memory_usage()
mem_profiler.export(path, format='json')
```

### PerformanceDashboard
```python
dashboard = PerformanceDashboard(config)
dashboard.start()
dashboard.update_metrics({'key': 'value'})
metrics = dashboard.get_metrics()
dashboard.stop()
```

## Troubleshooting

### Tests Timeout
```bash
pytest tests/integration/ --timeout=600
```

### Performance Tests Fail
- Close other applications
- Run tests in isolation
- Check system resources

### Concurrent Tests Flaky
- Run multiple times to verify
- Check thread synchronization
- Increase timeouts if needed

### Memory Tests Fail
```bash
# Force garbage collection
pytest tests/integration/ --forked
```

## Adding New Tests

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

## Contact

For issues with integration tests:
- Check test output for details
- Review README.md for detailed info
- Consult troubleshooting section
- Open issue with test output
