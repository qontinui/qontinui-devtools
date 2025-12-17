"""
Data models for documentation generation.

This module defines the core data structures used to represent documentation
elements extracted from Python source code.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DocItemType(Enum):
    """Types of documentation items."""

    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    PROPERTY = "property"
    ATTRIBUTE = "attribute"


class DocstringStyle(Enum):
    """Supported docstring formats."""

    GOOGLE = "google"
    NUMPY = "numpy"
    SPHINX = "sphinx"
    AUTO = "auto"


class OutputFormat(Enum):
    """Supported output formats for documentation."""

    HTML = "html"
    MARKDOWN = "markdown"
    JSON = "json"
    RST = "rst"


@dataclass
class Parameter:
    """Represents a function or method parameter.

    Attributes:
        name: The parameter name
        type_hint: The type annotation as a string
        default_value: The default value as a string (if any)
        description: Documentation description of the parameter
        optional: Whether the parameter is optional
    """

    name: str
    type_hint: str | None = None
    default_value: str | None = None
    description: str = ""
    optional: bool = False

    @property
    def is_optional(self) -> bool:
        """Check if parameter is optional."""
        return self.optional or self.default_value is not None


@dataclass
class Example:
    """Represents a code example from docstring.

    Attributes:
        code: The example code
        description: Description of what the example demonstrates
        output: Expected output (if provided)
    """

    code: str
    description: str = ""
    output: str | None = None


@dataclass
class DocItem:
    """Represents a documented item (module, class, function, etc.).

    Attributes:
        type: The type of documentation item
        name: The item's simple name
        qualified_name: The fully qualified name (e.g., module.Class.method)
        docstring: The raw docstring text
        file_path: Path to the source file
        line_number: Line number where the item is defined
        parameters: List of parameters (for functions/methods)
        return_type: Return type annotation as string
        return_description: Description of return value
        raises: List of exceptions raised with descriptions
        examples: List of code examples
        references: Cross-references to other items
        attributes: Class attributes (for classes)
        methods: Methods (for classes)
        decorators: List of decorators applied
        is_async: Whether function/method is async
        is_property: Whether method is a property
        is_classmethod: Whether method is a classmethod
        is_staticmethod: Whether method is a staticmethod
        parent: Parent item qualified name
        children: Child items qualified names
        source_code: The actual source code
        summary: Short summary (first line of docstring)
        description: Full description from docstring
        notes: Additional notes from docstring
        warnings: Warnings from docstring
        see_also: Related items from docstring
        metadata: Additional metadata
    """

    type: DocItemType
    name: str
    qualified_name: str
    docstring: str | None = None
    file_path: str = ""
    line_number: int = 0
    parameters: list[Parameter] = field(default_factory=list)
    return_type: str | None = None
    return_description: str | None = None
    raises: list[tuple[str, str]] = field(default_factory=list)
    examples: list[Example] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    attributes: list["DocItem"] = field(default_factory=list)
    methods: list["DocItem"] = field(default_factory=list)
    decorators: list[str] = field(default_factory=list)
    is_async: bool = False
    is_property: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False
    parent: str | None = None
    children: list[str] = field(default_factory=list)
    source_code: str | None = None
    summary: str = ""
    description: str = ""
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    see_also: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_public(self) -> bool:
        """Check if item is public (not private or protected)."""
        return not self.name.startswith("_")

    @property
    def is_private(self) -> bool:
        """Check if item is private (starts with __)."""
        return self.name.startswith("__") and not self.name.endswith("__")

    @property
    def is_protected(self) -> bool:
        """Check if item is protected (starts with _)."""
        return self.name.startswith("_") and not self.name.startswith("__")

    @property
    def is_dunder(self) -> bool:
        """Check if item is a dunder method."""
        return self.name.startswith("__") and self.name.endswith("__")

    @property
    def signature(self) -> str:
        """Generate method/function signature."""
        if self.type not in (DocItemType.FUNCTION, DocItemType.METHOD):
            return self.name

        parts: list[Any] = []
        if self.is_async:
            parts.append("async")
        parts.append("def")
        parts.append(self.name)

        # Build parameters
        params: list[Any] = []
        for param in self.parameters:
            param_str = param.name
            if param.type_hint:
                param_str += f": {param.type_hint}"
            if param.default_value:
                param_str += f" = {param.default_value}"
            params.append(param_str)

        parts.append(f"({', '.join(params)})")

        if self.return_type:
            parts.append(f"-> {self.return_type}")

        return " ".join(parts)


@dataclass
class DocumentationTree:
    """Represents the complete documentation tree.

    Attributes:
        root: Root documentation item (usually a module)
        modules: Mapping of qualified names to module items
        classes: Mapping of qualified names to class items
        functions: Mapping of qualified names to function items
        all_items: Mapping of all qualified names to items
        package_name: Name of the documented package
        version: Package version
        index: Search index data
    """

    root: DocItem
    modules: dict[str, DocItem] = field(default_factory=dict)
    classes: dict[str, DocItem] = field(default_factory=dict)
    functions: dict[str, DocItem] = field(default_factory=dict)
    all_items: dict[str, DocItem] = field(default_factory=dict)
    package_name: str = ""
    version: str = ""
    index: dict[str, list[str]] = field(default_factory=dict)

    def get_item(self, qualified_name: str) -> DocItem | None:
        """Get an item by its qualified name."""
        return self.all_items.get(qualified_name)

    def get_public_items(self, item_type: DocItemType | None = None) -> list[DocItem]:
        """Get all public items, optionally filtered by type."""
        items: list[Any] = []
        for item in self.all_items.values():
            if item.is_public:
                if item_type is None or item.type == item_type:
                    items.append(item)
        return sorted(items, key=lambda x: x.qualified_name)

    def get_children(self, qualified_name: str) -> list[DocItem]:
        """Get all children of an item."""
        item = self.get_item(qualified_name)
        if not item:
            return []

        children: list[Any] = []
        for child_name in item.children:
            child = self.get_item(child_name)
            if child:
                children.append(child)
        return children

    def search(self, query: str) -> list[DocItem]:
        """Search for items matching the query."""
        query_lower = query.lower()
        matches: list[Any] = []

        for item in self.all_items.values():
            # Search in name
            if query_lower in item.name.lower():
                matches.append((item, 10))
            # Search in qualified name
            elif query_lower in item.qualified_name.lower():
                matches.append((item, 8))
            # Search in docstring
            elif item.docstring and query_lower in item.docstring.lower():
                matches.append((item, 5))
            # Search in description
            elif query_lower in item.description.lower():
                matches.append((item, 3))

        # Sort by score (descending)
        matches.sort(key=lambda x: x[1], reverse=True)
        return [item for item, score in matches]
