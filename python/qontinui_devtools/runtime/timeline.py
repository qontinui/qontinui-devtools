"""Timeline export utilities for event traces.

This module provides functionality to export event traces to various formats
including Chrome Trace Event Format and interactive HTML timelines.
"""

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .event_tracer import EventTrace


def export_chrome_trace(
    traces: list["EventTrace"],
    output_path: str
) -> None:
    """Export traces to Chrome Trace Event Format.

    This format can be viewed in chrome://tracing or https://ui.perfetto.dev/

    Format specification:
    https://docs.google.com/document/d/1CvAClvFfyA5R-PhYUmn5OOQtYMH4h6I0nSsKchNAySU

    Args:
        traces: List of EventTrace instances
        output_path: Output file path (.json)

    Example:
        >>> tracer = EventTracer()
        >>> # ... trace some events ...
        >>> export_chrome_trace(tracer.get_all_traces(), "timeline.json")
        >>> # Open chrome://tracing and load timeline.json
    """
    events = []

    for trace in traces:
        # Add trace metadata as instant event
        events.append({
            "name": f"{trace.event_type}:{trace.event_id}",
            "cat": "metadata",
            "ph": "i",  # Instant event
            "ts": int(trace.created_at * 1_000_000),
            "pid": 0,
            "tid": 0,
            "s": "g",  # Global scope
            "args": {
                "event_id": trace.event_id,
                "event_type": trace.event_type,
                "completed": trace.completed,
                "total_latency": trace.total_latency
            }
        })

        # Add duration events for each stage
        for i, checkpoint in enumerate(trace.checkpoints):
            if i < len(trace.checkpoints) - 1:
                next_checkpoint = trace.checkpoints[i + 1]

                # Duration event (Complete event type)
                events.append({
                    "name": checkpoint.name,
                    "cat": trace.event_type,
                    "ph": "X",  # Complete event
                    "ts": int(checkpoint.timestamp * 1_000_000),  # microseconds
                    "dur": int((next_checkpoint.timestamp - checkpoint.timestamp) * 1_000_000),
                    "pid": 0,
                    "tid": checkpoint.thread_id,
                    "args": checkpoint.metadata
                })

            # Add instant event for checkpoint
            events.append({
                "name": f"checkpoint:{checkpoint.name}",
                "cat": trace.event_type,
                "ph": "i",  # Instant event
                "ts": int(checkpoint.timestamp * 1_000_000),
                "pid": 0,
                "tid": checkpoint.thread_id,
                "s": "t",  # Thread scope
                "args": checkpoint.metadata
            })

    # Write trace file
    trace_data = {
        "traceEvents": events,
        "displayTimeUnit": "ms",
        "systemTraceEvents": "SystemTraceData",
        "otherData": {
            "version": "qontinui-devtools-1.0",
            "trace_count": len(traces)
        }
    }

    with open(output_path, 'w') as f:
        json.dump(trace_data, f, indent=2)


