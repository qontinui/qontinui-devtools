"""Heuristic analysis to reduce false positives in race condition detection."""


from .ast_analyzer import AnalysisContext, LockInfo, StateAccess


def is_likely_thread_safe(
    state_name: str,
    state_type: str,
    type_annotation: str,
    context: AnalysisContext,
) -> bool:
    """Heuristic to determine if state is thread-safe."""

    # NOTE: We do NOT check if the VALUE TYPE is immutable (int, str, etc.)
    # because even immutable values can have race conditions when the
    # VARIABLE is reassigned: e.g., _count = 0; _count += 1

    # Check for thread-local storage
    if _is_thread_local(state_name, type_annotation):
        return True

    # Check for constants (uppercase names with underscores)
    if _is_likely_constant(state_name):
        return True

    # Check for protected state (has associated lock)
    if _has_associated_lock(state_name, context):
        return True

    # Check for queue-based communication (thread-safe)
    if _is_queue_type(type_annotation):
        return True

    # Check for atomic types
    if _is_atomic_type(type_annotation):
        return True

    return False


def _is_immutable_type(type_annotation: str) -> bool:
    """Check if type is immutable."""
    immutable_types = {
        "int",
        "float",
        "str",
        "bool",
        "bytes",
        "tuple",
        "frozenset",
        "NoneType",
        "type",
        "complex",
        "range",
        "slice",
    }
    return type_annotation in immutable_types


def _is_thread_local(name: str, type_annotation: str) -> bool:
    """Check if variable uses thread-local storage."""
    if "threading.local" in type_annotation or "local()" in type_annotation:
        return True
    if "_local" in name.lower() or "thread_local" in name.lower():
        return True
    return False


def _is_likely_constant(name: str) -> bool:
    """Check if name suggests a constant."""
    # All uppercase (e.g., MAX_SIZE, API_KEY)
    if name.isupper() and "_" in name:
        return True
    # Starts with multiple capitals (e.g., APIKey, HTTPConnection)
    if len(name) > 1 and name[0].isupper() and name[1].isupper():
        return True
    return False


def _has_associated_lock(state_name: str, context: AnalysisContext) -> bool:
    """Check if state has an associated lock nearby in code."""
    # Look for locks with similar names
    state_base = state_name.lstrip("_")
    for lock in context.locks:
        lock_base = lock.name.lstrip("_")
        # Check for naming patterns like: _cache/_cache_lock, data/data_lock
        if (
            state_base in lock_base
            or lock_base in state_base
            or state_base.replace("_", "") in lock_base.replace("_", "")
        ):
            return True

    return False


def _is_queue_type(type_annotation: str) -> bool:
    """Check if type is a thread-safe queue."""
    queue_types = {
        "Queue",
        "LifoQueue",
        "PriorityQueue",
        "SimpleQueue",
        "queue.Queue",
        "queue.LifoQueue",
        "queue.PriorityQueue",
    }
    return type_annotation in queue_types


def _is_atomic_type(type_annotation: str) -> bool:
    """Check if type provides atomic operations."""
    atomic_types = {
        "Value",
        "Array",
        "RawValue",
        "RawArray",  # multiprocessing
        "Atomic",
        "AtomicInt",
        "AtomicLong",  # If using atomic libraries
    }
    return type_annotation in atomic_types


def calculate_severity(
    state_name: str,
    state_type: str,
    accesses: list[StateAccess],
    locks: list[LockInfo],
) -> str:
    """
    Calculate severity based on access patterns.

    Returns: "critical", "high", "medium", or "low"
    """
    if not accesses:
        return "low"

    # Count different access patterns
    unprotected_writes = 0
    unprotected_reads = 0
    protected_writes = 0
    protected_reads = 0

    for access in accesses:
        if access.in_lock_context:
            if "write" in access.access_type:
                protected_writes += 1
            else:
                protected_reads += 1
        else:
            if "write" in access.access_type:
                unprotected_writes += 1
            else:
                unprotected_reads += 1

    # Critical: Multiple unprotected writes (write-write race)
    if unprotected_writes >= 2:
        return "critical"

    # Critical: Unprotected write with any reads
    if unprotected_writes >= 1 and (unprotected_reads + protected_reads) >= 1:
        return "critical"

    # High: Single unprotected write
    if unprotected_writes >= 1:
        return "high"

    # Medium: Multiple unprotected reads with protected writes
    if unprotected_reads >= 2 and protected_writes >= 1:
        return "medium"

    # Low: Mostly protected or read-only
    return "low"


def is_check_then_act_pattern(accesses: list[StateAccess]) -> bool:
    """
    Detect check-then-act race condition pattern.

    Example:
        if key not in cache:  # Check
            cache[key] = value  # Act
    """
    # Look for read followed by write without lock
    for i, access in enumerate(accesses[:-1]):
        next_access = accesses[i + 1]
        if (
            access.access_type == "read"
            and next_access.access_type in ("write", "read_write")
            and not access.in_lock_context
            and not next_access.in_lock_context
            # Within a few lines of each other
            and abs(next_access.line_number - access.line_number) <= 5
        ):
            return True
    return False


