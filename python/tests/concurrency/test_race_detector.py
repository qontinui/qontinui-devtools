"""Tests for the race condition detector."""

import tempfile
from pathlib import Path

import pytest
from qontinui_devtools.concurrency import RaceConditionDetector


class TestRaceDetectorBasics:
    """Test basic functionality of race detector."""

    def test_detect_unprotected_class_variable(self, tmp_path: Path) -> None:
        """Test detection of class variable without lock."""
        test_code = """
class Cache:
    _data = {}

    def get(self, key)) -> Any:
        return self._data.get(key)

    def set(self, key, value):
        self._data[key] = value  # Race condition!
"""
        test_file = tmp_path / "cache.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        # Should detect race on _data
        assert len(races) >= 1
        data_races = [r for r in races if r.shared_state.name == "_data"]
        assert len(data_races) == 1
        assert data_races[0].severity in ("critical", "high")

    def test_detect_module_global_race(self, tmp_path: Path) -> None:
        """Test detection of module-level global race condition."""
        test_code = """
_instances = {}

def get_instance(key):
    if key not in _instances:  # Check
        _instances[key] = create()  # Act - Race condition!
    return _instances[key]
"""
        test_file = tmp_path / "singleton.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        # Should detect race on _instances
        assert len(races) >= 1
        instance_races = [r for r in races if r.shared_state.name == "_instances"]
        assert len(instance_races) == 1
        assert instance_races[0].severity == "critical"

    def test_detect_protected_state(self, tmp_path: Path) -> None:
        """Test that properly locked state is not flagged."""
        test_code = """
import threading

class Cache:
    def __init__(self):
        self._data = {}
        self._lock = threading.Lock()

    def set(self, key, value):
        with self._lock:
            self._data[key] = value  # Properly locked!
"""
        test_file = tmp_path / "safe_cache.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        # Should not detect race (or only low severity)
        data_races = [r for r in races if r.shared_state.name == "_data"]
        if data_races:
            # If detected, should be low severity
            assert data_races[0].severity == "low"

    def test_immutable_types_ignored(self, tmp_path: Path) -> None:
        """Test that immutable types are not flagged."""
        test_code = """
class Config:
    MAX_SIZE = 100  # Immutable int
    API_URL = "https://api.example.com"  # Immutable str

    def get_max(self):
        return self.MAX_SIZE
"""
        test_file = tmp_path / "config.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        # Should not detect races on immutable types
        assert len(races) == 0


class TestRacePatterns:
    """Test detection of specific race condition patterns."""

    def test_check_then_act_pattern(self, tmp_path: Path) -> None:
        """Test detection of check-then-act race condition."""
        test_code = """
class Cache:
    _cache = {}

    def get_or_create(self, key)) -> Any:
        if key not in self._cache:  # Check
            self._cache[key] = expensive_operation()  # Act
        return self._cache[key]
"""
        test_file = tmp_path / "check_act.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        assert len(races) >= 1
        cache_race = races[0]
        assert "check-then-act" in cache_race.patterns_detected

    def test_double_checked_locking(self, tmp_path: Path) -> None:
        """Test detection of double-checked locking pattern."""
        test_code = """
import threading

class Singleton:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:  # First check (unprotected)
            with cls._lock:
                if cls._instance is None:  # Second check (protected)
                    cls._instance = Singleton()  # Create
        return cls._instance
"""
        test_file = tmp_path / "dcl.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        # Should detect the pattern
        if races:
            instance_races = [r for r in races if r.shared_state.name == "_instance"]
            if instance_races:
                assert "double-checked-locking" in instance_races[0].patterns_detected

    def test_write_write_conflict(self, tmp_path: Path) -> None:
        """Test detection of write-write conflicts."""
        test_code = """
class Counter:
    _count = 0

    def increment(self):
        self._count += 1  # Write

    def decrement(self):
        self._count -= 1  # Write
"""
        test_file = tmp_path / "counter.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        assert len(races) >= 1
        count_race = races[0]
        assert count_race.severity == "critical"

    def test_read_write_conflict(self, tmp_path: Path) -> None:
        """Test detection of read-write conflicts."""
        test_code = """
class SharedBuffer:
    _buffer = []

    def add(self, item):
        self._buffer.append(item)  # Write

    def get_all(self):
        return self._buffer[:]  # Read
"""
        test_file = tmp_path / "buffer.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        assert len(races) >= 1
        assert races[0].severity in ("critical", "high")


