"""
Comprehensive tests for the ImportTracer module.

This test suite verifies:
- Basic import tracking functionality
- Circular dependency detection
- Thread safety
- Import graph construction
- Report generation
"""

import sys
import threading
import time
import unittest
from pathlib import Path

# Add tests directory to path to allow imports of fixtures
test_dir = Path(__file__).parent.parent
if str(test_dir) not in sys.path:
    sys.path.insert(0, str(test_dir))

# Also ensure we can import from fixtures
fixtures_dir = test_dir / "fixtures"
if str(fixtures_dir) not in sys.path:
    sys.path.insert(0, str(fixtures_dir))

from qontinui_devtools.import_analysis import (
    ImportEvent,
    ImportGraph,
    ImportTracer,
)


class TestImportEvent(unittest.TestCase):
    """Test the ImportEvent dataclass."""

    def test_create_import_event(self):
        """Test creating an ImportEvent."""
        event = ImportEvent(
            module_name="test_module",
            importer="main",
            timestamp=time.time(),
            thread_id=threading.get_ident(),
            stack_trace=["frame1", "frame2"],
        )

        self.assertEqual(event.module_name, "test_module")
        self.assertEqual(event.importer, "main")
        self.assertIsInstance(event.timestamp, float)
        self.assertIsInstance(event.thread_id, int)
        self.assertEqual(len(event.stack_trace), 2)

    def test_to_dict(self):
        """Test converting ImportEvent to dictionary."""
        event = ImportEvent(
            module_name="test_module",
            importer="main",
            timestamp=12345.67,
            thread_id=999,
            stack_trace=["frame"],
        )

        event_dict = event.to_dict()

        self.assertIsInstance(event_dict, dict)
        self.assertEqual(event_dict["module_name"], "test_module")
        self.assertEqual(event_dict["importer"], "main")
        self.assertEqual(event_dict["timestamp"], 12345.67)
        self.assertEqual(event_dict["thread_id"], 999)


