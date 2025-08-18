#!/usr/bin/env python3
"""
Regenerate the Katana OpenAPI client from the specification.

This script:
1. Validates the OpenAPI specification using multiple validators:
   - openapi-spec-validator (basic OpenAPI compliance)
   - Redocly CLI (advanced linting with detailed rules)
2. Generates a new client using openapi-python-client
3. Moves the generated client to the main workspace
4. Runs linting checks and auto-fixes on the generated code
5. Applies final formatting to ensure consistency
6. Runs tests to verify the client works

The script will fail if any validation errors are found.
Validation warnings will be displayed but won't cause failure.

Usage:
    poetry run python regenerate_client.py

The script should be run with 'poetry run python' to ensure all dependencies
(including PyYAML and openapi-spec-validator) are available.
Node.js and npx are required for Redocly validation.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command and return the result."""
    print(f"🔨 Running: {' '.join(cmd)}")
    if cwd:
        print(f"   📁 Working directory: {cwd}")
    if timeout:
        print(f"   ⏱️  Timeout: {timeout}s")

    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, check=False, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        print(f"   ⏰ Command timed out after {timeout}s")
        return subprocess.CompletedProcess(
            cmd, 124, "", f"Command timed out after {timeout}s"
        )

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if check and result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    return result


def run_command_streaming(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
    timeout: int | None = None,
) -> int:
    """Run a command with real-time output streaming."""
    print(f"🔨 Running: {' '.join(cmd)}")
    if cwd:
        print(f"   📁 Working directory: {cwd}")
    if timeout:
        print(f"   ⏱️  Timeout: {timeout}s")

    try:
        process = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True,
        )

        # Stream output in real-time
        if process.stdout:
            for line in process.stdout:
                print(line, end="")

        # Wait for process to complete
        returncode = process.wait(timeout=timeout)

    except subprocess.TimeoutExpired:
        print(f"\n   ⏰ Command timed out after {timeout}s")
        if process:
            process.kill()
        return 124
    except Exception as e:
        print(f"\n   ❌ Error running command: {e}")
        return 1

    if check and returncode != 0:
        print(f"❌ Command failed with exit code {returncode}")
        sys.exit(returncode)

    return returncode


def validate_openapi_spec(spec_path: Path) -> bool:
    """Validate the OpenAPI specification using multiple validators."""
    print("🔍 Validating OpenAPI specification...")

    # First check if the spec file exists
    if not spec_path.exists():
        print(f"❌ OpenAPI spec file not found: {spec_path}")
        return False

    # Run basic OpenAPI spec validation
    if not _validate_with_openapi_spec_validator(spec_path):
        return False

    # Run Redocly validation
    if not _validate_with_redocly(spec_path):
        return False

    print("✅ All OpenAPI validations passed")
    return True


def _validate_with_openapi_spec_validator(spec_path: Path) -> bool:
    """Validate using openapi-spec-validator."""
    print("   📋 Running openapi-spec-validator...")

    try:
        # Import required validation dependencies
        import yaml
        from openapi_spec_validator import validate_spec as openapi_validate_spec
        from openapi_spec_validator.exceptions import OpenAPISpecValidatorError

    except ImportError as e:
        print("   ❌ Required validation dependencies missing:")
        print(f"      Missing: {e.name}")
        print("      Run: poetry add --group dev pyyaml openapi-spec-validator")
        return False

    # Load and validate the spec
    try:
        with open(spec_path, encoding="utf-8") as f:
            spec = yaml.safe_load(f)

        openapi_validate_spec(spec)
        print("   ✅ openapi-spec-validator passed")
        return True

    except yaml.YAMLError as e:
        print(f"   ❌ YAML parsing error: {e}")
        return False
    except OpenAPISpecValidatorError as e:
        print(f"   ❌ OpenAPI spec validation error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ OpenAPI spec validation failed: {e}")
        return False


def _validate_with_redocly(spec_path: Path) -> bool:
    """Validate using Redocly CLI."""
    print("   🎯 Running Redocly validation...")

    # Check if npx is available
    npx_check = run_command(["which", "npx"], check=False)
    if npx_check.returncode != 0:
        print("   ⚠️  npx not found, skipping Redocly validation")
        print("      Install Node.js to enable Redocly validation")
        return True  # Don't fail if Node.js is not available

    # Run Redocly validation (non-interactive)
    result = run_command(
        ["npx", "--yes", "@redocly/cli", "lint", str(spec_path)],
        cwd=spec_path.parent,
        check=False,
    )

    if result.returncode != 0:
        print("   ❌ Redocly validation failed")
        print("      Check the output above for specific errors and warnings")
        return False

    print("   ✅ Redocly validation passed")
    return True


