"""
Chart generation utilities for HTML reports.

Provides functions to create Chart.js configuration objects for various chart types.
"""

from typing import Any


def create_bar_chart(
    labels: list[str],
    data: list[int | float],
    title: str,
    color: str = "blue",
    horizontal: bool = False,
) -> dict[str, Any]:
    """
    Create Chart.js bar chart configuration.

    Args:
        labels: X-axis labels
        data: Data points
        title: Chart title
        color: Color scheme (blue, red, green, yellow, purple)
        horizontal: If True, create horizontal bar chart

    Returns:
        Chart.js configuration dict
    """
    color_map = {
        "blue": ("rgba(59, 130, 246, 0.7)", "rgba(59, 130, 246, 1)"),
        "red": ("rgba(239, 68, 68, 0.7)", "rgba(239, 68, 68, 1)"),
        "green": ("rgba(16, 185, 129, 0.7)", "rgba(16, 185, 129, 1)"),
        "yellow": ("rgba(245, 158, 11, 0.7)", "rgba(245, 158, 11, 1)"),
        "purple": ("rgba(139, 92, 246, 0.7)", "rgba(139, 92, 246, 1)"),
    }

    bg_color, border_color = color_map.get(color, color_map["blue"])

    return {
        "type": "bar" if not horizontal else "horizontalBar",
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": title,
                    "data": data,
                    "backgroundColor": bg_color,
                    "borderColor": border_color,
                    "borderWidth": 2,
                }
            ],
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "title": {"display": True, "text": title, "font": {"size": 16}},
                "legend": {"display": False},
            },
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "ticks": {"precision": 0},
                },
            },
        },
    }


def create_pie_chart(
    labels: list[str], data: list[int | float], title: str, colors: list[str] | None = None
) -> dict[str, Any]:
    """
    Create Chart.js pie chart configuration.

    Args:
        labels: Segment labels
        data: Data points
        title: Chart title
        colors: Optional list of color schemes (default: ["red", "yellow", "blue", "green"])

    Returns:
        Chart.js configuration dict
    """
    if colors is None:
        colors = ["red", "yellow", "blue", "green", "purple", "pink"]

    color_map = {
        "red": ("rgba(239, 68, 68, 0.8)", "rgba(239, 68, 68, 1)"),
        "yellow": ("rgba(245, 158, 11, 0.8)", "rgba(245, 158, 11, 1)"),
        "blue": ("rgba(59, 130, 246, 0.8)", "rgba(59, 130, 246, 1)"),
        "green": ("rgba(16, 185, 129, 0.8)", "rgba(16, 185, 129, 1)"),
        "purple": ("rgba(139, 92, 246, 0.8)", "rgba(139, 92, 246, 1)"),
        "pink": ("rgba(236, 72, 153, 0.8)", "rgba(236, 72, 153, 1)"),
    }

    bg_colors = []
    border_colors = []
    for i, _ in enumerate(data):
        color = colors[i % len(colors)]
        bg, border = color_map.get(color, color_map["blue"])
        bg_colors.append(bg)
        border_colors.append(border)

    return {
        "type": "pie",
        "data": {
            "labels": labels,
            "datasets": [
                {
                    "label": title,
                    "data": data,
                    "backgroundColor": bg_colors,
                    "borderColor": border_colors,
                    "borderWidth": 2,
                }
            ],
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "title": {"display": True, "text": title, "font": {"size": 16}},
                "legend": {"position": "bottom"},
            },
        },
    }


def create_doughnut_chart(
    labels: list[str], data: list[int | float], title: str, colors: list[str] | None = None
) -> dict[str, Any]:
    """
    Create Chart.js doughnut chart configuration.

    Args:
        labels: Segment labels
        data: Data points
        title: Chart title
        colors: Optional list of color schemes

    Returns:
        Chart.js configuration dict
    """
    config = create_pie_chart(labels, data, title, colors)
    config["type"] = "doughnut"
    return config


