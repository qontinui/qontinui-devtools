"""AST analysis for detecting shared state and threading primitives."""

import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StateAccess:
    """Record of accessing shared state."""
    name: str
    access_type: str  # "read", "write", "read_write"
    line_number: int
    col_offset: int
    in_lock_context: bool = False
    lock_name: str | None = None


@dataclass
class LockInfo:
    """Information about a lock."""
    name: str
    type: str  # "Lock", "RLock", "Semaphore", etc.
    line_number: int
    scope: str  # "instance", "class", "module"


@dataclass
class AnalysisContext:
    """Context for analyzing a file."""
    file_path: str
    shared_states: list[dict[str, Any]] = field(default_factory=list)
    state_accesses: list[StateAccess] = field(default_factory=list)
    locks: list[LockInfo] = field(default_factory=list)
    current_class: str | None = None
    current_function: str | None = None
    in_lock_context: bool = False
    current_lock: str | None = None
    lock_depth: int = 0


class SharedStateVisitor(ast.NodeVisitor):
    """Find shared mutable state in AST."""

    def __init__(self, file_path: str) -> None:
        self.context = AnalysisContext(file_path=file_path)
        self._class_stack: list[str] = []
        self._function_stack: list[str] = []
        self._lock_context_stack: list[str] = []
        self._assignment_targets: set[int] = set()  # Track nodes being assigned

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition to find class variables."""
        self._class_stack.append(node.name)
        self.context.current_class = node.name

        # Find class variables (assignments at class level)
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        # Track all class variables except constants (all uppercase)
                        # Even if initial value is immutable, the variable can be reassigned
                        if not target.id.isupper() or "_" not in target.id:
                            type_info = self._infer_type(item.value)
                            self.context.shared_states.append({
                                "name": target.id,
                                "type": "class_variable",
                                "class_name": node.name,
                                "line_number": item.lineno,
                                "col_offset": item.col_offset,
                                "inferred_type": type_info,
                                "value_ast": item.value,
                            })
            elif isinstance(item, ast.AnnAssign):
                if isinstance(item.target, ast.Name):
                    # Track annotated class variables
                    if not item.target.id.isupper() or "_" not in item.target.id:
                        type_info = self._get_annotation_type(item.annotation)
                        self.context.shared_states.append({
                            "name": item.target.id,
                            "type": "class_variable",
                            "class_name": node.name,
                            "line_number": item.lineno,
                            "col_offset": item.col_offset,
                            "inferred_type": type_info,
                            "value_ast": item.value if item.value else None,
                        })

        self.generic_visit(node)
        self._class_stack.pop()
        self.context.current_class = self._class_stack[-1] if self._class_stack else None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        self._function_stack.append(node.name)
        self.context.current_function = node.name
        self.generic_visit(node)
        self._function_stack.pop()
        self.context.current_function = self._function_stack[-1] if self._function_stack else None

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        self._function_stack.append(node.name)
        self.context.current_function = node.name
        self.generic_visit(node)
        self._function_stack.pop()
        self.context.current_function = self._function_stack[-1] if self._function_stack else None

    def visit_Assign(self, node: ast.Assign) -> None:
        """Find module-level assignments and track state access."""
        # Module-level mutable state (not in any class or function)
        if not self._class_stack and not self._function_stack:
            for target in node.targets:
                if isinstance(target, ast.Name):
                    # Track module globals except constants and private names
                    if not target.id.startswith("__") and not (target.id.isupper() and "_" in target.id):
                        type_info = self._infer_type(node.value)
                        self.context.shared_states.append({
                            "name": target.id,
                            "type": "module_global",
                            "line_number": node.lineno,
                            "col_offset": node.col_offset,
                            "inferred_type": type_info,
                            "value_ast": node.value,
                        })

        # Track writes to potentially shared state
        if self._function_stack:
            # Mark targets for assignment detection
            for target in node.targets:
                self._assignment_targets.add(id(target))
                self._record_state_access(target, "write", node.lineno, node.col_offset)

        self.generic_visit(node)

        # Clear assignment targets after processing
        if self._function_stack:
            for target in node.targets:
                self._assignment_targets.discard(id(target))

    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        """Track augmented assignments (+=, -=, etc.)."""
        if self._function_stack:
            self._assignment_targets.add(id(node.target))
            self._record_state_access(node.target, "read_write", node.lineno, node.col_offset)
        self.generic_visit(node)
        if self._function_stack:
            self._assignment_targets.discard(id(node.target))

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Track attribute access."""
        if self._function_stack and isinstance(node.value, ast.Name):
            # Track reads (writes are handled in Assign)
            if not self._is_being_assigned(node):
                self._record_state_access(node, "read", node.lineno, node.col_offset)
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        """Track dictionary/list subscript operations."""
        if self._function_stack:
            # Determine if it's a read or write based on whether it's an assignment target
            access_type = "write" if id(node) in self._assignment_targets else "read"
            self._record_state_access(node.value, access_type, node.lineno, node.col_offset)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        """Track name access."""
        if self._function_stack and not self._is_being_assigned(node):
            # Check if it's a module-level name
            if node.id.isupper() or node.id.startswith("_"):
                self._record_state_access(node, "read", node.lineno, node.col_offset)
        self.generic_visit(node)

    def _record_state_access(self, node: ast.AST, access_type: str, line: int, col: int) -> None:
        """Record an access to potentially shared state."""
        name = self._extract_name(node)
        if name and not name.startswith("__"):
            self.context.state_accesses.append(StateAccess(
                name=name,
                access_type=access_type,
                line_number=line,
                col_offset=col,
                in_lock_context=self.context.in_lock_context,
                lock_name=self.context.current_lock,
            ))

    def _extract_name(self, node: ast.AST) -> str | None:
        """Extract variable name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            base = self._extract_name(node.value)
            return f"{base}.{node.attr}" if base else node.attr
        elif isinstance(node, ast.Subscript):
            return self._extract_name(node.value)
        return None

    def _is_being_assigned(self, node: ast.AST) -> bool:
        """Check if node is being assigned to."""
        return id(node) in self._assignment_targets

    def _infer_type(self, node: ast.AST | None) -> str:
        """Infer type from AST node."""
        if node is None:
            return "unknown"

        if isinstance(node, ast.Dict):
            return "dict"
        elif isinstance(node, ast.List):
            return "list"
        elif isinstance(node, ast.Set):
            return "set"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return node.func.id
            elif isinstance(node.func, ast.Attribute):
                return node.func.attr
        elif isinstance(node, ast.Constant):
            return type(node.value).__name__

        return "unknown"

    def _get_annotation_type(self, node: ast.AST) -> str:
        """Extract type from type annotation."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name):
                return node.value.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return "unknown"

    def _is_mutable_type(self, type_info: str) -> bool:
        """Check if type is mutable."""
        mutable_types = {
            "dict", "list", "set", "deque", "defaultdict", "OrderedDict",
            "Counter", "bytearray", "array", "unknown"
        }
        return type_info in mutable_types


