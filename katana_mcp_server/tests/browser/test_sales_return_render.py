"""Browser-render coverage for the sales-return deletion card."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.browser


class TestSalesReturnDeleteRender:
    def test_delete_preview_renders_identifying_details(self, render_scenario):
        frame = render_scenario("sales_return_delete_preview")

        assert frame.locator("text=Delete Sales Return").count() >= 1
        assert frame.locator("text=RO-8101").count() >= 1
        assert frame.locator("text=Rows").count() >= 1
        assert frame.locator("button").filter(has_text="Confirm").count() >= 1

    def test_delete_applied_hides_confirmation(self, render_scenario):
        frame = render_scenario("sales_return_delete_applied")

        assert frame.locator("text=DELETED").count() >= 1
        assert frame.locator("button").filter(has_text="Confirm").count() == 0
