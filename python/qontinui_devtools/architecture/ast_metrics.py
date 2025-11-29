"""AST-based metrics utilities for analyzing Python code structure."""

import ast

try:
    from radon.complexity import cc_visit
    from radon.raw import analyze
except ImportError:
    cc_visit = None
    analyze = None


def count_lines(node: ast.AST, source: str) -> tuple[int, int]:
    """Count total and code lines in AST node.

    Args:
        node: AST node to analyze
        source: Full source code

    Returns:
        (total_lines, code_lines) tuple
    """
    if not hasattr(node, "lineno") or not hasattr(node, "end_lineno"):
        return 0, 0

    start_line = node.lineno
    end_line = node.end_lineno or start_line

    total_lines = end_line - start_line + 1

    # Count non-empty, non-comment lines
    source_lines = source.split("\n")
    code_lines = 0

    for i in range(start_line - 1, min(end_line, len(source_lines))):
        line = source_lines[i].strip()
        # Skip empty lines and pure comment lines
        if line and not line.startswith("#"):
            code_lines += 1

    return total_lines, code_lines


def count_methods(class_node: ast.ClassDef) -> dict[str, int]:
    """Count methods by type.

    Args:
        class_node: Class AST node

    Returns:
        Dictionary with method counts by type
    """
    counts = {
        "instance": 0,
        "class": 0,
        "static": 0,
        "private": 0,
        "public": 0,
    }

    for node in class_node.body:
        if isinstance(node, ast.FunctionDef):
            # Check for decorators
            is_classmethod = any(
                isinstance(d, ast.Name) and d.id == "classmethod" for d in node.decorator_list
            )
            is_staticmethod = any(
                isinstance(d, ast.Name) and d.id == "staticmethod" for d in node.decorator_list
            )

            if is_classmethod:
                counts["class"] += 1
            elif is_staticmethod:
                counts["static"] += 1
            else:
                counts["instance"] += 1

            # Check if private
            if node.name.startswith("_") and not node.name.startswith("__"):
                counts["private"] += 1
            else:
                counts["public"] += 1

    return counts


def count_attributes(class_node: ast.ClassDef) -> int:
    """Count attributes defined in __init__.

    Args:
        class_node: Class AST node

    Returns:
        Number of instance attributes
    """

    # Find __init__ method
    init_method = None
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == "__init__":
            init_method = node
            break

    if not init_method:
        return 0

    # Count self.attribute assignments
    class AttributeVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.attributes: set[str] = set()

        def visit_Assign(self, node: ast.Assign) -> None:
            for target in node.targets:
                if isinstance(target, ast.Attribute):
                    if isinstance(target.value, ast.Name) and target.value.id == "self":
                        self.attributes.add(target.attr)
            self.generic_visit(node)

        def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
            if isinstance(node.target, ast.Attribute):
                if isinstance(node.target.value, ast.Name) and node.target.value.id == "self":
                    self.attributes.add(node.target.attr)
            self.generic_visit(node)

    visitor = AttributeVisitor()
    visitor.visit(init_method)

    return len(visitor.attributes)


def calculate_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity using radon.

    Args:
        node: AST node to analyze

    Returns:
        Cyclomatic complexity score
    """
    if cc_visit is None:
        # Fallback: simple complexity estimation
        return _estimate_complexity(node)

    try:
        # Convert AST back to source for radon
        source = ast.unparse(node)
        results = cc_visit(source)

        total_complexity = sum(item.complexity for item in results)
        return total_complexity
    except Exception:
        return _estimate_complexity(node)


def _estimate_complexity(node: ast.AST) -> int:
    """Fallback complexity estimation without radon.

    Args:
        node: AST node to analyze

    Returns:
        Estimated complexity score
    """

    class ComplexityVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.complexity = 1

        def visit_If(self, node: ast.If) -> None:
            self.complexity += 1
            self.generic_visit(node)

        def visit_For(self, node: ast.For) -> None:
            self.complexity += 1
            self.generic_visit(node)

        def visit_While(self, node: ast.While) -> None:
            self.complexity += 1
            self.generic_visit(node)

        def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
            self.complexity += 1
            self.generic_visit(node)

        def visit_With(self, node: ast.With) -> None:
            self.complexity += 1
            self.generic_visit(node)

        def visit_BoolOp(self, node: ast.BoolOp) -> None:
            # Add complexity for and/or operators
            self.complexity += len(node.values) - 1
            self.generic_visit(node)

    visitor = ComplexityVisitor()
    visitor.visit(node)

    return visitor.complexity


def extract_method_names(class_node: ast.ClassDef) -> list[str]:
    """Extract all method names from class.

    Args:
        class_node: Class AST node

    Returns:
        List of method names
    """
    method_names = []

    for node in class_node.body:
        if isinstance(node, ast.FunctionDef):
            method_names.append(node.name)

    return method_names


def find_shared_attributes(method1: ast.FunctionDef, method2: ast.FunctionDef) -> set[str]:
    """Find attributes shared between two methods.

    Args:
        method1: First method AST node
        method2: Second method AST node

    Returns:
        Set of shared attribute names
    """

    def get_accessed_attributes(method: ast.FunctionDef) -> set[str]:
        """Get all self.attribute accesses in a method."""
        attributes = set()

        class AttributeAccessVisitor(ast.NodeVisitor):
            def visit_Attribute(self, node: ast.Attribute) -> None:
                if isinstance(node.value, ast.Name) and node.value.id == "self":
                    attributes.add(node.attr)
                self.generic_visit(node)

        visitor = AttributeAccessVisitor()
        visitor.visit(method)
        return attributes

    attrs1 = get_accessed_attributes(method1)
    attrs2 = get_accessed_attributes(method2)

    return attrs1 & attrs2


def get_method_by_name(class_node: ast.ClassDef, method_name: str) -> ast.FunctionDef | None:
    """Get method node by name.

    Args:
        class_node: Class AST node
        method_name: Name of method to find

    Returns:
        Method AST node or None
    """
    for node in class_node.body:
        if isinstance(node, ast.FunctionDef) and node.name == method_name:
            return node
    return None


def analyze_method_calls(class_node: ast.ClassDef) -> dict[str, set[str]]:
    """Analyze which methods call other methods.

    Args:
        class_node: Class AST node

    Returns:
        Dictionary mapping method names to set of called method names
    """
    call_graph: dict[str, set[str]] = {}

    for node in class_node.body:
        if isinstance(node, ast.FunctionDef):
            called_methods = set()

            class MethodCallVisitor(ast.NodeVisitor):
                def visit_Call(self, call_node: ast.Call) -> None:
                    # Check for self.method() calls
                    if isinstance(call_node.func, ast.Attribute):
                        if (
                            isinstance(call_node.func.value, ast.Name)
                            and call_node.func.value.id == "self"
                        ):
                            called_methods.add(call_node.func.attr)
                    self.generic_visit(call_node)

            visitor = MethodCallVisitor()
            visitor.visit(node)
            call_graph[node.name] = called_methods

    return call_graph
