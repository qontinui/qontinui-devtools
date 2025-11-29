"""Dead code detection for Python codebases.

This module provides functionality to detect unused code including:
- Unused functions
- Unused classes
- Unused imports
- Unused variables

The detector performs static analysis using AST traversal to identify
definitions and usages across the codebase.
"""

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class DeadCode:
    """A piece of dead code.

    Attributes:
        type: Type of dead code ("function", "class", "import", "variable")
        name: Name of the unused element
        file_path: Path to the file containing the dead code
        line_number: Line number where the dead code is defined
        reason: Explanation of why this is considered dead code
        confidence: Confidence level (0-1) that this is truly dead code
    """

    type: str
    name: str
    file_path: str
    line_number: int
    reason: str
    confidence: float


class DefinitionCollector(ast.NodeVisitor):
    """Collect all definitions in a module."""

    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        self.functions: dict[str, int] = {}
        self.classes: dict[str, int] = {}
        self.imports: dict[str, int] = {}
        self.variables: dict[str, int] = {}
        self._in_class = False
        self._in_function = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        # Skip special methods like __init__, __str__, etc. (they're used implicitly)
        # Don't skip private methods, but flag them later
        if not (node.name.startswith("__") and node.name.endswith("__")):
            # Only track module-level and class-level functions
            if not self._in_function:
                self.functions[node.name] = node.lineno

        # Visit nested functions
        old_in_function = self._in_function
        self._in_function = True
        self.generic_visit(node)
        self._in_function = old_in_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        if not (node.name.startswith("__") and node.name.endswith("__")):
            if not self._in_function:
                self.functions[node.name] = node.lineno

        old_in_function = self._in_function
        self._in_function = True
        self.generic_visit(node)
        self._in_function = old_in_function

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        if not node.name.startswith("_"):
            self.classes[node.name] = node.lineno

        # Visit class body
        old_in_class = self._in_class
        self._in_class = True
        self.generic_visit(node)
        self._in_class = old_in_class

    def visit_Import(self, node: ast.Import) -> None:
        """Visit import statement."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node.lineno
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit from...import statement."""
        for alias in node.names:
            if alias.name == "*":
                continue
            name = alias.asname if alias.asname else alias.name
            self.imports[name] = node.lineno
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit assignment statement."""
        # Only track module-level variables
        if not self._in_function and not self._in_class:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # Skip dunder variables and private variables
                    if not target.id.startswith("_"):
                        self.variables[target.id] = node.lineno
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visit annotated assignment statement."""
        if not self._in_function and not self._in_class:
            if isinstance(node.target, ast.Name):
                if not node.target.id.startswith("_"):
                    self.variables[node.target.id] = node.lineno
        self.generic_visit(node)


