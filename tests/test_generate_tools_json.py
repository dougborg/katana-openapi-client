"""Tests for the generate_tools_json.py script.

This module tests the tools.json generator that extracts tool metadata
from the Katana MCP server for Docker MCP Registry submission.
"""

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Import the script module by adding parent directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))

from generate_tools_json import (  # type: ignore[import-not-found] # noqa: E402
    _extract_description,
    _extract_from_directory,
    extract_tool_info_from_ast,
    generate_json,
    validate_tools,
)


class TestExtractToolInfo:
    """Tests for extract_tool_info_from_ast function."""

    def test_extract_from_real_tools_directory(self):
        """Test extraction from actual MCP server tools."""
        # Get the actual tools directory
        project_root = Path(__file__).parent.parent
        tools_dir = project_root / "katana_mcp_server" / "src" / "katana_mcp" / "tools"

        # Extract tools
        tools = extract_tool_info_from_ast(tools_dir)

        # Verify we got tools
        assert len(tools) > 0, "Should extract at least one tool"

        # Verify structure
        for tool in tools:
            assert "name" in tool, "Tool should have name"
            assert "description" in tool, "Tool should have description"
            assert isinstance(tool["name"], str), "Name should be string"
            assert isinstance(tool["description"], str), "Description should be string"
            assert len(tool["name"]) > 0, "Name should not be empty"
            assert len(tool["description"]) > 0, "Description should not be empty"

        # Verify specific known tools exist
        tool_names = {tool["name"] for tool in tools}
        assert "search_items" in tool_names, "Should have search_items tool"
        assert "check_inventory" in tool_names, "Should have check_inventory tool"
        assert "create_product" in tool_names, "Should have create_product tool"

        # Verify alphabetical sorting
        sorted_names = [tool["name"] for tool in tools]
        assert sorted_names == sorted(sorted_names), (
            "Tools should be sorted alphabetically"
        )

    def test_nonexistent_directory_raises_error(self):
        """Test that nonexistent directory raises FileNotFoundError."""
        fake_dir = Path("/nonexistent/directory")
        with pytest.raises(FileNotFoundError, match="Tools directory not found"):
            extract_tool_info_from_ast(fake_dir)

    def test_empty_directory_raises_error(self):
        """Test that empty tools directory raises ValueError."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tools_dir = Path(tmpdir)
            # Create empty foundation and workflows directories
            (tools_dir / "foundation").mkdir()
            (tools_dir / "workflows").mkdir()

            with pytest.raises(ValueError, match="No tools found"):
                extract_tool_info_from_ast(tools_dir)


class TestExtractFromDirectory:
    """Tests for _extract_from_directory function."""

    def test_extract_from_foundation_directory(self):
        """Test extraction from foundation tools directory."""
        project_root = Path(__file__).parent.parent
        foundation_dir = (
            project_root
            / "katana_mcp_server"
            / "src"
            / "katana_mcp"
            / "tools"
            / "foundation"
        )

        tools = _extract_from_directory(foundation_dir)

        # Should have multiple tools
        assert len(tools) > 0, "Should extract foundation tools"

        # Verify structure
        for tool in tools:
            assert "name" in tool
            assert "description" in tool

    def test_skips_private_functions(self):
        """Test that private functions (starting with _) are skipped."""
        # Create temporary test file
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)
            test_file = test_dir / "test_tools.py"
            test_file.write_text("""
async def public_tool():
    \"\"\"Public tool description.\"\"\"
    pass

async def _private_impl():
    \"\"\"Private implementation.\"\"\"
    pass
""")

            tools = _extract_from_directory(test_dir)

            # Should only have public tool
            assert len(tools) == 1
            assert tools[0]["name"] == "public_tool"
            assert "private_impl" not in [t["name"] for t in tools]

    def test_handles_syntax_errors_gracefully(self):
        """Test that syntax errors in files are handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir)
            bad_file = test_dir / "bad_syntax.py"
            bad_file.write_text("def incomplete(")

            # Should not raise, just skip the file
            tools = _extract_from_directory(test_dir)
            assert len(tools) == 0


class TestExtractDescription:
    """Tests for _extract_description function."""

    def test_extract_from_docstring(self):
        """Test description extraction from docstring."""
        import ast

        code = """
async def test_tool():
    \"\"\"First line of docstring.

    More details here.
    \"\"\"
    pass
"""
        tree = ast.parse(code)
        func_node = tree.body[0]
        description = _extract_description(func_node)

        assert description == "First line of docstring."

    def test_extract_from_multiline_docstring(self):
        """Test extraction with empty lines in docstring."""
        import ast

        code = '''
async def test_tool():
    """

    Actual first line.

    More details.
    """
    pass
'''
        tree = ast.parse(code)
        func_node = tree.body[0]
        description = _extract_description(func_node)

        assert description == "Actual first line."

    def test_fallback_when_no_docstring(self):
        """Test fallback description when no docstring."""
        import ast

        code = """
async def test_tool():
    pass
"""
        tree = ast.parse(code)
        func_node = tree.body[0]
        description = _extract_description(func_node)

        assert description == "Tool: test_tool"


