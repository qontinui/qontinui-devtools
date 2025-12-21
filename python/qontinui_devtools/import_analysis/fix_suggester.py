"""Fix suggester for circular dependencies.

This module analyzes circular import dependencies and suggests
appropriate fixes based on usage patterns.
"""

from dataclasses import dataclass

from .ast_utils import ImportStatement


@dataclass
class FixSuggestion:
    """A suggested fix for a circular dependency.

    Attributes:
        fix_type: Type of fix ('lazy_import', 'type_checking', 'restructure')
        description: Human-readable description of the fix
        code_example: Example code showing how to apply the fix
        affected_files: Files that would need to be modified
    """

    fix_type: str
    description: str
    code_example: str | None
    affected_files: list[str]


def analyze_cycle(cycle: list[str], import_map: dict[str, list[ImportStatement]]) -> FixSuggestion:
    """Analyze a circular dependency cycle and suggest how to break it.

    Args:
        cycle: List of module names forming a cycle (e.g., ['a', 'b', 'c', 'a'])
        import_map: Map of module names to their import statements

    Returns:
        A FixSuggestion with the recommended approach
    """
    # Get the import statements involved in the cycle
    cycle_imports = _extract_cycle_imports(cycle, import_map)

    if not cycle_imports:
        return FixSuggestion(
            fix_type="restructure",
            description="Unable to analyze cycle imports. Consider restructuring the modules.",
            code_example=None,
            affected_files=[],
        )

    # Analyze the usage patterns of the imports
    usage_analysis = _analyze_usage_patterns(cycle_imports)

    # Decide on the best fix strategy
    if usage_analysis["has_type_only_imports"]:
        return _suggest_type_checking_fix(cycle_imports)
    elif usage_analysis["has_function_level_usage"]:
        return _suggest_lazy_import_fix(cycle_imports)
    else:
        return _suggest_restructure_fix(cycle, cycle_imports)


def _extract_cycle_imports(
    cycle: list[str], import_map: dict[str, list[ImportStatement]]
) -> list[ImportStatement]:
    """Extract the import statements that form the cycle.

    Args:
        cycle: List of module names in the cycle
        import_map: Map of module names to imports

    Returns:
        List of ImportStatements involved in the cycle
    """
    cycle_imports: list[ImportStatement] = []

    # For each pair of consecutive modules in the cycle
    for i in range(len(cycle) - 1):
        current_module = cycle[i]
        next_module = cycle[i + 1]

        # Find imports from current_module that import next_module
        if current_module in import_map:
            for import_stmt in import_map[current_module]:
                # Check if this import references the next module in the cycle
                if next_module in import_stmt.module or import_stmt.module.startswith(
                    next_module + "."
                ):
                    cycle_imports.append(import_stmt)

    return cycle_imports


def _analyze_usage_patterns(imports: list[ImportStatement]) -> dict[str, bool]:
    """Analyze how imports are used to determine the best fix strategy.

    Args:
        imports: List of import statements to analyze

    Returns:
        Dictionary with analysis results
    """
    analysis = {
        "has_type_only_imports": False,
        "has_function_level_usage": False,
        "has_wildcard_imports": False,
        "has_from_imports": False,
    }

    for import_stmt in imports:
        # Check for wildcard imports
        if "*" in import_stmt.imported_names:
            analysis["has_wildcard_imports"] = True

        # Check if it's a from import
        if import_stmt.is_from_import:
            analysis["has_from_imports"] = True

        # Try to detect type-only usage (heuristic: lowercase names often classes/types)
        # This is a simple heuristic - in practice, would need more sophisticated analysis
        if import_stmt.imported_names:
            for name in import_stmt.imported_names:
                # Type hints often use PascalCase
                if name and name[0].isupper():
                    analysis["has_type_only_imports"] = True

    return analysis


def _suggest_type_checking_fix(imports: list[ImportStatement]) -> FixSuggestion:
    """Suggest using TYPE_CHECKING to fix the cycle.

    Args:
        imports: Import statements involved in the cycle

    Returns:
        FixSuggestion for TYPE_CHECKING approach
    """
    # Pick the first import as an example
    example_import = imports[0] if imports else None

    if example_import and example_import.is_from_import:
        names = ", ".join(example_import.imported_names)
        code_example = f"""# Move import inside TYPE_CHECKING block:
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from {example_import.module} import {names}

# This import is only used for type hints and won't execute at runtime,
# breaking the circular dependency.
"""
    else:
        code_example = """# Example:
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from module_a import SomeClass

# Use string annotations for type hints:
def my_function() -> 'SomeClass':
    # Import at runtime only when needed
    from module_a import SomeClass
    return SomeClass()
"""

    affected_files = list({imp.file_path for imp in imports})

    return FixSuggestion(
        fix_type="type_checking",
        description=(
            "Use TYPE_CHECKING guard for type-only imports. "
            "This defers imports to type-checking time only, "
            "breaking the runtime circular dependency."
        ),
        code_example=code_example,
        affected_files=affected_files,
    )


