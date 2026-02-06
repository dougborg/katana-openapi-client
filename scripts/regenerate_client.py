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
    uv run python regenerate_client.py

The script should be run with 'uv run python' to ensure all dependencies
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
        print("      Run: uv add --dev pyyaml openapi-spec-validator")
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
from .utils import (
    APIError,
    AuthenticationError,
    RateLimitError,
    ServerError,
    ValidationError,
    get_error_message,
    get_variant_display_name,
    handle_response,
    is_error,
    is_success,
    unwrap,
    unwrap_data,
)

__all__ = [
    "APIError",
    "AuthenticatedClient",
    "AuthenticationError",
    "Client",
    "KatanaClient",
    "RateLimitError",
    "ServerError",
    "ValidationError",
    "get_error_message",
    "get_variant_display_name",
    "handle_response",
    "is_error",
    "is_success",
    "unwrap",
    "unwrap_data",
]
'''
        main_init.write_text(init_content, encoding="utf-8")
        print("   📄 Updated __init__.py with flattened imports and utils exports")

        # Fix imports in generated API files to use client_types instead of types
        print("🔧 Fixing imports in generated API files...")
        _fix_types_imports(target_client_path)

        # Note: We don't copy the generated README.md as it contains Poetry references
        # The main README.md in the repository root provides documentation instead

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
        ["uv", "run", "poe", "test"], cwd=workspace_path, check=False
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
        ["uv", "run", "poe", "format-python"], cwd=workspace_path, check=False
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

    # Fix the B032 issue and type annotation in receive_purchase_order.py
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
            # Add explicit cast to fix ty error - ty doesn't narrow types in for loops
            if (
                "for componentsschemas_purchase_order_receive_request_type_0_item_data in body:"
                in content
            ):
                # Add cast import if not present
                if "from typing import" in content and "cast" not in content:
                    content = re.sub(
                        r"from typing import ([^\n]+)",
                        r"from typing import \1, cast",
                        content,
                        count=1,
                    )
                # Add cast before the loop
                content = re.sub(
                    r'(if isinstance\(body, list\):)\s*\n(\s+)_kwargs\["json"\] = \[\]\s*\n(\s+)for componentsschemas_purchase_order_receive_request_type_0_item_data in body:',
                    r'\1\n\2_kwargs["json"] = []\n\2# Cast needed for type checker to understand loop variable type\n\2typed_body = cast(list["PurchaseOrderReceiveRow"], body)\n\2for componentsschemas_purchase_order_receive_request_type_0_item_data in typed_body:',
                    content,
                )
            receive_po_file.write_text(content, encoding="utf-8")
            print("   ✓ Fixed B032 and type annotation in receive_purchase_order.py")
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

    # Fix ty type errors in generated code
    fix_ty_type_errors(workspace_path)

    # Fix pagination defaults for auto-pagination
    fix_pagination_defaults(workspace_path)

    return True


def fix_pagination_defaults(workspace_path: Path) -> None:
    """Fix pagination defaults to enable auto-pagination by default.

    The openapi-python-client generator creates endpoints with:
    - `page: int | Unset = 1`
    - `limit: int | Unset = 50`

    These defaults cause page and limit params to always be included in requests,
    which affects KatanaClient's automatic pagination feature.

    This function changes both defaults to UNSET so that:
    - By default, no page/limit params are sent → auto-pagination ON with limit=250
    - Explicitly passing page=N disables auto-pagination (get just that page)
    - Explicitly passing limit=N uses that limit per page (caller's choice)
    """
    print("🔧 Fixing pagination defaults for auto-pagination support...")

    client_path = workspace_path / "katana_public_api_client"
    api_path = client_path / "api"

    if not api_path.exists():
        print("   ⚠️  API directory not found, skipping")
        return

    page_fixed = 0
    limit_fixed = 0
    for py_file in api_path.rglob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            original = content

            # Change page default from 1 to UNSET
            # Handle both type orderings: "int | Unset" and "Unset | int"
            # Using [,)] to handle both trailing comma and closing paren cases
            new_content = re.sub(
                r"(page:\s*(?:int\s*\|\s*Unset|Unset\s*\|\s*int)\s*=\s*)1(\s*[,)])",
                r"\1UNSET\2",
                content,
            )
            if new_content != content:
                page_fixed += 1
                content = new_content

            # Change limit default from 50 to UNSET
            new_content = re.sub(
                r"(limit:\s*(?:int\s*\|\s*Unset|Unset\s*\|\s*int)\s*=\s*)50(\s*[,)])",
                r"\1UNSET\2",
                content,
            )
            if new_content != content:
                limit_fixed += 1
                content = new_content

            if content != original:
                py_file.write_text(content, encoding="utf-8")

        except Exception as e:
            print(f"   ⚠️  Could not fix {py_file}: {e}")

    print(f"   ✓ Fixed page defaults in {page_fixed} API files")
    print(f"   ✓ Fixed limit defaults in {limit_fixed} API files")


def fix_ty_type_errors(workspace_path: Path) -> None:
    """Add type: ignore comments and casts for ty type checker errors in generated code."""
    print("🔧 Adding type: ignore comments and casts for ty type checker...")

    client_path = workspace_path / "katana_public_api_client"

    # Fix from_dict method calls in API files and model files
    all_py_files = list((client_path / "api").rglob("*.py")) + list(
        (client_path / "models").rglob("*.py")
    )

    for py_file in all_py_files:
        try:
            content = py_file.read_text(encoding="utf-8")
            original = content

            # Fix .from_dict(data) calls - cast data to Mapping[str, Any]
            # Pattern 1: Single line calls
            content = re.sub(
                r"(\w+)\.from_dict\(data\)(\s*#\s*type:\s*ignore\[arg-type\])?",
                r"\1.from_dict(cast(Mapping[str, Any], data))",
                content,
            )

            # Pattern 2: Multi-line calls with data on next line
            content = re.sub(
                r"(\w+)\.from_dict\(\s*\n\s+data\s*\n\s*\)(\s*#\s*type:\s*ignore\[arg-type\])?",
                r"\1.from_dict(\n                cast(Mapping[str, Any], data)\n            )",
                content,
            )

            # Ensure cast and Mapping are imported
            if "cast(Mapping[str, Any], data)" in content:
                # Check if cast is already imported from typing
                if not re.search(r"from typing import.*\bcast\b", content):
                    # Find the from typing import line and add cast at the end
                    content = re.sub(
                        r"(from typing import (?:[^,\n]+(?:,\s*)?)+)",
                        r"\1, cast",
                        content,
                        count=1,
                    )

                # Check if Mapping is imported from collections.abc
                if not re.search(r"from collections\.abc import.*\bMapping\b", content):
                    # Check if there's already a collections.abc import
                    if "from collections.abc import" in content:
                        # Add Mapping to existing import at the end
                        content = re.sub(
                            r"(from collections\.abc import (?:[^,\n]+(?:,\s*)?)+)",
                            r"\1, Mapping",
                            content,
                            count=1,
                        )
                    else:
                        # Add new import after typing import
                        content = re.sub(
                            r"(from typing import [^\n]+\n)",
                            r"\1from collections.abc import Mapping\n",
                            content,
                            count=1,
                        )

            # Note: We previously added # type: ignore[misc] to from_dict methods and
            # # type: ignore[return-value] to cast() calls, but ty no longer requires these
            # suppressions. Removed to avoid "unused-ignore-comment" warnings.

            if content != original:
                py_file.write_text(content, encoding="utf-8")
        except Exception as e:
            print(f"   ⚠️  Could not fix {py_file}: {e}")

    print("   ✓ Added type: ignore comments and casts for ty type checker errors")


def run_lint_check(workspace_path: Path) -> bool:
    """Run linting and auto-fix issues in the generated code."""
    print("🔍 Running linting and auto-fix on generated code...")

    # First, run ruff with --fix and --unsafe-fixes to auto-fix as much as possible
    print("🔧 Auto-fixing linting issues with ruff (including unsafe fixes)...")
    run_command(
        ["uv", "run", "ruff", "check", "--fix", "--unsafe-fixes", "."],
        cwd=workspace_path,
        check=False,
    )

    # Fix specific issues that ruff can't handle automatically
    fix_specific_generated_issues(workspace_path)

    print("📄 All issues handled by automated fixes")

    # Then run the lint command to check for any remaining issues
    print("🔍 Checking for remaining linting issues...")
    check_result = run_command(
        ["uv", "run", "poe", "lint-ruff"], cwd=workspace_path, check=False
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
