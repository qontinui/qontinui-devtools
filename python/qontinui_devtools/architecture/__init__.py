"""Architecture analysis tools for detecting anti-patterns and design issues."""

from .clustering import MethodCluster
from .coupling_analyzer import CohesionMetrics, CouplingCohesionAnalyzer, CouplingMetrics
from .dependency_graph import DependencyGraphBuilder
from .god_class_detector import ClassMetrics, ExtractionSuggestion, GodClassDetector
from .graph_visualizer import DependencyGraphVisualizer, GraphEdge, GraphNode
from .metrics_utils import (
    calculate_lcc,
    calculate_lcom,
    calculate_lcom4,
    calculate_tcc,
    count_abstract_classes,
)
from .srp_analyzer import SRPAnalyzer, SRPViolation

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
