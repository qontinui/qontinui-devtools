"""Dead code detector for Rust codebases.

This module provides functionality to detect unused code including:
- Unused functions
- Unused structs
- Unused enums
- Unused traits
- Unused constants

The detector performs static analysis using regex patterns to identify
definitions and usages across the codebase.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RustDeadCode:
    """A piece of dead code in Rust.

    Attributes:
        type: Type of dead code ("function", "struct", "enum", "trait", "const")
        name: Name of the unused element
        file_path: Path to the file containing the dead code
        line_number: Line number where the dead code is defined
        reason: Explanation of why this is considered dead code
        confidence: Confidence level (0-1) that this is truly dead code
        visibility: Visibility modifier (pub, pub(crate), private)
    """

    type: str
    name: str
    file_path: str
    line_number: int
    reason: str
    confidence: float
    visibility: str


class DeadCodeDetector:
    """Detect unused code in Rust projects.

    This detector performs static analysis to find:
    - Unused functions (not called anywhere in the codebase)
    - Unused structs (not instantiated or referenced)
    - Unused enums (not referenced)
    - Unused traits (not implemented or used)
    - Unused constants (not referenced)

    The detector uses regex analysis to track definitions and usages
    across all Rust files in the project.
    """

    def __init__(self, root_path: str, verbose: bool = False) -> None:
        """Initialize the detector.

        Args:
            root_path: Root directory to analyze
            verbose: If True, print progress information
        """
        self.root_path = Path(root_path)
        self.verbose = verbose
        self._definitions: dict[str, list[tuple[str, int, str, str]]] = {
            "function": [],
            "struct": [],
            "enum": [],
            "trait": [],
            "const": [],
        }
        self._all_usages: set[str] = set()
        self._rust_files: list[Path] = []

    def _find_rust_files(self) -> list[Path]:
        """Find all Rust files in the project."""
        rust_files = []
        for path in self.root_path.rglob("*.rs"):
            # Skip common directories
            parts = path.parts
            skip_dirs = {"target", ".git", "vendor"}
            if any(skip_dir in parts for skip_dir in skip_dirs):
                continue
            rust_files.append(path)
        return rust_files

    def _extract_visibility(self, line: str) -> str:
        """Extract visibility modifier from a line.

        Args:
            line: Line of Rust code

        Returns:
            Visibility modifier: 'pub', 'pub(crate)', 'pub(super)', or 'private'
        """
        if re.search(r"\bpub\(crate\)", line):
            return "pub(crate)"
        elif re.search(r"\bpub\(super\)", line):
            return "pub(super)"
        elif re.search(r"\bpub\b", line):
            return "pub"
        else:
            return "private"

    def _scan_definitions(self) -> None:
        """Scan all files for definitions."""
        self._rust_files = self._find_rust_files()

        for file_path in self._rust_files:
            self._scan_file_definitions(file_path)

    def _scan_file_definitions(self, file_path: Path) -> None:
        """Scan a single file for definitions.

        Args:
            file_path: Path to the Rust file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                # Skip comments and blank lines
                line = line.strip()
                if not line or line.startswith("//"):
                    continue

                visibility = self._extract_visibility(line)

                # Match function definitions
                # fn foo(...) -> ...
                # pub fn foo(...) -> ...
                # async fn foo(...) -> ...
                func_pattern = r"(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:unsafe\s+)?fn\s+(\w+)\s*[<(]"
                func_match = re.search(func_pattern, line)
                if func_match:
                    name = func_match.group(1)
                    # Skip test functions and main
                    if name not in ("main", "test") and not line.startswith("#[test]"):
                        self._definitions["function"].append(
                            (name, line_num, str(file_path), visibility)
                        )

                # Match struct definitions
                # struct Foo { ... }
                # pub struct Foo { ... }
                struct_pattern = r"(?:pub(?:\([^)]*\))?\s+)?struct\s+(\w+)"
                struct_match = re.search(struct_pattern, line)
                if struct_match:
                    name = struct_match.group(1)
                    self._definitions["struct"].append(
                        (name, line_num, str(file_path), visibility)
                    )

                # Match enum definitions
                # enum Foo { ... }
                # pub enum Foo { ... }
                enum_pattern = r"(?:pub(?:\([^)]*\))?\s+)?enum\s+(\w+)"
                enum_match = re.search(enum_pattern, line)
                if enum_match:
                    name = enum_match.group(1)
                    self._definitions["enum"].append((name, line_num, str(file_path), visibility))

                # Match trait definitions
                # trait Foo { ... }
                # pub trait Foo { ... }
                trait_pattern = r"(?:pub(?:\([^)]*\))?\s+)?trait\s+(\w+)"
                trait_match = re.search(trait_pattern, line)
                if trait_match:
                    name = trait_match.group(1)
                    self._definitions["trait"].append(
                        (name, line_num, str(file_path), visibility)
                    )

                # Match const definitions
                # const FOO: ...
                # pub const FOO: ...
                const_pattern = r"(?:pub(?:\([^)]*\))?\s+)?const\s+([A-Z_][A-Z0-9_]*)\s*:"
                const_match = re.search(const_pattern, line)
                if const_match:
                    name = const_match.group(1)
                    self._definitions["const"].append(
                        (name, line_num, str(file_path), visibility)
                    )

        except (UnicodeDecodeError, PermissionError):
            pass

    def _scan_usages(self) -> None:
        """Scan all files for usages."""
        for file_path in self._rust_files:
            self._scan_file_usages(file_path)

    def _scan_file_usages(self, file_path: Path) -> None:
        """Scan a single file for usages.

        Args:
            file_path: Path to the Rust file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Remove comments to avoid false positives
            content = re.sub(r"//.*", "", content)
            content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

            # Extract all identifiers (simple approach)
            identifiers = re.findall(r"\b([a-zA-Z_]\w*)\b", content)
            self._all_usages.update(identifiers)

        except (UnicodeDecodeError, PermissionError):
            pass

    def _find_unused(self) -> list[RustDeadCode]:
        """Find all unused code by comparing definitions and usages."""
        dead_code: list[RustDeadCode] = []

        for code_type, definitions in self._definitions.items():
            for name, line_num, file_path, visibility in definitions:
                # Count how many times this name appears
                # If it appears only once (its definition), it's likely unused
                usage_count = list(self._all_usages).count(name)

                # Heuristic: if name appears <= 2 times, it might be unused
                # (once for definition, maybe once in the same file)
                if usage_count <= 2:
                    confidence = self._calculate_confidence(
                        name, code_type, visibility, usage_count
                    )

                    if confidence > 0.3:  # Only report if confidence is reasonable
                        dead_code.append(
                            RustDeadCode(
                                type=code_type,
                                name=name,
                                file_path=file_path,
                                line_number=line_num,
                                reason=f"{code_type.capitalize()} '{name}' appears to be unused",
                                confidence=confidence,
                                visibility=visibility,
                            )
                        )

        # Sort by confidence (high first), then by type
        dead_code.sort(key=lambda x: (-x.confidence, x.type))
        return dead_code

    def _calculate_confidence(
        self, name: str, code_type: str, visibility: str, usage_count: int
    ) -> float:
        """Calculate confidence that this is truly dead code.

        Args:
            name: Name of the code element
            code_type: Type of code
            visibility: Visibility modifier
            usage_count: Number of times the name appears

        Returns:
            Confidence level between 0 and 1
        """
        # Start with base confidence
        confidence = 0.7

        # Public items have lower confidence (might be used externally)
        if visibility == "pub":
            confidence *= 0.5
        elif visibility == "pub(crate)":
            confidence *= 0.7

        # If used at all, lower confidence
        if usage_count > 1:
            confidence *= 0.6

        # Common patterns that shouldn't be flagged highly
        common_names = {"new", "default", "from", "into", "clone", "fmt", "error"}
        if name.lower() in common_names:
            confidence *= 0.4

        # Test-related items
        if "test" in name.lower() or "mock" in name.lower():
            confidence *= 0.3

        return min(1.0, max(0.0, confidence))

    def analyze(self) -> list[RustDeadCode]:
        """Find all dead code in the project.

        Returns:
            List of RustDeadCode objects representing unused code
        """
        # Step 1: Find all definitions
        self._scan_definitions()

        # Step 2: Find all usages
        self._scan_usages()

        # Step 3: Compare to find unused code
        return self._find_unused()

    def find_unused_functions(self) -> list[RustDeadCode]:
        """Find unused functions only."""
        all_dead_code = self.analyze()
        return [dc for dc in all_dead_code if dc.type == "function"]

    def find_unused_structs(self) -> list[RustDeadCode]:
        """Find unused structs only."""
        all_dead_code = self.analyze()
        return [dc for dc in all_dead_code if dc.type == "struct"]

    def find_unused_enums(self) -> list[RustDeadCode]:
        """Find unused enums only."""
        all_dead_code = self.analyze()
        return [dc for dc in all_dead_code if dc.type == "enum"]

    def get_stats(self) -> dict[str, int]:
        """Get statistics about dead code.

        Returns:
            Dictionary with counts of each type of dead code
        """
        all_dead_code = self.analyze()
        return {
            "total": len(all_dead_code),
            "functions": len([dc for dc in all_dead_code if dc.type == "function"]),
            "structs": len([dc for dc in all_dead_code if dc.type == "struct"]),
            "enums": len([dc for dc in all_dead_code if dc.type == "enum"]),
            "traits": len([dc for dc in all_dead_code if dc.type == "trait"]),
            "consts": len([dc for dc in all_dead_code if dc.type == "const"]),
        }

    def generate_report(self, dead_code: list[RustDeadCode]) -> str:
        """Generate a detailed text report of dead code.

        Args:
            dead_code: List of detected dead code

        Returns:
            Formatted report as a string
        """
        if not dead_code:
            return "No dead code found."

        lines: list[str] = []
        lines.append("=" * 80)
        lines.append("RUST DEAD CODE REPORT")
        lines.append("=" * 80)
        lines.append(f"\nProject: {self.root_path}")
        lines.append(f"Total items found: {len(dead_code)}")
        lines.append("")

        # Group by type
        by_type: dict[str, list[RustDeadCode]] = {}
        for dc in dead_code:
            by_type.setdefault(dc.type, []).append(dc)

        for code_type, items in sorted(by_type.items()):
            lines.append(f"\n{code_type.upper()}S ({len(items)}):")
            lines.append("-" * 80)

            for dc in items:
                rel_path = Path(dc.file_path).relative_to(self.root_path)
                lines.append(
                    f"\n  {dc.name} ({dc.visibility})"
                    f" - Confidence: {dc.confidence:.0%}"
                )
                lines.append(f"    {rel_path}:{dc.line_number}")
                lines.append(f"    {dc.reason}")

        lines.append("\n" + "=" * 80)
        return "\n".join(lines)
