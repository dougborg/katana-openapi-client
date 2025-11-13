#!/usr/bin/env python3
"""Generate tools.json for Docker MCP Registry from MCP server tools.

This script introspects the registered MCP tools and generates a tools.json
file suitable for the Docker MCP Registry submission. This ensures the tools
list stays in sync with the actual tool implementations.

The script uses AST parsing to extract tool information without importing
the server module, avoiding potential import errors and runtime dependencies.

Usage:
    python scripts/generate_tools_json.py                    # Print to stdout
    python scripts/generate_tools_json.py -o tools.json      # Write to file
    python scripts/generate_tools_json.py -o tools.json -p   # Pretty-print
"""

import argparse
import ast
import json
import sys
from pathlib import Path


def extract_tool_info_from_ast(tools_dir: Path) -> list[dict[str, str]]:
    """Extract tool information by parsing Python source files with AST.

    This approach avoids runtime imports that might fail due to missing
    dependencies or environment configuration issues.

    Args:
        tools_dir: Path to the tools directory (foundation + workflows)

    Returns:
        List of tool dictionaries with name and description

    Raises:
        FileNotFoundError: If tools directory doesn't exist
        ValueError: If no tools are found
    """
    if not tools_dir.exists():
        raise FileNotFoundError(f"Tools directory not found: {tools_dir}")

    tools: list[dict[str, str]] = []
    foundation_dir = tools_dir / "foundation"
    workflows_dir = tools_dir / "workflows"

    # Process foundation tools
    if foundation_dir.exists():
        tools.extend(_extract_from_directory(foundation_dir))

    # Process workflow tools
    if workflows_dir.exists():
        tools.extend(_extract_from_directory(workflows_dir))

    if not tools:
        raise ValueError("No tools found in the MCP server")

    # Sort alphabetically by name
    tools.sort(key=lambda x: x["name"])

    return tools


def _extract_from_directory(directory: Path) -> list[dict[str, str]]:
    """Extract tools from a single directory.

    Args:
        directory: Path to tool module directory

    Returns:
        List of tool dictionaries
    """
    tools: list[dict[str, str]] = []

    for py_file in sorted(directory.glob("*.py")):
        if py_file.name == "__init__.py":
            continue

        try:
            with open(py_file) as f:
                tree = ast.parse(f.read(), filename=str(py_file))

            # Find all async function definitions that are tools
            # Tools are the public async functions (not starting with _)
            for node in ast.walk(tree):
                if isinstance(node, ast.AsyncFunctionDef) and not node.name.startswith(
                    "_"
                ):
                    # This is a tool function
                    description = _extract_description(node)
                    tools.append({"name": node.name, "description": description})

        except Exception as e:
            print(
                f"Warning: Failed to parse {py_file}: {e}",
                file=sys.stderr,
            )
            continue

    return tools


def _extract_description(node: ast.AsyncFunctionDef) -> str:
    """Extract description from function docstring.

    Args:
        node: AST node for async function

    Returns:
        First non-empty line of docstring or default description
    """
    docstring = ast.get_docstring(node)
    if docstring:
        # Extract first non-empty line
        lines = [line.strip() for line in docstring.split("\n") if line.strip()]
        if lines:
            return lines[0]

    # Fallback description
    return f"Tool: {node.name}"


def validate_tools(tools: list[dict[str, str]]) -> None:
    """Validate tool list structure.

    Args:
        tools: List of tool dictionaries

    Raises:
        ValueError: If validation fails
    """
    if not tools:
        raise ValueError("Tool list is empty")

    for i, tool in enumerate(tools):
        if not isinstance(tool, dict):
            raise ValueError(f"Tool {i} is not a dictionary")

        if "name" not in tool:
            raise ValueError(f"Tool {i} missing 'name' field")

        if "description" not in tool:
            raise ValueError(f"Tool {i} missing 'description' field")

        if not isinstance(tool["name"], str) or not tool["name"]:
            raise ValueError(f"Tool {i} has invalid name")

        if not isinstance(tool["description"], str) or not tool["description"]:
            raise ValueError(f"Tool {i} has invalid description")


def generate_json(tools: list[dict[str, str]], pretty: bool = False) -> str:
    """Generate JSON string from tools list.

    Args:
        tools: List of tool dictionaries
        pretty: Whether to pretty-print with indentation

    Returns:
        JSON string with newline
    """
    if pretty:
        return json.dumps(tools, indent=2) + "\n"
    return json.dumps(tools) + "\n"


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate tools.json for Docker MCP Registry",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Print to stdout
  python scripts/generate_tools_json.py

  # Write to file
  python scripts/generate_tools_json.py -o tools.json

  # Write with pretty formatting
  python scripts/generate_tools_json.py -o tools.json --pretty
        """,
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        help="Output file path (default: stdout)",
    )
    parser.add_argument(
        "--pretty",
        "-p",
        action="store_true",
        help="Pretty-print JSON output with indentation",
    )

    args = parser.parse_args()

    try:
        # Locate tools directory
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        tools_dir = project_root / "katana_mcp_server" / "src" / "katana_mcp" / "tools"

        # Extract tool information
        tools = extract_tool_info_from_ast(tools_dir)

        # Validate structure
        validate_tools(tools)

        # Generate JSON
        json_output = generate_json(tools, pretty=args.pretty)

        # Write output
        if args.output:
            args.output.write_text(json_output)
            print(
                f"✓ Generated tools.json with {len(tools)} tools → {args.output}",
                file=sys.stderr,
            )
        else:
            print(json_output, end="")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
