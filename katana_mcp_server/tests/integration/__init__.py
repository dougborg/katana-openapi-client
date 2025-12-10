"""Integration tests for Katana MCP Server.

These tests verify end-to-end workflows against the real Katana API.
They require KATANA_API_KEY environment variable to be set.

Test categories:
- Inventory workflow: search → get details → check stock
- Purchase order workflow: create PO → receive items
- Manufacturing workflow: create MO → fulfill order
- Error scenarios: authentication, validation, API errors
"""
