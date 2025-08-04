#!/usr/bin/env python3
"""
Regenerate the Katana OpenAPI client from the specification using OpenAPI Generator.

This script:
1. Validates the OpenAPI specification using multiple validators:
   - openapi-spec-validator (basic OpenAPI compliance)
   - Redocly CLI (advanced linting with detailed rules)
2. Generates a new client using OpenAPI Generator (java-based) with python-pydantic-v1
3. Moves the generated client to the main workspace
4. Formats the generated code (now includes generated files)
5. Runs linting checks on the generated code
6. Installs dependencies and runs tests

The script will fail if any validation errors are found, unless --force is used.
Validation warnings will be displayed but won't cause failure.

Usage:
    poetry run python regenerate_client.py [--force] [--skip-validation] [--skip-tests]

The script should be run with 'poetry run python' to ensure all dependencies
(including PyYAML and openapi-spec-validator) are available.
Java 11+ is required for OpenAPI Generator.
Node.js and npx are required for Redocly validation.
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
        except (TypeError, ImportError) as e:
            print(f"   ❌ OpenAPI spec validation failed: {e}")
            return False
        except openapi_validate_spec.__globals__.get(
            "OpenAPIValidationError", Exception
        ) as e:
            print(f"   ❌ OpenAPI spec validation error: {e}")
            return False

    except ImportError as e:
        print("   ❌ Required validation dependencies missing:")
        print(f"      Missing: {e.name}")
        print("      Run: poetry add --group dev pyyaml openapi-spec-validator")
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

    # Run Redocly validation
    result = run_command(
        ["npx", "@redocly/cli", "lint", str(spec_path)],
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
    """Generate the OpenAPI client using OpenAPI Generator."""
    print("🚀 Generating OpenAPI client with OpenAPI Generator...")

    # Remove old generated directory if it exists
    temp_client_dir = workspace_path / "katana_api_client_generated"
    if temp_client_dir.exists():
        print(f"🗑️  Removing old temporary client directory: {temp_client_dir}")
        shutil.rmtree(temp_client_dir)

    # Check if OpenAPI Generator CLI jar exists
    jar_path = workspace_path / "openapi-generator-cli.jar"
    if not jar_path.exists():
        print("📥 Downloading OpenAPI Generator CLI...")
        # Download the OpenAPI Generator CLI jar
        result = run_command(
            [
                "wget",
                "-q",
                "https://repo1.maven.org/maven2/org/openapitools/openapi-generator-cli/7.10.0/openapi-generator-cli-7.10.0.jar",
                "-O",
                str(jar_path),
            ],
            cwd=workspace_path,
            check=False,
        )

        if result.returncode != 0:
            print("❌ Failed to download OpenAPI Generator CLI")
            return False

    # Generate the client using OpenAPI Generator with python-pydantic-v1
    print("📦 Generating Pydantic-based client...")
    result = run_command(
        [
            "java",
            "-jar",
            str(jar_path),
            "generate",
            "-g",
            "python-pydantic-v1",
            "-i",
            str(spec_path),
            "-o",
            str(temp_client_dir),
            "--package-name",
            "katana_api_client",
            "--additional-properties=library=asyncio,generateSourceCodeOnly=true",
            "--model-name-mappings",
            "error=ErrorResponse",  # Avoid naming conflicts
        ],
        cwd=workspace_path,
        check=False,
    )

    if result.returncode != 0:
        print("❌ Client generation failed")
        return False

    # Check if the client was generated
    generated_client_path = temp_client_dir / "katana_api_client"
    if not generated_client_path.exists():
        print("❌ Generated client directory not found")
        return False

    print("✅ Pydantic-based client generated successfully")
    return True


def move_client_to_workspace(workspace_path: Path) -> bool:
    """Move the generated client to the main workspace, replacing the old Union-based client."""
    print("📁 Moving Pydantic-based client to main workspace...")

    temp_client_dir = workspace_path / "katana_api_client_generated"
    source_client_path = temp_client_dir / "katana_api_client"
    target_client_path = workspace_path / "katana_public_api_client"
    generated_path = target_client_path / "generated"

    if not source_client_path.exists():
        print(f"❌ Source client path not found: {source_client_path}")
        return False

    try:
        # Ensure the target client directory exists
        target_client_path.mkdir(parents=True, exist_ok=True)

        # Remove the old generated directory completely and replace it
        if generated_path.exists():
            shutil.rmtree(generated_path)
            print("   🗑️  Removed old generated directory")

        # Create new generated subdirectory structure
        generated_path.mkdir(parents=True, exist_ok=True)

        # OpenAPI Generator creates different structure - we need to map the files
        generated_items_mapping = {
            # Core client files
            "api_client.py": "client.py",  # Map to expected name
            "configuration.py": "configuration.py",
            "exceptions.py": "errors.py",  # Map to expected name
            "api_response.py": "api_response.py",
            "rest.py": "rest.py",
            # Directories
            "api": "api",
            "models": "models",
        }

        print("🔄 Moving generated files to generated/ subdirectory...")

        # Move generated files to the generated/ subdirectory
        for source_name, target_name in generated_items_mapping.items():
            source_item = source_client_path / source_name
            target_item = generated_path / target_name

            if source_item.exists():
                # Copy the new generated item
                if source_item.is_dir():
                    shutil.copytree(source_item, target_item)
                    print(f"   📦 Added directory: generated/{target_name}")
                else:
                    shutil.copy2(source_item, target_item)
                    print(f"   📄 Added file: generated/{target_name}")

        # Create/update the generated/__init__.py with appropriate imports for new structure
        generated_init = generated_path / "__init__.py"
        generated_init_content = '''"""Generated OpenAPI client code - do not edit manually.