class UsageCollector(ast.NodeVisitor):
    """Collect all usages of names in a module."""

    def __init__(self) -> None:
        self.used_names: set[str] = set()

    def visit_Name(self, node: ast.Name) -> None:
        """Visit name reference."""
        if isinstance(node.ctx, (ast.Load, ast.Del)):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Visit attribute access."""
        # Track the module/object being accessed (e.g., os.getcwd -> track 'os')
        if isinstance(node.value, ast.Name):
            self.used_names.add(node.value.id)
        # Also track the attribute name itself
        self.used_names.add(node.attr)
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        """Visit function call."""
        # Handle direct function calls
        if isinstance(node.func, ast.Name):
            self.used_names.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.used_names.add(node.func.attr)
            # Also track the object being called on
            if isinstance(node.func.value, ast.Name):
                self.used_names.add(node.func.value.id)
        self.generic_visit(node)


class DeadCodeDetector:
    """Detect unused code in Python projects.

    This detector performs static analysis to find:
    - Unused functions (not called anywhere in the codebase)
    - Unused classes (not instantiated or referenced)
    - Unused imports (imported but never used)
    - Unused module-level variables (defined but never used)

    The detector uses AST analysis to track definitions and usages
    across all Python files in the project.
    """

    def __init__(self, root_path: str) -> None:
        """Initialize the detector.

        Args:
            root_path: Root directory to analyze
        """
        self.root_path = Path(root_path)
        self._definitions: dict[str, DefinitionCollector] = {}
        self._all_usages: set[str] = set()
        self._python_files: list[Path] = []

    def _find_python_files(self) -> list[Path]:
        """Find all Python files in the project."""
        python_files = []
        for path in self.root_path.rglob("*.py"):
            # Skip common directories
            parts = path.parts
            skip_dirs = {
                "__pycache__",
                ".pytest_cache",
                ".git",
                ".tox",
                "venv",
                ".venv",
                "env",
                ".env",
                "node_modules",
            }
            if any(skip_dir in parts for skip_dir in skip_dirs):
                continue
            python_files.append(path)
        return python_files

    def _parse_file(self, file_path: Path) -> ast.AST | None:
        """Parse a Python file into an AST.

        Args:
            file_path: Path to the Python file

        Returns:
            AST node or None if parsing fails
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()
            return ast.parse(source, filename=str(file_path))
        except (SyntaxError, UnicodeDecodeError):
            return None

    def _scan_definitions(self) -> None:
        """Scan all files for definitions."""
        self._python_files = self._find_python_files()

        for file_path in self._python_files:
            tree = self._parse_file(file_path)
            if tree is None:
                continue

            collector = DefinitionCollector(str(file_path))
            collector.visit(tree)
            self._definitions[str(file_path)] = collector

    def _scan_usages(self) -> None:
        """Scan all files for usages."""
        for file_path in self._python_files:
            tree = self._parse_file(file_path)
            if tree is None:
                continue

            collector = UsageCollector()
            collector.visit(tree)
            self._all_usages.update(collector.used_names)

    def _find_unused(self) -> list[DeadCode]:
        """Find all unused code by comparing definitions and usages."""
        dead_code: list[DeadCode] = []

        # Check each file's definitions
        for file_path, definitions in self._definitions.items():
            # Check unused functions
            for func_name, line_num in definitions.functions.items():
                if func_name not in self._all_usages:
                    # Check for common patterns that shouldn't be flagged
                    confidence = self._calculate_confidence(func_name, "function")
                    if confidence > 0:
                        dead_code.append(
                            DeadCode(
                                type="function",
                                name=func_name,
                                file_path=file_path,
                                line_number=line_num,
                                reason=f"Function '{func_name}' is defined but never called",
                                confidence=confidence,
                            )
                        )

            # Check unused classes
            for class_name, line_num in definitions.classes.items():
                if class_name not in self._all_usages:
                    confidence = self._calculate_confidence(class_name, "class")
                    if confidence > 0:
                        dead_code.append(
                            DeadCode(
                                type="class",
                                name=class_name,
                                file_path=file_path,
                                line_number=line_num,
                                reason=f"Class '{class_name}' is defined but never used",
                                confidence=confidence,
                            )
                        )

            # Check unused imports
            for import_name, line_num in definitions.imports.items():
                if import_name not in self._all_usages:
                    dead_code.append(
                        DeadCode(
                            type="import",
                            name=import_name,
                            file_path=file_path,
                            line_number=line_num,
                            reason=f"Import '{import_name}' is never used",
                            confidence=0.95,  # High confidence for unused imports
                        )
                    )

            # Check unused variables
            for var_name, line_num in definitions.variables.items():
                if var_name not in self._all_usages:
                    confidence = self._calculate_confidence(var_name, "variable")
                    if confidence > 0:
                        dead_code.append(
                            DeadCode(
                                type="variable",
                                name=var_name,
                                file_path=file_path,
                                line_number=line_num,
                                reason=f"Variable '{var_name}' is defined but never used",
                                confidence=confidence,
                            )
                        )

        return dead_code

    def _calculate_confidence(self, name: str, code_type: str) -> float:
        """Calculate confidence that this is truly dead code.

        Lower confidence for:
        - Public API functions (might be used externally)
        - Test fixtures
        - CLI entry points
        - Common patterns (main, setup, etc.)

        Args:
            name: Name of the code element
            code_type: Type of code (function, class, variable)

        Returns:
            Confidence level between 0 and 1
        """
        # Common entry points and API patterns
        low_confidence_patterns = {
            "main",
            "setup",
            "teardown",
            "setUp",
            "tearDown",
            "setUpClass",
            "tearDownClass",
        }

        if name in low_confidence_patterns:
            return 0.3

        # Test fixtures
        if name.startswith("test_") or name.startswith("fixture_"):
            return 0.4

        # CLI commands
        if name.endswith("_command") or name.endswith("_cli"):
            return 0.5

        # Everything else gets high confidence
        if code_type == "import":
            return 0.95
        return 0.85

    def analyze(self) -> list[DeadCode]:
        """Find all dead code in the project.

        Returns:
            List of DeadCode objects representing unused code
        """
        # Step 1: Find all definitions
        self._scan_definitions()

        # Step 2: Find all usages
        self._scan_usages()

        # Step 3: Compare to find unused code
        return self._find_unused()

    def find_unused_functions(self) -> list[DeadCode]:
        """Find unused functions only.

        Returns:
            List of DeadCode objects representing unused functions
        """
        all_dead_code = self.analyze()
        return [dc for dc in all_dead_code if dc.type == "function"]

    def find_unused_classes(self) -> list[DeadCode]:
        """Find unused classes only.

        Returns:
            List of DeadCode objects representing unused classes
        """
        all_dead_code = self.analyze()
        return [dc for dc in all_dead_code if dc.type == "class"]

    def find_unused_imports(self) -> list[DeadCode]:
        """Find unused imports only.

        Returns:
            List of DeadCode objects representing unused imports
        """
        all_dead_code = self.analyze()
        return [dc for dc in all_dead_code if dc.type == "import"]

    def find_unused_variables(self) -> list[DeadCode]:
        """Find unused module-level variables only.

        Returns:
            List of DeadCode objects representing unused variables
        """
        all_dead_code = self.analyze()
        return [dc for dc in all_dead_code if dc.type == "variable"]

    def get_stats(self) -> dict[str, int]:
        """Get statistics about dead code.

        Returns:
            Dictionary with counts of each type of dead code
        """
        all_dead_code = self.analyze()
        return {
            "total": len(all_dead_code),
            "functions": len([dc for dc in all_dead_code if dc.type == "function"]),
            "classes": len([dc for dc in all_dead_code if dc.type == "class"]),
            "imports": len([dc for dc in all_dead_code if dc.type == "import"]),
            "variables": len([dc for dc in all_dead_code if dc.type == "variable"]),
        }
