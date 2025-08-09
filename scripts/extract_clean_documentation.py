#!/usr/bin/env python3
"""
Extract clean documentation content from harvested Katana API HTML files.

This script processes the verbose HTML files downloaded from the Katana API reference
and extracts only the essential documentation content, removing all the README.io
infrastructure, styling, scripts, and other overhead.
"""

import asyncio
import json
from pathlib import Path
from typing import Any

import aiofiles
from bs4 import BeautifulSoup
from bs4.element import Tag


async def extract_content_from_html(
    html_content: str, file_path: Path
) -> dict[str, Any] | None:
    """
    Extract clean content from a single HTML file.

    Args:
        html_content: Raw HTML content
        file_path: Path to the HTML file for context

    Returns:
        Dictionary with extracted content or None if extraction fails
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")

        # Try to find content in multiple possible structures
        content_div = None
        content_source = "unknown"

        # First try: Original structure with rm-Markdown div
        content_div = soup.find("div", class_="rm-Markdown markdown-body content-body")
        if content_div and isinstance(content_div, Tag):
            content_source = "rm-Markdown"
        else:
            # Second try: Article tag structure
            content_div = soup.find("article", class_="rm-Article")
            if content_div and isinstance(content_div, Tag):
                content_source = "rm-Article"

        if not content_div or not isinstance(content_div, Tag):
            print(f"Warning: No main content found in {file_path}")
            return None

        # Extract title from h1 in the header
        title = None
        header = soup.find("header", id="content-head")
        if header and isinstance(header, Tag):
            h1 = header.find("h1")
            if h1 and isinstance(h1, Tag):
                title = h1.get_text(strip=True)

        # If no title found in header, look for h1 in content
        if not title:
            h1_in_content = content_div.find("h1")
            if h1_in_content and isinstance(h1_in_content, Tag):
                title = h1_in_content.get_text(strip=True)

        # Extract URL/endpoint info from filename
        filename = file_path.stem
        if filename.startswith("reference_"):
            endpoint_slug = filename[10:]  # Remove 'reference_' prefix
        else:
            endpoint_slug = filename

        # Clean up the content HTML - remove unnecessary attributes but keep structure
        # Remove data attributes, classes that are just styling, etc.
        for element in content_div.find_all(True):
            if not isinstance(element, Tag):
                continue

            tag = element
            # Keep essential attributes like href, id (for anchors), but remove styling classes
            attrs_to_keep = []
            if tag.name == "a" and tag.get("href"):
                attrs_to_keep.append(("href", str(tag["href"])))
            if tag.get("id"):
                attrs_to_keep.append(("id", str(tag["id"])))
            if tag.name in ["table", "th", "td"] and tag.get("align"):
                attrs_to_keep.append(("align", str(tag["align"])))

            # Clear all attributes and add back only the essential ones
            tag.attrs.clear()
            for attr_name, attr_value in attrs_to_keep:
                tag[attr_name] = attr_value

        # Get the cleaned HTML content
        content_html = str(content_div)

        # Also get plain text version for search/indexing
        content_text = content_div.get_text(separator="\n", strip=True)

        return {
            "title": title or "Untitled",
            "endpoint_slug": endpoint_slug,
            "html_content": content_html,
            "text_content": content_text,
            "original_file": str(file_path),
            "content_length": len(content_text),
            "content_source": content_source,
        }

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


async def process_html_file(file_path: Path, output_dir: Path) -> dict[str, Any] | None:
    """
    Process a single HTML file and save the extracted content.

    Args:
        file_path: Path to the HTML file
        output_dir: Directory to save cleaned content

    Returns:
        Metadata about the processed file
    """
    try:
        async with aiofiles.open(file_path, encoding="utf-8") as f:
            html_content = await f.read()

        # Extract clean content
        extracted = await extract_content_from_html(html_content, file_path)
        if not extracted:
            return None

        # Save as cleaned HTML file
        output_file = output_dir / f"{extracted['endpoint_slug']}.html"
        async with aiofiles.open(output_file, "w", encoding="utf-8") as f:
            await f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>{extracted["title"]}</title>
    <meta charset="utf-8">
    <meta name="source" content="Katana API Reference">
</head>
<body>
{extracted["html_content"]}
</body>
</html>""")

        # Save as markdown-style text file as well
        text_file = output_dir / f"{extracted['endpoint_slug']}.md"
        async with aiofiles.open(text_file, "w", encoding="utf-8") as f:
            await f.write(f"# {extracted['title']}\n\n{extracted['text_content']}")

        print(
            f"✓ Processed {file_path.name} -> {output_file.name} ({extracted['content_length']} chars)"
        )

        return {
            "title": extracted["title"],
            "endpoint_slug": extracted["endpoint_slug"],
            "html_file": str(output_file),
            "text_file": str(text_file),
            "content_length": extracted["content_length"],
            "original_file": str(file_path),
        }

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None