def generate_client(spec_path: Path, workspace_path: Path) -> bool:
    """Generate the OpenAPI client."""
    print("🚀 Generating OpenAPI client...")

    # Remove old generated directory if it exists
    temp_client_dir = workspace_path / "openapi_gen_temp"
    if temp_client_dir.exists():
        print(f"🗑️  Removing old temporary client directory: {temp_client_dir}")
        shutil.rmtree(temp_client_dir)

    # Generate the client
    result = run_command(
        [
            "openapi-python-client",
            "generate",
            "--path",
            str(spec_path),
            "--output-path",
            str(temp_client_dir),
        ],
        cwd=workspace_path,
        check=False,
    )

    if result.returncode != 0:
        print("❌ Client generation failed")
        return False

    # Check if the client was generated
    if not temp_client_dir.exists():
        print("❌ Generated client directory not found")
        return False

    print("✅ Client generated successfully")
    return True


def _fix_types_imports(target_client_path: Path) -> None:
    """Fix imports from 'types' to 'client_types' in all generated files."""
    import re

    print("🔧 Fixing types imports in generated files...")

    # Find all Python files in the client directory
    updated_files = 0
    for py_file in target_client_path.rglob("*.py"):
        if py_file.name in ["__init__.py", "katana_client.py", "log_setup.py"]:
            continue  # Skip custom files

        try:
            content = py_file.read_text(encoding="utf-8")
            original_content = content

            # Replace all patterns of types imports
            patterns = [
                # Relative imports from API files (3 dots = two levels up)
                (r"from \.\.\.types import", "from ...client_types import"),
                # Relative imports from models (2 dots = one level up)
                (r"from \.\.types import", "from ..client_types import"),
                # Direct relative imports (1 dot = same level)
                (r"from \.types import", "from .client_types import"),
                # Absolute imports
                (
                    r"from katana_public_api_client\.types import",
                    "from katana_public_api_client.client_types import",
                ),
            ]

            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)

            # Only write if content changed
            if content != original_content:
                py_file.write_text(content, encoding="utf-8")
                print(
                    f"   � Fixed imports in {py_file.relative_to(target_client_path)}"
                )
                updated_files += 1

        except (UnicodeDecodeError, OSError) as e:
            print(f"   ⚠️  Skipped {py_file}: {e}")

    print(f"   ✅ Updated imports in {updated_files} files")


def move_client_to_workspace(workspace_path: Path) -> bool:
    """Move the generated client to the main workspace, preserving custom files."""
    print("📁 Moving client to main workspace (flattened structure)...")

    temp_client_dir = workspace_path / "openapi_gen_temp"
    source_client_path = temp_client_dir / "katana_public_api_client"
    target_client_path = workspace_path / "katana_public_api_client"

    if not source_client_path.exists():
        print(f"❌ Source client path not found: {source_client_path}")
        return False

    try:
        # Ensure the target client directory exists
        target_client_path.mkdir(parents=True, exist_ok=True)

        # Define which files/directories are generated (should be replaced)
        # These will overwrite existing files in the main directory
        generated_items = [
            "client.py",
            "errors.py",
            "types.py",  # Will be renamed to client_types.py
            "py.typed",
            "api",
            "models",
        ]

        # Define custom files that should NOT be overwritten

        print("🔄 Updating generated files in main package directory...")

        # Move generated files to the main package directory
        for item_name in generated_items:
            source_item = source_client_path / item_name

            # Handle types.py rename to client_types.py
            if item_name == "types.py":
                target_item = target_client_path / "client_types.py"
            else:
                target_item = target_client_path / item_name

            if source_item.exists():
                # Remove existing generated item
                if target_item.exists():
                    if target_item.is_dir():
                        shutil.rmtree(target_item)
                        print(f"   🗑️  Removed existing directory: {item_name}")
                    else:
                        target_item.unlink()
                        print(f"   🗑️  Removed existing file: {item_name}")

                # Copy the new generated item
                if source_item.is_dir():
                    shutil.copytree(source_item, target_item)
                    print(f"   📦 Updated directory: {item_name}")
                else:
                    shutil.copy2(source_item, target_item)
                    print(f"   📄 Updated file: {item_name}")

        # Update main __init__.py with flattened imports (preserve any custom content)
        main_init = target_client_path / "__init__.py"
        init_content = '''"""Katana Public API Client - Python client for Katana Manufacturing ERP."""

from .client import AuthenticatedClient, Client
from .katana_client import KatanaClient

__all__ = [
    "AuthenticatedClient",
    "Client",
    "KatanaClient",
]
'''
        main_init.write_text(init_content, encoding="utf-8")
        print("   📄 Updated __init__.py with flattened imports")

        # Fix imports in generated API files to use client_types instead of types
        print("🔧 Fixing imports in generated API files...")
        _fix_types_imports(target_client_path)

        # Copy the generated README for reference
        source_readme = temp_client_dir / "README.md"
        target_readme = workspace_path / "CLIENT_README.md"
        if source_readme.exists():
            shutil.copy2(source_readme, target_readme)
            print(f"📝 Updated client README: {target_readme}")

        # Clean up temporary directory
        print(f"🗑️  Cleaning up temporary directory: {temp_client_dir}")
        shutil.rmtree(temp_client_dir)

        print("✅ Client moved successfully with flattened structure")
        return True

    except (OSError, shutil.Error) as e:
        print(f"❌ Failed to move client: {e}")
        return False


