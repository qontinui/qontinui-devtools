"""Coupling and Cohesion analyzer for Python codebases."""

import ast
from dataclasses import dataclass
from pathlib import Path

from .dependency_graph import DependencyGraphBuilder
from .metrics_utils import (
    calculate_lcc,
    calculate_lcom,
    calculate_lcom4,
    calculate_tcc,
    count_abstract_classes,
)


@dataclass
class CouplingMetrics:
    """Coupling metrics for a module or class."""

    name: str
    file_path: str
    afferent_coupling: int  # How many modules depend on this (Ca)
    efferent_coupling: int  # How many modules this depends on (Ce)
    instability: float  # Ce / (Ca + Ce), range 0-1
    abstractness: float  # Abstract classes / total classes
    distance_from_main: float  # Distance from ideal balance
    coupling_score: str  # "excellent", "good", "fair", "poor"


@dataclass
class CohesionMetrics:
    """Cohesion metrics for a class."""

    name: str
    file_path: str
    lcom: float  # Lack of Cohesion of Methods (0-1)
    lcom4: float  # LCOM4 metric (connected components)
    tcc: float  # Tight Class Cohesion (0-1)
    lcc: float  # Loose Class Cohesion (0-1)
    cohesion_score: str  # "excellent", "good", "fair", "poor"