async def main():
    """Main function to process all HTML files and extract clean documentation."""

    # Setup paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    docs_dir = project_root / "docs" / "katana-api-reference"
    output_dir = project_root / "docs" / "katana-api-clean"

    # Create output directory
    output_dir.mkdir(exist_ok=True)

    print(f"Looking for HTML files in: {docs_dir}")
    print(f"Output directory: {output_dir}")

    # Find all HTML files
    html_files = list(docs_dir.glob("*.html"))
    if not html_files:
        print("No HTML files found!")
        return

    print(f"Found {len(html_files)} HTML files to process")

    # Process files concurrently
    semaphore = asyncio.Semaphore(10)  # Limit concurrent file operations

    async def process_with_semaphore(file_path):
        async with semaphore:
            return await process_html_file(file_path, output_dir)

    tasks = [process_with_semaphore(file_path) for file_path in html_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter successful results
    successful_results = [r for r in results if isinstance(r, dict) and r is not None]

    print(f"\n✓ Successfully processed {len(successful_results)} files")
    print(f"✗ Failed to process {len(html_files) - len(successful_results)} files")

    # Save index of processed files
    index_file = output_dir / "clean_docs_index.json"
    async with aiofiles.open(index_file, "w", encoding="utf-8") as f:
        index_data = {
            "processed_count": len(successful_results),
            "total_files": len(html_files),
            "files": successful_results,
            "total_content_length": sum(
                int(r["content_length"]) for r in successful_results
            ),
        }
        await f.write(json.dumps(index_data, indent=2))

    print(f"\n📋 Index saved to: {index_file}")

    # Show statistics
    total_content = sum(int(r["content_length"]) for r in successful_results)
    print("📊 Statistics:")
    print(f"  - Total clean content: {total_content:,} characters")
    print(
        f"  - Average per file: {total_content // len(successful_results):,} characters"
    )
    print(
        f"  - Largest file: {max(int(r['content_length']) for r in successful_results):,} characters"
    )
    print(
        f"  - Smallest file: {min(int(r['content_length']) for r in successful_results):,} characters"
    )

    # Create a README for the clean docs
    readme_file = output_dir / "README.md"
    async with aiofiles.open(readme_file, "w", encoding="utf-8") as f:
        await f.write(f"""# Katana API Clean Documentation

This directory contains cleaned and optimized documentation extracted from the Katana API reference.

## Overview

- **Source**: Katana API Reference (https://developer.katanamrp.com/reference/)
- **Processed Files**: {len(successful_results)} files
- **Total Content**: {total_content:,} characters
- **Generated**: {asyncio.get_event_loop().time()}

## Files

Each endpoint is available in two formats:
- `.html` - Clean HTML with minimal styling
- `.md` - Markdown-compatible text format

## Purpose

These files are optimized for:
- AI/LLM consumption for schema improvement
- Fast loading and parsing
- Minimal file sizes
- Essential content only

## Original Sources

The original verbose HTML files (2MB+ each) contained extensive README.io infrastructure,
styling, JavaScript, and tracking code. This cleaned version focuses only on the
API documentation content itself.

## Usage

Reference these files when improving OpenAPI schema descriptions and examples.
The content provides authoritative descriptions for all Katana API endpoints.
""")

    print(f"📖 README created: {readme_file}")
    print("\n🎉 Documentation extraction complete!")


if __name__ == "__main__":
    asyncio.run(main())
