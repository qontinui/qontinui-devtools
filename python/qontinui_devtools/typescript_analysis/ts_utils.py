"""Utilities for parsing TypeScript/JavaScript files.

This module provides functions to parse and analyze TS/JS files without
requiring Node.js or external dependencies.
"""

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ImportStatement:
    """Represents an import statement in TypeScript/JavaScript."""

    source: str  # The module being imported from
    names: list[str]  # List of imported names
    default_import: str | None  # Default import name if present
    namespace_import: str | None  # Namespace import name (e.g., * as foo)
    is_type_only: bool  # True if this is a type-only import
    line_number: int
    raw_statement: str


@dataclass
class ExportStatement:
    """Represents an export statement in TypeScript/JavaScript."""

    name: str
    export_type: str  # "function", "class", "const", "type", "interface", "default"
    line_number: int
    is_type_only: bool  # True if this is a type-only export


def find_ts_js_files(root_path: Path) -> list[Path]:
    """Find all TypeScript and JavaScript files in a directory tree.

    Args:
        root_path: Root directory to search

    Returns:
        List of paths to TS/JS files
    """
    patterns = ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"]
    files = []

    for pattern in patterns:
        files.extend(root_path.glob(pattern))

    # Filter out node_modules, dist, build directories
    filtered = []
    exclude_dirs = {"node_modules", "dist", "build", ".next", "out", "__tests__"}

    for file in files:
        if not any(exclude_dir in file.parts for exclude_dir in exclude_dirs):
            filtered.append(file)

    return sorted(filtered)


def extract_imports(file_path: Path) -> list[ImportStatement]:
    """Extract import statements from a TypeScript/JavaScript file.

    Args:
        file_path: Path to the TS/JS file

    Returns:
        List of ImportStatement objects
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return []

    imports = []
    lines = content.split("\n")

    # Patterns for different import styles
    # 1. import foo from 'bar'
    # 2. import { foo, bar } from 'baz'
    # 3. import * as foo from 'bar'
    # 4. import type { foo } from 'bar'
    # 5. import 'side-effect'
    # 6. const foo = require('bar')

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Skip comments
        if line.startswith("//") or line.startswith("/*") or line.startswith("*"):
            continue

        # Handle ES6 imports
        if line.startswith("import"):
            is_type_only = "import type" in line

            # Extract the source module
            source_match = re.search(r'from\s+[\'"]([^\'"]+)[\'"]', line)
            if not source_match:
                # Side-effect import: import 'foo'
                source_match = re.search(r'import\s+[\'"]([^\'"]+)[\'"]', line)
                if source_match:
                    imports.append(
                        ImportStatement(
                            source=source_match.group(1),
                            names=[],
                            default_import=None,
                            namespace_import=None,
                            is_type_only=is_type_only,
                            line_number=line_num,
                            raw_statement=line,
                        )
                    )
                continue

            source = source_match.group(1)

            # Extract import names
            names = []
            default_import = None
            namespace_import = None

            # Check for namespace import: import * as foo
            namespace_match = re.search(r"import\s+\*\s+as\s+(\w+)", line)
            if namespace_match:
                namespace_import = namespace_match.group(1)
            else:
                # Check for default import: import foo from
                default_match = re.search(r"import\s+(\w+)\s+from", line)
                if default_match:
                    default_import = default_match.group(1)

                # Check for named imports: import { foo, bar }
                named_match = re.search(r"\{([^}]+)\}", line)
                if named_match:
                    named_imports = named_match.group(1)
                    # Split by comma and clean up
                    for name in named_imports.split(","):
                        name = name.strip()
                        # Handle 'as' aliases: foo as bar
                        if " as " in name:
                            name = name.split(" as ")[1].strip()
                        names.append(name)

            imports.append(
                ImportStatement(
                    source=source,
                    names=names,
                    default_import=default_import,
                    namespace_import=namespace_import,
                    is_type_only=is_type_only,
                    line_number=line_num,
                    raw_statement=line,
                )
            )

        # Handle CommonJS require
        elif "require(" in line:
            require_match = re.search(r'require\([\'"]([^\'"]+)[\'"]\)', line)
            if require_match:
                source = require_match.group(1)

                # Try to extract the variable name
                var_match = re.search(r"(?:const|let|var)\s+(\w+)\s*=", line)
                default_import = var_match.group(1) if var_match else None

                imports.append(
                    ImportStatement(
                        source=source,
                        names=[],
                        default_import=default_import,
                        namespace_import=None,
                        is_type_only=False,
                        line_number=line_num,
                        raw_statement=line,
                    )
                )

    return imports


def extract_exports(file_path: Path) -> list[ExportStatement]:
    """Extract export statements from a TypeScript/JavaScript file.

    Args:
        file_path: Path to the TS/JS file

    Returns:
        List of ExportStatement objects
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return []

    exports = []
    lines = content.split("\n")

    for line_num, line in enumerate(lines, 1):
        line = line.strip()

        # Skip comments
        if line.startswith("//") or line.startswith("/*") or line.startswith("*"):
            continue

        if not line.startswith("export"):
            continue

        is_type_only = "export type" in line

        # export default
        if "export default" in line:
            # Try to extract name
            name_match = re.search(r"export\s+default\s+(?:function|class)?\s*(\w+)", line)
            name = name_match.group(1) if name_match else "default"

            exports.append(
                ExportStatement(
                    name=name,
                    export_type="default",
                    line_number=line_num,
                    is_type_only=is_type_only,
                )
            )

        # export function/class/const/interface/type
        elif re.search(r"export\s+(?:async\s+)?function\s+(\w+)", line):
            match = re.search(r"export\s+(?:async\s+)?function\s+(\w+)", line)
            exports.append(
                ExportStatement(
                    name=match.group(1),
                    export_type="function",
                    line_number=line_num,
                    is_type_only=is_type_only,
                )
            )

        elif re.search(r"export\s+class\s+(\w+)", line):
            match = re.search(r"export\s+class\s+(\w+)", line)
            exports.append(
                ExportStatement(
                    name=match.group(1),
                    export_type="class",
                    line_number=line_num,
                    is_type_only=is_type_only,
                )
            )

        elif re.search(r"export\s+(?:const|let|var)\s+(\w+)", line):
            match = re.search(r"export\s+(?:const|let|var)\s+(\w+)", line)
            exports.append(
                ExportStatement(
                    name=match.group(1),
                    export_type="const",
                    line_number=line_num,
                    is_type_only=is_type_only,
                )
            )

        elif re.search(r"export\s+interface\s+(\w+)", line):
            match = re.search(r"export\s+interface\s+(\w+)", line)
            exports.append(
                ExportStatement(
                    name=match.group(1),
                    export_type="interface",
                    line_number=line_num,
                    is_type_only=True,
                )
            )

        elif re.search(r"export\s+type\s+(\w+)", line):
            match = re.search(r"export\s+type\s+(\w+)", line)
            exports.append(
                ExportStatement(
                    name=match.group(1), export_type="type", line_number=line_num, is_type_only=True
                )
            )

        # export { foo, bar }
        elif re.search(r"export\s+\{([^}]+)\}", line):
            match = re.search(r"export\s+\{([^}]+)\}", line)
            names_str = match.group(1)
            for name in names_str.split(","):
                name = name.strip()
                # Handle 'as' aliases
                if " as " in name:
                    name = name.split(" as ")[0].strip()
                exports.append(
                    ExportStatement(
                        name=name,
                        export_type="const",
                        line_number=line_num,
                        is_type_only=is_type_only,
                    )
                )

    return exports


