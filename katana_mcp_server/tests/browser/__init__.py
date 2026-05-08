"""Browser-based render tests for Katana MCP Prefab UI cards.

These tests spin up a minimal FastMCP server and fastmcp's ``apps_dev``
preview UI, then drive the rendered iframe via Playwright. They catch
runtime JS rendering failures in the Prefab renderer that the Python-side
unit tests cannot — specifically the failure mode that produced #629
(blank iframe on multi-state-bound DataTables).

Run with:
    uv run poe test-browser

First run requires::
    uv run playwright install chromium
"""
