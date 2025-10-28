"""Test fixture: Module with high coupling (many dependencies)."""

import os
import sys
import ast
import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional
from dataclasses import dataclass
from collections import defaultdict
import re
import time
import threading


class HighlyCoupledClass:
    """A class that depends on many external modules."""

    def __init__(self):
        self.path = Path("/tmp")
        self.data: Dict = {}
        self.logger = logging.getLogger(__name__)
        self.patterns: Set[str] = set()

    def process_data(self, input_file: str) -> List[Dict]:
        """Process data from a file."""
        # Uses: os, json, Path, logging
        if not os.path.exists(input_file):
            self.logger.error(f"File not found: {input_file}")
            return []

        with open(input_file) as f:
            data = json.load(f)

        return data

    def parse_code(self, source: str) -> ast.Module:
        """Parse Python source code."""
        # Uses: ast, re
        source = re.sub(r'#.*', '', source)
        return ast.parse(source)

    def run_parallel(self, tasks: List) -> None:
        """Run tasks in parallel."""
        # Uses: threading, time
        threads = []
        for task in tasks:
            t = threading.Thread(target=task)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()
            time.sleep(0.1)
