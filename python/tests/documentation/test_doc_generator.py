"""
from typing import Any

from typing import Any

Tests for documentation generator.
"""

import json
import tempfile
from pathlib import Path

from qontinui_devtools.documentation import (ASTDocExtractor, DocItem,
                                             DocItemType, DocstringParser,
                                             DocstringStyle,
                                             DocumentationGenerator,
                                             DocumentationTree, Example,
                                             OutputFormat, Parameter)


class TestParameter:
    """Test Parameter model."""

    def test_parameter_creation(self) -> None:
        """Test creating a parameter."""
        param = Parameter(
            name="value",
            type_hint="int",
            default_value="10",
            description="A number",
        )

        assert param.name == "value"
        assert param.type_hint == "int"
        assert param.default_value == "10"
        assert param.description == "A number"

    def test_parameter_is_optional(self) -> None:
        """Test parameter optional detection."""
        # Has default value
        param1 = Parameter(name="x", default_value="10")
        assert param1.is_optional

        # Marked as optional
        param2 = Parameter(name="y", optional=True)
        assert param2.is_optional

        # Not optional
        param3 = Parameter(name="z")
        assert not param3.is_optional


class TestExample:
    """Test Example model."""

    def test_example_creation(self) -> None:
        """Test creating an example."""
        example = Example(
            code="print('hello')",
            description="Print hello",
            output="hello",
        )

        assert example.code == "print('hello')"
        assert example.description == "Print hello"
        assert example.output == "hello"


class TestDocItem:
    """Test DocItem model."""

    def test_doc_item_creation(self) -> None:
        """Test creating a doc item."""
        item = DocItem(
            type=DocItemType.FUNCTION,
            name="foo",
            qualified_name="module.foo",
            docstring="A function",
            file_path="/path/to/file.py",
            line_number=10,
        )

        assert item.type == DocItemType.FUNCTION
        assert item.name == "foo"
        assert item.qualified_name == "module.foo"
        assert item.docstring == "A function"

    def test_doc_item_visibility(self) -> None:
        """Test visibility checks."""
        # Public
        public_item = DocItem(
            type=DocItemType.FUNCTION,
            name="public_func",
            qualified_name="module.public_func",
        )
        assert public_item.is_public
        assert not public_item.is_private
        assert not public_item.is_protected

        # Protected
        protected_item = DocItem(
            type=DocItemType.FUNCTION,
            name="_protected",
            qualified_name="module._protected",
        )
        assert not protected_item.is_public
        assert not protected_item.is_private
        assert protected_item.is_protected

        # Private
        private_item = DocItem(
            type=DocItemType.FUNCTION,
            name="__private",
            qualified_name="module.__private",
        )
        assert not private_item.is_public
        assert private_item.is_private
        assert not private_item.is_protected

        # Dunder
        dunder_item = DocItem(
            type=DocItemType.METHOD,
            name="__init__",
            qualified_name="Class.__init__",
        )
        assert not dunder_item.is_public
        assert not dunder_item.is_private
        assert not dunder_item.is_protected
        assert dunder_item.is_dunder

    def test_function_signature(self) -> None:
        """Test function signature generation."""
        item = DocItem(
            type=DocItemType.FUNCTION,
            name="calculate",
            qualified_name="module.calculate",
            parameters=[
                Parameter(name="x", type_hint="int"),
                Parameter(name="y", type_hint="int", default_value="10"),
            ],
            return_type="int",
        )

        sig = item.signature
        assert "def calculate" in sig
        assert "x: int" in sig
        assert "y: int = 10" in sig
        assert "-> int" in sig

    def test_async_function_signature(self) -> None:
        """Test async function signature."""
        item = DocItem(
            type=DocItemType.FUNCTION,
            name="fetch_data",
            qualified_name="module.fetch_data",
            is_async=True,
            return_type="dict",
        )

        sig = item.signature
        assert "async def fetch_data" in sig
        assert "-> dict" in sig


