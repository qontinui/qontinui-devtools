"""Regression detection for identifying behavioral changes between code versions."""

import json
import logging
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import (ChangeType, FunctionSignature, PerformanceMetric,
                     RegressionIssue, RegressionReport, RiskLevel,
                     SeverityLevel)
from .snapshot import APISnapshot

logger = logging.getLogger(__name__)


class RegressionDetector:
    """Detects regressions and breaking changes between code versions."""

    def __init__(
        self, snapshot_dir: Path | None = None, performance_threshold: float = 0.10
    ) -> None:
        """
        Initialize regression detector.

        Args:
            snapshot_dir: Directory to store snapshots (default: .regression_snapshots)
            performance_threshold: Threshold for performance regressions (default: 10%)
        """
        self.snapshot_dir = snapshot_dir or Path(".regression_snapshots")
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.performance_threshold = performance_threshold
        self.baseline_snapshot: APISnapshot | None = None
        self.current_snapshot: APISnapshot | None = None

    def create_snapshot(
        self, source_path: Path | str, version: str, save: bool = True
    ) -> APISnapshot:
        """
        Create API snapshot for a code version.

        Args:
            source_path: Path to source code directory
            version: Version identifier
            save: Whether to save snapshot to disk

        Returns:
            Created snapshot
        """
        source_path = Path(source_path)
        snapshot = APISnapshot()
        snapshot.create_snapshot(source_path, version)

        if save:
            snapshot_file = self.snapshot_dir / f"snapshot_{version}.json"
            snapshot.save_snapshot(snapshot_file)
            logger.info(f"Snapshot saved: {snapshot_file}")

        return snapshot

    def load_snapshot(self, version: str) -> APISnapshot:
        """
        Load snapshot from disk.

        Args:
            version: Version identifier

        Returns:
            Loaded snapshot
        """
        snapshot_file = self.snapshot_dir / f"snapshot_{version}.json"
        snapshot = APISnapshot()
        snapshot.load_snapshot(snapshot_file)
        return snapshot

    def detect_regressions(
        self,
        source_path: Path | str,
        baseline: str | APISnapshot,
        current_version: str = "current",
    ) -> RegressionReport:
        """
        Detect regressions between baseline and current code.

        Args:
            source_path: Path to current source code
            baseline: Baseline version identifier or snapshot
            current_version: Current version identifier

        Returns:
            Regression report with detected issues
        """
        # Load baseline snapshot
        if isinstance(baseline, str):
            self.baseline_snapshot = self.load_snapshot(baseline)
            baseline_version = baseline
        else:
            self.baseline_snapshot = baseline
            baseline_version = baseline.metadata.get("version", "baseline")

        # Create current snapshot
        self.current_snapshot = self.create_snapshot(source_path, current_version, save=True)

        # Detect various types of regressions
        issues: list[RegressionIssue] = []

        # API breaking changes
        issues.extend(self._detect_breaking_changes())

        # Behavioral changes (parameter/return type changes)
        issues.extend(self._detect_behavioral_changes())

        # Count issue types
        breaking_count = sum(1 for i in issues if i.change_type == ChangeType.BREAKING)
        behavioral_count = sum(1 for i in issues if i.change_type == ChangeType.BEHAVIORAL)
        performance_count = sum(1 for i in issues if i.change_type == ChangeType.PERFORMANCE)
        dependency_count = sum(1 for i in issues if i.change_type == ChangeType.DEPENDENCY)

        report = RegressionReport(
            baseline_version=baseline_version,
            current_version=current_version,
            issues=issues,
            breaking_count=breaking_count,
            behavioral_count=behavioral_count,
            performance_count=performance_count,
            dependency_count=dependency_count,
            total_functions_compared=len(self.baseline_snapshot.functions),
            total_classes_compared=len(self.baseline_snapshot.classes),
            timestamp=datetime.now().isoformat(),
        )

        report.summary = self._generate_summary(report)
        return report

    def _detect_breaking_changes(self) -> list[RegressionIssue]:
        """Detect API breaking changes (removed/renamed functions/classes)."""
        issues: list[RegressionIssue] = []

        if not self.baseline_snapshot or not self.current_snapshot:
            return issues

        # Compare functions
        added_funcs, removed_funcs, modified_funcs, _ = self.current_snapshot.compare_snapshots(
            self.baseline_snapshot
        )

        # Removed functions are breaking changes
        for func_key in removed_funcs:
            old_sig = self.baseline_snapshot.get_function(func_key)
            if old_sig:
                issue = RegressionIssue(
                    change_type=ChangeType.BREAKING,
                    risk_level=RiskLevel.CRITICAL,
                    description=f"Function '{func_key}' was removed",
                    old_signature=old_sig,
                    new_signature=None,
                    impact_description=(
                        f"Calls to {func_key}() will fail. " f"This is a breaking API change."
                    ),
                    migration_guide=(
                        f"1. Search codebase for calls to {func_key}()\n"
                        f"2. Replace with alternative implementation or remove calls\n"
                        f"3. Update tests and documentation"
                    ),
                    severity=SeverityLevel.SEVERE,
                    affected_modules=[old_sig.module_path],
                )
                issues.append(issue)

        # Compare classes
        added_cls, removed_cls, modified_cls, _ = self.current_snapshot.compare_classes(
            self.baseline_snapshot
        )

        # Removed classes are breaking changes
        for cls_key in removed_cls:
            old_cls = self.baseline_snapshot.get_class(cls_key)
            if old_cls:
                issue = RegressionIssue(
                    change_type=ChangeType.BREAKING,
                    risk_level=RiskLevel.CRITICAL,
                    description=f"Class '{cls_key}' was removed",
                    old_signature=None,
                    new_signature=None,
                    impact_description=(
                        f"Instantiation and usage of {cls_key} will fail. "
                        f"This is a breaking API change."
                    ),
                    migration_guide=(
                        f"1. Search codebase for usage of {cls_key}\n"
                        f"2. Replace with alternative class or refactor code\n"
                        f"3. Update imports, tests, and documentation"
                    ),
                    severity=SeverityLevel.SEVERE,
                    affected_modules=[old_cls.module_path],
                )
                issues.append(issue)

        return issues

    def _detect_behavioral_changes(self) -> list[RegressionIssue]:
        """Detect behavioral changes (signature modifications)."""
        issues: list[RegressionIssue] = []

        if not self.baseline_snapshot or not self.current_snapshot:
            return issues

        _, _, modified_funcs, _ = self.current_snapshot.compare_snapshots(self.baseline_snapshot)

        for func_key in modified_funcs:
            old_sig = self.baseline_snapshot.get_function(func_key)
            new_sig = self.current_snapshot.get_function(func_key)

            if not old_sig or not new_sig:
                continue

            # Check for async/sync changes first (most critical)
            if old_sig.is_async != new_sig.is_async:
                issue = RegressionIssue(
                    change_type=ChangeType.BREAKING,
                    risk_level=RiskLevel.CRITICAL,
                    description=(
                        f"Function '{func_key}' changed from "
                        f"{'async' if old_sig.is_async else 'sync'} to "
                        f"{'async' if new_sig.is_async else 'sync'}"
                    ),
                    old_signature=old_sig,
                    new_signature=new_sig,
                    impact_description=(
                        "Async/sync change requires all call sites to be updated. "
                        "This is a breaking change."
                    ),
                    migration_guide=(
                        f"1. Add/remove 'await' keyword at all call sites\n"
                        f"2. Ensure calling functions are {'async' if new_sig.is_async else 'sync'}\n"
                        f"3. Update event loop handling if needed"
                    ),
                    severity=SeverityLevel.SEVERE,
                    affected_modules=[new_sig.module_path],
                )
                issues.append(issue)
                continue

            # Check for parameter changes
            if old_sig.parameters != new_sig.parameters:
                risk_level, severity = self._assess_parameter_change(old_sig, new_sig)

                issue = RegressionIssue(
                    change_type=(
                        ChangeType.BREAKING
                        if risk_level == RiskLevel.CRITICAL
                        else ChangeType.BEHAVIORAL
                    ),
                    risk_level=risk_level,
                    description=f"Function '{func_key}' signature changed",
                    old_signature=old_sig,
                    new_signature=new_sig,
                    impact_description=self._describe_parameter_impact(old_sig, new_sig),
                    migration_guide=self._generate_parameter_migration(old_sig, new_sig),
                    severity=severity,
                    affected_modules=[new_sig.module_path],
                )
                issues.append(issue)

            # Check for return type changes
            elif old_sig.return_type != new_sig.return_type:
                risk_level = self._assess_return_type_change(old_sig, new_sig)

                issue = RegressionIssue(
                    change_type=ChangeType.BEHAVIORAL,
                    risk_level=risk_level,
                    description=f"Function '{func_key}' return type changed",
                    old_signature=old_sig,
                    new_signature=new_sig,
                    impact_description=(
                        f"Return type changed from {old_sig.return_type} "
                        f"to {new_sig.return_type}. Code expecting the old type may break."
                    ),
                    migration_guide=(
                        f"1. Review all call sites that use the return value\n"
                        f"2. Update code to handle new return type: {new_sig.return_type}\n"
                        f"3. Update tests to verify new behavior"
                    ),
                    severity=SeverityLevel.MODERATE,
                    affected_modules=[new_sig.module_path],
                )
                issues.append(issue)

        return issues

    def _assess_parameter_change(
        self, old_sig: FunctionSignature, new_sig: FunctionSignature
    ) -> tuple[RiskLevel, SeverityLevel]:
        """Assess risk level of parameter changes."""
        old_params = set(old_sig.parameters)
        new_params = set(new_sig.parameters)

        # Removed parameters = breaking change
        removed = old_params - new_params
        if removed:
            return RiskLevel.CRITICAL, SeverityLevel.SEVERE

        # Added required parameters = breaking change
        # (simplified check - assumes non-default params are required)
        added = new_params - old_params
        if added:
            # Check if any added param lacks default value
            has_required = any("=" not in param for param in added)
            if has_required:
                return RiskLevel.CRITICAL, SeverityLevel.SEVERE
            else:
                return RiskLevel.MEDIUM, SeverityLevel.MINOR

        # Parameter order change
        if old_sig.parameters != new_sig.parameters:
            return RiskLevel.HIGH, SeverityLevel.MODERATE

        return RiskLevel.LOW, SeverityLevel.MINOR

    def _assess_return_type_change(
        self, old_sig: FunctionSignature, new_sig: FunctionSignature
    ) -> RiskLevel:
        """Assess risk level of return type changes."""
        # None -> something or something -> None is high risk
        if (old_sig.return_type is None) != (new_sig.return_type is None):
            return RiskLevel.HIGH

        # Type change is medium risk
        return RiskLevel.MEDIUM

    def _describe_parameter_impact(
        self, old_sig: FunctionSignature, new_sig: FunctionSignature
    ) -> str:
        """Describe impact of parameter changes."""
        old_params = set(old_sig.parameters)
        new_params = set(new_sig.parameters)

        removed = old_params - new_params
        added = new_params - old_params

        parts: list[Any] = []
        if removed:
            parts.append(f"Removed parameters: {', '.join(removed)}")
        if added:
            parts.append(f"Added parameters: {', '.join(added)}")
        if not removed and not added and old_sig.parameters != new_sig.parameters:
            parts.append("Parameter order changed")

        return ". ".join(parts) + ". Existing code may break or behave unexpectedly."

    def _generate_parameter_migration(
        self, old_sig: FunctionSignature, new_sig: FunctionSignature
    ) -> str:
        """Generate migration guide for parameter changes."""
        lines = [
            f"1. Search for all calls to {old_sig.name}()",
            "2. Update call signatures:",
        ]

        old_params = set(old_sig.parameters)
        new_params = set(new_sig.parameters)
        removed = old_params - new_params
        added = new_params - old_params

        if removed:
            lines.append(f"   - Remove parameters: {', '.join(removed)}")
        if added:
            lines.append(f"   - Add parameters: {', '.join(added)}")
        if old_sig.parameters != new_sig.parameters:
            lines.append(f"   - Old: {old_sig.name}({', '.join(old_sig.parameters)})")
            lines.append(f"   - New: {new_sig.name}({', '.join(new_sig.parameters)})")

        lines.append("3. Update tests to cover new signature")
        return "\n".join(lines)

    def detect_performance_regressions(
        self,
        baseline_metrics: dict[str, PerformanceMetric],
        current_metrics: dict[str, PerformanceMetric],
    ) -> list[RegressionIssue]:
        """
        Detect performance regressions between metric sets.

        Args:
            baseline_metrics: Baseline performance metrics
            current_metrics: Current performance metrics

        Returns:
            List of performance regression issues
        """
        issues: list[RegressionIssue] = []

        for func_key, current_metric in current_metrics.items():
            if func_key not in baseline_metrics:
                continue

            baseline_metric = baseline_metrics[func_key]
            delta = (
                current_metric.execution_time_ms - baseline_metric.execution_time_ms
            ) / baseline_metric.execution_time_ms

            if delta > self.performance_threshold:
                risk_level = self._assess_performance_risk(delta)
                severity = self._assess_performance_severity(delta)

                issue = RegressionIssue(
                    change_type=ChangeType.PERFORMANCE,
                    risk_level=risk_level,
                    description=f"Performance regression in '{func_key}'",
                    old_signature=None,
                    new_signature=None,
                    impact_description=(
                        f"Execution time increased by {delta * 100:.1f}% "
                        f"({baseline_metric.execution_time_ms:.2f}ms -> "
                        f"{current_metric.execution_time_ms:.2f}ms)"
                    ),
                    migration_guide=(
                        f"1. Profile {func_key}() to identify bottlenecks\n"
                        f"2. Review recent changes to this function\n"
                        f"3. Consider optimization or algorithmic improvements\n"
                        f"4. Add performance tests to prevent future regressions"
                    ),
                    severity=severity,
                    affected_modules=[current_metric.module_path],
                    performance_delta=delta,
                    old_performance=baseline_metric,
                    new_performance=current_metric,
                )
                issues.append(issue)

        return issues

    def _assess_performance_risk(self, delta: float) -> RiskLevel:
        """Assess risk level based on performance degradation."""
        if delta > 0.50:  # >50% slower
            return RiskLevel.CRITICAL
        elif delta > 0.25:  # >25% slower
            return RiskLevel.HIGH
        elif delta > 0.10:  # >10% slower
            return RiskLevel.MEDIUM
        return RiskLevel.LOW

    def _assess_performance_severity(self, delta: float) -> SeverityLevel:
        """Assess severity based on performance degradation."""
        if delta > 0.50:
            return SeverityLevel.SEVERE
        elif delta > 0.25:
            return SeverityLevel.MODERATE
        return SeverityLevel.MINOR

    def compare_with_git(
        self,
        repo_path: Path | str,
        baseline_ref: str,
        current_ref: str = "HEAD",
        source_subdir: str = "",
    ) -> RegressionReport:
        """
        Compare two git references for regressions.

        Args:
            repo_path: Path to git repository
            baseline_ref: Baseline git reference (commit/branch/tag)
            current_ref: Current git reference
            source_subdir: Subdirectory containing source code

        Returns:
            Regression report
        """
        repo_path = Path(repo_path)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Checkout baseline
            baseline_path = temp_path / "baseline"
            self._git_checkout(repo_path, baseline_ref, baseline_path)
            baseline_source = baseline_path / source_subdir if source_subdir else baseline_path
            baseline_snapshot = self.create_snapshot(baseline_source, baseline_ref, save=False)

            # Checkout current
            current_path = temp_path / "current"
            self._git_checkout(repo_path, current_ref, current_path)
            current_source = current_path / source_subdir if source_subdir else current_path

            # Detect regressions
            return self.detect_regressions(current_source, baseline_snapshot, current_ref)

    def _git_checkout(self, repo_path: Path, ref: str, output_path: Path) -> None:
        """Checkout git reference to output path."""
        try:
            # Create worktree
            subprocess.run(
                ["git", "-C", str(repo_path), "worktree", "add", str(output_path), ref],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Git checkout failed: {e.stderr}")
            raise

    def detect_dependency_changes(
        self, baseline_deps: dict[str, str], current_deps: dict[str, str]
    ) -> list[RegressionIssue]:
        """
        Detect dependency version changes.

        Args:
            baseline_deps: Baseline dependencies {package: version}
            current_deps: Current dependencies {package: version}

        Returns:
            List of dependency change issues
        """
        issues: list[RegressionIssue] = []

        # Check for removed dependencies
        for pkg, version in baseline_deps.items():
            if pkg not in current_deps:
                issue = RegressionIssue(
                    change_type=ChangeType.DEPENDENCY,
                    risk_level=RiskLevel.HIGH,
                    description=f"Dependency '{pkg}' was removed",
                    old_signature=None,
                    new_signature=None,
                    impact_description=(
                        f"Package {pkg} (v{version}) is no longer a dependency. "
                        "Code relying on this package may break."
                    ),
                    migration_guide=(
                        f"1. Search for imports of {pkg}\n"
                        f"2. Either add {pkg} back or refactor code\n"
                        f"3. Update requirements and documentation"
                    ),
                    severity=SeverityLevel.MODERATE,
                )
                issues.append(issue)

        # Check for version changes
        for pkg, new_version in current_deps.items():
            if pkg in baseline_deps:
                old_version = baseline_deps[pkg]
                if old_version != new_version:
                    risk_level = self._assess_version_change_risk(old_version, new_version)

                    issue = RegressionIssue(
                        change_type=ChangeType.DEPENDENCY,
                        risk_level=risk_level,
                        description=f"Dependency '{pkg}' version changed",
                        old_signature=None,
                        new_signature=None,
                        impact_description=(
                            f"Package {pkg} upgraded from v{old_version} to v{new_version}. "
                            "API changes in the package may affect compatibility."
                        ),
                        migration_guide=(
                            f"1. Review {pkg} changelog between versions\n"
                            f"2. Test all functionality using {pkg}\n"
                            f"3. Update code for any breaking changes\n"
                            f"4. Update documentation and requirements"
                        ),
                        severity=SeverityLevel.MINOR,
                    )
                    issues.append(issue)

        return issues

    def _assess_version_change_risk(self, old_version: str, new_version: str) -> RiskLevel:
        """Assess risk of dependency version change."""
        try:
            old_parts = [int(x) for x in old_version.split(".")[:3]]
            new_parts = [int(x) for x in new_version.split(".")[:3]]

            # Major version change
            if len(old_parts) > 0 and len(new_parts) > 0 and old_parts[0] != new_parts[0]:
                return RiskLevel.HIGH

            # Minor version change
            if len(old_parts) > 1 and len(new_parts) > 1 and old_parts[1] != new_parts[1]:
                return RiskLevel.MEDIUM

            # Patch version change
            return RiskLevel.LOW
        except (ValueError, IndexError):
            return RiskLevel.MEDIUM

    def calculate_risk_score(self, report: RegressionReport) -> float:
        """
        Calculate overall risk score for a regression report.

        Args:
            report: Regression report

        Returns:
            Risk score between 0 (no risk) and 100 (critical risk)
        """
        weights = {
            RiskLevel.CRITICAL: 25.0,
            RiskLevel.HIGH: 15.0,
            RiskLevel.MEDIUM: 8.0,
            RiskLevel.LOW: 3.0,
        }

        score = 0.0
        for issue in report.issues:
            score += weights.get(issue.risk_level, 0.0)

        # Cap at 100
        return min(score, 100.0)

    def _generate_summary(self, report: RegressionReport) -> str:
        """Generate human-readable summary of report."""
        lines = [
            f"Regression Analysis: {report.baseline_version} -> {report.current_version}",
            f"Total Issues: {len(report.issues)}",
        ]

        if report.breaking_count > 0:
            lines.append(f"  - Breaking Changes: {report.breaking_count}")
        if report.behavioral_count > 0:
            lines.append(f"  - Behavioral Changes: {report.behavioral_count}")
        if report.performance_count > 0:
            lines.append(f"  - Performance Regressions: {report.performance_count}")
        if report.dependency_count > 0:
            lines.append(f"  - Dependency Changes: {report.dependency_count}")

        risk_score = self.calculate_risk_score(report)
        lines.append(f"Risk Score: {risk_score:.1f}/100")

        if report.has_breaking_changes():
            lines.append("\nWARNING: Breaking changes detected!")

        return "\n".join(lines)

    def save_report(self, report: RegressionReport, output_path: Path) -> None:
        """
        Save regression report to JSON file.

        Args:
            report: Report to save
            output_path: Output file path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, indent=2)
        logger.info(f"Report saved to {output_path}")

    def load_report(self, input_path: Path) -> RegressionReport:
        """
        Load regression report from JSON file.

        Args:
            input_path: Input file path

        Returns:
            Loaded report
        """
        with open(input_path, encoding="utf-8") as f:
            data = json.load(f)
        return RegressionReport.from_dict(data)
