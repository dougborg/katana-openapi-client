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
        """Single-action generic modify card: 1 action row, Confirm visible.

        Uses an MO modify (still on the legacy generic card) now that item
        modify routes to its dedicated ``build_item_modify_ui`` (#726).
        """
        frame = render_scenario("modify_mo_single_preview")
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
        # Every action shows PLANNED (none have been applied yet). Use a
        # regex anchored to whole-cell content — the post-#card-ux
        # content-rich summary cell ("added: variant_id,
        # planned_quantity_per_unit, notes") would otherwise match the
        # case-insensitive substring "planned" inside the field name.
        import re

        assert (
            frame.locator("td").filter(has_text=re.compile(r"^PLANNED$")).count() == 12
        )

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

    def test_item_modify_mixed_preview_renders_dual_diff(self, render_scenario):
        """#726 item modify card — a header ``uom`` change + (1 variant add +
        1 update + 1 delete) renders both diff surfaces: the decorated header
        line and the variant diff table with every kind visible. The resolved
        supplier name surfaces (never a bare ``#id``).
        """
        frame = render_scenario("item_modify_mixed_preview")
        # Header identity + resolved supplier name (anti-pattern #7).
        assert frame.locator("text=Carbon Wheelset").count() >= 1
        assert frame.locator("text=Acme Carbon Co").count() >= 1
        # Header scalar diff arrow.
        assert frame.locator("text=pcs → set").count() >= 1
        # Variant diff table: added SKU (+ gutter), updated price arrow,
        # deleted SKU (- gutter).
        assert frame.locator("td").filter(has_text="WHL-CARB-DISC").count() >= 1
        assert frame.locator("td").filter(has_text="1200 → 1250").count() >= 1
        assert frame.locator("td").filter(has_text="WHL-CARB-650B").count() >= 1
        # Plan summary line.
        assert frame.locator("text=+1 added").count() >= 1
        assert frame.locator("text=~1 updated").count() >= 1
        assert frame.locator("text=-1 deleted").count() >= 1
        # Confirm button (preview state).
        assert frame.locator("button").filter(has_text="Confirm").count() == 1
        # Anti-pattern guard: no internal ActionResult labels leak.
        assert frame.locator("td").filter(has_text="Add Variant").count() == 0
        assert frame.locator("td").filter(has_text="field(s) set").count() == 0

    def test_item_modify_mixed_applied_renders_per_row_status(self, render_scenario):
        """#726 applied item modify card — every plan-derived variant row
        shows APPLIED in the Status column; the header badge says APPLIED.
        """
        frame = render_scenario("item_modify_mixed_applied")
        assert frame.locator("table").count() >= 1
        # 3 variant actions (add + update + delete) → 3 APPLIED status cells.
        assert frame.locator("td").filter(has_text="APPLIED").count() >= 3

    def test_po_modify_rows_preview_renders_line_item_table(self, render_scenario):
        """#722 follow-up — PO modify card line-item table renders the row CRUD
        that was previously dropped: added row's resolved SKU/name, updated
        row's qty diff arrow, deleted row's preserved identity, summary line.
        """
        frame = render_scenario("po_modify_rows_preview")
        # Header diff still present.
        assert frame.locator("text=RECEIVED").count() >= 1
        # Line-item section + table.
        assert frame.locator("text=Line items:").count() >= 1
        assert frame.locator("table").count() >= 1
        # Added row's resolved SKU/name (the content-drop fix — no bare id).
        assert frame.locator("td").filter(has_text="WASHER-M5").count() >= 1
        assert frame.locator("td").filter(has_text="M5 washer").count() >= 1
        # Updated row's qty diff arrow + deleted row identity.
        assert frame.locator("td").filter(has_text="10 → 15").count() >= 1
        assert frame.locator("td").filter(has_text="NUT-M5").count() >= 1
        # Summary line.
        assert frame.locator("text=+1 added").count() >= 1
        assert frame.locator("text=~1 updated").count() >= 1
        assert frame.locator("text=-1 deleted").count() >= 1
        # Anti-pattern guard: no internal ActionResult labels leak.
        assert frame.locator("td").filter(has_text="Add Row").count() == 0

    def test_po_modify_rows_applied_renders_per_row_status(self, render_scenario):
        """#722 follow-up — applied PO modify: the row actions (add + update +
        delete) show APPLIED in the line-item table's Status column.
        """
        frame = render_scenario("po_modify_rows_applied")
        assert frame.locator("table").count() >= 1
        # 3 row actions → 3 APPLIED status cells.
        assert frame.locator("td").filter(has_text="APPLIED").count() >= 3

    def test_mo_modify_preview_renders_three_collection_tables(self, render_scenario):
        """#721 Phase 4 — MO modify card renders all three collection diff
        tables (recipe / operation / production) + the header diff, with
        resolved recipe SKU + operation status diff, in a real browser.
        """
        frame = render_scenario("mo_modify_preview")
        # Header scalar diff.
        assert frame.locator("text=10 → 20").count() >= 1
        # Three collection sections.
        assert frame.locator("text=Recipe (ingredients):").count() >= 1
        assert frame.locator("text=Operations:").count() >= 1
        assert frame.locator("text=Productions:").count() >= 1
        # Recipe add resolved SKU (no bare id) + operation status diff.
        assert frame.locator("td").filter(has_text="WASHER").count() >= 1
        assert (
            frame.locator("td").filter(has_text="NOT_STARTED → COMPLETED").count() >= 1
        )
        # Three diff tables rendered.
        assert frame.locator("table").count() >= 3

    def test_mo_modify_applied_renders_per_row_status(self, render_scenario):
        """#721 Phase 4 — applied MO modify: collection row actions show APPLIED
        in their Status columns across the three tables.
        """
        frame = render_scenario("mo_modify_applied")
        assert frame.locator("table").count() >= 3
        # recipe add + operation update + production add → ≥3 APPLIED cells.
        assert frame.locator("td").filter(has_text="APPLIED").count() >= 3

    def test_so_modify_partial_failure_applied_renders(self, render_scenario):
        """#723 SO modify card — partial-failure applied state renders the
        card-level PARTIAL FAILURE badge, the per-action APPLIED / FAILED
        Badges in the Line items + Shipping fees sections, and the
        consolidated sub-entity failed-action Alert with retry coaching.

        Pins end-to-end browser-render correctness for the SO modify
        card's most complex state — multiple parallel sub-entity outcomes
        where some succeed and some fail.
        """
        frame = render_scenario("so_modify_partial_failure_applied")
        # Header carries the SO order_no badge.
        assert frame.locator("text=SO-2026-001").count() >= 1
        # Card-level PARTIAL FAILURE state Badge (the build-time outcome
        # bucketing — ``_summarize_apply_outcome`` reads the response
        # actions on the standalone-applied path).
        assert frame.locator("text=PARTIAL FAILURE").count() >= 1
        # Per-section headers — Line items and Shipping fees are present
        # because the plan touches both; Fulfillments and Addresses are
        # not (no actions, no section header).
        assert frame.locator("text=Line items:").count() >= 1
        assert frame.locator("text=Shipping fees:").count() >= 1
        # Per-action status pills surface APPLIED on the successful
        # actions; FAILED on the failed one. ``count() >= 1`` because
        # multiple APPLIED Badges (one for the row that succeeded plus
        # potentially the card-level chrome).
        assert frame.locator("text=APPLIED").count() >= 1
        assert frame.locator("text=FAILED").count() >= 1
        # Sub-entity failed-action Alert — title + retry-coaching tail.
        assert frame.locator("text=404 Not Found").count() >= 1
        assert frame.locator("text=modify_sales_order(id=42").count() >= 1

    def test_so_modify_partial_failure_morphs_preview_to_applied(self, render_scenario):
        """#723 / #858 — Click-through morph test for the SO modify card.

        The standalone-applied scenario seeds the partial-failure state
        slots directly in Python; a slot-name typo in the
        :func:`build_so_modify_ui` Confirm-button SetState chain would
        sneak past that test. This test wires the **preview→Confirm→
        on_success morph path** end to end:

        1. Render the SO modify preview card via
           ``so_modify_partial_failure_preview``.
        2. Confirm a baseline preview shape — Confirm button visible,
           no sub-entity failed-action Alert yet, no per-row FAILED
           Badge / ``✗`` gutter (preview rows render as PLANNED with no
           Badge).
        3. Click Confirm. The iframe re-issues ``modify_sales_order``
           with ``preview=False``; the stub tool in
           :mod:`render_test_server` returns the partial-failure apply
           response.
        4. After the morph lands, assert (a) the state-driven sub-entity
           failed-action Alert has appeared with the error text and (b)
           the per-row chrome has morphed — the failed row carries a
           FAILED Badge and the ``✗`` gutter (#858 finding A). Without
           the row-binding fix the row text + Badge stayed frozen on
           the preview-time PLANNED state.

        Each per-section row list lives in ``state.so_<section>_rows``
        (see ``_build_so_subentity_row_lists``) and renders via
        ``ForEach``. The on_success chain SetStates each section list
        from ``$result.state.so_<section>_rows`` so the row chrome
        re-paints in lockstep with the apply outcome.
        """
        frame = render_scenario("so_modify_partial_failure_preview")

        # Pre-state: Confirm button visible, no failure alert yet (the
        # preview seeds ``applied_subentity_failed_count=0`` so the If
        # gate is closed).
        assert frame.locator("button").filter(has_text="Confirm").first.is_visible()
        # The failed-row error text only shows when the Alert is open
        # (the morph hasn't fired yet, so the bound text is the empty
        # preview seed).
        assert frame.locator("text=404 Not Found").count() == 0
        # Per-row chrome: preview-time rows are PLANNED, so no per-row
        # FAILED Badge yet and no ✗ gutter. Pre-fix the per-row chrome
        # stayed frozen here even after Confirm.
        assert frame.locator("text=FAILED").count() == 0
        # The delete_row line item renders with the kind gutter (``-``)
        # at preview time, not the failure gutter (``✗``).
        assert frame.locator("text=✗ row #9999").count() == 0

        # Fire the Confirm button — re-issues ``modify_sales_order``
        # with ``preview=False``, the stub returns the partial-failure
        # apply response, and the on_success chain seeds the failed-
        # subentity state slots from ``$result.state.*``.
        frame.locator("button").filter(has_text="Confirm").first.click()

        # Wait for the morph: the failed-action error text from the
        # apply response surfaces inside the now-visible Alert.
        frame.locator("text=404 Not Found").first.wait_for(
            state="visible", timeout=30000
        )
        # Retry-coaching tail from ``_so_subentity_failed_summary``
        # (references the SO id via ``modify_sales_order(id=42, ...)``).
        assert frame.locator("text=modify_sales_order(id=42").count() >= 1
        # Row-binding morph (#858 finding A): the failed row's gutter
        # glyph flipped to ``✗`` and the per-row FAILED Badge appeared.
        # Pre-fix these stayed at the preview-time PLANNED chrome.
        frame.locator("text=✗ row #9999").first.wait_for(state="visible", timeout=10000)
        assert frame.locator("text=FAILED").count() >= 1

    def test_so_failed_delete_applied_renders_error_text(self, render_scenario):
        """#858 finding B — A failed top-level ``delete`` action renders
        the FAILED chrome AND surfaces the :attr:`ActionResult.error`
        text via the state-driven header-op Alert.

        Pre-fix the FAILED chrome rendered without the error message
        — delete actions have no field changes (so
        :func:`_render_failed_changes_block` was empty) and ``delete`` is
        filtered out of :func:`_so_subentity_failed_summary` (so that
        Alert was empty too). Operator saw "FAILED" with no way to tell
        why.

        Pins end-to-end browser-render correctness for the new
        header-op Alert.
        """
        frame = render_scenario("so_delete_failed_applied")
        # FAILED chrome (the state-driven header Badge).
        assert frame.locator("text=FAILED").count() >= 1
        # Sales Order Failed title suffix (driven by ``applied_title_suffix``
        # on the standalone-applied failure path).
        assert frame.locator("text=Sales Order Failed").count() >= 1
        # The new state-driven header-op Alert surfaces the
        # ActionResult.error text verbatim (the load-bearing fix for
        # finding B).
        assert frame.locator("text=Sales order operation failed").count() >= 1
        assert frame.locator("text=Failed to delete the sales order").count() >= 1
        # And the actual error string from the response.
        assert (
            frame.locator("text=404 Not Found: sales order 42 does not exist").count()
            >= 1
        )

    def test_so_failed_delete_morphs_preview_to_applied(self, render_scenario):
        """#858 finding B — Click-through morph: the failed-delete error
        text surfaces only after Confirm fires, driven by the on_success
        ``SetState`` chain seeding ``applied_header_failed_summary`` from
        ``$result.state.applied_header_failed_summary``.

        Mistyped slot names in either side of the chain would leave the
        Alert empty (the preview seed) even after the apply lands. This
        test catches the slot-name typo that the standalone-applied test
        couldn't (the standalone path seeds the slot directly in
        Python).
        """
        frame = render_scenario("so_delete_failed_preview")
        # Pre-state: Confirm visible, no error text yet (header-op
        # Alert is gated on the ``applied_header_failed_count > 0``
        # condition; preview seeds it to 0).
        assert frame.locator("button").filter(has_text="Confirm").first.is_visible()
        assert (
            frame.locator("text=404 Not Found: sales order 42 does not exist").count()
            == 0
        )
        assert frame.locator("text=Sales order operation failed").count() == 0

        # Fire Confirm — stub returns the failed-delete apply response,
        # on_success chain seeds ``applied_header_failed_*`` from
        # ``$result.state.*``.
        frame.locator("button").filter(has_text="Confirm Delete").first.click()

        # Wait for the morph: the failed-delete error text appears
        # inside the now-visible header-op Alert.
        frame.locator(
            "text=404 Not Found: sales order 42 does not exist"
        ).first.wait_for(state="visible", timeout=30000)
        assert frame.locator("text=Sales order operation failed").count() >= 1

    def test_so_modify_fail_fast_not_run_morphs_preview_to_applied(
        self, render_scenario
    ):
        """#858 finding B (NOT-RUN morph) — Click-through: a 4-row plan
        that fails on row 2 must morph to a card showing all 4 rows
        (APPLIED + FAILED + NOT RUN + NOT RUN) instead of silently
        dropping rows 3-4.

        Pre-fix: ``execute_plan`` fail-fast truncated ``response.actions``
        at row 2 (the failure boundary). The morph overwrote each
        section's ``so_<section>_rows`` slot with the apply response's
        shorter list — rows 3-4 silently disappeared from the Line items
        section. Operator saw "1 succeeded, 1 failed" with no indication
        that 2 more changes were never attempted.

        Post-fix: ``_modify_sales_order_impl`` stashes the unattempted
        plan tail under ``response.extras["not_run_actions"]``;
        :func:`build_so_modify_ui` merges it back into the per-section
        row bucketing. The morph contract is preserved through the same
        ``$result.state.so_<section>_rows`` on_success chain — the
        merged actions list seeds those slots build-time + apply-time
        identically.
        """
        frame = render_scenario("so_modify_fail_fast_not_run_preview")
        # Pre-state: preview shows all 4 rows as PLANNED (no Badges).
        # The morph hasn't fired yet, so no NOT RUN / APPLIED / FAILED
        # chrome on the per-row Badges.
        assert frame.locator("button").filter(has_text="Confirm").first.is_visible()
        assert frame.locator("text=NOT RUN").count() == 0
        assert frame.locator("text=APPLIED").count() == 0
        assert frame.locator("text=FAILED").count() == 0

        # Fire Confirm — stub returns the fail-fast apply response with
        # 2 executed + 2 NOT-RUN extras. The on_success chain seeds the
        # ``so_rows_rows`` slot from ``$result.state.so_rows_rows`` so
        # the merged 4-row list re-paints the Line items section.
        frame.locator("button").filter(has_text="Confirm").first.click()

        # Wait for the morph: the NOT-RUN rows must materialize.
        frame.locator("text=NOT RUN").first.wait_for(state="visible", timeout=30000)
        # All four row states are visible on the morphed card —
        # APPLIED + FAILED + NOT RUN x2. Pre-fix the NOT RUN entries
        # were silently dropped.
        assert frame.locator("text=APPLIED").count() >= 1
        assert frame.locator("text=FAILED").count() >= 1
        assert frame.locator("text=NOT RUN").count() >= 2

    def test_so_correct_fail_fast_not_run_applied_renders(self, render_scenario):
        """#858 Copilot follow-up (comment 3312071378) — ``build_so_modify_ui``
        also handles ``correct_sales_order``; its failure path must also
        populate ``extras["not_run_actions"]`` so the morph picks up the
        unattempted restore / recreate / close phases instead of silently
        dropping them.

        Same wire shape as the ``modify_sales_order`` fail-fast scenario
        above — proves the row merge in :func:`_actions_with_not_run_tail`
        is tool-agnostic (it keys on ``response.extras``, not ``confirm_tool``).
        Standalone-applied test, not click-through: the impl-side fix is
        verified in :file:`test_corrections.py`; this proves the JS-side
        render reads the extras correctly for the correction tool too.
        """
        frame = render_scenario("so_correct_fail_fast_not_run_applied")
        # Pre-fix: failure response would have shown only the executed
        # prefix (1 APPLIED + 1 FAILED row); the NOT-RUN tail was hidden.
        # Post-fix: all 4 rows visible on the applied card.
        assert frame.locator("text=APPLIED").count() >= 1
        assert frame.locator("text=FAILED").count() >= 1
        assert frame.locator("text=NOT RUN").count() >= 2

    def test_so_correct_fail_fast_header_skipped_applied_surfaces_alert(
        self, render_scenario
    ):
        """#858 round-8 — A fail-fast ``correct_sales_order`` whose
        close-phase ``update_header`` lands in the NOT-RUN tail must
        surface that skipped step via the ``applied_header_skipped_*``
        Alert. Pre-round-8 the skipped header step had no rendering
        surface: sub-entity row lists only bucket sub-entity ops
        (rows / addresses / fulfillments / shipping fees), and the
        header field map filters NOT-RUN out per round 7. The result
        was a failed correction where the operator could see "edit
        row failed" but could NOT see that the SO close step never
        ran — the SO was left in PENDING status with no indication.

        Post-round-8 the state-driven Alert surfaces the count + the
        user-facing summary ("Step skipped: modify the sales order
        header (NOT RUN — earlier phase failed before this step ran).").
        """
        frame = render_scenario("so_correct_fail_fast_header_skipped_applied")
        # Alert title (gated by ``applied_header_skipped_count > 0``).
        assert (
            frame.locator("text=1 header step(s) skipped").count() >= 1
            or frame.locator("text=header step(s) skipped").count() >= 1
        )
        # User-facing verb derived from ``_SO_HEADER_OP_VERBS["update_header"]``
        # — the operator sees the *operation* they care about
        # ("modify the sales order header"), not the wire name.
        assert (
            frame.locator("text=Step skipped: modify the sales order header").count()
            >= 1
        )
        # Causal phrase makes it obvious why the step was skipped
        # (otherwise the operator might think the step ran and the
        # status was already correct).
        assert frame.locator("text=earlier phase failed").count() >= 1

    def test_so_modify_header_failed_with_changes_morphs_preview_to_applied(
        self, render_scenario
    ):
        """#858 finding C — Click-through: a failed ``update_header``
        action WITH field changes must surface the state-driven
        ``applied_header_failed_*`` Alert on the morph, NOT stay frozen
        on the preview-time "no failures" state of the build-time
        :func:`_render_failed_changes_block`.

        Pre-fix: the build-time block read off the preview ``changes``
        map (every action's ``succeeded=None``), painted "no failures"
        into the view tree, and stayed there on the morph. The
        ``applied_header_failed_*`` Alert deliberately excluded ops
        WITH changes to avoid double-render, leaving the failure
        completely invisible on the morphed iframe.

        Post-fix: :func:`_so_header_op_failure_alert_text` is the single
        source of truth for header-op failures (no-change ops AND
        update_header WITH changes). The build-time block was removed
        from the SO entity view so the error surfaces exactly once,
        from state, on BOTH the standalone-applied path and the
        preview→Confirm morph path.
        """
        frame = render_scenario("so_modify_header_failed_with_changes_preview")
        # Pre-state: Confirm visible, no error text yet (the state
        # Alert is gated on ``applied_header_failed_count > 0`` — the
        # preview seeds it to 0).
        assert frame.locator("button").filter(has_text="Confirm").first.is_visible()
        assert frame.locator("text=422 Unprocessable").count() == 0
        assert frame.locator("text=Sales order operation failed").count() == 0

        # Fire Confirm — stub returns the failed-update-header apply
        # response. The on_success chain copies
        # ``$result.state.applied_header_failed_summary`` into the
        # preview iframe's matching slot.
        frame.locator("button").filter(has_text="Confirm").first.click()

        # Wait for the morph: the 422 error text appears inside the
        # now-visible state Alert.
        frame.locator("text=422 Unprocessable").first.wait_for(
            state="visible", timeout=30000
        )
        # The dedicated header-op Alert title is visible.
        assert frame.locator("text=Sales order operation failed").count() >= 1
        # And the user-facing verb derived from the operation
        # (``_SO_HEADER_OP_VERBS["update_header"]``).
        assert (
            frame.locator("text=Failed to modify the sales order header").count() >= 1
        )

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
        # post-apply primary visible. Whole-cell regex to avoid matching
        # the content-rich summary cell's "planned_quantity_per_unit"
        # field-name substring (case-insensitive partial would catch it).
        import re

        assert (
            frame.locator("td").filter(has_text=re.compile(r"^PLANNED$")).count() == 12
        )
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
