#!/usr/bin/env python3
"""
Compare AST of generated client code before and after regeneration to ensure structural consistency.
Usage:
  python scripts/check_generated_client_ast.py
"""

import ast
import os
import shutil
import subprocess
import sys
import tempfile


def copy_dir(src, dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def compare_ast(dir1, dir2):
    for root, _, files in os.walk(dir1):
        for f in files:
            if not f.endswith(".py"):
                continue
            path1 = os.path.join(root, f)
            rel = os.path.relpath(path1, dir1)
            path2 = os.path.join(dir2, rel)
            if not os.path.exists(path2):
                print(f"Missing generated file: {rel}", file=sys.stderr)
                return False
            with open(path1, encoding="utf-8") as f1:
                tree1 = ast.parse(f1.read())
            with open(path2, encoding="utf-8") as f2:
                tree2 = ast.parse(f2.read())
            if ast.dump(tree1, include_attributes=False) != ast.dump(
                tree2, include_attributes=False
            ):
                print(f"AST mismatch in {rel}", file=sys.stderr)
                return False
    return True


def main():
    src = "katana_public_api_client"
    with tempfile.TemporaryDirectory() as tmp:
        old = os.path.join(tmp, "old")
        copy_dir(src, old)
        # Regenerate client via poe task
        subprocess.run(
            ["poetry", "run", "poe", "regenerate-client"],
            check=True,
        )
        # Format generated code via poe task
        subprocess.run(
            ["poetry", "run", "poe", "format-python"],
            check=True,
        )
        if not compare_ast(old, src):
            print(
                "Generated client AST does not match committed version. Please regenerate and commit.",
                file=sys.stderr,
            )
            sys.exit(1)
    print("Generated client AST matches.")


if __name__ == "__main__":
    main()