class LockUsageVisitor(ast.NodeVisitor):
    """Find threading primitives and lock usage."""

    def __init__(self, file_path: str) -> None:
        self.context = AnalysisContext(file_path=file_path)
        self._lock_stack: list[str] = []
        self._class_stack: list[str] = []
        self._in_with_lock = False

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Track class context."""
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    def visit_Assign(self, node: ast.Assign) -> None:
        """Find Lock() creation."""
        if isinstance(node.value, ast.Call):
            lock_type = self._get_lock_type(node.value)
            if lock_type:
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        scope = "class" if self._class_stack else "module"
                        self.context.locks.append(LockInfo(
                            name=target.id,
                            type=lock_type,
                            line_number=node.lineno,
                            scope=scope,
                        ))
                    elif isinstance(target, ast.Attribute):
                        self.context.locks.append(LockInfo(
                            name=target.attr,
                            type=lock_type,
                            line_number=node.lineno,
                            scope="instance",
                        ))

        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        """Find 'with lock:' patterns."""
        old_in_with = self._in_with_lock
        old_depth = self.context.lock_depth

        for item in node.items:
            lock_name = self._extract_lock_name(item.context_expr)
            if lock_name or self._looks_like_lock(item.context_expr):
                self._in_with_lock = True
                self.context.in_lock_context = True
                self.context.lock_depth += 1
                if lock_name:
                    self._lock_stack.append(lock_name)
                    self.context.current_lock = lock_name

        # Visit body with lock context
        for stmt in node.body:
            self.visit(stmt)

        # Restore context
        if self._in_with_lock != old_in_with:
            if self._lock_stack:
                self._lock_stack.pop()
            self.context.current_lock = self._lock_stack[-1] if self._lock_stack else None
            self.context.lock_depth = old_depth
            self.context.in_lock_context = len(self._lock_stack) > 0

        self._in_with_lock = old_in_with

    def visit_Call(self, node: ast.Call) -> None:
        """Find Lock() creation and acquire/release calls."""
        lock_type = self._get_lock_type(node)
        if lock_type:
            # Anonymous lock creation
            self.context.locks.append(LockInfo(
                name="_anonymous",
                type=lock_type,
                line_number=node.lineno,
                scope="local",
            ))

        self.generic_visit(node)

    def _get_lock_type(self, node: ast.Call) -> str | None:
        """Determine if a call creates a lock."""
        lock_types = {
            "Lock", "RLock", "Semaphore", "BoundedSemaphore",
            "Condition", "Event", "Barrier"
        }

        if isinstance(node.func, ast.Name):
            if node.func.id in lock_types:
                return node.func.id
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in lock_types:
                return node.func.attr

        return None

    def _extract_lock_name(self, node: ast.AST) -> str | None:
        """Extract lock variable name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Call):
            # Handle lock.acquire()
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in ("acquire", "acquire_lock"):
                    return self._extract_lock_name(node.func.value)
        return None

    def _looks_like_lock(self, node: ast.AST) -> bool:
        """Heuristic to detect if expression looks like a lock."""
        name = self._extract_lock_name(node)
        if name:
            lock_keywords = {"lock", "mutex", "semaphore", "condition"}
            return any(keyword in name.lower() for keyword in lock_keywords)
        return False


