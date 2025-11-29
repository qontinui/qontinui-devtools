"""API snapshot creation and comparison utilities."""

import ast
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .models import ClassSignature, FunctionSignature

logger = logging.getLogger(__name__)


class APISnapshot:
    """Creates and manages API snapshots for regression detection."""

    def __init__(self) -> None:
        """Initialize API snapshot manager."""
        self.functions: dict[str, FunctionSignature] = {}
        self.classes: dict[str, ClassSignature] = {}
        self.metadata: dict[str, Any] = {}

    def create_snapshot(self, source_path: Path, version: str = "") -> None:
        """
        Create snapshot of all public APIs in the source path.

        Args:
            source_path: Path to source code directory
            version: Version identifier for the snapshot
        """
        self.functions.clear()
        self.classes.clear()
        self.metadata = {
            "version": version,
            "timestamp": datetime.now().isoformat(),
            "source_path": str(source_path),
        }

        if not source_path.exists():
            raise ValueError(f"Source path does not exist: {source_path}")

        # Scan all Python files
        python_files = list(source_path.rglob("*.py"))
        logger.info(f"Scanning {len(python_files)} Python files for API snapshot")

        for py_file in python_files:
            try:
                self._scan_file(py_file, source_path)
            except Exception as e:
                logger.warning(f"Error scanning {py_file}: {e}")

        logger.info(
            f"Snapshot created: {len(self.functions)} functions, {len(self.classes)} classes"
        )

    def _scan_file(self, file_path: Path, base_path: Path) -> None:
        """
        Scan a Python file and extract API signatures.

        Args:
            file_path: Path to Python file
            base_path: Base path for relative module paths
        """
        try:
            with open(file_path, encoding="utf-8") as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))
            module_path = self._get_module_path(file_path, base_path)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    sig = self._extract_function_signature(node, module_path)
                    if sig and sig.is_public:
                        key = f"{module_path}.{sig.name}"
                        self.functions[key] = sig

                elif isinstance(node, ast.ClassDef):
                    cls_sig = self._extract_class_signature(node, module_path)
                    if cls_sig and cls_sig.is_public:
                        key = f"{module_path}.{cls_sig.name}"
                        self.classes[key] = cls_sig

        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {e}")

    def _get_module_path(self, file_path: Path, base_path: Path) -> str:
        """Convert file path to module path."""
        try:
            relative = file_path.relative_to(base_path)
            parts = list(relative.parts[:-1]) + [relative.stem]
            return ".".join(parts)
        except ValueError:
            return file_path.stem

    def _extract_function_signature(
        self, node: ast.FunctionDef, module_path: str
    ) -> FunctionSignature | None:
        """Extract function signature from AST node."""
        try:
            # Check if public
            is_public = not node.name.startswith("_")

            # Extract parameters
            parameters = []
            for arg in node.args.args:
                param_name = arg.arg
                if arg.annotation:
                    annotation = ast.unparse(arg.annotation)
                    param_name += f": {annotation}"
                parameters.append(param_name)

            # Extract return type
            return_type = None
            if node.returns:
                return_type = ast.unparse(node.returns)

            # Extract decorators
            decorators = [ast.unparse(dec) for dec in node.decorator_list]

            # Extract docstring
            docstring = ast.get_docstring(node)

            return FunctionSignature(
                name=node.name,
                parameters=parameters,
                return_type=return_type,
                module_path=module_path,
                decorators=decorators,
                docstring=docstring,
                is_async=isinstance(node, ast.AsyncFunctionDef),
                is_public=is_public,
                line_number=node.lineno,
            )
        except Exception as e:
            logger.debug(f"Error extracting function signature for {node.name}: {e}")
            return None

    def _extract_class_signature(
        self, node: ast.ClassDef, module_path: str
    ) -> ClassSignature | None:
        """Extract class signature from AST node."""
        try:
            # Check if public
            is_public = not node.name.startswith("_")

            # Extract base classes
            base_classes = []
            for base in node.bases:
                base_classes.append(ast.unparse(base))

            # Extract decorators
            decorators = [ast.unparse(dec) for dec in node.decorator_list]

            # Extract docstring
            docstring = ast.get_docstring(node)

            # Extract methods
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    method_sig = self._extract_function_signature(item, module_path)
                    if method_sig:
                        methods.append(method_sig)

            return ClassSignature(
                name=node.name,
                module_path=module_path,
                methods=methods,
                base_classes=base_classes,
                decorators=decorators,
                docstring=docstring,
                is_public=is_public,
                line_number=node.lineno,
            )
        except Exception as e:
            logger.debug(f"Error extracting class signature for {node.name}: {e}")
            return None

    def save_snapshot(self, output_path: Path) -> None:
        """
        Save snapshot to JSON file.

        Args:
            output_path: Path to save snapshot file
        """
        data = {
            "metadata": self.metadata,
            "functions": {k: v.to_dict() for k, v in self.functions.items()},
            "classes": {k: v.to_dict() for k, v in self.classes.items()},
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Snapshot saved to {output_path}")

    def load_snapshot(self, input_path: Path) -> None:
        """
        Load snapshot from JSON file.

        Args:
            input_path: Path to snapshot file
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Snapshot file not found: {input_path}")

        with open(input_path, encoding="utf-8") as f:
            data = json.load(f)

        self.metadata = data.get("metadata", {})
        self.functions = {
            k: FunctionSignature.from_dict(v) for k, v in data.get("functions", {}).items()
        }
        self.classes = {k: ClassSignature.from_dict(v) for k, v in data.get("classes", {}).items()}

        logger.info(
            f"Snapshot loaded: {len(self.functions)} functions, {len(self.classes)} classes"
        )

    def compare_snapshots(
        self, other: "APISnapshot"
    ) -> tuple[set[str], set[str], set[str], set[str]]:
        """
        Compare this snapshot with another.

        Args:
            other: Another snapshot to compare with

        Returns:
            Tuple of (added_functions, removed_functions, modified_functions, unchanged)
        """
        current_keys = set(self.functions.keys())
        other_keys = set(other.functions.keys())

        removed = other_keys - current_keys
        added = current_keys - other_keys
        common = current_keys & other_keys

        modified = set()
        unchanged = set()

        for key in common:
            if self.functions[key] != other.functions[key]:
                modified.add(key)
            else:
                unchanged.add(key)

        return added, removed, modified, unchanged

    def compare_classes(
        self, other: "APISnapshot"
    ) -> tuple[set[str], set[str], set[str], set[str]]:
        """
        Compare class signatures with another snapshot.

        Args:
            other: Another snapshot to compare with

        Returns:
            Tuple of (added_classes, removed_classes, modified_classes, unchanged)
        """
        current_keys = set(self.classes.keys())
        other_keys = set(other.classes.keys())

        removed = other_keys - current_keys
        added = current_keys - other_keys
        common = current_keys & other_keys

        modified = set()
        unchanged = set()

        for key in common:
            if self._class_modified(self.classes[key], other.classes[key]):
                modified.add(key)
            else:
                unchanged.add(key)

        return added, removed, modified, unchanged

    def _class_modified(self, cls1: ClassSignature, cls2: ClassSignature) -> bool:
        """Check if two class signatures differ."""
        if cls1.base_classes != cls2.base_classes:
            return True

        # Compare method signatures
        methods1 = {m.name: m for m in cls1.methods}
        methods2 = {m.name: m for m in cls2.methods}

        if set(methods1.keys()) != set(methods2.keys()):
            return True

        for name in methods1:
            if methods1[name] != methods2[name]:
                return True

        return False

    def get_function(self, key: str) -> FunctionSignature | None:
        """Get function signature by key."""
        return self.functions.get(key)

    def get_class(self, key: str) -> ClassSignature | None:
        """Get class signature by key."""
        return self.classes.get(key)

    def update_snapshot(self, source_path: Path) -> tuple[list[str], list[str]]:
        """
        Incrementally update snapshot with changes.

        Args:
            source_path: Path to source code directory

        Returns:
            Tuple of (added_apis, removed_apis)
        """
        old_functions = set(self.functions.keys())
        old_classes = set(self.classes.keys())

        # Create new snapshot
        self.create_snapshot(source_path, self.metadata.get("version", ""))

        new_functions = set(self.functions.keys())
        new_classes = set(self.classes.keys())

        added = list((new_functions - old_functions) | (new_classes - old_classes))
        removed = list((old_functions - new_functions) | (old_classes - new_classes))

        return added, removed

    def get_public_apis(self) -> list[str]:
        """Get list of all public API names."""
        return list(self.functions.keys()) + list(self.classes.keys())

    def filter_by_module(self, module_prefix: str) -> "APISnapshot":
        """
        Create a filtered snapshot containing only APIs from specific module.

        Args:
            module_prefix: Module prefix to filter by

        Returns:
            New snapshot with filtered APIs
        """
        filtered = APISnapshot()
        filtered.metadata = self.metadata.copy()

        filtered.functions = {
            k: v for k, v in self.functions.items() if k.startswith(module_prefix)
        }
        filtered.classes = {k: v for k, v in self.classes.items() if k.startswith(module_prefix)}

        return filtered
