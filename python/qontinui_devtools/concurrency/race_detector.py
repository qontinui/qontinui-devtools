"""Race condition detector for static analysis of threading issues."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .ast_analyzer import AnalysisContext, StateAccess, analyze_file
from .heuristics import (
    calculate_severity,
    get_false_positive_indicators,
    is_check_then_act_pattern,
    is_double_checked_locking,
    is_likely_thread_safe,
    suggest_fix,
)


@dataclass
class SharedState:
    """Mutable state that could be shared between threads."""

    name: str
    type: str  # "class_variable", "module_global", "closure_variable"
    file_path: str
    line_number: int
    col_offset: int
    is_protected: bool  # Has associated lock
    inferred_type: str = "unknown"
    class_name: str | None = None


@dataclass
class RaceCondition:
    """Potential race condition."""

    shared_state: SharedState
    access_locations: list[tuple[str, int, str]]  # (file, line, access_type)
    severity: str  # "critical", "high", "medium", "low"
    description: str
    suggestion: str
    patterns_detected: list[str] = field(default_factory=list)
    false_positive_indicators: list[str] = field(default_factory=list)


class RaceConditionDetector:
    """Static analyzer for race conditions."""

    def __init__(self, root_path: str | Path, exclude_patterns: list[str] | None = None) -> None:
        """
        Initialize race condition detector.

        Args:
            root_path: Root directory to analyze
            exclude_patterns: Patterns to exclude (e.g., ["test_", "venv/"])
        """
        self.root_path = Path(root_path)
        self.exclude_patterns = exclude_patterns or [
            "test_",
            "__pycache__",
            ".git",
            "venv",
            ".venv",
        ]
        self.contexts: dict[str, AnalysisContext] = {}
        self.shared_states: list[SharedState] = []
        self.race_conditions: list[RaceCondition] = []

    def analyze(self) -> list[RaceCondition]:
        """
        Perform complete analysis.

        Returns:
            List of detected race conditions, sorted by severity.
        """
        # Step 1: Find all Python files
        python_files = self._find_python_files()

        # Step 2: Analyze each file
        for file_path in python_files:
            try:
                context = analyze_file(file_path)
                self.contexts[str(file_path)] = context
            except Exception as e:
                # Log and continue
                print(f"Error analyzing {file_path}: {e}")
                continue

        # Step 3: Find shared state
        self.shared_states = self.find_shared_state()

        # Step 4: Detect race conditions
        self.race_conditions = self._detect_race_conditions()

        # Step 5: Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        self.race_conditions.sort(key=lambda r: severity_order.get(r.severity, 4))

        return self.race_conditions

    def find_shared_state(self) -> list[SharedState]:
        """Find all shared mutable state across analyzed files."""
        shared_states = []

        for file_path, context in self.contexts.items():
            for state_dict in context.shared_states:
                # Check if likely thread-safe
                is_safe = is_likely_thread_safe(
                    state_name=state_dict["name"],
                    state_type=state_dict["type"],
                    type_annotation=state_dict.get("inferred_type", "unknown"),
                    context=context,
                )

                shared_state = SharedState(
                    name=state_dict["name"],
                    type=state_dict["type"],
                    file_path=file_path,
                    line_number=state_dict["line_number"],
                    col_offset=state_dict.get("col_offset", 0),
                    is_protected=is_safe,
                    inferred_type=state_dict.get("inferred_type", "unknown"),
                    class_name=state_dict.get("class_name"),
                )

                shared_states.append(shared_state)

        return shared_states

    def find_lock_usage(self) -> dict[str, list[str]]:
        """
        Find all lock usage across analyzed files.

        Returns:
            Dictionary mapping file paths to list of lock names.
        """
        lock_usage = {}

        for file_path, context in self.contexts.items():
            if context.locks:
                lock_usage[file_path] = [lock.name for lock in context.locks]

        return lock_usage

    def check_protection(self, state: SharedState) -> bool:
        """
        Check if a shared state has proper lock protection.

        Args:
            state: The shared state to check

        Returns:
            True if protected, False otherwise
        """
        # Already marked as protected by heuristics
        if state.is_protected:
            return True

        # Get context for this file
        context = self.contexts.get(state.file_path)
        if not context:
            return False

        # Find accesses to this state
        accesses = self._get_accesses_for_state(state, context)

        # If all accesses are in lock context, it's protected
        if accesses and all(a.in_lock_context for a in accesses):
            return True

        return False

    def _detect_race_conditions(self) -> list[RaceCondition]:
        """Detect race conditions from shared state and access patterns."""
        race_conditions = []

        for state in self.shared_states:
            # Skip if already marked as protected
            if state.is_protected:
                continue

            # Get context
            context = self.contexts.get(state.file_path)
            if not context:
                continue

            # Get accesses to this state
            accesses = self._get_accesses_for_state(state, context)

            # Skip if no accesses found (definition only)
            if not accesses:
                continue

            # Check if there are unprotected writes
            unprotected_writes = [
                a for a in accesses if "write" in a.access_type and not a.in_lock_context
            ]

            if not unprotected_writes:
                # No unprotected writes, likely safe
                continue

            # Calculate severity
            severity = calculate_severity(
                state_name=state.name,
                state_type=state.type,
                accesses=accesses,
                locks=context.locks,
            )

            # Build description
            description = self._build_description(state, accesses, context)

            # Get suggestion
            suggestion = suggest_fix(
                state_name=state.name,
                state_type=state.type,
                severity=severity,
                accesses=accesses,
                context=context,
            )

            # Detect patterns
            patterns = []
            if is_check_then_act_pattern(accesses):
                patterns.append("check-then-act")
            if is_double_checked_locking(accesses):
                patterns.append("double-checked-locking")

            # Get false positive indicators
            fp_indicators = get_false_positive_indicators(
                state_name=state.name,
                state_type=state.type,
                context=context,
            )

            # Build access locations
            access_locations = [(state.file_path, a.line_number, a.access_type) for a in accesses]

            race = RaceCondition(
                shared_state=state,
                access_locations=access_locations,
                severity=severity,
                description=description,
                suggestion=suggestion,
                patterns_detected=patterns,
                false_positive_indicators=fp_indicators,
            )

            race_conditions.append(race)

        return race_conditions

    def _get_accesses_for_state(
        self, state: SharedState, context: AnalysisContext
    ) -> list[StateAccess]:
        """Get all accesses to a shared state."""
        accesses = []

        # Simple name matching (could be improved with scope analysis)
        state_name = state.name.lstrip("_")

        for access in context.state_accesses:
            access_name = access.name.lstrip("_")
            # Check for exact match or attribute match
            # Strip underscores from each part for comparison
            access_parts = [part.lstrip("_") for part in access.name.split(".")]

            if state_name == access_name or state_name in access_parts:
                accesses.append(access)

        return accesses

    def _build_description(
        self, state: SharedState, accesses: list[StateAccess], context: AnalysisContext
    ) -> str:
        """Build human-readable description of the race condition."""
        unprotected_writes = sum(
            1 for a in accesses if "write" in a.access_type and not a.in_lock_context
        )
        unprotected_reads = sum(
            1 for a in accesses if a.access_type == "read" and not a.in_lock_context
        )
        protected_accesses = sum(1 for a in accesses if a.in_lock_context)

        parts = []

        # State location
        if state.class_name:
            parts.append(
                f"Shared {state.inferred_type} '{state.name}' in class '{state.class_name}'"
            )
        else:
            parts.append(f"Module-level {state.inferred_type} '{state.name}'")

        # Access pattern
        if unprotected_writes > 1:
            parts.append(
                f"has {unprotected_writes} unprotected write operations (write-write race)"
            )
        elif unprotected_writes == 1 and unprotected_reads > 0:
            parts.append(
                f"has {unprotected_writes} unprotected write and {unprotected_reads} unprotected reads (read-write race)"
            )
        elif unprotected_writes == 1:
            parts.append("has unprotected write operation")

        # Lock context
        if protected_accesses > 0:
            parts.append(f"Some accesses ({protected_accesses}) are protected but not all")
        elif context.locks:
            parts.append(f"Locks available but not used: {[l.name for l in context.locks]}")
        else:
            parts.append("No locking mechanism found")

        return ". ".join(parts) + "."

    def _find_python_files(self) -> list[Path]:
        """Find all Python files in root path."""
        if self.root_path.is_file():
            return [self.root_path]

        python_files = []
        for file_path in self.root_path.rglob("*.py"):
            # Check exclusion patterns
            if any(pattern in str(file_path) for pattern in self.exclude_patterns):
                continue
            python_files.append(file_path)

        return python_files

    def generate_report(self, include_low: bool = False) -> str:
        """
        Generate a formatted report of race conditions.

        Args:
            include_low: Include low severity issues in report

        Returns:
            Formatted report string
        """
        if not self.race_conditions:
            return "No race conditions detected. Good job!"

        lines = []
        lines.append("=" * 80)
        lines.append("RACE CONDITION DETECTION REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Summary
        critical = sum(1 for r in self.race_conditions if r.severity == "critical")
        high = sum(1 for r in self.race_conditions if r.severity == "high")
        medium = sum(1 for r in self.race_conditions if r.severity == "medium")
        low = sum(1 for r in self.race_conditions if r.severity == "low")

        lines.append("SUMMARY")
        lines.append("-" * 80)
        lines.append(f"Total Issues: {len(self.race_conditions)}")
        lines.append(f"  Critical: {critical}")
        lines.append(f"  High:     {high}")
        lines.append(f"  Medium:   {medium}")
        lines.append(f"  Low:      {low}")
        lines.append("")

        # Detailed findings
        lines.append("DETAILED FINDINGS")
        lines.append("-" * 80)
        lines.append("")

        for i, race in enumerate(self.race_conditions, 1):
            # Skip low severity if not requested
            if not include_low and race.severity == "low":
                continue

            # Severity badge
            severity_badge = {
                "critical": "[CRITICAL]",
                "high": "[HIGH]",
                "medium": "[MEDIUM]",
                "low": "[LOW]",
            }

            lines.append(f"{i}. {severity_badge[race.severity]} {race.shared_state.name}")
            lines.append(f"   Type: {race.shared_state.inferred_type}")
            lines.append(
                f"   Location: {race.shared_state.file_path}:{race.shared_state.line_number}"
            )
            lines.append("")
            lines.append("   Description:")
            lines.append(f"     {race.description}")
            lines.append("")

            # Patterns
            if race.patterns_detected:
                lines.append("   Patterns Detected:")
                for pattern in race.patterns_detected:
                    lines.append(f"     - {pattern}")
                lines.append("")

            # Access locations
            if len(race.access_locations) <= 10:
                lines.append(f"   Access Locations ({len(race.access_locations)}):")
                for file_path, line_num, access_type in race.access_locations:
                    lines.append(f"     - Line {line_num}: {access_type}")
            else:
                lines.append(f"   Access Locations: {len(race.access_locations)} total")

            lines.append("")
            lines.append("   Suggestion:")
            lines.append(f"     {race.suggestion}")

            # False positive indicators
            if race.false_positive_indicators:
                lines.append("")
                lines.append("   Note: Possible false positive indicators:")
                for indicator in race.false_positive_indicators:
                    lines.append(f"     - {indicator}")

            lines.append("")
            lines.append("-" * 80)
            lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        return "\n".join(lines)

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the analysis."""
        return {
            "files_analyzed": len(self.contexts),
            "shared_states_found": len(self.shared_states),
            "race_conditions_found": len(self.race_conditions),
            "critical_issues": sum(1 for r in self.race_conditions if r.severity == "critical"),
            "high_issues": sum(1 for r in self.race_conditions if r.severity == "high"),
            "medium_issues": sum(1 for r in self.race_conditions if r.severity == "medium"),
            "low_issues": sum(1 for r in self.race_conditions if r.severity == "low"),
            "locks_found": sum(len(c.locks) for c in self.contexts.values()),
            "protected_states": sum(1 for s in self.shared_states if s.is_protected),
            "unprotected_states": sum(1 for s in self.shared_states if not s.is_protected),
        }
