"""Make the dependencies module runnable as a script.

Usage:
    python -m qontinui_devtools.dependencies [options] [project_path]
"""

from .cli import main

if __name__ == "__main__":
    main()