def is_double_checked_locking(accesses: list[StateAccess]) -> bool:
    """
    Detect double-checked locking pattern (which can be broken in Python).

    Example:
        if obj is None:  # First check (unprotected)
            with lock:
                if obj is None:  # Second check (protected)
                    obj = create()
    """
    # Look for: unprotected read -> protected read -> protected write
    for i in range(len(accesses) - 2):
        if (
            accesses[i].access_type == "read"
            and not accesses[i].in_lock_context
            and accesses[i + 1].access_type == "read"
            and accesses[i + 1].in_lock_context
            and accesses[i + 2].access_type == "write"
            and accesses[i + 2].in_lock_context
        ):
            return True
    return False


def analyze_lock_granularity(accesses: list[StateAccess]) -> str:
    """
    Analyze if lock granularity is appropriate.

    Returns: "too_coarse", "too_fine", or "appropriate"
    """
    if not accesses:
        return "appropriate"

    protected = sum(1 for a in accesses if a.in_lock_context)
    len(accesses) - protected

    # If nothing is protected, granularity doesn't matter
    if protected == 0:
        return "appropriate"

    # If only some accesses are protected, likely too fine (or missing protection)
    if 0 < protected < len(accesses):
        return "too_fine"

    # All accesses protected - check if they use different locks
    lock_names = {a.lock_name for a in accesses if a.lock_name}
    if len(lock_names) > 1:
        return "too_fine"

    return "appropriate"


def suggest_fix(
    state_name: str,
    state_type: str,
    severity: str,
    accesses: list[StateAccess],
    context: AnalysisContext,
) -> str:
    """Generate a suggestion for fixing the race condition."""

    # Check for existing locks
    has_locks = len(context.locks) > 0

    suggestions = []

    # Critical issues need immediate fixes
    if severity == "critical":
        if is_check_then_act_pattern(accesses):
            suggestions.append(
                f"Protect check-then-act pattern on '{state_name}' with a lock. "
                "The check and act operations must be atomic."
            )
        else:
            suggestions.append(
                f"Add lock protection around all accesses to '{state_name}'. "
                "Multiple threads are writing to this state simultaneously."
            )

        if not has_locks:
            suggestions.append(
                "Add a lock: self._lock = threading.Lock() in __init__, "
                "then use 'with self._lock:' around state access."
            )
        else:
            lock_names = [lock.name for lock in context.locks]
            suggestions.append(
                f"Use existing lock ({lock_names[0]}) or create a dedicated lock for '{state_name}'."
            )

    # High severity
    elif severity == "high":
        suggestions.append(
            f"Add lock protection for writes to '{state_name}'. "
            "Even a single unprotected write can cause data corruption."
        )

    # Medium severity
    elif severity == "medium":
        suggestions.append(
            f"Consider using a thread-safe data structure for '{state_name}' "
            "(e.g., queue.Queue) or add read locks."
        )

    # Check for alternatives
    if state_type == "dict":
        suggestions.append(
            "Alternative: Use threading.local() for thread-local storage, "
            "or consider using a concurrent data structure."
        )
    elif state_type == "list":
        suggestions.append("Alternative: Use queue.Queue for thread-safe list operations.")

    # Check for double-checked locking
    if is_double_checked_locking(accesses):
        suggestions.append(
            "WARNING: Double-checked locking detected. This pattern can be "
            "broken in Python. Use a single lock acquisition."
        )

    return " ".join(suggestions) if suggestions else "Add appropriate locking mechanism."


def get_false_positive_indicators(
    state_name: str,
    state_type: str,
    context: AnalysisContext,
) -> list[str]:
    """
    Get indicators that this might be a false positive.

    Returns list of reasons why this might not be a real race condition.
    """
    indicators = []

    # Check for single-threaded context clues
    if _looks_single_threaded(context):
        indicators.append("No threading imports or Thread creation found")

    # Check for test files
    if "test" in context.file_path.lower():
        indicators.append("File appears to be a test file")

    # Check for internal/private conventions
    if state_name.startswith("__"):
        indicators.append("Name uses Python private convention (__name)")

    # Check for documentation suggesting single-threaded
    # (Would need to parse docstrings - simplified here)

    # Check if state is only accessed in __init__
    init_only = all(
        "init" in context.current_function.lower() if context.current_function else False
        for _ in [1]  # Simplified check
    )
    if init_only:
        indicators.append("State appears to only be accessed during initialization")

    return indicators


def _looks_single_threaded(context: AnalysisContext) -> bool:
    """Check if code appears to be single-threaded."""
    # If no Thread creation or threading imports found
    has_threading = any("threading" in str(state) for state in context.shared_states)
    has_thread_class = any("Thread" in str(state) for state in context.shared_states)
    return not (has_threading or has_thread_class or context.locks)


def prioritize_issues(
    races: list[tuple[str, str, list[StateAccess]]]
) -> list[tuple[str, str, list[StateAccess]]]:
    """
    Prioritize race conditions by severity and likelihood.

    Returns sorted list with most important issues first.
    """
    scored_races = []

    for state_name, state_type, accesses in races:
        score = 0

        # More accesses = higher priority
        score += len(accesses) * 10

        # Unprotected writes are critical
        unprotected_writes = sum(
            1 for a in accesses if "write" in a.access_type and not a.in_lock_context
        )
        score += unprotected_writes * 100

        # Check-then-act pattern is high priority
        if is_check_then_act_pattern(accesses):
            score += 200

        scored_races.append((score, state_name, state_type, accesses))

    # Sort by score (descending)
    scored_races.sort(reverse=True, key=lambda x: x[0])

    return [(name, type_, accesses) for _, name, type_, accesses in scored_races]