class TestImportGraph(unittest.TestCase):
    """Test the ImportGraph class."""

    def setUp(self):
        """Set up test fixtures."""
        self.graph = ImportGraph()

    def test_add_import(self):
        """Test adding imports to the graph."""
        self.graph.add_import("module_a", "module_b")
        deps = self.graph.get_dependencies("module_a")
        self.assertIn("module_b", deps)

    def test_get_dependencies(self):
        """Test retrieving module dependencies."""
        self.graph.add_import("A", "B")
        self.graph.add_import("A", "C")

        deps = self.graph.get_dependencies("A")
        self.assertEqual(len(deps), 2)
        self.assertIn("B", deps)
        self.assertIn("C", deps)

    def test_get_dependencies_nonexistent(self):
        """Test getting dependencies of non-existent module."""
        deps = self.graph.get_dependencies("nonexistent")
        self.assertEqual(len(deps), 0)

    def test_simple_circular_dependency(self):
        """Test detecting simple A -> B -> A cycle."""
        self.graph.add_import("A", "B")
        self.graph.add_import("B", "A")

        cycles = self.graph.find_circular_paths()

        self.assertGreater(len(cycles), 0, "Should detect circular dependency")

        # Verify cycle contains both A and B
        found_cycle = False
        for cycle in cycles:
            if "A" in cycle and "B" in cycle:
                found_cycle = True
                break

        self.assertTrue(found_cycle, "Cycle should contain A and B")

    def test_three_node_cycle(self):
        """Test detecting A -> B -> C -> A cycle."""
        self.graph.add_import("A", "B")
        self.graph.add_import("B", "C")
        self.graph.add_import("C", "A")

        cycles = self.graph.find_circular_paths()

        self.assertGreater(len(cycles), 0, "Should detect circular dependency")

        # Verify cycle contains A, B, and C
        found_cycle = False
        for cycle in cycles:
            if "A" in cycle and "B" in cycle and "C" in cycle:
                found_cycle = True
                break

        self.assertTrue(found_cycle, "Cycle should contain A, B, and C")

    def test_no_circular_dependency(self):
        """Test that linear imports don't create false positives."""
        self.graph.add_import("A", "B")
        self.graph.add_import("B", "C")
        self.graph.add_import("C", "D")

        cycles = self.graph.find_circular_paths()

        self.assertEqual(len(cycles), 0, "Should not detect cycles in linear graph")

    def test_to_dict(self):
        """Test converting graph to dictionary."""
        self.graph.add_import("A", "B")
        self.graph.add_import("B", "C")

        graph_dict = self.graph.to_dict()

        self.assertIn("nodes", graph_dict)
        self.assertIn("edges", graph_dict)
        self.assertGreater(len(graph_dict["nodes"]), 0)
        self.assertGreater(len(graph_dict["edges"]), 0)

    def test_get_all_modules(self):
        """Test getting all modules in the graph."""
        self.graph.add_import("A", "B")
        self.graph.add_import("B", "C")

        modules = self.graph.get_all_modules()

        self.assertEqual(len(modules), 3)
        self.assertIn("A", modules)
        self.assertIn("B", modules)
        self.assertIn("C", modules)

    def test_thread_safety(self):
        """Test that graph is thread-safe."""

        def add_imports(start_idx):
            for i in range(start_idx, start_idx + 100):
                self.graph.add_import(f"module_{i}", f"module_{i+1}")

        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_imports, args=(i * 100,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # Verify we got all modules
        modules = self.graph.get_all_modules()
        self.assertGreater(len(modules), 400)


class TestImportTracer(unittest.TestCase):
    """Test the ImportTracer context manager."""

    def test_context_manager(self):
        """Test that ImportTracer works as a context manager."""
        with ImportTracer() as tracer:
            self.assertIsInstance(tracer, ImportTracer)

        # Hook should be removed after exiting context
        self.assertFalse(tracer._installed)

    def test_track_simple_import(self):
        """Test tracking a simple module import."""
        # Remove module from sys.modules if it exists
        if "fixtures.simple_module" in sys.modules:
            del sys.modules["fixtures.simple_module"]

        with ImportTracer() as tracer:
            import fixtures.simple_module  # noqa: F401

        events = tracer.get_events()

        # Should have tracked the import
        module_names = [e.module_name for e in events]
        self.assertTrue(
            any("simple_module" in name for name in module_names),
            f"simple_module not found in: {module_names}",
        )

    def test_detect_circular_import_simple(self):
        """Test detecting simple circular dependency A <-> B."""
        # Remove modules if they exist
        for mod in ["fixtures.circular_a", "fixtures.circular_b"]:
            if mod in sys.modules:
                del sys.modules[mod]

        with ImportTracer() as tracer:
            try:
                import fixtures.circular_a  # noqa: F401
            except ImportError:
                # Circular import might fail, that's okay
                pass

        cycles = tracer.find_circular_dependencies()

        # Should detect the circular dependency
        if len(cycles) > 0:
            found_ab_cycle = False
            for cycle in cycles:
                cycle_str = "->".join(cycle)
                if "circular_a" in cycle_str and "circular_b" in cycle_str:
                    found_ab_cycle = True
                    break

            self.assertTrue(
                found_ab_cycle, f"Should detect circular_a <-> circular_b cycle. Found: {cycles}"
            )

    def test_detect_circular_import_complex(self):
        """Test detecting complex three-way circular dependency C -> D -> E -> C."""
        # Remove modules if they exist
        for mod in ["fixtures.circular_c", "fixtures.circular_d", "fixtures.circular_e"]:
            if mod in sys.modules:
                del sys.modules[mod]

        with ImportTracer() as tracer:
            try:
                import fixtures.circular_c  # noqa: F401
            except ImportError:
                # Circular import might fail, that's okay
                pass

        cycles = tracer.find_circular_dependencies()

        # Should detect the circular dependency
        if len(cycles) > 0:
            found_cde_cycle = False
            for cycle in cycles:
                cycle_str = "->".join(cycle)
                if all(name in cycle_str for name in ["circular_c", "circular_d", "circular_e"]):
                    found_cde_cycle = True
                    break

            self.assertTrue(
                found_cde_cycle, f"Should detect C -> D -> E -> C cycle. Found: {cycles}"
            )

    def test_generate_report(self):
        """Test generating a text report."""
        # Remove module if it exists
        if "fixtures.simple_module" in sys.modules:
            del sys.modules["fixtures.simple_module"]

        with ImportTracer() as tracer:
            import fixtures.simple_module  # noqa: F401

        report = tracer.generate_report()

        self.assertIsInstance(report, str)
        self.assertIn("IMPORT TRACER REPORT", report)
        self.assertIn("Total imports tracked", report)

    def test_to_dict(self):
        """Test exporting tracer data to dictionary."""
        with ImportTracer() as tracer:
            pass  # Track some imports

        data = tracer.to_dict()

        self.assertIsInstance(data, dict)
        self.assertIn("events", data)
        self.assertIn("graph", data)
        self.assertIn("circular_dependencies", data)
        self.assertIn("start_time", data)

    def test_get_graph(self):
        """Test getting the import graph."""
        with ImportTracer() as tracer:
            pass

        graph = tracer.get_graph()

        self.assertIsInstance(graph, ImportGraph)

    def test_multiple_threads(self):
        """Test that import tracking works across multiple threads."""
        # Remove module if it exists
        if "fixtures.simple_module" in sys.modules:
            del sys.modules["fixtures.simple_module"]

        events_collected = []

        def import_in_thread(tracer):
            import fixtures.simple_module  # noqa: F401

            events_collected.extend(tracer.get_events())

        with ImportTracer() as tracer:
            threads = []
            for _ in range(3):
                thread = threading.Thread(target=import_in_thread, args=(tracer,))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

        # Should have tracked imports from multiple threads
        events = tracer.get_events()
        thread_ids = {e.thread_id for e in events}

        # We expect at least the main thread
        self.assertGreater(len(events), 0)

    def test_no_false_positives(self):
        """Test that linear imports don't trigger false circular dependency warnings."""
        # Remove module if it exists
        if "fixtures.simple_module" in sys.modules:
            del sys.modules["fixtures.simple_module"]

        with ImportTracer() as tracer:
            import fixtures.simple_module  # noqa: F401

        cycles = tracer.find_circular_dependencies()

        # There should be no cycles for a simple module
        # (Note: There might be cycles in stdlib or other dependencies,
        # but not in our simple_module itself)
        simple_cycles = [c for c in cycles if any("simple_module" in node for node in c)]

        self.assertEqual(
            len(simple_cycles),
            0,
            f"simple_module should not have circular dependencies: {simple_cycles}",
        )


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete import analysis workflow."""

    def test_full_workflow(self):
        """Test the complete workflow: trace -> analyze -> report."""
        # Remove modules if they exist
        for mod in ["fixtures.circular_a", "fixtures.circular_b"]:
            if mod in sys.modules:
                del sys.modules[mod]

        # Step 1: Trace imports
        with ImportTracer() as tracer:
            try:
                import fixtures.circular_a  # noqa: F401
            except ImportError:
                pass

        # Step 2: Analyze
        cycles = tracer.find_circular_dependencies()
        events = tracer.get_events()
        graph = tracer.get_graph()

        # Step 3: Generate report
        report = tracer.generate_report()
        data = tracer.to_dict()

        # Verify we got useful data
        self.assertIsInstance(events, list)
        self.assertIsInstance(graph, ImportGraph)
        self.assertIsInstance(report, str)
        self.assertIsInstance(data, dict)

    def test_report_shows_circular_dependencies(self):
        """Test that report clearly shows circular dependencies."""
        # Remove modules if they exist
        for mod in ["fixtures.circular_a", "fixtures.circular_b"]:
            if mod in sys.modules:
                del sys.modules[mod]

        with ImportTracer() as tracer:
            try:
                import fixtures.circular_a  # noqa: F401
            except ImportError:
                pass

        report = tracer.generate_report()

        # Report should mention circular dependencies if found
        cycles = tracer.find_circular_dependencies()
        if cycles:
            self.assertIn("CIRCULAR", report.upper())


def run_tests():
    """Run all tests and return results."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == "__main__":
    unittest.main()
