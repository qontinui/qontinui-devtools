"""Dependency graph builder for module coupling analysis."""

import ast
import os
from pathlib import Path
from typing import Dict, Set, List
from collections import defaultdict


class DependencyGraphBuilder:
    """Build and analyze module dependency graphs."""

    def __init__(self, verbose: bool = False):
        """Initialize the dependency graph builder.

        Args:
            verbose: If True, print progress information
        """
        self.verbose = verbose
        self.module_map: Dict[str, str] = {}  # module name -> file path
        self.reverse_map: Dict[str, str] = {}  # file path -> module name

    def build(self, root_path: str) -> Dict[str, Set[str]]:
        """Build dependency graph for all modules in the given path.

        Args:
            root_path: Root directory to analyze

        Returns:
            Dictionary mapping module paths to sets of imported module paths
        """
        root = Path(root_path).resolve()

        if not root.exists():
            raise ValueError(f"Path does not exist: {root_path}")

        # First pass: build module map
        if self.verbose:
            print(f"Scanning Python files in {root}...")

        if root.is_file():
            python_files = [root]
        else:
            python_files = list(root.rglob("*.py"))

        for file_path in python_files:
            module_name = self._file_to_module_name(file_path, root)
            self.module_map[module_name] = str(file_path)
            self.reverse_map[str(file_path)] = module_name

        if self.verbose:
            print(f"Found {len(python_files)} Python files")

        # Second pass: build dependency graph
        graph: Dict[str, Set[str]] = defaultdict(set)

        for file_path in python_files:
            module_name = self.reverse_map[str(file_path)]
            imports = self._extract_imports(file_path)

            for imported in imports:
                # Try to resolve to a module in our codebase
                resolved = self._resolve_import(imported, str(file_path), root)
                if resolved and resolved in self.module_map:
                    graph[str(file_path)].add(self.module_map[resolved])

        if self.verbose:
            total_deps = sum(len(deps) for deps in graph.values())
            print(f"Built graph with {total_deps} dependencies")

        return dict(graph)

    def _file_to_module_name(self, file_path: Path, root: Path) -> str:
        """Convert file path to module name.

        Args:
            file_path: Path to Python file
            root: Root directory

        Returns:
            Module name (e.g., 'package.module')
        """
        try:
            relative = file_path.relative_to(root)
        except ValueError:
            # File is not relative to root, use just the filename
            relative = Path(file_path.name)

        # Remove .py extension
        parts = list(relative.parts)
        if not parts:
            return ''

        if parts[-1].endswith('.py'):
            parts[-1] = parts[-1][:-3]

        # Remove __init__ from module names
        if parts and parts[-1] == '__init__':
            parts = parts[:-1]

        return '.'.join(parts) if parts else ''

    def _extract_imports(self, file_path: Path) -> List[str]:
        """Extract all import statements from a file.

        Args:
            file_path: Path to Python file

        Returns:
            List of imported module names
        """
        imports: List[str] = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
        except Exception:
            return imports

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
                    # Also add submodule imports
                    for alias in node.names:
                        if alias.name != '*':
                            full_name = f"{node.module}.{alias.name}"
                            imports.append(full_name)

        return imports

    def _resolve_import(self, import_name: str, from_file: str, root: Path) -> str | None:
        """Resolve an import statement to a module name in our codebase.

        Args:
            import_name: The imported module name
            from_file: File that contains the import
            root: Root directory

        Returns:
            Resolved module name or None if not in our codebase
        """
        # Direct match
        if import_name in self.module_map:
            return import_name

        # Try to find partial matches (for submodules)
        parts = import_name.split('.')
        for i in range(len(parts), 0, -1):
            candidate = '.'.join(parts[:i])
            if candidate in self.module_map:
                return candidate

        # Try relative imports
        from_module = self.reverse_map.get(from_file, '')
        if from_module:
            from_parts = from_module.split('.')
            # Try same package
            same_package = '.'.join(from_parts[:-1] + [import_name.split('.')[0]])
            if same_package in self.module_map:
                return same_package

        return None

    def calculate_afferent_coupling(self, module: str, graph: Dict[str, Set[str]]) -> int:
        """Calculate afferent coupling (Ca) - how many modules depend on this module.

        Args:
            module: Module path to analyze
            graph: Dependency graph

        Returns:
            Number of modules that depend on this module
        """
        count = 0
        for source, targets in graph.items():
            if module in targets and source != module:
                count += 1
        return count

    def calculate_efferent_coupling(self, module: str, graph: Dict[str, Set[str]]) -> int:
        """Calculate efferent coupling (Ce) - how many modules this module depends on.

        Args:
            module: Module path to analyze
            graph: Dependency graph

        Returns:
            Number of modules this module depends on
        """
        return len(graph.get(module, set()))

    def get_all_modules(self, graph: Dict[str, Set[str]]) -> Set[str]:
        """Get all unique module paths from the dependency graph.

        Args:
            graph: Dependency graph

        Returns:
            Set of all module paths
        """
        modules: Set[str] = set(graph.keys())
        for targets in graph.values():
            modules.update(targets)
        return modules

    def find_cycles(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Find all cycles in the dependency graph.

        Args:
            graph: Dependency graph

        Returns:
            List of cycles, where each cycle is a list of module paths
        """
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)
            return False

        for module in graph.keys():
            if module not in visited:
                dfs(module)

        return cycles

    def get_module_name(self, file_path: str) -> str:
        """Get the module name for a file path.

        Args:
            file_path: File path

        Returns:
            Module name
        """
        return self.reverse_map.get(file_path, os.path.basename(file_path))

    def calculate_fan_in_fan_out(
        self,
        module: str,
        graph: Dict[str, Set[str]]
    ) -> tuple[int, int]:
        """Calculate fan-in and fan-out for a module.

        Fan-in: Number of modules that call this module
        Fan-out: Number of modules this module calls

        Args:
            module: Module path to analyze
            graph: Dependency graph

        Returns:
            Tuple of (fan_in, fan_out)
        """
        fan_out = self.calculate_efferent_coupling(module, graph)
        fan_in = self.calculate_afferent_coupling(module, graph)
        return (fan_in, fan_out)
