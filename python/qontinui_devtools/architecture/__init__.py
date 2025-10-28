"""Architecture analysis tools for detecting anti-patterns and design issues."""

from .god_class_detector import ClassMetrics, ExtractionSuggestion, GodClassDetector
from .srp_analyzer import SRPAnalyzer, SRPViolation
from .clustering import MethodCluster
from .coupling_analyzer import (
    CouplingCohesionAnalyzer,
    CouplingMetrics,
    CohesionMetrics,
)
from .dependency_graph import DependencyGraphBuilder
from .metrics_utils import (
    calculate_lcom,
    calculate_lcom4,
    calculate_tcc,
    calculate_lcc,
    count_abstract_classes,
)
from .graph_visualizer import (
    DependencyGraphVisualizer,
    GraphNode,
    GraphEdge,
)

__all__ = [
    "GodClassDetector",
    "ClassMetrics",
    "ExtractionSuggestion",
    "SRPAnalyzer",
    "SRPViolation",
    "MethodCluster",
    "CouplingCohesionAnalyzer",
    "CouplingMetrics",
    "CohesionMetrics",
    "DependencyGraphBuilder",
    "calculate_lcom",
    "calculate_lcom4",
    "calculate_tcc",
    "calculate_lcc",
    "count_abstract_classes",
    "DependencyGraphVisualizer",
    "GraphNode",
    "GraphEdge",
]
