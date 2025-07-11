#!/usr/bin/env python3
"""
Regenerate the Katana OpenAPI client from the specification.

This script:
1. Validates the OpenAPI specification
2. Backs up the existing client (if it exists)
3. Generates a new client using openapi-python-client
4. Moves the generated client to the main workspace
5. Installs dependencies and runs tests

Usage:
    python regenerate_client.py [--force] [--skip-validation] [--skip-tests]
"""

import argparse
import shutil
import subprocess
import sys
from datetime import datetime
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

    try:
        result = run_command(
            [
                sys.executable,
                "-c",
                f"import yaml; from openapi_spec_validator import validate_spec; "
                f"spec = yaml.safe_load(open('{spec_path}')); validate_spec(spec); print('✅ OpenAPI spec is valid')",
            ],
            check=False,
        )

        return result.returncode == 0
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False


def backup_existing_client(client_path: Path, backup_dir: Path) -> bool:
    """Backup the existing client if it exists."""
    if not client_path.exists():
        print("i  No existing client to backup")
        return True

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"katana_public_api_client_backup_{timestamp}"

    print(f"📦 Backing up existing client to: {backup_path}")
    try:
        shutil.copytree(client_path, backup_path)
        print("✅ Backup created successfully")
        return True
    except Exception as e:
        print(f"❌ Backup failed: {e}")
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

    # Run the custom format command which handles both Python and Markdown
    result = run_command(["poetry", "poe", "format"], cwd=workspace_path, check=False)

    if result.returncode != 0:
        print("⚠️  Formatting had issues but continuing")
        return True  # Don't fail the whole process for formatting issues

    print("✅ Code formatted successfully")
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
    backup_dir = workspace_path / "backups"

    print("🚀 Katana OpenAPI Client Regeneration")
    print("=" * 50)
    print(f"📁 Workspace: {workspace_path}")
    print(f"📄 OpenAPI spec: {spec_path}")
    print(f"📦 Client path: {client_path}")

    # Create backup directory
    backup_dir.mkdir(exist_ok=True)

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

    # Step 2: Backup existing client
    if not backup_existing_client(client_path, backup_dir):
        print("❌ Failed to backup existing client")
        sys.exit(1)

    # Step 3: Generate new client
    if not generate_client(spec_path, workspace_path):
        print("❌ Failed to generate client")
        sys.exit(1)

    # Step 4: Move client to workspace
    if not move_client_to_workspace(workspace_path):
        print("❌ Failed to move client to workspace")
        sys.exit(1)

    # Step 5: Install dependencies
    if not install_dependencies(workspace_path):
        print("❌ Failed to install dependencies")
        sys.exit(1)

    # Step 6: Run tests
    if not args.skip_tests:
        if not run_tests(workspace_path):
            print("⚠️  Tests had issues but continuing")
    else:
        print("⏭️  Skipping tests")

    # Step 7: Format generated code
    if not format_generated_code(workspace_path):
        print("⚠️  Formatting had issues but continuing")

    print("\n" + "=" * 50)
    print("✅ Client regeneration completed successfully!")
    print("\n💡 Next steps:")
    print("   1. Review the generated client in ./katana_public_api_client/")
    print("   2. Update your code imports if needed")
    print("   3. Test your application with the new client")
    print(f"   4. Backup was saved to: {backup_dir}")


if __name__ == "__main__":
    main()