def create_line_chart(
    labels: list[str],
    datasets: list[dict[str, Any]],
    title: str,
    x_label: str = "",
    y_label: str = "",
) -> dict[str, Any]:
    """
    Create Chart.js line chart configuration for trends.

    Args:
        labels: X-axis labels
        datasets: List of datasets, each with 'label', 'data', and optional 'color'
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label

    Returns:
        Chart.js configuration dict
    """
    color_map = {
        "blue": ("rgba(59, 130, 246, 0.7)", "rgba(59, 130, 246, 1)"),
        "red": ("rgba(239, 68, 68, 0.7)", "rgba(239, 68, 68, 1)"),
        "green": ("rgba(16, 185, 129, 0.7)", "rgba(16, 185, 129, 1)"),
        "yellow": ("rgba(245, 158, 11, 0.7)", "rgba(245, 158, 11, 1)"),
        "purple": ("rgba(139, 92, 246, 0.7)", "rgba(139, 92, 246, 1)"),
    }

    default_colors = ["blue", "red", "green", "yellow", "purple"]
    formatted_datasets = []

    for i, dataset in enumerate(datasets):
        color = dataset.get("color", default_colors[i % len(default_colors)])
        bg_color, border_color = color_map.get(color, color_map["blue"])

        formatted_datasets.append(
            {
                "label": dataset["label"],
                "data": dataset["data"],
                "backgroundColor": bg_color,
                "borderColor": border_color,
                "borderWidth": 2,
                "fill": dataset.get("fill", False),
                "tension": 0.4,
            }
        )

    return {
        "type": "line",
        "data": {"labels": labels, "datasets": formatted_datasets},
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "title": {"display": True, "text": title, "font": {"size": 16}},
                "legend": {"position": "top"},
            },
            "scales": {
                "x": {"title": {"display": bool(x_label), "text": x_label}},
                "y": {
                    "beginAtZero": True,
                    "title": {"display": bool(y_label), "text": y_label},
                    "ticks": {"precision": 0},
                },
            },
        },
    }


def create_scatter_chart(
    datasets: list[dict[str, Any]],
    title: str,
    x_label: str = "",
    y_label: str = "",
) -> dict[str, Any]:
    """
    Create Chart.js scatter chart configuration.

    Args:
        datasets: List of datasets with 'label', 'data' (list of {x, y}), and optional 'color'
        title: Chart title
        x_label: X-axis label
        y_label: Y-axis label

    Returns:
        Chart.js configuration dict
    """
    color_map = {
        "blue": ("rgba(59, 130, 246, 0.7)", "rgba(59, 130, 246, 1)"),
        "red": ("rgba(239, 68, 68, 0.7)", "rgba(239, 68, 68, 1)"),
        "green": ("rgba(16, 185, 129, 0.7)", "rgba(16, 185, 129, 1)"),
        "yellow": ("rgba(245, 158, 11, 0.7)", "rgba(245, 158, 11, 1)"),
        "purple": ("rgba(139, 92, 246, 0.7)", "rgba(139, 92, 246, 1)"),
    }

    default_colors = ["blue", "red", "green", "yellow", "purple"]
    formatted_datasets = []

    for i, dataset in enumerate(datasets):
        color = dataset.get("color", default_colors[i % len(default_colors)])
        bg_color, border_color = color_map.get(color, color_map["blue"])

        formatted_datasets.append(
            {
                "label": dataset["label"],
                "data": dataset["data"],
                "backgroundColor": bg_color,
                "borderColor": border_color,
                "borderWidth": 2,
            }
        )

    return {
        "type": "scatter",
        "data": {"datasets": formatted_datasets},
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "title": {"display": True, "text": title, "font": {"size": 16}},
                "legend": {"position": "top"},
            },
            "scales": {
                "x": {"title": {"display": bool(x_label), "text": x_label}},
                "y": {"title": {"display": bool(y_label), "text": y_label}},
            },
        },
    }


def create_stacked_bar_chart(
    labels: list[str],
    datasets: list[dict[str, Any]],
    title: str,
    horizontal: bool = False,
) -> dict[str, Any]:
    """
    Create Chart.js stacked bar chart configuration.

    Args:
        labels: X-axis labels
        datasets: List of datasets with 'label', 'data', and optional 'color'
        title: Chart title
        horizontal: If True, create horizontal stacked bar chart

    Returns:
        Chart.js configuration dict
    """
    color_map = {
        "blue": ("rgba(59, 130, 246, 0.7)", "rgba(59, 130, 246, 1)"),
        "red": ("rgba(239, 68, 68, 0.7)", "rgba(239, 68, 68, 1)"),
        "green": ("rgba(16, 185, 129, 0.7)", "rgba(16, 185, 129, 1)"),
        "yellow": ("rgba(245, 158, 11, 0.7)", "rgba(245, 158, 11, 1)"),
        "purple": ("rgba(139, 92, 246, 0.7)", "rgba(139, 92, 246, 1)"),
    }

    default_colors = ["blue", "red", "green", "yellow", "purple"]
    formatted_datasets = []

    for i, dataset in enumerate(datasets):
        color = dataset.get("color", default_colors[i % len(default_colors)])
        bg_color, border_color = color_map.get(color, color_map["blue"])

        formatted_datasets.append(
            {
                "label": dataset["label"],
                "data": dataset["data"],
                "backgroundColor": bg_color,
                "borderColor": border_color,
                "borderWidth": 2,
            }
        )

    return {
        "type": "bar" if not horizontal else "horizontalBar",
        "data": {"labels": labels, "datasets": formatted_datasets},
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "title": {"display": True, "text": title, "font": {"size": 16}},
                "legend": {"position": "top"},
            },
            "scales": {
                "x": {"stacked": True},
                "y": {"stacked": True, "beginAtZero": True, "ticks": {"precision": 0}},
            },
        },
    }