def _suggest_lazy_import_fix(imports: list[ImportStatement]) -> FixSuggestion:
    """Suggest using lazy imports to fix the cycle.

    Args:
        imports: Import statements involved in the cycle

    Returns:
        FixSuggestion for lazy import approach
    """
    example_import = imports[0] if imports else None

    if example_import:
        if example_import.is_from_import:
            names = ", ".join(example_import.imported_names[:2])  # Show first 2 names
            code_example = f"""# Move import inside function:
# Remove this from top of file:
# from {example_import.module} import {names}

def my_function() -> None:
    # Import only when function is called:
    from {example_import.module} import {names}
    # ... use imported items ...

# This defers the import until the function runs,
# breaking the circular dependency at module load time.
"""
        else:
            code_example = f"""# Move import inside function:
# Remove this from top of file:
# import {example_import.module}

def my_function() -> None:
    # Import only when function is called:
    import {example_import.module}
    # ... use the module ...

# This defers the import until the function runs.
"""
    else:
        code_example = """# Move import to function level:
def my_function() -> None:
    from module_a import something
    # Use 'something' here
"""

    affected_files = list({imp.file_path for imp in imports})

    return FixSuggestion(
        fix_type="lazy_import",
        description=(
            "Move imports inside functions where they're used (lazy imports). "
            "This defers the import until the function is called, "
            "breaking the circular dependency at module load time."
        ),
        code_example=code_example,
        affected_files=affected_files,
    )


def _suggest_restructure_fix(cycle: list[str], imports: list[ImportStatement]) -> FixSuggestion:
    """Suggest restructuring to fix the cycle.

    Args:
        cycle: Module names in the cycle
        imports: Import statements involved

    Returns:
        FixSuggestion for restructuring approach
    """
    cycle_display = " -> ".join(cycle)
    affected_files = list({imp.file_path for imp in imports})

    code_example = f"""# Circular dependency detected: {cycle_display}

# Consider these refactoring approaches:

1. Extract Common Dependencies:
   - Create a new module (e.g., 'common.py' or 'base.py')
   - Move shared classes/functions that both modules need
   - Both modules import from the common module

2. Dependency Inversion:
   - Define interfaces/protocols in a separate module
   - Have implementations depend on abstractions
   - Break the concrete dependency cycle

3. Merge Modules:
   - If modules are tightly coupled, consider merging them
   - into a single module with clear internal organization

4. Event-Based Communication:
   - Use events/signals instead of direct imports
   - One module emits events, another subscribes
   - Breaks the direct import dependency
"""

    return FixSuggestion(
        fix_type="restructure",
        description=(
            "Circular dependency requires architectural restructuring. "
            "Consider extracting shared dependencies to a common module, "
            "using dependency inversion, merging tightly coupled modules, "
            "or switching to event-based communication."
        ),
        code_example=code_example,
        affected_files=affected_files,
    )


def suggest_best_break_point(cycle: list[str], import_map: dict[str, list[ImportStatement]]) -> str:
    """Suggest the best place to break the cycle.

    Args:
        cycle: List of module names in the cycle
        import_map: Map of module names to their imports

    Returns:
        Suggestion of where to break the cycle
    """
    # Count how many imports each module in the cycle has
    import_counts: dict[str, int] = {}

    for i in range(len(cycle) - 1):
        current = cycle[i]
        next_module = cycle[i + 1]

        if current not in import_counts:
            import_counts[current] = 0

        if current in import_map:
            for imp in import_map[current]:
                if next_module in imp.module:
                    import_counts[current] += len(imp.imported_names) if imp.imported_names else 1

    if not import_counts:
        return "Unable to determine best break point."

    # Suggest breaking at the module with the fewest imports
    min_module = min(import_counts, key=import_counts.get)  # type: ignore
    min_count = import_counts[min_module]

    return (
        f"Consider breaking the cycle at '{min_module}' "
        f"(has {min_count} import(s) involved in the cycle)."
    )
