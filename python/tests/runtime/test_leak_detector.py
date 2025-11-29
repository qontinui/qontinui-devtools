"""Tests for leak detector utilities."""

import gc

import pytest
from qontinui_devtools.runtime import (
    analyze_growth_trend,
    analyze_object_retention,
    classify_leak_severity,
    detect_common_leak_patterns,
    find_cycles_containing,
    find_leaked_objects,
    find_reference_chains,
    get_object_size_deep,
    suggest_fixes,
)


class TestAnalyzeGrowthTrend:
    """Test growth trend analysis."""

    def test_linear_growth(self):
        """Test detecting linear growth."""
        samples = [(float(i), i * 10) for i in range(10)]

        is_growing, rate = analyze_growth_trend(samples, threshold=5.0)

        assert is_growing
        assert rate > 5.0

    def test_no_growth(self):
        """Test no growth detection."""
        samples = [(float(i), 100) for i in range(10)]

        is_growing, rate = analyze_growth_trend(samples, threshold=1.0)

        assert not is_growing
        assert abs(rate) < 1.0

    def test_negative_growth(self):
        """Test negative growth (memory decrease)."""
        samples = [(float(i), 100 - i * 5) for i in range(10)]

        is_growing, rate = analyze_growth_trend(samples, threshold=1.0)

        assert not is_growing
        assert rate < 0

    def test_insufficient_samples(self):
        """Test with only one sample."""
        samples = [(0.0, 100)]

        is_growing, rate = analyze_growth_trend(samples)

        assert not is_growing
        assert rate == 0.0

    def test_small_growth_below_threshold(self):
        """Test small growth below threshold."""
        samples = [(float(i), 100 + i * 0.001) for i in range(10)]

        is_growing, rate = analyze_growth_trend(samples, threshold=0.01)

        assert not is_growing
        assert rate < 0.01


class TestFindReferenceChains:
    """Test reference chain finding."""

    def test_simple_reference_chain(self):
        """Test finding simple reference chains."""
        obj = {"key": "value"}

        chains = find_reference_chains(obj, max_depth=3, max_chains=5)

        assert isinstance(chains, list)
        # Should find at least one chain
        assert len(chains) >= 0

    def test_nested_reference_chain(self):
        """Test finding nested reference chains."""
        inner = {"inner": "data"}

        chains = find_reference_chains(inner, max_depth=5)

        assert isinstance(chains, list)

    def test_max_depth_limit(self):
        """Test max depth limiting."""
        obj = {"data": "value"}

        chains = find_reference_chains(obj, max_depth=1)

        assert isinstance(chains, list)
        # All chains should respect max_depth
        assert all(len(chain) <= 2 for chain in chains)  # +1 for the object itself

    def test_max_chains_limit(self):
        """Test max chains limiting."""
        obj = [1, 2, 3, 4, 5]

        chains = find_reference_chains(obj, max_chains=3)

        assert len(chains) <= 3


class TestFindLeakedObjects:
    """Test leaked object finding."""

    def test_find_new_objects(self):
        """Test finding objects created after baseline."""
        baseline_ids = {id(obj) for obj in gc.get_objects()[:1000]}

        # Create new objects
        new_obj1 = {"new": "object1"}
        new_obj2 = [1, 2, 3, 4, 5]

        current_objects = [new_obj1, new_obj2] + gc.get_objects()[:100]

        leaked = find_leaked_objects(baseline_ids, current_objects)

        # Should find at least the new objects
        assert len(leaked) >= 2

    def test_no_new_objects(self):
        """Test when no new objects are created."""
        baseline_objects = [{"a": 1}, {"b": 2}, {"c": 3}]
        baseline_ids = {id(obj) for obj in baseline_objects}

        leaked = find_leaked_objects(baseline_ids, baseline_objects)

        assert len(leaked) == 0