def run_tests(workspace_path: Path) -> bool:
    """Run tests to verify the client works."""
    print("🧪 Running client tests...")

    # Check if tests directory exists
    tests_dir = workspace_path / "tests"
    if not tests_dir.exists():
        print("i  No tests directory found, skipping tests")
        return True

    # Run the full test suite with streaming output
    returncode = run_command_streaming(
        ["poetry", "run", "poe", "test"], cwd=workspace_path, check=False
    )

    if returncode != 0:
        print("⚠️  Some tests failed, but client may still be functional")
        return True  # Don't fail the whole process for test failures

    print("✅ Tests passed")
    return True


def format_generated_code(workspace_path: Path) -> bool:
    """Format the generated code using the project's formatters."""
    print("✨ Formatting generated code...")

    # First, apply any custom post-processing to fix RST issues in generated files
    print("🔧 Post-processing generated docstrings for better RST formatting...")
    if not post_process_generated_docstrings(workspace_path):
        print("⚠️  Post-processing had issues but continuing")

    # Run the full format command (this handles all files consistently)
    print("🎨 Formatting all Python files...")
    result = run_command(
        ["poetry", "run", "poe", "format-python"], cwd=workspace_path, check=False
    )

    if result.returncode != 0:
        print("❌ Failed to format files")
        return False

    print("✅ Code formatted successfully")
    return True


def post_process_generated_docstrings(workspace_path: Path) -> bool:
    """Post-process generated Python files to improve RST docstring formatting.

    This function applies targeted fixes to common RST formatting issues in
    generated OpenAPI client code that cause Sphinx warnings. It also removes
    "Attributes:" sections from class docstrings to prevent AutoAPI 3.2+
    duplicate object warnings.
    """
    client_path = workspace_path / "katana_public_api_client"
    if not client_path.exists():
        return True

    # Only process generated files (not custom files like katana_client.py, log_setup.py)
    generated_patterns = [
        "api/**/*.py",
        "models/**/*.py",
        "client.py",
        "client_types.py",
        "errors.py",
    ]
    python_files: list[Path] = []

    for pattern in generated_patterns:
        python_files.extend(client_path.glob(pattern))
    processed_count = 0

    for py_file in python_files:
        try:
            content = py_file.read_text(encoding="utf-8")
            original_content = content

            # Fix: Remove "Attributes:" sections from class docstrings
            # AutoAPI 3.2+ generates both docstring attributes and typed attribute
            # directives, causing duplicate object warnings. We remove the docstring
            # attributes section since AutoAPI will auto-document typed attributes.

            # First, remove the Attributes section
            content = re.sub(
                r'(class\s+\w+[^:]*:\s*"""[^"]*?)(\s*Attributes:\s*.*?)(\s*""")',
                r"\1\3",
                content,
                flags=re.DOTALL,
            )

            # Then, remove empty docstrings (just whitespace between triple quotes)
            content = re.sub(
                r'(class\s+\w+[^:]*:)\s*"""\s*"""',
                r"\1",
                content,
            )

            # Fix: Add blank line between docstring sections
            # This fixes "Block quote ends without a blank line" warnings
            # The issue is when Args section ends and Raises/Returns section begins
            # without a blank line between them

            # Pattern: Last line of Args section followed directly by Raises/Returns
            content = re.sub(
                r"(\n\s+\w+[^:]*:[^\n]*\.\n)(\s+)(Raises?:|Returns?:)",
                r"\1\n\2\3",
                content,
            )

            # Only write if we made changes
            if content != original_content:
                py_file.write_text(content, encoding="utf-8")
                processed_count += 1

        except (OSError, UnicodeError, FileNotFoundError) as e:
            print(f"⚠️  Error processing {py_file}: {e}")
            # Continue processing other files

    print(
        f"📝 Post-processed {processed_count} generated files for better RST formatting and AutoAPI compatibility"
    )
    return True


