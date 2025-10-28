"""Flame graph generation for performance profiling.

This module provides utilities for generating flame graphs from stack samples,
supporting both SVG (static) and speedscope JSON (interactive) formats.
"""

import json
from collections import defaultdict
from typing import Any


def generate_flame_graph(
    stack_samples: list[tuple[float, list[str]]],
    output_path: str,
    title: str = "Action Profile",
    format: str = "svg",
) -> None:
    """Generate flame graph from stack samples.

    Args:
        stack_samples: List of (timestamp, stack_frames) tuples
        output_path: Path to save the output file
        title: Title for the flame graph
        format: Output format - "svg" for static SVG or "json" for speedscope format

    Raises:
        ValueError: If format is not supported or samples are empty
    """
    if not stack_samples:
        raise ValueError("Cannot generate flame graph from empty samples")

    if format == "json":
        data = samples_to_speedscope(stack_samples, title)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
    elif format == "svg":
        svg_content = samples_to_svg(stack_samples, title)
        with open(output_path, "w") as f:
            f.write(svg_content)
    else:
        raise ValueError(f"Unsupported format: {format}. Use 'svg' or 'json'")


def samples_to_speedscope(
    stack_samples: list[tuple[float, list[str]]], name: str = "Profile"
) -> dict[str, Any]:
    """Convert stack samples to speedscope JSON format.

    Speedscope (https://www.speedscope.app/) is an interactive flame graph visualizer.

    Args:
        stack_samples: List of (timestamp, stack_frames) tuples
        name: Profile name

    Returns:
        Dictionary in speedscope format
    """
    # Build frame index
    frames: list[str] = []
    frame_index: dict[str, int] = {}

    def get_frame_index(frame: str) -> int:
        if frame not in frame_index:
            frame_index[frame] = len(frames)
            frames.append(frame)
        return frame_index[frame]

    # Convert samples to speedscope format
    events: list[dict[str, Any]] = []
    start_time = stack_samples[0][0] if stack_samples else 0.0

    for timestamp, stack in stack_samples:
        relative_time = timestamp - start_time
        # Convert to microseconds for speedscope
        time_us = int(relative_time * 1_000_000)

        # Add stack frames (reversed - deepest first for speedscope)
        frame_indices = [get_frame_index(frame) for frame in reversed(stack)]

        events.append({"type": "O", "at": time_us, "frame": frame_indices[-1]})

    # Build speedscope profile
    speedscope_data = {
        "$schema": "https://www.speedscope.app/file-format-schema.json",
        "version": "0.0.1",
        "shared": {"frames": [{"name": frame} for frame in frames]},
        "profiles": [
            {
                "type": "sampled",
                "name": name,
                "unit": "microseconds",
                "startValue": 0,
                "endValue": int(
                    (stack_samples[-1][0] - start_time) * 1_000_000
                )
                if stack_samples
                else 0,
                "samples": [[get_frame_index(f) for f in reversed(s)] for _, s in stack_samples],
                "weights": [1] * len(stack_samples),
            }
        ],
    }

    return speedscope_data


