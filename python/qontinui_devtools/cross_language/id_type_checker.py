"""Cross-language ID type consistency checker.

from typing import Any, Any

Detects type mismatches for ID fields across TypeScript, Rust, and Python codebases.
Common issues detected:
- TypeScript using `number` for UUID fields (should be `string`)
- Rust using `i32`/`i64` for UUID fields (should be `String`)
- Python using `int` for UUID fields (should be `str` or `UUID`)
- JavaScript/TypeScript code using `parseInt()` on UUID-like values
- Cross-language type inconsistencies for the same logical field
"""

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from typing import Any


class IssueSeverity(Enum):
    """Severity levels for detected issues."""

    ERROR = "error"  # Definite bug (e.g., parseInt on UUID)
    WARNING = "warning"  # Likely bug (e.g., number type for *Id field)
    INFO = "info"  # Potential issue worth reviewing


class Language(Enum):
    """Supported programming languages."""

    TYPESCRIPT = "typescript"
    RUST = "rust"
    PYTHON = "python"


@dataclass
class IDField:
    """Represents an ID field found in source code."""

    name: str  # Field name (e.g., "projectId", "project_id")
    declared_type: str  # Type as declared (e.g., "number", "i32", "int")
    expected_type: str  # Expected type for UUIDs (e.g., "string", "String", "str")
    language: Language
    file_path: Path
    line_number: int
    context: str  # Surrounding code context
    struct_or_interface: str | None = None  # Parent struct/interface name


@dataclass
class IDTypeIssue:
    """Represents a detected ID type issue."""

    severity: IssueSeverity
    message: str
    field: IDField
    suggestion: str
    category: str  # "integer_id", "parseint_uuid", "cross_language_mismatch"


@dataclass
class ParseIntUsage:
    """Represents usage of parseInt on an ID-like value."""

    variable_name: str
    file_path: Path
    line_number: int
    context: str
    is_id_field: bool  # True if variable name suggests it's an ID


