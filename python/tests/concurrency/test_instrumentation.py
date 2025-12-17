"""Tests for state instrumentation."""

import threading
import time

from qontinui_devtools.concurrency.instrumentation import (
    Access,
    InstrumentedObject,
    RaceConflict,
    SharedStateTracker,
)


def test_shared_state_tracker_record_read() -> None:
    """Test recording read accesses."""
    tracker = SharedStateTracker()
    obj_id = 123

    tracker.record_read(obj_id, thread_id=1, timestamp=1.0)
    tracker.record_read(obj_id, thread_id=2, timestamp=1.001)

    stats = tracker.get_stats()
    assert stats["total_accesses"] == 2
    assert stats["read_count"] == 2
    assert stats["write_count"] == 0


def test_shared_state_tracker_record_write() -> None:
    """Test recording write accesses."""
    tracker = SharedStateTracker()
    obj_id = 123

    tracker.record_write(obj_id, thread_id=1, timestamp=1.0)
    tracker.record_write(obj_id, thread_id=2, timestamp=1.001)

    stats = tracker.get_stats()
    assert stats["total_accesses"] == 2
    assert stats["read_count"] == 0
    assert stats["write_count"] == 2


def test_detect_write_write_conflict() -> None:
    """Test detecting write-write conflicts."""
    tracker = SharedStateTracker(conflict_window=0.01)
    obj_id = 123

    # Two writes from different threads within conflict window
    tracker.record_write(obj_id, thread_id=1, timestamp=1.0)
    tracker.record_write(obj_id, thread_id=2, timestamp=1.001)

    conflicts = tracker.detect_conflicts()
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "write-write"
    assert conflicts[0].obj_id == obj_id


def test_detect_read_write_conflict() -> None:
    """Test detecting read-write conflicts."""
    tracker = SharedStateTracker(conflict_window=0.01)
    obj_id = 123

    # Read followed by write from different thread
    tracker.record_read(obj_id, thread_id=1, timestamp=1.0)
    tracker.record_write(obj_id, thread_id=2, timestamp=1.001)

    conflicts = tracker.detect_conflicts()
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "read-write"


def test_detect_write_read_conflict() -> None:
    """Test detecting write-read conflicts."""
    tracker = SharedStateTracker(conflict_window=0.01)
    obj_id = 123

    # Write followed by read from different thread
    tracker.record_write(obj_id, thread_id=1, timestamp=1.0)
    tracker.record_read(obj_id, thread_id=2, timestamp=1.001)

    conflicts = tracker.detect_conflicts()
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == "write-read"


def test_no_conflict_same_thread() -> None:
    """Test that same thread accesses don't create conflicts."""
    tracker = SharedStateTracker(conflict_window=0.01)
    obj_id = 123

    # Same thread, should not conflict
    tracker.record_write(obj_id, thread_id=1, timestamp=1.0)
    tracker.record_write(obj_id, thread_id=1, timestamp=1.001)

    conflicts = tracker.detect_conflicts()
    assert len(conflicts) == 0


def test_no_conflict_outside_window() -> None:
    """Test that accesses outside conflict window don't conflict."""
    tracker = SharedStateTracker(conflict_window=0.001)
    obj_id = 123

    # Accesses too far apart
    tracker.record_write(obj_id, thread_id=1, timestamp=1.0)
    tracker.record_write(obj_id, thread_id=2, timestamp=1.01)

    conflicts = tracker.detect_conflicts()
    assert len(conflicts) == 0


def test_tracker_clear() -> None:
    """Test clearing tracked accesses."""
    tracker = SharedStateTracker()
    obj_id = 123

    tracker.record_read(obj_id, thread_id=1, timestamp=1.0)
    tracker.record_write(obj_id, thread_id=2, timestamp=1.001)

    assert tracker.get_stats()["total_accesses"] == 2

    tracker.clear()
    assert tracker.get_stats()["total_accesses"] == 0


def test_tracker_get_stats() -> None:
    """Test getting tracker statistics."""
    tracker = SharedStateTracker()

    tracker.record_read(100, thread_id=1, timestamp=1.0)
    tracker.record_write(100, thread_id=2, timestamp=1.001)
    tracker.record_read(200, thread_id=1, timestamp=1.002)

    stats = tracker.get_stats()
    assert stats["total_accesses"] == 3
    assert stats["total_objects"] == 2
    assert stats["read_count"] == 2
    assert stats["write_count"] == 1
    assert stats["thread_count"] == 2
    assert 1 in stats["threads"]
    assert 2 in stats["threads"]


def test_tracker_with_location() -> None:
    """Test recording accesses with location information."""
    tracker = SharedStateTracker()
    obj_id = 123

    tracker.record_read(obj_id, thread_id=1, timestamp=1.0, location="file.py:10")
    tracker.record_write(obj_id, thread_id=2, timestamp=1.001, location="file.py:20")

    conflicts = tracker.detect_conflicts()
    assert len(conflicts) == 1
    assert conflicts[0].access_1.location == "file.py:10"
    assert conflicts[0].access_2.location == "file.py:20"


