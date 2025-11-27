"""Unsafe code analyzer for Rust codebases.

This module analyzes the usage of unsafe code in Rust projects:
- Find all unsafe blocks
- Categorize by type (raw pointers, FFI, etc.)
- Report locations and context
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table


@dataclass
class UnsafeBlock:
    """An unsafe block in Rust code.

    Attributes:
        file_path: Path to the file containing the unsafe code
        line_number: Line number where the unsafe block starts
        block_type: Type of unsafe block (function, impl, block, trait)
        context: Surrounding code context
        category: Category of unsafe operation (pointer, ffi, etc.)
        code_snippet: The actual unsafe code
    """

    file_path: str
    line_number: int
    block_type: str
    context: str
    category: str
    code_snippet: str


class UnsafeAnalyzer:
    """Analyze unsafe code usage in Rust projects.

    This analyzer finds and categorizes unsafe code:
    - Unsafe functions
    - Unsafe blocks
    - Unsafe trait implementations
    - Raw pointer operations
    - FFI calls
    - Memory operations

    The analyzer uses regex patterns to identify unsafe code patterns.
    """

    def __init__(self, root_path: str, verbose: bool = False) -> None:
        """Initialize the analyzer.

        Args:
            root_path: Root directory to analyze
            verbose: If True, print progress information
        """
        self.root_path = Path(root_path)
        self.verbose = verbose
        self.console = Console()
        self._unsafe_blocks: list[UnsafeBlock] = []

    def _find_rust_files(self) -> list[Path]:
        """Find all Rust files in the project."""
        rust_files = []
        for path in self.root_path.rglob("*.rs"):
            parts = path.parts
            skip_dirs = {"target", ".git", "vendor"}
            if any(skip_dir in parts for skip_dir in skip_dirs):
                continue
            rust_files.append(path)
        return rust_files

    def _categorize_unsafe(self, code: str) -> str:
        """Categorize the type of unsafe operation.

        Args:
            code: Unsafe code snippet

        Returns:
            Category of unsafe operation
        """
        # Check for raw pointers
        if re.search(r"\*(?:const|mut)\s+\w+", code):
            return "raw_pointers"

        # Check for FFI
        if re.search(r"extern\s+\"C\"", code) or "ffi::" in code:
            return "ffi"

        # Check for memory operations
        if any(
            op in code
            for op in [
                "std::ptr::",
                "offset",
                "read",
                "write",
                "copy",
                "transmute",
                "from_raw",
                "into_raw",
            ]
        ):
            return "memory_operations"

        # Check for assembly
        if "asm!" in code or "llvm_asm!" in code:
            return "assembly"

        # Check for union access
        if re.search(r"union\s+\w+", code):
            return "union_access"

        # Check for mutable statics
        if re.search(r"static\s+mut\s+", code):
            return "mutable_static"

        return "other"

    def _extract_context(self, lines: list[str], line_num: int, context_size: int = 2) -> str:
        """Extract context around a line.

        Args:
            lines: All lines in the file
            line_num: Target line number (1-indexed)
            context_size: Number of lines before/after to include

        Returns:
            Context string
        """
        start = max(0, line_num - context_size - 1)
        end = min(len(lines), line_num + context_size)
        context_lines = lines[start:end]
        return "".join(context_lines).strip()

    def _scan_file(self, file_path: Path) -> None:
        """Scan a single file for unsafe code.

        Args:
            file_path: Path to the Rust file
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                content = "".join(lines)

            # Find unsafe functions
            # unsafe fn foo(...) { ... }
            unsafe_fn_pattern = r"(?:pub(?:\([^)]*\))?\s+)?unsafe\s+fn\s+(\w+)"
            for match in re.finditer(unsafe_fn_pattern, content):
                line_num = content[: match.start()].count("\n") + 1
                context = self._extract_context(lines, line_num)
                code_snippet = lines[line_num - 1].strip()
                category = self._categorize_unsafe(context)

                self._unsafe_blocks.append(
                    UnsafeBlock(
                        file_path=str(file_path),
                        line_number=line_num,
                        block_type="function",
                        context=context,
                        category=category,
                        code_snippet=code_snippet,
                    )
                )

            # Find unsafe blocks
            # unsafe { ... }
            unsafe_block_pattern = r"unsafe\s*\{"
            for match in re.finditer(unsafe_block_pattern, content):
                line_num = content[: match.start()].count("\n") + 1
                context = self._extract_context(lines, line_num, context_size=5)
                code_snippet = lines[line_num - 1].strip()
                category = self._categorize_unsafe(context)

                self._unsafe_blocks.append(
                    UnsafeBlock(
                        file_path=str(file_path),
                        line_number=line_num,
                        block_type="block",
                        context=context,
                        category=category,
                        code_snippet=code_snippet,
                    )
                )

            # Find unsafe impl blocks
            # unsafe impl Trait for Type { ... }
            unsafe_impl_pattern = r"unsafe\s+impl"
            for match in re.finditer(unsafe_impl_pattern, content):
                line_num = content[: match.start()].count("\n") + 1
                context = self._extract_context(lines, line_num)
                code_snippet = lines[line_num - 1].strip()
                category = self._categorize_unsafe(context)

                self._unsafe_blocks.append(
                    UnsafeBlock(
                        file_path=str(file_path),
                        line_number=line_num,
                        block_type="impl",
                        context=context,
                        category=category,
                        code_snippet=code_snippet,
                    )
                )

            # Find unsafe trait definitions
            # unsafe trait Foo { ... }
            unsafe_trait_pattern = r"unsafe\s+trait"
            for match in re.finditer(unsafe_trait_pattern, content):
                line_num = content[: match.start()].count("\n") + 1
                context = self._extract_context(lines, line_num)
                code_snippet = lines[line_num - 1].strip()
                category = self._categorize_unsafe(context)

                self._unsafe_blocks.append(
                    UnsafeBlock(
                        file_path=str(file_path),
                        line_number=line_num,
                        block_type="trait",
                        context=context,
                        category=category,
                        code_snippet=code_snippet,
                    )
                )

        except (UnicodeDecodeError, PermissionError) as e:
            if self.verbose:
                self.console.print(f"[yellow]Warning: Could not read {file_path}: {e}[/yellow]")

    def analyze(self) -> list[UnsafeBlock]:
        """Analyze all unsafe code in the project.

        Returns:
            List of UnsafeBlock objects
        """
        if self.verbose:
            self.console.print(f"\n[bold]Analyzing unsafe code:[/bold] {self.root_path}")

        rust_files = self._find_rust_files()

        for file_path in rust_files:
            self._scan_file(file_path)

        if self.verbose:
            self.console.print(f"Files scanned: {len(rust_files)}")
            self.console.print(f"Unsafe blocks found: {len(self._unsafe_blocks)}")

        return self._unsafe_blocks

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics about unsafe code usage.

        Returns:
            Dictionary with statistics
        """
        if not self._unsafe_blocks:
            self.analyze()

        # Count by type
        by_type: dict[str, int] = {}
        for block in self._unsafe_blocks:
            by_type[block.block_type] = by_type.get(block.block_type, 0) + 1

        # Count by category
        by_category: dict[str, int] = {}
        for block in self._unsafe_blocks:
            by_category[block.category] = by_category.get(block.category, 0) + 1

        # Count by file
        by_file: dict[str, int] = {}
        for block in self._unsafe_blocks:
            rel_path = str(Path(block.file_path).relative_to(self.root_path))
            by_file[rel_path] = by_file.get(rel_path, 0) + 1

        return {
            "total_unsafe_blocks": len(self._unsafe_blocks),
            "by_type": by_type,
            "by_category": by_category,
            "files_with_unsafe": len(by_file),
            "top_files": sorted(by_file.items(), key=lambda x: x[1], reverse=True)[:10],
        }

    def generate_report(self, unsafe_blocks: list[UnsafeBlock] | None = None) -> str:
        """Generate a detailed text report of unsafe code.

        Args:
            unsafe_blocks: List of unsafe blocks to report (uses all if None)

        Returns:
            Formatted report as a string
        """
        if unsafe_blocks is None:
            unsafe_blocks = self._unsafe_blocks

        if not unsafe_blocks:
            return "No unsafe code found."

        lines: list[str] = []
        lines.append("=" * 80)
        lines.append("RUST UNSAFE CODE REPORT")
        lines.append("=" * 80)
        lines.append(f"\nProject: {self.root_path}")
        lines.append(f"Total unsafe blocks: {len(unsafe_blocks)}")
        lines.append("")

        # Statistics
        stats = self.get_statistics()
        lines.append("BY TYPE:")
        for block_type, count in sorted(stats["by_type"].items()):
            lines.append(f"  {block_type}: {count}")

        lines.append("\nBY CATEGORY:")
        for category, count in sorted(stats["by_category"].items()):
            lines.append(f"  {category}: {count}")

        lines.append("\n" + "-" * 80)
        lines.append("\nDETAILS:")

        # Group by file
        by_file: dict[str, list[UnsafeBlock]] = {}
        for block in unsafe_blocks:
            by_file.setdefault(block.file_path, []).append(block)

        for file_path, blocks in sorted(by_file.items()):
            rel_path = Path(file_path).relative_to(self.root_path)
            lines.append(f"\n{rel_path} ({len(blocks)} unsafe blocks):")

            for block in sorted(blocks, key=lambda b: b.line_number):
                lines.append(f"\n  Line {block.line_number}: {block.block_type}")
                lines.append(f"    Category: {block.category}")
                lines.append(f"    Code: {block.code_snippet}")

        lines.append("\n" + "=" * 80)
        return "\n".join(lines)

    def generate_rich_report(self, unsafe_blocks: list[UnsafeBlock] | None = None) -> None:
        """Generate a rich console report with colors and formatting.

        Args:
            unsafe_blocks: List of unsafe blocks to report (uses all if None)
        """
        if unsafe_blocks is None:
            unsafe_blocks = self._unsafe_blocks

        if not unsafe_blocks:
            self.console.print("\n[bold green]No unsafe code found[/bold green]\n")
            return

        self.console.print(f"\n[bold yellow]Found {len(unsafe_blocks)} unsafe blocks[/bold yellow]\n")

        # Statistics
        stats = self.get_statistics()

        # Table for type breakdown
        type_table = Table(title="Unsafe Code by Type")
        type_table.add_column("Type", style="cyan")
        type_table.add_column("Count", justify="right", style="green")

        for block_type, count in sorted(stats["by_type"].items()):
            type_table.add_row(block_type, str(count))

        self.console.print(type_table)
        self.console.print()

        # Table for category breakdown
        category_table = Table(title="Unsafe Code by Category")
        category_table.add_column("Category", style="cyan")
        category_table.add_column("Count", justify="right", style="yellow")

        for category, count in sorted(stats["by_category"].items()):
            category_table.add_row(category, str(count))

        self.console.print(category_table)
        self.console.print()

        # Top files
        self.console.print("[bold]Top Files with Unsafe Code:[/bold]")
        for file_path, count in stats["top_files"][:5]:
            self.console.print(f"  {file_path}: [yellow]{count}[/yellow] blocks")
        self.console.print()
