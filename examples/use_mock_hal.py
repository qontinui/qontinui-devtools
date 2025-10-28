#!/usr/bin/env python3
"""Example: Using Mock HAL for testing without hardware."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from rich.console import Console

console = Console()

def main() -> None:
    console.print("[cyan]Mock HAL Usage Example[/cyan]")
    console.print("This demonstrates testing with Mock HAL instead of real hardware...")
    console.print("[yellow]Note: Mock HAL implementation coming in next phase[/yellow]")

if __name__ == "__main__":
    main()
