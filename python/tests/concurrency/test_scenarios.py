"""Tests for pre-built race condition scenarios."""

from qontinui_devtools.concurrency.scenarios import (
    run_all_scenarios,
    test_check_then_act,
    test_check_then_act_safe,
    test_counter_increment,
    test_counter_increment_safe,
    test_dictionary_concurrent_access,
    test_lazy_initialization,
    test_lazy_initialization_safe,
    test_list_append,
)


def test_dictionary_concurrent_access_scenario():
    """Test dictionary concurrent access scenario."""
    result = test_dictionary_concurrent_access(threads=5, iterations=5)

    assert result.test_name == "worker"
    assert result.total_iterations == 25


def test_check_then_act_scenario():
    """Test check-then-act scenario."""
    result = test_check_then_act(threads=5, iterations=10)

    assert result.test_name == "worker"
    assert result.total_iterations == 50
    # Pattern is inherently racy, but may not always fail due to GIL


def test_check_then_act_safe_scenario():
    """Test thread-safe check-then-act scenario."""
    result = test_check_then_act_safe(threads=5, iterations=10)

    assert result.test_name == "worker"
    assert result.total_iterations == 50
    assert result.failed == 0
    assert not result.race_detected


def test_counter_increment_scenario():
    """Test counter increment scenario."""
    result = test_counter_increment(threads=5, iterations=5)

    assert result.test_name == "worker"
    assert result.total_iterations == 25
    # May detect race through counter mismatch


def test_counter_increment_safe_scenario():
    """Test thread-safe counter increment scenario."""
    result = test_counter_increment_safe(threads=5, iterations=5)

    assert result.test_name == "worker"
    assert result.total_iterations == 25
    assert result.failed == 0
    # Counter should be exactly correct


def test_lazy_initialization_scenario():
    """Test lazy initialization scenario."""
    result = test_lazy_initialization(threads=10, iterations=10)

    assert result.test_name == "worker"
    assert result.total_iterations == 100
    # May detect multiple initializations


def test_lazy_initialization_safe_scenario():
    """Test thread-safe lazy initialization scenario."""
    result = test_lazy_initialization_safe(threads=10, iterations=10)

    assert result.test_name == "worker"
    assert result.total_iterations == 100
    assert result.failed == 0
    # Should initialize exactly once


def test_list_append_scenario():
    """Test list append scenario."""
    result = test_list_append(threads=5, iterations=5)

    assert result.test_name == "worker"
    assert result.total_iterations == 25


def test_run_all_scenarios_function():
    """Test running all scenarios at once."""
    results = run_all_scenarios()

    assert isinstance(results, dict)
    assert len(results) > 0

    # Check that expected scenarios are present
    expected_scenarios = [
        "dictionary_access",
        "check_then_act",
        "check_then_act_safe",
        "counter_increment",
        "counter_increment_safe",
        "lazy_initialization",
        "lazy_initialization_safe",
        "list_append",
    ]

    for scenario in expected_scenarios:
        assert scenario in results
        assert results[scenario].total_iterations > 0


def test_counter_with_custom_expected():
    """Test counter scenario with custom expected value."""
    threads = 3
    iterations = 4
    expected = threads * iterations * 100

    result = test_counter_increment_safe(
        threads=threads, iterations=iterations, expected_total=expected
    )

    assert result.total_iterations == threads * iterations
    assert result.failed == 0


def test_scenarios_complete_successfully():
    """Test that all safe scenarios complete without failures."""
    safe_scenarios = [
        test_check_then_act_safe,
        test_counter_increment_safe,
        test_lazy_initialization_safe,
    ]

    for scenario_func in safe_scenarios:
        result = scenario_func(threads=5, iterations=10)
        assert result.failed == 0, f"{scenario_func.__name__} had failures"
        assert not result.race_detected, f"{scenario_func.__name__} detected race"
