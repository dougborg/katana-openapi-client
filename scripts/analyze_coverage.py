#!/usr/bin/env python3
"""
Analyze test coverage, separating generated code from core logic.

This script helps understand the true test coverage for the codebase by
categorizing files into generated (which don't need high coverage) and
core logic (which should have high coverage).

Usage:
    poetry run python scripts/analyze_coverage.py

    # Or with coverage report:
    poetry run pytest --cov=katana_public_api_client --cov-report=json -m 'not docs' -q
    poetry run python scripts/analyze_coverage.py
"""

import json
import sys
from pathlib import Path
from typing import Any, TypedDict


class FileStats(TypedDict):
    """Statistics for a single file."""

    statements: int
    covered: int
    missing: int
    percent: float


class CategoryStats(TypedDict):
    """Statistics for a category of files."""

    file_count: int
    statements: int
    covered: int
    missing: int
    percent: float
    files: list[tuple[str, FileStats]]


def categorize_file(file_path: str) -> str:
    """
    Categorize a file into generated or core logic.

    Args:
        file_path: Path to the file relative to project root

    Returns:
        Category name: 'generated_api', 'generated_models', 'core_logic', or 'other'
    """
    if "katana_public_api_client/api/" in file_path:
        return "generated_api"
    elif "katana_public_api_client/models/" in file_path:
        return "generated_models"
    elif file_path in [
        "katana_public_api_client/katana_client.py",
        "katana_public_api_client/utils.py",
        "katana_public_api_client/client.py",
        "katana_public_api_client/log_setup.py",
        "katana_public_api_client/__init__.py",
    ]:
        return "core_logic"
    elif "katana_public_api_client/client_types.py" in file_path:
        return "generated_types"
    elif "katana_public_api_client/errors.py" in file_path:
        return "generated_errors"
    else:
        return "other"


def load_coverage_data() -> dict[str, Any] | None:
    """Load coverage data from coverage.json if it exists."""
    coverage_file = Path("coverage.json")
    if not coverage_file.exists():
        return None

    with open(coverage_file) as f:
        return json.load(f)


def analyze_coverage() -> dict[str, CategoryStats]:
    """
    Analyze coverage data and categorize by file type.

    Returns:
        Dictionary mapping category name to statistics
    """
    coverage_data = load_coverage_data()
    if not coverage_data:
        print("❌ No coverage.json found. Run tests with --cov-report=json first:")
        print(
            "   poetry run pytest --cov=katana_public_api_client"
            " --cov-report=json -m 'not docs'"
        )
        sys.exit(1)

    # Initialize categories
    categories: dict[str, CategoryStats] = {
        "generated_api": {
            "file_count": 0,
            "statements": 0,
            "covered": 0,
            "missing": 0,
            "percent": 0.0,
            "files": [],
        },
        "generated_models": {
            "file_count": 0,
            "statements": 0,
            "covered": 0,
            "missing": 0,
            "percent": 0.0,
            "files": [],
        },
        "generated_types": {
            "file_count": 0,
            "statements": 0,
            "covered": 0,
            "missing": 0,
            "percent": 0.0,
            "files": [],
        },
        "generated_errors": {
            "file_count": 0,
            "statements": 0,
            "covered": 0,
            "missing": 0,
            "percent": 0.0,
            "files": [],
        },
        "core_logic": {
            "file_count": 0,
            "statements": 0,
            "covered": 0,
            "missing": 0,
            "percent": 0.0,
            "files": [],
        },
        "other": {
            "file_count": 0,
            "statements": 0,
            "covered": 0,
            "missing": 0,
            "percent": 0.0,
            "files": [],
        },
    }

    # Process each file
    files_data = coverage_data.get("files", {})
    for file_path, file_data in files_data.items():
        summary = file_data.get("summary", {})
        statements = summary.get("num_statements", 0)
        covered = summary.get("covered_lines", 0)
        missing = statements - covered
        percent = summary.get("percent_covered", 0.0)

        # Skip files with no statements
        if statements == 0:
            continue

        # Categorize
        category = categorize_file(file_path)
        cat_stats = categories[category]

        cat_stats["file_count"] += 1
        cat_stats["statements"] += statements
        cat_stats["covered"] += covered
        cat_stats["missing"] += missing
        cat_stats["files"].append(
            (
                file_path,
                {
                    "statements": statements,
                    "covered": covered,
                    "missing": missing,
                    "percent": percent,
                },
            )
        )

    # Calculate percentages
    for stats in categories.values():
        if stats["statements"] > 0:
            stats["percent"] = (stats["covered"] / stats["statements"]) * 100

    return categories


