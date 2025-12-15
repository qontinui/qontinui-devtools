"""
Tests for HTML report generator.
"""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from qontinui_devtools.reporting import HTMLReportGenerator, ReportData, ReportSection


class TestReportSection:
    """Tests for ReportSection dataclass."""

    def test_valid_section(self):
        """Test creating a valid report section."""
        section = ReportSection(
            id="test",
            title="Test Section",
            content="<p>Test content</p>",
            severity="success",
            metrics={"count": 5},
        )

        assert section.id == "test"
        assert section.title == "Test Section"
        assert section.severity == "success"
        assert section.metrics["count"] == 5

    def test_invalid_severity(self):
        """Test that invalid severity raises error."""
        with pytest.raises(ValueError, match="Invalid severity"):
            ReportSection(
                id="test",
                title="Test",
                content="content",
                severity="invalid",
            )

    def test_default_metrics(self):
        """Test default empty metrics."""
        section = ReportSection(
            id="test",
            title="Test",
            content="content",
            severity="info",
        )

        assert section.metrics == {}
        assert section.chart_data == {}


class TestReportData:
    """Tests for ReportData dataclass."""

    def test_create_report_data(self):
        """Test creating report data."""
        data = ReportData(
            project_name="TestProject",
            analysis_date=datetime(2024, 1, 1, 12, 0, 0),
            project_path="/path/to/project",
        )

        assert data.project_name == "TestProject"
        assert data.sections == []
        assert data.summary_metrics == {}

    def test_add_section(self):
        """Test adding sections to report."""
        data = ReportData(
            project_name="Test",
            analysis_date=datetime.now(),
        )

        section1 = ReportSection(
            id="sec1",
            title="Section 1",
            content="content1",
            severity="info",
        )

        section2 = ReportSection(
            id="sec2",
            title="Section 2",
            content="content2",
            severity="warning",
        )

        data.add_section(section1)
        data.add_section(section2)

        assert len(data.sections) == 2
        assert data.sections[0].id == "sec1"
        assert data.sections[1].id == "sec2"

    def test_get_section(self):
        """Test getting section by ID."""
        data = ReportData(
            project_name="Test",
            analysis_date=datetime.now(),
        )

        section = ReportSection(
            id="test",
            title="Test",
            content="content",
            severity="info",
        )

        data.add_section(section)

        retrieved = data.get_section("test")
        assert retrieved is not None
        assert retrieved.id == "test"

        not_found = data.get_section("nonexistent")
        assert not_found is None

    def test_get_overall_status_all_success(self):
        """Test overall status with all success sections."""
        data = ReportData(
            project_name="Test",
            analysis_date=datetime.now(),
        )

        data.add_section(
            ReportSection(
                id="s1",
                title="S1",
                content="c",
                severity="success",
            )
        )

        data.add_section(
            ReportSection(
                id="s2",
                title="S2",
                content="c",
                severity="success",
            )
        )

        color, icon, message = data.get_overall_status()
        assert color == "green"
        assert "Passed" in message or "Excellent" in message

    def test_get_overall_status_with_errors(self):
        """Test overall status with errors."""
        data = ReportData(
            project_name="Test",
            analysis_date=datetime.now(),
        )

        data.add_section(
            ReportSection(
                id="s1",
                title="S1",
                content="c",
                severity="error",
            )
        )

        color, icon, message = data.get_overall_status()
        assert color == "red"
        assert "error" in message.lower()

    def test_get_overall_status_with_warnings(self):
        """Test overall status with warnings."""
        data = ReportData(
            project_name="Test",
            analysis_date=datetime.now(),
        )

        # Add multiple warnings to trigger warning status
        for i in range(6):
            data.add_section(
                ReportSection(
                    id=f"s{i}",
                    title=f"S{i}",
                    content="c",
                    severity="warning",
                )
            )

        color, icon, message = data.get_overall_status()
        assert color == "yellow"
        assert "warning" in message.lower()


