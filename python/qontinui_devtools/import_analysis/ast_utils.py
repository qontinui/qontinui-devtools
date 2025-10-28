"""AST utilities for extracting import statements from Python source files.

This module provides tools for parsing Python files using the AST module
and extracting import information without executing the code.
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ImportStatement:
    """A single import statement extracted from Python source code.

    Attributes:
        module: The module being imported (e.g., 'os.path', 'typing')
        imported_names: List of specific names imported (empty for 'import X')
        is_from_import: True for 'from X import Y', False for 'import X'
        line_number: Line number where import appears
        file_path: Absolute path to the file containing the import
    """

    module: str
    imported_names: list[str]
    is_from_import: bool
    line_number: int
    file_path: str

    def __str__(self) -> str:
        """Human-readable representation of the import."""
        if self.is_from_import:
            if self.imported_names:
                names = ", ".join(self.imported_names)
                return f"from {self.module} import {names}"
            else:
                return f"from {self.module} import *"
        else:
            return f"import {self.module}"


class ImportExtractor(ast.NodeVisitor):
    """Extract all import statements from an AST.

    This visitor walks through the AST and collects all import and
    from-import statements, storing them as ImportStatement objects.
    """

    def __init__(self, file_path: str) -> None:
        """Initialize the extractor.

        Args:
            file_path: Path to the file being analyzed
        """
        self.file_path = file_path
        self.imports: list[ImportStatement] = []

    def visit_Import(self, node: ast.Import) -> None:
        """Visit an 'import X' statement.

        Args:
            node: The Import AST node
        """
        for alias in node.names:
            import_stmt = ImportStatement(
                module=alias.name,
                imported_names=[],
                is_from_import=False,
                line_number=node.lineno,
                file_path=self.file_path,
            )
            self.imports.append(import_stmt)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit a 'from X import Y' statement.

        Args:
            node: The ImportFrom AST node
        """
        # Handle relative imports
        if node.module is None:
            # This is a relative import like 'from . import foo'
            # We'll skip these for now as they require package context
            self.generic_visit(node)
            return

        # Handle 'from X import *'
        if any(alias.name == "*" for alias in node.names):
            import_stmt = ImportStatement(
                module=node.module,
                imported_names=["*"],
                is_from_import=True,
                line_number=node.lineno,
                file_path=self.file_path,
            )
            self.imports.append(import_stmt)
        else:
            # Handle 'from X import a, b, c'
            imported_names = [alias.name for alias in node.names]
            import_stmt = ImportStatement(
                module=node.module,
                imported_names=imported_names,
                is_from_import=True,
                line_number=node.lineno,
                file_path=self.file_path,
            )
            self.imports.append(import_stmt)

        self.generic_visit(node)


def extract_imports(file_path: str) -> list[ImportStatement]:
    """Parse a Python file and extract all import statements.

    Args:
        file_path: Path to the Python file to analyze

    Returns:
        List of ImportStatement objects found in the file

    Raises:
        SyntaxError: If the file contains invalid Python syntax
        FileNotFoundError: If the file doesn't exist
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        source = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # Try with a different encoding
        try:
            source = path.read_text(encoding="latin-1")
        except Exception as e:
            raise ValueError(f"Could not read file {file_path}: {e}") from e

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in {file_path}: {e}") from e

    extractor = ImportExtractor(str(path.resolve()))
    extractor.visit(tree)

    return extractor.imports


def module_path_from_file(file_path: str, root_path: str) -> str:
    """Convert a file path to a Python module path.

    Args:
        file_path: Absolute path to a Python file
        root_path: Root directory of the project

    Returns:
        Module path (e.g., 'foo.bar.baz' for 'src/foo/bar/baz.py')

    Example:
        >>> module_path_from_file('/project/src/foo/bar.py', '/project/src')
        'foo.bar'
    """
    file_path_obj = Path(file_path).resolve()
    root_path_obj = Path(root_path).resolve()

    try:
        relative = file_path_obj.relative_to(root_path_obj)
    except ValueError:
        # File is not under root_path
        return str(file_path_obj.stem)

    # Remove .py extension and convert path separators to dots
    parts = list(relative.parts)
    if parts[-1].endswith(".py"):
        parts[-1] = parts[-1][:-3]

    # Remove __init__ from the end
    if parts[-1] == "__init__":
        parts = parts[:-1]

    # Return empty string if no parts remain
    if not parts:
        return ""

    return ".".join(parts)


def resolve_import_to_module(
    import_stmt: ImportStatement, current_module: str, root_path: str
) -> str:
    """Resolve an import statement to an absolute module path.

    This handles both absolute and relative imports, converting them to
    absolute module paths for dependency graph construction.

    Args:
        import_stmt: The import statement to resolve
        current_module: The module containing this import
        root_path: Root path of the project

    Returns:
        Absolute module path
    """
    # For now, we'll just return the module as-is
    # A more sophisticated implementation would handle:
    # 1. Relative imports (from . import foo)
    # 2. Package resolution
    # 3. sys.path considerations
    return import_stmt.module


def find_python_files(root_path: str) -> list[str]:
    """Find all Python files in a directory tree.

    Args:
        root_path: Root directory to search

    Returns:
        List of absolute paths to Python files
    """
    root = Path(root_path).resolve()
    python_files: list[str] = []

    for path in root.rglob("*.py"):
        # Skip common directories that shouldn't be analyzed
        skip_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "build", "dist"}

        if any(skip_dir in path.parts for skip_dir in skip_dirs):
            continue

        python_files.append(str(path))

    return python_files


def get_module_file_path(module_name: str, root_path: str) -> str | None:
    """Try to find the file path for a given module name.

    Args:
        module_name: Module name (e.g., 'foo.bar.baz')
        root_path: Root directory of the project

    Returns:
        Absolute file path if found, None otherwise
    """
    root = Path(root_path).resolve()
    parts = module_name.split(".")

    # Try as a module file
    module_file = root / Path(*parts[:-1]) / f"{parts[-1]}.py"
    if module_file.exists():
        return str(module_file)

    # Try as a package
    package_init = root / Path(*parts) / "__init__.py"
    if package_init.exists():
        return str(package_init)

    return None