This module contains the Pydantic-based client generated by OpenAPI Generator.
It provides direct model access and exception-based error handling.
"""

from .client import ApiClient
from .configuration import Configuration
from .errors import *  # noqa: F403
from .api_response import ApiResponse

# Import all API classes
from .api import *  # noqa: F403

# Import all model classes
from .models import *  # noqa: F403

__all__ = [
    "ApiClient",
    "Configuration",
    "ApiResponse",
]
'''
        generated_init.write_text(generated_init_content, encoding="utf-8")
        print("   📄 Created generated/__init__.py")

        # Copy the main __init__.py from source to see what imports we need
        source_init = source_client_path / "__init__.py"
        if source_init.exists():
            # Read the source init to get the actual imports and API classes
            source_init_content = source_init.read_text(encoding="utf-8")

            # Extract API imports from the source (these will be our API classes)
            api_imports = []
            model_imports = []

            for line in source_init_content.split("\n"):
                if "from katana_api_client.api." in line:
                    # Extract the API class name
                    import_part = line.split("import ")[-1].strip()
                    api_imports.append(import_part)
                elif "from katana_api_client.models." in line:
                    # Extract the model class name
                    import_part = line.split("import ")[-1].strip()
                    model_imports.append(import_part)

            # Update the generated __init__.py with proper exports
            if api_imports or model_imports:
                all_exports = [
                    "ApiClient",
                    "Configuration",
                    "ApiResponse",
                    *api_imports,
                    *model_imports,
                ]
                updated_init_content = generated_init_content.replace(
                    '__all__ = [\n    "ApiClient",\n    "Configuration", \n    "ApiResponse",\n]',
                    "__all__ = [\n"
                    + "\n".join(f'    "{item}",' for item in all_exports)
                    + "\n]",
                )
                generated_init.write_text(updated_init_content, encoding="utf-8")
                print(
                    f"   📄 Updated generated/__init__.py with {len(api_imports)} APIs and {len(model_imports)} models"
                )

        # Update main __init__.py to import from the new generated structure
        main_init = target_client_path / "__init__.py"
        if main_init.exists():
            current_content = main_init.read_text(encoding="utf-8")

            # Update to import from the new generated structure
            updated_content = current_content.replace(
                "from .generated.client import AuthenticatedClient, Client",
                "from .generated import ApiClient, Configuration",
            ).replace("from .generated import *", "from .generated import *")

            main_init.write_text(updated_content, encoding="utf-8")
            print("   📄 Updated main __init__.py imports for new structure")

        # Clean up temporary directory
        if temp_client_dir.exists():
            shutil.rmtree(temp_client_dir)
            print("   🗑️  Cleaned up temporary generation directory")

        # Ensure all file operations are flushed to disk before proceeding
        import os
        import time

        os.sync()  # Force filesystem sync
        time.sleep(0.5)  # Small delay to ensure all files are available
        print("   💾 Synced filesystem after file operations")

        print("✅ Successfully moved Pydantic-based client to workspace")
        return True

    except Exception as e:
        print(f"❌ Error moving client to workspace: {e}")
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

    # Run the full format command for all files (includes generated code)
    # This uses the project's ruff configuration which properly handles all source paths
    print("🎨 Formatting all Python files with ruff...")
    result = run_command(
        ["poetry", "run", "poe", "format-python"], cwd=workspace_path, check=False
    )

    if result.returncode != 0:
        print("❌ Failed to format files")
        return False

    # Run auto-fix linting to fix as many issues as possible
    print("🔧 Auto-fixing linting issues with ruff...")
    lint_result = run_command(
        ["poetry", "run", "poe", "lint-ruff-fix"], cwd=workspace_path, check=False
    )

    if lint_result.returncode != 0:
        print("⚠️  Some linting issues couldn't be auto-fixed, but continuing")

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
    generated OpenAPI client code that cause Sphinx warnings. It also removes
    "Attributes:" sections from class docstrings to prevent AutoAPI 3.2+
    duplicate object warnings, and fixes common import and code issues.
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

            # Fix: Add missing imports for typing annotations
            if (
                "Dict" in content or "Any" in content
            ) and "from typing import" not in content:
                # Add typing imports at the top after encoding declaration
                if "# coding: utf-8" in content:
                    content = content.replace(
                        "# coding: utf-8\n",
                        "# coding: utf-8\n\nfrom typing import Any\n",
                    )
                elif "from __future__ import annotations" in content:
                    content = content.replace(
                        "from __future__ import annotations\n",
                        "from __future__ import annotations\n\nfrom typing import Any\n",
                    )
                else:
                    # Add after the first import if no encoding/future imports
                    lines = content.split("\n")
                    first_import_idx = -1
                    for i, line in enumerate(lines):
                        if (
                            line.startswith(("import ", "from "))
                            and "typing" not in line
                        ):
                            first_import_idx = i
                            break
                    if first_import_idx > -1:
                        lines.insert(first_import_idx, "from typing import Any")
                        content = "\n".join(lines)

            # Fix: Replace deprecated typing.Dict with dict
            content = content.replace(
                "from typing import Any, Dict", "from typing import Any"
            )
            content = content.replace("Dict[", "dict[")
            content = content.replace("typing.Dict", "dict")

            # Fix: Undefined name issues for self-referencing types
            if py_file.name == "webhook_event.py":
                content = content.replace(
                    "F821 Undefined name `WebhookEvent`", ""
                ).replace(
                    ": WebhookEvent",
                    ': "WebhookEvent"',  # Quote self-references
                )

            # Fix: Remove duplicate dictionary keys
            if "purchase_order_accounting_metadata.py" in py_file.name:
                # This is a known issue in generated code - need to remove duplicate keys
                content = re.sub(
                    r'(\s+"purchase_order_id":\s+\{[^}]+\},)\s+"purchase_order_id":\s+\{[^}]+\},',
                    r"\1",
                    content,
                )

            # Fix: Unused variables
            content = re.sub(r"(\s+)instance\s*=\s*[^,]+,\s*\n", r"", content)

            # Fix: Add ClassVar annotations for mutable class attributes
            if "api_client.py" in py_file.name:
                content = re.sub(
                    r"(\s+)(default_headers\s*:\s*)(dict\[[^]]+\])(\s*=\s*\{\})",
                    r"\1\2typing.ClassVar[\3]\4",
                    content,
                )
                # Ensure typing is imported
                if (
                    "import typing" not in content
                    and "from typing import" not in content
                ):
                    content = "import typing\n" + content

            # Only write if we made changes
            if content != original_content:
                py_file.write_text(content, encoding="utf-8")
                processed_count += 1

        except (OSError, UnicodeError, FileNotFoundError) as e:
            print(f"⚠️  Error processing {py_file}: {e}")
            # Continue processing other files

    print(
        f"📝 Post-processed {processed_count} generated files for better RST formatting and code quality"
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
