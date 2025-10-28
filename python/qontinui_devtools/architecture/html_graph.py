"""Interactive HTML graph generator using D3.js."""

import json
from typing import Any
from .graph_visualizer import GraphNode, GraphEdge


def generate_html_graph(
    nodes: list[GraphNode], edges: list[GraphEdge], title: str = "Interactive Dependency Graph"
) -> str:
    """Generate HTML with embedded D3.js force-directed graph.

    Args:
        nodes: List of graph nodes
        edges: List of graph edges
        title: Graph title

    Returns:
        Complete HTML string with embedded JavaScript
    """
    # Convert nodes and edges to JSON-serializable format
    nodes_data = [node.to_dict() for node in nodes]
    edges_data = [edge.to_dict() for edge in edges]

    # Generate HTML
    html = HTML_TEMPLATE.format(
        title=title,
        nodes_json=json.dumps(nodes_data, indent=2),
        edges_json=json.dumps(edges_data, indent=2),
    )

    return html


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f5f5;
            overflow: hidden;
        }}

        #header {{
            background: white;
            padding: 15px 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 1000;
            position: relative;
        }}

        h1 {{
            font-size: 24px;
            color: #333;
            margin: 0;
        }}

        #controls {{
            display: flex;
            gap: 10px;
            align-items: center;
        }}

        .control-group {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        label {{
            font-size: 14px;
            color: #666;
        }}

        input[type="text"], select {{
            padding: 5px 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}

        button {{
            padding: 5px 15px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }}

        button:hover {{
            background: #0056b3;
        }}

        button.secondary {{
            background: #6c757d;
        }}

        button.secondary:hover {{
            background: #545b62;
        }}

        #graph-container {{
            width: 100%;
            height: calc(100vh - 70px);
            position: relative;
        }}

        #graph {{
            width: 100%;
            height: 100%;
        }}

        svg {{
            cursor: move;
        }}

        .node {{
            cursor: pointer;
            transition: opacity 0.2s;
        }}

        .node:hover {{
            opacity: 0.8;
        }}

        .node circle, .node rect {{
            stroke-width: 2px;
        }}

        .node text {{
            font-size: 12px;
            pointer-events: none;
            text-anchor: middle;
            fill: #333;
            font-weight: 500;
        }}

        .link {{
            stroke-opacity: 0.6;
            fill: none;
        }}

        .link:hover {{
            stroke-opacity: 1;
            stroke-width: 3px !important;
        }}

        .link-label {{
            font-size: 10px;
            fill: #666;
            text-anchor: middle;
            pointer-events: none;
        }}

        #details {{
            position: absolute;
            top: 80px;
            right: 20px;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-width: 300px;
            display: none;
            z-index: 1000;
        }}

        #details.visible {{
            display: block;
        }}

        #details h2 {{
            font-size: 18px;
            margin-bottom: 10px;
            color: #333;
        }}

        #details .close {{
            position: absolute;
            top: 10px;
            right: 10px;
            cursor: pointer;
            font-size: 20px;
            color: #999;
        }}

        #details .close:hover {{
            color: #333;
        }}

        #details .metric {{
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #eee;
        }}

        #details .metric:last-child {{
            border-bottom: none;
        }}

        #details .metric-label {{
            font-weight: 600;
            color: #666;
        }}

        #details .metric-value {{
            color: #333;
        }}

        #stats {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            font-size: 14px;
            z-index: 1000;
        }}

        #stats .stat {{
            margin: 5px 0;
        }}

        #stats .stat-label {{
            font-weight: 600;
            color: #666;
        }}

        #stats .stat-value {{
            color: #333;
            margin-left: 5px;
        }}

        .legend {{
            position: absolute;
            bottom: 20px;
            right: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            font-size: 12px;
            z-index: 1000;
        }}

        .legend h3 {{
            font-size: 14px;
            margin-bottom: 10px;
            color: #333;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
        }}

        .legend-color {{
            width: 20px;
            height: 20px;
            margin-right: 8px;
            border-radius: 3px;
            border: 1px solid #ccc;
        }}

        .legend-shape {{
            width: 20px;
            height: 20px;
            margin-right: 8px;
            display: inline-block;
        }}

        .tooltip {{
            position: absolute;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 2000;
            display: none;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>{title}</h1>
        <div id="controls">
            <div class="control-group">
                <label for="search">Search:</label>
                <input type="text" id="search" placeholder="Node name...">
            </div>
            <div class="control-group">
                <label for="filter-type">Type:</label>
                <select id="filter-type">
                    <option value="all">All</option>
                    <option value="module">Modules</option>
                    <option value="class">Classes</option>
                    <option value="function">Functions</option>
                </select>
            </div>
            <div class="control-group">
                <label for="filter-edge">Edges:</label>
                <select id="filter-edge">
                    <option value="all">All</option>
                    <option value="imports">Imports</option>
                    <option value="inherits">Inherits</option>
                    <option value="calls">Calls</option>
                </select>
            </div>
            <button id="reset-zoom">Reset View</button>
            <button id="export-svg" class="secondary">Export SVG</button>
        </div>
    </div>

    <div id="graph-container">
        <div id="graph"></div>

        <div id="details">
            <span class="close">&times;</span>
            <h2 id="detail-title">Node Details</h2>
            <div id="detail-content"></div>
        </div>

        <div id="stats">
            <div class="stat">
                <span class="stat-label">Nodes:</span>
                <span class="stat-value" id="node-count">0</span>
            </div>
            <div class="stat">
                <span class="stat-label">Edges:</span>
                <span class="stat-value" id="edge-count">0</span>
            </div>
            <div class="stat">
                <span class="stat-label">Visible:</span>
                <span class="stat-value" id="visible-count">0</span>
            </div>
        </div>

        <div class="legend">
            <h3>Legend</h3>
            <div class="legend-item">
                <div class="legend-color" style="background: #4A90E2;"></div>
                <span>Module</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #F5A623;"></div>
                <span>Class</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #7ED321;"></div>
                <span>Function</span>
            </div>
            <div class="legend-item" style="margin-top: 10px;">
                <svg width="20" height="20" class="legend-shape">
                    <line x1="0" y1="10" x2="20" y2="10" stroke="#555" stroke-width="2"/>
                </svg>
                <span>Imports</span>
            </div>
            <div class="legend-item">
                <svg width="20" height="20" class="legend-shape">
                    <line x1="0" y1="10" x2="20" y2="10" stroke="#0066cc" stroke-width="2"/>
                </svg>
                <span>Inherits</span>
            </div>
            <div class="legend-item">
                <svg width="20" height="20" class="legend-shape">
                    <line x1="0" y1="10" x2="20" y2="10" stroke="#009900" stroke-width="2"/>
                </svg>
                <span>Calls</span>
            </div>
        </div>

        <div class="tooltip" id="tooltip"></div>
    </div>

    <script>
        // Data
        const nodesData = {nodes_json};
        const edgesData = {edges_json};

        // Graph dimensions
        const width = window.innerWidth;
        const height = window.innerHeight - 70;

        // Color schemes
        const nodeColors = {{
            module: '#4A90E2',
            class: '#F5A623',
            function: '#7ED321'
        }};

        const edgeColors = {{
            imports: '#555555',
            inherits: '#0066cc',
            calls: '#009900'
        }};

        // Create SVG
        const svg = d3.select('#graph')
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        // Add zoom behavior
        const g = svg.append('g');
        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on('zoom', (event) => {{
                g.attr('transform', event.transform);
            }});
        svg.call(zoom);

        // Create arrow markers for edges
        svg.append('defs').selectAll('marker')
            .data(['imports', 'inherits', 'calls'])
            .enter().append('marker')
            .attr('id', d => `arrow-${{d}}`)
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', d => edgeColors[d]);

        // Force simulation
        const simulation = d3.forceSimulation(nodesData)
            .force('link', d3.forceLink(edgesData)
                .id(d => d.id)
                .distance(100))
            .force('charge', d3.forceManyBody().strength(-300))
            .force('center', d3.forceCenter(width / 2, height / 2))
            .force('collision', d3.forceCollide().radius(30));

        // Create links
        const link = g.append('g')
            .selectAll('line')
            .data(edgesData)
            .enter().append('line')
            .attr('class', 'link')
            .attr('stroke', d => edgeColors[d.edge_type])
            .attr('stroke-width', d => Math.sqrt(d.weight) * 2)
            .attr('marker-end', d => `url(#arrow-${{d.edge_type}})`);

        // Create nodes
        const node = g.append('g')
            .selectAll('g')
            .data(nodesData)
            .enter().append('g')
            .attr('class', 'node')
            .call(d3.drag()
                .on('start', dragStarted)
                .on('drag', dragged)
                .on('end', dragEnded));

        // Add circles/shapes to nodes
        node.append('circle')
            .attr('r', d => (d.size || 20) / 2)
            .attr('fill', d => nodeColors[d.node_type] || '#999')
            .attr('stroke', '#fff')
            .on('click', showDetails)
            .on('mouseover', showTooltip)
            .on('mouseout', hideTooltip);

        // Add labels to nodes
        node.append('text')
            .attr('dy', d => (d.size || 20) / 2 + 15)
            .text(d => d.label);

        // Update positions on simulation tick
        simulation.on('tick', () => {{
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);

            node.attr('transform', d => `translate(${{d.x}},${{d.y}})`);
        }});

        // Drag functions
        function dragStarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}

        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}

        function dragEnded(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}

        // Show node details
        function showDetails(event, d) {{
            const details = document.getElementById('details');
            const title = document.getElementById('detail-title');
            const content = document.getElementById('detail-content');

            title.textContent = d.label;

            let html = `
                <div class="metric">
                    <span class="metric-label">ID:</span>
                    <span class="metric-value">${{d.id}}</span>
                </div>
                <div class="metric">
                    <span class="metric-label">Type:</span>
                    <span class="metric-value">${{d.node_type}}</span>
                </div>
            `;

            if (d.package) {{
                html += `
                    <div class="metric">
                        <span class="metric-label">Package:</span>
                        <span class="metric-value">${{d.package}}</span>
                    </div>
                `;
            }}

            for (const [key, value] of Object.entries(d.metrics || {{}})) {{
                html += `
                    <div class="metric">
                        <span class="metric-label">${{key}}:</span>
                        <span class="metric-value">${{value}}</span>
                    </div>
                `;
            }}

            content.innerHTML = html;
            details.classList.add('visible');
        }}

        // Show tooltip
        function showTooltip(event, d) {{
            const tooltip = document.getElementById('tooltip');
            tooltip.style.display = 'block';
            tooltip.style.left = event.pageX + 10 + 'px';
            tooltip.style.top = event.pageY + 10 + 'px';
            tooltip.textContent = `${{d.label}} (${{d.node_type}})`;
        }}

        function hideTooltip() {{
            document.getElementById('tooltip').style.display = 'none';
        }}

        // Close details panel
        document.querySelector('#details .close').addEventListener('click', () => {{
            document.getElementById('details').classList.remove('visible');
        }});

        // Search functionality
        document.getElementById('search').addEventListener('input', (e) => {{
            const searchTerm = e.target.value.toLowerCase();

            node.style('opacity', d => {{
                if (!searchTerm) return 1;
                return d.label.toLowerCase().includes(searchTerm) ||
                       d.id.toLowerCase().includes(searchTerm) ? 1 : 0.2;
            }});

            link.style('opacity', d => {{
                if (!searchTerm) return 0.6;
                const sourceMatch = d.source.label.toLowerCase().includes(searchTerm) ||
                                  d.source.id.toLowerCase().includes(searchTerm);
                const targetMatch = d.target.label.toLowerCase().includes(searchTerm) ||
                                  d.target.id.toLowerCase().includes(searchTerm);
                return sourceMatch || targetMatch ? 0.6 : 0.1;
            }});
        }});

        // Filter by node type
        document.getElementById('filter-type').addEventListener('change', (e) => {{
            const filterType = e.target.value;

            node.style('display', d => {{
                return filterType === 'all' || d.node_type === filterType ? 'block' : 'none';
            }});

            updateStats();
        }});

        // Filter by edge type
        document.getElementById('filter-edge').addEventListener('change', (e) => {{
            const filterEdge = e.target.value;

            link.style('display', d => {{
                return filterEdge === 'all' || d.edge_type === filterEdge ? 'block' : 'none';
            }});

            updateStats();
        }});

        // Reset zoom
        document.getElementById('reset-zoom').addEventListener('click', () => {{
            svg.transition()
                .duration(750)
                .call(zoom.transform, d3.zoomIdentity);
        }});

        // Export SVG
        document.getElementById('export-svg').addEventListener('click', () => {{
            const svgData = svg.node().outerHTML;
            const blob = new Blob([svgData], {{type: 'image/svg+xml'}});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'dependency_graph.svg';
            a.click();
            URL.revokeObjectURL(url);
        }});

        // Update stats
        function updateStats() {{
            const visibleNodes = node.filter(function() {{
                return d3.select(this).style('display') !== 'none';
            }}).size();

            document.getElementById('node-count').textContent = nodesData.length;
            document.getElementById('edge-count').textContent = edgesData.length;
            document.getElementById('visible-count').textContent = visibleNodes;
        }}

        updateStats();

        // Handle window resize
        window.addEventListener('resize', () => {{
            const newWidth = window.innerWidth;
            const newHeight = window.innerHeight - 70;
            svg.attr('width', newWidth).attr('height', newHeight);
            simulation.force('center', d3.forceCenter(newWidth / 2, newHeight / 2));
            simulation.alpha(0.3).restart();
        }});
    </script>
</body>
</html>
"""
