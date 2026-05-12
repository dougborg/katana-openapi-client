"""Browser render tests for state-bound DataTable cards beyond the
modification surface.

After #629 surfaced ``rows="bare-string"`` as broken, all 5 state-bound
DataTable callsites in ``prefab_ui.py`` were mustache-wrapped. The
modification card got dedicated coverage in
``test_modification_render.py``; this file pins the other 4 — symmetric
proof that the audit fix actually renders, not just passes the
``_assert_state_bindings_resolve`` contract check.

If any of these break, the failure mode is the same as #629: the iframe
loads but the body stays empty (zero ``table`` elements). Each test
asserts a positive count of rendered rows.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.browser


class TestOtherCardsRender:
    """Verify state-bound DataTables outside the modification surface
    actually render. Catches regressions in the audit fix from #634."""

    def test_search_results_renders(self, render_scenario):
        """``build_search_results_ui`` — rows='{{ items }}' with 50 entries.

        Pre-mustache-fix this rendered as a blank iframe; post-fix it
        renders the table with all 50 items (paginated, so the visible
        count depends on page_size=20).
        """
        frame = render_scenario("search_results")
        assert frame.locator("table").count() == 1, (
            "search_results card failed to render — DataTable missing"
        )
        # First page: header + 20 items (pageSize=20).
        # Just assert there's a positive row count — the exact number
        # depends on pagination + which page renders first.
        assert frame.locator("table tr").count() >= 5
        # SKUs from the test fixture should be visible.
        assert frame.locator("text=SKU-0000").count() >= 1

    def test_inventory_check_renders(self, render_scenario):
        """``build_inventory_check_ui`` — rows='{{ stock.by_location }}'.

        Path-expression form (``stock.by_location``) — the mustache
        wrapper must support dot-notation. Renders a Metrics row plus a
        per-location DataTable.
        """
        frame = render_scenario("inventory_check")
        # Multi-location split → DataTable plus the Metric tiles.
        assert frame.locator("table").count() == 1
        # 2 locations + header.
        assert frame.locator("table tr").count() >= 3
        assert frame.locator("text=Main Warehouse").count() >= 1
        assert frame.locator("text=East Warehouse").count() >= 1

    def test_verification_renders(self, render_scenario):
        """``build_verification_ui`` — two state-bound DataTables in one
        card (rows='{{ matches }}' and rows='{{ discrepancies }}').

        Both must render. Pre-fix this would fail on the first one and
        leave the body empty; post-fix both should populate.
        """
        frame = render_scenario("verification")
        # 2 DataTables (matches + discrepancies).
        assert frame.locator("table").count() == 2
        # Match rows visible.
        assert frame.locator("text=SKU-A").count() >= 1
        assert frame.locator("text=SKU-B").count() >= 1
        # Discrepancy row visible.
        assert frame.locator("text=SKU-C").count() >= 1
        assert frame.locator("text=qty_mismatch").count() >= 1

    def test_batch_recipe_update_renders(self, render_scenario):
        """``build_batch_recipe_update_ui`` — rows='{{ rows }}' over 5
        sub-ops grouped by ``group_label``.
        """
        frame = render_scenario("batch_recipe_update")
        assert frame.locator("table").count() == 1
        # 5 sub-ops + header.
        assert frame.locator("table tr").count() >= 6
        # SKU strings from the test fixture.
        assert frame.locator("text=SKU-OLD-0").count() >= 1
