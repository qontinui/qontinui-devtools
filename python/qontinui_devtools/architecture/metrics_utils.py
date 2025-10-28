"""Metrics calculation utilities for coupling and cohesion analysis."""

import ast
from typing import Set, Dict, List, Tuple
from collections import defaultdict


def calculate_lcom4(class_node: ast.ClassDef) -> float:
    """Calculate LCOM4 (Lack of Cohesion of Methods - version 4).

    LCOM4 measures the number of connected components in a class.
    A connected component is a set of methods that are related through
    shared attributes or method calls.

    Algorithm:
    1. Build graph: nodes = methods, edges = shared attributes or method calls
    2. Find connected components using DFS
    3. LCOM4 = number of components

    Lower is better (1 = perfect cohesion, all methods connected)

    Args:
        class_node: AST node representing the class

    Returns:
        Number of connected components (1.0 = best, higher = worse)
    """
    methods = [node for node in class_node.body if isinstance(node, ast.FunctionDef)]

    if len(methods) <= 1:
        return 1.0

    # Build method-to-attributes mapping
    method_attrs = find_method_attribute_connections(class_node)

    # Build method-to-method call graph
    method_calls = find_method_call_connections(class_node)

    # Build adjacency list for the graph
    graph: Dict[str, Set[str]] = defaultdict(set)
    method_names = [m.name for m in methods]

    # Add edges for shared attributes
    for i, method1 in enumerate(method_names):
        for j, method2 in enumerate(method_names):
            if i >= j:
                continue

            attrs1 = method_attrs.get(method1, set())
            attrs2 = method_attrs.get(method2, set())

            # If methods share attributes, they're connected
            if attrs1 & attrs2:
                graph[method1].add(method2)
                graph[method2].add(method1)

    # Add edges for method calls
    for caller, callees in method_calls.items():
        for callee in callees:
            if callee in method_names:
                graph[caller].add(callee)
                graph[callee].add(caller)

    # Find connected components using DFS
    visited: Set[str] = set()
    components = 0

    def dfs(node: str) -> None:
        visited.add(node)
        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                dfs(neighbor)

    for method in method_names:
        if method not in visited:
            components += 1
            dfs(method)

    return float(components)


def calculate_tcc(class_node: ast.ClassDef) -> float:
    """Calculate Tight Class Cohesion.

    TCC measures the ratio of directly connected method pairs to
    the total possible method pairs.

    TCC = (directly connected method pairs) / (total method pairs)

    Range: 0-1, where 1 is perfect cohesion.

    Args:
        class_node: AST node representing the class

    Returns:
        TCC score (0-1, higher is better)
    """
    methods = [node for node in class_node.body if isinstance(node, ast.FunctionDef)]

    if len(methods) <= 1:
        return 1.0

    # Build method-to-attributes mapping
    method_attrs = find_method_attribute_connections(class_node)

    # Count directly connected pairs
    connected_pairs = 0
    total_pairs = 0
    method_names = [m.name for m in methods]

    for i, method1 in enumerate(method_names):
        for j, method2 in enumerate(method_names):
            if i >= j:
                continue

            total_pairs += 1

            attrs1 = method_attrs.get(method1, set())
            attrs2 = method_attrs.get(method2, set())

            # If methods share attributes, they're directly connected
            if attrs1 & attrs2:
                connected_pairs += 1

    if total_pairs == 0:
        return 1.0

    return connected_pairs / total_pairs


def calculate_lcc(class_node: ast.ClassDef) -> float:
    """Calculate Loose Class Cohesion.

    LCC includes both direct and indirect connections between methods.
    Methods are indirectly connected if they're connected through a chain
    of other methods.

    LCC = (directly + indirectly connected pairs) / (total method pairs)

    Range: 0-1, where 1 is perfect cohesion.
    LCC >= TCC (loose cohesion includes tight cohesion)

    Args:
        class_node: AST node representing the class

    Returns:
        LCC score (0-1, higher is better)
    """
    methods = [node for node in class_node.body if isinstance(node, ast.FunctionDef)]

    if len(methods) <= 1:
        return 1.0

    # Build method-to-attributes mapping
    method_attrs = find_method_attribute_connections(class_node)

    # Build adjacency list for direct connections
    graph: Dict[str, Set[str]] = defaultdict(set)
    method_names = [m.name for m in methods]

    for i, method1 in enumerate(method_names):
        for j, method2 in enumerate(method_names):
            if i >= j:
                continue

            attrs1 = method_attrs.get(method1, set())
            attrs2 = method_attrs.get(method2, set())

            # If methods share attributes, they're directly connected
            if attrs1 & attrs2:
                graph[method1].add(method2)
                graph[method2].add(method1)

    # Use BFS to find all reachable pairs (direct + indirect)
    def are_connected(start: str, end: str) -> bool:
        """Check if two methods are connected (directly or indirectly)."""
        if start == end:
            return False

        visited: Set[str] = {start}
        queue: List[str] = [start]

        while queue:
            current = queue.pop(0)

            if current == end:
                return True

            for neighbor in graph.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return False

    # Count connected pairs (direct + indirect)
    connected_pairs = 0
    total_pairs = 0

    for i, method1 in enumerate(method_names):
        for j, method2 in enumerate(method_names):
            if i >= j:
                continue

            total_pairs += 1

            if are_connected(method1, method2):
                connected_pairs += 1

    if total_pairs == 0:
        return 1.0

    return connected_pairs / total_pairs