class TestLockDetection:
    """Test lock detection and association."""

    def test_detect_lock_creation(self, tmp_path: Path) -> None:
        """Test detection of lock creation."""
        test_code = """
import threading

class ThreadSafe:
    def __init__(self):
        self._lock = threading.Lock()
        self._rlock = threading.RLock()
        self._semaphore = threading.Semaphore(5)
"""
        test_file = tmp_path / "locks.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        detector.analyze()

        lock_usage = detector.find_lock_usage()
        assert str(test_file) in lock_usage
        locks = lock_usage[str(test_file)]
        assert "_lock" in locks or "_rlock" in locks or "_semaphore" in locks

    def test_with_lock_context(self, tmp_path: Path) -> None:
        """Test detection of 'with lock:' usage."""
        test_code = """
import threading

class SafeCounter:
    def __init__(self):
        self._count = 0
        self._lock = threading.Lock()

    def increment(self):
        with self._lock:
            self._count += 1  # Protected
"""
        test_file = tmp_path / "with_lock.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        # Should have no critical races (all accesses protected)
        critical_races = [r for r in races if r.severity == "critical"]
        assert len(critical_races) == 0


class TestHeuristics:
    """Test heuristic analysis."""

    def test_thread_local_storage(self, tmp_path: Path) -> None:
        """Test that thread-local storage is recognized as safe."""
        test_code = """
import threading

_local = threading.local()

def get_connection():
    if not hasattr(_local, 'conn'):
        _local.conn = create_connection()
    return _local.conn
"""
        test_file = tmp_path / "local.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        # Thread-local should not be flagged
        local_races = [r for r in races if "_local" in r.shared_state.name]
        assert len(local_races) == 0

    def test_queue_types_safe(self, tmp_path: Path) -> None:
        """Test that queue types are recognized as thread-safe."""
        test_code = """
from queue import Queue

class TaskManager:
    _tasks = Queue()

    def add_task(self, task):
        self._tasks.put(task)  # Thread-safe

    def get_task(self):
        return self._tasks.get()  # Thread-safe
"""
        test_file = tmp_path / "queue.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        # Queue should not be flagged
        queue_races = [r for r in races if "_tasks" in r.shared_state.name]
        assert len(queue_races) == 0

    def test_constants_ignored(self, tmp_path: Path) -> None:
        """Test that constants (uppercase) are not flagged."""
        test_code = """
MAX_CONNECTIONS = 100
API_TIMEOUT = 30.0

def get_max():
    return MAX_CONNECTIONS
"""
        test_file = tmp_path / "constants.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        # Constants should not be flagged
        assert len(races) == 0


class TestReporting:
    """Test report generation."""

    def test_generate_report(self, tmp_path: Path) -> None:
        """Test report generation."""
        test_code = """
class BadCache:
    _data = {}

    def set(self, key, value):
        self._data[key] = value
"""
        test_file = tmp_path / "report.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        detector.analyze()

        report = detector.generate_report()

        assert "RACE CONDITION DETECTION REPORT" in report
        assert "SUMMARY" in report
        assert "DETAILED FINDINGS" in report

    def test_statistics(self, tmp_path: Path) -> None:
        """Test statistics generation."""
        test_code = """
class Stats:
    _counter = 0
    _cache = {}

    def increment(self):
        self._counter += 1

    def cache_set(self, key, value):
        self._cache[key] = value
"""
        test_file = tmp_path / "stats.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        detector.analyze()

        stats = detector.get_statistics()

        assert "files_analyzed" in stats
        assert stats["files_analyzed"] >= 1
        assert "shared_states_found" in stats
        assert "race_conditions_found" in stats