class TestDocumentationTree:
    """Test DocumentationTree model."""

    def test_tree_creation(self) -> None:
        """Test creating a documentation tree."""
        root = DocItem(
            type=DocItemType.MODULE,
            name="mymodule",
            qualified_name="mymodule",
        )

        tree = DocumentationTree(
            root=root,
            package_name="mypackage",
            version="1.0.0",
        )

        assert tree.root == root
        assert tree.package_name == "mypackage"
        assert tree.version == "1.0.0"

    def test_get_item(self) -> None:
        """Test getting an item by qualified name."""
        root = DocItem(
            type=DocItemType.MODULE,
            name="mymodule",
            qualified_name="mymodule",
        )

        item1 = DocItem(
            type=DocItemType.CLASS,
            name="MyClass",
            qualified_name="mymodule.MyClass",
        )

        tree = DocumentationTree(root=root)
        tree.all_items = {
            "mymodule": root,
            "mymodule.MyClass": item1,
        }

        assert tree.get_item("mymodule.MyClass") == item1
        assert tree.get_item("nonexistent") is None

    def test_get_public_items(self) -> None:
        """Test filtering public items."""
        root = DocItem(
            type=DocItemType.MODULE,
            name="mymodule",
            qualified_name="mymodule",
        )

        public_func = DocItem(
            type=DocItemType.FUNCTION,
            name="public_func",
            qualified_name="mymodule.public_func",
        )

        private_func = DocItem(
            type=DocItemType.FUNCTION,
            name="_private_func",
            qualified_name="mymodule._private_func",
        )

        tree = DocumentationTree(root=root)
        tree.all_items = {
            "mymodule": root,
            "mymodule.public_func": public_func,
            "mymodule._private_func": private_func,
        }

        public_items = tree.get_public_items()
        assert len(public_items) == 2  # root + public_func
        assert public_func in public_items
        assert private_func not in public_items

    def test_get_public_items_by_type(self) -> None:
        """Test filtering public items by type."""
        root = DocItem(
            type=DocItemType.MODULE,
            name="mymodule",
            qualified_name="mymodule",
        )

        func = DocItem(
            type=DocItemType.FUNCTION,
            name="func",
            qualified_name="mymodule.func",
        )

        cls = DocItem(
            type=DocItemType.CLASS,
            name="MyClass",
            qualified_name="mymodule.MyClass",
        )

        tree = DocumentationTree(root=root)
        tree.all_items = {
            "mymodule": root,
            "mymodule.func": func,
            "mymodule.MyClass": cls,
        }

        functions = tree.get_public_items(DocItemType.FUNCTION)
        assert len(functions) == 1
        assert func in functions

        classes = tree.get_public_items(DocItemType.CLASS)
        assert len(classes) == 1
        assert cls in classes

    def test_search(self) -> None:
        """Test search functionality."""
        root = DocItem(
            type=DocItemType.MODULE,
            name="mymodule",
            qualified_name="mymodule",
            docstring="A module for calculations",
        )

        calc_func = DocItem(
            type=DocItemType.FUNCTION,
            name="calculate",
            qualified_name="mymodule.calculate",
            docstring="Calculate something",
        )

        tree = DocumentationTree(root=root)
        tree.all_items = {
            "mymodule": root,
            "mymodule.calculate": calc_func,
        }

        # Search by name
        results = tree.search("calculate")
        assert calc_func in results

        # Search by docstring
        results = tree.search("calculations")
        assert root in results


