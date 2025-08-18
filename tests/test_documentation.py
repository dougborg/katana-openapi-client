"""
Test documentation generation to ensure it works in CI/CD.
"""

import os
import subprocess
from pathlib import Path

import pytest


@pytest.mark.docs
def test_documentation_builds_successfully():
    """Test that MkDocs documentation builds without errors."""
    if os.getenv("CI_DOCS_BUILD", "false").lower() != "true":
        pytest.skip("Documentation tests only run when CI_DOCS_BUILD=true")

    # Check if documentation is already built
    build_dir = Path(__file__).parent.parent / "site"
    if build_dir.exists() and (build_dir / "index.html").exists():
        print("✅ Documentation already built, skipping build test")
        return

    try:
        # Run the docs build command directly with poethepoet
        result = subprocess.run(
            ["poe", "docs-build"],
            check=False,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes for docs build (increased for CI)
            cwd=Path(__file__).parent.parent,
        )

        # Check if build succeeded
        assert result.returncode == 0, f"Documentation build failed:\n{result.stderr}"

        # Check if key files were generated (MkDocs builds to 'site' directory)
        assert build_dir.exists(), "Documentation build directory not created"
        assert (build_dir / "index.html").exists(), "Main index not generated"
        assert (build_dir / "reference" / "index.html").exists(), (
            "API documentation not generated"
        )

        print("✅ Documentation build successful!")
        print(f"Build output: {build_dir}")

    except subprocess.TimeoutExpired:
        pytest.fail("Documentation build timed out after 10 minutes")
    except Exception as e:
        pytest.fail(f"Documentation build failed with error: {e}")


@pytest.mark.docs
def test_documentation_has_api_reference():
    """Test that API reference documentation is generated."""
    if os.getenv("CI_DOCS_BUILD", "false").lower() != "true":
        pytest.skip("Documentation tests only run when CI_DOCS_BUILD=true")

    build_dir = Path(__file__).parent.parent / "site"

    # Run docs build first if needed
    if not build_dir.exists() or not (build_dir / "index.html").exists():
        subprocess.run(
            ["poe", "docs-build"],
            check=False,
            cwd=Path(__file__).parent.parent,
            timeout=600,  # 10 minutes for docs build
        )

    # Check that API reference exists
    api_dir = build_dir / "reference"
    assert api_dir.exists(), "API reference directory not found"

    # Check for main API documentation
    assert (api_dir / "katana_public_api_client" / "index.html").exists(), (
        "Main API package documentation not found"
    )

    print("✅ API reference documentation generated successfully!")


@pytest.mark.docs
def test_documentation_has_openapi_docs():
    """Test that OpenAPI documentation is generated."""
    if os.getenv("CI_DOCS_BUILD", "false").lower() != "true":
        pytest.skip("Documentation tests only run when CI_DOCS_BUILD=true")

    build_dir = Path(__file__).parent.parent / "site"

    # Run docs build first if needed
    if not build_dir.exists():
        subprocess.run(
            ["poe", "docs-build"],
            check=False,
            cwd=Path(__file__).parent.parent,
            timeout=300,  # 5 minutes for docs build
        )

    # Check that OpenAPI documentation exists
    assert (build_dir / "openapi-docs" / "index.html").exists(), (
        "OpenAPI documentation not found"
    )

    print("✅ OpenAPI documentation generated successfully!")


if __name__ == "__main__":
    # Enable docs testing environment variable for direct execution
    os.environ["CI_DOCS_BUILD"] = "true"

    # Run all tests
    test_documentation_builds_successfully()
    test_documentation_has_api_reference()
    test_documentation_has_openapi_docs()


def test_documentation_search_functionality():
    """Test that documentation search index is generated."""
    if os.getenv("CI_DOCS_BUILD", "false").lower() != "true":
        pytest.skip("Documentation tests only run when CI_DOCS_BUILD=true")

    build_dir = Path(__file__).parent.parent / "docs" / "_build" / "html"

    # Run docs build first if needed
    if not build_dir.exists():
        subprocess.run(
            ["poe", "docs-build"],
            check=False,
            cwd=Path(__file__).parent.parent,
            timeout=300,  # 5 minutes for docs build
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