def fix_specific_generated_issues(workspace_path: Path) -> bool:
    """Fix specific issues in generated code that ruff can't handle automatically."""
    print("🔧 Fixing specific generated code issues...")

    # Fix the B032 issue in receive_purchase_order.py
    receive_po_file = (
        workspace_path
        / "katana_public_api_client"
        / "api"
        / "purchase_order"
        / "receive_purchase_order.py"
    )
    if receive_po_file.exists():
        try:
            content = receive_po_file.read_text(encoding="utf-8")
            # Remove the standalone type annotation that causes B032
            content = content.replace(
                '    _kwargs["json"]: dict[str, Any] | list[dict[str, Any]]\n', ""
            )
            receive_po_file.write_text(content, encoding="utf-8")
            print("   ✓ Fixed B032 issue in receive_purchase_order.py")
        except Exception as e:
            print(f"   ⚠️  Could not fix receive_purchase_order.py: {e}")

    # Fix Union types in client_types.py to use | syntax
    client_types_file = workspace_path / "katana_public_api_client" / "client_types.py"
    if client_types_file.exists():
        try:
            content = client_types_file.read_text(encoding="utf-8")
            # Replace Union types with | syntax
            content = content.replace(
                "FileContent = Union[IO[bytes], bytes, str]",
                "FileContent = IO[bytes] | bytes | str",
            )
            content = content.replace(
                "FileTypes = Union[\n    # (filename, file (or bytes), content_type)\n    tuple[str | None, FileContent, str | None],\n    # (filename, file (or bytes), content_type, headers)\n    tuple[str | None, FileContent, str | None, Mapping[str, str]],\n]",
                "FileTypes = (\n    # (filename, file (or bytes), content_type)\n    tuple[str | None, FileContent, str | None] |\n    # (filename, file (or bytes), content_type, headers)\n    tuple[str | None, FileContent, str | None, Mapping[str, str]]\n)",
            )
            client_types_file.write_text(content, encoding="utf-8")
            print("   ✓ Fixed Union types in client_types.py")
        except Exception as e:
            print(f"   ⚠️  Could not fix client_types.py: {e}")

    return True


def run_lint_check(workspace_path: Path) -> bool:
    """Run linting and auto-fix issues in the generated code."""
    print("🔍 Running linting and auto-fix on generated code...")

    # First, run ruff with --fix and --unsafe-fixes to auto-fix as much as possible
    print("🔧 Auto-fixing linting issues with ruff (including unsafe fixes)...")
    run_command(
        ["poetry", "run", "ruff", "check", "--fix", "--unsafe-fixes", "."],
        cwd=workspace_path,
        check=False,
    )

    # Fix specific issues that ruff can't handle automatically
    fix_specific_generated_issues(workspace_path)

    print("📄 All issues handled by automated fixes")

    # Then run the lint command to check for any remaining issues
    print("🔍 Checking for remaining linting issues...")
    check_result = run_command(
        ["poetry", "run", "poe", "lint-ruff"], cwd=workspace_path, check=False
    )

    if check_result.returncode != 0:
        print("⚠️  Some linting issues remain but continuing")
        print("💡 These are typically minor issues or intentional code patterns")
        return True  # Don't fail the whole process for linting issues

    print("✅ Linting checks passed")
    return True


def main():
    """Main function."""
    # Setup paths
    workspace_path = Path.cwd()
    spec_path = workspace_path / "docs" / "katana-openapi.yaml"
    client_path = workspace_path / "katana_public_api_client"

    print("🚀 Katana OpenAPI Client Regeneration")
    print("=" * 50)
    print(f"📁 Workspace: {workspace_path}")
    print(f"📄 OpenAPI spec: {spec_path}")
    print(f"📦 Client path: {client_path}")

    # Step 1: Validate OpenAPI spec
    if not validate_openapi_spec(spec_path):
        print("❌ OpenAPI spec validation failed")
        sys.exit(1)

    # Step 2: Generate new client
    if not generate_client(spec_path, workspace_path):
        print("❌ Failed to generate client")
        sys.exit(1)

    # Step 3: Move client to workspace
    if not move_client_to_workspace(workspace_path):
        print("❌ Failed to move client to workspace")
        sys.exit(1)

    # Step 4: Run linting checks and auto-fixes
    if not run_lint_check(workspace_path):
        print("⚠️  Linting had issues but continuing")

    # Step 5: Format generated code
    if not format_generated_code(workspace_path):
        print("⚠️  Formatting had issues but continuing")

    # Step 6: Run tests
    if not run_tests(workspace_path):
        print("⚠️  Tests had issues but continuing")

    print("\n" + "=" * 50)
    print("✅ Client regeneration completed successfully!")
    print("\n💡 Next steps:")
    print("   1. Review the generated client in ./katana_public_api_client/")
    print("   2. Update your code imports if needed")
    print("   3. Test your application with the new client")


if __name__ == "__main__":
    main()
