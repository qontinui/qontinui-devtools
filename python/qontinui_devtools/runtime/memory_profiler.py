"""Memory profiler for detecting leaks and analyzing memory usage patterns.

This module provides tools for:
- Taking memory snapshots at intervals
- Tracking object allocation patterns
- Detecting memory leaks through growth analysis
- Analyzing memory usage trends
- Generating detailed memory reports
"""

import gc
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

try:
    import psutil
except ImportError:
    psutil = None

try:
    import tracemalloc
except ImportError:
    tracemalloc = None


@dataclass
class MemorySnapshot:
    """Snapshot of memory state at a point in time."""

    timestamp: float
    total_mb: float
    rss_mb: float  # Resident Set Size
    vms_mb: float  # Virtual Memory Size
    objects_by_type: dict[str, int]  # Type name → count
    top_objects: list[tuple[str, int]]  # (type, size_bytes)
    tracemalloc_snapshot: Any | None = None  # tracemalloc snapshot
    gc_stats: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        """String representation of snapshot."""
        return (
            f"MemorySnapshot(timestamp={self.timestamp:.2f}, "
            f"total_mb={self.total_mb:.2f}, "
            f"objects={sum(self.objects_by_type.values())})"
        )


@dataclass
class MemoryLeak:
    """Detected memory leak with growth metrics."""

    object_type: str
    count_increase: int
    size_increase_mb: float
    growth_rate: float  # objects/second
    samples: list[tuple[float, int]]  # (timestamp, count)
    confidence: float = 0.0  # 0.0 to 1.0

    def __str__(self) -> str:
        """String representation of leak."""
        return (
            f"MemoryLeak({self.object_type}: +{self.count_increase} objects, "
            f"+{self.size_increase_mb:.2f} MB, {self.growth_rate:.2f} obj/s, "
            f"confidence={self.confidence:.2%})"
        )


