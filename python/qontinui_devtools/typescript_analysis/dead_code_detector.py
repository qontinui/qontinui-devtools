"""Dead code detection for TypeScript/JavaScript codebases.

This module provides functionality to detect unused code including:
- Unused exports
- Unused functions
- Unused classes
- Unused variables
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

from .ts_utils import extract_exports, extract_imports, find_ts_js_files


@dataclass
class DeadCode:
    """A piece of dead code.

    Attributes:
        type: Type of dead code ("function", "class", "const", "interface", "type")
        name: Name of the unused element
        file_path: Path to the file containing the dead code
        line_number: Line number where the dead code is defined
        reason: Explanation of why this is considered dead code
        confidence: Confidence level (0-1) that this is truly dead code
    """

    type: str
    name: str
    file_path: Path
    line_number: int
    reason: str
    confidence: float


class DeadCodeDetector:
    """Detector for unused code in TypeScript/JavaScript projects.

    This analyzer:
    1. Scans all TS/JS files
    2. Collects all exports
    3. Tracks usage across the codebase
    4. Identifies unused exports

    Example:
        >>> detector = DeadCodeDetector('/path/to/project')
        >>> dead_code = detector.analyze()
        >>> for code in dead_code:
        ...     print(f"{code.name} is unused")
    """

    def __init__(self, root_path: str, verbose: bool = False) -> None:
        """Initialize the detector.

        Args:
            root_path: Root directory of the project to analyze
            verbose: If True, print progress information
        """
        self.root_path = Path(root_path).resolve()
        self.verbose = verbose
        self.console = Console()

        # State
        self.files: list[Path] = []
        self.exports: dict[Path, list] = {}  # file -> exports
        self.usage: dict[str, set[Path]] = {}  # export_name -> set of files using it

    def analyze(self) -> list[DeadCode]:
        """Perform dead code analysis.

        Returns:
            List of DeadCode objects for unused code
        """
        if self.verbose:
            self.console.print(
                f"\n[bold]Analyzing TypeScript/JavaScript project:[/bold] {self.root_path}"
            )

        # Step 1: Find all files
        self.files = find_ts_js_files(self.root_path)

        if self.verbose:
            self.console.print(f"Found {len(self.files)} files")

        # Step 2: Collect all exports
        self._collect_exports()

        # Step 3: Track usage
        self._track_usage()

        # Step 4: Identify dead code
        dead_code = self._identify_dead_code()

        if self.verbose:
            self.console.print(
                f"\n[yellow]Found {len(dead_code)} potentially unused exports[/yellow]"
            )

        return dead_code

    def _collect_exports(self) -> None:
        """Collect all exports from all files."""
        if self.verbose:
            self.console.print("Collecting exports...")

        for file_path in self.files:
            exports = extract_exports(file_path)
            self.exports[file_path] = exports

            # Initialize usage tracking
            for export in exports:
                if export.name not in self.usage:
                    self.usage[export.name] = set()

    def _track_usage(self) -> None:
        """Track where exports are used."""
        if self.verbose:
            self.console.print("Tracking usage...")

        for file_path in self.files:
            # Read file content to check for usage
            try:
                content = file_path.read_text(encoding="utf-8")
            except Exception:
                continue

            # Check imports
            imports = extract_imports(file_path)

            for imp in imports:
                # Track named imports
                for name in imp.names:
                    if name in self.usage:
                        self.usage[name].add(file_path)

                # Track default imports
                if imp.default_import and imp.default_import in self.usage:
                    self.usage[imp.default_import].add(file_path)

                # Track namespace imports
                if imp.namespace_import and imp.namespace_import in self.usage:
                    self.usage[imp.namespace_import].add(file_path)

            # Also check for usage in the same file (local usage)
            for export_name in self.usage.keys():
                # Use regex to find usage of the name
                # This is a simple heuristic - may have false positives
                pattern = r"\b" + re.escape(export_name) + r"\b"
                if re.search(pattern, content):
                    self.usage[export_name].add(file_path)

    def _identify_dead_code(self) -> list[DeadCode]:
        """Identify unused exports."""
        dead_code: list[Any] = []

        for file_path, exports in self.exports.items():
            for export in exports:
                # Check if used anywhere
                used_in_files = self.usage.get(export.name, set())

                # Remove the file where it's defined from usage
                # (we already counted local usage, but it shouldn't count for export)
                other_files_usage = used_in_files - {file_path}

                # If not used in any other file, it might be dead code
                if not other_files_usage:
                    # Determine confidence
                    confidence = self._calculate_confidence(export, file_path, used_in_files)

                    # Determine reason
                    if export.is_type_only:
                        reason = "Type/interface not imported in any file"
                    elif used_in_files:
                        reason = "Exported but only used locally in the same file"
                    else:
                        reason = "Not used anywhere in the codebase"

                    dead_code.append(
                        DeadCode(
                            type=export.export_type,
                            name=export.name,
                            file_path=file_path,
                            line_number=export.line_number,
                            reason=reason,
                            confidence=confidence,
                        )
                    )

        # Sort by confidence (highest first)
        dead_code.sort(key=lambda x: (-x.confidence, str(x.file_path), x.line_number))

        return dead_code

    def _calculate_confidence(self, export, file_path: Path, used_in_files: set[Path]) -> float:
        """Calculate confidence that this is truly dead code.

        Args:
            export: The export statement
            file_path: File containing the export
            used_in_files: Set of files where it's used

        Returns:
            Confidence score (0-1)
        """
        confidence = 0.5  # Base confidence

        # Higher confidence if not used at all
        if not used_in_files:
            confidence += 0.3

        # Lower confidence for common names (might be used dynamically)
        common_names = {"default", "index", "config", "utils", "helpers"}
        if export.name.lower() in common_names:
            confidence -= 0.2

        # Higher confidence for specific types
        if export.export_type in ["function", "class"]:
            confidence += 0.1

        # Lower confidence for types (might be used in type annotations)
        if export.is_type_only:
            confidence -= 0.1

        # Check if file is an index file (likely a re-export)
        if file_path.name.startswith("index."):
            confidence -= 0.2

        # Clamp to [0, 1]
        return max(0.0, min(1.0, confidence))

    def generate_rich_report(self, dead_code: list[DeadCode]) -> None:
        """Generate a rich console report of dead code.

        Args:
            dead_code: List of detected dead code
        """
        if not dead_code:
            self.console.print("\n[green]No dead code found![/green]")
            return

        self.console.print(
            f"\n[bold yellow]Found {len(dead_code)} potentially unused exports:[/bold yellow]\n"
        )

        # Group by file
        by_file: dict[Path, list[DeadCode]] = {}
        for code in dead_code:
            if code.file_path not in by_file:
                by_file[code.file_path] = []
            by_file[code.file_path].append(code)

        # Create table
        table = Table(title="Dead Code Report")
        table.add_column("File", style="cyan")
        table.add_column("Name", style="yellow")
        table.add_column("Type", style="magenta")
        table.add_column("Line", style="green")
        table.add_column("Confidence", style="red")
        table.add_column("Reason", style="white")

        for file_path in sorted(by_file.keys()):
            codes = by_file[file_path]
            rel_path = (
                file_path.relative_to(self.root_path)
                if file_path.is_relative_to(self.root_path)
                else file_path
            )

            for code in codes:
                table.add_row(
                    str(rel_path),
                    code.name,
                    code.type,
                    str(code.line_number),
                    f"{code.confidence:.0%}",
                    code.reason,
                )

        self.console.print(table)

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about the analysis.

        Returns:
            Dictionary with statistics
        """
        total_exports = sum(len(exports) for exports in self.exports.values())

        return {
            "total_files": len(self.files),
            "total_exports": total_exports,
        }

    def generate_report(self, dead_code: list[DeadCode]) -> str:
        """Generate a text report of dead code.

        Args:
            dead_code: List of detected dead code

        Returns:
            Text report as a string
        """
        if not dead_code:
            return "No dead code found!"

        lines = [
            "=" * 80,
            "DEAD CODE REPORT",
            "=" * 80,
            f"\nFound {len(dead_code)} potentially unused exports\n",
        ]

        # Group by file
        by_file: dict[Path, list[DeadCode]] = {}
        for code in dead_code:
            if code.file_path not in by_file:
                by_file[code.file_path] = []
            by_file[code.file_path].append(code)

        for file_path in sorted(by_file.keys()):
            codes = by_file[file_path]
            rel_path = (
                file_path.relative_to(self.root_path)
                if file_path.is_relative_to(self.root_path)
                else file_path
            )

            lines.append(f"\n{rel_path}:")
            lines.append("-" * 40)

            for code in codes:
                lines.append(f"  Line {code.line_number}: {code.type} '{code.name}'")
                lines.append(f"    Confidence: {code.confidence:.0%}")
                lines.append(f"    Reason: {code.reason}")

        lines.append("\n" + "=" * 80)
        stats = self.get_statistics()
        lines.append("STATISTICS:")
        lines.append(f"  Total files analyzed: {stats['total_files']}")
        lines.append(f"  Total exports: {stats['total_exports']}")
        lines.append(f"  Potentially unused: {len(dead_code)}")
        lines.append("=" * 80)

        return "\n".join(lines)