class CouplingCohesionAnalyzer:
    """Analyze coupling and cohesion metrics for Python code."""

    def __init__(self, verbose: bool = False):
        """Initialize the analyzer.

        Args:
            verbose: If True, print progress information
        """
        self.verbose = verbose
        self.graph_builder = DependencyGraphBuilder(verbose=verbose)

    def analyze_directory(self, path: str) -> tuple[list[CouplingMetrics], list[CohesionMetrics]]:
        """Analyze a directory for coupling and cohesion metrics.

        Args:
            path: Directory or file path to analyze

        Returns:
            Tuple of (coupling_metrics, cohesion_metrics)
        """
        root = Path(path).resolve()

        if not root.exists():
            raise ValueError(f"Path does not exist: {path}")

        # Get all Python files
        if root.is_file():
            python_files = [root]
        else:
            python_files = list(root.rglob("*.py"))

        if self.verbose:
            print(f"Analyzing {len(python_files)} Python files...")

        # Build dependency graph for coupling analysis
        dep_graph = self.graph_builder.build(str(root))

        # Calculate coupling metrics for each module
        coupling_metrics: list[CouplingMetrics] = []
        for file_path in python_files:
            metrics = self.calculate_coupling(str(file_path), dep_graph)
            coupling_metrics.append(metrics)

        # Calculate cohesion metrics for each class
        cohesion_metrics: list[CohesionMetrics] = []
        for file_path in python_files:
            class_metrics = self._analyze_file_cohesion(file_path)
            cohesion_metrics.extend(class_metrics)

        if self.verbose:
            print(f"Found {len(coupling_metrics)} modules")
            print(f"Found {len(cohesion_metrics)} classes")

        return (coupling_metrics, cohesion_metrics)

    def calculate_coupling(
        self, module_path: str, dep_graph: dict[str, set] | None = None
    ) -> CouplingMetrics:
        """Calculate coupling metrics for a module.

        Args:
            module_path: Path to the module file
            dep_graph: Pre-built dependency graph (optional)

        Returns:
            CouplingMetrics for the module
        """
        if dep_graph is None:
            # Build graph just for this module
            parent = str(Path(module_path).parent)
            dep_graph = self.graph_builder.build(parent)

        # Calculate afferent and efferent coupling
        ca = self.graph_builder.calculate_afferent_coupling(module_path, dep_graph)
        ce = self.graph_builder.calculate_efferent_coupling(module_path, dep_graph)

        # Calculate instability
        instability = self.calculate_instability(ca, ce)

        # Calculate abstractness
        abstract_count, total_count = count_abstract_classes(module_path)
        abstractness = abstract_count / total_count if total_count > 0 else 0.0

        # Calculate distance from main sequence
        distance = self.calculate_distance_from_main(instability, abstractness)

        # Classify coupling quality
        # Good coupling: balanced instability, appropriate abstractness, low distance
        coupling_score = self._classify_coupling(ca, ce, instability, distance)

        # Get module name
        module_name = self.graph_builder.get_module_name(module_path)

        return CouplingMetrics(
            name=module_name,
            file_path=module_path,
            afferent_coupling=ca,
            efferent_coupling=ce,
            instability=instability,
            abstractness=abstractness,
            distance_from_main=distance,
            coupling_score=coupling_score,
        )

    def calculate_cohesion(self, class_node: ast.ClassDef, file_path: str) -> CohesionMetrics:
        """Calculate cohesion metrics for a class.

        Args:
            class_node: AST node representing the class
            file_path: Path to the file containing the class

        Returns:
            CohesionMetrics for the class
        """
        # Calculate all cohesion metrics
        lcom = calculate_lcom(class_node)
        lcom4 = calculate_lcom4(class_node)
        tcc = calculate_tcc(class_node)
        lcc = calculate_lcc(class_node)

        # Classify cohesion quality
        cohesion_score = self._classify_cohesion(lcom, lcom4, tcc, lcc)

        return CohesionMetrics(
            name=class_node.name,
            file_path=file_path,
            lcom=lcom,
            lcom4=lcom4,
            tcc=tcc,
            lcc=lcc,
            cohesion_score=cohesion_score,
        )

    def _analyze_file_cohesion(self, file_path: Path) -> list[CohesionMetrics]:
        """Analyze cohesion for all classes in a file.

        Args:
            file_path: Path to Python file

        Returns:
            List of CohesionMetrics for all classes in the file
        """
        metrics: list[CohesionMetrics] = []

        try:
            with open(file_path, encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(file_path))
        except Exception:
            return metrics

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_metrics = self.calculate_cohesion(node, str(file_path))
                metrics.append(class_metrics)

        return metrics

    def build_dependency_graph(self, path: str) -> dict[str, set]:
        """Build dependency graph for a directory.

        Args:
            path: Directory path to analyze

        Returns:
            Dictionary mapping module paths to sets of imported module paths
        """
        return self.graph_builder.build(path)

    def calculate_instability(self, ca: int, ce: int) -> float:
        """Calculate instability metric.

        Instability = Ce / (Ca + Ce)

        Range: 0 (maximally stable) to 1 (maximally unstable)

        Args:
            ca: Afferent coupling
            ce: Efferent coupling

        Returns:
            Instability score (0-1)
        """
        total = ca + ce
        if total == 0:
            return 0.0
        return ce / total

    def calculate_distance_from_main(self, instability: float, abstractness: float) -> float:
        """Calculate distance from the main sequence.

        The main sequence is the ideal balance: A + I = 1
        Distance = |A + I - 1|

        Args:
            instability: Instability score (0-1)
            abstractness: Abstractness score (0-1)

        Returns:
            Distance from main sequence (0-1, lower is better)
        """
        return abs(abstractness + instability - 1.0)

    def _classify_coupling(self, ca: int, ce: int, instability: float, distance: float) -> str:
        """Classify coupling quality.

        Args:
            ca: Afferent coupling
            ce: Efferent coupling
            instability: Instability score
            distance: Distance from main sequence

        Returns:
            Quality score: 'excellent', 'good', 'fair', 'poor'
        """
        # Primary metric: distance from main sequence
        # Secondary: efferent coupling (dependency count)

        if distance <= 0.1:
            if ce <= 5:
                return "excellent"
            elif ce <= 10:
                return "good"
            else:
                return "fair"
        elif distance <= 0.2:
            if ce <= 10:
                return "good"
            elif ce <= 15:
                return "fair"
            else:
                return "poor"
        elif distance <= 0.3:
            if ce <= 5:
                return "fair"
            else:
                return "poor"
        else:
            return "poor"

    def _classify_cohesion(self, lcom: float, lcom4: float, tcc: float, lcc: float) -> str:
        """Classify cohesion quality.

        Args:
            lcom: LCOM score (higher is worse)
            lcom4: LCOM4 score (1 is best)
            tcc: TCC score (higher is better)
            lcc: LCC score (higher is better)

        Returns:
            Quality score: 'excellent', 'good', 'fair', 'poor'
        """
        # Primary metric: LCOM4 (should be 1)
        # Secondary: TCC (direct connections)
        # Tertiary: LCC (indirect connections)

        if lcom4 <= 1.0:
            if tcc >= 0.7:
                return "excellent"
            elif tcc >= 0.5:
                return "good"
            elif tcc >= 0.3:
                return "fair"
            else:
                return "fair" if lcc >= 0.5 else "poor"
        elif lcom4 <= 2.0:
            if tcc >= 0.5:
                return "good"
            elif tcc >= 0.3:
                return "fair"
            else:
                return "poor"
        elif lcom4 <= 3.0:
            if tcc >= 0.4:
                return "fair"
            else:
                return "poor"
        else:
            return "poor"

    def generate_report(
        self,
        coupling: list[CouplingMetrics],
        cohesion: list[CohesionMetrics],
    ) -> str:
        """Generate a text report of coupling and cohesion metrics.

        Args:
            coupling: List of coupling metrics
            cohesion: List of cohesion metrics

        Returns:
            Formatted text report
        """
        lines: list[str] = []

        lines.append("=" * 80)
        lines.append("COUPLING & COHESION ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Coupling section
        lines.append("COUPLING METRICS")
        lines.append("-" * 80)
        lines.append("")

        if coupling:
            # Sort by efferent coupling (highest first)
            sorted_coupling = sorted(coupling, key=lambda x: x.efferent_coupling, reverse=True)

            for metric in sorted_coupling[:20]:  # Top 20
                lines.append(f"Module: {metric.name}")
                lines.append(f"  File: {metric.file_path}")
                lines.append(f"  Afferent Coupling (Ca): {metric.afferent_coupling}")
                lines.append(f"  Efferent Coupling (Ce): {metric.efferent_coupling}")
                lines.append(f"  Instability (I): {metric.instability:.3f}")
                lines.append(f"  Abstractness (A): {metric.abstractness:.3f}")
                lines.append(f"  Distance from Main: {metric.distance_from_main:.3f}")
                lines.append(f"  Score: {metric.coupling_score.upper()}")
                lines.append("")
        else:
            lines.append("No modules analyzed.")
            lines.append("")

        # Cohesion section
        lines.append("")
        lines.append("COHESION METRICS")
        lines.append("-" * 80)
        lines.append("")

        if cohesion:
            # Sort by LCOM (highest first - worst cohesion)
            sorted_cohesion = sorted(cohesion, key=lambda x: x.lcom, reverse=True)

            for metric in sorted_cohesion[:20]:  # Top 20
                lines.append(f"Class: {metric.name}")
                lines.append(f"  File: {metric.file_path}")
                lines.append(f"  LCOM: {metric.lcom:.3f} (lower is better)")
                lines.append(f"  LCOM4: {metric.lcom4:.1f} (1 is ideal)")
                lines.append(f"  TCC: {metric.tcc:.3f} (higher is better)")
                lines.append(f"  LCC: {metric.lcc:.3f} (higher is better)")
                lines.append(f"  Score: {metric.cohesion_score.upper()}")
                lines.append("")
        else:
            lines.append("No classes analyzed.")
            lines.append("")

        # Summary statistics
        lines.append("")
        lines.append("SUMMARY STATISTICS")
        lines.append("-" * 80)
        lines.append("")

        if coupling:
            avg_ce = sum(c.efferent_coupling for c in coupling) / len(coupling)
            avg_ca = sum(c.afferent_coupling for c in coupling) / len(coupling)
            avg_instability = sum(c.instability for c in coupling) / len(coupling)
            avg_distance = sum(c.distance_from_main for c in coupling) / len(coupling)

            lines.append(f"Modules analyzed: {len(coupling)}")
            lines.append(f"Average Efferent Coupling: {avg_ce:.2f}")
            lines.append(f"Average Afferent Coupling: {avg_ca:.2f}")
            lines.append(f"Average Instability: {avg_instability:.3f}")
            lines.append(f"Average Distance from Main: {avg_distance:.3f}")
            lines.append("")

            poor_coupling = len([c for c in coupling if c.coupling_score == "poor"])
            if poor_coupling > 0:
                lines.append(f"⚠️  {poor_coupling} modules with poor coupling")
                lines.append("")

        if cohesion:
            avg_lcom = sum(c.lcom for c in cohesion) / len(cohesion)
            avg_lcom4 = sum(c.lcom4 for c in cohesion) / len(cohesion)
            avg_tcc = sum(c.tcc for c in cohesion) / len(cohesion)

            lines.append(f"Classes analyzed: {len(cohesion)}")
            lines.append(f"Average LCOM: {avg_lcom:.3f}")
            lines.append(f"Average LCOM4: {avg_lcom4:.2f}")
            lines.append(f"Average TCC: {avg_tcc:.3f}")
            lines.append("")

            poor_cohesion = len([c for c in cohesion if c.cohesion_score == "poor"])
            if poor_cohesion > 0:
                lines.append(f"⚠️  {poor_cohesion} classes with poor cohesion")
                lines.append("")

        lines.append("=" * 80)

        return "\n".join(lines)
