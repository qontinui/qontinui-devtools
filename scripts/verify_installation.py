#!/usr/bin/env python3
"""Verify qontinui-devtools installation.

This script checks that all components are correctly installed and importable.
Run this after installing the package to ensure everything is working.
"""

import sys
from importlib import import_module


def verify_installation() -> bool:
    """Verify all components are installed correctly.

    Returns:
        True if all checks pass, False otherwise
    """

    required_modules = [
        "qontinui_devtools",
        "qontinui_devtools.import_analysis",
        "qontinui_devtools.concurrency",
        "qontinui_devtools.testing",
        "qontinui_devtools.architecture",
        "qontinui_devtools.reporting",
        "qontinui_devtools.ci",
    ]

    required_classes: list[tuple[str, str]] = [
        # Import Analysis
        ("qontinui_devtools", "ImportTracer"),
        ("qontinui_devtools", "CircularDependencyDetector"),
        # Concurrency
        ("qontinui_devtools", "RaceConditionDetector"),
        ("qontinui_devtools", "RaceConditionTester"),
        # Testing
        ("qontinui_devtools", "MockHAL"),
        # Architecture
        ("qontinui_devtools", "GodClassDetector"),
        ("qontinui_devtools", "SRPAnalyzer"),
        ("qontinui_devtools", "CouplingCohesionAnalyzer"),
        ("qontinui_devtools", "DependencyGraphVisualizer"),
        # Reporting
        ("qontinui_devtools", "HTMLReportGenerator"),
        ("qontinui_devtools", "ReportAggregator"),
    ]

    required_dependencies = [
        "click",
        "rich",
        "networkx",
        "graphviz",
        "astroid",
        "radon",
        "matplotlib",
        "pydantic",
        "structlog",
        "psutil",
        "jinja2",
        "tabulate",
        "colorama",
        "PIL",  # pillow
    ]

    print("=" * 70)
    print("Verifying qontinui-devtools installation")
    print("=" * 70)
    print()

    all_passed = True

    # Check modules
    print("Checking modules:")
    print("-" * 70)
    for module_name in required_modules:
        try:
            import_module(module_name)
            print(f"  \u2713 {module_name}")
        except ImportError as e:
            print(f"  \u2717 {module_name}: {e}")
            all_passed = False
    print()

    # Check classes
    print("Checking classes:")
    print("-" * 70)
    for module_name, class_name in required_classes:
        try:
            module = import_module(module_name)
            getattr(module, class_name)
            print(f"  \u2713 {module_name}.{class_name}")
        except (ImportError, AttributeError) as e:
            print(f"  \u2717 {module_name}.{class_name}: {e}")
            all_passed = False
    print()

    # Check CLI
    print("Checking CLI:")
    print("-" * 70)
    try:
        import importlib.util

        if importlib.util.find_spec("qontinui_devtools.cli") is not None:
            print("  \u2713 CLI entry point available")
        else:
            raise ImportError("qontinui_devtools.cli module not found")
    except ImportError as e:
        print(f"  \u2717 CLI: {e}")
        all_passed = False
    print()

    # Check version
    print("Checking version:")
    print("-" * 70)
    try:
        from qontinui_devtools import __version__

        print(f"  \u2713 Version: {__version__}")
    except ImportError as e:
        print(f"  \u2717 Version: {e}")
        all_passed = False
    print()

    # Check dependencies
    print("Checking dependencies:")
    print("-" * 70)
    for dep in required_dependencies:
        try:
            import_module(dep)
            print(f"  \u2713 {dep}")
        except ImportError as e:
            print(f"  \u2717 {dep}: {e}")
            all_passed = False
    print()

    # Summary
    print("=" * 70)
    if all_passed:
        print("\u2705 All checks passed! qontinui-devtools is properly installed.")
        print()
        print("Next steps:")
        print("  1. Try the CLI: qontinui-devtools --help")
        print("  2. Run tests: pytest")
        print("  3. Check the Quick Start guide: QUICKSTART.md")
    else:
        print("\u274c Some checks failed. Please review the errors above.")
        print()
        print("Common fixes:")
        print("  1. Reinstall: poetry install")
        print("  2. Update dependencies: poetry update")
        print("  3. Check Python version: python --version (requires 3.11+)")
    print("=" * 70)

    return all_passed


if __name__ == "__main__":
    success = verify_installation()
    sys.exit(0 if success else 1)