class TestDocstringParser:
    """Test DocstringParser."""

    def test_parse_empty_docstring(self) -> None:
        """Test parsing empty docstring."""
        parser = DocstringParser()
        result = parser.parse(None)

        assert result["summary"] == ""
        assert result["description"] == ""
        assert result["parameters"] == []

    def test_detect_google_style(self) -> None:
        """Test detecting Google-style docstrings."""
        parser = DocstringParser(DocstringStyle.AUTO)

        docstring = """
        A function.

        Args:
            x: A value
        """

        style = parser._detect_style(docstring)
        assert style == DocstringStyle.GOOGLE

    def test_detect_numpy_style(self) -> None:
        """Test detecting NumPy-style docstrings."""
        parser = DocstringParser(DocstringStyle.AUTO)

        docstring = """
        A function.

        Parameters
        ----------
        x : int
            A value
        """

        style = parser._detect_style(docstring)
        assert style == DocstringStyle.NUMPY

    def test_parse_google_args(self) -> None:
        """Test parsing Google-style arguments."""
        parser = DocstringParser(DocstringStyle.GOOGLE)

        docstring = """
        A function.

        Args:
            x (int): First value
            y (str): Second value
            z: Third value without type
        """

        result = parser.parse(docstring)

        assert len(result["parameters"]) == 3
        assert result["parameters"][0]["name"] == "x"
        assert result["parameters"][0]["type_hint"] == "int"
        assert "First value" in result["parameters"][0]["description"]

    def test_parse_google_returns(self) -> None:
        """Test parsing Google-style returns."""
        parser = DocstringParser(DocstringStyle.GOOGLE)

        docstring = """
        A function.

        Returns:
            int: The result
        """

        result = parser.parse(docstring)

        assert result["returns"] is not None
        assert result["returns"]["type"] == "int"
        assert "result" in result["returns"]["description"]

    def test_parse_google_raises(self) -> None:
        """Test parsing Google-style raises."""
        parser = DocstringParser(DocstringStyle.GOOGLE)

        docstring = """
        A function.

        Raises:
            ValueError: If value is invalid
            TypeError: If type is wrong
        """

        result = parser.parse(docstring)

        assert len(result["raises"]) == 2
        assert result["raises"][0][0] == "ValueError"
        assert "invalid" in result["raises"][0][1]

    def test_parse_google_examples(self) -> None:
        """Test parsing Google-style examples."""
        parser = DocstringParser(DocstringStyle.GOOGLE)

        docstring = """
        A function.

        Examples:
            >>> foo(1)
            2
            >>> foo(2)
            4
        """

        result = parser.parse(docstring)

        assert len(result["examples"]) > 0

    def test_parse_numpy_parameters(self) -> None:
        """Test parsing NumPy-style parameters."""
        parser = DocstringParser(DocstringStyle.NUMPY)

        docstring = """
        A function.

        Parameters
        ----------
        x : int
            First value
        y : str
            Second value
        """

        result = parser.parse(docstring)

        assert len(result["parameters"]) == 2
        assert result["parameters"][0]["name"] == "x"
        assert result["parameters"][0]["type_hint"] == "int"

    def test_parse_numpy_returns(self) -> None:
        """Test parsing NumPy-style returns."""
        parser = DocstringParser(DocstringStyle.NUMPY)

        docstring = """
        A function.

        Returns
        -------
        int
            The result
        """

        result = parser.parse(docstring)

        assert result["returns"] is not None
        assert result["returns"]["type"] == "int"

    def test_parse_basic_docstring(self) -> None:
        """Test parsing basic docstring."""
        parser = DocstringParser()

        docstring = "Just a simple description."

        result = parser.parse(docstring)

        assert result["summary"] == "Just a simple description."
        assert result["description"] == "Just a simple description."