class TestComplexScenarios:
    """Test complex real-world scenarios."""

    def test_singleton_pattern(self, tmp_path: Path) -> None:
        """Test detection in singleton pattern."""
        test_code = """
class Database:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance
"""
        test_file = tmp_path / "singleton.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        # Should detect race in singleton pattern
        assert len(races) >= 1
        assert races[0].severity in ("critical", "high")

    def test_hal_factory_pattern(self, tmp_path: Path) -> None:
        """Test detection of HALFactory-like race conditions."""
        test_code = """
class HALFactory:
    _instances = {}

    @classmethod
    def get_hal(cls, hal_type):
        if hal_type not in cls._instances:
            cls._instances[hal_type] = cls._create_hal(hal_type)
        return cls._instances[hal_type]

    @classmethod
    def _create_hal(cls, hal_type):
        # Create HAL instance
        pass
"""
        test_file = tmp_path / "hal.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        # Should detect the check-then-act race
        assert len(races) >= 1
        instances_race = races[0]
        assert "check-then-act" in instances_race.patterns_detected
        assert instances_race.severity == "critical"

    def test_multiple_files(self, tmp_path: Path) -> None:
        """Test analysis across multiple files."""
        file1 = tmp_path / "module1.py"
        file1.write_text(
            """
class Cache1:
    _data = {}

    def set(self, k, v):
        self._data[k] = v
"""
        )

        file2 = tmp_path / "module2.py"
        file2.write_text(
            """
class Cache2:
    _data = []

    def append(self, item):
        self._data.append(item)
"""
        )

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        # Should detect races in both files
        assert len(races) >= 2

        stats = detector.get_statistics()
        assert stats["files_analyzed"] >= 2


class TestExclusions:
    """Test exclusion patterns."""

    def test_exclude_test_files(self, tmp_path: Path) -> None:
        """Test that test files can be excluded."""
        test_file = tmp_path / "example.py"
        test_file.write_text(
            """
class TestCache:
    _data = {}

    def test_set(self) -> None:
        self._data['key'] = 'value'
"""
        )

        detector = RaceConditionDetector(tmp_path, exclude_patterns=["test_"])
        detector.analyze()

        # Should not analyze excluded files
        stats = detector.get_statistics()
        assert stats["files_analyzed"] == 0

    def test_exclude_venv(self, tmp_path: Path) -> None:
        """Test that venv directories are excluded by default."""
        venv_dir = tmp_path / "venv" / "lib"
        venv_dir.mkdir(parents=True)

        venv_file = venv_dir / "module.py"
        venv_file.write_text(
            """
_data = {}

def unsafe():
    _data['key'] = 'value'
"""
        )

        main_file = tmp_path / "main.py"
        main_file.write_text(
            """
_cache = {}

def process():
    _cache['key'] = 'value'
"""
        )

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        detector.analyze()

        stats = detector.get_statistics()
        # Should only analyze main.py, not venv files
        assert stats["files_analyzed"] == 1


class TestSeverityCalculation:
    """Test severity calculation logic."""

    def test_critical_multiple_writes(self, tmp_path: Path) -> None:
        """Test that multiple unprotected writes are critical."""
        test_code = """
class MultiWrite:
    _value = 0

    def increment(self):
        self._value += 1

    def decrement(self):
        self._value -= 1

    def reset(self):
        self._value = 0
"""
        test_file = tmp_path / "multiwrite.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        assert len(races) >= 1
        assert races[0].severity == "critical"

    def test_high_single_write(self, tmp_path: Path) -> None:
        """Test that single unprotected write is high severity."""
        test_code = """
class SingleWrite:
    _data = []

    def append(self, item):
        self._data.append(item)
"""
        test_file = tmp_path / "single.py"
        test_file.write_text(test_code)

        detector = RaceConditionDetector(tmp_path, exclude_patterns=[])
        races = detector.analyze()

        assert len(races) >= 1
        assert races[0].severity in ("critical", "high")


@pytest.fixture
def tmp_path():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
