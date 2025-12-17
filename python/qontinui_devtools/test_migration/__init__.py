"""
Brobot Test Migration System

This package provides tools for migrating Java unit and integration tests
from the Brobot library to equivalent Python tests in the Qontinui project.

This module is designed to be independent of the main qontinui package
to avoid dependency issues during the migration process.

TODO: DEPRECATED - Migrated to qontinui-devtools (Phase 2: Core Library Cleanup)
This entire directory was moved to qontinui-devtools/python/qontinui_devtools/brobot_migration/
This directory can be removed after verifying the migration works correctly.
Users should use: from qontinui_devtools.brobot_migration import ...
"""

__version__ = "0.1.0"

# Prevent automatic import of parent qontinui package
import sys
from pathlib import Path

# Ensure we can import our submodules without triggering parent imports
_current_dir = Path(__file__).parent
sys.path.insert(0, str(_current_dir))

# Clean up
del sys, Path