class TestASTDocExtractor:
    """Test ASTDocExtractor."""

    def test_extract_module_docstring(self) -> None:
        """Test extracting module docstring."""
        source = '''"""Module docstring."""

def foo() -> None:
    pass
'''

        extractor = ASTDocExtractor("test.py", source)
        items = extractor.extract()

        module_items = [item for item in items if item.type == DocItemType.MODULE]
        assert len(module_items) == 1
        assert (
            module_items[0].docstring is not None
            and "Module docstring" in module_items[0].docstring
        )

    def test_extract_function(self) -> None:
        """Test extracting function."""
        source = '''
def calculate(x: int, y: int = 10) -> int:
    """Calculate something.

    Args:
        x: First value
        y: Second value

    Returns:
        The result
    """
    return x + y
'''

        extractor = ASTDocExtractor("test.py", source)
        items = extractor.extract()

        func_items = [item for item in items if item.type == DocItemType.FUNCTION]
        assert len(func_items) == 1

        func = func_items[0]
        assert func.name == "calculate"
        assert len(func.parameters) == 2
        assert func.parameters[0].name == "x"
        assert func.parameters[0].type_hint == "int"
        assert func.parameters[1].default_value == "10"
        assert func.return_type == "int"

    def test_extract_async_function(self) -> None:
        """Test extracting async function."""
        source = '''
async def fetch_data() -> dict:
    """Fetch data."""
    return {}
'''

        extractor = ASTDocExtractor("test.py", source)
        items = extractor.extract()

        func_items = [item for item in items if item.type == DocItemType.FUNCTION]
        assert len(func_items) == 1
        assert func_items[0].is_async

    def test_extract_class(self) -> None:
        """Test extracting class."""
        source = '''
class Calculator:
    """A calculator class."""

    def add(self, x: int, y: int) -> int:
        """Add two numbers."""
        return x + y
'''

        extractor = ASTDocExtractor("test.py", source)
        items = extractor.extract()

        class_items = [item for item in items if item.type == DocItemType.CLASS]
        assert len(class_items) == 1
        assert class_items[0].name == "Calculator"

        method_items = [item for item in items if item.type == DocItemType.METHOD]
        assert len(method_items) == 1
        assert method_items[0].name == "add"

    def test_extract_decorators(self) -> None:
        """Test extracting decorators."""
        source = '''
class MyClass:
    @property
    def value(self) -> Any:
        """A property."""
        return self._value

    @staticmethod
    def static_method() -> None:
        """A static method."""
        pass

    @classmethod
    def class_method(cls) -> None:
        """A class method."""
        pass
'''

        extractor = ASTDocExtractor("test.py", source)
        items = extractor.extract()

        method_items = [
            item for item in items if item.type in (DocItemType.METHOD, DocItemType.PROPERTY)
        ]

        prop = next(item for item in method_items if item.name == "value")
        assert prop.is_property

        static = next(item for item in method_items if item.name == "static_method")
        assert static.is_staticmethod

        classm = next(item for item in method_items if item.name == "class_method")
        assert classm.is_classmethod

    def test_extract_with_syntax_error(self) -> None:
        """Test extraction with syntax error."""
        source = "def foo("  # Invalid syntax

        extractor = ASTDocExtractor("test.py", source)
        items = extractor.extract()

        # Should not crash, just return empty
        assert items == []


