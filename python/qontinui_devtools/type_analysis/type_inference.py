"""Type inference engine for suggesting type hints.

This module analyzes code patterns to infer appropriate type hints for
untyped functions, parameters, and return values.
"""

import ast


class TypeInferenceEngine:
    """Infers types based on code analysis."""

    def __init__(self) -> None:
        """Initialize the inference engine."""
        self.type_mappings: dict[str, str] = {}
        self._init_default_mappings()

    def _init_default_mappings(self) -> None:
        """Initialize default type mappings for common patterns."""
        self.type_mappings = {
            # Common default values
            "None": "None",
            "True": "bool",
            "False": "bool",
            "''": "str",
            '""': "str",
            "[]": "list[Any]",
            "{}": "dict[str, Any]",
            "()": "tuple[()]",
            "set()": "set[Any]",
            # Common patterns
            "_id": "int",
            "_name": "str",
            "_path": "str | Path",
            "_file": "str | Path",
            "_dir": "str | Path",
            "_count": "int",
            "_size": "int",
            "_length": "int",
            "_index": "int",
            "_enabled": "bool",
            "_flag": "bool",
            "_is_": "bool",
            "_has_": "bool",
            "_can_": "bool",
            "_should_": "bool",
            "_items": "list[Any]",
            "_list": "list[Any]",
            "_dict": "dict[str, Any]",
            "_map": "dict[str, Any]",
            "_set": "set[Any]",
            "_data": "Any",
            "_value": "Any",
            "_result": "Any",
        }

    def infer_from_default(self, default_value: ast.expr) -> tuple[str | None, float]:
        """Infer type from a default value.

        Args:
            default_value: AST node for the default value

        Returns:
            Tuple of (inferred_type, confidence)
        """
        if isinstance(default_value, ast.Constant):
            value = default_value.value
            if value is None:
                return ("None", 0.9)
            elif isinstance(value, bool):
                return ("bool", 1.0)
            elif isinstance(value, int):
                return ("int", 1.0)
            elif isinstance(value, float):
                return ("float", 1.0)
            elif isinstance(value, str):
                return ("str", 1.0)
            elif isinstance(value, bytes):
                return ("bytes", 1.0)

        elif isinstance(default_value, ast.List):
            if not default_value.elts:
                return ("list[Any]", 0.8)
            # Try to infer element type
            elem_types = set()
            for elem in default_value.elts[:5]:  # Sample first 5 elements
                elem_type, _ = self.infer_from_default(elem)
                if elem_type:
                    elem_types.add(elem_type)
            if len(elem_types) == 1:
                return (f"list[{elem_types.pop()}]", 0.8)
            return ("list[Any]", 0.7)

        elif isinstance(default_value, ast.Dict):
            if not default_value.keys:
                return ("dict[str, Any]", 0.8)
            return ("dict[str, Any]", 0.7)

        elif isinstance(default_value, ast.Set):
            return ("set[Any]", 0.8)

        elif isinstance(default_value, ast.Tuple):
            if not default_value.elts:
                return ("tuple[()]", 0.9)
            # Infer tuple element types
            tuple_elem_types: list[str] = []
            for elem in default_value.elts:
                elem_type, _ = self.infer_from_default(elem)
                if elem_type:
                    tuple_elem_types.append(elem_type)
                else:
                    tuple_elem_types.append("Any")
            return (f"tuple[{', '.join(tuple_elem_types)}]", 0.7)

        elif isinstance(default_value, ast.Call):
            if isinstance(default_value.func, ast.Name):
                func_name = default_value.func.id
                if func_name == "list":
                    return ("list[Any]", 0.8)
                elif func_name == "dict":
                    return ("dict[str, Any]", 0.8)
                elif func_name == "set":
                    return ("set[Any]", 0.8)
                elif func_name == "tuple":
                    return ("tuple[Any, ...]", 0.8)

        return (None, 0.0)

    def infer_from_name(self, name: str) -> tuple[str | None, float]:
        """Infer type from parameter/variable name.

        Args:
            name: Name of the parameter/variable

        Returns:
            Tuple of (inferred_type, confidence)
        """
        # Check exact matches
        if name in self.type_mappings:
            return (self.type_mappings[name], 0.6)

        # Check suffix patterns
        for suffix, type_hint in self.type_mappings.items():
            if suffix.startswith("_") and not suffix.endswith("_") and name.endswith(suffix):
                return (type_hint, 0.5)

        # Check prefix patterns (like is_, has_, can_)
        for prefix, type_hint in self.type_mappings.items():
            if (
                prefix.startswith("_")
                and prefix.endswith("_")
                and name.startswith(prefix.strip("_"))
            ):
                return (type_hint, 0.5)

        return (None, 0.0)

    def infer_return_type(
        self, function_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> tuple[str | None, float, str]:
        """Infer return type from function body.

        Args:
            function_node: AST node for the function

        Returns:
            Tuple of (inferred_type, confidence, reason)
        """
        return_types = set()
        has_none_return = False
        return_nodes = []

        # Collect all return statements
        for node in ast.walk(function_node):
            if isinstance(node, ast.Return):
                return_nodes.append(node)

        if not return_nodes:
            return ("None", 0.9, "No return statements found")

        for ret_node in return_nodes:
            if ret_node.value is None:
                has_none_return = True
                continue

            # Try to infer type from the return value
            ret_type = self._infer_expr_type(ret_node.value)
            if ret_type:
                # Check if this is explicitly returning None as a constant
                if ret_type == "None":
                    has_none_return = True
                else:
                    return_types.add(ret_type)

        # Build final type hint
        if not return_types and has_none_return:
            return ("None", 0.9, "All returns are None")

        if not return_types:
            return ("Any", 0.4, "Cannot determine return type")

        if len(return_types) == 1:
            single_type = return_types.pop()
            if has_none_return:
                return (f"{single_type} | None", 0.7, "Returns value or None")
            return (single_type, 0.7, f"Returns {single_type}")

        # Multiple return types - create Union
        sorted_types = sorted(return_types)
        if has_none_return:
            sorted_types.append("None")

        union_type = " | ".join(sorted_types)
        return (union_type, 0.6, f"Returns multiple types: {union_type}")

    def _infer_expr_type(self, expr: ast.expr) -> str | None:
        """Infer type from an expression.

        Args:
            expr: AST expression node

        Returns:
            Inferred type string or None
        """
        if isinstance(expr, ast.Constant):
            value = expr.value
            if value is None:
                return "None"
            elif isinstance(value, bool):
                return "bool"
            elif isinstance(value, int):
                return "int"
            elif isinstance(value, float):
                return "float"
            elif isinstance(value, str):
                return "str"
            elif isinstance(value, bytes):
                return "bytes"

        elif isinstance(expr, ast.List):
            return "list[Any]"

        elif isinstance(expr, ast.Dict):
            return "dict[str, Any]"

        elif isinstance(expr, ast.Set):
            return "set[Any]"

        elif isinstance(expr, ast.Tuple):
            return "tuple[Any, ...]"

        elif isinstance(expr, ast.ListComp):
            return "list[Any]"

        elif isinstance(expr, ast.DictComp):
            return "dict[str, Any]"

        elif isinstance(expr, ast.SetComp):
            return "set[Any]"

        elif isinstance(expr, ast.Call):
            if isinstance(expr.func, ast.Name):
                func_name = expr.func.id
                if func_name == "list":
                    return "list[Any]"
                elif func_name == "dict":
                    return "dict[str, Any]"
                elif func_name == "set":
                    return "set[Any]"
                elif func_name == "tuple":
                    return "tuple[Any, ...]"
                elif func_name == "str":
                    return "str"
                elif func_name == "int":
                    return "int"
                elif func_name == "float":
                    return "float"
                elif func_name == "bool":
                    return "bool"

        elif isinstance(expr, ast.BinOp):
            # Infer from binary operations
            if isinstance(
                expr.op, ast.Add | ast.Sub | ast.Mult | ast.Div | ast.FloorDiv | ast.Mod | ast.Pow
            ):
                left_type = self._infer_expr_type(expr.left)
                right_type = self._infer_expr_type(expr.right)
                if left_type == right_type and left_type in ("int", "float"):
                    return left_type
                if left_type in ("int", "float") and right_type in ("int", "float"):
                    return "float"  # Mixed int/float operations
            elif isinstance(expr.op, ast.Add):
                # String concatenation
                left_type = self._infer_expr_type(expr.left)
                if left_type == "str":
                    return "str"

        elif isinstance(expr, ast.Compare):
            return "bool"

        elif isinstance(expr, ast.BoolOp):
            return "bool"

        elif isinstance(expr, ast.UnaryOp):
            if isinstance(expr.op, ast.Not):
                return "bool"

        return None

    def infer_parameter_type(
        self, param: ast.arg, function_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> tuple[str | None, float, str]:
        """Infer parameter type from usage in function body.

        Args:
            param: Parameter AST node
            function_node: Function containing the parameter

        Returns:
            Tuple of (inferred_type, confidence, reason)
        """
        param_name = param.arg

        # First try inferring from default value
        defaults = function_node.args.defaults
        args = function_node.args.args
        if args and defaults:
            # Match parameter with default
            default_offset = len(args) - len(defaults)
            param_idx = next((i for i, arg in enumerate(args) if arg.arg == param_name), -1)
            if param_idx >= default_offset:
                default_idx = param_idx - default_offset
                if default_idx < len(defaults):
                    inferred_type, confidence = self.infer_from_default(defaults[default_idx])
                    if inferred_type and inferred_type != "None":
                        return (inferred_type, confidence, "Inferred from default value")
                    elif inferred_type == "None":
                        # Try to infer from usage
                        usage_type = self._infer_from_usage(param_name, function_node)
                        if usage_type:
                            return (
                                f"{usage_type} | None",
                                0.7,
                                "Inferred from usage with None default",
                            )

        # Try inferring from name
        name_type, name_confidence = self.infer_from_name(param_name)

        # Try inferring from usage in function body
        usage_type = self._infer_from_usage(param_name, function_node)

        if usage_type and name_type:
            # Both methods found a type, use the more confident one
            if name_confidence > 0.6:
                return (name_type, name_confidence, "Inferred from parameter name")
            return (usage_type, 0.6, "Inferred from usage in function")
        elif usage_type:
            return (usage_type, 0.6, "Inferred from usage in function")
        elif name_type:
            return (name_type, name_confidence, "Inferred from parameter name")

        return (None, 0.0, "Cannot infer type")

    def _infer_from_usage(
        self, param_name: str, function_node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> str | None:
        """Infer type from how parameter is used in function.

        Args:
            param_name: Parameter name
            function_node: Function node

        Returns:
            Inferred type or None
        """
        usages = []

        for node in ast.walk(function_node):
            # Check method calls on the parameter
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute):
                    if isinstance(node.func.value, ast.Name) and node.func.value.id == param_name:
                        method_name = node.func.attr
                        # String methods
                        if method_name in (
                            "lower",
                            "upper",
                            "strip",
                            "split",
                            "join",
                            "replace",
                            "startswith",
                            "endswith",
                        ):
                            return "str"
                        # List methods
                        elif method_name in (
                            "append",
                            "extend",
                            "pop",
                            "remove",
                            "clear",
                            "index",
                            "count",
                        ):
                            return "list[Any]"
                        # Dict methods
                        elif method_name in (
                            "get",
                            "keys",
                            "values",
                            "items",
                            "update",
                            "pop",
                            "clear",
                        ):
                            return "dict[str, Any]"
                        # Set methods
                        elif method_name in ("add", "remove", "discard", "union", "intersection"):
                            return "set[Any]"
                        # Path methods
                        elif method_name in (
                            "exists",
                            "is_file",
                            "is_dir",
                            "read_text",
                            "write_text",
                        ):
                            return "Path"

            # Check subscript access
            elif isinstance(node, ast.Subscript):
                if isinstance(node.value, ast.Name) and node.value.id == param_name:
                    # Could be list, dict, or tuple
                    usages.append("subscriptable")

            # Check iteration
            elif isinstance(node, ast.For):
                if isinstance(node.iter, ast.Name) and node.iter.id == param_name:
                    return "Iterable[Any]"

            # Check comparison with None
            elif isinstance(node, ast.Compare):
                if isinstance(node.left, ast.Name) and node.left.id == param_name:
                    for op in node.ops:
                        if isinstance(op, ast.Is | ast.IsNot):
                            # Parameter is compared with None, might be Optional
                            usages.append("optional")

        return None

    def suggest_type_improvements(self, current_type: str) -> list[str]:
        """Suggest improvements for existing type hints.

        Args:
            current_type: Current type hint

        Returns:
            List of suggestions
        """
        suggestions = []

        # Detect bare Any usage
        if current_type == "Any":
            suggestions.append("Consider using a more specific type instead of Any")

        # Detect unparameterized generics
        if current_type == "list":
            suggestions.append("Use list[T] instead of bare list")
        elif current_type == "dict":
            suggestions.append("Use dict[K, V] instead of bare dict")
        elif current_type == "set":
            suggestions.append("Use set[T] instead of bare set")
        elif current_type == "tuple":
            suggestions.append("Use tuple[T, ...] or tuple[T1, T2, ...] instead of bare tuple")

        # Detect old-style Optional
        if "Optional[" in current_type:
            suggestions.append("Consider using T | None instead of Optional[T] (PEP 604)")

        # Detect old-style Union
        if "Union[" in current_type:
            suggestions.append("Consider using T1 | T2 instead of Union[T1, T2] (PEP 604)")

        return suggestions
