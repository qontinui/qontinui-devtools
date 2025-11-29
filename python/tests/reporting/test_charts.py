"""
Tests for chart generation utilities.
"""

from qontinui_devtools.reporting.charts import (
    create_bar_chart,
    create_doughnut_chart,
    create_line_chart,
    create_multi_axis_chart,
    create_pie_chart,
    create_radar_chart,
    create_scatter_chart,
    create_stacked_bar_chart,
)


class TestBarChart:
    """Tests for bar chart creation."""

    def test_create_basic_bar_chart(self):
        """Test creating a basic bar chart."""
        chart = create_bar_chart(
            labels=["A", "B", "C"],
            data=[10, 20, 30],
            title="Test Chart",
        )

        assert chart["type"] == "bar"
        assert chart["data"]["labels"] == ["A", "B", "C"]
        assert chart["data"]["datasets"][0]["data"] == [10, 20, 30]
        assert chart["options"]["plugins"]["title"]["text"] == "Test Chart"

    def test_bar_chart_colors(self):
        """Test bar chart with different colors."""
        for color in ["blue", "red", "green", "yellow", "purple"]:
            chart = create_bar_chart(
                labels=["X"],
                data=[5],
                title="Color Test",
                color=color,
            )

            assert "rgba" in chart["data"]["datasets"][0]["backgroundColor"]

    def test_horizontal_bar_chart(self):
        """Test creating horizontal bar chart."""
        chart = create_bar_chart(
            labels=["A", "B"],
            data=[1, 2],
            title="Horizontal",
            horizontal=True,
        )

        assert chart["type"] == "horizontalBar"


class TestPieChart:
    """Tests for pie chart creation."""

    def test_create_basic_pie_chart(self):
        """Test creating a basic pie chart."""
        chart = create_pie_chart(
            labels=["Red", "Blue", "Green"],
            data=[30, 50, 20],
            title="Distribution",
        )

        assert chart["type"] == "pie"
        assert chart["data"]["labels"] == ["Red", "Blue", "Green"]
        assert chart["data"]["datasets"][0]["data"] == [30, 50, 20]
        assert len(chart["data"]["datasets"][0]["backgroundColor"]) == 3

    def test_pie_chart_custom_colors(self):
        """Test pie chart with custom colors."""
        chart = create_pie_chart(
            labels=["A", "B"],
            data=[60, 40],
            title="Custom Colors",
            colors=["red", "blue"],
        )

        bg_colors = chart["data"]["datasets"][0]["backgroundColor"]
        assert len(bg_colors) == 2


class TestDoughnutChart:
    """Tests for doughnut chart creation."""

    def test_create_doughnut_chart(self):
        """Test creating a doughnut chart."""
        chart = create_doughnut_chart(
            labels=["X", "Y", "Z"],
            data=[10, 20, 30],
            title="Doughnut",
        )

        assert chart["type"] == "doughnut"
        assert chart["data"]["labels"] == ["X", "Y", "Z"]


class TestLineChart:
    """Tests for line chart creation."""

    def test_create_basic_line_chart(self):
        """Test creating a basic line chart."""
        chart = create_line_chart(
            labels=["Jan", "Feb", "Mar"],
            datasets=[
                {"label": "Series 1", "data": [10, 20, 15]},
                {"label": "Series 2", "data": [5, 15, 25]},
            ],
            title="Trend",
        )

        assert chart["type"] == "line"
        assert chart["data"]["labels"] == ["Jan", "Feb", "Mar"]
        assert len(chart["data"]["datasets"]) == 2
        assert chart["data"]["datasets"][0]["label"] == "Series 1"

    def test_line_chart_with_axis_labels(self):
        """Test line chart with axis labels."""
        chart = create_line_chart(
            labels=["1", "2", "3"],
            datasets=[{"label": "Data", "data": [1, 2, 3]}],
            title="Test",
            x_label="Time",
            y_label="Value",
        )

        assert chart["options"]["scales"]["x"]["title"]["text"] == "Time"
        assert chart["options"]["scales"]["y"]["title"]["text"] == "Value"

    def test_line_chart_colors(self):
        """Test line chart with custom colors."""
        chart = create_line_chart(
            labels=["A"],
            datasets=[
                {"label": "Red", "data": [1], "color": "red"},
                {"label": "Blue", "data": [2], "color": "blue"},
            ],
            title="Colors",
        )

        datasets = chart["data"]["datasets"]
        assert "rgba" in datasets[0]["backgroundColor"]
        assert "rgba" in datasets[1]["backgroundColor"]


