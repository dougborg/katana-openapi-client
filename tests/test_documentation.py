"""
Test documentation generation to ensure it works in CI/CD.
"""

import subprocess
from pathlib import Path

import pytest


def test_documentation_builds_successfully():
    """Test that Sphinx documentation builds without errors."""
    try:
        # Run the docs build command directly with poethepoet
        result = subprocess.run(
            ["poe", "docs-build"],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=Path(__file__).parent.parent,
        )

        # Check if build succeeded
        assert result.returncode == 0, f"Documentation build failed:\n{result.stderr}"

        # Check that key files were generated
        build_dir = Path(__file__).parent.parent / "docs" / "_build" / "html"
        assert build_dir.exists(), "Documentation build directory not found"

        # Check for main documentation files
        assert (build_dir / "index.html").exists(), "Main index.html not generated"
        assert (
            build_dir / "autoapi" / "katana_public_api_client" / "index.html"
        ).exists(), "API documentation not generated"
        assert (build_dir / "genindex.html").exists(), "General index not generated"

        print("✅ Documentation build successful!")
        print(f"Build output: {build_dir}")

    except subprocess.TimeoutExpired:
        pytest.fail("Documentation build timed out")
    except Exception as e:
        pytest.fail(f"Documentation build failed with error: {e}")


def test_documentation_has_api_reference():
    """Test that API reference documentation is generated."""
    build_dir = Path(__file__).parent.parent / "docs" / "_build" / "html"

    # Run docs build first if needed
    if not build_dir.exists():
        subprocess.run(
            ["poe", "docs-build"],
            check=False,
            cwd=Path(__file__).parent.parent,
            timeout=120,
        )

    # Check that API reference exists
    api_dir = build_dir / "autoapi" / "katana_public_api_client"
    assert api_dir.exists(), "API reference directory not found"

    # Check for main classes
    assert (api_dir / "katana_client" / "index.html").exists(), (
        "KatanaClient documentation not found"
    )
    assert (api_dir / "log_setup" / "index.html").exists(), (
        "log_setup documentation not found"
    )

    print("✅ API reference documentation generated successfully!")


def test_documentation_search_functionality():
    """Test that documentation search index is generated."""
    build_dir = Path(__file__).parent.parent / "docs" / "_build" / "html"

    # Run docs build first if needed
    if not build_dir.exists():
        subprocess.run(
            ["poe", "docs-build"],
            check=False,
            cwd=Path(__file__).parent.parent,
            timeout=120,
        )

    # Check that search files exist
    assert (build_dir / "search.html").exists(), "Search page not generated"
    assert (build_dir / "searchindex.js").exists(), "Search index not generated"

    # Check that searchindex.js contains references to our classes
    searchindex_content = (build_dir / "searchindex.js").read_text()
    assert "katanaclient" in searchindex_content.lower(), "KatanaClient not indexed"
    assert "resilientasynctransport" in searchindex_content.lower(), (
        "ResilientAsyncTransport not indexed"
    )

    print("✅ Documentation search functionality working!")


if __name__ == "__main__":
    test_documentation_builds_successfully()
    test_documentation_has_api_reference()
    test_documentation_search_functionality()
    print("\n🎉 All documentation tests passed!")