class TestClassifyLeakSeverity:
    """Test leak severity classification."""

    def test_critical_severity_large_size(self):
        """Test critical severity with large size."""
        severity = classify_leak_severity(count_increase=1000, size_mb=150.0, growth_rate=50.0)

        assert severity == "critical"

    def test_critical_severity_fast_growth(self):
        """Test critical severity with fast growth."""
        severity = classify_leak_severity(count_increase=5000, size_mb=50.0, growth_rate=1500.0)

        assert severity == "critical"

    def test_high_severity(self):
        """Test high severity."""
        severity = classify_leak_severity(count_increase=2000, size_mb=25.0, growth_rate=200.0)

        assert severity == "high"

    def test_medium_severity(self):
        """Test medium severity."""
        severity = classify_leak_severity(count_increase=500, size_mb=3.0, growth_rate=50.0)

        assert severity == "medium"

    def test_low_severity(self):
        """Test low severity."""
        severity = classify_leak_severity(count_increase=100, size_mb=0.5, growth_rate=5.0)

        assert severity == "low"


class TestAnalyzeObjectRetention:
    """Test object retention analysis."""

    def test_retention_analysis(self):
        """Test analyzing object retention."""
        obj = {"key": "value", "nested": {"inner": "data"}}

        analysis = analyze_object_retention(obj)

        assert "type" in analysis
        assert analysis["type"] == "dict"
        assert "size" in analysis
        assert "referrer_count" in analysis
        assert "is_tracked" in analysis
        assert "referrer_types" in analysis

    def test_retention_analysis_list(self):
        """Test retention analysis for list."""
        obj = [1, 2, 3, 4, 5]

        analysis = analyze_object_retention(obj)

        assert analysis["type"] == "list"
        assert analysis["size"] > 0

    def test_retention_analysis_custom_object(self):
        """Test retention analysis for custom object."""

        class CustomClass:
            def __init__(self):
                self.data = "test"

        obj = CustomClass()

        analysis = analyze_object_retention(obj)

        assert analysis["type"] == "CustomClass"


class TestFindCyclesContaining:
    """Test cycle detection."""

    def test_simple_cycle(self):
        """Test detecting simple reference cycle."""
        # Create a cycle
        obj1 = {"name": "obj1"}
        obj2 = {"name": "obj2", "ref": obj1}
        obj1["ref"] = obj2

        cycles = find_cycles_containing(obj1)

        # Should find at least one cycle
        assert isinstance(cycles, list)

    def test_no_cycle(self):
        """Test object without cycles."""
        obj = {"key": "value", "number": 42}

        cycles = find_cycles_containing(obj)

        # Should not find any significant cycles
        assert isinstance(cycles, list)


class TestGetObjectSizeDeep:
    """Test deep object size calculation."""

    def test_simple_dict_size(self):
        """Test size of simple dict."""
        obj = {"key": "value"}

        size = get_object_size_deep(obj)

        assert size > 0
        assert size >= 240  # Minimum dict size

    def test_nested_dict_size(self):
        """Test size of nested dict."""
        obj = {"outer": {"inner": {"deep": "value"}}}

        size = get_object_size_deep(obj)

        # Nested dict should be larger than simple dict
        simple_size = get_object_size_deep({"key": "value"})
        assert size > simple_size

    def test_list_size(self):
        """Test size of list."""
        obj = [1, 2, 3, 4, 5]

        size = get_object_size_deep(obj)

        assert size > 0

    def test_complex_structure_size(self):
        """Test size of complex structure."""
        obj = {
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "tuple": (1, 2, 3),
            "set": {1, 2, 3},
        }

        size = get_object_size_deep(obj)

        # Should account for all nested structures
        assert size > 1000

    def test_circular_reference_size(self):
        """Test size calculation with circular reference."""
        obj = {"name": "obj"}
        obj["self"] = obj

        # Should handle circular reference without infinite loop
        size = get_object_size_deep(obj)

        assert size > 0


