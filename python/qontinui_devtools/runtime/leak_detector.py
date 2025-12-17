"""Advanced leak detection utilities and reference chain analysis.

This module provides:
- Growth trend analysis using statistics
- Reference chain discovery
- Object retention analysis
- Leak classification
"""

import gc
import sys
from typing import Any


def analyze_growth_trend(
    samples: list[tuple[float, Any]], threshold: float = 0.01
) -> tuple[bool, float]:
    """Analyze if samples show growth trend using linear regression.

    Args:
        samples: List of (timestamp, value) tuples
        threshold: Minimum growth rate to consider as growing

    Returns:
        (is_growing, growth_rate) tuple
    """
    if len(samples) < 2:
        return False, 0.0

    # Extract times and values
    times = [s[0] for s in samples]
    values = [float(s[1]) for s in samples]

    # Normalize time to start at 0
    min_time = min(times)
    times = [t - min_time for t in times]

    # Simple linear regression: y = mx + b
    n = len(samples)
    sum_x = sum(times)
    sum_y = sum(values)
    sum_xy = sum(t * v for t, v in zip(times, values, strict=False))
    sum_xx = sum(t * t for t in times)

    # Calculate slope (growth rate)
    denominator = n * sum_xx - sum_x * sum_x
    if denominator == 0:
        return False, 0.0

    slope = (n * sum_xy - sum_x * sum_y) / denominator

    # Determine if growing
    is_growing = slope > threshold

    return is_growing, slope


def find_reference_chains(obj: Any, max_depth: int = 5, max_chains: int = 10) -> list[list[str]]:
    """Find reference chains keeping an object alive.

    Uses gc.get_referrers() to trace back what's holding references.

    Args:
        obj: Object to analyze
        max_depth: Maximum depth to traverse
        max_chains: Maximum number of chains to return

    Returns:
        List of reference chains (each chain is a list of type names)
    """
    chains: list[list[str]] = []
    visited = set()

    def _trace_referrers(current_obj: Any, current_chain: list[str], depth: int) -> None:
        """Recursively trace referrers."""
        if depth >= max_depth or len(chains) >= max_chains:
            return

        obj_id = id(current_obj)
        if obj_id in visited:
            return

        visited.add(obj_id)

        try:
            referrers = gc.get_referrers(current_obj)
        except Exception:
            return

        for referrer in referrers:
            # Skip frame objects and module dicts
            if isinstance(referrer, type(sys._getframe())):
                continue

            ref_type = type(referrer).__name__

            # Skip this module's locals
            if isinstance(referrer, dict) and "__name__" in referrer:
                continue

            new_chain = current_chain + [ref_type]

            # If we found a significant referrer, record the chain
            if ref_type in ("module", "type", "function", "method"):
                chains.append(new_chain)
                if len(chains) >= max_chains:
                    return

            # Continue tracing
            _trace_referrers(referrer, new_chain, depth + 1)

    _trace_referrers(obj, [type(obj).__name__], 0)

    return chains


def find_leaked_objects(baseline_objects: set[int], current_objects: list[Any]) -> list[Any]:
    """Find objects that were created after baseline.

    Args:
        baseline_objects: Set of object IDs from baseline
        current_objects: List of current objects

    Returns:
        List of new objects not in baseline
    """
    leaked: list[Any] = []
    for obj in current_objects:
        if id(obj) not in baseline_objects:
            leaked.append(obj)
    return leaked


def classify_leak_severity(count_increase: int, size_mb: float, growth_rate: float) -> str:
    """Classify leak severity based on metrics.

    Args:
        count_increase: Number of objects leaked
        size_mb: Memory size in MB
        growth_rate: Growth rate (objects/sec)

    Returns:
        Severity level: "critical", "high", "medium", "low"
    """
    # Critical: Large memory impact or very fast growth
    if size_mb > 100 or growth_rate > 1000:
        return "critical"

    # High: Significant memory or fast growth
    if size_mb > 10 or growth_rate > 100:
        return "high"

    # Medium: Moderate impact
    if size_mb > 1 or growth_rate > 10:
        return "medium"

    # Low: Minor impact
    return "low"


def analyze_object_retention(obj: Any) -> dict[str, Any]:
    """Analyze why an object is being retained in memory.

    Args:
        obj: Object to analyze

    Returns:
        Dictionary with retention analysis
    """
    analysis = {
        "type": type(obj).__name__,
        "size": sys.getsizeof(obj),
        "referrer_count": len(gc.get_referrers(obj)),
        "is_tracked": gc.is_tracked(obj),
        "referent_count": len(gc.get_referents(obj)) if hasattr(gc, "get_referents") else 0,
    }

    # Analyze referrers
    try:
        referrers = gc.get_referrers(obj)
        referrer_types: dict[str, int] = {}
        for ref in referrers:
            ref_type = type(ref).__name__
            referrer_types[ref_type] = referrer_types.get(ref_type, 0) + 1

        analysis["referrer_types"] = referrer_types
    except Exception as e:
        analysis["referrer_types"] = {"error": str(e)}

    return analysis


