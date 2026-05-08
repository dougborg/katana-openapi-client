"""Browser render tests for the modification card.

These run the actual Prefab JS renderer against our card builders and
assert the rendered DOM. Catches the bug class that #629 surfaced —
runtime JS errors that the Python-side unit tests cannot detect.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.browser


class TestModificationCardRender:
    """Verify the modification card builders render correctly in a real browser."""

    def test_trivial_card_renders(self, render_scenario):
        """Sanity: a minimal Card+Text app renders. If this fails the
        whole harness is broken — fix that before debugging anything else.
        """
        frame = render_scenario("trivial_text")
        assert frame.locator("text=Trivial Test").count() == 1, (
            "trivial card baseline broken — apps_dev pipeline not working"
        )

    def test_state_bound_datatable_requires_mustache(self, render_scenario):
        """Pin the bare-string-vs-mustache contract. Bare-string state
        references crash the renderer; mustache form works. The card
        builders in :mod:`prefab_ui` must always emit mustache form.
        """
        bare = render_scenario("datatable_state")
        # Bare-string ref triggers ``t.some is not a function`` — body is empty.
        assert bare.locator("table").count() == 0, (
            "bare-string state ref unexpectedly rendered — renderer "
            "behavior changed; revisit the assertion in "
            "_assert_state_bindings_resolve."
        )

        templated = render_scenario("datatable_state_template")
        assert templated.locator("table").count() == 1
        assert templated.locator("td").count() >= 4  # 2 rows x 2 cells

    def test_modify_single_action_preview_renders(self, render_scenario):
        """Single-action modify card: 1 action row, Confirm button visible."""
        frame = render_scenario("modify_item_single_preview")
        assert frame.locator("table").count() == 1
        # Header + 1 action row.
        assert frame.locator("table tr").count() == 2
        assert frame.locator("text=PLANNED").count() >= 1
        assert frame.locator("button").filter(has_text="Confirm").count() == 1

    def test_modify_twelve_actions_preview_renders(self, render_scenario):
        """Reproduces #629: 12-action mixed plan must render all rows.

        Pre-fix this rendered as a blank iframe. With the mustache fix
        and one-DataTable design, all 12 rows show with PLANNED status.
        """
        frame = render_scenario("modify_mo_12_actions_preview")
        assert frame.locator("table").count() == 1
        # Header + 12 action rows.
        assert frame.locator("table tr").count() == 13
        # Every action shows PLANNED (none have been applied yet).
        assert frame.locator("td").filter(has_text="PLANNED").count() == 12

    def test_modify_twelve_actions_applied_renders(self, render_scenario):
        """Result card after a successful apply: all 12 rows APPLIED."""
        frame = render_scenario("modify_mo_12_actions_applied")
        assert frame.locator("table").count() == 1
        assert frame.locator("table tr").count() == 13
        # Every action shows APPLIED (verified).
        assert frame.locator("td").filter(has_text="APPLIED").count() == 12

    def test_apply_button_morphs_card_to_applied_state(self, render_scenario):
        """Click-through: Confirm fires the apply call, the on_success
        chain flips ``state.applied=True``, and the footer/badge row
        morphs to its applied state.

        The pinned-here behavior is the conservative apply UX — the row
        cells stay PLANNED because ``$result.actions`` doesn't resolve
        in the on_success Rx context (see in-code comment in
        ``build_modification_preview_ui``). A live-tick UX where rows
        transition PLANNED → APPLIED in place is tracked as a follow-up
        once the right Rx path is identified.

        The stub ``modify_manufacturing_order`` tool in
        ``render_test_server.py`` matches production wire shape via
        ``make_tool_result``, so this test fails the same way production
        would if the apply path regresses.
        """
        frame = render_scenario("modify_mo_12_actions_preview")

        # Pre-state: 12 PLANNED, 0 APPLIED, "Applying..." badge absent,
        # "Applied" footer pill absent.
        assert frame.locator("td").filter(has_text="PLANNED").count() == 12
        assert frame.locator("text=Applied").count() == 0

        # Fire the Confirm button.
        frame.locator("button").filter(has_text="Confirm").first.click()

        # Wait for the applied-state morph: the "Applied" pill in the
        # button row appears once on_success fires. ``wait_for`` polls
        # with a 30s timeout — completes fast when the apply succeeds,
        # fails deterministically if the on_success chain is broken.
        frame.locator("text=Applied").first.wait_for(state="visible", timeout=30000)

        # The Confirm button is now disabled (state.applied gates it via
        # the ``locked`` Rx in ``_render_apply_button_row``).
        confirm = frame.locator("button").filter(has_text="Confirm").first
        assert confirm.is_disabled()
