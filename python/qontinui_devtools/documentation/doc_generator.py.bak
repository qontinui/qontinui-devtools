"""
Documentation generator for Python code.

This module provides automated documentation generation by extracting docstrings,
type hints, and code structure from Python source files.
"""

import ast
import json
import re
from pathlib import Path
from typing import Any

from .models import (
    DocItem,
    DocItemType,
    DocstringStyle,
    DocumentationTree,
    Example,
    OutputFormat,
    Parameter,
)


class DocstringParser:
    """Parse docstrings in various formats."""

    def __init__(self, style: DocstringStyle = DocstringStyle.AUTO) -> None:
        """Initialize parser.

        Args:
            style: Docstring style to parse
        """
        self.style = style

    def parse(self, docstring: str | None) -> dict[str, Any]:
        """Parse a docstring into structured data.

        Args:
            docstring: The docstring text to parse

        Returns:
            Dictionary containing parsed docstring components
        """
        if not docstring:
            return self._empty_result()

        # Detect style if AUTO
        style = self.style
        if style == DocstringStyle.AUTO:
            style = self._detect_style(docstring)

        if style == DocstringStyle.GOOGLE:
            return self._parse_google(docstring)
        elif style == DocstringStyle.NUMPY:
            return self._parse_numpy(docstring)
        else:
            return self._parse_basic(docstring)

    def _empty_result(self) -> dict[str, Any]:
        """Return empty parse result."""
        return {
            "summary": "",
            "description": "",
            "parameters": [],
            "returns": None,
            "raises": [],
            "examples": [],
            "notes": [],
            "warnings": [],
            "see_also": [],
        }

    def _detect_style(self, docstring: str) -> DocstringStyle:
        """Detect docstring style.

        Args:
            docstring: Docstring text

        Returns:
            Detected style
        """
        # Google style indicators
        if re.search(r"^\s*(Args|Returns|Raises|Examples?):\s*$", docstring, re.MULTILINE):
            return DocstringStyle.GOOGLE

        # NumPy style indicators (section header followed by dashes)
        if re.search(r"^\s*(Parameters|Returns|Raises)\s*\n\s*-{3,}\s*$", docstring, re.MULTILINE):
            return DocstringStyle.NUMPY

        return DocstringStyle.GOOGLE  # Default

    def _parse_basic(self, docstring: str) -> dict[str, Any]:
        """Parse basic docstring (just description)."""
        result = self._empty_result()
        lines = docstring.strip().split("\n")
        result["summary"] = lines[0].strip() if lines else ""
        result["description"] = docstring.strip()
        return result

    def _parse_google(self, docstring: str) -> dict[str, Any]:
        """Parse Google-style docstring.

        Args:
            docstring: Docstring text

        Returns:
            Parsed components
        """
        result = self._empty_result()
        lines = docstring.strip().split("\n")

        # Extract summary (first line)
        if lines:
            result["summary"] = lines[0].strip()

        # Parse sections
        current_section = None
        current_content: list[Any] = []
        description_lines: list[Any] = []
        in_description = True

        for _i, line in enumerate(lines[1:], 1):
            stripped = line.strip()

            # Check for section headers
            if stripped.endswith(":") and stripped[:-1] in [
                "Args",
                "Arguments",
                "Parameters",
                "Returns",
                "Return",
                "Yields",
                "Raises",
                "Examples",
                "Example",
                "Note",
                "Notes",
                "Warning",
                "Warnings",
                "See Also",
            ]:
                # Save previous section
                if current_section:
                    self._process_google_section(result, current_section, current_content)

                in_description = False
                current_section = stripped[:-1]
                current_content: list[Any] = []
            elif current_section:
                current_content.append(line)
            elif in_description and stripped:
                description_lines.append(line)

        # Process last section
        if current_section:
            self._process_google_section(result, current_section, current_content)

        # Set description
        if description_lines:
            result["description"] = "\n".join(description_lines).strip()
        else:
            result["description"] = result["summary"]

        return result

    def _process_google_section(
        self, result: dict[str, Any], section: str, content: list[str]
    ) -> None:
        """Process a Google-style section.

        Args:
            result: Result dictionary to update
            section: Section name
            content: Section content lines
        """
        section_lower = section.lower()

        if section_lower in ["args", "arguments", "parameters"]:
            result["parameters"] = self._parse_google_parameters(content)
        elif section_lower in ["returns", "return", "yields"]:
            result["returns"] = self._parse_google_returns(content)
        elif section_lower == "raises":
            result["raises"] = self._parse_google_raises(content)
        elif section_lower in ["examples", "example"]:
            result["examples"] = self._parse_examples(content)
        elif section_lower in ["note", "notes"]:
            result["notes"] = ["\n".join(content).strip()]
        elif section_lower in ["warning", "warnings"]:
            result["warnings"] = ["\n".join(content).strip()]
        elif section_lower == "see also":
            result["see_also"] = self._parse_see_also(content)

    def _parse_google_parameters(self, lines: list[str]) -> list[dict[str, Any]]:
        """Parse Google-style parameters."""
        parameters: list[Any] = []
        current_param = None

        # Find the base indentation level
        base_indent = None
        for line in lines:
            if line.strip():
                if base_indent is None:
                    base_indent = len(line) - len(line.lstrip())
                break
        if base_indent is None:
            base_indent = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check if this is a parameter definition
            indent = len(line) - len(line.lstrip())
            relative_indent = indent - base_indent
            match = re.match(r"^(\w+)\s*(\([^)]+\))?\s*:\s*(.*)$", stripped)

            if match and relative_indent <= 0:  # Main parameter line
                if current_param:
                    parameters.append(current_param)

                name = match.group(1)
                type_hint = match.group(2)
                desc = match.group(3)

                if type_hint:
                    type_hint = type_hint.strip("()")

                current_param = {
                    "name": name,
                    "type_hint": type_hint,
                    "description": desc,
                }
            elif current_param and relative_indent > 0:
                # Continuation of description
                if current_param["description"]:
                    current_param["description"] += " "
                current_param["description"] += stripped

        if current_param:
            parameters.append(current_param)

        return parameters

    def _parse_google_returns(self, lines: list[str]) -> dict[str, Any] | None:
        """Parse Google-style returns section."""
        content = "\n".join(lines).strip()
        if not content:
            return None

        # Try to extract type and description
        match = re.match(r"^([^:]+):\s*(.*)$", content, re.DOTALL)
        if match:
            return {"type": match.group(1).strip(), "description": match.group(2).strip()}

        return {"type": None, "description": content}

    def _parse_google_raises(self, lines: list[str]) -> list[tuple[str, str]]:
        """Parse Google-style raises section."""
        raises: list[Any] = []
        current_exception = None

        # Find the base indentation level
        base_indent = None
        for line in lines:
            if line.strip():
                if base_indent is None:
                    base_indent = len(line) - len(line.lstrip())
                break
        if base_indent is None:
            base_indent = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check if this is an exception definition
            indent = len(line) - len(line.lstrip())
            relative_indent = indent - base_indent
            match = re.match(r"^(\w+)\s*:\s*(.*)$", stripped)

            if match and relative_indent <= 0:  # Main exception line
                if current_exception:
                    raises.append(current_exception)

                current_exception = (match.group(1), match.group(2))
            elif current_exception and relative_indent > 0:
                # Continuation
                desc = current_exception[1] + " " + stripped
                current_exception = (current_exception[0], desc)

        if current_exception:
            raises.append(current_exception)

        return raises

    def _parse_numpy(self, docstring: str) -> dict[str, Any]:
        """Parse NumPy-style docstring.

        Args:
            docstring: Docstring text

        Returns:
            Parsed components
        """
        result = self._empty_result()
        lines = docstring.strip().split("\n")

        # Extract summary
        if lines:
            result["summary"] = lines[0].strip()

        # Find sections
        sections: dict[Any, Any] = {}
        current_section = None
        current_content: list[Any] = []
        description_lines: list[Any] = []
        in_description = True
        i = 1

        while i < len(lines):
            line = lines[i]

            # Check for section header (followed by dashes on next line)
            if i + 1 < len(lines) and re.match(r"^-{3,}$", lines[i + 1].strip()):
                if current_section:
                    sections[current_section] = current_content

                in_description = False
                current_section = line.strip()
                current_content: list[Any] = []
                i += 2  # Skip header and dashes
                continue
            elif current_section:
                if not re.match(r"^-{3,}$", line.strip()):
                    current_content.append(line)
            elif in_description and line.strip():
                description_lines.append(line)

            i += 1

        # Save last section
        if current_section:
            sections[current_section] = current_content

        # Process sections
        for section_name, content in sections.items():
            section_lower = section_name.lower()

            if section_lower == "parameters":
                result["parameters"] = self._parse_numpy_parameters(content)
            elif section_lower == "returns":
                result["returns"] = self._parse_numpy_returns(content)
            elif section_lower == "raises":
                result["raises"] = self._parse_numpy_raises(content)
            elif section_lower == "examples":
                result["examples"] = self._parse_examples(content)
            elif section_lower == "notes":
                result["notes"] = ["\n".join(content).strip()]
            elif section_lower == "warnings":
                result["warnings"] = ["\n".join(content).strip()]
            elif section_lower == "see also":
                result["see_also"] = self._parse_see_also(content)

        # Set description
        if description_lines:
            result["description"] = "\n".join(description_lines).strip()
        else:
            result["description"] = result["summary"]

        return result

    def _parse_numpy_parameters(self, lines: list[str]) -> list[dict[str, Any]]:
        """Parse NumPy-style parameters."""
        parameters: list[Any] = []
        current_param = None

        # Find the base indentation level
        base_indent = None
        for line in lines:
            if line.strip():
                if base_indent is None:
                    base_indent = len(line) - len(line.lstrip())
                break
        if base_indent is None:
            base_indent = 0

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check for parameter definition (name : type)
            indent = len(line) - len(line.lstrip())
            relative_indent = indent - base_indent
            match = re.match(r"^(\w+)\s*:\s*(.*)$", stripped)

            if match and relative_indent <= 0:  # Parameter name line
                if current_param:
                    parameters.append(current_param)

                current_param = {
                    "name": match.group(1),
                    "type_hint": match.group(2) if match.group(2) else None,
                    "description": "",
                }
            elif current_param and relative_indent > 0:
                # Description continuation
                if current_param["description"]:
                    current_param["description"] += " "
                current_param["description"] += stripped

        if current_param:
            parameters.append(current_param)

        return parameters

    def _parse_numpy_returns(self, lines: list[str]) -> dict[str, Any] | None:
        """Parse NumPy-style returns section."""
        if not lines:
            return None

        # Find the base indentation level
        base_indent = None
        for line in lines:
            if line.strip():
                if base_indent is None:
                    base_indent = len(line) - len(line.lstrip())
                break
        if base_indent is None:
            base_indent = 0

        # Try to extract type and description
        # In NumPy style, the type is on the first line at base indent
        # and description is indented more
        type_str = None
        description_parts: list[Any] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            indent = len(line) - len(line.lstrip())
            relative_indent = indent - base_indent

            if relative_indent <= 0 and type_str is None:
                # This is the type line
                type_str = stripped
            elif relative_indent > 0:
                # This is description
                description_parts.append(stripped)

        return {
            "type": type_str,
            "description": " ".join(description_parts) if description_parts else "",
        }

    def _parse_numpy_raises(self, lines: list[str]) -> list[tuple[str, str]]:
        """Parse NumPy-style raises section."""
        raises: list[Any] = []
        current_exception = None

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Check for exception definition
            if not line.startswith(" " * 4):
                if current_exception:
                    raises.append(current_exception)

                current_exception = (stripped, "")
            elif current_exception:
                # Description
                if current_exception[1]:
                    current_exception = (
                        current_exception[0],
                        current_exception[1] + " " + stripped,
                    )
                else:
                    current_exception = (current_exception[0], stripped)

        if current_exception:
            raises.append(current_exception)

        return raises

    def _parse_examples(self, lines: list[str]) -> list[dict[str, Any]]:
        """Parse examples from docstring."""
        examples: list[Any] = []
        content = "\n".join(lines).strip()

        if not content:
            return examples

        # Split by >>> or code blocks
        code_blocks = re.split(r"(?:^|\n)(?:>>>|\.\.\.)", content)

        for block in code_blocks:
            block = block.strip()
            if block:
                examples.append({"code": block, "description": "", "output": None})

        return examples

    def _parse_see_also(self, lines: list[str]) -> list[str]:
        """Parse see also references."""
        refs: list[Any] = []
        for line in lines:
            stripped = line.strip()
            if stripped:
                # Extract reference name
                match = re.match(r"^(\w+)", stripped)
                if match:
                    refs.append(match.group(1))
        return refs


