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

    def test_bom_modify_mixed_preview_renders_all_kinds(self, render_scenario):
        """#811 BOM modify card — a 5-row recipe + (1 add + 1 update + 2
        delete) plan renders the full table with every kind visible:
        existing rows untouched, added row's resolved SKU surfaces,
        updated row shows the diff arrow, deleted rows carry their
        original SKU + a PLANNED status.
        """
        frame = render_scenario("bom_modify_mixed_preview")
        assert frame.locator("table").count() == 1
        # Header product identity.
        assert frame.locator("text=Mayhem 140 Frame").count() >= 1
        # Added row's resolved SKU (the user-centric piece — #811's
        # acceptance criterion: no "Add Bom Row" placeholder).
        assert frame.locator("td").filter(has_text="FS90250").count() >= 1
        # Existing-untouched SKUs still in the table (frame raw + 2
        # surviving rows).
        assert frame.locator("td").filter(has_text="FRM-AL-140").count() >= 1
        # Deleted SKUs (still in the table with deleted kind).
        assert frame.locator("td").filter(has_text="PNT-MTB").count() >= 1
        # Plan summary line shows the per-kind tally.
        assert frame.locator("text=+1 added").count() >= 1
        assert frame.locator("text=~1 updated").count() >= 1
        assert frame.locator("text=-2 deleted").count() >= 1
        # Confirm button (preview state).
        assert frame.locator("button").filter(has_text="Confirm").count() == 1
        # Anti-pattern guard: no internal-ActionResult-model labels.
        assert frame.locator("td").filter(has_text="Add Bom Row").count() == 0
        assert frame.locator("td").filter(has_text="Update Bom Row").count() == 0
        assert frame.locator("td").filter(has_text="field(s) set").count() == 0

    def test_bom_modify_mixed_applied_renders_per_row_status(self, render_scenario):
        """Result card after a successful apply — every plan-derived row
        shows APPLIED in the Status column. Existing-untouched rows show
        no status (empty cell). Aggregate header badge says APPLIED.
        """
        frame = render_scenario("bom_modify_mixed_applied")
        assert frame.locator("table").count() == 1
        # Per-row APPLIED pills land in the Status column. The plan has
        # 4 actions (1 add + 1 update + 2 delete), so 4 APPLIED cells in
        # the rendered table.
        assert frame.locator("td").filter(has_text="APPLIED").count() >= 4

    def test_apply_button_morphs_card_to_applied_state(self, render_scenario):
        """Click-through: Confirm fires the apply call, the on_success
        chain flips ``state.applied=True``, and the button morphs from
        ``Confirm Changes`` into the applied-state primary button — per
        the button-state-machine design in ``_render_apply_button_row``
        (#755 "fold status into button"):

        - Preview: ``Confirm Changes`` (default variant, fires apply)
        - Applied + ``result.katana_url`` truthy: ``View in Katana``
          (success variant, opens link)
        - Applied no url: ``Applied`` (success variant, disabled)
        - Error: ``Retry`` (warning variant, re-fires apply)

        Pre-existing limitation: ``$result`` in the on_success Rx
        context resolves to the apply tool's ``structured_content`` (a
        PrefabApp wire envelope keyed by ``$prefab``/``view``/``state``),
        NOT the raw ``ModificationResponse``. So
        ``If("result.katana_url")`` evaluates against the envelope dict
        and finds no ``katana_url`` field — the Else branch fires and
        we get the "Applied" Button, not "View in Katana". This is the
        same Rx-context limitation that prevents ``RESULT.actions``
        from driving live-tick row morphs (see in-code comment in
        ``build_modification_preview_ui``). Both gaps will lift if/when
        the rail can extract the raw response payload from the apply.

        The test pins the *current* behavior: post-Confirm, the Confirm
        button is replaced with a post-apply Button — either "View in
        Katana" (when the envelope happens to expose a katana_url, which
        no production tool does today) or "Applied" (the fallback).
        Either pass the morph contract; both fail the morph regression.

        The stub ``modify_manufacturing_order`` tool in
        ``render_test_server.py`` matches production wire shape via
        ``make_tool_result``, so this test fails the same way production
        would if the apply path regresses.
        """
        frame = render_scenario("modify_mo_12_actions_preview")

        # Pre-state: 12 PLANNED actions, Confirm button visible, neither
        # post-apply primary visible.
        assert frame.locator("td").filter(has_text="PLANNED").count() == 12
        assert frame.locator("button").filter(has_text="Confirm").first.is_visible()
        assert frame.locator("button").filter(has_text="View in Katana").count() == 0
        # Use exact-match locator for "Applied" to avoid matching the
        # "Applied" inside the "Modification Applied" Muted footer text
        # that legacy ``build_modification_preview_ui`` renders.
        assert frame.locator("button[role='button']", has_text="Applied").count() == 0

        # Fire the Confirm button.
        frame.locator("button").filter(has_text="Confirm").first.click()

        # Wait for the applied-state morph: the Confirm button is
        # REPLACED with a post-apply primary Button. Whether the morph
        # lands on "View in Katana" or "Applied" depends on whether the
        # on_success Rx context exposes ``result.katana_url`` (today's
        # rail wraps the response in a PrefabApp envelope, so the
        # Else/"Applied" branch fires — but either button is acceptable
        # for "the morph succeeded").
        frame.locator(
            "button:has-text('View in Katana'), button:has-text('Applied')"
        ).first.wait_for(state="visible", timeout=30000)

        # After the morph, the original Confirm button is gone — the
        # If/Elif/Else state machine swapped the button slot to a
        # post-apply primary. (Cancel stays visible-but-disabled in
        # all terminal states so the row width stays stable.)
        assert frame.locator("button").filter(has_text="Confirm").count() == 0
