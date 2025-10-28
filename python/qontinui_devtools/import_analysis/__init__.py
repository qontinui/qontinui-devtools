"""
Import analysis tools for detecting circular dependencies and import deadlocks.

This package provides utilities to trace Python imports in real-time,
build import graphs, and detect circular dependencies that can cause
application freezes or deadlocks.

Example (Runtime tracing):
    >>> from qontinui_devtools.import_analysis import ImportTracer
    >>> with ImportTracer() as tracer:
    ...     import my_module
    >>> cycles = tracer.find_circular_dependencies()
    >>> if cycles:
    ...     print(f"Found {len(cycles)} circular dependencies!")

Example (Static analysis):
    >>> from qontinui_devtools.import_analysis import CircularDependencyDetector
    >>> detector = CircularDependencyDetector('/path/to/project')
    >>> cycles = detector.analyze()
    >>> for cycle in cycles:
    ...     print(cycle)
"""

from .circular_detector import CircularDependency, CircularDependencyDetector
from .import_tracer import ImportEvent, ImportGraph, ImportTracer
from .visualizer import generate_html_report, visualize_import_graph

__all__ = [
    "ImportTracer",
    "ImportEvent",
    "ImportGraph",
    "visualize_import_graph",
    "generate_html_report",
    "CircularDependency",
    "CircularDependencyDetector",
]

__version__ = "1.0.0"
