# HTML Report Generator Examples

This directory contains examples demonstrating how to use the qontinui-devtools HTML Report Generator.

## Examples

### 1. `generate_report.py` - Automated Report Generation

Runs all analysis tools and generates a comprehensive HTML report automatically.

**Usage:**
```bash
python generate_report.py <project_path> [output_report.html]
```

**Example:**
```bash
python generate_report.py ../qontinui/src qontinui_analysis.html
```

**Features:**
- Automatically runs all analyses (imports, architecture, quality, concurrency)
- Aggregates results into a single report
- Generates interactive HTML with charts
- Provides summary metrics in console

### 2. `custom_report.py` - Custom Report Creation

Demonstrates how to manually create report sections and customize content.

**Usage:**
```bash
python custom_report.py
```

**Features:**
- Shows how to create custom ReportSection objects
- Demonstrates manual chart generation
- Custom content with HTML formatting
- Full control over report structure

## Using the CLI

The easiest way to generate reports is using the CLI:

```bash
# Run comprehensive analysis with HTML report
qontinui-devtools analyze ./src --report analysis.html

# Verbose mode
qontinui-devtools analyze ./src --report analysis.html --verbose

# JSON output
qontinui-devtools analyze ./src --format json --output results.json
```

## Report Features

Generated HTML reports include:

1. **Executive Summary**
   - Overall quality status (pass/fail)
   - Key metrics cards
   - Quality score (0-100)
   - Critical issues count

2. **Import Analysis**
   - Circular dependencies detection
   - Import graph visualization
   - Refactoring suggestions

3. **Architecture Quality**
   - God class detection
   - SRP violations
   - Coupling metrics
   - Extraction suggestions

4. **Code Quality**
   - Lines of code
   - Complexity metrics
   - Documentation coverage
   - Common issues

5. **Concurrency Analysis**
   - Race condition detection
   - Shared state analysis
   - Synchronization recommendations

6. **Recommendations**
   - Prioritized action items
   - Estimated effort
   - Long-term improvements

7. **Interactive Features**
   - Smooth navigation
   - Responsive design (mobile-friendly)
   - Interactive Chart.js visualizations
   - Collapsible sections
   - Back-to-top button

## Customization

### Creating Custom Sections

```python
from qontinui_devtools.reporting import ReportSection

section = ReportSection(
    id="my_section",
    title="My Custom Section",
    content="<p>Custom HTML content</p>",
    severity="warning",  # success, warning, error, info
    metrics={"my_metric": 42},
)
```

### Adding Charts

```python
from qontinui_devtools.reporting import create_bar_chart, create_pie_chart

# Bar chart
bar_chart = create_bar_chart(
    labels=["A", "B", "C"],
    data=[10, 20, 30],
    title="My Chart",
    color="blue"
)

# Pie chart
pie_chart = create_pie_chart(
    labels=["Success", "Warning", "Error"],
    data=[85, 12, 3],
    title="Distribution"
)

# Add to section
section.chart_data = bar_chart
```

### Styling Content

Use HTML in the `content` field:

```python
content = """
<h3>Section Title</h3>
<p>Description text</p>
<ul>
    <li>Item 1</li>
    <li>Item 2</li>
</ul>
<code>inline_code()</code>
"""
```

## Tips

1. **Large Projects**: Use verbose mode to track progress
2. **CI/CD Integration**: Generate JSON reports for automated processing
3. **Sharing Reports**: HTML reports are standalone files with embedded CSS/JS
4. **Performance**: Analysis typically takes <30 seconds for medium projects
5. **Trends**: Save reports over time to track quality improvements

## Dependencies

The HTML report generator requires:
- `jinja2` - Template engine
- `click` - CLI framework
- `rich` - Console output formatting

Chart.js and Tailwind CSS are loaded from CDN (no installation needed).

## Troubleshooting

**Import errors:**
```bash
pip install -e python/
```

**Missing templates:**
Templates are embedded in the generator as fallback if files aren't found.

**Analysis fails:**
Check that the project path exists and contains Python files.

## Further Reading

- [qontinui-devtools Documentation](../README.md)
- [Import Analysis](../python/qontinui_devtools/import_analysis/)
- [Architecture Analysis](../python/qontinui_devtools/architecture/)
- [Concurrency Testing](../python/qontinui_devtools/concurrency/)