def export_timeline_html(
    traces: list["EventTrace"],
    output_path: str
) -> None:
    """Export interactive HTML timeline visualization.

    Args:
        traces: List of EventTrace instances
        output_path: Output file path (.html)

    Example:
        >>> tracer = EventTracer()
        >>> # ... trace some events ...
        >>> export_timeline_html(tracer.get_all_traces(), "timeline.html")
    """
    # Generate HTML with embedded D3.js visualization
    html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Event Timeline - Qontinui DevTools</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        h1 {
            margin-top: 0;
            color: #333;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }

        .stat-card {
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
            border-left: 4px solid #007bff;
        }

        .stat-label {
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
            margin-top: 5px;
        }

        .timeline {
            margin-top: 20px;
        }

        .trace-row {
            fill: #4CAF50;
            opacity: 0.8;
        }

        .trace-row:hover {
            opacity: 1;
        }

        .trace-row.incomplete {
            fill: #f44336;
        }

        .axis text {
            font-size: 11px;
        }

        .tooltip {
            position: absolute;
            padding: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
        }

        .checkpoint-marker {
            fill: #2196F3;
            stroke: white;
            stroke-width: 2;
        }

        .legend {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 6px;
        }

        .legend-item {
            display: inline-block;
            margin-right: 20px;
        }

        .legend-color {
            display: inline-block;
            width: 20px;
            height: 12px;
            margin-right: 5px;
            vertical-align: middle;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Event Timeline</h1>

        <div class="stats" id="stats"></div>

        <div class="timeline" id="timeline"></div>

        <div class="legend">
            <div class="legend-item">
                <span class="legend-color" style="background: #4CAF50;"></span>
                <span>Completed</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #f44336;"></span>
                <span>Incomplete</span>
            </div>
            <div class="legend-item">
                <span class="legend-color" style="background: #2196F3;"></span>
                <span>Checkpoint</span>
            </div>
        </div>
    </div>

    <div class="tooltip" id="tooltip"></div>

    <script>
        const traces = TRACES_DATA;

        // Calculate statistics
        const stats = {
            total: traces.length,
            completed: traces.filter(t => t.completed).length,
            avgLatency: traces.reduce((sum, t) => sum + t.total_latency, 0) / traces.length,
            maxLatency: Math.max(...traces.map(t => t.total_latency))
        };

        // Render statistics
        const statsContainer = d3.select('#stats');

        statsContainer.append('div')
            .attr('class', 'stat-card')
            .html(`
                <div class="stat-label">Total Events</div>
                <div class="stat-value">${stats.total}</div>
            `);

        statsContainer.append('div')
            .attr('class', 'stat-card')
            .html(`
                <div class="stat-label">Completed</div>
                <div class="stat-value">${stats.completed}</div>
            `);

        statsContainer.append('div')
            .attr('class', 'stat-card')
            .html(`
                <div class="stat-label">Avg Latency</div>
                <div class="stat-value">${(stats.avgLatency * 1000).toFixed(2)}ms</div>
            `);

        statsContainer.append('div')
            .attr('class', 'stat-card')
            .html(`
                <div class="stat-label">Max Latency</div>
                <div class="stat-value">${(stats.maxLatency * 1000).toFixed(2)}ms</div>
            `);

        // Timeline visualization
        const margin = {top: 20, right: 20, bottom: 50, left: 150};
        const width = 1200 - margin.left - margin.right;
        const height = Math.max(400, traces.length * 30) - margin.top - margin.bottom;

        const svg = d3.select('#timeline')
            .append('svg')
            .attr('width', width + margin.left + margin.right)
            .attr('height', height + margin.top + margin.bottom)
            .append('g')
            .attr('transform', `translate(${margin.left},${margin.top})`);

        // Time scale
        const minTime = Math.min(...traces.flatMap(t =>
            t.checkpoints.map(c => c.timestamp)
        ));
        const maxTime = Math.max(...traces.flatMap(t =>
            t.checkpoints.map(c => c.timestamp)
        ));

        const xScale = d3.scaleLinear()
            .domain([0, (maxTime - minTime) * 1000])  // Convert to ms
            .range([0, width]);

        const yScale = d3.scaleBand()
            .domain(traces.map((_, i) => i))
            .range([0, height])
            .padding(0.2);

        // Axes
        const xAxis = d3.axisBottom(xScale)
            .ticks(10)
            .tickFormat(d => `${d.toFixed(0)}ms`);

        svg.append('g')
            .attr('class', 'axis')
            .attr('transform', `translate(0,${height})`)
            .call(xAxis);

        const yAxis = d3.axisLeft(yScale)
            .tickFormat((_, i) => traces[i].event_id);

        svg.append('g')
            .attr('class', 'axis')
            .call(yAxis);

        // Tooltip
        const tooltip = d3.select('#tooltip');

        // Draw traces
        traces.forEach((trace, i) => {
            if (trace.checkpoints.length < 2) return;

            const startTime = trace.checkpoints[0].timestamp;
            const endTime = trace.checkpoints[trace.checkpoints.length - 1].timestamp;

            // Trace bar
            svg.append('rect')
                .attr('class', `trace-row ${trace.completed ? '' : 'incomplete'}`)
                .attr('x', xScale((startTime - minTime) * 1000))
                .attr('y', yScale(i))
                .attr('width', xScale((endTime - startTime) * 1000))
                .attr('height', yScale.bandwidth())
                .on('mouseover', function(event) {
                    tooltip
                        .style('opacity', 1)
                        .html(`
                            <strong>${trace.event_id}</strong><br>
                            Type: ${trace.event_type}<br>
                            Latency: ${(trace.total_latency * 1000).toFixed(2)}ms<br>
                            Status: ${trace.completed ? 'Completed' : 'Incomplete'}
                        `)
                        .style('left', (event.pageX + 10) + 'px')
                        .style('top', (event.pageY - 10) + 'px');
                })
                .on('mouseout', function() {
                    tooltip.style('opacity', 0);
                });

            // Checkpoint markers
            trace.checkpoints.forEach(checkpoint => {
                svg.append('circle')
                    .attr('class', 'checkpoint-marker')
                    .attr('cx', xScale((checkpoint.timestamp - minTime) * 1000))
                    .attr('cy', yScale(i) + yScale.bandwidth() / 2)
                    .attr('r', 4)
                    .on('mouseover', function(event) {
                        tooltip
                            .style('opacity', 1)
                            .html(`
                                <strong>${checkpoint.name}</strong><br>
                                Time: ${((checkpoint.timestamp - startTime) * 1000).toFixed(2)}ms
                            `)
                            .style('left', (event.pageX + 10) + 'px')
                            .style('top', (event.pageY - 10) + 'px');
                    })
                    .on('mouseout', function() {
                        tooltip.style('opacity', 0);
                    });
            });
        });
    </script>
</body>
</html>"""

    # Convert traces to JSON
    traces_data = []
    for trace in traces:
        traces_data.append({
            "event_id": trace.event_id,
            "event_type": trace.event_type,
            "created_at": trace.created_at,
            "completed": trace.completed,
            "total_latency": trace.total_latency,
            "checkpoints": [
                {
                    "name": cp.name,
                    "timestamp": cp.timestamp,
                    "thread_id": cp.thread_id,
                    "metadata": cp.metadata
                }
                for cp in trace.checkpoints
            ]
        })

    # Replace placeholder with actual data
    html_content = html_template.replace(
        'TRACES_DATA',
        json.dumps(traces_data)
    )

    with open(output_path, 'w') as f:
        f.write(html_content)
