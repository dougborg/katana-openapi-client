"""Definition confirmation cards mount with choices and accurate apply state."""

import pytest

pytestmark = pytest.mark.browser


def test_definition_preview_shows_active_and_retired_choices(render_scenario):
    frame = render_scenario("custom_field_update_preview")
    assert frame.get_by_text("Sales Rep", exact=True).count() == 1
    assert frame.get_by_text("Alex (active)", exact=True).count() == 1
    assert frame.get_by_text("Sam (retired)", exact=True).count() == 1
    assert frame.get_by_text("Taylor (active)", exact=True).count() == 1
    assert frame.get_by_role("button", name="Confirm & Update").is_enabled()
    assert frame.get_by_role("button", name="Cancel").count() == 1


def test_definition_applied_hides_confirmation(render_scenario):
    frame = render_scenario("custom_field_update_applied")
    assert frame.get_by_text("APPLIED", exact=True).count() == 1
    assert frame.get_by_role("button", name="Confirm & Update").count() == 0
    assert frame.get_by_text("Taylor (active)", exact=True).count() == 1


@pytest.mark.parametrize("is_preview", [True, False])
def test_definition_delete_states(render_scenario, is_preview):
    frame = render_scenario(
        "custom_field_delete_preview" if is_preview else "custom_field_delete_applied"
    )
    assert (
        frame.get_by_text(
            "Delete Sales Rep; values will no longer appear on records", exact=True
        ).count()
        == 1
    )
    assert frame.get_by_role("button", name="Confirm & Delete").count() == int(
        is_preview
    )
    assert (
        frame.get_by_text("PREVIEW" if is_preview else "APPLIED", exact=True).count()
        == 1
    )