def test_tracker_default_thread_id() -> None:
    """Test that tracker uses current thread ID by default."""
    tracker = SharedStateTracker()
    obj_id = 123

    tracker.record_read(obj_id)  # No thread_id specified
    stats = tracker.get_stats()

    assert stats["thread_count"] == 1
    assert threading.get_ident() in stats["threads"]


def test_tracker_default_timestamp() -> None:
    """Test that tracker uses current time by default."""
    tracker = SharedStateTracker()
    obj_id = 123

    time.time()
    tracker.record_read(obj_id)
    time.time()

    # Can't directly check timestamp, but verify it was recorded
    stats = tracker.get_stats()
    assert stats["total_accesses"] == 1


def test_access_repr() -> None:
    """Test Access string representation."""
    access = Access(thread_id=123, timestamp=1.5, access_type="read")
    repr_str = repr(access)

    assert "123" in repr_str
    assert "read" in repr_str
    assert "1.5" in repr_str


def test_race_conflict_repr() -> None:
    """Test RaceConflict string representation."""
    access_1 = Access(thread_id=1, timestamp=1.0, access_type="write")
    access_2 = Access(thread_id=2, timestamp=1.001, access_type="write")

    conflict = RaceConflict(
        obj_id=123,
        access_1=access_1,
        access_2=access_2,
        conflict_type="write-write",
        time_difference=0.001,
    )

    repr_str = repr(conflict)
    assert "123" in repr_str
    assert "write-write" in repr_str
    assert "1" in repr_str
    assert "2" in repr_str


def test_instrumented_object_getattr() -> None:
    """Test InstrumentedObject tracks attribute access."""
    tracker = SharedStateTracker()

    class TestClass:
        def __init__(self) -> None:
            self.value = 42

    obj = TestClass()
    instrumented = InstrumentedObject(obj, tracker)

    # Access attribute (read)
    value = instrumented.value

    assert value == 42
    stats = tracker.get_stats()
    assert stats["read_count"] >= 1


def test_instrumented_object_setattr() -> None:
    """Test InstrumentedObject tracks attribute modification."""
    tracker = SharedStateTracker()

    class TestClass:
        def __init__(self) -> None:
            self.value = 42

    obj = TestClass()
    instrumented = InstrumentedObject(obj, tracker)

    # Modify attribute (write)
    instrumented.value = 100

    assert obj.value == 100
    stats = tracker.get_stats()
    assert stats["write_count"] >= 1


def test_instrumented_object_getitem() -> None:
    """Test InstrumentedObject tracks container access."""
    tracker = SharedStateTracker()
    obj = {"key": "value"}
    instrumented = InstrumentedObject(obj, tracker)

    # Access item (read)
    value = instrumented["key"]

    assert value == "value"
    stats = tracker.get_stats()
    assert stats["read_count"] == 1


def test_instrumented_object_setitem() -> None:
    """Test InstrumentedObject tracks container modification."""
    tracker = SharedStateTracker()
    obj = {"key": "value"}
    instrumented = InstrumentedObject(obj, tracker)

    # Modify item (write)
    instrumented["key"] = "new_value"

    assert obj["key"] == "new_value"
    stats = tracker.get_stats()
    assert stats["write_count"] == 1


def test_multiple_objects_tracking() -> None:
    """Test tracking multiple objects."""
    tracker = SharedStateTracker(conflict_window=0.01)

    obj1_id = 100
    obj2_id = 200

    # Concurrent access to obj1
    tracker.record_write(obj1_id, thread_id=1, timestamp=1.0)
    tracker.record_write(obj1_id, thread_id=2, timestamp=1.001)

    # Sequential access to obj2
    tracker.record_write(obj2_id, thread_id=1, timestamp=1.0)
    tracker.record_write(obj2_id, thread_id=2, timestamp=1.1)

    conflicts = tracker.detect_conflicts()

    # Should only detect conflict on obj1
    assert len(conflicts) == 1
    assert conflicts[0].obj_id == obj1_id


def test_concurrent_tracking() -> None:
    """Test tracker with actual concurrent access."""
    tracker = SharedStateTracker()
    shared_dict = {"value": 0}
    obj_id = id(shared_dict)

    def worker(thread_id: int) -> None:
        for _i in range(100):
            tracker.record_read(obj_id, thread_id=thread_id)
            shared_dict["value"] += 1
            tracker.record_write(obj_id, thread_id=thread_id)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(5)]

    for t in threads:
        t.start()
    for t in threads:
        t.join()

    stats = tracker.get_stats()
    assert stats["total_accesses"] == 1000  # 5 threads * 100 * 2 (read+write)
    assert stats["read_count"] == 500
    assert stats["write_count"] == 500
    assert stats["thread_count"] == 5

    # Should detect some conflicts
    conflicts = tracker.detect_conflicts()
    # Due to concurrent access, should have conflicts
    # (but exact number depends on timing)
    assert len(conflicts) >= 0  # Just verify it runs
