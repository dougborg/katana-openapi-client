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

    def test_customer_create_preview_renders(self, render_scenario):
        """``build_customer_create_ui`` preview state (#817).

        Mounts the four-tier customer create card and asserts the
        user-facing fields surface as values — not API plumbing.
        """
        frame = render_scenario("customer_create_preview")
        # Tier 1 — title + customer name in the headline badge + PREVIEW state.
        assert frame.locator("text=Customer Preview").count() >= 1
        assert frame.locator("text=Gourmet Bistro Group").count() >= 1
        assert frame.locator("text=PREVIEW").count() >= 1
        # Tier 3 — contact fields rendered with their values, not abstractions.
        assert frame.locator("text=procurement@gourmetbistro.com").count() >= 1
        assert frame.locator("text=+1-555-0125").count() >= 1
        assert frame.locator("text=USD").count() >= 1
        assert frame.locator("text=Fine Dining").count() >= 1
        # Tier 4 — Confirm + Cancel.
        assert frame.locator("text=Confirm & Create Customer").count() >= 1
        assert frame.locator("text=Cancel").count() >= 1
        # Anti-regression: no "Operation #" / "Target #" / "field(s) changed"
        # internal-model leakage in user-visible content.
        assert frame.locator("text=Operation #").count() == 0
        assert frame.locator("text=field(s) changed").count() == 0

    def test_customer_create_preview_renders_addresses(self, render_scenario):
        """Address blocks render with real street/city/state/zip — and the
        equivalent shipping address de-dupes to '(same as billing)'."""
        frame = render_scenario("customer_create_preview_with_addresses")
        # Billing address surfaces the actual lines, not an address ID.
        assert frame.locator("text=Billing Address:").count() >= 1
        assert frame.locator("text=123 Market St, Suite 4").count() >= 1
        assert frame.locator("text=Springfield, IL 62701").count() >= 1
        # The equivalent shipping address renders the de-dup line, not a
        # duplicate of the billing block.
        assert frame.locator("text=Shipping Address: (same as billing)").count() >= 1

    def test_customer_create_applied_renders_view_in_katana(self, render_scenario):
        """Applied state surfaces the View-in-Katana link + next-action."""
        frame = render_scenario("customer_create_applied")
        assert frame.locator("text=Customer Created").count() >= 1
        assert frame.locator("text=CREATED").count() >= 1
        assert frame.locator("text=View in Katana").count() >= 1
        # Direct-apply rail's next-action button.
        assert frame.locator("text=Create Sales Order").count() >= 1

    def test_customer_create_block_warning_hides_confirm(self, render_scenario):
        """A BLOCK: warning hides the Confirm button and surfaces the
        block-warning Badge (gate from _render_warnings_block →
        _render_preview_footer)."""
        frame = render_scenario("customer_create_block_warning")
        # Warning text surfaces, with the BLOCK: prefix stripped.
        assert (
            frame.locator(
                "text=a customer named 'Gourmet Bistro Group' already exists"
            ).count()
            >= 1
        )
        # Confirm button gone; cannot-proceed coaching shows up.
        assert frame.locator("text=Confirm & Create Customer").count() == 0
        assert frame.locator("text=Cannot proceed").count() >= 1

    def test_customer_create_minimal_renders_fallback(self, render_scenario):
        """A customer with no optional fields renders the empty-Tier-3
        fallback Muted line instead of a visually-blank card body."""
        frame = render_scenario("customer_create_minimal")
        assert frame.locator("text=Minimal Co").count() >= 1
        assert (
            frame.locator("text=No additional contact details provided.").count() >= 1
        )

    def test_product_bom_renders(self, render_scenario):
        """``build_product_bom_ui`` — rows='{{ bom.rows }}' over 3
        ingredient rows. Pre-#810 the tool returned ``make_json_result``
        (no PrefabApp) and the iframe stalled on "Waiting for content..."
        forever; this scenario proves the card now renders end-to-end.
        """
        frame = render_scenario("product_bom")
        # Header content: product name (linked) + ingredient-count badge.
        assert frame.locator("text=Test Frame").count() >= 1
        assert frame.locator("text=3 ingredients").count() >= 1
        # DataTable with header + 3 ingredient rows.
        assert frame.locator("table").count() == 1
        assert frame.locator("table tr").count() >= 4
        # User-facing identifiers (SKU + display_name), NOT internal UUIDs.
        assert frame.locator("text=FS90250").count() >= 1
        assert frame.locator("text=M5 chainring bolt").count() >= 1
        assert frame.locator("text=OR12-NBR").count() >= 1
        # Footer action surfaced.
        assert frame.locator("text=Manage BOM").count() >= 1

    def test_product_bom_empty_renders(self, render_scenario):
        """``build_product_bom_ui`` with no rows — the friendly hint
        replaces the DataTable. Pins the empty-state path so a cold-
        cache or new-variant lookup doesn't fall back to the
        empty-iframe failure mode #470 originally caught.
        """
        frame = render_scenario("product_bom_empty")
        # Empty-state hint instead of a DataTable.
        assert frame.locator("table").count() == 0
        assert frame.locator("text=No BOM rows for this variant").count() >= 1
        # Header still informative — the empty hint isn't a substitute for
        # the identity badge / title.
        assert frame.locator("text=Test Frame").count() >= 1
        # Footer action still present — the user may want to add rows.
        assert frame.locator("text=Manage BOM").count() >= 1

    def test_variant_batch_renders(self, render_scenario):
        """``build_variant_batch_ui`` — rows='{{ rows }}' over 3 found
        + 2 not-found inputs. Closes the get_variant_details batch-path
        empty-card sibling bug from #810: the batch return was
        ``ToolResult(structured_content=<dict>)`` with no PrefabApp.
        """
        frame = render_scenario("variant_batch")
        # Count badges in the header.
        assert frame.locator("text=3 found").count() >= 1
        assert frame.locator("text=2 not found").count() >= 1
        # DataTable for found variants.
        assert frame.locator("table").count() == 1
        assert frame.locator("table tr").count() >= 4  # header + 3
        assert frame.locator("text=VAR-A").count() >= 1
        assert frame.locator("text=VAR-C").count() >= 1
        # Not-found Alert section surfaces the missing inputs.
        assert frame.locator("text=DOES-NOT-EXIST-1").count() >= 1
        assert frame.locator("text=999999999").count() >= 1

    def test_so_create_with_fees_preview_renders(self, render_scenario):
        """``build_so_create_ui`` with inline shipping fees on preview (#818).

        The card surfaces each planned fee with description / amount /
        tax-rate suffix and a total-summary line. No APPLIED / FAILED
        status pills on preview. The PREVIEW state header keeps the
        Confirm button available (no BLOCK warnings).
        """
        frame = render_scenario("so_create_with_fees_preview")
        # Tier 1 — title + state.
        assert frame.locator("text=Sales Order Preview").count() >= 1
        assert frame.locator("text=PREVIEW").count() >= 1
        # Shipping fees section header + per-fee rows.
        assert frame.locator("text=Shipping fees:").count() >= 1
        assert frame.locator("text=Standard shipping").count() >= 1
        assert frame.locator("text=Handling").count() >= 1
        # Tax-rate suffix renders.
        assert frame.locator("text=tax rate #301").count() >= 1
        # Summary line.
        assert frame.locator("text=Total shipping").count() >= 1
        assert frame.locator("text=2 fee(s)").count() >= 1
        # Confirm available; no failure chrome.
        assert frame.locator("text=Confirm & Create Sales Order").count() >= 1
        assert frame.locator("text=APPLIED").count() == 0
        assert frame.locator("text=FAILED").count() == 0

    def test_so_create_with_fees_applied_all_success_renders(self, render_scenario):
        """``build_so_create_ui`` applied state with every fee succeeded.

        Each row gains the APPLIED pill + the server-assigned id surfaces
        (id=5001 / id=5002). No retry coaching since nothing failed.
        """
        frame = render_scenario("so_create_with_fees_applied_all_success")
        # Tier 1 — applied chrome.
        assert frame.locator("text=Sales Order Created").count() >= 1
        # APPLIED pills, one per fee.
        assert frame.locator("text=APPLIED").count() >= 2
        # Server-assigned ids surface.
        assert frame.locator("text=id=5001").count() >= 1
        assert frame.locator("text=id=5002").count() >= 1
        # View-in-Katana + Fulfill button rail.
        assert frame.locator("text=View in Katana").count() >= 1
        assert frame.locator("text=Fulfill Order").count() >= 1
        # No retry-coaching Alert.
        assert frame.locator("text=Retry the failed fees").count() == 0

    def test_so_create_with_fees_applied_partial_failure_renders(self, render_scenario):
        """Partial failure: SO created + one fee succeeded + one fee failed.

        Pins the per-fee status pill mix (APPLIED + FAILED) and the
        destructive Alert at the bottom coaching the operator toward
        ``modify_sales_order(id=<so_id>, add_shipping_fees=[...])``.
        """
        frame = render_scenario("so_create_with_fees_applied_partial_failure")
        # Tier 1 — applied chrome (the SO itself succeeded).
        assert frame.locator("text=Sales Order Created").count() >= 1
        # Mixed status pills + inline error text.
        assert frame.locator("text=APPLIED").count() >= 1
        assert frame.locator("text=FAILED").count() >= 1
        assert frame.locator("text=422: invalid tax rate id").count() >= 1
        # Destructive Alert with retry coaching at the bottom of the
        # shipping-fees section.
        assert frame.locator("text=shipping fee(s) failed").count() >= 1
        assert frame.locator("text=modify_sales_order").count() >= 1
        assert frame.locator("text=add_shipping_fees").count() >= 1
        # Partial-failure warning surfaces as a regular (non-BLOCK) Badge.
        assert frame.locator("text=1 of 2 shipping fee(s) failed").count() >= 1


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
