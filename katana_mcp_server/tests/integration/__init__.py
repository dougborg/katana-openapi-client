"""Integration tests for Katana MCP Server.

These tests verify end-to-end workflows against the real Katana API.
They require KATANA_API_KEY environment variable to be set.

TEST DATA ISOLATION
===================
Tests that create real data in Katana use a namespace strategy for isolation:

1. **Namespace Prefix**: All test data uses "MCPTEST-<session_id>-" prefix
   - Example SKU: "MCPTEST-abc123-WIDGET-001"
   - Example order number: "MCPTEST-abc123-PO-001"
   - Example name: "MCPTEST-abc123 Test Product"

2. **Automatic Cleanup**: The `tracked_test_session` fixture:
   - Tracks all resources created during a test
   - Automatically deletes them when the test completes (even on failure)
   - Cleans up in reverse order to handle dependencies

3. **Manual Cleanup**: If tests fail catastrophically, use:
   ```python
   from tests.integration.test_utils import cleanup_orphaned_test_data

   await cleanup_orphaned_test_data(client)
   ```

4. **Test Markers**:
   - `@pytest.mark.integration`: Test requires API access (skips without API key)
   - `@pytest.mark.creates_data`: Test creates real data (use tracked_test_session)

Test categories:
- Inventory workflow: search → get details → check stock
- Purchase order workflow: create PO → receive items
- Manufacturing workflow: create MO → fulfill order
- Error scenarios: authentication, validation, API errors
"""