def create_radar_chart(
    labels: list[str], datasets: list[dict[str, Any]], title: str
) -> dict[str, Any]:
    """
    Create Chart.js radar chart configuration.

    Args:
        labels: Axis labels
        datasets: List of datasets with 'label', 'data', and optional 'color'
        title: Chart title

    Returns:
        Chart.js configuration dict
    """
    color_map = {
        "blue": ("rgba(59, 130, 246, 0.3)", "rgba(59, 130, 246, 1)"),
        "red": ("rgba(239, 68, 68, 0.3)", "rgba(239, 68, 68, 1)"),
        "green": ("rgba(16, 185, 129, 0.3)", "rgba(16, 185, 129, 1)"),
        "yellow": ("rgba(245, 158, 11, 0.3)", "rgba(245, 158, 11, 1)"),
        "purple": ("rgba(139, 92, 246, 0.3)", "rgba(139, 92, 246, 1)"),
    }

    default_colors = ["blue", "red", "green", "yellow", "purple"]
    formatted_datasets = []

    for i, dataset in enumerate(datasets):
        color = dataset.get("color", default_colors[i % len(default_colors)])
        bg_color, border_color = color_map.get(color, color_map["blue"])

        formatted_datasets.append(
            {
                "label": dataset["label"],
                "data": dataset["data"],
                "backgroundColor": bg_color,
                "borderColor": border_color,
                "borderWidth": 2,
            }
        )

    return {
        "type": "radar",
        "data": {"labels": labels, "datasets": formatted_datasets},
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "title": {"display": True, "text": title, "font": {"size": 16}},
                "legend": {"position": "top"},
            },
            "scales": {
                "r": {
                    "beginAtZero": True,
                    "ticks": {"precision": 0},
                }
            },
        },
    }


def create_multi_axis_chart(
    labels: list[str],
    datasets: list[dict[str, Any]],
    title: str,
) -> dict[str, Any]:
    """
    Create Chart.js chart with multiple Y-axes.

    Args:
        labels: X-axis labels
        datasets: List of datasets with 'label', 'data', 'yAxisID', and optional 'color'
        title: Chart title

    Returns:
        Chart.js configuration dict
    """
    color_map = {
        "blue": ("rgba(59, 130, 246, 0.7)", "rgba(59, 130, 246, 1)"),
        "red": ("rgba(239, 68, 68, 0.7)", "rgba(239, 68, 68, 1)"),
        "green": ("rgba(16, 185, 129, 0.7)", "rgba(16, 185, 129, 1)"),
        "yellow": ("rgba(245, 158, 11, 0.7)", "rgba(245, 158, 11, 1)"),
        "purple": ("rgba(139, 92, 246, 0.7)", "rgba(139, 92, 246, 1)"),
    }

    default_colors = ["blue", "red", "green", "yellow", "purple"]
    formatted_datasets = []

    for i, dataset in enumerate(datasets):
        color = dataset.get("color", default_colors[i % len(default_colors)])
        bg_color, border_color = color_map.get(color, color_map["blue"])

        formatted_datasets.append(
            {
                "label": dataset["label"],
                "data": dataset["data"],
                "backgroundColor": bg_color,
                "borderColor": border_color,
                "borderWidth": 2,
                "yAxisID": dataset.get("yAxisID", "y"),
            }
        )

    return {
        "type": "line",
        "data": {"labels": labels, "datasets": formatted_datasets},
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "title": {"display": True, "text": title, "font": {"size": 16}},
                "legend": {"position": "top"},
            },
            "scales": {
                "y": {
                    "type": "linear",
                    "display": True,
                    "position": "left",
                    "beginAtZero": True,
                },
                "y1": {
                    "type": "linear",
                    "display": True,
                    "position": "right",
                    "beginAtZero": True,
                    "grid": {"drawOnChartArea": False},
                },
            },
        },
    }
