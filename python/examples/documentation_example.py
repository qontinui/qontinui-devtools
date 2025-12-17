"""
from typing import Any

Example demonstrating the Documentation Generator.

This script shows how to use the documentation generator to create
beautiful API documentation from Python source code.
"""

import tempfile
from pathlib import Path

from qontinui_devtools.documentation import DocstringStyle, DocumentationGenerator, OutputFormat


def create_sample_code(path: Path) -> None:
    """Create sample code to document."""
    sample_code = '''"""Sample Library.

A library demonstrating documentation generation capabilities.
"""

class DataProcessor:
    """Process and transform data.

    This class provides methods for data processing operations including
    validation, transformation, and export.

    Attributes:
        data: The raw data to process
        validated: Whether data has been validated
    """

    def __init__(self, data: list[dict]) -> None:
        """Initialize the processor.

        Args:
            data: List of data dictionaries to process
        """
        self.data = data
        self.validated = False

    def validate(self) -> bool:
        """Validate the data.

        Returns:
            True if validation passed, False otherwise

        Raises:
            ValueError: If data is empty or malformed

        Examples:
            >>> processor = DataProcessor([{"id": 1, "value": 100}])
            >>> processor.validate()
            True
        """
        if not self.data:
            raise ValueError("Data cannot be empty")

        for item in self.data:
            if not isinstance(item, dict):
                raise ValueError("Each item must be a dictionary")
            if "id" not in item:
                raise ValueError("Each item must have an 'id' field")

        self.validated = True
        return True

    def transform(self, func) -> list:
        """Transform data using a function.

        Args:
            func: Function to apply to each data item

        Returns:
            List of transformed items

        Raises:
            RuntimeError: If data hasn't been validated

        Examples:
            >>> processor = DataProcessor([{"id": 1, "value": 100}])
            >>> processor.validate()
            >>> result = processor.transform(lambda x: x["value"] * 2)
            >>> result
            [200]
        """
        if not self.validated:
            raise RuntimeError("Data must be validated before transformation")

        return [func(item) for item in self.data]

    @property
    def count(self) -> int:
        """Get the number of data items."""
        return len(self.data)

    @staticmethod
    def merge(*datasets: list[dict]) -> list[dict]:
        """Merge multiple datasets.

        Args:
            *datasets: Variable number of datasets to merge

        Returns:
            Merged dataset
        """
        result: list[Any] = []
        for dataset in datasets:
            result.extend(dataset)
        return result


async def fetch_remote_data(url: str, timeout: int = 30) -> dict:
    """Fetch data from a remote URL.

    Args:
        url: URL to fetch data from
        timeout: Timeout in seconds (default: 30)

    Returns:
        The fetched data as a dictionary

    Raises:
        ConnectionError: If connection fails
        TimeoutError: If request times out

    Examples:
        >>> data = await fetch_remote_data("https://api.example.com/data")
        >>> print(data)
        {'status': 'ok', 'data': [...]}

    Note:
        This function is async and must be awaited.

    Warning:
        Large datasets may take a long time to fetch.
    """
    # Implementation would go here
    pass


def format_output(data: list, style: str = "json") -> str:
    """Format data for output.

    Args:
        data: Data to format
        style: Output style - "json", "csv", or "xml"

    Returns:
        Formatted string

    Raises:
        ValueError: If style is not recognized

    See Also:
        DataProcessor: For data processing before formatting
        fetch_remote_data: For fetching remote data
    """
    if style not in ["json", "csv", "xml"]:
        raise ValueError(f"Unknown style: {style}")

    # Implementation would go here
    return ""
'''

    path.write_text(sample_code, encoding="utf-8")


def main() -> None:
    """Run the documentation generator example."""
    print("=" * 70)
    print("Documentation Generator Example")
    print("=" * 70)
    print()

    # Create temporary directory for sample code
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create sample code
        print("Creating sample code...")
        sample_file = tmpdir_path / "sample_library.py"
        create_sample_code(sample_file)
        print(f"Created: {sample_file}")
        print()

        # Initialize generator
        print("Initializing documentation generator...")
        generator = DocumentationGenerator(docstring_style=DocstringStyle.AUTO)
        print("Generator ready!")
        print()

        # Generate documentation
        print("Extracting documentation from source code...")
        tree = generator.generate_docs(
            str(sample_file),
            output_format=OutputFormat.HTML,
            include_private=False,
            package_name="sample_library",
            version="1.0.0",
        )
        print(f"Extracted {len(tree.all_items)} documentation items")
        print()

        # Print statistics
        print("Documentation Statistics:")
        print(f"  - Modules: {len(tree.modules)}")
        print(f"  - Classes: {len(tree.classes)}")
        print(f"  - Functions: {len(tree.functions)}")
        print(f"  - Total items: {len(tree.all_items)}")
        print()

        # Show class details
        if tree.classes:
            print("Classes found:")
            for name, cls in tree.classes.items():
                print(f"  - {name}")
                print(f"    Summary: {cls.summary}")
                print(f"    Methods: {len(cls.methods)}")
                for method in cls.methods:
                    print(f"      - {method.name}()")
                print()

        # Show function details
        if tree.functions:
            print("Functions found:")
            for name, func in tree.functions.items():
                print(f"  - {name}")
                print(f"    Summary: {func.summary}")
                print(f"    Parameters: {len(func.parameters)}")
                print(f"    Async: {func.is_async}")
                print()

        # Generate HTML documentation
        print("Generating HTML documentation...")
        html_output = tmpdir_path / "docs_html"
        generator.write_docs(tree, html_output, OutputFormat.HTML)
        print(f"HTML documentation written to: {html_output}")
        print(f"  - index.html: {(html_output / 'index.html').stat().st_size} bytes")
        print()

        # Generate Markdown documentation
        print("Generating Markdown documentation...")
        md_output = tmpdir_path / "docs_md"
        generator.write_docs(tree, md_output, OutputFormat.MARKDOWN)
        print(f"Markdown documentation written to: {md_output}")
        for md_file in md_output.glob("*.md"):
            print(f"  - {md_file.name}: {md_file.stat().st_size} bytes")
        print()

        # Generate JSON documentation
        print("Generating JSON documentation...")
        json_output = tmpdir_path / "docs_json"
        generator.write_docs(tree, json_output, OutputFormat.JSON)
        print(f"JSON documentation written to: {json_output}")
        json_file = json_output / "documentation.json"
        print(f"  - documentation.json: {json_file.stat().st_size} bytes")
        print()

        # Demonstrate search
        print("Searching for 'transform'...")
        results = tree.search("transform")
        print(f"Found {len(results)} results:")
        for item in results:
            print(f"  - {item.qualified_name} ({item.type.value})")
        print()

        print("=" * 70)
        print("Example completed successfully!")
        print("=" * 70)
        print()
        print("Features demonstrated:")
        print("  - Automatic docstring extraction")
        print("  - Google-style docstring parsing")
        print("  - Type hint extraction")
        print("  - Multiple output formats (HTML, Markdown, JSON)")
        print("  - Search functionality")
        print("  - Class and method documentation")
        print("  - Async function detection")
        print("  - Property and decorator detection")
        print()


if __name__ == "__main__":
    main()
