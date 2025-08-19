"""Generate the code reference pages and navigation."""

from pathlib import Path

import mkdocs_gen_files
from mkdocs_gen_files.nav import Nav

nav = Nav()

# Root package path
root = Path(__file__).parent.parent
src = root / "katana_public_api_client"

for path in sorted(src.rglob("*.py")):
    module_path = path.relative_to(root).with_suffix("")
    doc_path = path.relative_to(root).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)

    # Skip certain files
    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue

    # Skip test files and cache
    if any(part.startswith("test") or part == "__pycache__" for part in parts):
        continue

    # Add to navigation
    nav[parts] = doc_path.as_posix()

    # Create the documentation file
    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"# {ident}\n\n::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

# Write the navigation file
with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
