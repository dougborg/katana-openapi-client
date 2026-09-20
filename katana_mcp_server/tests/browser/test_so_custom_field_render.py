"""Sales-order confirmation shows header and inline-row field values."""

import pytest

pytestmark = pytest.mark.browser


@pytest.mark.parametrize("is_preview", [True, False])
def test_sales_order_custom_fields_are_visible(render_scenario, is_preview):
    frame = render_scenario(
        "so_custom_field_preview" if is_preview else "so_custom_field_applied"
    )
    fields = "{'00000000-0000-0000-0000-000000000001': 'Priority'}"
    assert frame.get_by_text(f"Custom fields: {fields}", exact=True).count() == 1
    assert frame.get_by_text(f"Item 1 custom fields: {fields}", exact=True).count() == 1
    assert frame.get_by_role(
        "button", name="Confirm & Create Sales Order"
    ).count() == int(is_preview)


def test_sales_order_explicit_clear_is_visible(render_scenario):
    frame = render_scenario("so_custom_field_clear_preview")
    assert frame.get_by_text("Custom fields: clear all values", exact=True).count() == 1
    assert (
        frame.get_by_text("Item 1 custom fields: clear all values", exact=True).count()
        == 1
    )
    assert frame.get_by_role("button", name="Confirm & Create Sales Order").is_enabled()