class ASTDocExtractor(ast.NodeVisitor):
    """Extract documentation from Python AST."""

    def __init__(self, file_path: str, source_code: str) -> None:
        """Initialize extractor.

        Args:
            file_path: Path to source file
            source_code: Source code content
        """
        self.file_path = file_path
        self.source_code = source_code
        self.source_lines = source_code.split("\n")
        self.items: list[DocItem] = []
        self.current_class: str | None = None
        self.parser = DocstringParser()

    def extract(self) -> list[DocItem]:
        """Extract all documentation items.

        Returns:
            List of documentation items
        """
        try:
            tree = ast.parse(self.source_code, filename=self.file_path)
            self.visit(tree)
        except SyntaxError as e:
            print(f"Syntax error in {self.file_path}: {e}")

        return self.items

    def visit_Module(self, node: ast.Module) -> None:
        """Visit module node."""
        docstring = ast.get_docstring(node)
        module_name = Path(self.file_path).stem

        # Parse docstring
        parsed = self.parser.parse(docstring)

        item = DocItem(
            type=DocItemType.MODULE,
            name=module_name,
            qualified_name=module_name,
            docstring=docstring,
            file_path=self.file_path,
            line_number=1,
            summary=parsed["summary"],
            description=parsed["description"],
            notes=parsed["notes"],
            warnings=parsed["warnings"],
            see_also=parsed["see_also"],
        )

        self.items.append(item)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definition."""
        docstring = ast.get_docstring(node)
        parent = self.current_class
        qualified_name = f"{parent}.{node.name}" if parent else node.name

        # Parse docstring
        parsed = self.parser.parse(docstring)

        # Extract decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]

        item = DocItem(
            type=DocItemType.CLASS,
            name=node.name,
            qualified_name=qualified_name,
            docstring=docstring,
            file_path=self.file_path,
            line_number=node.lineno,
            decorators=decorators,
            parent=parent,
            summary=parsed["summary"],
            description=parsed["description"],
            notes=parsed["notes"],
            warnings=parsed["warnings"],
            see_also=parsed["see_also"],
        )

        self.items.append(item)

        # Visit class body
        old_class = self.current_class
        self.current_class = qualified_name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition."""
        self._visit_function(node, is_async=False)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition."""
        self._visit_function(node, is_async=True)

    def _visit_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef, is_async: bool) -> None:
        """Visit function or method."""
        docstring = ast.get_docstring(node)

        # Determine if this is a method
        is_method = self.current_class is not None
        item_type = DocItemType.METHOD if is_method else DocItemType.FUNCTION

        qualified_name = f"{self.current_class}.{node.name}" if is_method else node.name

        # Parse docstring
        parsed = self.parser.parse(docstring)

        # Extract parameters
        parameters = self._extract_parameters(node, parsed["parameters"])

        # Extract return type
        return_type = self._get_type_annotation(node.returns)

        # Extract decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]

        # Check decorator types
        is_property = "property" in decorators
        is_classmethod = "classmethod" in decorators
        is_staticmethod = "staticmethod" in decorators

        # Extract examples
        examples: list[Any] = []
        for ex in parsed["examples"]:
            examples.append(Example(code=ex["code"], description=ex.get("description", "")))

        # Get return description
        return_description = None
        if parsed["returns"]:
            return_description = parsed["returns"].get("description")
            if not return_type and parsed["returns"].get("type"):
                return_type = parsed["returns"]["type"]

        item = DocItem(
            type=DocItemType.PROPERTY if is_property else item_type,
            name=node.name,
            qualified_name=qualified_name,
            docstring=docstring,
            file_path=self.file_path,
            line_number=node.lineno,
            parameters=parameters,
            return_type=return_type,
            return_description=return_description,
            raises=parsed["raises"],
            examples=examples,
            decorators=decorators,
            is_async=is_async,
            is_property=is_property,
            is_classmethod=is_classmethod,
            is_staticmethod=is_staticmethod,
            parent=self.current_class,
            summary=parsed["summary"],
            description=parsed["description"],
            notes=parsed["notes"],
            warnings=parsed["warnings"],
            see_also=parsed["see_also"],
        )

        self.items.append(item)

    def _extract_parameters(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef, parsed_params: list[dict]
    ) -> list[Parameter]:
        """Extract parameters from function."""
        parameters: list[Any] = []
        args = node.args

        # Create mapping of parsed parameters
        param_docs = {p["name"]: p for p in parsed_params}

        # Regular arguments
        for i, arg in enumerate(args.args):
            # Get default value if exists
            default_value = None
            defaults_offset = len(args.args) - len(args.defaults)
            if i >= defaults_offset:
                default_idx = i - defaults_offset
                default_value = self._get_default_value(args.defaults[default_idx])

            # Get type annotation
            type_hint = self._get_type_annotation(arg.annotation)

            # Get description from parsed docstring
            description = ""
            if arg.arg in param_docs:
                description = param_docs[arg.arg].get("description", "")
                if not type_hint and param_docs[arg.arg].get("type_hint"):
                    type_hint = param_docs[arg.arg]["type_hint"]

            parameters.append(
                Parameter(
                    name=arg.arg,
                    type_hint=type_hint,
                    default_value=default_value,
                    description=description,
                    optional=default_value is not None,
                )
            )

        # *args
        if args.vararg:
            type_hint = self._get_type_annotation(args.vararg.annotation)
            description = param_docs.get(args.vararg.arg, {}).get("description", "")

            parameters.append(
                Parameter(
                    name=f"*{args.vararg.arg}",
                    type_hint=type_hint,
                    description=description,
                )
            )

        # **kwargs
        if args.kwarg:
            type_hint = self._get_type_annotation(args.kwarg.annotation)
            description = param_docs.get(args.kwarg.arg, {}).get("description", "")

            parameters.append(
                Parameter(
                    name=f"**{args.kwarg.arg}",
                    type_hint=type_hint,
                    description=description,
                )
            )

        return parameters

    def _get_type_annotation(self, annotation: ast.expr | None) -> str | None:
        """Get type annotation as string."""
        if annotation is None:
            return None

        try:
            return ast.unparse(annotation)
        except Exception:
            return str(annotation)

    def _get_default_value(self, node: ast.expr) -> str:
        """Get default value as string."""
        try:
            return ast.unparse(node)
        except Exception:
            return str(node)

    def _get_decorator_name(self, node: ast.expr) -> str:
        """Get decorator name."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return str(node)