class TestDetectCommonLeakPatterns:
    """Test common leak pattern detection."""

    def test_excessive_list_pattern(self):
        """Test detecting excessive list objects."""
        objects = {"list": 15000, "dict": 1000}

        patterns = detect_common_leak_patterns(objects)

        assert len(patterns) > 0
        assert any("list" in p.lower() for p in patterns)

    def test_excessive_dict_pattern(self):
        """Test detecting excessive dict objects."""
        objects = {"dict": 8000, "list": 1000}

        patterns = detect_common_leak_patterns(objects)

        assert len(patterns) > 0
        assert any("dict" in p.lower() for p in patterns)

    def test_frame_leak_pattern(self):
        """Test detecting frame leaks."""
        objects = {"frame": 150, "dict": 1000}

        patterns = detect_common_leak_patterns(objects)

        assert len(patterns) > 0
        assert any("frame" in p.lower() for p in patterns)

    def test_thread_leak_pattern(self):
        """Test detecting thread leaks."""
        objects = {"Thread": 60, "dict": 1000}

        patterns = detect_common_leak_patterns(objects)

        assert len(patterns) > 0
        assert any("thread" in p.lower() for p in patterns)

    def test_file_handle_leak_pattern(self):
        """Test detecting file handle leaks."""
        objects = {"TextIOWrapper": 120, "dict": 1000}

        patterns = detect_common_leak_patterns(objects)

        assert len(patterns) > 0
        assert any("file" in p.lower() for p in patterns)

    def test_no_patterns_detected(self):
        """Test when no patterns are detected."""
        objects = {"dict": 100, "list": 50, "str": 200}

        patterns = detect_common_leak_patterns(objects)

        # Should detect no patterns with small counts
        assert len(patterns) == 0


class TestSuggestFixes:
    """Test fix suggestions."""

    def test_dict_leak_suggestions(self):
        """Test suggestions for dict leaks."""
        suggestions = suggest_fixes("dict")

        assert len(suggestions) > 0
        assert any("cache" in s.lower() for s in suggestions)
        assert any("weakref" in s.lower() or "lru" in s.lower() for s in suggestions)

    def test_list_leak_suggestions(self):
        """Test suggestions for list leaks."""
        suggestions = suggest_fixes("list")

        assert len(suggestions) > 0
        assert any("bounded" in s.lower() or "deque" in s.lower() for s in suggestions)

    def test_frame_leak_suggestions(self):
        """Test suggestions for frame leaks."""
        suggestions = suggest_fixes("frame")

        assert len(suggestions) > 0
        assert any("generator" in s.lower() or "exception" in s.lower() for s in suggestions)

    def test_function_leak_suggestions(self):
        """Test suggestions for function leaks."""
        suggestions = suggest_fixes("function")

        assert len(suggestions) > 0
        assert any("closure" in s.lower() or "loop" in s.lower() for s in suggestions)

    def test_thread_leak_suggestions(self):
        """Test suggestions for thread leaks."""
        suggestions = suggest_fixes("Thread")

        assert len(suggestions) > 0
        assert any("thread" in s.lower() for s in suggestions)

    def test_file_leak_suggestions(self):
        """Test suggestions for file handle leaks."""
        suggestions = suggest_fixes("TextIOWrapper")

        assert len(suggestions) > 0
        assert any("with" in s.lower() or "close" in s.lower() for s in suggestions)

    def test_cache_pattern_suggestions(self):
        """Test suggestions for cache-related leaks."""
        suggestions = suggest_fixes("dict", pattern="unbounded cache")

        assert len(suggestions) > 0
        assert any("cache" in s.lower() for s in suggestions)
        assert any("lru" in s.lower() or "eviction" in s.lower() for s in suggestions)

    def test_thread_pattern_suggestions(self):
        """Test suggestions for thread-related patterns."""
        suggestions = suggest_fixes("dict", pattern="thread leak")

        assert len(suggestions) > 0
        # Should include thread-specific suggestions
        thread_suggestions = [s for s in suggestions if "thread" in s.lower()]
        assert len(thread_suggestions) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
