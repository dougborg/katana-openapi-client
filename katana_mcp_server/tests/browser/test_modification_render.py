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

    def test_apply_button_ticks_rows_live(self, render_scenario):
        """Click-through live-tick: Confirm fires the apply call, the
        on_success chain pushes RESULT.actions into state.plan_actions,
        and rows transition from PLANNED to APPLIED in place.

        The stub ``modify_manufacturing_order`` tool in
        ``render_test_server.py`` returns a canned applied response.

        Waits on the observable post-state condition (12 APPLIED cells
        present) rather than a fixed timeout — fast on warm CI, robust
        on slow CI, deterministic-fail if the live-tick path breaks.
        """
        frame = render_scenario("modify_mo_12_actions_preview")

        # Pre-state: 12 PLANNED, 0 APPLIED.
        assert frame.locator("td").filter(has_text="PLANNED").count() == 12
        assert frame.locator("td").filter(has_text="APPLIED").count() == 0

        # Fire the Confirm button.
        frame.locator("button").filter(has_text="Confirm").first.click()

        # Wait for the live-tick to land — first APPLIED cell to become
        # visible. ``wait_for`` polls with a 30s default timeout, so this
        # completes ~immediately when the apply round-trip succeeds and
        # fails deterministically if the on_success chain is broken.
        frame.locator("td").filter(has_text="APPLIED").first.wait_for(
            state="visible", timeout=30000
        )

        # Post-state: 0 PLANNED, 12 APPLIED.
        assert frame.locator("td").filter(has_text="PLANNED").count() == 0, (
            "Live-tick failed — Confirm click did not push RESULT.actions "
            "into state.plan_actions, so rows stayed PLANNED. Check the "
            "on_success chain in _build_apply_action_direct."
        )
        assert frame.locator("td").filter(has_text="APPLIED").count() == 12