class CombinedVisitor(ast.NodeVisitor):
    """Combined visitor that tracks both shared state and lock usage."""

    def __init__(self, file_path: str) -> None:
        self.context = AnalysisContext(file_path=file_path)
        self._class_stack: list[str] = []
        self._function_stack: list[str] = []
        self._lock_context_stack: list[tuple[str, int]] = []
        self._shared_state_visitor = SharedStateVisitor(file_path)
        self._lock_visitor = LockUsageVisitor(file_path)

    def analyze(self, tree: ast.AST) -> AnalysisContext:
        """Analyze AST and return context."""
        # First pass: find shared state
        self._shared_state_visitor.visit(tree)

        # Second pass: find locks
        self._lock_visitor.visit(tree)

        # Merge contexts
        self.context.shared_states = self._shared_state_visitor.context.shared_states
        self.context.state_accesses = self._shared_state_visitor.context.state_accesses
        self.context.locks = self._lock_visitor.context.locks

        return self.context


def analyze_file(file_path: str | Path) -> AnalysisContext:
    """Analyze a Python file for race conditions."""
    file_path = Path(file_path)

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()

        tree = ast.parse(source, filename=str(file_path))
        visitor = CombinedVisitor(str(file_path))
        return visitor.analyze(tree)

    except SyntaxError as e:
        # Return empty context for files with syntax errors
        context = AnalysisContext(file_path=str(file_path))
        return context
    except Exception as e:
        # Log error and return empty context
        context = AnalysisContext(file_path=str(file_path))
        return context