class TestScatterChart:
    """Tests for scatter chart creation."""

    def test_create_scatter_chart(self):
        """Test creating a scatter chart."""
        chart = create_scatter_chart(
            datasets=[
                {
                    "label": "Dataset 1",
                    "data": [{"x": 1, "y": 2}, {"x": 2, "y": 3}],
                }
            ],
            title="Scatter",
        )

        assert chart["type"] == "scatter"
        assert len(chart["data"]["datasets"]) == 1
        assert len(chart["data"]["datasets"][0]["data"]) == 2

    def test_scatter_chart_with_labels(self):
        """Test scatter chart with axis labels."""
        chart = create_scatter_chart(
            datasets=[{"label": "Points", "data": [{"x": 1, "y": 1}]}],
            title="Test",
            x_label="X Axis",
            y_label="Y Axis",
        )

        assert chart["options"]["scales"]["x"]["title"]["text"] == "X Axis"
        assert chart["options"]["scales"]["y"]["title"]["text"] == "Y Axis"


class TestStackedBarChart:
    """Tests for stacked bar chart creation."""

    def test_create_stacked_bar_chart(self):
        """Test creating a stacked bar chart."""
        chart = create_stacked_bar_chart(
            labels=["Q1", "Q2", "Q3"],
            datasets=[
                {"label": "Product A", "data": [10, 15, 20]},
                {"label": "Product B", "data": [20, 25, 30]},
            ],
            title="Sales",
        )

        assert chart["type"] == "bar"
        assert chart["options"]["scales"]["x"]["stacked"] is True
        assert chart["options"]["scales"]["y"]["stacked"] is True
        assert len(chart["data"]["datasets"]) == 2

    def test_horizontal_stacked_bar_chart(self):
        """Test horizontal stacked bar chart."""
        chart = create_stacked_bar_chart(
            labels=["A"],
            datasets=[{"label": "D1", "data": [1]}],
            title="Horizontal Stacked",
            horizontal=True,
        )

        assert chart["type"] == "horizontalBar"


class TestRadarChart:
    """Tests for radar chart creation."""

    def test_create_radar_chart(self):
        """Test creating a radar chart."""
        chart = create_radar_chart(
            labels=["Speed", "Strength", "Intelligence", "Agility"],
            datasets=[
                {"label": "Character 1", "data": [80, 70, 90, 85]},
                {"label": "Character 2", "data": [90, 85, 70, 80]},
            ],
            title="Stats",
        )

        assert chart["type"] == "radar"
        assert len(chart["data"]["labels"]) == 4
        assert len(chart["data"]["datasets"]) == 2


class TestMultiAxisChart:
    """Tests for multi-axis chart creation."""

    def test_create_multi_axis_chart(self):
        """Test creating a multi-axis chart."""
        chart = create_multi_axis_chart(
            labels=["Jan", "Feb", "Mar"],
            datasets=[
                {"label": "Revenue", "data": [100, 150, 200], "yAxisID": "y"},
                {"label": "Users", "data": [1000, 1500, 2000], "yAxisID": "y1"},
            ],
            title="Multi Axis",
        )

        assert chart["type"] == "line"
        assert len(chart["data"]["datasets"]) == 2
        assert chart["data"]["datasets"][0]["yAxisID"] == "y"
        assert chart["data"]["datasets"][1]["yAxisID"] == "y1"
        assert "y1" in chart["options"]["scales"]


class TestChartOptions:
    """Tests for chart options and configuration."""

    def test_chart_responsive(self):
        """Test that charts are responsive."""
        chart = create_bar_chart(
            labels=["A"],
            data=[1],
            title="Test",
        )

        assert chart["options"]["responsive"] is True
        assert chart["options"]["maintainAspectRatio"] is False

    def test_chart_title_display(self):
        """Test chart title display."""
        chart = create_pie_chart(
            labels=["A"],
            data=[100],
            title="Test Title",
        )

        assert chart["options"]["plugins"]["title"]["display"] is True
        assert chart["options"]["plugins"]["title"]["text"] == "Test Title"

    def test_chart_legend_position(self):
        """Test chart legend positioning."""
        chart = create_line_chart(
            labels=["A"],
            datasets=[{"label": "D", "data": [1]}],
            title="Test",
        )

        assert "legend" in chart["options"]["plugins"]
        assert chart["options"]["plugins"]["legend"]["position"] == "top"

    def test_bar_chart_scales(self):
        """Test bar chart scale configuration."""
        chart = create_bar_chart(
            labels=["A"],
            data=[1],
            title="Test",
        )

        assert chart["options"]["scales"]["y"]["beginAtZero"] is True
        assert chart["options"]["scales"]["y"]["ticks"]["precision"] == 0