def samples_to_svg(
    stack_samples: list[tuple[float, list[str]]],
    title: str = "Flame Graph",
    width: int = 1200,
    height: int = 800,
) -> str:
    """Generate SVG flame graph from stack samples.

    This creates a simplified flame graph representation. For production use,
    consider using dedicated libraries like py-flame-graph or Brendan Gregg's
    FlameGraph tool.

    Args:
        stack_samples: List of (timestamp, stack_frames) tuples
        title: Graph title
        width: SVG width in pixels
        height: SVG height in pixels

    Returns:
        SVG content as string
    """
    # Aggregate stacks to count occurrences
    stack_counts: dict[tuple[str, ...], int] = defaultdict(int)
    for _, stack in stack_samples:
        # Build cumulative stacks (root to leaf)
        for i in range(1, len(stack) + 1):
            stack_tuple = tuple(stack[:i])
            stack_counts[stack_tuple] += 1

    if not stack_counts:
        return _generate_empty_svg(title, width, height)

    # Calculate total samples for normalization
    total_samples = len(stack_samples)

    # Build flame graph structure
    # Each level is a list of (frame_name, x, width, parent_stack)
    levels: list[list[tuple[str, float, float, tuple[str, ...]]]] = []

    # Sort stacks by depth
    stacks_by_depth: dict[int, list[tuple[tuple[str, ...], int]]] = defaultdict(list)
    for stack, count in stack_counts.items():
        stacks_by_depth[len(stack)].append((stack, count))

    # Build levels bottom-up
    for depth in sorted(stacks_by_depth.keys()):
        level: list[tuple[str, float, float, tuple[str, ...]]] = []
        x_offset = 0.0

        for stack, count in sorted(stacks_by_depth[depth], key=lambda x: x[0]):
            frame_width = (count / total_samples) * width
            frame_name = stack[-1]  # Last frame in stack

            level.append((frame_name, x_offset, frame_width, stack))
            x_offset += frame_width

        levels.append(level)

    # Generate SVG
    frame_height = 20
    svg_height = len(levels) * frame_height + 100  # Extra for title and padding

    svg_parts = [
        f'<svg width="{width}" height="{svg_height}" xmlns="http://www.w3.org/2000/svg">',
        f'<text x="{width/2}" y="30" text-anchor="middle" font-size="18" font-weight="bold">{title}</text>',
        '<g transform="translate(0, 50)">',
    ]

    # Color palette
    colors = [
        "#e74c3c",
        "#3498db",
        "#2ecc71",
        "#f39c12",
        "#9b59b6",
        "#1abc9c",
        "#e67e22",
        "#34495e",
    ]

    # Render frames
    for level_idx, level in enumerate(levels):
        y = svg_height - 100 - (level_idx * frame_height)

        for frame_name, x, frame_width, stack in level:
            if frame_width < 1:  # Skip very narrow frames
                continue

            # Choose color based on frame name hash
            color = colors[hash(frame_name) % len(colors)]

            # Truncate frame name if too long
            display_name = frame_name
            if frame_width < 100:
                display_name = frame_name[:int(frame_width / 8)]
                if len(display_name) < len(frame_name):
                    display_name += "..."

            svg_parts.extend(
                [
                    f'<rect x="{x}" y="{y}" width="{frame_width}" height="{frame_height}" '
                    f'fill="{color}" stroke="white" stroke-width="0.5"/>',
                    f'<text x="{x + 2}" y="{y + frame_height - 5}" '
                    f'font-size="11" fill="white" font-family="monospace">{display_name}</text>',
                ]
            )

    svg_parts.extend(["</g>", "</svg>"])

    return "\n".join(svg_parts)


def _generate_empty_svg(title: str, width: int, height: int) -> str:
    """Generate an empty SVG with a message.

    Args:
        title: Graph title
        width: SVG width
        height: SVG height

    Returns:
        SVG content
    """
    return f"""<svg width="{width}" height="{height}" xmlns="http://www.w3.org/2000/svg">
    <text x="{width/2}" y="{height/2}" text-anchor="middle" font-size="18" fill="#999">
        {title} - No samples available
    </text>
</svg>"""


def aggregate_stacks(
    stack_samples: list[tuple[float, list[str]]]
) -> dict[tuple[str, ...], int]:
    """Aggregate stack samples into counts.

    Args:
        stack_samples: List of (timestamp, stack_frames) tuples

    Returns:
        Dictionary mapping stack tuples to their occurrence counts
    """
    counts: dict[tuple[str, ...], int] = defaultdict(int)
    for _, stack in stack_samples:
        stack_tuple = tuple(stack)
        counts[stack_tuple] += 1
    return dict(counts)


def get_hot_paths(
    stack_samples: list[tuple[float, list[str]]], top_n: int = 10
) -> list[tuple[tuple[str, ...], int, float]]:
    """Find the hottest execution paths.

    Args:
        stack_samples: List of (timestamp, stack_frames) tuples
        top_n: Number of top paths to return

    Returns:
        List of (stack, count, percentage) tuples sorted by count
    """
    counts = aggregate_stacks(stack_samples)
    total = len(stack_samples)

    hot_paths = [
        (stack, count, (count / total) * 100) for stack, count in counts.items()
    ]

    # Sort by count descending
    hot_paths.sort(key=lambda x: x[1], reverse=True)

    return hot_paths[:top_n]