def find_method_attribute_connections(class_node: ast.ClassDef) -> Dict[str, Set[str]]:
    """Map each method to the attributes it accesses.

    This analyzes method bodies to find all self.attribute accesses.

    Args:
        class_node: AST node representing the class

    Returns:
        Dictionary mapping method names to sets of attribute names
    """
    method_attrs: Dict[str, Set[str]] = {}

    for node in class_node.body:
        if not isinstance(node, ast.FunctionDef):
            continue

        # Skip __init__ and other special methods for LCOM calculation
        # (but include them for other metrics)
        method_name = node.name
        attrs: Set[str] = set()

        # Walk the method body to find attribute accesses
        for child in ast.walk(node):
            # Look for self.attribute patterns
            if isinstance(child, ast.Attribute):
                if isinstance(child.value, ast.Name) and child.value.id == 'self':
                    attrs.add(child.attr)

        method_attrs[method_name] = attrs

    return method_attrs


def find_method_call_connections(class_node: ast.ClassDef) -> Dict[str, Set[str]]:
    """Map each method to other methods it calls.

    This analyzes method bodies to find calls to other methods in the class.

    Args:
        class_node: AST node representing the class

    Returns:
        Dictionary mapping method names to sets of called method names
    """
    method_calls: Dict[str, Set[str]] = {}

    for node in class_node.body:
        if not isinstance(node, ast.FunctionDef):
            continue

        method_name = node.name
        calls: Set[str] = set()

        # Walk the method body to find method calls
        for child in ast.walk(node):
            # Look for self.method() patterns
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if isinstance(child.func.value, ast.Name) and child.func.value.id == 'self':
                        calls.add(child.func.attr)

        method_calls[method_name] = calls

    return method_calls


def calculate_lcom(class_node: ast.ClassDef) -> float:
    """Calculate traditional LCOM (Lack of Cohesion of Methods).

    LCOM is the number of method pairs that don't share attributes
    minus the number that do share attributes. If negative, it's set to 0.

    This is normalized to 0-1 range for easier interpretation.

    Args:
        class_node: AST node representing the class

    Returns:
        LCOM score normalized to 0-1 (higher = worse cohesion)
    """
    methods = [node for node in class_node.body if isinstance(node, ast.FunctionDef)]

    if len(methods) <= 1:
        return 0.0

    # Build method-to-attributes mapping
    method_attrs = find_method_attribute_connections(class_node)

    # Count pairs that share/don't share attributes
    share_attrs = 0
    no_share_attrs = 0

    method_names = [m.name for m in methods]

    for i, method1 in enumerate(method_names):
        for j, method2 in enumerate(method_names):
            if i >= j:
                continue

            attrs1 = method_attrs.get(method1, set())
            attrs2 = method_attrs.get(method2, set())

            if attrs1 & attrs2:
                share_attrs += 1
            else:
                no_share_attrs += 1

    # LCOM = P - Q (if P > Q, else 0)
    lcom = max(0, no_share_attrs - share_attrs)

    # Normalize to 0-1 range
    total_pairs = share_attrs + no_share_attrs
    if total_pairs == 0:
        return 0.0

    return lcom / total_pairs


def count_abstract_classes(module_path: str) -> Tuple[int, int]:
    """Count abstract and total classes in a module.

    A class is considered abstract if:
    1. It inherits from ABC or ABCMeta
    2. It has at least one method decorated with @abstractmethod

    Args:
        module_path: Path to the Python module

    Returns:
        Tuple of (abstract_count, total_count)
    """
    try:
        with open(module_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=module_path)
    except Exception:
        return (0, 0)

    abstract_count = 0
    total_count = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            total_count += 1

            # Check if inherits from ABC or ABCMeta
            is_abstract = False
            for base in node.bases:
                if isinstance(base, ast.Name):
                    if base.id in ('ABC', 'ABCMeta'):
                        is_abstract = True
                        break

            # Check for @abstractmethod decorators
            if not is_abstract:
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        for decorator in item.decorator_list:
                            if isinstance(decorator, ast.Name):
                                if decorator.id == 'abstractmethod':
                                    is_abstract = True
                                    break
                            elif isinstance(decorator, ast.Attribute):
                                if decorator.attr == 'abstractmethod':
                                    is_abstract = True
                                    break
                    if is_abstract:
                        break

            if is_abstract:
                abstract_count += 1

    return (abstract_count, total_count)


def classify_score(value: float, thresholds: Dict[str, float], inverse: bool = False) -> str:
    """Classify a metric value into a quality score.

    Args:
        value: The metric value to classify
        thresholds: Dict with keys 'excellent', 'good', 'fair' and their threshold values
        inverse: If True, lower values are better (like LCOM)

    Returns:
        Score category: 'excellent', 'good', 'fair', or 'poor'
    """
    if inverse:
        if value <= thresholds['excellent']:
            return 'excellent'
        elif value <= thresholds['good']:
            return 'good'
        elif value <= thresholds['fair']:
            return 'fair'
        else:
            return 'poor'
    else:
        if value >= thresholds['excellent']:
            return 'excellent'
        elif value >= thresholds['good']:
            return 'good'
        elif value >= thresholds['fair']:
            return 'fair'
        else:
            return 'poor'