class TestHTMLReportGenerator:
    """Tests for HTMLReportGenerator."""

    def test_initialization(self):
        """Test generator initialization."""
        generator = HTMLReportGenerator(verbose=False)
        assert generator.verbose is False
        assert generator.env is not None

    def test_generate_report(self):
        """Test generating HTML report."""
        generator = HTMLReportGenerator()

        # Create test data
        report_data = ReportData(
            project_name="TestProject",
            analysis_date=datetime(2024, 1, 1, 12, 0, 0),
            project_path="/test/path",
            version="1.0.0",
        )

        report_data.summary_metrics = {
            "files_analyzed": 10,
            "total_lines": 1000,
        }

        report_data.add_section(
            ReportSection(
                id="imports",
                title="Import Analysis",
                content="<p>No circular dependencies found.</p>",
                severity="success",
                metrics={"circular_dependencies": 0},
            )
        )

        report_data.add_section(
            ReportSection(
                id="architecture",
                title="Architecture",
                content="<p>2 god classes detected.</p>",
                severity="warning",
                metrics={"god_classes": 2},
            )
        )

        # Generate report
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            generator.generate(report_data, output_path)

            # Verify file was created
            assert Path(output_path).exists()

            # Read and verify content
            html_content = Path(output_path).read_text()

            # Check for key elements
            assert "TestProject" in html_content
            assert "Code Quality Report" in html_content
            assert "Import Analysis" in html_content
            assert "Architecture" in html_content
            assert "No circular dependencies" in html_content
            assert "god classes" in html_content

            # Check for Chart.js
            assert "chart.js" in html_content.lower()

            # Check for navigation
            assert "nav" in html_content.lower()

            # Check for sections
            assert 'id="imports"' in html_content
            assert 'id="architecture"' in html_content

        finally:
            # Cleanup
            Path(output_path).unlink(missing_ok=True)

    def test_calculate_quality_score(self):
        """Test quality score calculation."""
        generator = HTMLReportGenerator()

        # Perfect score
        report_data = ReportData(
            project_name="Test",
            analysis_date=datetime.now(),
        )
        report_data.summary_metrics = {}
        generator.report_data = report_data

        score = generator._calculate_quality_score()
        assert score == 100.0

        # With errors
        report_data.add_section(
            ReportSection(
                id="s1",
                title="S1",
                content="c",
                severity="error",
            )
        )
        score = generator._calculate_quality_score()
        assert score < 100.0

        # With warnings
        report_data.add_section(
            ReportSection(
                id="s2",
                title="S2",
                content="c",
                severity="warning",
            )
        )
        score = generator._calculate_quality_score()
        assert score < 90.0

    def test_prepare_key_metrics(self):
        """Test preparing key metrics for display."""
        generator = HTMLReportGenerator()

        report_data = ReportData(
            project_name="Test",
            analysis_date=datetime.now(),
        )

        report_data.summary_metrics = {
            "files_analyzed": 50,
            "circular_dependencies": 0,
            "god_classes": 0,
            "race_conditions": 0,
        }

        report_data.add_section(
            ReportSection(
                id="s1",
                title="S1",
                content="c",
                severity="success",
            )
        )

        generator.report_data = report_data
        metrics = generator._prepare_key_metrics()

        assert len(metrics) > 0
        assert any(m["name"] == "Total Issues" for m in metrics)
        assert any(m["name"] == "Files Analyzed" for m in metrics)
        assert any(m["name"] == "Quality Score" for m in metrics)

    def test_create_summary_section(self):
        """Test creating summary section from metrics."""
        generator = HTMLReportGenerator()

        metrics = {
            "files_analyzed": 42,
            "total_lines": 5000,
            "issues_found": 3,
        }

        section = generator.create_summary_section(metrics)

        assert section.id == "summary"
        assert section.title == "Summary"
        assert section.severity == "info"
        assert "files_analyzed" in section.content.lower() or "42" in section.content
        assert section.metrics == metrics

    def test_generate_with_invalid_data(self):
        """Test generating report with no data."""
        generator = HTMLReportGenerator()

        with pytest.raises(ValueError, match="No report data"):
            generator.generate(
                report_data=None,  # type: ignore
                output_path="test.html",
            )

    def test_add_section_without_data(self):
        """Test adding section without setting report data first."""
        generator = HTMLReportGenerator()

        section = ReportSection(
            id="test",
            title="Test",
            content="content",
            severity="info",
        )

        with pytest.raises(ValueError, match="No report data"):
            generator.add_section(section)

    def test_format_datetime(self):
        """Test datetime formatting."""
        dt = datetime(2024, 1, 15, 14, 30, 45)
        formatted = HTMLReportGenerator._format_datetime(dt)

        assert "2024" in formatted
        assert "01" in formatted or "1" in formatted
        assert "15" in formatted

    def test_format_number(self):
        """Test number formatting."""
        assert HTMLReportGenerator._format_number(1000) == "1,000"
        assert HTMLReportGenerator._format_number(1000000) == "1,000,000"
        assert HTMLReportGenerator._format_number(42) == "42"