def find_cycles_containing(obj: Any) -> list[list[Any]]:
    """Find reference cycles containing the given object.

    Args:
        obj: Object to check for cycles

    Returns:
        List of cycles (each cycle is a list of objects)
    """
    cycles: list[list[Any]] = []
    visited = set()
    path: list[Any] = []

    def _dfs(current: Any) -> None:
        """Depth-first search for cycles."""
        current_id = id(current)

        if current_id in visited:
            # Found a cycle
            if current in path:
                cycle_start = path.index(current)
                cycle = path[cycle_start:]
                if len(cycle) > 1:  # Ignore self-references
                    cycles.append(cycle[:])
            return

        visited.add(current_id)
        path.append(current)

        try:
            referents = gc.get_referents(current)
            for referent in referents:
                # Skip frames and common containers
                if isinstance(referent, type(sys._getframe()) | type | type(gc)):
                    continue
                _dfs(referent)
        except Exception:
            pass

        path.pop()

    _dfs(obj)

    return cycles


def get_object_size_deep(obj: Any, seen: set[int] | None = None) -> int:
    """Calculate deep size of an object including referenced objects.

    Args:
        obj: Object to measure
        seen: Set of already seen object IDs (for recursion)

    Returns:
        Total size in bytes
    """
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return 0

    seen.add(obj_id)
    size = sys.getsizeof(obj)

    # Recursively measure referenced objects
    if isinstance(obj, dict):
        size += sum(
            get_object_size_deep(k, seen) + get_object_size_deep(v, seen) for k, v in obj.items()
        )
    elif isinstance(obj, list | tuple | set | frozenset):
        size += sum(get_object_size_deep(item, seen) for item in obj)
    elif hasattr(obj, "__dict__"):
        size += get_object_size_deep(obj.__dict__, seen)
    elif hasattr(obj, "__slots__"):
        size += sum(
            get_object_size_deep(getattr(obj, slot, None), seen)
            for slot in obj.__slots__
            if hasattr(obj, slot)
        )

    return size


def detect_common_leak_patterns(objects_by_type: dict[str, int]) -> list[str]:
    """Detect common memory leak patterns.

    Args:
        objects_by_type: Dictionary of object counts by type

    Returns:
        List of detected patterns with descriptions
    """
    patterns: list[Any] = []

    # Pattern 1: Excessive list/dict growth
    if objects_by_type.get("list", 0) > 10000:
        patterns.append("Excessive list objects (possible unbounded cache or accumulator)")

    if objects_by_type.get("dict", 0) > 5000:
        patterns.append("Excessive dict objects (possible unbounded cache or mapping)")

    # Pattern 2: Frame leaks
    if objects_by_type.get("frame", 0) > 100:
        patterns.append("Excessive frame objects (possible exception or generator leak)")

    # Pattern 3: Closure/function leaks
    if objects_by_type.get("function", 0) > 1000:
        patterns.append("Excessive function objects (possible closure or decorator leak)")

    # Pattern 4: String accumulation
    if objects_by_type.get("str", 0) > 50000:
        patterns.append("Excessive string objects (possible string accumulation)")

    # Pattern 5: Weak reference issues
    if objects_by_type.get("weakref", 0) > 1000:
        patterns.append("Excessive weak references (possible cleanup issue)")

    # Pattern 6: Thread-related leaks
    if objects_by_type.get("Thread", 0) > 50:
        patterns.append("Excessive Thread objects (possible thread leak)")

    # Pattern 7: File handle leaks
    if objects_by_type.get("TextIOWrapper", 0) > 100:
        patterns.append("Excessive file handles (possible file descriptor leak)")

    return patterns


def suggest_fixes(leak_type: str, pattern: str | None = None) -> list[str]:
    """Suggest fixes for common leak patterns.

    Args:
        leak_type: Type of object leaking
        pattern: Detected pattern if any

    Returns:
        List of suggested fixes
    """
    suggestions: list[Any] = []

    # Type-specific suggestions
    if leak_type == "dict":
        suggestions.append("Consider using weakref.WeakValueDictionary for caches")
        suggestions.append("Implement cache size limits with LRU eviction")
        suggestions.append("Ensure dict.clear() is called when data is no longer needed")

    elif leak_type == "list":
        suggestions.append("Implement bounded collections with size limits")
        suggestions.append("Use deque with maxlen for sliding window operations")
        suggestions.append("Clear lists when done: list.clear()")

    elif leak_type == "frame":
        suggestions.append("Ensure generators are properly closed")
        suggestions.append("Check for exception handling that retains frames")
        suggestions.append("Use context managers to ensure cleanup")

    elif leak_type == "function":
        suggestions.append("Avoid creating functions in loops")
        suggestions.append("Check for circular references in closures")
        suggestions.append("Use functools.lru_cache with maxsize")

    elif leak_type == "Thread":
        suggestions.append("Ensure threads are joined properly")
        suggestions.append("Use daemon threads for background tasks")
        suggestions.append("Implement thread pooling with fixed size")

    elif leak_type == "TextIOWrapper":
        suggestions.append("Always use 'with' statements for file operations")
        suggestions.append("Explicitly close files when done")
        suggestions.append("Check for exception handling that skips cleanup")

    # Pattern-specific suggestions
    if pattern and "cache" in pattern.lower():
        suggestions.append("Implement cache eviction policy (LRU, TTL, size-based)")
        suggestions.append("Use functools.lru_cache instead of manual caching")

    if pattern and "thread" in pattern.lower():
        suggestions.append("Use concurrent.futures.ThreadPoolExecutor")
        suggestions.append("Implement proper thread lifecycle management")

    return suggestions