class TestDocumentationGenerator:
    """Test DocumentationGenerator."""

    def test_generator_creation(self) -> None:
        """Test creating generator."""
        gen = DocumentationGenerator()
        assert gen.docstring_style == DocstringStyle.AUTO

        gen2 = DocumentationGenerator(DocstringStyle.GOOGLE)
        assert gen2.docstring_style == DocstringStyle.GOOGLE

    def test_generate_docs_from_file(self) -> None:
        """Test generating docs from a file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                '''"""Test module."""

def foo(x: int) -> int:
    """Foo function.

    Args:
        x: A value

    Returns:
        Result
    """
    return x * 2
'''
            )
            f.flush()

            gen = DocumentationGenerator()
            tree = gen.generate_docs(f.name, package_name="test", version="1.0.0")

            assert tree.package_name == "test"
            assert tree.version == "1.0.0"
            assert len(tree.modules) > 0
            assert len(tree.functions) > 0

            # Cleanup
            Path(f.name).unlink()

    def test_generate_docs_from_directory(self) -> None:
        """Test generating docs from a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "module1.py").write_text(
                '''"""Module 1."""

def func1() -> None:
    """Function 1."""
    pass
'''
            )

            (Path(tmpdir) / "module2.py").write_text(
                '''"""Module 2."""

class MyClass:
    """A class."""
    pass
'''
            )

            gen = DocumentationGenerator()
            tree = gen.generate_docs(tmpdir)

            assert len(tree.modules) == 2
            assert len(tree.classes) == 1
            assert len(tree.functions) == 1

    def test_exclude_private_members(self) -> None:
        """Test excluding private members."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                '''"""Test module."""

def public_func() -> None:
    """Public function."""
    pass

def _private_func() -> None:
    """Private function."""
    pass
'''
            )
            f.flush()

            gen = DocumentationGenerator()
            tree = gen.generate_docs(f.name, include_private=False)

            # Private function should be excluded
            func_names = [func.name for func in tree.functions.values()]
            assert "public_func" in func_names
            assert "_private_func" not in func_names

            Path(f.name).unlink()

    def test_include_private_members(self) -> None:
        """Test including private members."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                '''"""Test module."""

def public_func() -> None:
    """Public function."""
    pass

def _private_func() -> None:
    """Private function."""
    pass
'''
            )
            f.flush()

            gen = DocumentationGenerator()
            tree = gen.generate_docs(f.name, include_private=True)

            # Both functions should be included
            func_names = [func.name for func in tree.functions.values()]
            assert "public_func" in func_names
            assert "_private_func" in func_names

            Path(f.name).unlink()

    def test_build_search_index(self) -> None:
        """Test building search index."""
        root = DocItem(
            type=DocItemType.MODULE,
            name="mymodule",
            qualified_name="mymodule",
            docstring="A module for testing search functionality",
        )

        tree = DocumentationTree(root=root)
        tree.all_items = {"mymodule": root}

        gen = DocumentationGenerator()
        index = gen._build_search_index(tree)

        # Should index by name
        assert "mymodule" in index

        # Should index by words in docstring
        assert "testing" in index or "search" in index

    def test_write_html_docs(self) -> None:
        """Test writing HTML documentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = DocItem(
                type=DocItemType.MODULE,
                name="mymodule",
                qualified_name="mymodule",
            )

            tree = DocumentationTree(
                root=root,
                package_name="test",
                version="1.0.0",
            )

            gen = DocumentationGenerator()
            gen.write_docs(tree, tmpdir, OutputFormat.HTML)

            # Check that index.html was created
            assert (Path(tmpdir) / "index.html").exists()

            # Check content
            content = (Path(tmpdir) / "index.html").read_text()
            assert "test" in content or "mymodule" in content

    def test_write_markdown_docs(self) -> None:
        """Test writing Markdown documentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = DocItem(
                type=DocItemType.MODULE,
                name="mymodule",
                qualified_name="mymodule",
                summary="Test module",
            )

            tree = DocumentationTree(
                root=root,
                package_name="test",
                version="1.0.0",
            )
            tree.modules = {"mymodule": root}

            gen = DocumentationGenerator()
            gen.write_docs(tree, tmpdir, OutputFormat.MARKDOWN)

            # Check that index.md was created
            assert (Path(tmpdir) / "index.md").exists()

            # Check content
            content = (Path(tmpdir) / "index.md").read_text()
            assert "test" in content or "Documentation" in content

    def test_write_json_docs(self) -> None:
        """Test writing JSON documentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            root = DocItem(
                type=DocItemType.MODULE,
                name="mymodule",
                qualified_name="mymodule",
            )

            func = DocItem(
                type=DocItemType.FUNCTION,
                name="foo",
                qualified_name="mymodule.foo",
            )

            tree = DocumentationTree(
                root=root,
                package_name="test",
                version="1.0.0",
            )
            tree.modules = {"mymodule": root}
            tree.functions = {"mymodule.foo": func}
            tree.all_items = {"mymodule": root, "mymodule.foo": func}

            gen = DocumentationGenerator()
            gen.write_docs(tree, tmpdir, OutputFormat.JSON)

            # Check that documentation.json was created
            assert (Path(tmpdir) / "documentation.json").exists()

            # Check content
            data = json.loads((Path(tmpdir) / "documentation.json").read_text())
            assert data["package_name"] == "test"
            assert data["version"] == "1.0.0"
            assert "mymodule" in data["modules"]
            assert "mymodule.foo" in data["functions"]

    def test_generate_markdown_index(self) -> None:
        """Test generating markdown index."""
        root = DocItem(
            type=DocItemType.MODULE,
            name="mymodule",
            qualified_name="mymodule",
            summary="A test module",
        )

        tree = DocumentationTree(
            root=root,
            package_name="TestPackage",
            version="1.0.0",
        )
        tree.modules = {"mymodule": root}

        gen = DocumentationGenerator()
        md = gen._generate_markdown_index(tree)

        assert "TestPackage" in md
        assert "1.0.0" in md
        assert "mymodule" in md

    def test_generate_module_markdown(self) -> None:
        """Test generating module markdown."""
        module = DocItem(
            type=DocItemType.MODULE,
            name="mymodule",
            qualified_name="mymodule",
            summary="A test module",
        )

        func = DocItem(
            type=DocItemType.FUNCTION,
            name="foo",
            qualified_name="mymodule.foo",
            parent="mymodule",
            summary="A function",
        )

        tree = DocumentationTree(root=module)
        tree.all_items = {
            "mymodule": module,
            "mymodule.foo": func,
        }

        gen = DocumentationGenerator()
        md = gen._generate_module_markdown(module, tree)

        assert "# mymodule" in md
        assert "A test module" in md
        assert "foo" in md

    def test_generate_basic_html(self) -> None:
        """Test generating basic HTML."""
        root = DocItem(
            type=DocItemType.MODULE,
            name="mymodule",
            qualified_name="mymodule",
        )

        tree = DocumentationTree(
            root=root,
            package_name="TestPackage",
        )

        gen = DocumentationGenerator()
        html = gen._generate_basic_html(tree)

        assert "<!DOCTYPE html>" in html
        assert "TestPackage" in html


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_complete_workflow(self) -> None:
        """Test complete documentation generation workflow."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a test module
            source_file = Path(tmpdir) / "mylib.py"
            source_file.write_text(
                '''"""My Library.

