#!/usr/bin/env python3
"""
Regenerate the Katana OpenAPI client from the specification.

This script:
1. Validates the OpenAPI specification
2. Generates a new client using openapi-python-client
3. Moves the generated client to the main workspace
4. Formats the generated code (now includes generated files)
5. Runs linting checks on the generated code
6. Installs dependencies and runs tests

Note: Generated files are now included in formatting and linting,
so they will be consistently styled according to project standards.

Usage:
    poetry run python regenerate_client.py [--force] [--skip-validation] [--skip-tests]

The script should be run with 'poetry run python' to ensure all dependencies
(including PyYAML and openapi-spec-validator) are available.
"""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def run_command(
    cmd: list[str], cwd: Path | None = None, check: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run a command and return the result."""
    print(f"🔨 Running: {' '.join(cmd)}")
    if cwd:
        print(f"   📁 Working directory: {cwd}")

    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if check and result.returncode != 0:
        print(f"❌ Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)

    return result


def validate_openapi_spec(spec_path: Path) -> bool:
    """Validate the OpenAPI specification."""
    print("🔍 Validating OpenAPI specification...")

    # First check if the spec file exists
    if not spec_path.exists():
        print(f"❌ OpenAPI spec file not found: {spec_path}")
        return False

    try:
        # Import required validation dependencies
        import yaml
        from openapi_spec_validator import validate_spec as openapi_validate_spec

        # Load and validate the spec
        try:
            with open(spec_path, encoding="utf-8") as f:
                spec = yaml.safe_load(f)

            openapi_validate_spec(spec)
            print("✅ OpenAPI spec is valid")
            return True

        except yaml.YAMLError as e:
            print(f"❌ YAML parsing error: {e}")
            return False
        except Exception as e:
            print(f"❌ OpenAPI spec validation failed: {e}")
            return False

    except ImportError as e:
        print("❌ Required validation dependencies missing:")
        print(f"   Missing: {e.name}")
        print("   Run: poetry add --group dev pyyaml openapi-spec-validator")
        return False


def generate_client(spec_path: Path, workspace_path: Path) -> bool:
    """Generate the OpenAPI client."""
    print("🚀 Generating OpenAPI client...")

    # Remove old generated directory if it exists
    temp_client_dir = workspace_path / "katana-public-api-client"
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


def move_client_to_workspace(workspace_path: Path) -> bool:
    """Move the generated client to the main workspace using proper separation."""
    print("📁 Moving client to main workspace with proper separation...")

    temp_client_dir = workspace_path / "katana-public-api-client"
    source_client_path = temp_client_dir / "katana_public_api_client"
    target_client_path = workspace_path / "katana_public_api_client"
    generated_path = target_client_path / "generated"

    if not source_client_path.exists():
        print(f"❌ Source client path not found: {source_client_path}")
        return False

    try:
        # Ensure the target client directory exists
        target_client_path.mkdir(parents=True, exist_ok=True)

        # Create the generated subdirectory structure
        generated_path.mkdir(parents=True, exist_ok=True)

        # Define which files/directories are generated (should be replaced)
        generated_items = [
            "client.py",
            "errors.py",
            "types.py",
            "py.typed",
            "api",
            "models",
        ]

        print("🔄 Updating generated files in generated/ subdirectory...")

        # Move generated files to the generated/ subdirectory
        for item_name in generated_items:
            source_item = source_client_path / item_name
            target_item = generated_path / item_name

            if source_item.exists():
                # Remove existing generated item
                if target_item.exists():
                    if target_item.is_dir():
                        shutil.rmtree(target_item)
                        print(
                            f"   🗑️  Removed existing directory: generated/{item_name}"
                        )
                    else:
                        target_item.unlink()
                        print(f"   🗑️  Removed existing file: generated/{item_name}")

                # Copy the new generated item
                if source_item.is_dir():
                    shutil.copytree(source_item, target_item)
                    print(f"   📦 Updated directory: generated/{item_name}")
                else:
                    shutil.copy2(source_item, target_item)
                    print(f"   📄 Updated file: generated/{item_name}")

        # Create/update the generated/__init__.py
        generated_init = generated_path / "__init__.py"
        generated_init_content = '''"""Generated OpenAPI client code - do not edit manually."""

from .client import AuthenticatedClient, Client
from .errors import *
from .types import *

__all__ = [
    "AuthenticatedClient",
    "Client",
]
'''
        generated_init.write_text(generated_init_content, encoding="utf-8")
        print("   📄 Updated generated/__init__.py")

        # Ensure main __init__.py has correct imports (don't overwrite custom content)
        main_init = target_client_path / "__init__.py"
        if main_init.exists():
            current_content = main_init.read_text(encoding="utf-8")

            # Only update if it doesn't already have the correct import
            if "from .generated.client import" not in current_content:
                # Update imports to use the new structure
                updated_content = current_content.replace(
                    "from .client import AuthenticatedClient, Client",
                    "from .generated.client import AuthenticatedClient, Client",
                )

                main_init.write_text(updated_content, encoding="utf-8")
                print("   📄 Updated main __init__.py imports")
        else:
            # Create main __init__.py if it doesn't exist
            main_init_content = '''"""A client library for accessing Katana Public API"""

__version__ = "0.1.0"

from .generated.client import AuthenticatedClient, Client
from .katana_client import KatanaClient
from .log_setup import get_logger, setup_logging

__all__ = (
    "AuthenticatedClient",
    "Client",
    "KatanaClient",
    "setup_logging",
    "get_logger",
    "__version__",
)
'''
            main_init.write_text(main_init_content, encoding="utf-8")
            print("   📄 Created main __init__.py")

        # Copy the generated README for reference
        source_readme = temp_client_dir / "README.md"
        target_readme = workspace_path / "CLIENT_README.md"
        if source_readme.exists():
            shutil.copy2(source_readme, target_readme)
            print(f"📝 Updated client README: {target_readme}")

        # Clean up temporary directory
        print(f"🗑️  Cleaning up temporary directory: {temp_client_dir}")
        shutil.rmtree(temp_client_dir)

        print("✅ Client moved successfully with proper separation")
        return True

    except Exception as e:
        print(f"❌ Failed to move client: {e}")
        return False


def install_dependencies(workspace_path: Path) -> bool:
    """Install Poetry dependencies."""
    print("📦 Installing dependencies with Poetry...")

    result = run_command(["poetry", "install"], cwd=workspace_path, check=False)

    if result.returncode != 0:
        print("❌ Failed to install dependencies")
        return False

    print("✅ Dependencies installed successfully")
    return True


def run_tests(workspace_path: Path) -> bool:
    """Run tests to verify the client works."""
    print("🧪 Running client tests...")

    test_script = workspace_path / "simple_test_client.py"
    if not test_script.exists():
        print("i  No test script found, skipping tests")
        return True

    result = run_command(
        ["poetry", "run", "python", str(test_script)], cwd=workspace_path, check=False
    )

    if result.returncode != 0:
        print("⚠️  Tests failed, but client may still be functional")
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

    # Run the format command which now includes generated files
    result = run_command(
        ["poetry", "run", "poe", "format"], cwd=workspace_path, check=False
    )

    if result.returncode != 0:
        print("⚠️  Formatting had issues but continuing")
        return True  # Don't fail the whole process for formatting issues

    print("✅ Code formatted successfully")
    return True


def apply_generated_code_patches(workspace_path: Path) -> bool:
    """Apply systematic patches to fix known issues in generated code.

    This function applies patch files from the patches/ directory to fix
    systematic issues that occur in generated OpenAPI client code.
    """
    patches_path = workspace_path / "patches"
    if not patches_path.exists():
        print("   📄 No patches directory found, skipping patch application")
        return True

    patch_files = list(patches_path.glob("*.patch"))
    if not patch_files:
        print("   📄 No patch files found, skipping patch application")
        return True

    print(f"   🩹 Found {len(patch_files)} patch files to apply")

    for patch_file in sorted(patch_files):
        try:
            # Apply the patch using git apply (works even outside git repos)
            result = subprocess.run(
                ["git", "apply", "--ignore-whitespace", str(patch_file)],
                cwd=workspace_path,
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode == 0:
                print(f"   ✅ Applied patch: {patch_file.name}")
            else:
                print(f"   ⚠️  Failed to apply patch {patch_file.name}: {result.stderr}")
                # Don't fail the whole process, just log the issue

        except (subprocess.SubprocessError, OSError) as e:
            print(f"   ⚠️  Error applying patch {patch_file.name}: {e}")
            # Don't fail the whole process

    return True


def post_process_generated_docstrings(workspace_path: Path) -> bool:
    """Post-process generated Python files to improve RST docstring formatting.

    This function applies targeted fixes to common RST formatting issues in
    generated OpenAPI client code that cause Sphinx warnings.
    """
    generated_path = workspace_path / "katana_public_api_client" / "generated"
    if not generated_path.exists():
        return True

    python_files = list(generated_path.rglob("*.py"))
    processed_count = 0

    for py_file in python_files:
        try:
            content = py_file.read_text(encoding="utf-8")
            original_content = content

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
        f"📝 Post-processed {processed_count} generated files for better RST formatting"
    )
    return True


def run_lint_check(workspace_path: Path) -> bool:
    """Run linting and auto-fix issues in the generated code."""
    print("🔍 Running linting and auto-fix on generated code...")

    # First, run ruff with --fix using the poe task to ensure consistency
    print("🔧 Auto-fixing linting issues with ruff...")
    run_command(
        ["poetry", "run", "poe", "lint-ruff-fix"],
        cwd=workspace_path,
        check=False,
    )

    # Apply systematic patches to fix remaining issues that ruff can't handle
    print("🩹 Applying patches to fix systematic issues in generated code...")
    if not apply_generated_code_patches(workspace_path):
        print("⚠️  Patch application had issues but continuing")

    # Then run the lint command to check for any remaining issues
    print("🔍 Checking for remaining linting issues...")
    check_result = run_command(
        ["poetry", "run", "poe", "lint-ruff"], cwd=workspace_path, check=False
    )

    if check_result.returncode != 0:
        print("⚠️  Some linting issues remain but continuing")
        print("💡 You may want to review and fix these issues manually")
        return True  # Don't fail the whole process for linting issues

    print("✅ Linting checks passed")
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Regenerate Katana OpenAPI client")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force regeneration even if validation fails",
    )
    parser.add_argument(
        "--skip-validation", action="store_true", help="Skip OpenAPI spec validation"
    )
    parser.add_argument(
        "--skip-tests", action="store_true", help="Skip running tests after generation"
    )
    parser.add_argument(
        "--skip-format",
        action="store_true",
        help="Skip formatting and linting generated code",
    )
    parser.add_argument(
        "--spec-path",
        type=Path,
        default="katana-openapi.yaml",
        help="Path to OpenAPI spec",
    )

    args = parser.parse_args()

    # Setup paths
    workspace_path = Path.cwd()
    spec_path = workspace_path / args.spec_path
    client_path = workspace_path / "katana_public_api_client"

    print("🚀 Katana OpenAPI Client Regeneration")
    print("=" * 50)
    print(f"📁 Workspace: {workspace_path}")
    print(f"📄 OpenAPI spec: {spec_path}")
    print(f"📦 Client path: {client_path}")

    # Step 1: Validate OpenAPI spec
    if not args.skip_validation:
        if not validate_openapi_spec(spec_path):
            if not args.force:
                print(
                    "❌ OpenAPI spec validation failed. Use --force to continue anyway."
                )
                sys.exit(1)
            else:
                print("⚠️  Continuing despite validation failure due to --force flag")
    else:
        print("⏭️  Skipping OpenAPI spec validation")

    # Step 2: Generate new client
    if not generate_client(spec_path, workspace_path):
        print("❌ Failed to generate client")
        sys.exit(1)

    # Step 3: Move client to workspace
    if not move_client_to_workspace(workspace_path):
        print("❌ Failed to move client to workspace")
        sys.exit(1)

    # Step 4: Install dependencies
    if not install_dependencies(workspace_path):
        print("❌ Failed to install dependencies")
        sys.exit(1)

    # Step 5: Run tests
    if not args.skip_tests:
        if not run_tests(workspace_path):
            print("⚠️  Tests had issues but continuing")
    else:
        print("⏭️  Skipping tests")

    # Step 6: Format generated code
    if not args.skip_format:
        if not format_generated_code(workspace_path):
            print("⚠️  Formatting had issues but continuing")

        # Step 7: Run linting checks
        if not run_lint_check(workspace_path):
            print("⚠️  Linting had issues but continuing")
    else:
        print("⏭️  Skipping formatting and linting")

    print("\n" + "=" * 50)
    print("✅ Client regeneration completed successfully!")
    print("\n💡 Next steps:")
    print("   1. Review the generated client in ./katana_public_api_client/")
    print("   2. Update your code imports if needed")
    print("   3. Test your application with the new client")


if __name__ == "__main__":
    main()
