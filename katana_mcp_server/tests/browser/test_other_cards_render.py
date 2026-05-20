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

import json
import tempfile
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.browser

# Pinned to match ``render_test_server.GET_VARIANT_DETAILS_RECORD_PATH``
# so the test process and the dev-server subprocess agree on where the
# stub writes its received args. If the constant moves, both sides need
# to update.
_GET_VARIANT_DETAILS_RECORD_PATH = (
    Path(tempfile.gettempdir()) / "katana_test_get_variant_details_received.json"
)


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

    def test_inventory_at_single_renders(self, render_scenario):
        """``build_inventory_at_ui`` single-item layout — variant info in the
        header, per-location DataTable below.

        Pins the path-expression form (``rows='{{ rows }}'``) for the
        flattened (variant, location) row list. Single-item layout drops
        the SKU/Item columns from the table — header carries them via a
        Badge.
        """
        frame = render_scenario("inventory_at_single")
        # Header chrome: "Inventory as of YYYY-MM-DD" title + SKU badge.
        assert frame.locator("text=Inventory as of 2026-04-01").count() >= 1
        assert frame.locator("text=SKU-WIDGET").count() >= 1
        # Table with header + 2 location rows.
        assert frame.locator("table").count() == 1
        assert frame.locator("table tr").count() >= 3
        assert frame.locator("text=Main Warehouse").count() >= 1
        assert frame.locator("text=East Warehouse").count() >= 1

    def test_inventory_at_batch_renders(self, render_scenario):
        """``build_inventory_at_ui`` batch layout — SKU/Item columns visible,
        flat (variant, location) row list, empty-history placeholder, and
        a "not found" Muted footer.

        Pins three things at once: the columns conditionally added in
        batch mode, the empty by_location placeholder row, and the
        not_found surfacing.
        """
        frame = render_scenario("inventory_at_batch")
        # 3 items x locations: SKU-A (1 loc) + SKU-B (2 locs) + SKU-C
        # (1 empty placeholder row) = 4 data rows + header = 5+ rows.
        assert frame.locator("table").count() == 1
        assert frame.locator("table tr").count() >= 5
        # Batch layout includes SKU column rows.
        assert frame.locator("text=SKU-A").count() >= 1
        assert frame.locator("text=SKU-B").count() >= 1
        assert frame.locator("text=SKU-C").count() >= 1  # placeholder row
        # Annex appears in only one row (SKU-B), Main in two rows (A + B).
        assert frame.locator("text=Annex").count() >= 1
        # not_found footer surfaces the ghost SKU.
        assert frame.locator("text=GHOST-SKU").count() >= 1

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
        mixed sub-ops grouped by ``group_label``, exercising the per-row
        diff overlay (Qty / Batch / Serials columns) added by #557.
        """
        frame = render_scenario("batch_recipe_update")
        assert frame.locator("table").count() == 1
        # 5 sub-ops + header.
        assert frame.locator("table tr").count() >= 6
        # SKU strings from the test fixture — covers add, delete, update,
        # and batch / serial-tracked variants.
        assert frame.locator("text=SKU-NEW-NUT").count() >= 1
        assert frame.locator("text=SKU-OLD-BOLT").count() >= 1
        # Diff overlay rendering: ``+ N`` for adds, ``- N`` for deletes,
        # ``before -> after`` for updates. Cell text uses ASCII arrow.
        assert frame.locator("text=+ 2.0").count() >= 1
        assert frame.locator("text=- 2.0").count() >= 1
        # Update diff renders ``before -> after`` (the literal hyphen-arrow
        # is split into multiple text nodes by the DataTable cell — match
        # on a single half to confirm the cell content rendered).
        assert frame.locator("text=1.0").count() >= 1
        assert frame.locator("text=4.0").count() >= 1
        # Optional columns surface when at least one row supplies a value.
        assert frame.locator("text=batch 42x30").count() >= 1
        assert frame.locator("text=SN-001").count() >= 1


class TestDataTableRowClickBinding:
    """Verify DataTable ``onRowClick`` ``{{ field }}`` per-row bindings
    actually resolve client-side against the clicked row's data (#494).

    Background: #491 found that the MCP host silently dropped Mustache
    ``{{ request.<field> }}`` arguments in CallTool actions (host-state
    substitution). The fix in #493 inlined values at preview-build time
    for the order/receipt/batch/fulfill builders, but deliberately left
    the DataTable per-row ``{{ sku }}`` and ``{{ id }}`` bindings alone
    because those expand via the DataTable component's own row-context
    machinery (``$event`` is the row dict per the component docstring)
    — a different code path. These tests prove that path actually works
    end-to-end through the iframe.

    Both card builders' row-click handlers route to a stub
    ``get_variant_details`` (defined in ``render_test_server.py``) that
    echoes back whichever argument the host actually delivered. The
    on_success ``SetState("detail", RESULT)`` then renders the echoed
    card in a ``Slot(name="detail")``. The test asserts the echoed text
    matches the clicked row's data — proving substitution worked.

    Failure modes the tests catch:
    - Host drops the binding silently → echo shows ``None`` → fail
    - Host emits the literal Mustache string → echo shows ``"{{ sku }}"``
      → fail
    - on_error fires (host rejects the call upfront) → toast appears
      but the detail slot never populates → fail (wait_for times out)
    """

    def _wait_and_read_record(self, timeout_s: float = 15.0) -> dict:
        """Poll the cross-process record file until the stub writes to it,
        then parse + return its contents."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if _GET_VARIANT_DETAILS_RECORD_PATH.exists():
                return json.loads(_GET_VARIANT_DETAILS_RECORD_PATH.read_text())
            time.sleep(0.25)
        raise AssertionError(
            f"Stub never wrote to {_GET_VARIANT_DETAILS_RECORD_PATH} within "
            f"{timeout_s}s — the row-click never reached the server. Either "
            "the host dropped the CallTool, or the click target didn't fire "
            "onRowClick."
        )

    @pytest.fixture(autouse=True)
    def _clear_record(self):
        """Wipe the cross-process record file before each test so a stale
        write from a prior test can't masquerade as a fresh substitution."""
        _GET_VARIANT_DETAILS_RECORD_PATH.unlink(missing_ok=True)
        yield
        _GET_VARIANT_DETAILS_RECORD_PATH.unlink(missing_ok=True)

    def test_search_results_row_click_passes_clicked_sku(self, render_scenario):
        """``build_search_results_ui`` DataTable: clicking row N fires
        ``get_variant_details(sku="SKU-NNNN")`` with the row's own SKU.

        Picks "SKU-0003" — far enough from the first row that a
        first-row-only binding would also be caught. Clicks a ``<td>``
        cell within the row because the Prefab DataTable renderer
        currently attaches the click listener at the cell level (verified
        empirically — ``tr.click()`` and ``tr.dispatchEvent("click")``
        do not fire the handler, but a click on a contained ``<td>``
        does).
        """
        frame = render_scenario("search_results")
        # Click the SKU cell within the row whose SKU is "SKU-0003".
        frame.locator("td.pf-table-cell").filter(has_text="SKU-0003").first.click()

        record = self._wait_and_read_record()
        # Substitution must have resolved the {{ sku }} binding against
        # the clicked row's data — not None, not the literal Mustache
        # string, not some other row's SKU.
        assert record["received_sku"] == "SKU-0003", (
            f"Expected received_sku='SKU-0003' (the clicked row's SKU). "
            f"Got: {record!r}. If 'received_sku' is None the host silently "
            f"dropped the binding. If it's '{{ sku }}' the host emitted the "
            f"literal template. Either is the #491-class failure mode."
        )
        # search_results binds only {{ sku }}, not {{ id }} — variant_id
        # should be absent.
        assert record["received_variant_id"] is None

    def test_item_detail_variant_row_click_passes_clicked_variant_id(
        self, render_scenario
    ):
        """``build_item_detail_ui`` variants DataTable: clicking variant
        row N fires ``get_variant_details(variant_id=N)`` with the row's
        own id. Pins the #494 fix path for the card landed in #698.

        Picks variant_id=700002 (the middle row) so first-row-only and
        last-row-only bugs would both fail this test. The middle row's
        SKU is "VAR-B" — click that cell to drive the row-click.
        """
        frame = render_scenario("item_detail")
        frame.locator("td.pf-table-cell").filter(has_text="VAR-B").first.click()

        record = self._wait_and_read_record()
        assert record["received_variant_id"] == 700002, (
            f"Expected received_variant_id=700002 (the clicked row's id). "
            f"Got: {record!r}. The item_detail variants DataTable binds "
            f"{{ id }} via on_row_click — a None or wrong-row value here "
            f"means the row-context substitution is broken."
        )
        # item_detail binds only {{ id }}, not {{ sku }}.
        assert record["received_sku"] is None

    def test_search_results_row_click_populates_detail_slot(self, render_scenario):
        """End-to-end drill-down: clicking a row not only fires the
        CallTool with the right SKU, but the returned card actually
        renders inside the ``Slot(name="detail")``.

        The Slot-side fix paired with the substitution fix: a bare
        ``SetState("detail", RESULT)`` would put the PrefabApp envelope
        (``{$prefab, view, defs, state}``) into state, which the Slot
        can't render because it checks ``"type" in D`` on the stored
        value. ``RESULT.view`` (``{{ $result.view }}``) extracts the
        root view component, which DOES have ``type``, so the Slot
        renders the response card.
        """
        frame = render_scenario("search_results")
        # Pre-click: fallback content is visible; echoed card is not.
        assert frame.locator("text=Click a row to see").count() >= 1
        assert frame.locator("text=Echoed Variant Details").count() == 0

        frame.locator("td.pf-table-cell").filter(has_text="SKU-0007").first.click()

        # The echoed response card appears in the detail slot.
        frame.locator("text=Echoed Variant Details").wait_for(
            state="visible", timeout=15000
        )
        # And it shows the clicked row's SKU echoed back.
        assert frame.locator("text=received_sku='SKU-0007'").count() >= 1
