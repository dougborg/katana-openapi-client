"""Tests for katana_mcp package structure and imports."""


def test_package_import():
    """Test that the main package can be imported."""
    import katana_mcp

    assert katana_mcp.__version__ == "0.3.0"


def test_submodule_imports():
    """Test that submodules can be imported."""
    from katana_mcp import prompts, resources, tools

    assert tools is not None
    assert resources is not None
    assert prompts is not None


def test_package_metadata():
    """Test that package metadata is available."""
    import katana_mcp

    assert hasattr(katana_mcp, "__version__")
    assert isinstance(katana_mcp.__version__, str)
    assert len(katana_mcp.__version__) > 0


def test_package_docstring():
    """Test that the package has documentation."""
    import katana_mcp

    assert katana_mcp.__doc__ is not None
    assert "MCP Server" in katana_mcp.__doc__ or "MCP server" in katana_mcp.__doc__
    assert "Katana" in katana_mcp.__doc__