class MemoryProfiler:
    """Profile memory usage and detect leaks."""

    def __init__(
        self,
        enable_tracemalloc: bool = True,
        snapshot_interval: float = 5.0,
        track_top_n: int = 20,
    ) -> None:
        """Initialize memory profiler.

        Args:
            enable_tracemalloc: Enable tracemalloc for detailed tracking
            snapshot_interval: Default interval between snapshots (seconds)
            track_top_n: Number of top objects to track by size
        """
        if psutil is None:
            raise ImportError(
                "psutil is required for memory profiling. " "Install it with: pip install psutil"
            )

        self._snapshots: list[MemorySnapshot] = []
        self._baseline: MemorySnapshot | None = None
        self._enable_tracemalloc = enable_tracemalloc and tracemalloc is not None
        self._interval = snapshot_interval
        self._track_top_n = track_top_n
        self._running = False
        self._process = psutil.Process()

    def start(self) -> None:
        """Start memory profiling."""
        if self._running:
            raise RuntimeError("Memory profiler is already running")

        if self._enable_tracemalloc:
            tracemalloc.start()

        self._baseline = self.take_snapshot()
        self._running = True

    def stop(self) -> None:
        """Stop memory profiling."""
        if not self._running:
            return

        if self._enable_tracemalloc:
            tracemalloc.stop()

        self._running = False

    def take_snapshot(self) -> MemorySnapshot:
        """Take a memory snapshot.

        Returns:
            MemorySnapshot with current memory state
        """
        # Force garbage collection for accurate measurement
        gc.collect()

        # Get process memory info
        mem_info = self._process.memory_info()

        # Count objects by type
        objects_by_type = self._count_objects_by_type()

        # Get top objects by estimated size
        top_objects = self._get_top_objects()

        # Get GC statistics
        gc_stats = self._get_gc_stats()

        # Take tracemalloc snapshot
        tm_snapshot = None
        if self._enable_tracemalloc:
            tm_snapshot = tracemalloc.take_snapshot()

        snapshot = MemorySnapshot(
            timestamp=time.time(),
            total_mb=mem_info.rss / (1024 * 1024),
            rss_mb=mem_info.rss / (1024 * 1024),
            vms_mb=mem_info.vms / (1024 * 1024),
            objects_by_type=objects_by_type,
            top_objects=top_objects,
            tracemalloc_snapshot=tm_snapshot,
            gc_stats=gc_stats,
        )

        self._snapshots.append(snapshot)
        return snapshot

    def _count_objects_by_type(self) -> dict[str, int]:
        """Count all objects by their type.

        Returns:
            Dictionary mapping type names to counts
        """
        objects_by_type: dict[str, int] = defaultdict(int)

        for obj in gc.get_objects():
            try:
                type_name = type(obj).__name__
                objects_by_type[type_name] += 1
            except Exception:
                # Skip objects that cause issues
                continue

        return dict(objects_by_type)

    def _get_top_objects(self) -> list[tuple[str, int]]:
        """Get top N objects by estimated size.

        Returns:
            List of (type_name, estimated_size) tuples
        """
        if not self._enable_tracemalloc:
            return []

        try:
            snapshot = tracemalloc.take_snapshot()
            top_stats = snapshot.statistics("lineno")

            # Group by type and sum sizes
            type_sizes: dict[str, int] = defaultdict(int)

            for stat in top_stats[: self._track_top_n * 5]:
                # This is a rough estimate - we track by line number
                type_sizes[str(stat.traceback)] += stat.size

            # Sort by size and take top N
            sorted_types = sorted(type_sizes.items(), key=lambda x: x[1], reverse=True)
            return sorted_types[: self._track_top_n]

        except Exception:
            return []

    def _get_gc_stats(self) -> dict[str, Any]:
        """Get garbage collection statistics.

        Returns:
            Dictionary with GC stats
        """
        return {
            "collections": gc.get_count(),
            "objects": len(gc.get_objects()),
            "garbage": len(gc.garbage),
            "is_enabled": gc.isenabled(),
        }

    def detect_leaks(
        self,
        min_samples: int = 3,
        growth_threshold: float = 10.0,  # objects/second
        min_increase: int = 100,  # minimum object count increase
    ) -> list[MemoryLeak]:
        """Detect memory leaks from snapshots.

        Args:
            min_samples: Minimum number of samples required
            growth_threshold: Minimum growth rate (objects/sec)
            min_increase: Minimum absolute increase in object count

        Returns:
            List of detected memory leaks
        """
        if len(self._snapshots) < min_samples:
            return []

        leaks: list[MemoryLeak] = []

        # Get all object types that appear in snapshots
        all_types = set()
        for snapshot in self._snapshots:
            all_types.update(snapshot.objects_by_type.keys())

        # Analyze each object type
        for obj_type in all_types:
            samples = [(s.timestamp, s.objects_by_type.get(obj_type, 0)) for s in self._snapshots]

            # Check for steady growth
            is_growing, growth_rate, confidence = self._analyze_growth(samples, growth_threshold)

            if is_growing:
                # Calculate metrics
                first_count = samples[0][1]
                last_count = samples[-1][1]
                count_increase = last_count - first_count

                if count_increase >= min_increase:
                    # Estimate size increase (rough)
                    size_increase_mb = self._estimate_size_increase(obj_type, count_increase)

                    leak = MemoryLeak(
                        object_type=obj_type,
                        count_increase=count_increase,
                        size_increase_mb=size_increase_mb,
                        growth_rate=growth_rate,
                        samples=samples,
                        confidence=confidence,
                    )
                    leaks.append(leak)

        # Sort by confidence and growth rate
        leaks.sort(key=lambda x: (x.confidence, x.growth_rate), reverse=True)

        return leaks

    def _analyze_growth(
        self, samples: list[tuple[float, int]], threshold: float
    ) -> tuple[bool, float, float]:
        """Analyze if samples show steady growth.

        Uses simple linear regression to detect growth trend.

        Args:
            samples: List of (timestamp, count) tuples
            threshold: Minimum growth rate threshold

        Returns:
            (is_growing, growth_rate, confidence)
        """
        if len(samples) < 2:
            return False, 0.0, 0.0

        # Extract times and counts
        times = [s[0] - samples[0][0] for s in samples]  # Normalize to start at 0
        counts = [s[1] for s in samples]

        # Simple linear regression: y = mx + b
        n = len(samples)
        sum_x = sum(times)
        sum_y = sum(counts)
        sum_xy = sum(t * c for t, c in zip(times, counts, strict=False))
        sum_xx = sum(t * t for t in times)

        # Calculate slope (growth rate)
        denominator = n * sum_xx - sum_x * sum_x
        if denominator == 0:
            return False, 0.0, 0.0

        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n

        # Calculate R-squared (confidence)
        mean_y = sum_y / n
        ss_tot = sum((c - mean_y) ** 2 for c in counts)
        ss_res = sum((counts[i] - (slope * times[i] + intercept)) ** 2 for i in range(n))

        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        # Check if growth is significant
        is_growing = slope > threshold and r_squared > 0.7

        return is_growing, slope, r_squared

    def _estimate_size_increase(self, obj_type: str, count_increase: int) -> float:
        """Estimate memory size increase for object type.

        Args:
            obj_type: Type name
            count_increase: Number of new objects

        Returns:
            Estimated size increase in MB
        """
        # Rough estimates for common types
        size_estimates = {
            "dict": 240,  # bytes per dict
            "list": 64,  # bytes per list
            "tuple": 48,  # bytes per tuple
            "str": 50,  # average string
            "int": 28,  # bytes per int
            "float": 24,  # bytes per float
            "set": 224,  # bytes per set
            "object": 16,  # base object
        }

        estimated_bytes = size_estimates.get(obj_type, 32) * count_increase
        return estimated_bytes / (1024 * 1024)

    def compare_snapshots(
        self, snapshot1: MemorySnapshot, snapshot2: MemorySnapshot
    ) -> dict[str, Any]:
        """Compare two snapshots.

        Args:
            snapshot1: First snapshot
            snapshot2: Second snapshot

        Returns:
            Dictionary with comparison metrics
        """
        time_diff = snapshot2.timestamp - snapshot1.timestamp
        memory_diff = snapshot2.total_mb - snapshot1.total_mb

        # Compare object counts
        type_diffs: dict[str, int] = {}
        all_types = set(snapshot1.objects_by_type.keys()) | set(snapshot2.objects_by_type.keys())

        for obj_type in all_types:
            count1 = snapshot1.objects_by_type.get(obj_type, 0)
            count2 = snapshot2.objects_by_type.get(obj_type, 0)
            diff = count2 - count1
            if diff != 0:
                type_diffs[obj_type] = diff

        # Sort by absolute difference
        sorted_diffs = sorted(type_diffs.items(), key=lambda x: abs(x[1]), reverse=True)

        return {
            "time_diff": time_diff,
            "memory_diff_mb": memory_diff,
            "memory_rate_mb_per_sec": memory_diff / time_diff if time_diff > 0 else 0,
            "total_objects_diff": sum(type_diffs.values()),
            "type_diffs": dict(sorted_diffs[:20]),  # Top 20
            "gc_collections_diff": [
                snapshot2.gc_stats["collections"][i] - snapshot1.gc_stats["collections"][i]
                for i in range(3)
            ],
        }

    def generate_report(self) -> str:
        """Generate comprehensive memory profiling report.

        Returns:
            Multi-line report string
        """
        lines: list[Any] = []
        lines.append("=" * 80)
        lines.append("MEMORY PROFILING REPORT")
        lines.append("=" * 80)
        lines.append("")

        if not self._snapshots:
            lines.append("No snapshots collected.")
            return "\n".join(lines)

        # Summary
        first = self._snapshots[0]
        last = self._snapshots[-1]
        duration = last.timestamp - first.timestamp

        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Duration: {duration:.1f} seconds")
        lines.append(f"Snapshots: {len(self._snapshots)}")
        lines.append(
            f"Memory: {first.total_mb:.1f} MB → {last.total_mb:.1f} MB "
            f"({last.total_mb - first.total_mb:+.1f} MB)"
        )
        lines.append(f"Rate: {(last.total_mb - first.total_mb) / duration:.2f} MB/second")
        lines.append("")

        # Detect leaks
        leaks = self.detect_leaks()
        if leaks:
            lines.append("DETECTED MEMORY LEAKS")
            lines.append("-" * 80)
            for i, leak in enumerate(leaks[:10], 1):
                lines.append(
                    f"{i}. {leak.object_type}: +{leak.count_increase:,} objects "
                    f"(+{leak.size_increase_mb:.2f} MB, "
                    f"growth={leak.growth_rate:.1f} obj/s, "
                    f"confidence={leak.confidence:.1%})"
                )
            lines.append("")

        # Object count changes
        if len(self._snapshots) >= 2:
            comparison = self.compare_snapshots(first, last)
            lines.append("TOP OBJECT COUNT CHANGES")
            lines.append("-" * 80)
            for obj_type, diff in list(comparison["type_diffs"].items())[:15]:
                lines.append(f"  {obj_type:30s} {diff:+10,d}")
            lines.append("")

        # GC statistics
        lines.append("GARBAGE COLLECTION")
        lines.append("-" * 80)
        lines.append(f"Collections (gen0, gen1, gen2): {tuple(last.gc_stats['collections'])}")
        lines.append(f"Total objects: {last.gc_stats['objects']:,}")
        lines.append(f"Garbage objects: {last.gc_stats['garbage']}")
        lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)

    @property
    def snapshots(self) -> list[MemorySnapshot]:
        """Get all collected snapshots."""
        return self._snapshots.copy()

    @property
    def baseline(self) -> MemorySnapshot | None:
        """Get baseline snapshot."""
        return self._baseline

    def clear(self) -> None:
        """Clear all collected snapshots."""
        self._snapshots.clear()
        self._baseline = None

    def get_memory_usage(self) -> dict[str, float]:
        """Get current memory usage (for compatibility with tests).
        
        Returns:
            Dictionary with current_mb, peak_mb, and snapshots count
        """
        if not self._snapshots:
            return {"current_mb": 0.0, "peak_mb": 0.0, "snapshots": 0}
        
        current_mb = self._snapshots[-1].total_mb
        peak_mb = max(s.total_mb for s in self._snapshots)
        
        return {
            "current_mb": current_mb,
            "peak_mb": peak_mb,
            "snapshots": len(self._snapshots),
        }

    def export(self, output_path: str, format: str = "json") -> None:
        """Export memory profiling data (for compatibility with tests).
        
        Args:
            output_path: Output file path
            format: Export format (json or text)
        """
        import json
        from pathlib import Path
        
        if format == "json":
            data = {
                "snapshots": [
                    {
                        "timestamp": s.timestamp,
                        "total_mb": s.total_mb,
                        "rss_mb": s.rss_mb,
                        "vms_mb": s.vms_mb,
                        "objects_by_type": s.objects_by_type,
                        "gc_stats": s.gc_stats,
                    }
                    for s in self._snapshots
                ],
                "leaks": [
                    {
                        "object_type": leak.object_type,
                        "count_increase": leak.count_increase,
                        "size_increase_mb": leak.size_increase_mb,
                        "growth_rate": leak.growth_rate,
                        "confidence": leak.confidence,
                    }
                    for leak in self.detect_leaks()
                ],
                "summary": self.get_memory_usage(),
            }
            
            Path(output_path).write_text(json.dumps(data, indent=2))
        else:
            # Text format
            Path(output_path).write_text(self.generate_report())
