"""Instrumentation for detecting race conditions at runtime.

This module provides tools to track access to shared state and detect
concurrent read-write or write-write conflicts that indicate race conditions.
"""

import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class Access:
    """Record of accessing shared state."""

    thread_id: int
    timestamp: float
    access_type: str  # "read" or "write"
    location: str = ""  # Optional: where in code

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Access(thread={self.thread_id}, "
            f"type={self.access_type}, "
            f"time={self.timestamp:.6f})"
        )


@dataclass
class RaceConflict:
    """Detected race conflict between two accesses."""

    obj_id: int
    access_1: Access
    access_2: Access
    conflict_type: str  # "read-write", "write-write"
    time_difference: float  # Time between accesses in seconds

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"RaceConflict(obj={self.obj_id}, "
            f"type={self.conflict_type}, "
            f"threads=[{self.access_1.thread_id}, {self.access_2.thread_id}], "
            f"time_diff={self.time_difference*1000:.2f}ms)"
        )


class SharedStateTracker:
    """Track access to shared state to detect races.

    This class records all reads and writes to shared objects and analyzes
    them to find concurrent access patterns that indicate race conditions.

    Example:
        tracker = SharedStateTracker()

        # Record accesses
        tracker.record_read(id(obj), threading.get_ident(), time.time())
        tracker.record_write(id(obj), threading.get_ident(), time.time())

        # Detect conflicts
        conflicts = tracker.detect_conflicts()
        for conflict in conflicts:
            print(f"Race detected: {conflict}")
    """

    def __init__(self, conflict_window: float = 0.001) -> None:
        """Initialize tracker.

        Args:
            conflict_window: Time window in seconds to consider accesses
                as concurrent (default 1ms)
        """
        self._accesses: dict[int, list[Access]] = {}
        self._lock = threading.Lock()
        self._conflict_window = conflict_window

    def record_read(
        self,
        obj_id: int,
        thread_id: int | None = None,
        timestamp: float | None = None,
        location: str = ""
    ) -> None:
        """Record a read access to shared state.

        Args:
            obj_id: ID of the object being accessed
            thread_id: Thread ID (defaults to current thread)
            timestamp: Access timestamp (defaults to current time)
            location: Optional location in code
        """
        if thread_id is None:
            thread_id = threading.get_ident()
        if timestamp is None:
            timestamp = time.time()

        access = Access(
            thread_id=thread_id,
            timestamp=timestamp,
            access_type="read",
            location=location
        )

        with self._lock:
            if obj_id not in self._accesses:
                self._accesses[obj_id] = []
            self._accesses[obj_id].append(access)

    def record_write(
        self,
        obj_id: int,
        thread_id: int | None = None,
        timestamp: float | None = None,
        location: str = ""
    ) -> None:
        """Record a write access to shared state.

        Args:
            obj_id: ID of the object being accessed
            thread_id: Thread ID (defaults to current thread)
            timestamp: Access timestamp (defaults to current time)
            location: Optional location in code
        """
        if thread_id is None:
            thread_id = threading.get_ident()
        if timestamp is None:
            timestamp = time.time()

        access = Access(
            thread_id=thread_id,
            timestamp=timestamp,
            access_type="write",
            location=location
        )

        with self._lock:
            if obj_id not in self._accesses:
                self._accesses[obj_id] = []
            self._accesses[obj_id].append(access)

    def detect_conflicts(self) -> list[RaceConflict]:
        """Find concurrent read-write or write-write conflicts.

        Analyzes all recorded accesses to find patterns that indicate
        race conditions:
        - Write-Write: Two writes from different threads within conflict window
        - Read-Write: Read and write from different threads within conflict window

        Returns:
            List of detected race conflicts
        """
        conflicts: list[RaceConflict] = []

        with self._lock:
            for obj_id, accesses in self._accesses.items():
                # Sort by timestamp
                sorted_accesses = sorted(accesses, key=lambda a: a.timestamp)

                # Check each pair of consecutive accesses
                for i in range(len(sorted_accesses) - 1):
                    access_1 = sorted_accesses[i]
                    access_2 = sorted_accesses[i + 1]

                    # Skip if same thread
                    if access_1.thread_id == access_2.thread_id:
                        continue

                    time_diff = access_2.timestamp - access_1.timestamp

                    # Check if within conflict window
                    if time_diff > self._conflict_window:
                        continue

                    # Determine conflict type
                    conflict_type = None
                    if access_1.access_type == "write" and access_2.access_type == "write":
                        conflict_type = "write-write"
                    elif access_1.access_type == "write" and access_2.access_type == "read":
                        conflict_type = "write-read"
                    elif access_1.access_type == "read" and access_2.access_type == "write":
                        conflict_type = "read-write"

                    if conflict_type:
                        conflicts.append(RaceConflict(
                            obj_id=obj_id,
                            access_1=access_1,
                            access_2=access_2,
                            conflict_type=conflict_type,
                            time_difference=time_diff
                        ))

        return conflicts

    def clear(self) -> None:
        """Clear all recorded accesses."""
        with self._lock:
            self._accesses.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about recorded accesses.

        Returns:
            Dictionary with statistics:
            - total_accesses: Total number of accesses
            - total_objects: Number of objects tracked
            - read_count: Number of reads
            - write_count: Number of writes
            - threads: Set of thread IDs
        """
        with self._lock:
            total_accesses = sum(len(accesses) for accesses in self._accesses.values())
            read_count = sum(
                1 for accesses in self._accesses.values()
                for a in accesses if a.access_type == "read"
            )
            write_count = sum(
                1 for accesses in self._accesses.values()
                for a in accesses if a.access_type == "write"
            )
            threads = {
                a.thread_id
                for accesses in self._accesses.values()
                for a in accesses
            }

            return {
                "total_accesses": total_accesses,
                "total_objects": len(self._accesses),
                "read_count": read_count,
                "write_count": write_count,
                "thread_count": len(threads),
                "threads": threads
            }


class InstrumentedObject:
    """Wrapper that tracks access to an object.

    This class wraps any object and automatically tracks reads and writes
    using a SharedStateTracker.

    Example:
        tracker = SharedStateTracker()
        obj = InstrumentedObject({"key": "value"}, tracker)

        # Accesses are automatically tracked
        value = obj["key"]  # Recorded as read
        obj["key"] = "new"  # Recorded as write
    """

    def __init__(self, obj: Any, tracker: SharedStateTracker) -> None:
        """Initialize instrumented object.

        Args:
            obj: Object to instrument
            tracker: Tracker to record accesses
        """
        object.__setattr__(self, '_obj', obj)
        object.__setattr__(self, '_tracker', tracker)
        object.__setattr__(self, '_obj_id', id(obj))

    def __getattribute__(self, name: str) -> Any:
        """Record reads."""
        if name in ('_obj', '_tracker', '_obj_id'):
            return object.__getattribute__(self, name)

        tracker = object.__getattribute__(self, '_tracker')
        obj_id = object.__getattribute__(self, '_obj_id')
        obj = object.__getattribute__(self, '_obj')

        tracker.record_read(obj_id, location=f"getattr:{name}")
        return getattr(obj, name)

    def __setattr__(self, name: str, value: Any) -> None:
        """Record writes."""
        tracker = object.__getattribute__(self, '_tracker')
        obj_id = object.__getattribute__(self, '_obj_id')
        obj = object.__getattribute__(self, '_obj')

        tracker.record_write(obj_id, location=f"setattr:{name}")
        setattr(obj, name, value)

    def __getitem__(self, key: Any) -> Any:
        """Record reads for container access."""
        tracker = object.__getattribute__(self, '_tracker')
        obj_id = object.__getattribute__(self, '_obj_id')
        obj = object.__getattribute__(self, '_obj')

        tracker.record_read(obj_id, location=f"getitem:{key}")
        return obj[key]

    def __setitem__(self, key: Any, value: Any) -> None:
        """Record writes for container access."""
        tracker = object.__getattribute__(self, '_tracker')
        obj_id = object.__getattribute__(self, '_obj_id')
        obj = object.__getattribute__(self, '_obj')

        tracker.record_write(obj_id, location=f"setitem:{key}")
        obj[key] = value
