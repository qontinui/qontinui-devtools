"""
Report Aggregator for collecting data from all analysis tools.

This module runs all analysis tools and aggregates their results into a single ReportData object.
"""

import html
from datetime import datetime
from pathlib import Path
from typing import Any

from .html_reporter import ReportData, ReportSection
from .charts import create_bar_chart, create_pie_chart, create_line_chart


class ReportAggregator:
    """Aggregate results from all analysis tools."""

    def __init__(self, project_path: str, verbose: bool = False) -> None:
        """
        Initialize the report aggregator.

        Args:
            project_path: Path to the project to analyze
            verbose: Enable verbose logging
        """
        self.project_path = Path(project_path)
        self.verbose = verbose
        self.results: dict[str, Any] = {}

        if not self.project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

    def run_all_analyses(self) -> ReportData:
        """
        Run all analysis tools and aggregate results.

        Returns:
            ReportData object with aggregated results
        """
        if self.verbose:
            print(f"Running analyses on: {self.project_path}")

        # Initialize report data
        report_data = ReportData(
            project_name=self.project_path.name,
            analysis_date=datetime.now(),
            project_path=str(self.project_path),
            version="1.0.0",
        )

        # Run analyses
        try:
            self.results["imports"] = self._run_import_analysis()
            if self.verbose:
                print("✓ Import analysis complete")
        except Exception as e:
            if self.verbose:
                print(f"✗ Import analysis failed: {e}")
            self.results["imports"] = {"error": str(e)}

        try:
            self.results["architecture"] = self._run_architecture_analysis()
            if self.verbose:
                print("✓ Architecture analysis complete")
        except Exception as e:
            if self.verbose:
                print(f"✗ Architecture analysis failed: {e}")
            self.results["architecture"] = {"error": str(e)}

        try:
            self.results["quality"] = self._run_quality_checks()
            if self.verbose:
                print("✓ Quality checks complete")
        except Exception as e:
            if self.verbose:
                print(f"✗ Quality checks failed: {e}")
            self.results["quality"] = {"error": str(e)}

        try:
            self.results["concurrency"] = self._run_concurrency_analysis()
            if self.verbose:
                print("✓ Concurrency analysis complete")
        except Exception as e:
            if self.verbose:
                print(f"✗ Concurrency analysis failed: {e}")
            self.results["concurrency"] = {"error": str(e)}

        # Create report data
        return self._create_report_data(report_data)

    def _run_import_analysis(self) -> dict[str, Any]:
        """Run import analysis using CircularDependencyDetector."""
        try:
            from ..import_analysis import CircularDependencyDetector

            detector = CircularDependencyDetector(str(self.project_path))
            cycles = detector.analyze()

            return {
                "circular_dependencies": len(cycles),
                "cycles": cycles,
                "graph": detector.graph if hasattr(detector, "graph") else None,
                "total_imports": len(
                    detector.graph.edges() if hasattr(detector, "graph") else []
                ),
            }
        except ImportError:
            return {"error": "Import analysis module not available"}

    def _run_architecture_analysis(self) -> dict[str, Any]:
        """Run architecture analysis using GodClassDetector and SRPAnalyzer."""
        result: dict[str, Any] = {}

        try:
            from ..architecture import GodClassDetector

            detector = GodClassDetector()
            god_classes = []

            # Scan all Python files
            for py_file in self.project_path.rglob("*.py"):
                try:
                    classes = detector.analyze_file(str(py_file))
                    god_classes.extend(classes)
                except Exception:
                    pass

            result["god_classes"] = len(god_classes)
            result["god_class_details"] = god_classes
        except ImportError:
            result["god_classes"] = 0
            result["error"] = "Architecture analysis module not available"

        try:
            from ..architecture import SRPAnalyzer

            analyzer = SRPAnalyzer()
            violations = []

            # Scan all Python files
            for py_file in self.project_path.rglob("*.py"):
                try:
                    file_violations = analyzer.analyze_file(str(py_file))
                    violations.extend(file_violations)
                except Exception:
                    pass

            result["srp_violations"] = len(violations)
            result["srp_details"] = violations
        except ImportError:
            result["srp_violations"] = 0

        return result

    def _run_quality_checks(self) -> dict[str, Any]:
        """Run code quality checks."""
        result: dict[str, Any] = {
            "total_files": 0,
            "total_lines": 0,
            "total_functions": 0,
            "total_classes": 0,
            "issues": [],
        }

        # Count files and lines
        for py_file in self.project_path.rglob("*.py"):
            if "test" in str(py_file):
                continue

            try:
                content = py_file.read_text(encoding="utf-8")
                result["total_files"] += 1
                result["total_lines"] += len(content.splitlines())

                # Count functions and classes (simple regex)
                result["total_functions"] += content.count("\ndef ")
                result["total_classes"] += content.count("\nclass ")

                # Check for common issues
                if "import *" in content:
                    result["issues"].append(
                        {
                            "file": str(py_file),
                            "issue": "Wildcard import detected",
                            "severity": "warning",
                        }
                    )

                if "# TODO" in content or "# FIXME" in content:
                    result["issues"].append(
                        {
                            "file": str(py_file),
                            "issue": "TODO/FIXME comment found",
                            "severity": "info",
                        }
                    )

            except Exception:
                pass

        return result

    def _run_concurrency_analysis(self) -> dict[str, Any]:
        """Run concurrency analysis using RaceConditionDetector."""
        try:
            from ..concurrency import RaceConditionDetector

            detector = RaceConditionDetector()
            race_conditions = []

            # Scan all Python files
            for py_file in self.project_path.rglob("*.py"):
                try:
                    races = detector.analyze_file(str(py_file))
                    race_conditions.extend(races)
                except Exception:
                    pass

            return {
                "race_conditions": len(race_conditions),
                "race_details": race_conditions,
            }
        except ImportError:
            return {"race_conditions": 0, "error": "Concurrency module not available"}

    def _create_report_data(self, report_data: ReportData) -> ReportData:
        """
        Create report data from analysis results.

        Args:
            report_data: Initial report data

        Returns:
            Complete ReportData with sections
        """
        # Add summary metrics
        report_data.summary_metrics = {
            "files_analyzed": self.results.get("quality", {}).get("total_files", 0),
            "total_lines": self.results.get("quality", {}).get("total_lines", 0),
            "circular_dependencies": self.results.get("imports", {}).get(
                "circular_dependencies", 0
            ),
            "god_classes": self.results.get("architecture", {}).get("god_classes", 0),
            "race_conditions": self.results.get("concurrency", {}).get(
                "race_conditions", 0
            ),
            "srp_violations": self.results.get("architecture", {}).get(
                "srp_violations", 0
            ),
            "critical_issues": self._count_critical_issues(),
        }

        # Create sections
        report_data.add_section(self._create_import_section())
        report_data.add_section(self._create_architecture_section())
        report_data.add_section(self._create_quality_section())
        report_data.add_section(self._create_concurrency_section())
        report_data.add_section(self._create_recommendations_section())

        return report_data

    def _count_critical_issues(self) -> int:
        """Count critical issues across all analyses."""
        count = 0

        # Circular dependencies are critical
        count += self.results.get("imports", {}).get("circular_dependencies", 0)

        # Race conditions are critical
        count += self.results.get("concurrency", {}).get("race_conditions", 0)

        # Multiple god classes is critical
        god_classes = self.results.get("architecture", {}).get("god_classes", 0)
        if god_classes > 3:
            count += god_classes - 3

        return count

    def _create_import_section(self) -> ReportSection:
        """Create import analysis section."""
        imports = self.results.get("imports", {})
        circular_deps = imports.get("circular_dependencies", 0)
        cycles = imports.get("cycles", [])

        if circular_deps == 0:
            severity = "success"
            content = "<p>✓ No circular dependencies detected. Import structure is clean.</p>"
        elif circular_deps <= 2:
            severity = "warning"
            content = f"<p>⚠ Found {circular_deps} circular dependencies:</p><ul>"
            for cycle in cycles[:2]:
                cycle_str = " → ".join(html.escape(str(c)) for c in cycle)
                content += f"<li><code>{cycle_str}</code></li>"
            content += "</ul>"
        else:
            severity = "error"
            content = f"<p>❌ Found {circular_deps} circular dependencies (showing first 5):</p><ul>"
            for cycle in cycles[:5]:
                cycle_str = " → ".join(html.escape(str(c)) for c in cycle)
                content += f"<li><code>{cycle_str}</code></li>"
            content += "</ul>"
            content += "<p><strong>Action Required:</strong> Refactor imports to break circular dependencies.</p>"

        metrics = {
            "circular_dependencies": circular_deps,
            "total_imports": imports.get("total_imports", 0),
        }

        return ReportSection(
            id="imports",
            title="Import Analysis",
            content=content,
            severity=severity,
            metrics=metrics,
        )

    def _create_architecture_section(self) -> ReportSection:
        """Create architecture analysis section."""
        arch = self.results.get("architecture", {})
        god_classes = arch.get("god_classes", 0)
        srp_violations = arch.get("srp_violations", 0)
        god_class_details = arch.get("god_class_details", [])

        if god_classes == 0 and srp_violations == 0:
            severity = "success"
            content = "<p>✓ Architecture is clean. No god classes or SRP violations detected.</p>"
        elif god_classes <= 2:
            severity = "warning"
            content = f"<p>⚠ Found {god_classes} god classes and {srp_violations} SRP violations.</p>"
            if god_class_details:
                content += "<h3>God Classes:</h3><ul>"
                for cls in god_class_details[:3]:
                    if hasattr(cls, "class_name"):
                        content += f"<li><code>{html.escape(cls.class_name)}</code> - {cls.method_count} methods</li>"
                    else:
                        content += f"<li>{html.escape(str(cls))}</li>"
                content += "</ul>"
        else:
            severity = "error"
            content = f"<p>❌ Found {god_classes} god classes and {srp_violations} SRP violations.</p>"
            content += "<p><strong>Critical:</strong> Multiple god classes detected. Consider refactoring.</p>"
            if god_class_details:
                content += "<h3>Top God Classes:</h3><ul>"
                for cls in god_class_details[:5]:
                    if hasattr(cls, "class_name"):
                        content += f"<li><code>{html.escape(cls.class_name)}</code> - {cls.method_count} methods</li>"
                    else:
                        content += f"<li>{html.escape(str(cls))}</li>"
                content += "</ul>"

        metrics = {
            "god_classes": god_classes,
            "srp_violations": srp_violations,
        }

        return ReportSection(
            id="architecture",
            title="Architecture Quality",
            content=content,
            severity=severity,
            metrics=metrics,
        )

    def _create_quality_section(self) -> ReportSection:
        """Create code quality section."""
        quality = self.results.get("quality", {})
        total_files = quality.get("total_files", 0)
        total_lines = quality.get("total_lines", 0)
        issues = quality.get("issues", [])

        severity = "success" if len(issues) < 5 else ("warning" if len(issues) < 10 else "error")

        content = f"<p>Analyzed {total_files} files with {total_lines:,} lines of code.</p>"

        if len(issues) == 0:
            content += "<p>✓ No code quality issues detected.</p>"
        else:
            content += f"<p>Found {len(issues)} code quality issues:</p><ul>"
            for issue in issues[:10]:
                severity_icon = "⚠" if issue.get("severity") == "warning" else "ℹ"
                file_path = Path(issue["file"]).name
                content += f"<li>{severity_icon} <code>{html.escape(file_path)}</code>: {html.escape(issue['issue'])}</li>"
            if len(issues) > 10:
                content += f"<li>... and {len(issues) - 10} more</li>"
            content += "</ul>"

        metrics = {
            "total_files": total_files,
            "total_lines": total_lines,
            "total_issues": len(issues),
        }

        return ReportSection(
            id="quality",
            title="Code Quality",
            content=content,
            severity=severity,
            metrics=metrics,
        )

    def _create_concurrency_section(self) -> ReportSection:
        """Create concurrency analysis section."""
        concurrency = self.results.get("concurrency", {})
        race_conditions = concurrency.get("race_conditions", 0)
        race_details = concurrency.get("race_details", [])

        if race_conditions == 0:
            severity = "success"
            content = "<p>✓ No race conditions detected in concurrent code.</p>"
        elif race_conditions <= 2:
            severity = "warning"
            content = f"<p>⚠ Found {race_conditions} potential race conditions:</p><ul>"
            for race in race_details[:2]:
                if hasattr(race, "description"):
                    content += f"<li>{html.escape(race.description)}</li>"
                else:
                    content += f"<li>{html.escape(str(race))}</li>"
            content += "</ul>"
        else:
            severity = "error"
            content = f"<p>❌ Found {race_conditions} potential race conditions:</p><ul>"
            for race in race_details[:5]:
                if hasattr(race, "description"):
                    content += f"<li>{html.escape(race.description)}</li>"
                else:
                    content += f"<li>{html.escape(str(race))}</li>"
            content += "</ul>"
            content += "<p><strong>Critical:</strong> Add proper synchronization to prevent data races.</p>"

        metrics = {
            "race_conditions": race_conditions,
        }

        return ReportSection(
            id="concurrency",
            title="Concurrency Analysis",
            content=content,
            severity=severity,
            metrics=metrics,
        )

    def _create_recommendations_section(self) -> ReportSection:
        """Create recommendations section."""
        recommendations = []

        # Check circular dependencies
        circular_deps = self.results.get("imports", {}).get("circular_dependencies", 0)
        if circular_deps > 0:
            recommendations.append(
                "🔄 <strong>Break circular dependencies</strong>: Refactor import structure to eliminate cycles."
            )

        # Check god classes
        god_classes = self.results.get("architecture", {}).get("god_classes", 0)
        if god_classes > 0:
            recommendations.append(
                "🏛 <strong>Refactor god classes</strong>: Split large classes into smaller, focused classes."
            )

        # Check race conditions
        race_conditions = self.results.get("concurrency", {}).get("race_conditions", 0)
        if race_conditions > 0:
            recommendations.append(
                "🔒 <strong>Add synchronization</strong>: Use locks or other mechanisms to prevent race conditions."
            )

        # Check SRP violations
        srp_violations = self.results.get("architecture", {}).get("srp_violations", 0)
        if srp_violations > 0:
            recommendations.append(
                "📐 <strong>Follow Single Responsibility Principle</strong>: Each class should have one reason to change."
            )

        if not recommendations:
            content = "<p>✓ Excellent! No major issues found. Keep up the good work!</p>"
            content += "<h3>Best Practices:</h3><ul>"
            content += "<li>Continue writing unit tests</li>"
            content += "<li>Document complex code sections</li>"
            content += "<li>Regular code reviews</li>"
            content += "</ul>"
            severity = "success"
        else:
            content = "<h3>Priority Recommendations:</h3><ol>"
            for rec in recommendations:
                content += f"<li>{rec}</li>"
            content += "</ol>"
            severity = "warning" if len(recommendations) <= 2 else "error"

        return ReportSection(
            id="recommendations",
            title="Recommendations",
            content=content,
            severity=severity,
            metrics={"total_recommendations": len(recommendations)},
        )
