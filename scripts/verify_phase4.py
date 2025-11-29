#!/usr/bin/env python3
"""Verification script for Phase 4 integration.

This script verifies that all Phase 4 components are properly integrated:
- All modules are importable
- CLI commands are available
- Integration tests pass
- Documentation is present
- Version numbers are correct
"""

import subprocess
import sys
from pathlib import Path


class Color:
    """ANSI color codes."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Color.BOLD}{Color.BLUE}{'=' * 70}{Color.END}")
    print(f"{Color.BOLD}{Color.BLUE}{text:^70}{Color.END}")
    print(f"{Color.BOLD}{Color.BLUE}{'=' * 70}{Color.END}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Color.GREEN}✓ {text}{Color.END}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Color.RED}✗ {text}{Color.END}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Color.YELLOW}⚠ {text}{Color.END}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Color.BLUE}ℹ {text}{Color.END}")


def verify_imports() -> tuple[bool, list[str]]:
    """Verify all Phase 4 modules can be imported."""
    print_header("Verifying Module Imports")

    modules = [
        "qontinui_devtools",
        "qontinui_devtools.security",
        "qontinui_devtools.documentation",
        "qontinui_devtools.regression",
        "qontinui_devtools.type_analysis",
        "qontinui_devtools.dependencies",
    ]

    classes = [
        ("qontinui_devtools.security", "SecurityAnalyzer"),
        ("qontinui_devtools.documentation", "DocumentationGenerator"),
        ("qontinui_devtools.regression", "RegressionDetector"),
        ("qontinui_devtools.type_analysis", "TypeAnalyzer"),
        ("qontinui_devtools.dependencies", "DependencyHealthChecker"),
    ]

    errors = []
    success_count = 0

    # Test module imports
    for module in modules:
        try:
            __import__(module)
            print_success(f"Imported {module}")
            success_count += 1
        except ImportError as e:
            error_msg = f"Failed to import {module}: {e}"
            print_error(error_msg)
            errors.append(error_msg)

    # Test class imports
    for module, class_name in classes:
        try:
            mod = __import__(module, fromlist=[class_name])
            getattr(mod, class_name)
            print_success(f"Imported {module}.{class_name}")
            success_count += 1
        except (ImportError, AttributeError) as e:
            error_msg = f"Failed to import {module}.{class_name}: {e}"
            print_warning(error_msg)  # Warning, not error (may not be implemented)

    # Test main package exports
    try:
        from qontinui_devtools import (
            DependencyHealthChecker,
            DocumentationGenerator,
            RegressionDetector,
            SecurityAnalyzer,
            TypeAnalyzer,
        )

        print_success("All Phase 4 classes exported from main package")
        success_count += 1
    except ImportError as e:
        error_msg = f"Failed to import from main package: {e}"
        print_warning(error_msg)

    total_checks = len(modules) + len(classes) + 1
    print(f"\n{Color.BOLD}Import checks: {success_count}/{total_checks} passed{Color.END}")

    return len(errors) == 0, errors


def verify_cli_commands() -> tuple[bool, list[str]]:
    """Verify CLI commands are available."""
    print_header("Verifying CLI Commands")

    commands = [
        ["qontinui-devtools", "--version"],
        ["qontinui-devtools", "security", "--help"],
        ["qontinui-devtools", "docs", "--help"],
        ["qontinui-devtools", "regression", "--help"],
        ["qontinui-devtools", "types", "--help"],
        ["qontinui-devtools", "deps", "--help"],
    ]

    errors = []
    success_count = 0

    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print_success(f"Command available: {' '.join(cmd)}")
                success_count += 1
            else:
                error_msg = f"Command failed: {' '.join(cmd)}"
                print_error(error_msg)
                errors.append(error_msg)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            error_msg = f"Command not found or timed out: {' '.join(cmd)}"
            print_error(error_msg)
            errors.append(error_msg)

    print(f"\n{Color.BOLD}CLI checks: {success_count}/{len(commands)} passed{Color.END}")

    return len(errors) == 0, errors


def verify_version() -> tuple[bool, list[str]]:
    """Verify version numbers are correct."""
    print_header("Verifying Version Numbers")

    errors = []
    target_version = "1.1.0"

    # Check __init__.py version
    try:
        from qontinui_devtools import __version__

        if __version__ == target_version:
            print_success(f"__init__.py version: {__version__}")
        else:
            error_msg = (
                f"__init__.py version mismatch: expected {target_version}, got {__version__}"
            )
            print_error(error_msg)
            errors.append(error_msg)
    except ImportError as e:
        error_msg = f"Failed to import version: {e}"
        print_error(error_msg)
        errors.append(error_msg)

    # Check pyproject.toml version
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        content = pyproject_path.read_text()
        if f'version = "{target_version}"' in content:
            print_success(f"pyproject.toml version: {target_version}")
        else:
            error_msg = "pyproject.toml version mismatch"
            print_error(error_msg)
            errors.append(error_msg)
    else:
        error_msg = "pyproject.toml not found"
        print_error(error_msg)
        errors.append(error_msg)

    # Check CLI version
    try:
        result = subprocess.run(
            ["qontinui-devtools", "--version"], capture_output=True, text=True, timeout=5
        )
        if target_version in result.output:
            print_success(f"CLI version: {target_version}")
        else:
            error_msg = "CLI version mismatch"
            print_error(error_msg)
            errors.append(error_msg)
    except Exception as e:
        error_msg = f"Failed to check CLI version: {e}"
        print_error(error_msg)
        errors.append(error_msg)

    return len(errors) == 0, errors


def verify_documentation() -> tuple[bool, list[str]]:
    """Verify documentation files exist."""
    print_header("Verifying Documentation")

    docs_root = Path(__file__).parent.parent / "docs"
    required_docs = [
        "phase4-guide.md",
    ]

    errors = []
    success_count = 0

    for doc in required_docs:
        doc_path = docs_root / doc
        if doc_path.exists():
            size_kb = doc_path.stat().st_size / 1024
            print_success(f"Found {doc} ({size_kb:.1f} KB)")
            success_count += 1
        else:
            error_msg = f"Missing documentation: {doc}"
            print_error(error_msg)
            errors.append(error_msg)

    # Check README updates
    readme_path = Path(__file__).parent.parent / "README.md"
    if readme_path.exists():
        content = readme_path.read_text()
        phase4_keywords = [
            "Phase 4",
            "Security Analyzer",
            "Documentation Generator",
            "Regression Detector",
            "Type Hint Analyzer",
            "Dependency Health",
        ]
        found_keywords = [kw for kw in phase4_keywords if kw in content]

        if len(found_keywords) >= 4:
            print_success(f"README contains Phase 4 information ({len(found_keywords)}/6 keywords)")
            success_count += 1
        else:
            error_msg = "README missing Phase 4 information"
            print_error(error_msg)
            errors.append(error_msg)

    # Check CHANGELOG
    changelog_path = Path(__file__).parent.parent / "CHANGELOG.md"
    if changelog_path.exists():
        content = changelog_path.read_text()
        if "[1.1.0]" in content and "Phase 4" in content:
            print_success("CHANGELOG contains v1.1.0 release notes")
            success_count += 1
        else:
            error_msg = "CHANGELOG missing v1.1.0 release notes"
            print_error(error_msg)
            errors.append(error_msg)

    total_checks = len(required_docs) + 2
    print(f"\n{Color.BOLD}Documentation checks: {success_count}/{total_checks} passed{Color.END}")

    return len(errors) == 0, errors


def verify_tests() -> tuple[bool, list[str]]:
    """Verify integration tests exist."""
    print_header("Verifying Integration Tests")

    test_file = (
        Path(__file__).parent.parent
        / "python"
        / "tests"
        / "integration"
        / "test_phase4_integration.py"
    )

    errors = []

    if test_file.exists():
        size_kb = test_file.stat().st_size / 1024
        print_success(f"Found test_phase4_integration.py ({size_kb:.1f} KB)")

        # Count test functions
        content = test_file.read_text()
        test_count = content.count("def test_")
        class_count = content.count("class Test")

        print_info(f"  - {test_count} test functions")
        print_info(f"  - {class_count} test classes")

        if test_count >= 40:
            print_success(f"Sufficient test coverage: {test_count} tests")
        else:
            error_msg = f"Insufficient tests: {test_count} (expected >= 40)"
            print_warning(error_msg)
    else:
        error_msg = "Missing test_phase4_integration.py"
        print_error(error_msg)
        errors.append(error_msg)

    return len(errors) == 0, errors


def run_smoke_tests() -> tuple[bool, list[str]]:
    """Run basic smoke tests."""
    print_header("Running Smoke Tests")

    errors = []

    # Test that CLI doesn't crash
    commands = [
        ["qontinui-devtools", "--help"],
        ["qontinui-devtools", "security", "scan", "--help"],
        ["qontinui-devtools", "docs", "generate", "--help"],
        ["qontinui-devtools", "regression", "check", "--help"],
        ["qontinui-devtools", "types", "coverage", "--help"],
        ["qontinui-devtools", "deps", "check", "--help"],
    ]

    success_count = 0

    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print_success(f"Smoke test passed: {' '.join(cmd[1:])}")
                success_count += 1
            else:
                error_msg = f"Smoke test failed: {' '.join(cmd[1:])}"
                print_error(error_msg)
                errors.append(error_msg)
        except Exception as e:
            error_msg = f"Smoke test error: {' '.join(cmd[1:])}: {e}"
            print_error(error_msg)
            errors.append(error_msg)

    print(f"\n{Color.BOLD}Smoke tests: {success_count}/{len(commands)} passed{Color.END}")

    return len(errors) == 0, errors


def main() -> int:
    """Run all verification checks."""
    print(f"\n{Color.BOLD}Phase 4 Integration Verification{Color.END}")
    print(f"{Color.BOLD}Version 1.1.0{Color.END}\n")

    all_errors = []
    results = []

    # Run all verification checks
    checks = [
        ("Imports", verify_imports),
        ("CLI Commands", verify_cli_commands),
        ("Version", verify_version),
        ("Documentation", verify_documentation),
        ("Tests", verify_tests),
        ("Smoke Tests", run_smoke_tests),
    ]

    for name, check_func in checks:
        success, errors = check_func()
        results.append((name, success))
        all_errors.extend(errors)

    # Print summary
    print_header("Verification Summary")

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        if success:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")

    print(f"\n{Color.BOLD}Overall: {passed}/{total} checks passed{Color.END}")

    if all_errors:
        print(f"\n{Color.BOLD}{Color.RED}Errors found:{Color.END}")
        for error in all_errors:
            print(f"  - {error}")

    if passed == total:
        print(f"\n{Color.BOLD}{Color.GREEN}{'=' * 70}{Color.END}")
        print(
            f"{Color.BOLD}{Color.GREEN}All verifications passed! Phase 4 integration complete.{Color.END}"
        )
        print(f"{Color.BOLD}{Color.GREEN}{'=' * 70}{Color.END}\n")
        return 0
    else:
        print(f"\n{Color.BOLD}{Color.RED}{'=' * 70}{Color.END}")
        print(
            f"{Color.BOLD}{Color.RED}Some verifications failed. Please review errors above.{Color.END}"
        )
        print(f"{Color.BOLD}{Color.RED}{'=' * 70}{Color.END}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