class IDTypeChecker:
    """Analyzes codebases for ID type consistency issues across languages."""

    # Patterns that suggest a field is a UUID/string ID
    UUID_ID_PATTERNS = [
        r".*[Ii]d$",  # projectId, user_id, etc.
        r".*[Uu]uid$",  # userUuid
        r".*_uuid$",  # user_uuid
    ]

    # Fields that are commonly integers (not UUIDs)
    INTEGER_ID_EXCEPTIONS = [
        r".*[Ii]ndex$",  # arrayIndex
        r".*[Cc]ount$",  # itemCount
        r".*[Nn]um(ber)?$",  # lineNumber
        r".*[Ss]ize$",  # pageSize
        r".*[Ll]ength$",  # arrayLength
        r".*_idx$",  # array_idx
        r"port",  # port numbers
        r"sequence",  # sequence numbers
    ]

    def __init__(self, verbose: bool = False) -> None:
        """Initialize the checker.

        Args:
            verbose: Enable verbose output
        """
        self.verbose = verbose
        self.console = Console()
        self.id_fields: list[IDField] = []
        self.issues: list[IDTypeIssue] = []
        self.parseint_usages: list[ParseIntUsage] = []

    def analyze(self, paths: list[Path]) -> list[IDTypeIssue]:
        """Analyze the given paths for ID type issues.

        Args:
            paths: List of directories or files to analyze

        Returns:
            List of detected issues
        """
        self.id_fields: list[Any] = []
        self.issues: list[Any] = []
        self.parseint_usages: list[Any] = []

        for path in paths:
            if path.is_file():
                self._analyze_file(path)
            elif path.is_dir():
                self._analyze_directory(path)

        # Detect cross-language mismatches
        self._detect_cross_language_mismatches()

        return self.issues

    def _analyze_directory(self, directory: Path) -> None:
        """Analyze all relevant files in a directory."""
        # TypeScript/JavaScript
        for pattern in ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"]:
            for file in directory.glob(pattern):
                if self._should_skip_file(file):
                    continue
                self._analyze_typescript_file(file)

        # Rust
        for file in directory.glob("**/*.rs"):
            if self._should_skip_file(file):
                continue
            self._analyze_rust_file(file)

        # Python
        for file in directory.glob("**/*.py"):
            if self._should_skip_file(file):
                continue
            self._analyze_python_file(file)

    def _analyze_file(self, file: Path) -> None:
        """Analyze a single file based on its extension."""
        suffix = file.suffix.lower()
        if suffix in (".ts", ".tsx", ".js", ".jsx"):
            self._analyze_typescript_file(file)
        elif suffix == ".rs":
            self._analyze_rust_file(file)
        elif suffix == ".py":
            self._analyze_python_file(file)

    def _should_skip_file(self, file: Path) -> bool:
        """Check if a file should be skipped."""
        skip_dirs = {
            "node_modules",
            "dist",
            "build",
            ".next",
            "target",
            "__pycache__",
            ".git",
            "venv",
            ".venv",
        }
        return any(skip_dir in file.parts for skip_dir in skip_dirs)

    def _is_uuid_id_field(self, field_name: str) -> bool:
        """Check if a field name suggests it should be a UUID/string ID."""
        # First check if it matches exception patterns (definitely integer)
        for pattern in self.INTEGER_ID_EXCEPTIONS:
            if re.match(pattern, field_name, re.IGNORECASE):
                return False

        # Then check if it matches UUID ID patterns
        for pattern in self.UUID_ID_PATTERNS:
            if re.match(pattern, field_name):
                return True

        return False

    def _analyze_typescript_file(self, file: Path) -> None:
        """Analyze a TypeScript/JavaScript file."""
        try:
            content = file.read_text(encoding="utf-8")
        except Exception:
            return

        lines = content.split("\n")
        current_interface = None
        current_type = None

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track interface/type context
            interface_match = re.match(r"(?:export\s+)?interface\s+(\w+)", stripped)
            type_match = re.match(r"(?:export\s+)?type\s+(\w+)\s*=", stripped)

            if interface_match:
                current_interface = interface_match.group(1)
            elif type_match:
                current_type = type_match.group(1)
            elif stripped.startswith("}"):
                current_interface = None
                current_type = None

            # Look for parseInt usage on ID-like variables
            parseint_matches = re.finditer(
                r"parseInt\s*\(\s*(\w+(?:\.\w+)*)",
                line,
            )
            for match in parseint_matches:
                var_name = match.group(1)
                is_id = self._is_uuid_id_field(var_name.split(".")[-1])

                usage = ParseIntUsage(
                    variable_name=var_name,
                    file_path=file,
                    line_number=line_num,
                    context=stripped,
                    is_id_field=is_id,
                )
                self.parseint_usages.append(usage)

                if is_id:
                    self.issues.append(
                        IDTypeIssue(
                            severity=IssueSeverity.ERROR,
                            message=f"parseInt() called on ID field '{var_name}' - UUIDs cannot be parsed as integers",
                            field=IDField(
                                name=var_name,
                                declared_type="parseInt() call",
                                expected_type="string (no parsing needed)",
                                language=Language.TYPESCRIPT,
                                file_path=file,
                                line_number=line_num,
                                context=stripped,
                            ),
                            suggestion=f"Remove parseInt() - use '{var_name}' directly as a string",
                            category="parseint_uuid",
                        )
                    )

            # Look for Number() usage on ID-like variables
            number_matches = re.finditer(
                r"Number\s*\(\s*(\w+(?:\.\w+)*)",
                line,
            )
            for match in number_matches:
                var_name = match.group(1)
                if self._is_uuid_id_field(var_name.split(".")[-1]):
                    self.issues.append(
                        IDTypeIssue(
                            severity=IssueSeverity.ERROR,
                            message=f"Number() called on ID field '{var_name}' - UUIDs cannot be converted to numbers",
                            field=IDField(
                                name=var_name,
                                declared_type="Number() call",
                                expected_type="string (no conversion needed)",
                                language=Language.TYPESCRIPT,
                                file_path=file,
                                line_number=line_num,
                                context=stripped,
                            ),
                            suggestion=f"Remove Number() - use '{var_name}' directly as a string",
                            category="parseint_uuid",
                        )
                    )

            # Look for field declarations with number type
            # Pattern: fieldName: number or fieldName?: number
            field_match = re.match(
                r"(?:readonly\s+)?(\w+)\s*\??\s*:\s*(number|Number)(?:\s*\||\s*;|\s*$)",
                stripped,
            )
            if field_match:
                field_name = field_match.group(1)
                field_type = field_match.group(2)

                if self._is_uuid_id_field(field_name):
                    id_field = IDField(
                        name=field_name,
                        declared_type=field_type,
                        expected_type="string",
                        language=Language.TYPESCRIPT,
                        file_path=file,
                        line_number=line_num,
                        context=stripped,
                        struct_or_interface=current_interface or current_type,
                    )
                    self.id_fields.append(id_field)

                    self.issues.append(
                        IDTypeIssue(
                            severity=IssueSeverity.WARNING,
                            message=f"ID field '{field_name}' declared as number - should be string for UUIDs",
                            field=id_field,
                            suggestion=f"Change type from '{field_type}' to 'string'",
                            category="integer_id",
                        )
                    )

    def _analyze_rust_file(self, file: Path) -> None:
        """Analyze a Rust file."""
        try:
            content = file.read_text(encoding="utf-8")
        except Exception:
            return

        lines = content.split("\n")
        current_struct = None
        in_struct = False
        brace_depth = 0

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track struct context
            struct_match = re.match(r"(?:pub\s+)?struct\s+(\w+)", stripped)
            if struct_match:
                current_struct = struct_match.group(1)
                in_struct = True
                brace_depth = 0

            if in_struct:
                brace_depth += stripped.count("{") - stripped.count("}")
                if brace_depth <= 0 and "{" not in stripped:
                    in_struct = False
                    current_struct = None

            # Look for field declarations with integer type
            # Pattern: pub field_name: i32, or field_name: Option<i32>
            field_patterns = [
                r"(?:pub\s+)?(\w+)\s*:\s*(i32|i64|u32|u64|isize|usize)",
                r"(?:pub\s+)?(\w+)\s*:\s*Option<\s*(i32|i64|u32|u64|isize|usize)\s*>",
            ]

            for pattern in field_patterns:
                match = re.search(pattern, stripped)
                if match:
                    field_name = match.group(1)
                    field_type = match.group(2)

                    if self._is_uuid_id_field(field_name):
                        id_field = IDField(
                            name=field_name,
                            declared_type=field_type,
                            expected_type="String",
                            language=Language.RUST,
                            file_path=file,
                            line_number=line_num,
                            context=stripped,
                            struct_or_interface=current_struct,
                        )
                        self.id_fields.append(id_field)

                        self.issues.append(
                            IDTypeIssue(
                                severity=IssueSeverity.WARNING,
                                message=f"ID field '{field_name}' declared as {field_type} - should be String for UUIDs",
                                field=id_field,
                                suggestion=f"Change type from '{field_type}' to 'String' (or 'Option<String>')",
                                category="integer_id",
                            )
                        )

    def _analyze_python_file(self, file: Path) -> None:
        """Analyze a Python file."""
        try:
            content = file.read_text(encoding="utf-8")
        except Exception:
            return

        lines = content.split("\n")
        current_class = None

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Track class context
            class_match = re.match(r"class\s+(\w+)", stripped)
            if class_match:
                current_class = class_match.group(1)

            # Look for field declarations with int type
            # Patterns for dataclasses, Pydantic, and type hints
            field_patterns = [
                # dataclass: field_name: int = ...
                r"(\w+)\s*:\s*(int|Int)\s*(?:=|$)",
                # Pydantic: field_name: int = Field(...)
                r"(\w+)\s*:\s*(int|Int)\s*=\s*Field",
                # Optional[int]
                r"(\w+)\s*:\s*Optional\s*\[\s*(int|Int)\s*\]",
            ]

            for pattern in field_patterns:
                match = re.search(pattern, stripped)
                if match:
                    field_name = match.group(1)
                    field_type = match.group(2)

                    if self._is_uuid_id_field(field_name):
                        id_field = IDField(
                            name=field_name,
                            declared_type=field_type,
                            expected_type="str",
                            language=Language.PYTHON,
                            file_path=file,
                            line_number=line_num,
                            context=stripped,
                            struct_or_interface=current_class,
                        )
                        self.id_fields.append(id_field)

                        self.issues.append(
                            IDTypeIssue(
                                severity=IssueSeverity.WARNING,
                                message=f"ID field '{field_name}' declared as {field_type} - should be str for UUIDs",
                                field=id_field,
                                suggestion=f"Change type from '{field_type}' to 'str' (or 'Optional[str]')",
                                category="integer_id",
                            )
                        )

            # Look for int() calls on ID-like variables
            int_matches = re.finditer(r"int\s*\(\s*(\w+(?:\.\w+)*)", line)
            for match in int_matches:
                var_name = match.group(1)
                if self._is_uuid_id_field(var_name.split(".")[-1]):
                    self.issues.append(
                        IDTypeIssue(
                            severity=IssueSeverity.ERROR,
                            message=f"int() called on ID field '{var_name}' - UUIDs cannot be converted to integers",
                            field=IDField(
                                name=var_name,
                                declared_type="int() call",
                                expected_type="str (no conversion needed)",
                                language=Language.PYTHON,
                                file_path=file,
                                line_number=line_num,
                                context=stripped,
                            ),
                            suggestion=f"Remove int() - use '{var_name}' directly as a string",
                            category="parseint_uuid",
                        )
                    )

    def _detect_cross_language_mismatches(self) -> None:
        """Detect cases where the same ID field has different types across languages."""
        # Group fields by normalized name
        fields_by_name: dict[str, list[IDField]] = {}

        for f in self.id_fields:
            # Normalize name: convert to snake_case lowercase
            normalized = self._normalize_field_name(f.name)
            if normalized not in fields_by_name:
                fields_by_name[normalized] = []
            fields_by_name[normalized].append(f)

        # Check for type mismatches
        for _name, fields in fields_by_name.items():
            if len(fields) < 2:
                continue

            # Check if types are inconsistent
            types_by_language: dict[Any, Any] = {}
            for f in fields:
                lang = f.language.value
                if lang not in types_by_language:
                    types_by_language[lang] = set()
                types_by_language[lang].add(f.declared_type)

            # Report if there are mixed string and integer types
            has_string = any(
                t in ("string", "String", "str")
                for types in types_by_language.values()
                for t in types
            )
            has_integer = any(
                t in ("number", "i32", "i64", "u32", "u64", "int", "isize", "usize")
                for types in types_by_language.values()
                for t in types
            )

            if has_string and has_integer:
                for f in fields:
                    if f.declared_type in (
                        "number",
                        "i32",
                        "i64",
                        "u32",
                        "u64",
                        "int",
                        "isize",
                        "usize",
                    ):
                        self.issues.append(
                            IDTypeIssue(
                                severity=IssueSeverity.ERROR,
                                message=f"Cross-language type mismatch: '{f.name}' is string in some files but {f.declared_type} here",
                                field=f,
                                suggestion="Ensure consistent string types across all languages for UUID fields",
                                category="cross_language_mismatch",
                            )
                        )

    def _normalize_field_name(self, name: str) -> str:
        """Normalize field name to snake_case lowercase for comparison."""
        # Convert camelCase to snake_case
        result = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
        return result.lower()

    def generate_report(self) -> str:
        """Generate a text report of all issues."""
        if not self.issues:
            return "No ID type issues found."

        lines = ["ID Type Consistency Report", "=" * 50, ""]

        # Group by severity
        by_severity: dict[IssueSeverity, list[IDTypeIssue]] = {}
        for issue in self.issues:
            if issue.severity not in by_severity:
                by_severity[issue.severity] = []
            by_severity[issue.severity].append(issue)

        for severity in [IssueSeverity.ERROR, IssueSeverity.WARNING, IssueSeverity.INFO]:
            if severity not in by_severity:
                continue

            lines.append(f"\n{severity.value.upper()}S ({len(by_severity[severity])})")
            lines.append("-" * 40)

            for issue in by_severity[severity]:
                lines.append(f"\n  {issue.message}")
                lines.append(f"    File: {issue.field.file_path}:{issue.field.line_number}")
                if issue.field.struct_or_interface:
                    lines.append(f"    In: {issue.field.struct_or_interface}")
                lines.append(f"    Context: {issue.field.context}")
                lines.append(f"    Suggestion: {issue.suggestion}")

        return "\n".join(lines)

    def generate_rich_report(self) -> None:
        """Generate a rich console report."""
        if not self.issues:
            self.console.print(
                Panel("[green]No ID type issues found![/green]", title="ID Type Check")
            )
            return

        # Summary
        errors = sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)
        warnings = sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)

        summary = f"[red]{errors} errors[/red], [yellow]{warnings} warnings[/yellow]"
        self.console.print(Panel(summary, title="ID Type Check Summary"))

        # Detailed table
        table = Table(title="ID Type Issues", show_lines=True)
        table.add_column("Severity", style="bold")
        table.add_column("File:Line")
        table.add_column("Field")
        table.add_column("Issue")
        table.add_column("Suggestion")

        for issue in sorted(self.issues, key=lambda i: (i.severity.value, str(i.field.file_path))):
            severity_style = {
                IssueSeverity.ERROR: "[red]ERROR[/red]",
                IssueSeverity.WARNING: "[yellow]WARNING[/yellow]",
                IssueSeverity.INFO: "[blue]INFO[/blue]",
            }[issue.severity]

            # Shorten file path for display
            file_loc = f"{issue.field.file_path.name}:{issue.field.line_number}"

            field_name = issue.field.name
            if issue.field.struct_or_interface:
                field_name = f"{issue.field.struct_or_interface}.{field_name}"

            table.add_row(
                severity_style,
                file_loc,
                field_name,
                issue.message,
                issue.suggestion,
            )

        self.console.print(table)

    def get_statistics(self) -> dict:
        """Get analysis statistics."""
        return {
            "total_issues": len(self.issues),
            "errors": sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR),
            "warnings": sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING),
            "info": sum(1 for i in self.issues if i.severity == IssueSeverity.INFO),
            "id_fields_found": len(self.id_fields),
            "parseint_usages": len(self.parseint_usages),
            "by_category": {
                "parseint_uuid": sum(1 for i in self.issues if i.category == "parseint_uuid"),
                "integer_id": sum(1 for i in self.issues if i.category == "integer_id"),
                "cross_language_mismatch": sum(
                    1 for i in self.issues if i.category == "cross_language_mismatch"
                ),
            },
            "by_language": {
                "typescript": sum(
                    1 for i in self.issues if i.field.language == Language.TYPESCRIPT
                ),
                "rust": sum(1 for i in self.issues if i.field.language == Language.RUST),
                "python": sum(1 for i in self.issues if i.field.language == Language.PYTHON),
            },
        }