class TestReportGeneration:
    """Integration tests for report generation."""

    def test_full_report_generation(self):
        """Test generating a complete report with all sections."""
        generator = HTMLReportGenerator(verbose=False)

        # Create comprehensive test data
        report_data = ReportData(
            project_name="ComprehensiveTest",
            analysis_date=datetime.now(),
            project_path="/test/project",
            version="1.0.0",
        )

        report_data.summary_metrics = {
            "files_analyzed": 100,
            "total_lines": 10000,
            "circular_dependencies": 2,
            "god_classes": 3,
            "race_conditions": 1,
            "critical_issues": 6,
        }

        # Add all section types
        sections = [
            ReportSection(
                id="imports",
                title="Import Analysis",
                content="<p>Found 2 circular dependencies.</p>",
                severity="warning",
                metrics={"circular_dependencies": 2},
            ),
            ReportSection(
                id="architecture",
                title="Architecture",
                content="<p>Found 3 god classes.</p>",
                severity="warning",
                metrics={"god_classes": 3},
            ),
            ReportSection(
                id="quality",
                title="Code Quality",
                content="<p>Code quality is good.</p>",
                severity="success",
                metrics={"total_issues": 5},
            ),
            ReportSection(
                id="concurrency",
                title="Concurrency",
                content="<p>Found 1 race condition.</p>",
                severity="warning",
                metrics={"race_conditions": 1},
            ),
            ReportSection(
                id="recommendations",
                title="Recommendations",
                content="<p>Fix circular dependencies first.</p>",
                severity="info",
                metrics={"total_recommendations": 4},
            ),
        ]

        for section in sections:
            report_data.add_section(section)

        # Generate report
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            generator.generate(report_data, output_path)

            # Verify
            html_content = Path(output_path).read_text()

            # Check all sections present
            for section in sections:
                assert section.title in html_content
                assert f'id="{section.id}"' in html_content

            # Check metrics
            assert "100" in html_content  # files_analyzed appears in summary
            # Note: Not all summary_metrics necessarily appear in key metrics cards,
            # but they're available in the data structure

            # Check charts
            assert "Chart" in html_content
            assert "canvas" in html_content

            # Check responsive design
            assert "responsive" in html_content.lower()
            assert "viewport" in html_content.lower()

            # Verify file size is reasonable (should be > 5KB for full report)
            assert Path(output_path).stat().st_size > 5000

        finally:
            Path(output_path).unlink(missing_ok=True)

    def test_report_with_empty_sections(self):
        """Test report with minimal data."""
        generator = HTMLReportGenerator()

        report_data = ReportData(
            project_name="MinimalTest",
            analysis_date=datetime.now(),
        )

        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
            output_path = f.name

        try:
            generator.generate(report_data, output_path)

            # Should still generate valid HTML
            assert Path(output_path).exists()

            html_content = Path(output_path).read_text()
            assert "MinimalTest" in html_content
            assert "<!DOCTYPE html>" in html_content

        finally:
            Path(output_path).unlink(missing_ok=True)