A library for doing cool things.
"""

class Calculator:
    """A calculator class.

    This class provides basic arithmetic operations.
    """

    def add(self, x: int, y: int) -> int:
        """Add two numbers.

        Args:
            x: First number
            y: Second number

        Returns:
            Sum of x and y

        Examples:
            >>> calc = Calculator()
            >>> calc.add(2, 3)
            5
        """
        return x + y

    def subtract(self, x: int, y: int) -> int:
        """Subtract two numbers.

        Args:
            x: First number
            y: Second number

        Returns:
            Difference of x and y
        """
        return x - y

def multiply(x: int, y: int) -> int:
    """Multiply two numbers.

    Args:
        x: First number
        y: Second number

    Returns:
        Product of x and y

    Raises:
        ValueError: If inputs are invalid
    """
    return x * y
'''
            )

            # Generate documentation
            gen = DocumentationGenerator()
            tree = gen.generate_docs(
                str(source_file),
                package_name="mylib",
                version="1.0.0",
            )

            # Verify structure
            assert tree.package_name == "mylib"
            assert tree.version == "1.0.0"
            assert len(tree.modules) == 1
            assert len(tree.classes) == 1
            assert len(tree.functions) == 1

            # Verify class
            calculator = tree.classes["Calculator"]
            assert calculator.name == "Calculator"
            assert len(calculator.methods) == 2

            # Verify method
            add_method = next(m for m in calculator.methods if m.name == "add")
            assert len(add_method.parameters) == 3  # self, x, y
            assert add_method.return_type == "int"

            # Verify function
            multiply_func = tree.functions["multiply"]
            assert multiply_func.name == "multiply"
            assert len(multiply_func.raises) == 1

            # Write HTML
            output_dir = Path(tmpdir) / "docs"
            gen.write_docs(tree, output_dir, OutputFormat.HTML)
            assert (output_dir / "index.html").exists()

            # Write Markdown
            md_dir = Path(tmpdir) / "md_docs"
            gen.write_docs(tree, md_dir, OutputFormat.MARKDOWN)
            assert (md_dir / "index.md").exists()

            # Write JSON
            json_dir = Path(tmpdir) / "json_docs"
            gen.write_docs(tree, json_dir, OutputFormat.JSON)
            assert (json_dir / "documentation.json").exists()

    def test_numpy_style_docstrings(self) -> None:
        """Test with NumPy-style docstrings."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(
                '''"""Module with NumPy docstrings."""

def calculate(x, y) -> Any:
    """
    Calculate something.

    Parameters
    ----------
    x : int
        First value
    y : int
        Second value

    Returns
    -------
    int
        The result

    Raises
    ------
    ValueError
        If inputs are invalid
    """
    return x + y
'''
            )
            f.flush()

            gen = DocumentationGenerator(DocstringStyle.NUMPY)
            tree = gen.generate_docs(f.name)

            func = list(tree.functions.values())[0]
            assert len(func.parameters) == 2
            assert func.return_type == "int"
            assert len(func.raises) == 1

            Path(f.name).unlink()