def print_summary(categories: dict[str, CategoryStats]) -> None:
    """Print a formatted summary of coverage by category."""
    print("\n" + "=" * 80)
    print("COVERAGE ANALYSIS - Generated vs. Core Logic")
    print("=" * 80 + "\n")

    # Overall totals
    total_files = sum(c["file_count"] for c in categories.values())
    total_statements = sum(c["statements"] for c in categories.values())
    total_covered = sum(c["covered"] for c in categories.values())
    total_percent = (
        (total_covered / total_statements * 100) if total_statements > 0 else 0
    )

    print(f"📊 Overall Coverage: {total_percent:.1f}%")
    print(f"   Total Files: {total_files}")
    print(f"   Total Statements: {total_statements:,}")
    print(f"   Covered: {total_covered:,}")
    print(f"   Missing: {total_statements - total_covered:,}\n")

    # Category breakdown
    print("📁 Coverage by Category:\n")

    for category_name, stats in categories.items():
        if stats["file_count"] == 0:
            continue

        # Pick emoji and label
        if category_name.startswith("generated"):
            emoji = "🤖"
            label = category_name.replace("_", " ").title()
            note = "(low coverage OK - generated code)"
        elif category_name == "core_logic":
            emoji = "⚙️"
            label = "Core Logic"
            note = "(target: 70%+)"
        else:
            emoji = "📄"
            label = category_name.title()
            note = ""

        print(f"{emoji} {label}:")
        print(f"   Files: {stats['file_count']}")
        print(f"   Statements: {stats['statements']:,}")
        print(f"   Coverage: {stats['percent']:.1f}% {note}")
        print()

    # Core logic detail
    core_stats = categories["core_logic"]
    if core_stats["file_count"] > 0:
        print("\n" + "-" * 80)
        print("⚙️  CORE LOGIC DETAIL (Target: 70%+)")
        print("-" * 80 + "\n")

        # Sort by coverage percentage
        sorted_files = sorted(core_stats["files"], key=lambda x: x[1]["percent"])

        for file_path, file_stats in sorted_files:
            filename = file_path.split("/")[-1]
            percent = file_stats["percent"]
            covered = file_stats["covered"]
            total = file_stats["statements"]

            # Status indicator
            if percent >= 70:
                status = "✅"
            elif percent >= 50:
                status = "⚠️"
            else:
                status = "❌"

            print(f"{status} {filename:30} {percent:5.1f}% ({covered}/{total})")

    # Summary and recommendations
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80 + "\n")

    core_percent = core_stats["percent"]
    if core_percent >= 70:
        print("✅ Core logic coverage is good (>= 70%)")
    elif core_percent >= 50:
        print("⚠️  Core logic coverage is moderate (50-70%)")
        print("   → Aim to add more tests for core logic files")
    else:
        print("❌ Core logic coverage is low (< 50%)")
        print("   → Priority: Add comprehensive tests for core logic")

    # Identify specific files needing work
    low_coverage_files = [
        (path, stats) for path, stats in core_stats["files"] if stats["percent"] < 70
    ]

    if low_coverage_files:
        print("\n📋 Files needing better coverage (< 70%):")
        for file_path, file_stats in sorted(
            low_coverage_files, key=lambda x: x[1]["percent"]
        ):
            filename = file_path.split("/")[-1]
            print(f"   • {filename:30} {file_stats['percent']:5.1f}%")

    print("\n💡 Tips:")
    print("   • Generated code (api/, models/) doesn't need high coverage")
    print("   • Focus testing efforts on core logic files")
    print("   • Aim for 70%+ coverage on katana_client.py and utils.py")
    print("   • See issue #31 for detailed testing roadmap")
    print()


def main() -> None:
    """Main entry point."""
    categories = analyze_coverage()
    print_summary(categories)

    # Exit code based on core logic coverage
    core_percent = categories["core_logic"]["percent"]
    if core_percent < 50:
        sys.exit(1)  # Fail if core coverage is too low
    sys.exit(0)


if __name__ == "__main__":
    main()
