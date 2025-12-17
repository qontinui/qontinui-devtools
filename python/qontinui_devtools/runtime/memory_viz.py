"""Memory usage visualization tools.

This module provides:
- Memory timeline plots
- Object growth charts
- Heatmaps for memory allocation
- Interactive HTML reports
"""

from pathlib import Path
from typing import Any

try:
    import matplotlib

    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


def plot_memory_timeline(
    snapshots: list[Any],  # list[MemorySnapshot]
    output_path: str,
    title: str = "Memory Usage Over Time",
) -> None:
    """Plot memory usage over time.

    Args:
        snapshots: List of MemorySnapshot objects
        output_path: Path to save the plot
        title: Plot title
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "matplotlib is required for visualization. " "Install it with: pip install matplotlib"
        )

    if not snapshots:
        raise ValueError("No snapshots provided")

    # Extract data
    times = [s.timestamp - snapshots[0].timestamp for s in snapshots]
    memory_mb = [s.total_mb for s in snapshots]
    rss_mb = [s.rss_mb for s in snapshots]
    vms_mb = [s.vms_mb for s in snapshots]

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot lines
    ax.plot(times, memory_mb, marker="o", label="Total Memory", linewidth=2)
    ax.plot(times, rss_mb, marker="s", label="RSS", linewidth=1.5, alpha=0.7)
    ax.plot(times, vms_mb, marker="^", label="VMS", linewidth=1.5, alpha=0.7)

    # Formatting
    ax.set_xlabel("Time (seconds)", fontsize=12)
    ax.set_ylabel("Memory (MB)", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    # Add min/max annotations
    max_idx = memory_mb.index(max(memory_mb))
    ax.annotate(
        f"Peak: {memory_mb[max_idx]:.1f} MB",
        xy=(times[max_idx], memory_mb[max_idx]),
        xytext=(10, 10),
        textcoords="offset points",
        bbox={"boxstyle": "round,pad=0.5", "fc": "yellow", "alpha": 0.7},
        arrowprops={"arrowstyle": "->", "connectionstyle": "arc3,rad=0"},
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_object_growth(
    snapshots: list[Any],  # list[MemorySnapshot]
    object_type: str,
    output_path: str,
    title: str | None = None,
) -> None:
    """Plot object count growth over time.

    Args:
        snapshots: List of MemorySnapshot objects
        object_type: Type of object to track
        output_path: Path to save the plot
        title: Plot title (auto-generated if None)
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "matplotlib is required for visualization. " "Install it with: pip install matplotlib"
        )

    if not snapshots:
        raise ValueError("No snapshots provided")

    # Extract data
    times = [s.timestamp - snapshots[0].timestamp for s in snapshots]
    counts = [s.objects_by_type.get(object_type, 0) for s in snapshots]

    if not title:
        title = f"Growth of {object_type} Objects Over Time"

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot
    ax.plot(times, counts, marker="o", linewidth=2, color="#2E86AB")
    ax.fill_between(times, counts, alpha=0.3, color="#2E86AB")

    # Formatting
    ax.set_xlabel("Time (seconds)", fontsize=12)
    ax.set_ylabel(f"{object_type} Count", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)

    # Add growth rate annotation
    if len(counts) >= 2:
        growth = counts[-1] - counts[0]
        rate = growth / times[-1] if times[-1] > 0 else 0
        ax.text(
            0.02,
            0.98,
            f"Growth: {growth:+d} objects\nRate: {rate:.1f} obj/s",
            transform=ax.transAxes,
            verticalalignment="top",
            bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5},
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_top_objects(
    snapshots: list[Any],  # list[MemorySnapshot]
    output_path: str,
    top_n: int = 15,
    title: str = "Top Objects by Count",
) -> None:
    """Plot top objects by count from the last snapshot.

    Args:
        snapshots: List of MemorySnapshot objects
        output_path: Path to save the plot
        top_n: Number of top objects to show
        title: Plot title
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "matplotlib is required for visualization. " "Install it with: pip install matplotlib"
        )

    if not snapshots:
        raise ValueError("No snapshots provided")

    # Get last snapshot
    last_snapshot = snapshots[-1]

    # Get top objects
    sorted_objects = sorted(
        last_snapshot.objects_by_type.items(),
        key=lambda x: x[1],
        reverse=True,
    )[:top_n]

    if not sorted_objects:
        return

    types, counts = zip(*sorted_objects, strict=False)

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # Horizontal bar chart
    y_pos = range(len(types))
    cmap = plt.get_cmap('viridis')
    colors = cmap([(i / len(types)) for i in range(len(types))])

    ax.barh(y_pos, counts, color=colors)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(types)
    ax.invert_yaxis()  # Labels read top-to-bottom
    ax.set_xlabel("Count", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.grid(True, axis="x", alpha=0.3)

    # Add count labels
    for i, (_obj_type, count) in enumerate(sorted_objects):
        ax.text(count, i, f" {count:,}", va="center", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_leak_heatmap(
    snapshots: list[Any],  # list[MemorySnapshot]
    output_path: str,
    tracked_types: list[str] | None = None,
    title: str = "Object Growth Heatmap",
) -> None:
    """Create a heatmap showing object growth patterns.

    Args:
        snapshots: List of MemorySnapshot objects
        output_path: Path to save the plot
        tracked_types: List of object types to track (auto-detect if None)
        title: Plot title
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "matplotlib is required for visualization. " "Install it with: pip install matplotlib"
        )

    if not snapshots or len(snapshots) < 2:
        raise ValueError("Need at least 2 snapshots")

    # Auto-detect types if not provided
    if tracked_types is None:
        # Find types that appear in all snapshots
        all_types = set()
        for snapshot in snapshots:
            all_types.update(snapshot.objects_by_type.keys())

        # Get top types by final count
        last_snapshot = snapshots[-1]
        sorted_types = sorted(
            [(t, last_snapshot.objects_by_type.get(t, 0)) for t in all_types],
            key=lambda x: x[1],
            reverse=True,
        )
        tracked_types = [t for t, _ in sorted_types[:20]]

    # Build data matrix
    data: list[Any] = []
    for obj_type in tracked_types:
        counts = [s.objects_by_type.get(obj_type, 0) for s in snapshots]
        # Normalize to show growth from baseline
        baseline = counts[0] if counts[0] > 0 else 1
        normalized = [(c - baseline) / baseline * 100 for c in counts]
        data.append(normalized)

    # Create figure
    fig, ax = plt.subplots(figsize=(14, 10))

    # Heatmap
    im = ax.imshow(data, cmap="RdYlGn_r", aspect="auto", interpolation="nearest")

    # Set ticks
    ax.set_xticks(range(len(snapshots)))
    ax.set_yticks(range(len(tracked_types)))
    ax.set_xticklabels([f"{i}" for i in range(len(snapshots))], rotation=45)
    ax.set_yticklabels(tracked_types)

    # Labels
    ax.set_xlabel("Snapshot", fontsize=12)
    ax.set_ylabel("Object Type", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")

    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label("Growth (%)", rotation=270, labelpad=20)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_comparison(
    snapshot1: Any,  # MemorySnapshot
    snapshot2: Any,  # MemorySnapshot
    output_path: str,
    top_n: int = 15,
    title: str = "Memory Snapshot Comparison",
) -> None:
    """Create a comparison plot between two snapshots.

    Args:
        snapshot1: First snapshot
        snapshot2: Second snapshot
        output_path: Path to save the plot
        top_n: Number of top changes to show
        title: Plot title
    """
    if not MATPLOTLIB_AVAILABLE:
        raise ImportError(
            "matplotlib is required for visualization. " "Install it with: pip install matplotlib"
        )

    # Calculate differences
    all_types = set(snapshot1.objects_by_type.keys()) | set(snapshot2.objects_by_type.keys())

    diffs: dict[Any, Any] = {}
    for obj_type in all_types:
        count1 = snapshot1.objects_by_type.get(obj_type, 0)
        count2 = snapshot2.objects_by_type.get(obj_type, 0)
        diff = count2 - count1
        if diff != 0:
            diffs[obj_type] = diff

    # Get top changes
    sorted_diffs = sorted(diffs.items(), key=lambda x: abs(x[1]), reverse=True)[:top_n]

    if not sorted_diffs:
        return

    types, changes = zip(*sorted_diffs, strict=False)

    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

    # Left: Object count differences
    colors = ["green" if c > 0 else "red" for c in changes]
    y_pos = range(len(types))

    ax1.barh(y_pos, changes, color=colors, alpha=0.7)
    ax1.set_yticks(y_pos)
    ax1.set_yticklabels(types)
    ax1.invert_yaxis()
    ax1.set_xlabel("Count Change", fontsize=12)
    ax1.set_title("Object Count Changes", fontsize=12, fontweight="bold")
    ax1.grid(True, axis="x", alpha=0.3)
    ax1.axvline(x=0, color="black", linewidth=0.5)

    # Add labels
    for i, change in enumerate(changes):
        ax1.text(
            change,
            i,
            f" {change:+d}",
            va="center",
            ha="left" if change > 0 else "right",
            fontsize=9,
        )

    # Right: Memory overview
    time_diff = snapshot2.timestamp - snapshot1.timestamp
    mem_diff = snapshot2.total_mb - snapshot1.total_mb

    categories = ["Total MB", "RSS MB", "VMS MB"]
    before = [snapshot1.total_mb, snapshot1.rss_mb, snapshot1.vms_mb]
    after = [snapshot2.total_mb, snapshot2.rss_mb, snapshot2.vms_mb]

    x = range(len(categories))
    width = 0.35

    ax2.bar([i - width / 2 for i in x], before, width, label="Before", alpha=0.8)
    ax2.bar([i + width / 2 for i in x], after, width, label="After", alpha=0.8)

    ax2.set_ylabel("Memory (MB)", fontsize=12)
    ax2.set_title("Memory Usage Comparison", fontsize=12, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories)
    ax2.legend()
    ax2.grid(True, axis="y", alpha=0.3)

    # Add summary text
    summary = (
        f"Time: {time_diff:.1f}s\n"
        f"Memory: {mem_diff:+.1f} MB\n"
        f"Rate: {mem_diff / time_diff:.2f} MB/s"
    )
    ax2.text(
        0.02,
        0.98,
        summary,
        transform=ax2.transAxes,
        verticalalignment="top",
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5},
        fontsize=10,
    )

    plt.suptitle(title, fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def generate_html_report(
    snapshots: list[Any],  # list[MemorySnapshot]
    leaks: list[Any],  # list[MemoryLeak]
    output_path: str,
    plot_dir: str | None = None,
) -> None:
    """Generate an interactive HTML report.

    Args:
        snapshots: List of MemorySnapshot objects
        leaks: List of detected MemoryLeak objects
        output_path: Path to save the HTML report
        plot_dir: Directory to save plots (temp dir if None)
    """
    if not snapshots:
        raise ValueError("No snapshots provided")

    # Create plot directory
    if plot_dir is None:
        plot_path = Path(output_path).parent / "memory_plots"
    else:
        plot_path = Path(plot_dir)

    plot_path.mkdir(exist_ok=True)

    # Generate plots
    timeline_path = plot_path / "timeline.png"
    top_objects_path = plot_path / "top_objects.png"

    try:
        plot_memory_timeline(snapshots, str(timeline_path))
        plot_top_objects(snapshots, str(top_objects_path))
    except Exception as e:
        print(f"Warning: Could not generate plots: {e}")

    # Generate HTML
    first = snapshots[0]
    last = snapshots[-1]
    duration = last.timestamp - first.timestamp
    mem_change = last.total_mb - first.total_mb

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Memory Profile Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            background-color: #ecf0f1;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }}
        .metric {{
            display: inline-block;
            margin: 10px 20px 10px 0;
        }}
        .metric-label {{
            font-weight: bold;
            color: #7f8c8d;
        }}
        .metric-value {{
            font-size: 1.5em;
            color: #2c3e50;
        }}
        .leak {{
            background-color: #ffe5e5;
            border-left: 4px solid #e74c3c;
            padding: 15px;
            margin: 10px 0;
            border-radius: 3px;
        }}
        .leak-critical {{ border-left-color: #c0392b; }}
        .leak-high {{ border-left-color: #e74c3c; }}
        .leak-medium {{ border-left-color: #e67e22; }}
        .leak-low {{ border-left-color: #f39c12; }}
        .plot {{
            text-align: center;
            margin: 30px 0;
        }}
        .plot img {{
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #3498db;
            color: white;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .positive {{ color: #27ae60; }}
        .negative {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Memory Profiling Report</h1>

        <div class="summary">
            <div class="metric">
                <div class="metric-label">Duration</div>
                <div class="metric-value">{duration:.1f}s</div>
            </div>
            <div class="metric">
                <div class="metric-label">Initial Memory</div>
                <div class="metric-value">{first.total_mb:.1f} MB</div>
            </div>
            <div class="metric">
                <div class="metric-label">Final Memory</div>
                <div class="metric-value">{last.total_mb:.1f} MB</div>
            </div>
            <div class="metric">
                <div class="metric-label">Change</div>
                <div class="metric-value {'positive' if mem_change < 0 else 'negative'}">
                    {mem_change:+.1f} MB
                </div>
            </div>
            <div class="metric">
                <div class="metric-label">Snapshots</div>
                <div class="metric-value">{len(snapshots)}</div>
            </div>
        </div>
"""

    # Add leaks section
    if leaks:
        html += f"""
        <h2>Detected Memory Leaks ({len(leaks)})</h2>
"""
        for i, leak in enumerate(leaks[:10], 1):
            severity = (
                "high" if leak.confidence > 0.9 else "medium" if leak.confidence > 0.7 else "low"
            )
            html += f"""
        <div class="leak leak-{severity}">
            <strong>{i}. {leak.object_type}</strong><br>
            Count increase: {leak.count_increase:,} objects<br>
            Size increase: {leak.size_increase_mb:.2f} MB<br>
            Growth rate: {leak.growth_rate:.2f} objects/second<br>
            Confidence: {leak.confidence:.1%}
        </div>
"""
    else:
        html += """
        <h2>Detected Memory Leaks</h2>
        <p style="color: #27ae60; font-weight: bold;">✓ No memory leaks detected</p>
"""

    # Add plots
    if timeline_path.exists():
        html += f"""
        <h2>Memory Timeline</h2>
        <div class="plot">
            <img src="{timeline_path.relative_to(Path(output_path).parent)}" alt="Memory Timeline">
        </div>
"""

    if top_objects_path.exists():
        html += f"""
        <h2>Top Objects</h2>
        <div class="plot">
            <img src="{top_objects_path.relative_to(Path(output_path).parent)}" alt="Top Objects">
        </div>
"""

    # Add object counts table
    html += """
        <h2>Object Counts</h2>
        <table>
            <tr>
                <th>Type</th>
                <th>Initial</th>
                <th>Final</th>
                <th>Change</th>
            </tr>
"""

    # Get top object changes
    all_types = set(first.objects_by_type.keys()) | set(last.objects_by_type.keys())
    changes: list[Any] = []
    for obj_type in all_types:
        initial = first.objects_by_type.get(obj_type, 0)
        final = last.objects_by_type.get(obj_type, 0)
        change = final - initial
        if change != 0:
            changes.append((obj_type, initial, final, change))

    changes.sort(key=lambda x: abs(x[3]), reverse=True)

    for obj_type, initial, final, change in changes[:30]:
        change_class = "positive" if change < 0 else "negative"
        html += f"""
            <tr>
                <td>{obj_type}</td>
                <td>{initial:,}</td>
                <td>{final:,}</td>
                <td class="{change_class}">{change:+,}</td>
            </tr>
"""

    html += """
        </table>
    </div>
</body>
</html>
"""

    # Write HTML file
    Path(output_path).write_text(html)