def resolve_import_path(import_source: str, from_file: Path, root_path: Path) -> Path | None:
    """Resolve an import source to an actual file path.

    Args:
        import_source: The import source string (e.g., './foo', '@/components/bar')
        from_file: The file containing the import
        root_path: The project root path

    Returns:
        Resolved file path or None if not found
    """
    # Skip external modules (no ./ or ../ or @/)
    if not import_source.startswith(("..", ".", "@", "~")):
        return None

    # Handle path aliases
    if import_source.startswith("@/"):
        # Assume @ maps to src directory
        import_source = import_source.replace("@/", "src/")
        base_path = root_path
    elif import_source.startswith("~/"):
        import_source = import_source.replace("~/", "")
        base_path = root_path
    else:
        # Relative import
        base_path = from_file.parent

    # Try different extensions
    extensions = [".ts", ".tsx", ".js", ".jsx", ""]

    for ext in extensions:
        # Try as file
        resolved = (base_path / f"{import_source}{ext}").resolve()
        if resolved.exists() and resolved.is_file():
            return resolved

        # Try as directory with index file
        index_file = (base_path / import_source / f"index{ext}").resolve()
        if index_file.exists() and index_file.is_file():
            return index_file

    return None


def module_path_from_file(file_path: Path, root_path: Path) -> str:
    """Convert a file path to a module path.

    Args:
        file_path: Path to the file
        root_path: Project root path

    Returns:
        Module path string
    """
    try:
        relative = file_path.relative_to(root_path)
        # Remove extension
        module_path = str(relative.with_suffix(""))
        # Convert path separators to dots
        return module_path.replace("/", ".").replace("\\", ".")
    except ValueError:
        return str(file_path)


def count_lines_of_code(file_path: Path) -> dict[str, int]:
    """Count lines of code in a file.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with 'total', 'code', 'comment', 'blank' counts
    """
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception:
        return {"total": 0, "code": 0, "comment": 0, "blank": 0}

    lines = content.split("\n")
    total = len(lines)
    blank = 0
    comment = 0
    code = 0

    in_multiline_comment = False

    for line in lines:
        stripped = line.strip()

        if not stripped:
            blank += 1
        elif stripped.startswith("//"):
            comment += 1
        elif stripped.startswith("/*"):
            comment += 1
            in_multiline_comment = True
        elif in_multiline_comment:
            comment += 1
            if "*/" in stripped:
                in_multiline_comment = False
        else:
            code += 1

    return {"total": total, "code": code, "comment": comment, "blank": blank}