class TestValidateTools:
    """Tests for validate_tools function."""

    def test_validate_valid_tools(self):
        """Test validation passes for valid tools."""
        tools = [
            {"name": "tool1", "description": "Description 1"},
            {"name": "tool2", "description": "Description 2"},
        ]

        # Should not raise
        validate_tools(tools)

    def test_empty_list_raises_error(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError, match="Tool list is empty"):
            validate_tools([])

    def test_missing_name_raises_error(self):
        """Test that missing name field raises ValueError."""
        tools = [{"description": "Description"}]
        with pytest.raises(ValueError, match="missing 'name' field"):
            validate_tools(tools)

    def test_missing_description_raises_error(self):
        """Test that missing description field raises ValueError."""
        tools = [{"name": "tool1"}]
        with pytest.raises(ValueError, match="missing 'description' field"):
            validate_tools(tools)

    def test_empty_name_raises_error(self):
        """Test that empty name raises ValueError."""
        tools = [{"name": "", "description": "Description"}]
        with pytest.raises(ValueError, match="invalid name"):
            validate_tools(tools)

    def test_empty_description_raises_error(self):
        """Test that empty description raises ValueError."""
        tools = [{"name": "tool1", "description": ""}]
        with pytest.raises(ValueError, match="invalid description"):
            validate_tools(tools)

    def test_non_dict_raises_error(self):
        """Test that non-dictionary element raises ValueError."""
        tools = ["not a dict"]
        with pytest.raises(ValueError, match="not a dictionary"):
            validate_tools(tools)


class TestGenerateJson:
    """Tests for generate_json function."""

    def test_compact_json_format(self):
        """Test compact JSON generation."""
        tools = [
            {"name": "tool1", "description": "Description 1"},
            {"name": "tool2", "description": "Description 2"},
        ]

        result = generate_json(tools, pretty=False)

        # Should be compact (no indentation)
        assert "\n  " not in result
        assert result.endswith("\n")

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed == tools

    def test_pretty_json_format(self):
        """Test pretty-printed JSON generation."""
        tools = [
            {"name": "tool1", "description": "Description 1"},
            {"name": "tool2", "description": "Description 2"},
        ]

        result = generate_json(tools, pretty=True)

        # Should have indentation
        assert "\n  " in result
        assert result.endswith("\n")

        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed == tools

    def test_empty_list(self):
        """Test JSON generation with empty list."""
        tools = []
        result = generate_json(tools)

        assert result == "[]\n"
        parsed = json.loads(result)
        assert parsed == []


class TestEndToEnd:
    """End-to-end integration tests."""

    def test_full_extraction_workflow(self):
        """Test complete workflow from extraction to JSON generation."""
        # Get tools directory
        project_root = Path(__file__).parent.parent
        tools_dir = project_root / "katana_mcp_server" / "src" / "katana_mcp" / "tools"

        # Extract tools
        tools = extract_tool_info_from_ast(tools_dir)

        # Validate
        validate_tools(tools)

        # Generate JSON
        json_output = generate_json(tools, pretty=True)

        # Verify JSON is valid
        parsed = json.loads(json_output)
        assert isinstance(parsed, list)
        assert len(parsed) == len(tools)

        # Verify each tool has required fields
        for tool in parsed:
            assert "name" in tool
            assert "description" in tool

    def test_output_file_generation(self):
        """Test writing output to file."""
        project_root = Path(__file__).parent.parent
        tools_dir = project_root / "katana_mcp_server" / "src" / "katana_mcp" / "tools"

        tools = extract_tool_info_from_ast(tools_dir)
        json_output = generate_json(tools, pretty=True)

        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)
            temp_path.write_text(json_output)

        try:
            # Verify file contents
            content = temp_path.read_text()
            parsed = json.loads(content)
            assert len(parsed) == len(tools)
        finally:
            temp_path.unlink()


class TestToolCount:
    """Tests for verifying expected tool count."""

    def test_minimum_tool_count(self):
        """Test that we have a minimum expected number of tools."""
        project_root = Path(__file__).parent.parent
        tools_dir = project_root / "katana_mcp_server" / "src" / "katana_mcp" / "tools"

        tools = extract_tool_info_from_ast(tools_dir)

        # As of writing, we have 15 tools
        # Use a minimum threshold to avoid brittle tests
        assert len(tools) >= 10, f"Expected at least 10 tools, got {len(tools)}"

    def test_specific_tools_present(self):
        """Test that specific critical tools are present."""
        project_root = Path(__file__).parent.parent
        tools_dir = project_root / "katana_mcp_server" / "src" / "katana_mcp" / "tools"

        tools = extract_tool_info_from_ast(tools_dir)
        tool_names = {tool["name"] for tool in tools}

        # Critical foundation tools that should always exist
        critical_tools = [
            "search_items",
            "check_inventory",
            "create_product",
            "create_material",
            "create_purchase_order",
        ]

        for tool_name in critical_tools:
            assert tool_name in tool_names, f"Critical tool '{tool_name}' not found"