class DocumentationGenerator:
    """Generate documentation from Python source code."""

    def __init__(self, docstring_style: DocstringStyle = DocstringStyle.AUTO) -> None:
        """Initialize generator.

        Args:
            docstring_style: Style of docstrings to parse
        """
        self.docstring_style = docstring_style
        self.parser = DocstringParser(docstring_style)

    def generate_docs(
        self,
        source_path: str | Path,
        output_format: OutputFormat = OutputFormat.HTML,
        include_private: bool = False,
        package_name: str = "",
        version: str = "",
    ) -> DocumentationTree:
        """Generate documentation for Python code.

        Args:
            source_path: Path to source code (file or directory)
            output_format: Output format for documentation
            include_private: Include private members
            package_name: Name of package being documented
            version: Version of package

        Returns:
            Documentation tree
        """
        source_path = Path(source_path)

        # Collect all Python files
        python_files: list[Any] = []
        if source_path.is_file():
            python_files = [source_path]
        else:
            python_files = list(source_path.rglob("*.py"))

        # Extract documentation from each file
        all_items: list[Any] = []
        for file_path in python_files:
            try:
                source_code = file_path.read_text(encoding="utf-8")
                extractor = ASTDocExtractor(str(file_path), source_code)
                items = extractor.extract()
                all_items.extend(items)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        # Build documentation tree
        tree = self._build_tree(all_items, include_private, package_name, version)

        return tree

    def _build_tree(
        self,
        items: list[DocItem],
        include_private: bool,
        package_name: str,
        version: str,
    ) -> DocumentationTree:
        """Build documentation tree from items."""
        # Filter private members if requested
        if not include_private:
            items = [item for item in items if item.is_public or item.is_dunder]

        # Organize items
        modules: dict[Any, Any] = {}
        classes: dict[Any, Any] = {}
        functions: dict[Any, Any] = {}
        all_items: dict[Any, Any] = {}

        root = None

        for item in items:
            all_items[item.qualified_name] = item

            if item.type == DocItemType.MODULE:
                modules[item.qualified_name] = item
                if root is None:
                    root = item
            elif item.type == DocItemType.CLASS:
                classes[item.qualified_name] = item
            elif item.type == DocItemType.FUNCTION:
                functions[item.qualified_name] = item

        # Build parent-child relationships
        for item in items:
            if item.parent and item.parent in all_items:
                parent = all_items[item.parent]
                parent.children.append(item.qualified_name)

                # Add to parent's methods or attributes
                if item.type in (DocItemType.METHOD, DocItemType.FUNCTION, DocItemType.PROPERTY):
                    parent.methods.append(item)
                else:
                    parent.attributes.append(item)

        # Create root if none exists
        if root is None:
            root = DocItem(
                type=DocItemType.MODULE,
                name=package_name or "Documentation",
                qualified_name=package_name or "root",
            )

        tree = DocumentationTree(
            root=root,
            modules=modules,
            classes=classes,
            functions=functions,
            all_items=all_items,
            package_name=package_name,
            version=version,
        )

        # Build search index
        tree.index = self._build_search_index(tree)

        return tree

    def _build_search_index(self, tree: DocumentationTree) -> dict[str, list[str]]:
        """Build search index for documentation."""
        index: dict[Any, Any] = {}

        for qualified_name, item in tree.all_items.items():
            # Index by name
            name_lower = item.name.lower()
            if name_lower not in index:
                index[name_lower] = []
            index[name_lower].append(qualified_name)

            # Index by words in docstring
            if item.docstring:
                words = re.findall(r"\w+", item.docstring.lower())
                for word in words:
                    if len(word) > 3:  # Skip short words
                        if word not in index:
                            index[word] = []
                        if qualified_name not in index[word]:
                            index[word].append(qualified_name)

        return index

    def write_docs(
        self,
        tree: DocumentationTree,
        output_path: str | Path,
        output_format: OutputFormat = OutputFormat.HTML,
    ) -> None:
        """Write documentation to files.

        Args:
            tree: Documentation tree
            output_path: Output directory
            output_format: Output format
        """
        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        if output_format == OutputFormat.HTML:
            self._write_html(tree, output_path)
        elif output_format == OutputFormat.MARKDOWN:
            self._write_markdown(tree, output_path)
        elif output_format == OutputFormat.JSON:
            self._write_json(tree, output_path)

    def _write_html(self, tree: DocumentationTree, output_path: Path) -> None:
        """Write HTML documentation."""
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape

            # Setup Jinja2
            template_dir = Path(__file__).parent / "templates"
            env = Environment(
                loader=FileSystemLoader(str(template_dir)),
                autoescape=select_autoescape(["html", "xml"]),
            )

            # Load template
            try:
                template = env.get_template("api_reference.html.jinja2")
            except Exception:
                # Use basic template if file doesn't exist
                template = env.from_string(self._get_basic_html_template())

            # Render
            html = template.render(tree=tree)

            # Write
            (output_path / "index.html").write_text(html, encoding="utf-8")

        except ImportError:
            # Fallback without Jinja2
            html = self._generate_basic_html(tree)
            (output_path / "index.html").write_text(html, encoding="utf-8")

    def _write_markdown(self, tree: DocumentationTree, output_path: Path) -> None:
        """Write Markdown documentation."""
        # Write index
        index_md = self._generate_markdown_index(tree)
        (output_path / "index.md").write_text(index_md, encoding="utf-8")

        # Write module pages
        for qualified_name, module in tree.modules.items():
            md = self._generate_module_markdown(module, tree)
            filename = qualified_name.replace(".", "_") + ".md"
            (output_path / filename).write_text(md, encoding="utf-8")

    def _write_json(self, tree: DocumentationTree, output_path: Path) -> None:
        """Write JSON documentation."""
        data = {
            "package_name": tree.package_name,
            "version": tree.version,
            "modules": {},
            "classes": {},
            "functions": {},
        }

        for qualified_name, item in tree.all_items.items():
            item_data = {
                "type": item.type.value,
                "name": item.name,
                "qualified_name": item.qualified_name,
                "docstring": item.docstring,
                "file_path": item.file_path,
                "line_number": item.line_number,
                "summary": item.summary,
                "description": item.description,
            }

            if item.type == DocItemType.MODULE:
                data["modules"][qualified_name] = item_data
            elif item.type == DocItemType.CLASS:
                data["classes"][qualified_name] = item_data
            elif item.type == DocItemType.FUNCTION:
                data["functions"][qualified_name] = item_data

        (output_path / "documentation.json").write_text(
            json.dumps(data, indent=2), encoding="utf-8"
        )

    def _generate_markdown_index(self, tree: DocumentationTree) -> str:
        """Generate markdown index page."""
        lines: list[Any] = []
        lines.append(f"# {tree.package_name or 'Documentation'}")

        if tree.version:
            lines.append(f"\nVersion: {tree.version}")

        lines.append("\n## Modules\n")
        for qualified_name, module in sorted(tree.modules.items()):
            link = qualified_name.replace(".", "_") + ".md"
            lines.append(f"- [{qualified_name}]({link})")
            if module.summary:
                lines.append(f"  - {module.summary}")

        return "\n".join(lines)

    def _generate_module_markdown(self, module: DocItem, tree: DocumentationTree) -> str:
        """Generate markdown for a module."""
        lines: list[Any] = []
        lines.append(f"# {module.name}\n")

        if module.summary:
            lines.append(f"{module.summary}\n")

        if module.description and module.description != module.summary:
            lines.append(f"{module.description}\n")

        # Classes
        classes = [
            item
            for item in tree.all_items.values()
            if item.parent == module.qualified_name and item.type == DocItemType.CLASS
        ]

        if classes:
            lines.append("## Classes\n")
            for cls in sorted(classes, key=lambda x: x.name):
                lines.append(f"### {cls.name}\n")
                if cls.summary:
                    lines.append(f"{cls.summary}\n")

                # Methods
                methods = [m for m in cls.methods if m.is_public]
                if methods:
                    lines.append("#### Methods\n")
                    for method in sorted(methods, key=lambda x: x.name):
                        lines.append(f"##### `{method.signature}`\n")
                        if method.summary:
                            lines.append(f"{method.summary}\n")

        # Functions
        functions = [
            item
            for item in tree.all_items.values()
            if item.parent == module.qualified_name and item.type == DocItemType.FUNCTION
        ]

        if functions:
            lines.append("## Functions\n")
            for func in sorted(functions, key=lambda x: x.name):
                lines.append(f"### `{func.signature}`\n")
                if func.summary:
                    lines.append(f"{func.summary}\n")

        return "\n".join(lines)

    def _generate_basic_html(self, tree: DocumentationTree) -> str:
        """Generate basic HTML without templates."""
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"<title>{tree.package_name or 'Documentation'}</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }",
            "h1 { color: #333; }",
            "h2 { color: #666; border-bottom: 2px solid #ddd; }",
            ".item { margin: 20px 0; padding: 15px; background: #f9f9f9; }",
            ".signature { font-family: monospace; background: #e8e8e8; padding: 5px; }",
            "</style>",
            "</head>",
            "<body>",
            f"<h1>{tree.package_name or 'Documentation'}</h1>",
        ]

        if tree.version:
            html.append(f"<p>Version: {tree.version}</p>")

        # Modules
        if tree.modules:
            html.append("<h2>Modules</h2>")
            for _qualified_name, module in sorted(tree.modules.items()):
                html.append('<div class="item">')
                html.append(f"<h3>{module.name}</h3>")
                if module.summary:
                    html.append(f"<p>{module.summary}</p>")
                html.append("</div>")

        # Classes
        if tree.classes:
            html.append("<h2>Classes</h2>")
            for _qualified_name, cls in sorted(tree.classes.items()):
                html.append('<div class="item">')
                html.append(f"<h3>{cls.name}</h3>")
                if cls.summary:
                    html.append(f"<p>{cls.summary}</p>")
                html.append("</div>")

        html.append("</body>")
        html.append("</html>")

        return "\n".join(html)

    def _get_basic_html_template(self) -> str:
        """Get basic HTML template string."""
        return """<!DOCTYPE html>
<html>
<head>
    <title>{{ tree.package_name or 'Documentation' }}</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }
        h1 { color: #333; }
        h2 { color: #666; border-bottom: 2px solid #ddd; }
        .item { margin: 20px 0; padding: 15px; background: #f9f9f9; }
    </style>
</head>
<body>
    <h1>{{ tree.package_name or 'Documentation' }}</h1>
    {% if tree.version %}
    <p>Version: {{ tree.version }}</p>
    {% endif %}
</body>
</html>"""
