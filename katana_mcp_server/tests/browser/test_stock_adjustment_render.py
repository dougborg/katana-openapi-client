"""Browser render tests for the stock-adjustment cards.

Verifies the create / update / delete preview cards render correctly in a
real browser, plus the post-apply state for each. Closes #311 + most of
#639's audit gap.

Each tool gets a preview test (Confirm + Cancel buttons present, table
populated) and a result test (Confirm hidden, "View in Katana" present
when applicable, status badge flipped).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.browser


class TestStockAdjustmentCreateRender:
    def test_create_preview_renders_with_rows(self, render_scenario):
        """Preview card: 3-row stock adjustment renders with PREVIEW badge,
        DataTable populated, Confirm button visible.
        """
        frame = render_scenario("stock_adjustment_create_preview")
        # PREVIEW badge present
        assert frame.locator("text=PREVIEW").count() >= 1
        # 3 rows + header
        assert frame.locator("table").count() == 1
        assert frame.locator("table tr").count() == 4
        # Quantity column shows signed values
        assert frame.locator("td").filter(has_text="+1.0").count() >= 1
        # Confirm button present
        assert frame.locator("button").filter(has_text="Confirm").count() >= 1
        # Reason muted line
        assert frame.locator("text=Found one in stock").count() >= 1

    def test_create_applied_renders_view_button(self, render_scenario):
        """Result card: APPLIED badge, no Confirm button, View-in-Katana
        link present (response carries katana_url).
        """
        frame = render_scenario("stock_adjustment_create_applied")
        assert frame.locator("text=APPLIED").count() >= 1
        # 3 rows + header still visible
        assert frame.locator("table tr").count() == 4
        # No Confirm button on result card
        assert frame.locator("button").filter(has_text="Confirm").count() == 0
        # View in Katana button present
        assert frame.locator("button").filter(has_text="View in Katana").count() == 1


class TestStockAdjustmentUpdateRender:
    def test_update_preview_renders_field_changes(self, render_scenario):
        """Preview: PREVIEW badge, DataTable with changed field rows,
        Confirm button present.
        """
        frame = render_scenario("stock_adjustment_update_preview")
        assert frame.locator("text=PREVIEW").count() >= 1
        # The diff DataTable lists the changed fields by label.
        assert frame.locator("td").filter(has_text="Number").count() >= 1
        assert frame.locator("td").filter(has_text="Reason").count() >= 1
        assert frame.locator("button").filter(has_text="Confirm").count() >= 1

    def test_update_applied_renders_no_confirm(self, render_scenario):
        """Result card: UPDATED badge, no Confirm button, View-in-Katana
        link visible.
        """
        frame = render_scenario("stock_adjustment_update_applied")
        assert frame.locator("text=UPDATED").count() >= 1
        assert frame.locator("button").filter(has_text="Confirm").count() == 0
        assert frame.locator("button").filter(has_text="View in Katana").count() == 1


class TestStockAdjustmentDeleteRender:
    def test_delete_preview_renders_metrics(self, render_scenario):
        """Preview: PREVIEW badge, identifying Metric tiles (Number /
        Location / Rows), Confirm button present, irreversibility warning.
        """
        frame = render_scenario("stock_adjustment_delete_preview")
        assert frame.locator("text=PREVIEW").count() >= 1
        # Metric tiles render their labels.
        assert frame.locator("text=Number").count() >= 1
        assert frame.locator("text=Rows").count() >= 1
        # The number from the fixture.
        assert frame.locator("text=SA-FY26-Q2-001").count() >= 1
        # Confirm button present.
        assert frame.locator("button").filter(has_text="Confirm").count() >= 1
        # Irreversibility warning surfaces.
        assert (
            frame.locator("text=cannot be undone").count() >= 1
            or frame.locator("text=reverses the associated").count() >= 1
        )

    def test_delete_applied_renders_no_confirm(self, render_scenario):
        """Result card: DELETED badge, no Confirm button. No
        ``View in Katana`` button — the entity is gone server-side
        (Katana nulls the URL on successful delete).
        """
        frame = render_scenario("stock_adjustment_delete_applied")
        assert frame.locator("text=DELETED").count() >= 1
        assert frame.locator("button").filter(has_text="Confirm").count() == 0
