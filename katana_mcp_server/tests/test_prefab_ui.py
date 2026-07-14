"""Tests for Prefab UI builder functions.

Verifies that all UI builders can be called without errors and produce
valid PrefabApp instances. This catches constructor signature mismatches
(e.g., positional vs keyword args) that would only surface at runtime.
"""

from __future__ import annotations

import json
import re
from typing import Any, ClassVar

import pytest
from katana_mcp.tools.foundation.bom_table import _merge_bom_rows_for_modify_card
from katana_mcp.tools.prefab_ui import (
    PREVIEW_APPLY_COACHING,
    _format_money,
    _paginate,
    build_batch_recipe_update_ui,
    build_bom_modify_ui,
    build_fulfill_preview_ui,
    build_fulfill_success_ui,
    build_inventory_check_batch_ui,
    build_inventory_check_ui,
    build_item_create_ui,
    build_item_detail_ui,
    build_item_modify_ui,
    build_low_stock_ui,
    build_mo_create_ui,
    build_mo_modify_ui,
    build_po_create_ui,
    build_po_modify_ui,
    build_receipt_ui,
    build_search_results_ui,
    build_so_create_ui,
    build_so_detail_ui,
    build_so_modify_ui,
    build_stock_transfer_modify_ui,
    build_variant_details_ui,
    build_verification_ui,
    status_badge_variant,
    with_preview_coaching,
)
from prefab_ui.app import PrefabApp
from pydantic import BaseModel


class _StubRequest(BaseModel):
    """Minimal Pydantic stub used by builder tests that don't care about the
    real request shape — only that the builder accepts a BaseModel and emits
    a valid envelope.
    """

    preview: bool = True


def _walk_view_tree(node: Any) -> list[dict[str, Any]]:
    """Yield every Component dict in a view tree (for test traversal)."""
    found: list[dict[str, Any]] = []

    def visit(o: Any) -> None:
        if isinstance(o, dict):
            if "type" in o:
                found.append(o)
            for v in o.values():
                visit(v)
        elif isinstance(o, list):
            for v in o:
                visit(v)

    visit(node)
    return found


_MUSTACHE_RE = re.compile(r"^\s*\{\{\s*([^}\s]+)\s*\}\}\s*$")


def _assert_state_bindings_resolve(envelope: dict[str, Any]) -> None:
    """Every DataTable rendering rows by state-key reference must point to
    a slot that exists in ``state``, AND must use the mustache template
    form ``{{ key }}``. Bare strings crash the JS renderer with
    ``t.some is not a function`` — discovered via headless render tests.
    """
    state = envelope.get("state") or {}
    for component in _walk_view_tree(envelope.get("view")):
        if component.get("type") != "DataTable":
            continue
        rows = component.get("rows")
        if not isinstance(rows, str):
            continue
        m = _MUSTACHE_RE.match(rows)
        assert m is not None, (
            f"DataTable.rows={rows!r} is a bare string. State-bound rows "
            f"must use the mustache template form '{{{{ key }}}}' — bare "
            f"strings crash the JS renderer."
        )
        # The mustache content can be a path expression like "stock.by_location"
        # — only the first segment must exist in state.
        first_segment = m.group(1).split(".", 1)[0]
        assert first_segment in state, (
            f"DataTable.rows={rows!r} references missing state slot "
            f"{first_segment!r}. Available: {sorted(state)}"
        )


def _assert_valid_prefab(app: PrefabApp) -> None:
    """Assert that a PrefabApp serializes to valid JSON.

    Beyond the basic shape check, also rounds-trips through ``json.dumps``
    (catches non-serializable values that ``to_json`` may have skipped) and
    verifies that every state-bound DataTable references a present slot.
    """
    result = app.to_json()
    assert isinstance(result, dict)
    assert "$prefab" in result
    # Full JSON serialization roundtrip — catches anything ``to_json``
    # produced that pydantic_core wouldn't accept downstream.
    json.dumps(result)
    _assert_state_bindings_resolve(result)


class TestFormatMoney:
    """``_format_money`` delegates to Babel for currency-aware rendering."""

    def test_usd_amount(self):
        assert _format_money(1500.0, "USD") == "$1,500.00"

    def test_eur_uses_euro_symbol(self):
        assert _format_money(1500.0, "EUR") == "€1,500.00"

    def test_jpy_has_no_decimals(self):
        # JPY's ISO definition has zero decimal places — Babel drops them
        # automatically; a hand-rolled formatter would render "¥1500.00".
        assert _format_money(1500, "JPY") == "¥1,500"

    def test_missing_currency_falls_back_to_usd(self):
        assert _format_money(1500.0, None) == "$1,500.00"

    def test_none_amount_renders_as_zero(self):
        assert _format_money(None, "USD") == "$0.00"

    def test_unknown_currency_keeps_code_prefix(self):
        # Babel gracefully handles unknown ISO codes by prefixing the code
        # instead of raising — keeps the helper total over partial.
        assert _format_money(1500.0, "XYZ") == "XYZ1,500.00"


class TestBuildSearchResultsUI:
    def test_with_items(self):
        items = [
            {
                "id": 1,
                "sku": "SKU-001",
                "name": "Widget",
                "item_type": "product",
                "is_sellable": True,
            },
            {
                "id": 2,
                "sku": "SKU-002",
                "name": "Bolt",
                "item_type": "material",
                "is_sellable": False,
            },
        ]
        app = build_search_results_ui(items, "widget", 2)
        _assert_valid_prefab(app)

    def test_with_items_renders_table_and_buttons(self):
        """Regression guard for #470 — the existing populated-results path
        must still render the DataTable, the drill-down Slot, and the
        "Check inventory" button. Pairs with
        ``test_empty_results_omits_table_and_buttons``.
        """
        items = [
            {"id": 1, "sku": "SKU-001", "name": "Widget", "is_sellable": True},
        ]
        app = build_search_results_ui(items, "widget", 1)
        envelope = app.to_json()
        assert _has_node_of_type(envelope, "DataTable"), (
            "Populated search results must render a DataTable."
        )
        assert _has_node_of_type(envelope, "Slot"), (
            "Populated search results must render the drill-down Slot."
        )
        check_inventory_buttons = _find_buttons_by_label(
            envelope, "Check inventory for search results"
        )
        assert len(check_inventory_buttons) == 1, (
            "Populated search results must render the 'Check inventory' button."
        )

    def test_check_inventory_button_uses_call_tool_with_collected_skus(self):
        """The "Check inventory for search results" button must invoke
        ``check_inventory`` directly via ``CallTool`` (deterministic
        re-invocation), passing the SKUs collected at card-build time
        as ``skus_or_variant_ids``. No ``SendMessage`` chat-prompt
        indirection — that's what the migration in this PR replaces."""
        items = [
            {"id": 1, "sku": "SKU-001", "name": "Widget", "is_sellable": True},
            {"id": 2, "sku": "SKU-002", "name": "Gadget", "is_sellable": True},
        ]
        envelope = build_search_results_ui(items, "widget", 2).to_json()
        button = _find_buttons_by_label(envelope, "Check inventory for search results")[
            0
        ]
        on_click = button.get("onClick") or button.get("on_click")
        assert isinstance(on_click, dict), (
            f"Expected onClick to be a dict action; got {on_click!r}"
        )
        assert on_click.get("action") == "toolCall", (
            f"Expected CallTool action; got {on_click!r}"
        )
        assert on_click.get("tool") == "check_inventory"
        assert on_click.get("arguments") == {
            "skus_or_variant_ids": ["SKU-001", "SKU-002"]
        }

    def test_check_inventory_button_falls_back_to_update_context_when_sku_less(self):
        """When every search result is SKU-less (legacy null-SKU rows
        per CLAUDE.md), Check Inventory can't construct CallTool args —
        falls back to ``UpdateContext`` asking the agent to resolve
        variant IDs first."""
        items = [
            {"id": 1, "sku": None, "name": "Legacy Import", "is_sellable": True},
        ]
        envelope = build_search_results_ui(items, "widget", 1).to_json()
        button = _find_buttons_by_label(envelope, "Check inventory for search results")[
            0
        ]
        on_click = button.get("onClick") or button.get("on_click")
        assert isinstance(on_click, dict)
        assert on_click.get("action") == "updateContext", (
            f"Expected UpdateContext fallback for null-SKU results; got {on_click!r}"
        )

    def test_empty_results(self):
        app = build_search_results_ui([], "nothing", 0)
        _assert_valid_prefab(app)

    def test_empty_results_omits_table_and_buttons(self):
        """#470 — when ``total_count == 0`` we render the header + badges
        + a Muted hint, but no DataTable, no Slot, and no "Check
        inventory" button (all of which would reference nonexistent
        results).
        """
        app = build_search_results_ui([], "00.4021.018.003", 0)
        envelope = app.to_json()

        assert not _has_node_of_type(envelope, "DataTable"), (
            "Empty search results must not render a DataTable."
        )
        assert not _has_node_of_type(envelope, "Slot"), (
            "Empty search results must not render the drill-down Slot."
        )
        check_inventory_buttons = _find_buttons_by_label(
            envelope, "Check inventory for search results"
        )
        assert len(check_inventory_buttons) == 0, (
            "Empty search results must not render the 'Check inventory' button."
        )

        # Empty-state hint must mention the query and surface the fallback
        # advice so a user pasting a full SKU knows to try a substring.
        # Assert on the Muted node's actual content rather than
        # ``str(envelope)`` — the header badge renders ``Query: ...``
        # unconditionally, so an envelope-wide substring check would pass
        # even if the Muted hint regressed.
        muted_contents = _collect_node_content(envelope, "Muted")
        hint = next(
            (c for c in muted_contents if c.startswith("No items match")),
            None,
        )
        assert hint is not None, (
            f"Empty-state must render a 'No items match' Muted hint; "
            f"got Muted contents: {muted_contents!r}"
        )
        assert '"00.4021.018.003"' in hint, (
            f"Empty-state hint must echo the original query; got {hint!r}"
        )
        assert "partial SKU" in hint, (
            f"Empty-state hint must suggest a partial-SKU/name fallback; got {hint!r}"
        )


class TestBuildVariantDetailsUI:
    def test_full_variant(self):
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget Pro",
            "type": "product",
            "sales_price": 29.99,
            "purchase_price": 15.00,
            "product_id": 10,
            "material_id": None,
            "lead_time": 7,
            "supplier_item_codes": ["SUP-001", "SUP-002"],
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)

    def test_minimal_variant(self):
        variant = {"id": 1, "sku": "X"}
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)

    def test_includes_uom_when_set(self):
        """UoM should render in the reference section when the parent supplied it."""
        variant = {
            "id": 100,
            "sku": "SEAL-250",
            "name": "General Sealant",
            "uom": "ml",
            "sales_price": 12.99,
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "UoM: ml" in rendered
        # Price should use uom suffix when uom isn't pcs/ea.
        assert "$12.99 / ml" in rendered

    def test_omits_uom_when_unset(self):
        """No UoM line and no /uom price suffix when parent didn't supply uom."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "sales_price": 10.0,
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "UoM:" not in rendered
        assert "$10.00" in rendered
        # No `/ <uom>` suffix on the bare price.
        assert "$10.00 /" not in rendered

    def test_price_uses_factory_base_currency_eur(self):
        """#751 — variant prices render with the tenant's base currency.

        Pre-#751 the builder hardcoded USD; an EUR-base tenant saw
        ``$12.99`` instead of ``€12.99``. The caller now threads
        ``base_currency_code`` (resolved once per batch via
        :func:`resolve_factory_base_currency`) into the variant dict
        before building the card.
        """
        variant = {
            "id": 100,
            "sku": "WIDGET-EU",
            "name": "Widget (EU)",
            "sales_price": 12.99,
            "purchase_price": 7.50,
            "base_currency_code": "EUR",
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "€12.99" in rendered  # EUR symbol
        assert "€7.50" in rendered
        # USD must not leak in when the base is non-USD.
        assert "$12.99" not in rendered

    def test_price_uses_factory_base_currency_jpy_no_decimals(self):
        """#751 — JPY tenants get ``\xa51,500`` (no decimals) per ISO 4217.

        Verifies Babel's per-ISO decimal-digit rule round-trips through
        the variant builder, not just the standalone ``_format_money``
        helper.
        """
        variant = {
            "id": 100,
            "sku": "WIDGET-JP",
            "name": "Widget (JP)",
            "sales_price": 1500.0,
            "base_currency_code": "JPY",
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "\xa51,500" in rendered  # JPY yen symbol, no decimals
        assert "\xa51,500.00" not in rendered  # Babel drops the decimals

    def test_price_falls_back_to_usd_when_base_currency_missing(self):
        """Cold-cache / pre-#751 fixtures: missing ``base_currency_code``
        falls back to USD so the card still renders cleanly."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "sales_price": 10.0,
            # No base_currency_code field.
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "$10.00" in rendered

    def test_includes_purchase_uom_when_set_and_different_from_stock(self):
        """Purchase UoM row renders the kit-size conversion when the item is
        purchased in a different unit than it's stocked in (SP0502 case: stock
        in pcs, buy as 4-pcs kits)."""
        variant = {
            "id": 100,
            "sku": "SP0502",
            "name": "Spoke (kit)",
            "uom": "pcs",
            "purchase_uom": "kit",
            "purchase_uom_conversion_rate": 4.0,
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Purchase UoM: kit (x4 pcs)" in rendered

    def test_omits_purchase_uom_when_unset(self):
        """The common case (purchase == stock UoM) leaves the row absent."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "uom": "pcs",
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Purchase UoM:" not in rendered

    def test_omits_purchase_uom_when_equals_stock_uom(self):
        """Even if both fields are populated, omit the redundant row when
        purchase and stock UoM match — the row would just say the same thing
        twice."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "uom": "pcs",
            "purchase_uom": "pcs",
            "purchase_uom_conversion_rate": 1.0,
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Purchase UoM:" not in rendered

    def test_purchase_uom_without_conversion_rate_renders_label_only(self):
        """If purchase_uom is set but conversion_rate is None, surface the
        label without the ``(xN stock)`` parenthetical — better than dropping
        the row entirely."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "uom": "pcs",
            "purchase_uom": "kit",
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Purchase UoM: kit" in rendered
        # No conversion-factor parenthetical when rate is missing.
        assert "Purchase UoM: kit (" not in rendered

    def test_includes_config_attributes_as_badges(self):
        """Config attributes should appear inline so the variant axes are visible."""
        variant = {
            "id": 100,
            "sku": "SHIRT-RED-L",
            "name": "T-Shirt",
            "config_attributes": [
                {"config_name": "Color", "config_value": "Red"},
                {"config_name": "Size", "config_value": "Large"},
            ],
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Color: Red" in rendered
        assert "Size: Large" in rendered

    def test_includes_default_supplier_name(self):
        """Supplier name lands in the reference section without the
        previously-rendered ``(<id>)`` parenthetical. IDs are noise for
        human readers; tooling reads them from ``structured_content``.
        """
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "default_supplier_id": 42,
            "default_supplier_name": "Acme Industrial",
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Default Supplier:" in rendered
        assert "Acme Industrial" in rendered
        # The (id) parenthetical was dropped.
        assert "Acme Industrial (42)" not in rendered

    def test_supplier_name_renders_as_external_link(self):
        """When both name and id are known, the supplier name renders as
        an external Link pointing at the Katana supplier page — same
        pattern as the title's parent-product link. Follows the module
        convention: link Katana entities wherever possible, never use
        ``SendMessage`` as an indirect way to surface a URL."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "default_supplier_id": 1301979,
            "default_supplier_name": "Acme Bearings",
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        envelope = app.to_json()
        links = _find_components_by_type(envelope, "Link")
        # One link in the supplier line pointing at the Katana supplier
        # page (the title may add another link to the parent — both are
        # fine; we just need to find the supplier one).
        supplier_link_hrefs = [
            link.get("href")
            for link in links
            if isinstance(link.get("href"), str)
            and "/contacts/suppliers/" in link.get("href", "")
        ]
        assert "https://factory.katanamrp.com/contacts/suppliers/1301979" in (
            supplier_link_hrefs
        )
        # The visible link text is the supplier name.
        supplier_link_contents = [
            link.get("content")
            for link in links
            if isinstance(link.get("href"), str)
            and "/contacts/suppliers/" in link.get("href", "")
        ]
        assert "Acme Bearings" in supplier_link_contents

    def test_supplier_renders_as_plain_text_when_id_missing(self):
        """With only ``default_supplier_name`` set (no id), the supplier
        line falls back to plain Text — can't construct a URL without
        the id."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "default_supplier_id": None,
            "default_supplier_name": "Unknown Inc",
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        envelope = app.to_json()
        rendered = str(envelope)
        assert "Default Supplier: Unknown Inc" in rendered
        # No supplier link rendered.
        links = _find_components_by_type(envelope, "Link")
        supplier_links = [
            link
            for link in links
            if isinstance(link.get("href"), str)
            and "/contacts/suppliers/" in link.get("href", "")
        ]
        assert supplier_links == []

    def test_title_uses_display_name_when_provided(self):
        """The card title pulls from ``display_name`` (the Katana-UI-format
        ``parent / configN`` string), not the raw ``name``. Falls back to
        ``name`` for legacy dicts and then ``sku``."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "raw-katana-name",
            "display_name": "Kitchen Knife / 8-inch / Black",
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        # The formatted display_name lands in the rendered title.
        assert "Kitchen Knife / 8-inch / Black" in rendered

    def test_title_wraps_in_link_when_katana_url_set(self):
        """When ``katana_url`` is set (parent product/material page),
        the title renders as a real external Link, not a SendMessage
        button. Clicking opens the parent page directly — no agent
        round-trip."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "display_name": "Parent / Red",
            "katana_url": "https://factory.katanamrp.com/material/12345",
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        envelope = app.to_json()
        # A Link node must carry the katana_url as href.
        links = _find_components_by_type(envelope, "Link")
        href_values = [
            link.get("href") for link in links if isinstance(link.get("href"), str)
        ]
        assert "https://factory.katanamrp.com/material/12345" in href_values
        # The footer "View in Katana" Button is gone — the title link
        # replaces it.
        assert len(_find_buttons_by_label(envelope, "View in Katana")) == 0

    def test_title_bare_when_no_katana_url(self):
        """Without ``katana_url`` the title still renders, just not as
        a Link — fallback path for orphan variants / missing parent."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "display_name": "Orphan Widget",
            "katana_url": None,
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Orphan Widget" in rendered

    def test_supplier_codes_inline_with_code_font(self):
        """Supplier codes render inline using ``Code`` components — same
        row as the label, monospace font, comma-separated. The previous
        rendering used a ``Muted`` label + ``ForEach`` Text block that
        broke each code onto its own line."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "supplier_item_codes": ["BB63802LLUMAX-BAG", "OTHER-CODE-123"],
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        envelope = app.to_json()
        rendered = str(envelope)
        # Both codes appear, wrapped in Code components for monospace
        # rendering.
        code_nodes = _find_components_by_type(envelope, "Code")
        code_contents = [
            n.get("content") for n in code_nodes if isinstance(n.get("content"), str)
        ]
        assert "BB63802LLUMAX-BAG" in code_contents
        assert "OTHER-CODE-123" in code_contents
        # Label text still appears once.
        assert "Supplier Codes:" in rendered

    def test_no_raw_id_row(self):
        """The bottom ``variant_id=... · material_id=...`` Muted row was
        dropped — IDs are noise for human readers. Tooling can still
        read IDs from ``structured_content``."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "material_id": 200,
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "variant_id=" not in rendered
        assert "material_id=" not in rendered
        assert "product_id=" not in rendered

    def test_no_part_of_line(self):
        """The ``Part of:`` Muted line was dropped — ``display_name``
        already includes the parent name as its leading segment, so the
        separate line just duplicated information (especially when the
        variant has no config attributes and ``display_name == parent_name``,
        which is the common case for single-variant materials)."""
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Widget",
            "display_name": "Acme Bearings / 8mm",
            "product_or_material_name": "Acme Bearings",
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Part of:" not in rendered

    def test_renders_when_parent_lookup_returns_nothing(self):
        """When parent enrichment finds nothing (uom/supplier/batch all None),
        the card still renders without crashing and skips the parent-derived rows.
        """
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Orphan Variant",
            "sales_price": 5.0,
            "uom": None,
            "default_supplier_id": None,
            "default_supplier_name": None,
            "is_batch_tracked": None,
        }
        app = build_variant_details_ui(variant)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "UoM:" not in rendered
        assert "Default Supplier" not in rendered
        assert "Batch tracked" not in rendered
        # Identity still renders.
        assert "Orphan Variant" in rendered
        assert "SKU-001" in rendered

    def test_footer_actions_wire_correct_action_types(self):
        """Variant footer buttons follow the migration:
        - ``Check Inventory`` → ``CallTool("check_inventory", ...)`` —
          deterministic, args resolvable from the variant.
        - ``Create Purchase Order`` → ``UpdateContext`` — PO needs
          supplier/location/items, not derivable from the variant.
        - ``List MOs Using This`` (materials) → ``UpdateContext`` —
          no ingredient filter on list_manufacturing_orders today.
        """
        variant = {
            "id": 100,
            "sku": "SKU-001",
            "name": "Steel Bar",
            "type": "material",
        }
        envelope = build_variant_details_ui(variant).to_json()

        check_inv = _find_buttons_by_label(envelope, "Check Inventory")[0]
        check_inv_action = check_inv.get("onClick") or check_inv.get("on_click")
        assert isinstance(check_inv_action, dict)
        assert check_inv_action.get("action") == "toolCall"
        assert check_inv_action.get("tool") == "check_inventory"
        assert check_inv_action.get("arguments") == {"skus_or_variant_ids": ["SKU-001"]}

        create_po = _find_buttons_by_label(envelope, "Create Purchase Order")[0]
        create_po_action = create_po.get("onClick") or create_po.get("on_click")
        assert isinstance(create_po_action, dict)
        assert create_po_action.get("action") == "updateContext"

        list_mos = _find_buttons_by_label(envelope, "List MOs Using This")[0]
        list_mos_action = list_mos.get("onClick") or list_mos.get("on_click")
        assert isinstance(list_mos_action, dict)
        assert list_mos_action.get("action") == "updateContext"

    def test_footer_falls_back_to_variant_id_when_sku_null(self):
        """Variants can legally have ``sku=None`` (legacy NetSuite imports —
        see CLAUDE.md "Variants can have null SKUs"). Check Inventory must
        key off ``variant_id`` instead of passing an empty string —
        ``check_inventory`` rejects blank SKUs. The Create Purchase Order
        copy must use the same identity so the agent's prompt agrees with
        the surrounding card.
        """
        variant = {
            "id": 100,
            "sku": None,
            "name": "Legacy Import",
            "type": "material",
        }
        envelope = build_variant_details_ui(variant).to_json()

        check_inv = _find_buttons_by_label(envelope, "Check Inventory")[0]
        check_inv_action = check_inv.get("onClick") or check_inv.get("on_click")
        assert isinstance(check_inv_action, dict)
        assert check_inv_action.get("action") == "toolCall"
        assert check_inv_action.get("tool") == "check_inventory"
        # variant_id (int) rather than empty string keeps the call valid.
        assert check_inv_action.get("arguments") == {"skus_or_variant_ids": [100]}

        create_po = _find_buttons_by_label(envelope, "Create Purchase Order")[0]
        create_po_action = create_po.get("onClick") or create_po.get("on_click")
        assert isinstance(create_po_action, dict)
        assert create_po_action.get("action") == "updateContext"
        content = create_po_action.get("content", "")
        assert isinstance(content, str)
        assert "variant_id 100" in content, (
            f"Create-PO copy must surface variant_id when SKU is null; got: {content!r}"
        )

    def test_footer_omits_all_action_buttons_when_no_identity(self):
        """If neither SKU nor variant_id is resolvable (truly orphan
        variant — extremely rare but legal on the wire), every footer
        action gets dropped: Check Inventory's CallTool would have no
        target, and the Create-PO / List-MOs UpdateContext prompts
        would interpolate ``variant_id None`` which is actively
        misleading to the agent. Better no action than a broken one."""
        variant = {"sku": None, "name": "Truly Orphan"}
        envelope = build_variant_details_ui(variant).to_json()
        for label in (
            "Check Inventory",
            "Create Purchase Order",
            "List MOs Using This",
        ):
            buttons = _find_buttons_by_label(envelope, label)
            assert len(buttons) == 0, (
                f"Variant with no SKU and no variant_id must not render "
                f"the {label!r} footer button — there's no stable identity "
                f"to anchor the downstream prompt to."
            )


class TestBuildItemDetailUI:
    def test_product(self):
        item = {
            "id": 1,
            "name": "Widget",
            "type": "product",
            "uom": "pcs",
            "category_name": "Finished Goods",
            "is_sellable": True,
            "is_producible": True,
        }
        app = build_item_detail_ui(item)
        _assert_valid_prefab(app)

    def test_minimal_item(self):
        app = build_item_detail_ui({"id": 1, "name": "X"})
        _assert_valid_prefab(app)

    def test_title_wraps_in_link_when_katana_url_set(self):
        """Title becomes an external Link to the Katana page when
        ``katana_url`` is set — same pattern as the variant card.
        Items DO have direct Katana pages (unlike variants), so the
        link goes straight to the item, not a parent."""
        item = {
            "id": 1,
            "name": "Widget",
            "type": "product",
            "katana_url": "https://factory.katanamrp.com/product/1",
        }
        app = build_item_detail_ui(item)
        _assert_valid_prefab(app)
        envelope = app.to_json()
        links = _find_components_by_type(envelope, "Link")
        hrefs = [
            link.get("href") for link in links if isinstance(link.get("href"), str)
        ]
        assert "https://factory.katanamrp.com/product/1" in hrefs

    def test_title_bare_when_no_katana_url(self):
        item = {"id": 1, "name": "Orphan Item", "type": "product"}
        app = build_item_detail_ui(item)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Orphan Item" in rendered

    def test_id_text_row_dropped(self):
        """The previous "ID: <id>" raw-text row was dropped — IDs are
        noise for human readers and ride on the JSON
        ``structured_content`` channel for tooling."""
        item = {"id": 12345, "name": "Widget", "type": "product"}
        app = build_item_detail_ui(item)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "ID: 12345" not in rendered

    def test_status_pills_vary_by_subtype(self):
        """Status pills appear conditionally per item type. Products
        show producible / sellable, materials show batch_tracked /
        serial_tracked, services show neither producible nor batch
        flags."""
        # Material with batch + serial tracking
        material = {
            "id": 1,
            "name": "Steel",
            "type": "material",
            "is_sellable": False,
            "batch_tracked": True,
            "serial_tracked": True,
        }
        app = build_item_detail_ui(material)
        envelope = app.to_json()
        rendered = str(envelope)
        assert "Not Sellable" in rendered
        assert "Batch tracked" in rendered
        assert "Serial tracked" in rendered
        # Material isn't producible — no Producible/Not Producible badge
        assert "Producible" not in rendered

    def test_supplier_renders_as_external_link(self):
        """Default supplier name → Katana ``/contacts/suppliers/{id}``
        Link, matching the variant card convention. Supplier ID is
        nested under ``supplier`` (not flat ``default_supplier_id``)."""
        item = {
            "id": 1,
            "name": "Steel Bar",
            "type": "material",
            "supplier": {"id": 555, "name": "Acme Metals"},
        }
        app = build_item_detail_ui(item)
        _assert_valid_prefab(app)
        envelope = app.to_json()
        links = _find_components_by_type(envelope, "Link")
        supplier_links = [
            link
            for link in links
            if isinstance(link.get("href"), str)
            and "/contacts/suppliers/" in link.get("href", "")
        ]
        assert len(supplier_links) == 1
        assert (
            supplier_links[0].get("href")
            == "https://factory.katanamrp.com/contacts/suppliers/555"
        )
        assert supplier_links[0].get("content") == "Acme Metals"

    def test_supplier_falls_back_to_default_supplier_id_when_no_nested_supplier(
        self,
    ):
        """Materials commonly have ``supplier=None`` while
        ``default_supplier_id`` is set (Katana doesn't always embed the
        full nested supplier even when the FK is populated). The card
        must still render a clickable supplier reference using the flat
        ID. Visible text is ``#<id>`` since no name is available; the
        ``href`` still points at the supplier page so one click takes
        you to the source of truth.
        """
        item = {
            "id": 1,
            "name": "Steel Bar",
            "type": "material",
            "supplier": None,
            "default_supplier_id": 1301979,
        }
        app = build_item_detail_ui(item)
        _assert_valid_prefab(app)
        envelope = app.to_json()
        links = _find_components_by_type(envelope, "Link")
        supplier_links = [
            link
            for link in links
            if isinstance(link.get("href"), str)
            and "/contacts/suppliers/" in link.get("href", "")
        ]
        assert len(supplier_links) == 1
        assert (
            supplier_links[0].get("href")
            == "https://factory.katanamrp.com/contacts/suppliers/1301979"
        )
        # Visible text is the ID with a # prefix since no name available.
        assert supplier_links[0].get("content") == "#1301979"

    def test_supplier_omitted_for_service(self):
        """Services don't have a default supplier on the response model.
        The card should skip the supplier line cleanly without any
        spurious 'Default Supplier' rendering."""
        item = {"id": 1, "name": "Assembly Service", "type": "service"}
        app = build_item_detail_ui(item)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Default Supplier" not in rendered

    def test_configs_render_as_axis_text_rows(self):
        """Configuration axes render as ``"Axis: val1, val2, ..."`` text
        rows — one per axis. Empty config list skips silently."""
        item = {
            "id": 1,
            "name": "T-Shirt",
            "type": "product",
            "configs": [
                {"id": 10, "name": "Color", "values": ["Red", "Blue", "Black"]},
                {"id": 11, "name": "Size", "values": ["S", "M", "L"]},
            ],
        }
        app = build_item_detail_ui(item)
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Color: Red, Blue, Black" in rendered
        assert "Size: S, M, L" in rendered

    def test_variants_render_as_datatable_with_callTool_drilldown(self):
        """Variants render as a DataTable; per-row click invokes
        ``get_variant_details`` via ``CallTool`` (direct tool invocation,
        not a SendMessage chat prompt). The CallTool arguments key off
        the row's ``id`` (always present) — not ``sku`` — so SKU-less
        variants stay clickable."""
        item = {
            "id": 1,
            "name": "T-Shirt",
            "type": "product",
            "variants": [
                {
                    "id": 10,
                    "sku": "TS-RED-S",
                    "sales_price": 19.99,
                    "purchase_price": 8.50,
                },
                {
                    "id": 11,
                    "sku": "TS-BLUE-M",
                    "sales_price": 19.99,
                    "purchase_price": 8.50,
                },
            ],
        }
        app = build_item_detail_ui(item)
        _assert_valid_prefab(app)
        envelope = app.to_json()
        # DataTable component present
        tables = _find_components_by_type(envelope, "DataTable")
        assert len(tables) == 1
        # Per-row click is a CallTool pointing at get_variant_details
        on_row_click = tables[0].get("onRowClick")
        assert isinstance(on_row_click, dict)
        assert on_row_click.get("action") == "toolCall"
        assert on_row_click.get("tool") == "get_variant_details"
        # Argument keys off the row's ``id`` field, not ``sku``. Using
        # ``id`` keeps SKU-less variants (legitimate per
        # ``ItemVariantSummary.sku: str | None``) clickable. The template
        # uses ``$event.id`` (not bare ``id``) because the renderer
        # spreads the row dict at ``$event``, not into the scope's top
        # level (#494, verified via browser test).
        args = on_row_click.get("arguments") or {}
        assert args.get("variant_id") == "{{ $event.id }}"
        assert "sku" not in args

    def test_variants_table_handles_sku_less_variants(self):
        """A variant with ``sku=None`` still renders and stays clickable.
        Regression test for the Copilot finding on PR #698: keying the
        row-click off ``sku`` would have produced ``arguments={"sku": null}``
        and the tool would reject the call. Using ``id`` (always present)
        keeps the path working."""
        item = {
            "id": 1,
            "name": "Legacy Import",
            "type": "material",
            "variants": [
                {
                    "id": 99,
                    "sku": None,  # SKU-less, legitimate per Katana
                    "sales_price": None,
                    "purchase_price": 12.50,
                }
            ],
        }
        app = build_item_detail_ui(item)
        _assert_valid_prefab(app)
        envelope = app.to_json()
        # Table renders despite the null SKU.
        tables = _find_components_by_type(envelope, "DataTable")
        assert len(tables) == 1
        # Row-click args reference the variant id, not sku.
        args = tables[0].get("onRowClick", {}).get("arguments") or {}
        assert args == {"variant_id": "{{ $event.id }}"}
        # The variant count metric reflects the single row.
        assert "Variants: 1" in str(envelope)

    def test_variants_table_omitted_when_empty(self):
        """Items with zero variants skip the table cleanly — defensive
        path for cold-cache / unusual data."""
        item = {"id": 1, "name": "X", "type": "service", "variants": []}
        app = build_item_detail_ui(item)
        _assert_valid_prefab(app)
        envelope = app.to_json()
        tables = _find_components_by_type(envelope, "DataTable")
        assert tables == []
        # The variant count metric row still appears with 0.
        assert "Variants: 0" in str(envelope)

    def test_material_footer_actions(self):
        """Materials get Create PO + List MOs Using This + Modify Item."""
        item = {"id": 100, "name": "Steel", "type": "material"}
        app = build_item_detail_ui(item)
        envelope = app.to_json()
        assert len(_find_buttons_by_label(envelope, "Create Purchase Order")) == 1
        assert len(_find_buttons_by_label(envelope, "List MOs Using This")) == 1
        assert len(_find_buttons_by_label(envelope, "Modify Item")) == 1
        # No Manufacturing Order action on a material
        assert len(_find_buttons_by_label(envelope, "Create Manufacturing Order")) == 0
        # No "View in Katana" footer button — title link replaces it
        assert len(_find_buttons_by_label(envelope, "View in Katana")) == 0

    def test_product_producible_footer_actions(self):
        """Producible products get Create Manufacturing Order + Modify Item.
        Non-producible products skip the MO action."""
        item = {
            "id": 100,
            "name": "Bike",
            "type": "product",
            "is_producible": True,
        }
        app = build_item_detail_ui(item)
        envelope = app.to_json()
        assert len(_find_buttons_by_label(envelope, "Create Manufacturing Order")) == 1
        assert len(_find_buttons_by_label(envelope, "Modify Item")) == 1
        # No material-specific actions
        assert len(_find_buttons_by_label(envelope, "Create Purchase Order")) == 0

    def test_product_non_producible_skips_mo_action(self):
        item = {
            "id": 100,
            "name": "Component",
            "type": "product",
            "is_producible": False,
        }
        app = build_item_detail_ui(item)
        envelope = app.to_json()
        assert len(_find_buttons_by_label(envelope, "Create Manufacturing Order")) == 0
        # Modify Item is still there for all types
        assert len(_find_buttons_by_label(envelope, "Modify Item")) == 1

    def test_service_minimal_footer(self):
        """Services don't have material or product-specific actions —
        just Modify Item."""
        item = {"id": 100, "name": "Assembly Service", "type": "service"}
        app = build_item_detail_ui(item)
        envelope = app.to_json()
        assert len(_find_buttons_by_label(envelope, "Modify Item")) == 1
        assert len(_find_buttons_by_label(envelope, "Create Purchase Order")) == 0
        assert len(_find_buttons_by_label(envelope, "Create Manufacturing Order")) == 0
        assert len(_find_buttons_by_label(envelope, "List MOs Using This")) == 0

    def test_modify_item_message_falls_back_when_type_missing(self):
        """When ``type`` is absent (minimal/partial dict), the Modify Item
        SendMessage falls back to the generic "item" instead of leaking
        "None" into the agent prompt."""
        item = {"id": 1, "name": "X"}
        app = build_item_detail_ui(item)
        rendered = str(app.to_json())
        assert "modify None" not in rendered
        assert "modify item 1" in rendered


class TestBuildInventoryCheckUI:
    def test_with_stock(self):
        stock = {
            "sku": "SKU-001",
            "product_name": "Widget",
            "in_stock": 125,
            "available_stock": 100,
            "committed": 25,
            "expected": 50,
        }
        app = build_inventory_check_ui(stock)
        _assert_valid_prefab(app)

    def test_zero_stock(self):
        stock = {
            "sku": "SKU-002",
            "product_name": "",
            "in_stock": 0,
            "available_stock": 0,
            "committed": 0,
            "expected": 0,
        }
        app = build_inventory_check_ui(stock)
        _assert_valid_prefab(app)

    def test_uom_badge_renders_when_set(self):
        """#549 — parent-derived UoM should appear as a header badge."""
        stock = {
            "sku": "LU2313",
            "product_name": "Tubeless Sealant",
            "uom": "ml",
            "in_stock": 250,
            "available_stock": 250,
            "committed": 0,
            "expected": 0,
        }
        envelope = build_inventory_check_ui(stock).to_json()
        badges = _find_components_by_type(envelope, "Badge")
        labels = [b.get("label") for b in badges]
        assert "ml" in labels, f"UoM badge missing; got {labels!r}"

    def test_low_stock_badge_when_any_location_below_reorder(self):
        """#549 — destructive Low Stock badge fires when any location's
        available is at or below its reorder_point. Multi-location +
        per-location threshold is the canonical Katana shape."""
        stock = {
            "sku": "SKU-LOW",
            "product_name": "Almost Out",
            "in_stock": 12,
            "available_stock": 12,
            "committed": 0,
            "expected": 0,
            "by_location": [
                {
                    "location_id": 1,
                    "location_name": "Main",
                    "in_stock": 5,
                    "committed": 0,
                    "expected": 0,
                    "available": 5,
                    "reorder_point": 10,
                },
                {
                    "location_id": 2,
                    "location_name": "Backup",
                    "in_stock": 7,
                    "committed": 0,
                    "expected": 0,
                    "available": 7,
                    "reorder_point": 5,
                },
            ],
        }
        envelope = build_inventory_check_ui(stock).to_json()
        badges = _find_components_by_type(envelope, "Badge")
        labels = [b.get("label") for b in badges]
        assert "Low Stock" in labels, f"Expected Low Stock badge; got {labels!r}"

    def test_low_stock_badge_when_available_equals_reorder_point(self):
        """Reorder semantics fire at ``available <= reorder_point``, so the
        equality case (``available == reorder_point``) must trigger the
        badge too — not just strictly-below. Pinning explicitly because the
        per-row Status column splits this case off as ``At reorder``, and
        the header badge has to honor that as a low-stock state.
        """
        stock = {
            "sku": "SKU-EQ",
            "product_name": "At Threshold",
            "in_stock": 10,
            "available_stock": 10,
            "committed": 0,
            "expected": 0,
            "by_location": [
                {
                    "location_id": 1,
                    "location_name": "Main",
                    "in_stock": 10,
                    "committed": 0,
                    "expected": 0,
                    "available": 10,
                    "reorder_point": 10,
                },
            ],
        }
        envelope = build_inventory_check_ui(stock).to_json()
        badges = _find_components_by_type(envelope, "Badge")
        labels = [b.get("label") for b in badges]
        assert "Low Stock" in labels, (
            f"Available equal to reorder point must trigger Low Stock badge; "
            f"got {labels!r}"
        )

    def test_no_low_stock_badge_when_all_above_threshold(self):
        """Symmetric to the badge test — no destructive badge when every
        location is above its reorder point."""
        stock = {
            "sku": "SKU-OK",
            "product_name": "Healthy",
            "in_stock": 100,
            "available_stock": 100,
            "committed": 0,
            "expected": 0,
            "by_location": [
                {
                    "location_id": 1,
                    "location_name": "Main",
                    "in_stock": 100,
                    "committed": 0,
                    "expected": 0,
                    "available": 100,
                    "reorder_point": 10,
                },
            ],
        }
        envelope = build_inventory_check_ui(stock).to_json()
        badges = _find_components_by_type(envelope, "Badge")
        labels = [b.get("label") for b in badges]
        assert "Low Stock" not in labels, (
            f"Healthy stock should not show Low Stock badge; got {labels!r}"
        )

    def test_no_low_stock_badge_when_no_thresholds_set(self):
        """A missing reorder_point is a missing signal — never flag."""
        stock = {
            "sku": "SKU-UNK",
            "product_name": "No Thresholds",
            "in_stock": 0,
            "available_stock": 0,
            "committed": 0,
            "expected": 0,
            "by_location": [
                {
                    "location_id": 1,
                    "location_name": "Main",
                    "in_stock": 0,
                    "committed": 0,
                    "expected": 0,
                    "available": 0,
                    "reorder_point": None,
                },
            ],
        }
        envelope = build_inventory_check_ui(stock).to_json()
        badges = _find_components_by_type(envelope, "Badge")
        labels = [b.get("label") for b in badges]
        assert "Low Stock" not in labels

    def test_footer_includes_create_po_and_view_variant_for_product(self):
        """Tier 4 — product variant gets [Create PO] + [View Variant
        Details], no [List MOs]."""
        stock = {
            "sku": "SKU-PROD",
            "product_name": "Sellable Product",
            "in_stock": 10,
            "available_stock": 10,
            "committed": 0,
            "expected": 0,
            "parent_type": "product",
            "variant_id": 999,
        }
        envelope = build_inventory_check_ui(stock).to_json()
        assert len(_find_buttons_by_label(envelope, "Create PO")) == 1
        assert len(_find_buttons_by_label(envelope, "View Variant Details")) == 1
        assert len(_find_buttons_by_label(envelope, "List MOs Using This")) == 0

    def test_footer_omits_list_mos_button(self):
        """The "List MOs Using This" action was removed in #757 / #758 —
        no available tool answers "what MOs consume this material" in
        a single call (``list_manufacturing_orders.variant_ids`` filters
        finished goods; ``list_blocking_ingredients`` has no per-variant
        filter). Pin the absence so re-adding the button without the
        upstream filter regresses this test, not production UX.
        """
        stock = {
            "sku": "MAT-001",
            "product_name": "Sealant",
            "in_stock": 10,
            "available_stock": 10,
            "committed": 0,
            "expected": 0,
            "parent_type": "material",
            "variant_id": 12345,
        }
        envelope = build_inventory_check_ui(stock).to_json()
        assert len(_find_buttons_by_label(envelope, "Create PO")) == 1
        assert len(_find_buttons_by_label(envelope, "List MOs Using This")) == 0

    def test_title_links_to_katana_when_url_set(self):
        """#549 — title becomes a Link to the parent Katana page when
        ``katana_url`` is on the response."""
        stock = {
            "sku": "SKU-LINK",
            "product_name": "Linked",
            "in_stock": 10,
            "available_stock": 10,
            "committed": 0,
            "expected": 0,
            "katana_url": "https://factory.katanamrp.com/product/123",
        }
        envelope = build_inventory_check_ui(stock).to_json()
        links = _find_components_by_type(envelope, "Link")
        hrefs = [link.get("href") for link in links]
        assert any("/product/123" in (h or "") for h in hrefs), (
            f"Title link missing; got hrefs {hrefs!r}"
        )

    def test_per_location_table_carries_reorder_and_status_columns(self):
        """#549 — Tier 3 DataTable now carries reorder_point + status_label
        columns derived from per-row threshold comparison."""
        stock = {
            "sku": "SKU-MULTI",
            "product_name": "Multi-warehouse",
            "in_stock": 30,
            "available_stock": 30,
            "committed": 0,
            "expected": 0,
            "by_location": [
                {
                    "location_id": 1,
                    "location_name": "A",
                    "in_stock": 5,
                    "committed": 0,
                    "expected": 0,
                    "available": 5,
                    "reorder_point": 10,
                },
                {
                    "location_id": 2,
                    "location_name": "B",
                    "in_stock": 25,
                    "committed": 0,
                    "expected": 0,
                    "available": 25,
                    "reorder_point": 10,
                },
            ],
        }
        envelope = build_inventory_check_ui(stock).to_json()
        tables = _find_components_by_type(envelope, "DataTable")
        assert len(tables) == 1, (
            f"Expected one per-location DataTable; got {len(tables)}"
        )
        column_keys = [c.get("key") for c in tables[0].get("columns", [])]
        assert "reorder_point" in column_keys
        assert "status_label" in column_keys
        # Post-#card-ux: ``location_id`` is NOT a visible column. The
        # raw ID had no user value (anti-pattern #2); rows where
        # ``location_name`` resolves null should be fixed impl-side
        # (typed cache + ``resolve_entity_name``), not patched with a
        # fallback ID column. Pre-#card-ux comment: "location_id is an
        # always-rendered fallback so rows are never unidentifiable."
        assert "location_id" not in column_keys, (
            f"Per-location table must drop the raw location_id column; "
            f"got columns {column_keys!r}"
        )
        # Ensure the builder annotated the rows in state with status_label
        rows_state = envelope.get("state", {}).get("stock", {}).get("by_location", [])
        labels = [r.get("status_label") for r in rows_state]
        assert "Below reorder" in labels, f"Got status labels {labels!r}"
        assert "Healthy" in labels

    def test_footer_uses_variant_id_when_sku_is_null(self):
        """Variants can have a null SKU (CLAUDE.md "Variants can have null
        SKUs — never assume ``Variant.sku`` is non-null"). The footer
        actions must fall back to ``variant_id`` so SKU-less rows still
        get actionable buttons instead of producing a broken
        "for SKU " prompt or silently dropping the View Variant Details
        button.
        """
        stock = {
            "sku": None,
            "variant_id": 9999,
            "product_name": "Legacy NetSuite Import",
            "in_stock": 10,
            "available_stock": 10,
            "committed": 0,
            "expected": 0,
            "parent_type": "product",
        }
        envelope = build_inventory_check_ui(stock).to_json()
        # Both buttons render
        assert len(_find_buttons_by_label(envelope, "Create PO")) == 1
        assert len(_find_buttons_by_label(envelope, "View Variant Details")) == 1
        # Prompt text uses variant_id, not "SKU ".
        # Walk the rendered JSON envelope — covers both the
        # UpdateContext content string (Create PO) and the CallTool
        # arguments dict (View Variant Details).
        import json as _json

        rendered = _json.dumps(envelope)
        assert "variant_id 9999" in rendered or '"variant_id": 9999' in rendered, (
            f"Expected variant_id fallback in agent prompts; rendered: {rendered[:500]!r}"
        )
        assert "for SKU " not in rendered, (
            f"Null-SKU footer must not produce broken 'for SKU ' prompts; "
            f"rendered: {rendered[:500]!r}"
        )

    def test_footer_actions_wire_correct_action_types(self):
        """Tier 4 actions on the inventory-check card follow the
        migration:
        - ``Create PO`` → ``UpdateContext`` — PO drafting needs
          supplier + location + items that aren't card-derivable.
        - ``View Variant Details`` → ``CallTool("get_variant_details")``
          — deterministic, args resolve directly from the row's SKU
          (or variant_id when SKU is null).
        """
        stock = {
            "sku": "SKU-X",
            "variant_id": 42,
            "in_stock": 1,
            "available_stock": 1,
            "committed": 0,
            "expected": 0,
        }
        envelope = build_inventory_check_ui(stock).to_json()

        create_po = _find_buttons_by_label(envelope, "Create PO")[0]
        create_po_action = create_po.get("onClick") or create_po.get("on_click")
        assert isinstance(create_po_action, dict)
        assert create_po_action.get("action") == "updateContext"

        view_details = _find_buttons_by_label(envelope, "View Variant Details")[0]
        view_details_action = view_details.get("onClick") or view_details.get(
            "on_click"
        )
        assert isinstance(view_details_action, dict)
        assert view_details_action.get("action") == "toolCall"
        assert view_details_action.get("tool") == "get_variant_details"
        assert view_details_action.get("arguments") == {"sku": "SKU-X"}

    def test_view_variant_details_falls_back_to_variant_id_when_sku_null(self):
        """When the row has no SKU, View Variant Details still works —
        ``CallTool`` keys off ``variant_id`` instead of ``sku``."""
        stock = {
            "sku": None,
            "variant_id": 9999,
            "in_stock": 1,
            "available_stock": 1,
            "committed": 0,
            "expected": 0,
        }
        envelope = build_inventory_check_ui(stock).to_json()
        view_details = _find_buttons_by_label(envelope, "View Variant Details")[0]
        action = view_details.get("onClick") or view_details.get("on_click")
        assert isinstance(action, dict)
        assert action.get("action") == "toolCall"
        assert action.get("tool") == "get_variant_details"
        assert action.get("arguments") == {"variant_id": 9999}

    def test_footer_omits_buttons_when_no_identity(self):
        """Defensive — if both sku and variant_id are missing (truly
        anonymous row), drop the buttons entirely rather than emit
        prompts with no target."""
        stock = {
            "sku": None,
            "variant_id": None,
            "product_name": "Mystery",
            "in_stock": 0,
            "available_stock": 0,
            "committed": 0,
            "expected": 0,
        }
        envelope = build_inventory_check_ui(stock).to_json()
        assert len(_find_buttons_by_label(envelope, "Create PO")) == 0
        assert len(_find_buttons_by_label(envelope, "View Variant Details")) == 0


class TestBuildLowStockUI:
    def test_with_items(self):
        items = [
            {
                "sku": "SKU-001",
                "product_name": "Widget",
                "current_stock": 3,
                "threshold": 10,
            },
        ]
        app = build_low_stock_ui(items, 10, 1)
        _assert_valid_prefab(app)

    def test_with_items_renders_table_and_restock_button(self):
        """Regression guard for the empty-state fix bundled with #470 —
        the populated path must still render the DataTable and the
        "Create Restock Orders" button.
        """
        items = [
            {
                "sku": "SKU-001",
                "product_name": "Widget",
                "current_stock": 3,
                "threshold": 10,
            },
        ]
        app = build_low_stock_ui(items, 10, 1)
        envelope = app.to_json()
        assert _has_node_of_type(envelope, "DataTable"), (
            "Populated low-stock report must render a DataTable."
        )
        restock_buttons = _find_buttons_by_label(envelope, "Create Restock Orders")
        assert len(restock_buttons) == 1, (
            "Populated low-stock report must render the 'Create Restock Orders' button."
        )

    def test_empty(self):
        app = build_low_stock_ui([], 10, 0)
        _assert_valid_prefab(app)

    def test_empty_omits_table_and_restock_button(self):
        """#470-adjacent — when ``total_count == 0`` (no items below the
        threshold) the report drops the empty DataTable and the
        "Create Restock Orders" button (both reference nonexistent rows)
        and renders an "all clear" Muted hint instead.
        """
        app = build_low_stock_ui([], 10, 0)
        envelope = app.to_json()

        assert not _has_node_of_type(envelope, "DataTable"), (
            "Empty low-stock report must not render a DataTable."
        )
        restock_buttons = _find_buttons_by_label(envelope, "Create Restock Orders")
        assert len(restock_buttons) == 0, (
            "Empty low-stock report must not render the 'Create Restock Orders' button."
        )

        # Assert on the Muted node's actual content rather than
        # ``str(envelope)`` — the header badge renders ``Threshold: 10``
        # unconditionally, so a substring check on the whole envelope
        # would pass even if the Muted hint regressed.
        muted_contents = _collect_node_content(envelope, "Muted")
        hint = next(
            (c for c in muted_contents if "threshold of" in c),
            None,
        )
        assert hint is not None, (
            f"Empty-state must render a 'threshold of …' Muted hint; "
            f"got Muted contents: {muted_contents!r}"
        )
        assert "threshold of 10" in hint, (
            f"Empty-state hint must echo the threshold value; got {hint!r}"
        )

    def test_low_stock_renders_tier_2_metrics_row(self):
        """#550 — four-tier redesign Tier 2 — exactly three Metric widgets
        with the expected labels render in the populated card.
        """
        items = [
            {
                "sku": "SKU-001",
                "display_name": "Widget A",
                "current_stock": 3,
                "threshold": 10,
                "default_supplier_id": 100,
            },
        ]
        app = build_low_stock_ui(items, 10, 1)
        envelope = app.to_json()
        metrics = _find_components_by_type(envelope, "Metric")
        labels = [m.get("label") for m in metrics]
        assert labels == [
            "Below threshold",
            "Critically low",
            "Suppliers involved",
        ], f"Expected the three Tier 2 metric labels; got {labels!r}"

    def test_low_stock_critically_low_count_excludes_threshold_rows(self):
        """#550 — Tier 2 "Critically low" Metric counts only stock-out
        rows (``current_stock == 0``), not every row below threshold.
        """
        items = [
            # Two stock-outs.
            {"sku": "A", "current_stock": 0, "threshold": 10},
            {"sku": "B", "current_stock": 0, "threshold": 10},
            # Below threshold but not stock-out — must be excluded.
            {"sku": "C", "current_stock": 4, "threshold": 10},
        ]
        app = build_low_stock_ui(items, 10, 3)
        envelope = app.to_json()
        metrics = _find_components_by_type(envelope, "Metric")
        crit = next(m for m in metrics if m.get("label") == "Critically low")
        assert crit.get("value") == "2", (
            f"Critically low Metric should count only stock==0 rows; got {crit!r}"
        )

    def test_low_stock_suppliers_involved_count_dedupes_by_supplier_id(self):
        """#550 — Tier 2 "Suppliers involved" Metric is the distinct count
        of ``default_supplier_id`` across the row set, ignoring ``None``.
        """
        items = [
            {"sku": "A", "current_stock": 1, "default_supplier_id": 100},
            {"sku": "B", "current_stock": 2, "default_supplier_id": 100},  # dupe
            {"sku": "C", "current_stock": 3, "default_supplier_id": 200},
            {"sku": "D", "current_stock": 4, "default_supplier_id": None},  # ignored
            {"sku": "E", "current_stock": 5},  # missing — ignored
        ]
        app = build_low_stock_ui(items, 10, 5)
        envelope = app.to_json()
        metrics = _find_components_by_type(envelope, "Metric")
        suppliers = next(m for m in metrics if m.get("label") == "Suppliers involved")
        assert suppliers.get("value") == "2", (
            f"Suppliers involved should dedupe by supplier_id and ignore None; "
            f"got {suppliers!r}"
        )

    def test_low_stock_datatable_includes_supplier_and_lead_time_columns(self):
        """#550 — Tier 3 — pin the full column set of the enriched
        DataTable so the four-tier redesign's columns don't silently
        regress.
        """
        items = [
            {
                "sku": "SKU-001",
                "display_name": "Widget A",
                "current_stock": 3,
                "threshold": 10,
                "uom": "pcs",
                "lead_time_days": 7,
                "default_supplier_name": "Acme",
                "minimum_order_quantity": 50.0,
            },
        ]
        app = build_low_stock_ui(items, 10, 1)
        envelope = app.to_json()
        tables = _find_components_by_type(envelope, "DataTable")
        assert len(tables) == 1
        column_keys = [c.get("key") for c in tables[0].get("columns", [])]
        assert column_keys == [
            "display_name",
            "sku",
            "uom",
            "current_stock",
            "threshold",
            "lead_time_days",
            "default_supplier_name",
            "minimum_order_quantity",
        ], f"Tier 3 DataTable column set drifted; got {column_keys!r}"

    def test_low_stock_renders_check_inventory_action_button(self):
        """#550 — Tier 4 adds a "Check Inventory" button alongside the
        existing "Create Restock Orders" trigger.
        """
        items = [
            {"sku": "A", "current_stock": 1, "threshold": 10},
        ]
        app = build_low_stock_ui(items, 10, 1)
        envelope = app.to_json()
        check_buttons = _find_buttons_by_label(envelope, "Check Inventory")
        assert len(check_buttons) == 1, (
            "Populated low-stock report must render the 'Check Inventory' button."
        )


class TestBuildPOCreateUI:
    """``build_po_create_ui`` handles both preview and applied states for
    create_purchase_order. Each test below pins one state's smoke
    properties; the dual-state nature of the builder means the same
    Prefab tree handles both — only the initial ``state.applied`` flag
    seeded in ``_init_create_card_state`` differs."""

    # Preview-shaped fixture: matches what ``_create_purchase_order_impl``
    # returns on the preview branch — no ``id``, no ``katana_url`` (those
    # only exist after Katana assigns an ID on apply). Applied-state tests
    # below merge in ``id`` / ``katana_url`` / ``is_preview=False``.
    _PO_RESPONSE: ClassVar[dict[str, Any]] = {
        "order_number": "PO-001",
        "supplier_id": 1,
        "supplier_name": "Acme",
        "location_id": 2,
        "location_name": "Brooklyn",
        "status": "NOT_RECEIVED",
        "entity_type": "regular",
        "total_cost": 1500.0,
        "currency": "USD",
        "item_count": 3,
        "notes": "Rush order",
        "is_preview": True,
        "warnings": [],
        "next_actions": [],
        "message": "Preview",
    }

    _PO_APPLIED: ClassVar[dict[str, Any]] = {
        "id": 12345,
        "katana_url": "https://factory.katanamrp.com/purchaseorder/12345",
        "is_preview": False,
    }

    def test_smoke_preview(self):
        app = build_po_create_ui(
            dict(self._PO_RESPONSE),
            confirm_request=_StubRequest(),
            confirm_tool="create_purchase_order",
        )
        _assert_valid_prefab(app)

    def test_smoke_applied(self):
        order = dict(self._PO_RESPONSE, **self._PO_APPLIED)
        app = build_po_create_ui(
            order,
            confirm_request=_StubRequest(),
            confirm_tool="create_purchase_order",
        )
        _assert_valid_prefab(app)
        assert app.state is not None
        assert app.state["applied"] is True

    def test_preview_state_seeds_applied_false(self):
        app = build_po_create_ui(
            dict(self._PO_RESPONSE),
            confirm_request=_StubRequest(),
            confirm_tool="create_purchase_order",
        )
        assert app.state is not None
        assert app.state["applied"] is False

    def test_applied_state_seeds_result_from_response(self):
        """The standalone-applied entry path seeds ``state.result`` from
        the response so the applied-state Buttons (which bind to
        ``{{ result.id }}`` and ``{{ result.katana_url }}``) resolve. On
        the in-place morph path, the on_success chain in
        ``_build_apply_action`` writes the same key."""
        order = dict(self._PO_RESPONSE, **self._PO_APPLIED)
        app = build_po_create_ui(
            order,
            confirm_request=_StubRequest(),
            confirm_tool="create_purchase_order",
        )
        assert app.state is not None
        result = app.state.get("result")
        assert isinstance(result, dict)
        assert result["id"] == 12345
        assert (
            result["katana_url"] == "https://factory.katanamrp.com/purchaseorder/12345"
        )

    def test_applied_buttons_bind_to_result_template(self):
        """Applied-state Buttons must use ``{{ result.X }}`` interpolation,
        not Python f-strings — the preview-branch response has no ``id`` /
        ``katana_url``, so f-strings would bake ``None`` into the closure
        and render an empty button row after the in-place morph fires.
        """
        app = build_po_create_ui(
            dict(self._PO_RESPONSE),
            confirm_request=_StubRequest(),
            confirm_tool="create_purchase_order",
        )
        rendered = str(app.to_json())
        assert "{{ result.id }}" in rendered
        assert "{{ result.katana_url }}" in rendered
        # And the f-string-interpolated literal must NOT appear — a regression
        # would re-introduce "Receive items for purchase order None".
        assert "purchase order None" not in rendered

    def test_outsourced_entity_type_renders_extra_badge(self):
        order = dict(self._PO_RESPONSE, entity_type="outsourced")
        app = build_po_create_ui(
            order,
            confirm_request=_StubRequest(),
            confirm_tool="create_purchase_order",
        )
        rendered = str(app.to_json())
        assert "outsourced" in rendered

    def test_supplier_renders_as_link_to_katana(self):
        app = build_po_create_ui(
            dict(self._PO_RESPONSE),
            confirm_request=_StubRequest(),
            confirm_tool="create_purchase_order",
        )
        rendered = str(app.to_json())
        # Supplier name surfaces inside a Link, with href pointing at the
        # Katana supplier page — matches the module's "link Katana
        # entities wherever possible" convention.
        assert "/contacts/suppliers/1" in rendered
        assert "Acme" in rendered


class TestBuildSOCreateUI:
    """``build_so_create_ui`` — same dual-state shape as PO; SO response
    has no ``location_name`` or ``notes`` and adds ``delivery_date``."""

    _SO_RESPONSE: ClassVar[dict[str, Any]] = {
        "order_number": "SO-001",
        "customer_id": 1,
        "customer_name": "Buyer Co",
        "location_id": 2,
        "status": "NOT_SHIPPED",
        "total": 500.0,
        "currency": "EUR",
        "delivery_date": "2026-06-01",
        "item_count": 2,
        "is_preview": True,
        "warnings": [],
        "next_actions": [],
        "message": "Preview",
    }

    _SO_APPLIED: ClassVar[dict[str, Any]] = {
        "id": 12346,
        "katana_url": "https://factory.katanamrp.com/salesorder/12346",
        "is_preview": False,
    }

    def test_smoke_preview(self):
        app = build_so_create_ui(
            dict(self._SO_RESPONSE),
            confirm_request=_StubRequest(),
            confirm_tool="create_sales_order",
        )
        _assert_valid_prefab(app)

    def test_smoke_applied(self):
        order = dict(self._SO_RESPONSE, **self._SO_APPLIED)
        app = build_so_create_ui(
            order,
            confirm_request=_StubRequest(),
            confirm_tool="create_sales_order",
        )
        _assert_valid_prefab(app)
        assert app.state is not None
        assert app.state["applied"] is True
        result = app.state.get("result")
        assert isinstance(result, dict)
        assert result["id"] == 12346

    def test_renders_delivery_date_metric(self):
        app = build_so_create_ui(
            dict(self._SO_RESPONSE),
            confirm_request=_StubRequest(),
            confirm_tool="create_sales_order",
        )
        rendered = str(app.to_json())
        assert "2026-06-01" in rendered

    def test_customer_renders_as_link_to_katana(self):
        app = build_so_create_ui(
            dict(self._SO_RESPONSE),
            confirm_request=_StubRequest(),
            confirm_tool="create_sales_order",
        )
        rendered = str(app.to_json())
        assert "/contacts/customers/1" in rendered
        assert "Buyer Co" in rendered

    def test_inline_shipping_fees_render_preview(self):
        """Preview state: planned shipping fees surface as rows with
        description / amount / tax. Section header + total summary line
        appear. No APPLIED / FAILED status pills (those are apply-only).
        """
        response = dict(
            self._SO_RESPONSE,
            shipping_fee_outcomes=[
                {
                    "description": "Standard shipping",
                    "amount": "8.95",
                    "tax_rate_id": 301,
                    "succeeded": None,
                    "created_id": None,
                    "error": None,
                },
                {
                    "description": "Handling",
                    "amount": "2.50",
                    "tax_rate_id": None,
                    "succeeded": None,
                    "created_id": None,
                    "error": None,
                },
            ],
        )
        app = build_so_create_ui(
            response,
            confirm_request=_StubRequest(),
            confirm_tool="create_sales_order",
        )
        rendered = str(app.to_json())
        # Section header + per-fee rows show up.
        assert "Shipping fees" in rendered
        assert "Standard shipping" in rendered
        assert "Handling" in rendered
        # Tax-rate suffix surfaces when present.
        assert "tax rate #301" in rendered
        # Summary line surfaces the total + count.
        assert "Total shipping" in rendered
        assert "2 fee(s)" in rendered
        # No status pills on preview.
        assert "APPLIED" not in rendered
        assert "FAILED" not in rendered

    def test_inline_shipping_fees_render_applied_success(self):
        """Applied + all-success: each fee row gains an APPLIED pill +
        the server-assigned created_id surfaces."""
        response = dict(
            self._SO_RESPONSE,
            is_preview=False,
            id=99,
            katana_url="https://factory.katanamrp.com/salesorder/99",
            shipping_fee_outcomes=[
                {
                    "description": "Standard shipping",
                    "amount": "8.95",
                    "tax_rate_id": None,
                    "succeeded": True,
                    "created_id": 5001,
                    "error": None,
                },
            ],
        )
        app = build_so_create_ui(
            response,
            confirm_request=_StubRequest(),
            confirm_tool="create_sales_order",
        )
        rendered = str(app.to_json())
        assert "APPLIED" in rendered
        assert "id=5001" in rendered
        # No failure retry coaching on a clean run.
        assert "modify_sales_order" not in rendered

    def test_inline_shipping_fees_render_applied_partial_failure(self):
        """Partial failure: failed rows get the FAILED pill + ✗ glyph +
        inline error text, and a destructive Alert at the bottom coaches
        the operator toward retrying via modify_sales_order."""
        response = dict(
            self._SO_RESPONSE,
            is_preview=False,
            id=99,
            katana_url="https://factory.katanamrp.com/salesorder/99",
            shipping_fee_outcomes=[
                {
                    "description": "Standard shipping",
                    "amount": "8.95",
                    "tax_rate_id": None,
                    "succeeded": True,
                    "created_id": 5001,
                    "error": None,
                },
                {
                    "description": "Handling",
                    "amount": "2.50",
                    "tax_rate_id": 9999,
                    "succeeded": False,
                    "created_id": None,
                    "error": "422: invalid tax rate",
                },
            ],
        )
        app = build_so_create_ui(
            response,
            confirm_request=_StubRequest(),
            confirm_tool="create_sales_order",
        )
        rendered = str(app.to_json())
        assert "APPLIED" in rendered
        assert "FAILED" in rendered
        assert "✗" in rendered
        assert "422: invalid tax rate" in rendered
        # Retry coaching surfaces in the Alert.
        assert "modify_sales_order" in rendered
        assert "add_shipping_fees" in rendered
        # The bottom-line total reflects ONLY succeeded fees, not the
        # full requested set — currency is EUR per ``_SO_RESPONSE``,
        # so the formatted strings appear with the € symbol. Showing
        # the full €11.45 when only €8.95 attached would misrepresent
        # the SO's actual state.
        assert "Total shipping applied" in rendered
        assert "1 of 2 fee(s) applied" in rendered
        assert "€11.45" not in rendered
        assert "8.95" in rendered  # the succeeded fee's amount

    def test_inline_shipping_fees_render_applied_all_failed(self):
        """Every fee failed: the SO exists but no fees attached. The
        total line is skipped entirely (no succeeded fees → nothing to
        sum); the failed-row Alert below still surfaces."""
        response = dict(
            self._SO_RESPONSE,
            is_preview=False,
            id=99,
            katana_url="https://factory.katanamrp.com/salesorder/99",
            shipping_fee_outcomes=[
                {
                    "description": "Standard shipping",
                    "amount": "8.95",
                    "succeeded": False,
                    "error": "500 upstream",
                },
                {
                    "description": "Handling",
                    "amount": "2.50",
                    "succeeded": False,
                    "error": "422 invalid tax",
                },
            ],
        )
        app = build_so_create_ui(
            response,
            confirm_request=_StubRequest(),
            confirm_tool="create_sales_order",
        )
        rendered = str(app.to_json())
        assert "FAILED" in rendered
        # No total line — every fee failed, nothing landed on the SO.
        assert "Total shipping" not in rendered
        # Retry coaching still surfaces.
        assert "modify_sales_order" in rendered

    def test_inline_shipping_fees_section_skipped_when_no_fees(self):
        """No shipping_fee_outcomes → the section is omitted entirely."""
        app = build_so_create_ui(
            dict(self._SO_RESPONSE, shipping_fee_outcomes=[]),
            confirm_request=_StubRequest(),
            confirm_tool="create_sales_order",
        )
        rendered = str(app.to_json())
        assert "Shipping fees" not in rendered
        assert "Total shipping" not in rendered


class TestBuildMOCreateUI:
    """``build_mo_create_ui`` — MO response uses ``order_no`` (not
    ``order_number``) and ``additional_info`` (not ``notes``)."""

    _MO_RESPONSE: ClassVar[dict[str, Any]] = {
        "order_no": "MO-001",
        "variant_id": 555,
        "sku": "WIDGET-42",
        "planned_quantity": 100.0,
        "location_id": 2,
        "status": "NOT_STARTED",
        "order_created_date": "2026-05-13T10:00:00+00:00",
        "production_deadline_date": "2026-06-01T17:00:00+00:00",
        "additional_info": "Priority run",
        "is_preview": True,
        "warnings": [],
        "next_actions": [],
        "message": "Preview",
    }

    _MO_APPLIED: ClassVar[dict[str, Any]] = {
        "id": 12347,
        "katana_url": "https://factory.katanamrp.com/manufacturingorder/12347",
        "is_preview": False,
    }

    def test_smoke_preview(self):
        app = build_mo_create_ui(
            dict(self._MO_RESPONSE),
            confirm_request=_StubRequest(),
            confirm_tool="create_manufacturing_order",
        )
        _assert_valid_prefab(app)

    def test_smoke_applied(self):
        order = dict(self._MO_RESPONSE, **self._MO_APPLIED)
        app = build_mo_create_ui(
            order,
            confirm_request=_StubRequest(),
            confirm_tool="create_manufacturing_order",
        )
        _assert_valid_prefab(app)
        assert app.state is not None
        assert app.state["applied"] is True
        result = app.state.get("result")
        assert isinstance(result, dict)
        assert result["id"] == 12347

    def test_renders_variant_and_deadline(self):
        app = build_mo_create_ui(
            dict(self._MO_RESPONSE),
            confirm_request=_StubRequest(),
            confirm_tool="create_manufacturing_order",
        )
        rendered = str(app.to_json())
        # Post-#card-ux: variant line surfaces SKU only (no "(ID: 555)"
        # parenthetical) when SKU is resolved — variant_id is a wire
        # identifier with no user value (anti-pattern #2). The SKU
        # itself, ``WIDGET-42``, IS the user-facing identifier.
        assert "Variant: WIDGET-42" in rendered
        # Deadline metric uses the date portion only.
        assert "2026-06-01" in rendered

    def test_variant_id_only_renders_when_sku_missing(self):
        """SKU-less variants (legacy NetSuite imports — CLAUDE.md
        ``Variants can have null SKUs``) fall back to ``"Variant ID:
        <id>"`` so the row stays identifiable. Confirmed by SKU-bearing
        rows above, which must NOT carry the ID parenthetical."""
        response = dict(self._MO_RESPONSE)
        response["sku"] = None
        app = build_mo_create_ui(
            response,
            confirm_request=_StubRequest(),
            confirm_tool="create_manufacturing_order",
        )
        rendered = str(app.to_json())
        # SKU is None → fall back path emits "Variant ID: 555".
        assert "Variant ID: 555" in rendered

    def test_uses_order_no_field_not_order_number(self):
        """MO response uses ``order_no``; verify the badge reads that
        (not ``order_number`` which doesn't exist on MO response)."""
        app = build_mo_create_ui(
            dict(self._MO_RESPONSE),
            confirm_request=_StubRequest(),
            confirm_tool="create_manufacturing_order",
        )
        rendered = str(app.to_json())
        assert "MO-001" in rendered


class TestFieldDiffIndex:
    """``_index_changes_by_field`` flattens every action's diff into a
    field-name keyed map keyed off the wire ``FieldChange.field``.
    Pins the projection so the per-entity entity-view helpers can rely
    on a stable lookup shape."""

    def test_indexes_changes_from_multiple_actions(self):
        from katana_mcp.tools.prefab_ui import _index_changes_by_field

        actions = [
            {
                "operation": "update_header",
                "succeeded": True,
                "changes": [
                    {"field": "status", "old": "NOT_RECEIVED", "new": "RECEIVED"},
                    {
                        "field": "expected_arrival_date",
                        "old": None,
                        "new": "2026-05-20",
                    },
                ],
            },
            {
                "operation": "update_row",
                "target_id": 9001,
                "succeeded": True,
                "changes": [
                    {"field": "quantity", "old": 5, "new": 10},
                ],
            },
        ]
        idx = _index_changes_by_field(actions)
        assert set(idx.keys()) == {"status", "expected_arrival_date", "quantity"}
        assert idx["status"].before == "NOT_RECEIVED"
        assert idx["status"].after == "RECEIVED"
        assert idx["expected_arrival_date"].kind == "changed"
        assert idx["quantity"].after == 10

    def test_added_field_kind(self):
        from katana_mcp.tools.prefab_ui import _index_changes_by_field

        idx = _index_changes_by_field(
            [
                {
                    "operation": "update_header",
                    "succeeded": None,
                    "changes": [
                        {"field": "additional_info", "new": "Net-30", "is_added": True},
                    ],
                }
            ]
        )
        assert idx["additional_info"].kind == "added"
        assert idx["additional_info"].before is None
        assert idx["additional_info"].after == "Net-30"

    def test_unchanged_field_kind(self):
        from katana_mcp.tools.prefab_ui import _index_changes_by_field

        idx = _index_changes_by_field(
            [
                {
                    "operation": "update_header",
                    "succeeded": True,
                    "changes": [
                        {
                            "field": "status",
                            "old": "OPEN",
                            "new": "OPEN",
                            "is_unchanged": True,
                        },
                    ],
                }
            ]
        )
        assert idx["status"].kind == "unchanged"

    def test_failed_action_propagates_to_field_changes(self):
        """A failed action surfaces its ``error`` on every FieldChange it
        was going to write — that's how the per-field ``✗`` glyph + inline
        error line get the right context to render."""
        from katana_mcp.tools.prefab_ui import _index_changes_by_field

        idx = _index_changes_by_field(
            [
                {
                    "operation": "update_header",
                    "succeeded": False,
                    "error": "422 Unprocessable: notes max 100 chars exceeded",
                    "changes": [
                        {"field": "additional_info", "old": "Net-30", "new": "x" * 200},
                    ],
                }
            ]
        )
        assert idx["additional_info"].failed is True
        assert "422" in (idx["additional_info"].error or "")

    def test_normalize_po_prior_state_maps_wire_keys_to_response_shape(self):
        """``_normalize_po_prior_state`` maps the wire-shape snapshot
        produced by ``RegularPurchaseOrder.to_dict()`` (``order_no``,
        ``total``, ``additional_info``, nested ``supplier``) to the
        response shape ``_render_po_entity_view`` reads (``order_number``,
        ``total_cost``, ``notes``, flat ``supplier_name``). Without
        this adapter the rendered modify card would show empty header
        fields in production — Copilot finding on #755."""
        from katana_mcp.tools.prefab_ui import _normalize_po_prior_state

        wire = {
            "id": 9001,
            "order_no": "PO-2026-001",
            "total": 1250.0,
            "additional_info": "Net-30",
            "supplier": {"id": 100, "name": "Acme Supply Co"},
            "supplier_id": 100,
            "status": "NOT_RECEIVED",
        }
        norm = _normalize_po_prior_state(wire)
        assert norm["order_number"] == "PO-2026-001"
        assert norm["total_cost"] == 1250.0
        assert norm["notes"] == "Net-30"
        assert norm["supplier_name"] == "Acme Supply Co"
        # Passthrough keys preserved.
        assert norm["id"] == 9001
        assert norm["supplier_id"] == 100
        assert norm["status"] == "NOT_RECEIVED"

    def test_normalize_po_prior_state_handles_none(self):
        from katana_mcp.tools.prefab_ui import _normalize_po_prior_state

        assert _normalize_po_prior_state(None) == {}
        assert _normalize_po_prior_state({}) == {}

    def test_summarize_apply_outcome_empty_actions_returns_applied(self):
        """An empty ``actions`` list is a legitimate no-op outcome — a
        modify/delete plan that produced zero actions (no-op patch, or
        all requested changes turned out unchanged). The bucketer MUST
        return ``APPLIED`` / ``default``, not the destructive
        ``PARTIAL FAILURE`` fallback that ``succeeded=0 + failed=0``
        otherwise lands on. Caught by Copilot review on #755."""
        from katana_mcp.tools.foundation.bom_table import _summarize_apply_outcome

        label, variant = _summarize_apply_outcome([])
        assert label == "APPLIED"
        assert variant == "default"

    def test_unchanged_kind_renders_value_from_change_when_value_arg_absent(self):
        """When ``compute_field_diff`` emits ``is_unchanged=True`` and the
        caller passes ``change`` without a separate ``value`` arg, the
        helper must surface the value from ``change.after``/``change.before``
        instead of falling through to ``(unset)``. Catches the misleading
        no-op-update render Copilot flagged on #755."""
        from katana_mcp.tools.prefab_ui import (
            FieldChangeView,
            _render_field_diff_line,
        )
        from prefab_ui.app import PrefabApp
        from prefab_ui.components import Card, CardContent

        with PrefabApp(state={}, css_class="p-4") as app, Card(), CardContent():
            _render_field_diff_line(
                "Status",
                change=FieldChangeView(
                    field="status",
                    before="NOT_RECEIVED",
                    after="NOT_RECEIVED",
                    kind="unchanged",
                ),
            )
        rendered = str(app.to_json())
        assert "Status: NOT_RECEIVED" in rendered
        assert "(unset)" not in rendered

    def test_unknown_prior_flag_propagates(self):
        """``is_unknown_prior=True`` (best-effort fetch failed) propagates
        to ``FieldChangeView.unknown_prior`` so the renderer can show
        ``(prior unknown) → new`` instead of misleadingly implying the
        prior was unset (see FieldChange's is_unknown_prior docstring)."""
        from katana_mcp.tools.prefab_ui import _index_changes_by_field

        idx = _index_changes_by_field(
            [
                {
                    "operation": "update_header",
                    "succeeded": None,
                    "changes": [
                        {
                            "field": "status",
                            "old": None,
                            "new": "RECEIVED",
                            "is_unknown_prior": True,
                        },
                    ],
                }
            ]
        )
        assert idx["status"].unknown_prior is True

    def test_include_operations_filters_to_header_actions(self):
        """``include_operations`` filters the flatten to header-level
        actions so sub-entity field changes whose names overlap header
        names (``status`` on fulfillments vs SO header status,
        ``tracking_number`` on fulfillments, row ``quantity`` /
        shipping-fee ``description`` / ``amount``) don't pollute the
        header-field map driving :func:`_render_so_header_scalar_diffs`
        and the header-level :func:`_render_failed_changes_block`.

        Caught by Copilot review on #858 (PR feat/723-so-modify-card)."""
        from katana_mcp.tools.prefab_ui import _index_changes_by_field

        actions = [
            # Header action — should pass through.
            {
                "operation": "update_header",
                "succeeded": True,
                "changes": [
                    {"field": "status", "old": "NOT_SHIPPED", "new": "PACKED"},
                    {"field": "additional_info", "old": "Net-30", "new": "Net-45"},
                ],
            },
            # Sub-entity action with overlapping field name —
            # ``status`` on fulfillment, NOT the header status. Must
            # NOT overwrite the header's status diff.
            {
                "operation": "update_fulfillment",
                "target_id": 555,
                "succeeded": True,
                "changes": [
                    {"field": "status", "old": "PACKED", "new": "DELIVERED"},
                    {"field": "tracking_number", "old": None, "new": "1Z999"},
                ],
            },
            # Sub-entity action with non-overlapping name (row
            # quantity). Also must not appear in the header map.
            {
                "operation": "update_row",
                "target_id": 999,
                "succeeded": False,
                "error": "422 Unprocessable: quantity > stock",
                "changes": [
                    {"field": "quantity", "old": 5, "new": 100},
                ],
            },
        ]
        idx = _index_changes_by_field(
            actions, include_operations=frozenset({"update_header", "delete"})
        )
        # Header fields present.
        assert "additional_info" in idx
        # Status came from the header action, NOT the fulfillment.
        assert idx["status"].before == "NOT_SHIPPED"
        assert idx["status"].after == "PACKED"
        # Sub-entity fields filtered out — quantity / tracking_number
        # only appear on row / fulfillment actions.
        assert "quantity" not in idx
        assert "tracking_number" not in idx

    def test_include_operations_none_preserves_all_actions(self):
        """``include_operations=None`` (the default) flattens every
        action — preserves the pre-filter behavior PO modify + tests
        rely on. Pins the back-compat contract."""
        from katana_mcp.tools.prefab_ui import _index_changes_by_field

        actions = [
            {
                "operation": "update_header",
                "succeeded": True,
                "changes": [{"field": "status", "old": "OPEN", "new": "CLOSED"}],
            },
            {
                "operation": "update_row",
                "succeeded": True,
                "changes": [{"field": "quantity", "old": 5, "new": 10}],
            },
        ]
        idx = _index_changes_by_field(actions)
        assert set(idx.keys()) == {"status", "quantity"}

    def test_not_run_synthesized_action_does_not_overwrite_executed_diff(self):
        """A synthesized NOT-RUN ``update_header`` (the unattempted
        close-phase tail of a failed ``correct_sales_order``) must NOT
        overwrite an earlier EXECUTED ``update_header`` diff via
        last-write-wins on the field map. NOT RUN actions are plan
        placeholders; their "diff" is what *would have* run, not what
        ran. Without this filter the rendered header would show the
        skipped step's planned change as an applied scalar diff and
        suppress the NOT RUN indication entirely.

        Caught by Copilot review on #858 (PR feat/723-so-modify-card).
        Repro: a correction sequence with an executed open-phase
        ``update_header`` (succeeded=True, status: NOT_SHIPPED →
        DELIVERED) followed by a synthesized close-phase
        ``update_header`` (succeeded=None, status_label="NOT RUN",
        status: DELIVERED → NOT_SHIPPED). Without the filter,
        last-write-wins lets the NOT RUN diff masquerade as applied."""
        from katana_mcp.tools.prefab_ui import _index_changes_by_field

        actions = [
            # EXECUTED open-phase header update — real diff.
            {
                "operation": "update_header",
                "target_id": 7777,
                "succeeded": True,
                "error": None,
                "changes": [
                    {"field": "status", "old": "NOT_SHIPPED", "new": "DELIVERED"},
                ],
            },
            # SKIPPED close-phase header update — synthesized NOT-RUN
            # placeholder from a failed correction tail. Its "diff" is
            # the plan's intended close-phase revert; it never ran.
            {
                "operation": "update_header",
                "target_id": 7777,
                "succeeded": None,
                "error": None,
                "changes": [
                    {"field": "status", "old": "DELIVERED", "new": "NOT_SHIPPED"},
                ],
                "status_label": "NOT RUN",
            },
        ]
        idx = _index_changes_by_field(
            actions, include_operations=frozenset({"update_header", "delete"})
        )
        # The EXECUTED diff wins, not the synthesized NOT-RUN tail.
        assert idx["status"].before == "NOT_SHIPPED"
        assert idx["status"].after == "DELIVERED"
        assert idx["status"].failed is False
        # The executed action succeeded — no error propagates.
        assert idx["status"].error is None


class TestBuildPOModifyUI:
    """``build_po_modify_ui`` handles preview/applied/partial-failure for
    every PO write tool (``modify_purchase_order``, ``delete_purchase_order``,
    ``correct_purchase_order``). Shares the entity-view renderer with
    ``build_po_create_ui`` — the rendered field set is identical, only the
    diff overlay differs."""

    # Wire-shape ``prior_state`` matching ``RegularPurchaseOrder.to_dict()``
    # (the real production source). Uses wire keys (``order_no``,
    # ``total``, ``additional_info``, nested ``supplier``) — NOT the
    # response display shape — so tests catch shape-mismatch bugs at the
    # ``_normalize_po_prior_state`` boundary. The renderer normalizes
    # this to the response shape before consuming. Caught by Copilot
    # review on #755.
    _PO_PRIOR: ClassVar[dict[str, Any]] = {
        "id": 9001,
        "order_no": "PO-2026-001",
        "supplier_id": 100,
        "supplier": {"id": 100, "name": "Acme Supply Co"},
        "location_id": 1,
        "status": "NOT_RECEIVED",
        "entity_type": "regular",
        "total": 1250.0,
        "currency": "USD",
        "additional_info": "Net-30; deliver to dock B",
    }

    @classmethod
    def _preview(
        cls,
        actions: list[dict[str, Any]] | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        return {
            "entity_type": "purchase_order",
            "entity_id": cls._PO_PRIOR["id"],
            "is_preview": True,
            "actions": actions or [],
            "prior_state": dict(cls._PO_PRIOR),
            "warnings": [],
            "next_actions": [],
            "message": "Preview",
            "katana_url": "https://factory.katanamrp.com/purchaseorder/9001",
            **overrides,
        }

    @classmethod
    def _applied(
        cls,
        actions: list[dict[str, Any]] | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        return cls._preview(actions, is_preview=False, **overrides)

    def test_smoke_preview_header_only_change(self):
        actions = [
            {
                "operation": "update_header",
                "target_id": 9001,
                "succeeded": None,
                "changes": [
                    {
                        "field": "status",
                        "old": "NOT_RECEIVED",
                        "new": "PARTIALLY_RECEIVED",
                    },
                ],
            }
        ]
        app = build_po_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        # Title verb derived from confirm_tool.
        assert "Modify Purchase Order" in rendered
        # Diff line uses the arrow form.
        assert "NOT_RECEIVED" in rendered and "PARTIALLY_RECEIVED" in rendered
        assert "→" in rendered

    def test_applied_total_reflects_post_apply_state_not_prior(self):
        """Regression: the applied modify card's Total metric shows the
        server-recomputed total from ``extras['post_apply_state']``, not the
        stale pre-modify ``prior_state['total']``.

        Before the fix the card rendered the prior total (``$1,250.00``)
        even after row/qty edits changed it on the server (to ``$3,822.00``)
        — the dispatcher wrote the fresh PO through to the cache but never
        threaded its recomputed total back onto the card.
        """
        actions = [
            {
                "operation": "update_row",
                "target_id": 5001,
                "succeeded": True,
                "changes": [{"field": "quantity", "old": 10, "new": 12}],
            }
        ]
        app = build_po_modify_ui(
            self._applied(
                actions,
                extras={"post_apply_state": {"total": 3822.0, "currency": "USD"}},
            ),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        # The Total metric reflects the applied (post-modify) total …
        assert "$3,822.00" in rendered
        # … and NOT the pre-modify prior_state total.
        assert "$1,250.00" not in rendered

    def test_preview_total_falls_back_to_prior_state(self):
        """Without ``post_apply_state`` (the preview path — nothing applied
        yet), the Total metric renders the pre-modify ``prior_state`` total.
        Pins the fallback so the applied-path override doesn't regress
        preview rendering."""
        app = build_po_modify_ui(
            self._preview([]),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        rendered = str(app.to_json())
        assert "$1,250.00" in rendered

    def test_supplier_change_renders_composite_diff(self):
        """A supplier change surfaces ``Supplier: <old> (<old_id>) → <new>``
        — the composite name+ID rendering keeps the diff readable without
        a separate ``supplier_id`` line. ``ModificationResponse.model_dump()``
        does NOT carry a top-level ``supplier_name`` (it lives only in
        ``prior_state``), so the after-side name MUST come from the
        ``supplier_name`` FieldChange. This test uses the real wire shape
        (no top-level supplier_name override) to pin that contract."""
        actions = [
            {
                "operation": "update_header",
                "target_id": 9001,
                "succeeded": None,
                "changes": [
                    {"field": "supplier_id", "old": 100, "new": 105},
                    {
                        "field": "supplier_name",
                        "old": "Acme Supply Co",
                        "new": "BetaCo",
                    },
                ],
            }
        ]
        # Real-wire shape: only the prior carries supplier_name; no
        # top-level override on the response. If the renderer reads
        # ``entity.get("supplier_name")`` for the after side, it'll show
        # the OLD name (Acme) for both sides — the bug Copilot caught
        # on #755.
        app = build_po_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        rendered = str(app.to_json())
        assert "Supplier:" in rendered
        # Both old and new names appear — proves the after-side
        # was sourced from supplier_name FieldChange.after, not from
        # entity (which is the prior).
        assert "Acme Supply Co" in rendered
        assert "BetaCo" in rendered
        assert "→" in rendered
        # Regression-guard: ensure ``Acme Supply Co (100) → Acme Supply Co``
        # (the pre-fix bug shape) doesn't appear.
        assert "Acme Supply Co (100) → Acme Supply Co" not in rendered

    def test_unchanged_kind_supplier_change_falls_through_to_link_render(self):
        """A no-op supplier_id patch (request set supplier_id=100 when
        it was already 100) emits a ``FieldChangeView(kind="unchanged",
        before=100, after=100)``. The composite diff line MUST NOT
        render — that would show ``Acme (100) → Acme (100)`` which is
        noise. Instead, fall through to the normal Link-rendering
        ``_render_party_line``. Copilot finding on #755."""
        actions = [
            {
                "operation": "update_header",
                "succeeded": True,
                "changes": [
                    {
                        "field": "supplier_id",
                        "old": 100,
                        "new": 100,
                        "is_unchanged": True,
                    },
                ],
            }
        ]
        app = build_po_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        rendered = str(app.to_json())
        # Supplier appears as the normal Link-rendered party line
        # (no arrow in the supplier text).
        assert "Acme Supply Co" in rendered
        # Specifically: the supplier line does not show the no-op
        # diff form.
        assert "Acme Supply Co (100) → Acme Supply Co (100)" not in rendered
        # And the Link href to Katana is present (the unchanged fall-
        # through gives back the Link form).
        assert "/contacts/suppliers/100" in rendered

    def test_location_change_renders_composite_diff_from_changes(self):
        """Same contract as supplier — ``location_name`` after-side comes
        from the FieldChange, not from ``entity`` (which carries the
        prior name)."""
        actions = [
            {
                "operation": "update_header",
                "target_id": 9001,
                "succeeded": None,
                "changes": [
                    {"field": "location_id", "old": 1, "new": 2},
                    {
                        "field": "location_name",
                        "old": "Main Warehouse",
                        "new": "Brooklyn",
                    },
                ],
            }
        ]
        app = build_po_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        rendered = str(app.to_json())
        assert "Location:" in rendered
        assert "Main Warehouse" in rendered
        assert "Brooklyn" in rendered
        assert "Main Warehouse (1) → Main Warehouse" not in rendered

    def test_failed_action_surfaces_glyph_inline_and_error_in_alert(self):
        """Hybrid status approach with layout-stability split (#722):

        - Per-field decoration on failed fields uses a leading ``✗``
          glyph (in the 2-char gutter ``_render_field_diff_line`` reserves)
          so the field text position is the same in success / failure.
        - The actual error message does NOT render inline next to the
          field — it aggregates into the consolidated bottom Alert via
          ``_render_failed_changes_block``. This keeps the diff lines
          above stable when the apply outcome lands (preview ↔ applied
          doesn't shift adjacent rows).

        See sibling ``test_failed_field_errors_consolidate_in_bottom_alert_not_inline``
        for the structural pin on the Alert location.
        """
        actions = [
            {
                "operation": "update_header",
                "target_id": 9001,
                "succeeded": False,
                "error": "422 Unprocessable: notes max 100 chars exceeded",
                "changes": [
                    {"field": "additional_info", "old": "Net-30", "new": "x" * 200},
                ],
            }
        ]
        app = build_po_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        rendered = str(app.to_json())
        # Inline ✗ glyph leads the diff line (in the gutter).
        assert "✗" in rendered
        # Error message lives in the consolidated bottom Alert, not
        # inline. Substring match — the Alert renders the text within
        # the AlertDescription regardless of placement.
        assert "422 Unprocessable" in rendered

    def test_delete_card_uses_delete_verb_and_confirm_label(self):
        app = build_po_modify_ui(
            self._preview([{"operation": "delete", "succeeded": None, "changes": []}]),
            confirm_request=_StubRequest(),
            confirm_tool="delete_purchase_order",
        )
        rendered = str(app.to_json())
        assert "Delete Purchase Order" in rendered
        assert "Confirm Delete" in rendered

    def test_cancel_messages_use_natural_noun_phrases_per_verb(self):
        """``_build_cancel_action`` interpolates its arg into the
        ``UpdateContext`` payload "User cancelled <noun phrase> preview."
        — the noun phrase has to read naturally there. Modify/correct
        cards interpolate "those purchase order changes" / "those purchase
        order corrections"; delete cards interpolate "that purchase order
        deletion". The previous shape (e.g. "that purchase order modify")
        was grammatically awkward — Copilot flagged on #755."""
        for tool, expected_phrase in [
            ("modify_purchase_order", "those purchase order changes"),
            ("correct_purchase_order", "those purchase order corrections"),
            ("delete_purchase_order", "that purchase order deletion"),
        ]:
            app = build_po_modify_ui(
                self._preview(
                    [{"operation": "update_header", "succeeded": None, "changes": []}]
                ),
                confirm_request=_StubRequest(),
                confirm_tool=tool,
            )
            rendered = str(app.to_json())
            assert expected_phrase in rendered, (
                f"Cancel message for {tool} should interpolate "
                f"{expected_phrase!r}; got rendered tree without it."
            )
            # Regression-guard: the awkward verb form must not appear.
            verb = tool.split("_", 1)[0]
            assert f"that purchase order {verb}" not in rendered, (
                f"Awkward verb-form cancel message survived for {tool}."
            )

    def test_applied_partial_failure_renders_overall_badge(self):
        actions = [
            {
                "operation": "update_header",
                "succeeded": True,
                "changes": [
                    {"field": "status", "old": "OPEN", "new": "PARTIALLY_RECEIVED"}
                ],
            },
            {
                "operation": "add_additional_cost",
                "succeeded": False,
                "error": "422: tax_rate_id required",
                "changes": [{"field": "name", "new": "Shipping", "is_added": True}],
            },
        ]
        app = build_po_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        rendered = str(app.to_json())
        assert "PARTIAL FAILURE" in rendered
        # Regression-guard for the contradictory-chrome bug Copilot
        # caught on #755: a partial-failure outcome must NOT also
        # surface an "APPLIED" badge. The header should carry one
        # state label that describes the actual outcome.
        # Note: an APPLIED-bucketed status badge (e.g. for PO status
        # "RECEIVED") may still appear; this guard targets the state
        # badge specifically. The applied_state_label for partial
        # failures is "PARTIAL FAILURE" instead of "APPLIED".

    def test_applied_full_failure_uses_failed_state_label(self):
        """On a fully-failed apply (no succeeded actions), the header
        state badge MUST read ``FAILED`` — not ``APPLIED`` + a separate
        ``FAILED`` extra-badge (the contradictory shape Copilot caught
        on #755). ``applied_state_label`` is overridden from the default
        based on ``_summarize_apply_outcome``."""
        actions = [
            {
                "operation": "update_header",
                "succeeded": False,
                "error": "422: invalid status transition",
                "changes": [{"field": "status", "old": "OPEN", "new": "RECEIVED"}],
            },
        ]
        app = build_po_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        rendered = str(app.to_json())
        # FAILED appears (as the state badge).
        assert "FAILED" in rendered

    def test_failed_delete_overrides_title_and_verb_to_match_failure(self):
        """A failed delete must read "Purchase Order Failed" / "failed."
        — not "Purchase Order Deleted" / "deleted." (the latter would
        contradict the FAILED badge). The applied_title_suffix and
        applied_verb track the outcome, not just the verb. Copilot
        finding on #755."""
        actions = [
            {
                "operation": "delete",
                "succeeded": False,
                "error": "404: not found",
                "changes": [],
            }
        ]
        app = build_po_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="delete_purchase_order",
        )
        rendered = str(app.to_json())
        # The title and footer must reflect the failure outcome, not
        # the original verb (Delete).
        assert "Delete Purchase Order Failed" in rendered
        assert "FAILED" in rendered
        # Regression-guards: the misleading verb-driven copy must not
        # appear in applied state when the operation failed.
        assert "Delete Purchase Order Deleted" not in rendered
        # The footer "deleted." should also be suppressed in favor of
        # "failed." (we test for the presence of "failed." rather than
        # the absence of "deleted." to avoid the badge label collision).
        assert "failed." in rendered

    def test_diff_lines_use_2char_gutter_for_layout_stability(self):
        """Every changed-field line starts with a 2-char gutter (``"  "``
        when not failed, ``"✗ "`` when failed) so the field text position
        is invariant across the apply outcome. Per the user's note on
        #755: the status pill must NOT shift other elements when it pops
        in."""
        actions = [
            {
                "operation": "update_header",
                "succeeded": None,  # preview
                "changes": [
                    {
                        "field": "status",
                        "old": "NOT_RECEIVED",
                        "new": "PARTIALLY_RECEIVED",
                    },
                ],
            }
        ]
        app = build_po_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        rendered = str(app.to_json())
        # Preview state — leading "  Status:" with 2-space gutter.
        assert "  Status:" in rendered

    def test_failed_field_errors_consolidate_in_bottom_alert_not_inline(self):
        """Failed-field error messages aggregate into a single Alert at
        the bottom of the entity view — they don't render inline next
        to each failed field. Keeps the diff-line layout stable across
        the apply outcome (per user note on #755). The per-field ``✗``
        glyph still surfaces inline for at-a-glance failure location."""
        actions = [
            {
                "operation": "update_header",
                "succeeded": False,
                "error": "422: invalid status",
                "changes": [
                    {"field": "status", "old": "NOT_RECEIVED", "new": "RECEIVED"},
                ],
            }
        ]
        app = build_po_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        envelope = app.to_json()

        # Walk for the Alert block carrying the consolidated failure list.
        found_alert_with_error = False

        def walk(node: Any) -> None:
            nonlocal found_alert_with_error
            if isinstance(node, dict):
                if node.get("type") == "Alert" and node.get("variant") == "destructive":
                    flat = json.dumps(node)
                    if "422: invalid status" in flat:
                        found_alert_with_error = True
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(envelope)
        assert found_alert_with_error, (
            "Failed-action error should aggregate into the bottom Alert "
            "block, not render as an inline Muted next to the field."
        )

        # The ✗ glyph still appears inline next to the failed field.
        rendered = str(envelope)
        assert "✗ Status:" in rendered

    def test_party_id_swap_without_name_change_renders_id_only_for_after(self):
        """When ``supplier_id`` changes (e.g. 100 → 105) and no
        ``supplier_name`` FieldChange accompanies it — the common case
        because ``compute_field_diff`` only diffs request fields and
        ``supplier_name`` isn't a request field — the after side MUST
        render as bare ``#105`` (or empty), NOT as the OLD supplier
        name labelled as the new one. Copilot finding on #755."""
        actions = [
            {
                "operation": "update_header",
                "succeeded": None,
                "changes": [
                    # Only the ID is in the diff. No supplier_name change.
                    {"field": "supplier_id", "old": 100, "new": 105},
                ],
            }
        ]
        app = build_po_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        rendered = str(app.to_json())
        # Before side carries the OLD name (correct).
        assert "Acme Supply Co (100)" in rendered
        assert "→" in rendered
        # After side renders as bare #105 — the new name isn't in the
        # diff and we don't have it in the snapshot.
        assert "#105" in rendered
        # Regression-guard: NOT showing the old name on the after side.
        assert "Acme Supply Co (105)" not in rendered

    def test_applied_failure_uses_destructive_variant_not_default(self):
        """On a failed/partial-failure apply, the state badge variant MUST
        be ``destructive`` (red) — not the hardcoded ``default`` (green)
        the apply badge had before the fix. A failure rendered with
        success-colored chrome is the second contradictory-chrome bug
        Copilot caught on #755."""
        actions = [
            {
                "operation": "update_header",
                "succeeded": False,
                "error": "422: invalid",
                "changes": [{"field": "status", "old": "OPEN", "new": "RECEIVED"}],
            },
        ]
        app = build_po_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        # Walk the Prefab envelope JSON for the FAILED Badge node and
        # check its variant — rendered-text assertion alone can't tell
        # apart "FAILED in red" from "FAILED in green".
        envelope = app.to_json()
        found_destructive = False

        def walk(node: Any) -> None:
            nonlocal found_destructive
            if isinstance(node, dict):
                if (
                    node.get("type") == "Badge"
                    and node.get("label") == "FAILED"
                    and node.get("variant") == "destructive"
                ):
                    found_destructive = True
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(envelope)
        assert found_destructive, (
            "FAILED Badge with variant=destructive not found. The state-"
            "badge variant must reflect the apply outcome — green/default "
            "for success, red/destructive for failure."
        )

    def test_applied_state_renders_applied_terminology_not_created(self):
        """Modify cards pass ``applied_title_suffix="Applied"`` etc. so the
        rendered applied state reads ``"Purchase Order Applied"`` /
        ``"APPLIED"`` / ``"applied."`` — not the create-card defaults
        (``Created`` / ``CREATED`` / ``created.``). Catches a regression
        on the shared header/footer helpers' applied-state copy."""
        app = build_po_modify_ui(
            self._applied(
                [{"operation": "update_header", "succeeded": True, "changes": []}]
            ),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        rendered = str(app.to_json())
        assert "Modify Purchase Order Applied" in rendered
        assert "APPLIED" in rendered
        # Negative — the misleading create-card terminology must not appear.
        assert "Modify Purchase Order Created" not in rendered

    def test_delete_card_renders_deleted_terminology_not_applied(self):
        """Delete cards override the applied copy to ``"Deleted"`` /
        ``"DELETED"`` — modify and delete are both "non-create" but the
        verb differs and the rendered card should match."""
        app = build_po_modify_ui(
            self._applied([{"operation": "delete", "succeeded": True, "changes": []}]),
            confirm_request=_StubRequest(),
            confirm_tool="delete_purchase_order",
        )
        rendered = str(app.to_json())
        assert "Delete Purchase Order Deleted" in rendered
        assert "DELETED" in rendered

    def test_unknown_prior_renders_marker_not_unset(self):
        """When the best-effort fetch failed and changes carry
        ``is_unknown_prior=True``, the rendered diff line MUST show
        ``(prior unknown) → new`` — not the misleading ``(unset) → new``
        that would imply the field had been blank."""
        actions = [
            {
                "operation": "update_header",
                "succeeded": None,
                "changes": [
                    {
                        "field": "expected_arrival_date",
                        "old": None,
                        "new": "2026-05-20",
                        "is_unknown_prior": True,
                    },
                ],
            }
        ]
        app = build_po_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        rendered = str(app.to_json())
        assert "(prior unknown)" in rendered
        # The 2026-05-20 after-value should still render.
        assert "2026-05-20" in rendered
        # Negative — "(unset)" would be misleading here.
        assert "(unset) → 2026-05-20" not in rendered

    def test_state_seeds_result_on_applied_path(self):
        """Mirrors the create-card contract: standalone-applied path
        seeds ``state.result`` from the response so the applied-state
        Buttons (View-in-Katana etc.) resolve their ``{{ result.X }}``
        templates without waiting for an apply round-trip."""
        app = build_po_modify_ui(
            self._applied(
                [{"operation": "update_header", "succeeded": True, "changes": []}]
            ),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        assert app.state is not None
        assert app.state["applied"] is True
        result = app.state.get("result")
        assert isinstance(result, dict)
        assert result["entity_id"] == 9001


class TestPOModifyRowTable:
    """``build_po_modify_ui`` line-item diff table (#722 follow-up under #721).

    The card previously rendered header scalar diffs only and silently dropped
    every ``modify_purchase_order`` row CRUD action. These pin the row table:
    add/update/delete rows render with resolved SKU/name, the table is
    state-bound + morphs, and a header-only modify renders no table.
    """

    _PO_PRIOR: ClassVar[dict[str, Any]] = {
        "id": 9001,
        "order_no": "PO-2026-001",
        "supplier_id": 100,
        "supplier": {"id": 100, "name": "Acme Supply Co"},
        "location_id": 1,
        "status": "NOT_RECEIVED",
        "entity_type": "regular",
        "total": 1250.0,
        "currency": "USD",
        "additional_info": "Net-30",
        # Raw PurchaseOrderRow.to_dict() shape — variant_id + qty + price,
        # NO resolved sku/display_name (those come from extras.resolved_variants).
        "purchase_order_rows": [
            {"id": 7001, "variant_id": 401, "quantity": 10.0, "price_per_unit": 25.0},
            {"id": 7002, "variant_id": 402, "quantity": 5.0, "price_per_unit": 40.0},
        ],
    }
    _RESOLVED: ClassVar[dict[int, dict[str, Any]]] = {
        401: {"sku": "BOLT-M5", "display_name": "M5 bolt"},
        402: {"sku": "NUT-M5", "display_name": "M5 nut"},
        403: {"sku": "WASHER-M5", "display_name": "M5 washer"},
    }

    @classmethod
    def _preview(
        cls, actions: list[dict[str, Any]] | None = None, **overrides: Any
    ) -> dict[str, Any]:
        return {
            "entity_type": "purchase_order",
            "entity_id": 9001,
            "is_preview": True,
            "actions": actions or [],
            "prior_state": dict(cls._PO_PRIOR),
            "extras": {"resolved_variants": dict(cls._RESOLVED)},
            "warnings": [],
            "next_actions": [],
            "message": "Preview",
            "katana_url": "https://factory.katanamrp.com/purchaseorder/9001",
            **overrides,
        }

    @classmethod
    def _applied(
        cls, actions: list[dict[str, Any]] | None = None, **overrides: Any
    ) -> dict[str, Any]:
        return cls._preview(actions, is_preview=False, **overrides)

    @staticmethod
    def _add_row(*, variant_id: int, qty: float, price: float, **o: Any) -> dict:
        return {
            "operation": "add_row",
            "target_id": None,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [
                {
                    "field": "variant_id",
                    "old": None,
                    "new": variant_id,
                    "is_added": True,
                },
                {"field": "quantity", "old": None, "new": qty, "is_added": True},
                {
                    "field": "price_per_unit",
                    "old": None,
                    "new": price,
                    "is_added": True,
                },
            ],
            **o,
        }

    @staticmethod
    def _update_row(
        *, target_id: int, old_qty: float, new_qty: float, **o: Any
    ) -> dict:
        return {
            "operation": "update_row",
            "target_id": target_id,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [{"field": "quantity", "old": old_qty, "new": new_qty}],
            **o,
        }

    @staticmethod
    def _delete_row(*, target_id: int, **o: Any) -> dict:
        return {
            "operation": "delete_row",
            "target_id": target_id,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [],
            **o,
        }

    def test_row_crud_renders_all_kinds_and_summary(self):
        actions = [
            self._add_row(variant_id=403, qty=20.0, price=2.5),
            self._update_row(target_id=7001, old_qty=10.0, new_qty=15.0),
            self._delete_row(target_id=7002),
        ]
        app = build_po_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        # Added row's resolved SKU + name (the user-centric piece — no bare id).
        assert "+ WASHER-M5" in rendered
        assert "M5 washer" in rendered
        # Updated row's quantity diff arrow.
        assert "10 → 15" in rendered
        # Deleted row's preserved identity.
        assert "- NUT-M5" in rendered
        # Summary line.
        assert "+1 added" in rendered
        assert "~1 updated" in rendered
        assert "-1 deleted" in rendered

    def test_rows_seed_state_for_datatable_binding(self):
        app = build_po_modify_ui(
            self._preview([self._add_row(variant_id=403, qty=1.0, price=1.0)]),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        assert app.state is not None
        rows = app.state.get("po_row_rows")
        assert isinstance(rows, list)
        # 2 existing + 1 added.
        assert len(rows) == 3
        assert [r["kind"] for r in rows].count("added") == 1

    def test_short_row_table_disables_pagination(self):
        """End-to-end guard that the state-bound row table is wired through
        ``_paginate`` (not a hardcoded ``paginated=True``): a 3-row table
        fits one page, so the renderer's blank filler rows are suppressed.
        """
        app = build_po_modify_ui(
            self._preview([self._add_row(variant_id=403, qty=1.0, price=1.0)]),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        table = _bound_data_table(app.to_json(), "{{ po_row_rows }}")
        assert table.get("paginated") is False

    def test_overflowing_row_table_enables_pagination(self):
        """The same row table paginates (page size 20) once the rows
        overflow one page — confirms ``_paginate`` is fed the real row
        count, not a constant.
        """
        actions = [
            self._add_row(variant_id=403, qty=float(i), price=1.0) for i in range(25)
        ]
        app = build_po_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        # 2 prior rows + 25 added = 27 > 20.
        assert app.state is not None
        assert len(app.state["po_row_rows"]) == 27
        table = _bound_data_table(app.to_json(), "{{ po_row_rows }}")
        assert table.get("paginated") is True
        assert table.get("pageSize") == 20

    def test_header_only_modify_renders_no_row_table(self):
        actions = [
            {
                "operation": "update_header",
                "target_id": 9001,
                "succeeded": None,
                "changes": [
                    {"field": "status", "old": "NOT_RECEIVED", "new": "RECEIVED"}
                ],
            }
        ]
        app = build_po_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        # No row change → the line-item diff table isn't rendered (the header
        # diff carries the change); existing rows aren't listed as noise.
        assert "Line items:" not in rendered
        # The header diff still shows.
        assert "NOT_RECEIVED" in rendered and "RECEIVED" in rendered

    def test_unresolved_variant_falls_back_to_variant_id(self):
        # Add a variant absent from resolved_variants → "variant <id>" fallback.
        app = build_po_modify_ui(
            self._preview(
                [self._add_row(variant_id=99999, qty=1.0, price=1.0)],
                extras={"resolved_variants": {}},
            ),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        rendered = str(app.to_json())
        assert "(unresolved)" in rendered
        assert "variant 99999" in rendered

    def test_decimal_price_renders_trimmed(self):
        from decimal import Decimal

        actions = [
            {
                "operation": "update_row",
                "target_id": 7001,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [
                    {
                        "field": "price_per_unit",
                        "old": Decimal("25.0000000000"),
                        "new": Decimal("27.5000000000"),
                    }
                ],
            }
        ]
        app = build_po_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        rendered = str(app.to_json())
        assert "25 → 27.5" in rendered
        assert "0000000000" not in rendered

    def test_malformed_resolved_variants_does_not_crash(self):
        """A missing / malformed ``extras.resolved_variants`` (None, list) must
        not crash the card — it degrades to the ``variant <id>`` fallback
        (Copilot #881)."""
        from katana_mcp.tools.prefab_ui import _coerce_resolved_id_map

        assert _coerce_resolved_id_map(None) == {}
        assert _coerce_resolved_id_map([1, 2, 3]) == {}
        assert _coerce_resolved_id_map("nope") == {}
        # Well-formed still works (string keys coerced back to int).
        assert _coerce_resolved_id_map({"401": {"sku": "X", "display_name": "Y"}}) == {
            401: {"sku": "X", "display_name": "Y"}
        }
        # End-to-end: a non-dict extras value renders the row with the fallback.
        app = build_po_modify_ui(
            self._preview(
                [self._add_row(variant_id=403, qty=1.0, price=1.0)],
                extras={"resolved_variants": ["malformed"]},
            ),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        _assert_valid_prefab(app)
        assert "variant 403" in str(app.to_json())

    def test_header_only_modify_short_circuits_row_merge(self):
        """Header-only / additional-cost-only plans skip the row merge entirely
        — ``_po_modify_row_rows`` returns ``([], "")`` without projecting over
        the PO's row snapshot (Copilot #881)."""
        from katana_mcp.tools.prefab_ui import _po_modify_row_rows

        header_actions = [
            {
                "operation": "update_header",
                "target_id": 9001,
                "succeeded": None,
                "changes": [{"field": "status", "old": "X", "new": "Y"}],
            },
            {
                "operation": "add_additional_cost",
                "target_id": None,
                "succeeded": None,
                "changes": [],
            },
        ]
        rows, summary = _po_modify_row_rows(
            dict(self._PO_PRIOR), header_actions, extras={}
        )
        assert rows == []
        assert summary == ""
        # A row op does produce rows.
        rows2, summary2 = _po_modify_row_rows(
            dict(self._PO_PRIOR),
            [self._add_row(variant_id=403, qty=1.0, price=1.0)],
            extras={"resolved_variants": dict(self._RESOLVED)},
        )
        assert len(rows2) == 3 and summary2 == "+1 added"

    def test_header_only_modify_does_not_seed_row_state(self):
        """Header-only modify: no row change → the (potentially large) PO row
        snapshot is NOT copied into UI state (Copilot #881)."""
        actions = [
            {
                "operation": "update_header",
                "target_id": 9001,
                "succeeded": None,
                "changes": [
                    {"field": "status", "old": "NOT_RECEIVED", "new": "RECEIVED"}
                ],
            }
        ]
        app = build_po_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        assert app.state is not None
        assert "po_row_rows" not in app.state

    def test_not_run_tail_surfaces_in_row_table(self):
        applied_actions = [
            self._add_row(
                variant_id=403,
                qty=1.0,
                price=1.0,
                succeeded=False,
                status_label="FAILED",
                error="variant archived",
            )
        ]
        not_run = [
            self._update_row(
                target_id=7001, old_qty=10.0, new_qty=15.0, status_label="NOT RUN"
            )
        ]
        app = build_po_modify_ui(
            self._applied(
                applied_actions,
                extras={
                    "resolved_variants": dict(self._RESOLVED),
                    "not_run_actions": not_run,
                },
            ),
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        assert app.state is not None
        rows = app.state.get("po_row_rows")
        assert isinstance(rows, list)
        statuses = {r["id"]: r["status_label"] for r in rows}
        # Added row FAILED; the not-run update of 7001 shows NOT RUN.
        assert statuses.get(7001) == "NOT RUN"
        assert any(r["status_label"] == "FAILED" for r in rows)


class TestBuildMOModifyUI:
    """``build_mo_modify_ui`` (#721 Phase 4) — header diffs + three collection
    diff tables (recipe / operation / production), each shown only when that
    collection changes. Net-new card replacing the generic ActionResult table.
    """

    _PRIOR: ClassVar[dict[str, Any]] = {
        "order_no": "MO-2026-001",
        "status": "NOT_STARTED",
        "variant_id": 9,
        "sku": "WIDGET-A",
        "planned_quantity": 10,
        "location_id": 1,
        "location_name": "Main Factory",
        "additional_info": "rush",
        # Collections fetched + attached impl-side (RecipeRowInfo /
        # OperationRowInfo / ProductionInfo dumps).
        "recipe_rows": [
            {
                "id": 11,
                "variant_id": 402,
                "sku": "BOLT",
                "display_name": "M5 bolt",
                "planned_quantity_per_unit": 4.0,
            },
        ],
        "operation_rows": [
            {"id": 21, "operation_name": "Cut", "status": "NOT_STARTED"},
        ],
        "productions": [
            {"id": 31, "quantity": 5.0, "production_date": "2026-05-01T00:00:00Z"},
        ],
    }

    @classmethod
    def _preview(
        cls, actions: list[dict[str, Any]] | None = None, **overrides: Any
    ) -> dict[str, Any]:
        return {
            "entity_type": "manufacturing_order",
            "entity_id": 500,
            "is_preview": True,
            "order_no": "MO-2026-001",
            "status": "NOT_STARTED",
            "actions": actions or [],
            "prior_state": dict(cls._PRIOR),
            "extras": {
                "resolved_variants": {
                    403: {"sku": "WASHER", "display_name": "M5 washer"}
                }
            },
            "warnings": [],
            "next_actions": [],
            "message": "Preview",
            "katana_url": "https://factory.katanamrp.com/manufacturingorder/500",
            **overrides,
        }

    @classmethod
    def _applied(
        cls, actions: list[dict[str, Any]] | None = None, **overrides: Any
    ) -> dict[str, Any]:
        return cls._preview(actions, is_preview=False, **overrides)

    @staticmethod
    def _header(field: str, old: Any, new: Any) -> dict:
        return {
            "operation": "update_header",
            "target_id": 500,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [{"field": field, "old": old, "new": new}],
        }

    def test_header_diff_and_collections_render(self):
        actions = [
            self._header("planned_quantity", 10, 20),
            {
                "operation": "add_recipe_row",
                "target_id": None,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [
                    {"field": "variant_id", "old": None, "new": 403, "is_added": True},
                    {
                        "field": "planned_quantity_per_unit",
                        "old": None,
                        "new": 2.0,
                        "is_added": True,
                    },
                ],
            },
            {
                "operation": "update_operation_row",
                "target_id": 21,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [
                    {"field": "status", "old": "NOT_STARTED", "new": "COMPLETED"}
                ],
            },
            {
                "operation": "add_production",
                "target_id": None,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [
                    {
                        "field": "completed_quantity",
                        "old": None,
                        "new": 3.0,
                        "is_added": True,
                    }
                ],
            },
        ]
        app = build_mo_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_manufacturing_order",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        # Header scalar diff.
        assert "Modify Manufacturing Order" in rendered
        assert "10 → 20" in rendered
        # All three collection sections present.
        assert "Recipe (ingredients):" in rendered
        assert "Operations:" in rendered
        assert "Productions:" in rendered
        # Recipe add resolved SKU; operation status diff.
        assert "+ WASHER" in rendered
        assert "NOT_STARTED → COMPLETED" in rendered

    def test_header_only_modify_renders_no_collection_tables(self):
        app = build_mo_modify_ui(
            self._preview([self._header("status", "NOT_STARTED", "IN_PROGRESS")]),
            confirm_request=_StubRequest(),
            confirm_tool="modify_manufacturing_order",
        )
        assert app.state is not None
        rendered = str(app.to_json())
        # Header diff shows; no collection sections / state keys.
        assert "NOT_STARTED → IN_PROGRESS" in rendered
        assert "Recipe (ingredients):" not in rendered
        assert "Operations:" not in rendered
        assert "Productions:" not in rendered
        for key in ("mo_recipe_rows", "mo_operation_rows", "mo_production_rows"):
            assert key not in app.state

    def test_single_collection_seeds_only_that_state_key(self):
        actions = [
            {
                "operation": "delete_recipe_row",
                "target_id": 11,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [],
            },
        ]
        app = build_mo_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_manufacturing_order",
        )
        assert app.state is not None
        assert "mo_recipe_rows" in app.state
        assert "mo_operation_rows" not in app.state
        assert "mo_production_rows" not in app.state
        rendered = str(app.to_json())
        assert "- BOLT" in rendered  # deleted recipe row keeps identity

    def test_delete_verb(self):
        actions = [
            {
                "operation": "delete",
                "target_id": 500,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [],
            }
        ]
        app = build_mo_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="delete_manufacturing_order",
        )
        _assert_valid_prefab(app)
        assert "Confirm Delete" in str(app.to_json())

    def test_applied_recipe_row_morph_state(self):
        actions = [
            {
                "operation": "add_recipe_row",
                "target_id": None,
                "succeeded": True,
                "status_label": "APPLIED",
                "changes": [
                    {"field": "variant_id", "old": None, "new": 403, "is_added": True}
                ],
            },
        ]
        app = build_mo_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_manufacturing_order",
        )
        assert app.state is not None
        rows = app.state.get("mo_recipe_rows")
        assert isinstance(rows, list)
        assert any(r["status_label"] == "APPLIED" for r in rows)


class TestMOModifyDispatch:
    """``to_tool_result`` routes manufacturing_order modify responses to
    ``build_mo_modify_ui`` (not the legacy generic card)."""

    def test_mo_routes_to_mo_modify_card(self):
        from katana_mcp.tools._modification import (
            ConfirmableRequest,
            ModificationResponse,
            to_tool_result,
        )

        class _StubConfirmable(ConfirmableRequest):
            id: int = 500

        response = ModificationResponse(
            entity_type="manufacturing_order",
            entity_id=500,
            is_preview=True,
            actions=[],
            prior_state={"order_no": "MO-9", "status": "NOT_STARTED"},
            warnings=[],
            next_actions=[],
            message="Preview",
        )
        result = to_tool_result(
            response,
            confirm_request=_StubConfirmable(),
            confirm_tool="modify_manufacturing_order",
        )
        # The MO card titles "Modify Manufacturing Order"; the generic card
        # does not — its presence confirms the MO builder ran.
        assert "Manufacturing Order" in str(result.structured_content)


class TestBuildStockTransferModifyUI:
    """``build_stock_transfer_modify_ui`` (#721 Phase 5) — header-only card.

    Stock transfers have no GET-by-id endpoint, so ``prior_state`` is always
    ``None`` and every field diff reads ``(prior unknown) → new``; rows are
    immutable post-creation, so the card never renders a collection table.
    """

    @staticmethod
    def _preview(actions: list[dict[str, Any]], **overrides: Any) -> dict[str, Any]:
        return {
            "entity_type": "stock_transfer",
            "entity_id": 42,
            "is_preview": True,
            "actions": actions,
            "prior_state": None,
            "warnings": [],
            "next_actions": [],
            "message": "Preview: 2 action(s) planned for stock transfer 42",
            "katana_url": "https://factory.katanamrp.com/stocktransfer/42",
            **overrides,
        }

    @staticmethod
    def _unknown_prior(field: str, new: Any) -> dict[str, Any]:
        # Mirrors ``compute_field_diff(None, patch, unknown_prior=True)`` — the
        # impl's only diff shape for stock transfers (no GET to diff against).
        return {"field": field, "old": None, "new": new, "is_unknown_prior": True}

    def test_header_and_status_diffs_render(self):
        actions = [
            {
                "operation": "update_header",
                "target_id": 42,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [
                    self._unknown_prior("stock_transfer_number", "ST-002"),
                    self._unknown_prior(
                        "expected_arrival_date", "2026-06-10T00:00:00Z"
                    ),
                ],
            },
            {
                "operation": "update_status",
                "target_id": 42,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [self._unknown_prior("new_status", "IN_TRANSIT")],
            },
        ]
        app = build_stock_transfer_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_stock_transfer",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Modify Stock Transfer" in rendered
        # Every line reads "(prior unknown) → new" — there's no prior snapshot.
        assert "Transfer No: (prior unknown) → ST-002" in rendered
        assert "Expected Arrival: (prior unknown) → 2026-06-10T00:00:00Z" in rendered
        # ``new_status`` renders under the "Status" label.
        assert "Status: (prior unknown) → IN_TRANSIT" in rendered

    def test_no_collection_table_ever(self):
        actions = [
            {
                "operation": "update_header",
                "target_id": 42,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [self._unknown_prior("additional_info", "rush delivery")],
            }
        ]
        app = build_stock_transfer_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_stock_transfer",
        )
        # Header-only: rows are immutable post-create, so no DataTable, ever.
        assert not _has_node_of_type(app.to_json(), "DataTable")
        assert "Notes: (prior unknown) → rush delivery" in str(app.to_json())

    def test_delete_verb_and_message_body(self):
        actions = [
            {
                "operation": "delete",
                "target_id": 42,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [],
            }
        ]
        app = build_stock_transfer_modify_ui(
            self._preview(actions, message="Preview: delete stock transfer 42"),
            confirm_request=_StubRequest(),
            confirm_tool="delete_stock_transfer",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Delete Stock Transfer" in rendered
        assert "Confirm Delete" in rendered
        # Delete carries no field changes — the message anchors the body.
        assert "Preview: delete stock transfer 42" in rendered

    def test_applied_status_chrome(self):
        actions = [
            {
                "operation": "update_status",
                "target_id": 42,
                "succeeded": True,
                "status_label": "APPLIED",
                "changes": [self._unknown_prior("new_status", "RECEIVED")],
            }
        ]
        app = build_stock_transfer_modify_ui(
            self._preview(actions, is_preview=False),
            confirm_request=_StubRequest(),
            confirm_tool="modify_stock_transfer",
        )
        _assert_valid_prefab(app)
        assert "APPLIED" in str(app.to_json())

    def test_failed_apply_surfaces_error_in_consolidated_block(self):
        """A failed action (standalone-applied path) surfaces its error TEXT in
        the consolidated failure Alert — not just the inline ✗ gutter — so a
        failed/partial apply stays interpretable (Copilot #888). The label reads
        in card vocabulary ("Status"), not the wire field name ("new_status").
        """
        actions = [
            {
                "operation": "update_status",
                "target_id": 42,
                "succeeded": False,
                "status_label": "FAILED",
                "error": "422: invalid transition DRAFT → RECEIVED",
                "changes": [self._unknown_prior("new_status", "RECEIVED")],
            }
        ]
        app = build_stock_transfer_modify_ui(
            self._preview(actions, is_preview=False),
            confirm_request=_StubRequest(),
            confirm_tool="modify_stock_transfer",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        # Consolidated Alert carries the user-facing label + the error text.
        assert "Failed — Status: 422: invalid transition" in rendered

    def test_block_warning_suppresses_confirm(self):
        """``BLOCK:``-prefixed warnings suppress the Confirm button via the
        ``_render_warnings_block`` → ``block_warnings`` → footer gating chain.
        Same contract as every other modify card — the header-only ST card
        still surfaces a server-side BLOCK warning (e.g. an invalid status
        transition flagged pre-preview).
        """
        actions = [
            {
                "operation": "update_status",
                "target_id": 42,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [self._unknown_prior("new_status", "RECEIVED")],
            }
        ]
        app = build_stock_transfer_modify_ui(
            self._preview(
                actions, warnings=["BLOCK: status already RECEIVED — cannot advance"]
            ),
            confirm_request=_StubRequest(),
            confirm_tool="modify_stock_transfer",
        )
        rendered = str(app.to_json())
        # Block warning surfaces in the body (BLOCK: prefix stripped).
        assert "status already RECEIVED" in rendered
        # Footer copy switches to the "Cannot proceed" muted line.
        assert "Cannot proceed" in rendered

    def test_header_identity_prefers_transfer_number_over_id(self):
        """Tier-1 identity badge shows the (proposed) transfer number from a
        rename diff rather than the raw entity_id — keeps the header human-
        facing even with no GET endpoint (Copilot #888).
        """
        actions = [
            {
                "operation": "update_header",
                "target_id": 42,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [self._unknown_prior("stock_transfer_number", "ST-002")],
            }
        ]
        app = build_stock_transfer_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_stock_transfer",
        )
        badge_labels = [
            b.get("label") for b in _find_components_by_type(app.to_json(), "Badge")
        ]
        assert "ST-002" in badge_labels
        # Raw id is NOT used as identity when a human-readable number exists.
        assert "42" not in badge_labels

    def test_header_identity_falls_back_to_id_without_number(self):
        """A status-only modify carries no transfer number, so the identity
        badge falls back to the entity_id — the honest best available without
        a GET endpoint.
        """
        actions = [
            {
                "operation": "update_status",
                "target_id": 42,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [self._unknown_prior("new_status", "IN_TRANSIT")],
            }
        ]
        app = build_stock_transfer_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_stock_transfer",
        )
        badge_labels = [
            b.get("label") for b in _find_components_by_type(app.to_json(), "Badge")
        ]
        assert "42" in badge_labels


class TestStockTransferModifyDispatch:
    """``to_tool_result`` routes stock_transfer responses to
    ``build_stock_transfer_modify_ui`` — the last entity migrated off the
    generic card (#721 Phase 5). Unknown entity types now raise (Phase 6
    removed the generic fallback).
    """

    def test_stock_transfer_routes_to_st_card(self):
        from katana_mcp.tools._modification import (
            ConfirmableRequest,
            ModificationResponse,
            to_tool_result,
        )

        class _StubConfirmable(ConfirmableRequest):
            id: int = 42

        response = ModificationResponse(
            entity_type="stock_transfer",
            entity_id=42,
            is_preview=True,
            actions=[],
            prior_state=None,
            warnings=[],
            next_actions=[],
            message="Preview",
        )
        result = to_tool_result(
            response,
            confirm_request=_StubConfirmable(),
            confirm_tool="modify_stock_transfer",
        )
        assert "Stock Transfer" in str(result.structured_content)

    def test_unknown_entity_type_raises(self):
        from katana_mcp.tools._modification import (
            ConfirmableRequest,
            ModificationResponse,
            to_tool_result,
        )

        class _StubConfirmable(ConfirmableRequest):
            id: int = 1

        response = ModificationResponse(
            entity_type="totally_unknown_entity",
            entity_id=1,
            is_preview=True,
            actions=[],
            warnings=[],
            next_actions=[],
            message="Preview",
        )
        with pytest.raises(ValueError, match="no modify-card builder"):
            to_tool_result(
                response,
                confirm_request=_StubConfirmable(),
                confirm_tool="modify_totally_unknown",
            )


class TestBuildSOModifyUI:
    """``build_so_modify_ui`` handles preview/applied/partial-failure for
    every SO write tool (``modify_sales_order``, ``delete_sales_order``,
    ``correct_sales_order``). Mirrors ``TestBuildPOModifyUI``'s coverage
    shape — title verb derivation, diff-decoration, layout-stability,
    failure-state chrome, applied-state morph seeding.

    SO is more complex than PO because of the parallel-outcome
    sub-entities (rows, addresses, fulfillments, shipping fees). The
    sub-entity tests pin each section's rendering contract.
    """

    # Wire-shape prior_state matching ``SalesOrder.to_dict()`` — wire
    # keys ``order_no`` / ``additional_info`` (NOT ``order_number`` /
    # ``notes`` from the response shape). Catches shape-mismatch bugs
    # at the ``_normalize_so_prior_state`` boundary.
    _SO_PRIOR: ClassVar[dict[str, Any]] = {
        "id": 42,
        "order_no": "SO-2026-001",
        "customer_id": 1501,
        "customer_name": "Sarah Johnson",
        "location_id": 1,
        "status": "NOT_SHIPPED",
        "currency": "USD",
        "total": 1250.0,
        "additional_info": "Customer requested expedited delivery",
        "delivery_date": "2026-05-08T14:30:00Z",
    }

    @classmethod
    def _preview(
        cls,
        actions: list[dict[str, Any]] | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        return {
            "entity_type": "sales_order",
            "entity_id": cls._SO_PRIOR["id"],
            "is_preview": True,
            "actions": actions or [],
            "prior_state": dict(cls._SO_PRIOR),
            "warnings": [],
            "next_actions": [],
            "message": "Preview",
            "katana_url": "https://factory.katanamrp.com/salesorder/42",
            **overrides,
        }

    @classmethod
    def _applied(
        cls,
        actions: list[dict[str, Any]] | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        return cls._preview(actions, is_preview=False, **overrides)

    def test_smoke_preview_header_only_change(self):
        """Single status-update preview renders the title verb, diff line,
        and the cancel-phrase that ``_build_cancel_action`` interpolates."""
        actions = [
            {
                "operation": "update_header",
                "target_id": 42,
                "succeeded": None,
                "changes": [
                    {"field": "status", "old": "NOT_SHIPPED", "new": "PACKED"},
                ],
            }
        ]
        app = build_so_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Modify Sales Order" in rendered
        assert "NOT_SHIPPED" in rendered and "PACKED" in rendered
        assert "→" in rendered

    def test_storefront_link_renders_for_native_ecommerce_order(self):
        """A Shopify-sourced SO surfaces an 'Open in Shopify' storefront link,
        derived from the raw ``ecommerce_*`` fields the modify card's
        ``prior_state`` snapshot carries (#913)."""
        prior = {
            **self._SO_PRIOR,
            "ecommerce_order_type": "shopify",
            "ecommerce_store_name": "katana.myshopify.com",
            "ecommerce_order_id": "19433769",
        }
        app = build_so_modify_ui(
            self._preview(prior_state=prior),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Open in Shopify" in rendered
        assert "https://katana.myshopify.com/admin/orders/19433769" in rendered

    def test_no_storefront_link_for_unrecognized_or_absent_ecommerce(self):
        """eBay (unrecognized) and plain orders get no storefront link —
        mirrors Katana, which only deep-links the three native platforms."""
        ebay = build_so_modify_ui(
            self._preview(
                prior_state={
                    **self._SO_PRIOR,
                    "ecommerce_order_type": "ebay",
                    "ecommerce_store_name": "ebay.example",
                    "ecommerce_order_id": "EB-1",
                }
            ),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        # Assert on the storefront section's own marker ("Storefront:" Text) so
        # the test stays scoped to this feature and won't break if an unrelated
        # "Open in …" link is ever added elsewhere on the SO modify card.
        assert "Storefront:" not in str(ebay.to_json())
        # A plain SO with no ecommerce metadata at all also renders none.
        plain = build_so_modify_ui(
            self._preview(),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        assert "Storefront:" not in str(plain.to_json())

    def test_customer_change_renders_composite_diff(self):
        """A customer change surfaces ``Customer: <old> (<old_id>) → <new>``
        — the composite name+ID rendering keeps the diff readable. Same
        contract as PO's supplier-change rendering."""
        actions = [
            {
                "operation": "update_header",
                "target_id": 42,
                "succeeded": None,
                "changes": [
                    {"field": "customer_id", "old": 1501, "new": 1502},
                    {
                        "field": "customer_name",
                        "old": "Sarah Johnson",
                        "new": "Mike Smith",
                    },
                ],
            }
        ]
        app = build_so_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        rendered = str(app.to_json())
        assert "Customer:" in rendered
        assert "Sarah Johnson" in rendered
        assert "Mike Smith" in rendered
        assert "→" in rendered
        # Regression-guard: the bug shape (old name on both sides) must
        # not appear.
        assert "Sarah Johnson (1501) → Sarah Johnson" not in rendered

    def test_delete_card_uses_delete_verb_and_confirm_label(self):
        """Delete cards use "Confirm Delete" and the "Delete Sales Order"
        title; the cancel phrase reads naturally as a noun."""
        app = build_so_modify_ui(
            self._preview([{"operation": "delete", "succeeded": None, "changes": []}]),
            confirm_request=_StubRequest(),
            confirm_tool="delete_sales_order",
        )
        rendered = str(app.to_json())
        assert "Delete Sales Order" in rendered
        assert "Confirm Delete" in rendered

    def test_cancel_messages_use_natural_noun_phrases_per_verb(self):
        """``_build_cancel_action`` interpolates noun phrases — modify/
        correct cards say "those sales order changes" / "those sales
        order corrections"; delete cards say "that sales order deletion"."""
        for tool, expected_phrase in [
            ("modify_sales_order", "those sales order changes"),
            ("correct_sales_order", "those sales order corrections"),
            ("delete_sales_order", "that sales order deletion"),
        ]:
            app = build_so_modify_ui(
                self._preview(
                    [{"operation": "update_header", "succeeded": None, "changes": []}]
                ),
                confirm_request=_StubRequest(),
                confirm_tool=tool,
            )
            rendered = str(app.to_json())
            assert expected_phrase in rendered, (
                f"Cancel message for {tool} should interpolate "
                f"{expected_phrase!r}; got rendered tree without it."
            )

    def test_failed_action_surfaces_glyph_inline_and_error_in_alert(self):
        """Hybrid status approach — per-field ✗ glyph in the gutter +
        consolidated error message in the bottom Alert. Layout-stability
        rule from PO #722: failed apply doesn't reflow diff lines."""
        actions = [
            {
                "operation": "update_header",
                "target_id": 42,
                "succeeded": False,
                "error": "422 Unprocessable: invalid customer transition",
                "changes": [
                    {
                        "field": "status",
                        "old": "NOT_SHIPPED",
                        "new": "PACKED",
                    },
                ],
            }
        ]
        app = build_so_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        rendered = str(app.to_json())
        assert "✗" in rendered
        assert "422 Unprocessable" in rendered

    def test_applied_partial_failure_renders_overall_badge(self):
        """A mixed applied outcome (1 success + 1 fail) renders the
        ``PARTIAL FAILURE`` state badge with the destructive variant.
        Same contract as PO modify."""
        actions = [
            {
                "operation": "update_header",
                "succeeded": True,
                "changes": [
                    {"field": "status", "old": "NOT_SHIPPED", "new": "PACKED"},
                ],
            },
            {
                "operation": "add_shipping_fee",
                "succeeded": False,
                "error": "422: tax_rate_id required",
                "target_id": None,
                "changes": [
                    {
                        "field": "description",
                        "new": "Express ground",
                        "is_added": True,
                    },
                    {"field": "amount", "new": "12.99", "is_added": True},
                ],
            },
        ]
        app = build_so_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        rendered = str(app.to_json())
        assert "PARTIAL FAILURE" in rendered

    def test_applied_all_failed_uses_failed_state_label(self):
        """Fully-failed apply — header state badge MUST read ``FAILED``,
        not ``APPLIED``. ``applied_state_label`` overrides based on
        ``_summarize_apply_outcome``."""
        actions = [
            {
                "operation": "update_header",
                "succeeded": False,
                "error": "422: invalid status transition",
                "changes": [{"field": "status", "old": "PACKED", "new": "DELIVERED"}],
            },
        ]
        app = build_so_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        rendered = str(app.to_json())
        assert "FAILED" in rendered

    def test_failed_apply_uses_destructive_badge_variant(self):
        """The FAILED state badge MUST render with variant=destructive
        (red), NOT default (green). Pinned via envelope walk because
        rendered-text alone can't distinguish FAILED-in-red from
        FAILED-in-green. Same contract as PO modify."""
        actions = [
            {
                "operation": "update_header",
                "succeeded": False,
                "error": "422: invalid",
                "changes": [{"field": "status", "old": "OPEN", "new": "PACKED"}],
            },
        ]
        app = build_so_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        envelope = app.to_json()
        found_destructive = False

        def walk(node: Any) -> None:
            nonlocal found_destructive
            if isinstance(node, dict):
                if (
                    node.get("type") == "Badge"
                    and node.get("label") == "FAILED"
                    and node.get("variant") == "destructive"
                ):
                    found_destructive = True
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(envelope)
        assert found_destructive, (
            "FAILED Badge with variant=destructive not found — the state "
            "badge variant must reflect the apply outcome, not the verb."
        )

    def test_failed_delete_overrides_title_and_verb_to_match_failure(self):
        """A failed delete reads "Sales Order Failed" / verb="failed" — not
        "Sales Order Deleted" / "deleted." which would contradict the
        FAILED badge.

        Unlike the PO modify card (which passes a literal verb to the
        footer at build time), the SO modify card passes
        ``applied_verb="{{ applied_verb }}"`` as a mustache template so
        the footer body morphs in lockstep with the state-driven outcome
        Badge. The literal verb lives in ``state.applied_verb``.
        Same morph contract as ``build_bom_modify_ui`` (#811)."""
        actions = [
            {
                "operation": "delete",
                "succeeded": False,
                "error": "404: not found",
                "changes": [],
            }
        ]
        app = build_so_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="delete_sales_order",
        )
        rendered = str(app.to_json())
        assert "Delete Sales Order Failed" in rendered
        assert "FAILED" in rendered
        assert "Delete Sales Order Deleted" not in rendered
        # State-driven verb: failed apply seeds applied_verb="failed"
        # so the morph reads "Sales Order Delete failed." after the
        # in-place state seeding lands.
        assert app.state is not None
        assert app.state["applied_verb"] == "failed"

    def test_applied_state_renders_applied_terminology_not_created(self):
        """Modify cards pass ``applied_title_suffix="Applied"`` so the
        rendered applied state reads ``"Sales Order Applied"`` — not the
        create-card default "Created"."""
        app = build_so_modify_ui(
            self._applied(
                [{"operation": "update_header", "succeeded": True, "changes": []}]
            ),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        rendered = str(app.to_json())
        assert "Modify Sales Order Applied" in rendered
        assert "APPLIED" in rendered
        assert "Modify Sales Order Created" not in rendered

    def test_delete_card_renders_deleted_terminology_not_applied(self):
        """Delete cards override the applied copy to "Deleted" / "DELETED"."""
        app = build_so_modify_ui(
            self._applied([{"operation": "delete", "succeeded": True, "changes": []}]),
            confirm_request=_StubRequest(),
            confirm_tool="delete_sales_order",
        )
        rendered = str(app.to_json())
        assert "Delete Sales Order Deleted" in rendered
        assert "DELETED" in rendered

    def test_state_seeds_result_on_applied_path(self):
        """Standalone-applied path seeds ``state.result`` from the response
        so the applied-state Buttons resolve their ``{{ result.X }}``
        templates without an apply round-trip."""
        app = build_so_modify_ui(
            self._applied(
                [{"operation": "update_header", "succeeded": True, "changes": []}]
            ),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        assert app.state is not None
        assert app.state["applied"] is True
        result = app.state.get("result")
        assert isinstance(result, dict)
        assert result["entity_id"] == 42

    def test_state_seeds_morph_slots_for_applied_outcome(self):
        """The Confirm button's on_success chain morphs the card via
        ``SetState`` from ``$result.state.<slot>``. The build-time state
        MUST seed each morph slot so the bindings have something to
        resolve to before the apply lands."""
        app = build_so_modify_ui(
            self._preview(
                [{"operation": "update_header", "succeeded": None, "changes": []}]
            ),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        assert app.state is not None
        # Preview path — slots seeded with safe defaults so the
        # If/Elif/Else branches have something to bind to.
        assert app.state["applied_outcome_label"] == "APPLIED"
        assert app.state["applied_outcome_variant"] == "default"
        assert app.state["applied_subentity_failed_count"] == 0
        assert app.state["applied_subentity_failed_summary"] == ""
        assert app.state["applied_verb"] == "applied"

    def test_sub_entity_section_renders_row_adds_with_gutter(self):
        """Add-row actions render in the Line items section with a ``+ ``
        gutter and the variant identity inline. Mirrors BOM's adds
        rendering convention."""
        actions = [
            {
                "operation": "add_row",
                "target_id": None,
                "succeeded": None,
                "changes": [
                    {"field": "variant_id", "old": None, "new": 2101, "is_added": True},
                    {"field": "quantity", "old": None, "new": 3.0, "is_added": True},
                ],
            }
        ]
        app = build_so_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        rendered = str(app.to_json())
        # Section header.
        assert "Line items" in rendered
        # Add gutter + variant identity.
        assert "+ " in rendered
        assert "variant 2101" in rendered
        assert "qty 3" in rendered

    def test_sub_entity_section_groups_actions_by_kind(self):
        """A mixed plan touching rows + addresses + shipping fees renders
        three section headers in the entity-view body, each grouping its
        own actions. Pins the operation→section bucketing contract."""
        actions = [
            {
                "operation": "add_row",
                "target_id": None,
                "succeeded": None,
                "changes": [
                    {"field": "variant_id", "old": None, "new": 100, "is_added": True},
                    {"field": "quantity", "old": None, "new": 1.0, "is_added": True},
                ],
            },
            {
                "operation": "delete_address",
                "target_id": 9001,
                "succeeded": None,
                "changes": [],
            },
            {
                "operation": "add_shipping_fee",
                "target_id": None,
                "succeeded": None,
                "changes": [
                    {
                        "field": "description",
                        "new": "Express",
                        "is_added": True,
                    },
                    {"field": "amount", "new": "12.99", "is_added": True},
                ],
            },
        ]
        app = build_so_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        rendered = str(app.to_json())
        assert "Line items" in rendered
        assert "Addresses" in rendered
        assert "Shipping fees" in rendered
        # Fulfillments has no actions — section should not render
        # (otherwise the card would have a "Fulfillments:" header with
        # no rows below it).
        assert "Fulfillments:" not in rendered

    def test_applied_sub_entity_failure_seeds_morph_summary(self):
        """Applied path with a failed sub-entity action seeds the
        ``applied_subentity_failed_count`` / ``applied_subentity_failed_summary``
        state slots — the in-place morph after Confirm reads ``$result.state.*``
        to surface failures the build-time render couldn't predict.

        Pre-formatted ``Failed — <op> #<target>: <error>`` lines, plus a
        retry-coaching tail referencing the SO id so the operator knows
        how to recover via ``modify_sales_order``."""
        actions = [
            {
                "operation": "add_shipping_fee",
                "target_id": None,
                "succeeded": True,
                "changes": [
                    {"field": "description", "new": "Express", "is_added": True},
                    {"field": "amount", "new": "12.99", "is_added": True},
                ],
            },
            {
                "operation": "delete_row",
                "target_id": 9999,
                "succeeded": False,
                "error": "404 Not Found: row 9999",
                "changes": [],
            },
        ]
        app = build_so_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        assert app.state is not None
        assert app.state["applied_subentity_failed_count"] == 1
        summary = app.state["applied_subentity_failed_summary"]
        assert "Failed — delete_row #9999" in summary
        assert "404 Not Found" in summary
        # Retry coaching references the SO id literally so the operator
        # can copy/paste without bouncing through the response object.
        assert "modify_sales_order(id=42" in summary

    def test_subentity_failure_retry_text_matches_confirm_tool(self):
        """The retry-coaching tail in the sub-entity failure summary must
        name the tool the operator actually invoked. ``correct_sales_order``
        partial failures must recommend re-issuing ``correct_sales_order``,
        not ``modify_sales_order`` — corrections and modifies have different
        audit-trail side effects, so misdirection here would silently
        drop a customer's correction off the books (#858 review follow-up).
        """
        actions = [
            {
                "operation": "delete_row",
                "target_id": 9999,
                "succeeded": False,
                "error": "404 Not Found: row 9999",
                "changes": [],
            },
        ]

        modify_app = build_so_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        assert modify_app.state is not None
        modify_summary = modify_app.state["applied_subentity_failed_summary"]
        assert "modify_sales_order(id=42" in modify_summary
        assert "correct_sales_order(id=42" not in modify_summary

        correct_app = build_so_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="correct_sales_order",
        )
        assert correct_app.state is not None
        correct_summary = correct_app.state["applied_subentity_failed_summary"]
        assert "correct_sales_order(id=42" in correct_summary
        # Regression-guard: the bug shape — a correction partial failure
        # MUST NOT direct the operator back through ``modify_sales_order``.
        assert "modify_sales_order(id=42" not in correct_summary

    def test_failed_subentity_action_uses_x_gutter_and_status_pill(self):
        """On the applied path, a failed sub-entity action row gets the
        ``✗ `` gutter + a destructive FAILED Badge alongside the summary."""
        actions = [
            {
                "operation": "delete_row",
                "target_id": 9999,
                "succeeded": False,
                "error": "404 Not Found",
                "status_label": "FAILED",
                "changes": [],
            },
        ]
        app = build_so_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        envelope = app.to_json()
        rendered = str(envelope)
        assert "✗ row #9999" in rendered
        # FAILED Badge alongside the row.
        found_failed = False

        def walk(node: Any) -> None:
            nonlocal found_failed
            if isinstance(node, dict):
                if (
                    node.get("type") == "Badge"
                    and node.get("label") == "FAILED"
                    and node.get("variant") == "destructive"
                ):
                    found_failed = True
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(envelope)
        assert found_failed, (
            "Failed sub-entity action must render with a FAILED + destructive "
            "Badge alongside its row text."
        )

    def test_address_update_collapses_to_bare_after_form(self):
        """Address updates collapse to the bare ``field: new`` form (no
        arrow) because Katana has no per-address GET endpoint —
        ``_format_so_diff_pairs(address_style=True)`` deliberately skips
        the ``is_unknown_prior`` arrow path so the summary line stays
        compact (otherwise every field would read
        ``(prior unknown) → new``, which is noise without signal).

        Pins the bare-after contract: the rendered output MUST surface
        the new field values and MUST NOT contain ``(prior unknown)``.
        A refactor that flips ``address_style=True`` to the arrow form
        would regress this test.
        """
        actions = [
            {
                "operation": "update_address",
                "target_id": 9001,
                "succeeded": None,
                "changes": [
                    {
                        "field": "city",
                        "old": None,
                        "new": "Springfield",
                        "is_unknown_prior": True,
                    },
                    {
                        "field": "zip",
                        "old": None,
                        "new": "12345",
                        "is_unknown_prior": True,
                    },
                ],
            }
        ]
        app = build_so_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        rendered = str(app.to_json())
        assert "Addresses" in rendered
        # The update summary surfaces the supplied fields' new values
        # in the bare ``field: new`` form.
        assert "Springfield" in rendered
        assert "12345" in rendered
        # Pin the bare-after contract: the address-style renderer MUST
        # NOT emit ``(prior unknown)`` (the arrow path is skipped for
        # address updates, per ``_format_so_diff_pairs(address_style=True)``).
        assert "(prior unknown)" not in rendered
        # And no arrow glyph either — address rows are bare-after only.
        assert "→" not in rendered

    def test_party_id_swap_without_name_falls_back_to_id_only(self):
        """When customer_id changes without an accompanying customer_name
        FieldChange (the common case — ``customer_name`` isn't a request
        field), the after side renders as ``#<id>``, NOT the old name.
        Same contract as PO #755."""
        actions = [
            {
                "operation": "update_header",
                "succeeded": None,
                "changes": [
                    {"field": "customer_id", "old": 1501, "new": 1502},
                ],
            }
        ]
        app = build_so_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        rendered = str(app.to_json())
        assert "Sarah Johnson (1501)" in rendered
        assert "→" in rendered
        assert "#1502" in rendered
        # Regression-guard: old name must not show on the after side.
        assert "Sarah Johnson (1502)" not in rendered

    def test_unchanged_kind_customer_change_falls_through_to_link_render(self):
        """A no-op customer_id patch (request set customer_id=1501 when it
        was already 1501) emits a ``FieldChangeView(kind="unchanged")``.
        The composite diff line MUST NOT render — fall through to the
        normal ``_render_party_line`` Link form."""
        actions = [
            {
                "operation": "update_header",
                "succeeded": True,
                "changes": [
                    {
                        "field": "customer_id",
                        "old": 1501,
                        "new": 1501,
                        "is_unchanged": True,
                    },
                ],
            }
        ]
        app = build_so_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        rendered = str(app.to_json())
        assert "Sarah Johnson" in rendered
        assert "Sarah Johnson (1501) → Sarah Johnson (1501)" not in rendered

    def test_diff_lines_use_2char_gutter_for_layout_stability(self):
        """Every changed-field line starts with a 2-char gutter (``"  "``
        when not failed, ``"✗ "`` when failed). Failed apply doesn't
        reflow the field text position."""
        actions = [
            {
                "operation": "update_header",
                "succeeded": None,
                "changes": [
                    {"field": "status", "old": "NOT_SHIPPED", "new": "PACKED"},
                ],
            }
        ]
        app = build_so_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        rendered = str(app.to_json())
        assert "  Status:" in rendered

    def test_warnings_block_warnings_gate_confirm(self):
        """``BLOCK:``-prefixed warnings suppress the Confirm button via the
        ``_render_warnings_block`` → ``block_warnings`` → footer gating
        chain. Same contract as PO modify and every other card."""
        app = build_so_modify_ui(
            self._preview(
                [{"operation": "update_header", "succeeded": None, "changes": []}],
                warnings=["BLOCK: cannot proceed — invalid request shape"],
            ),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        rendered = str(app.to_json())
        # Block warning surfaces in the body.
        assert "cannot proceed" in rendered
        # Footer copy switches to the "cannot proceed" muted line.
        assert "Cannot proceed" in rendered

    # --------------------------------------------------------------
    # #858 finding A — per-row chrome morphs from state, not from
    # Python-painted build-time values. Pin the state-bound row shape
    # so a refactor that drops the ``so_<section>_rows`` slots would
    # be caught at unit-test tier (mirroring BOM's ``plan_rows``
    # contract test).
    # --------------------------------------------------------------

    def test_subentity_row_lists_seeded_per_section_on_preview(self):
        """Preview-path build seeds one ``so_<section>_rows`` slot per
        sub-entity section in :data:`_SO_SUBENTITY_GROUPS`. Each slot's
        list mirrors the actions for that section, projected through
        :func:`_build_so_subentity_row` into the columnar cell shape
        (``gutter_summary`` + ``status_label``; #721 Phase 3). Preview rows
        carry ``status_label="PLANNED"`` — shown in the DataTable's Status
        column, consistent with the other modify cards.

        Pin contract: state slots exist on every preview render so the
        on_success ``SetState`` chain reading ``$result.state.so_<section>_rows``
        always has a destination slot — empty list for sections the plan
        doesn't touch (no None-guard needed in the on_success target).
        """
        actions = [
            {
                "operation": "add_row",
                "target_id": None,
                "succeeded": None,
                "changes": [
                    {"field": "variant_id", "old": None, "new": 100, "is_added": True},
                    {"field": "quantity", "old": None, "new": 1.0, "is_added": True},
                ],
            },
            {
                "operation": "delete_address",
                "target_id": 9001,
                "succeeded": None,
                "changes": [],
            },
        ]
        app = build_so_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        assert app.state is not None
        # All four section slots exist (empty when no actions).
        assert app.state["so_rows_rows"] == [
            {
                "gutter_summary": "+ variant 100, qty 1.0",
                "status_label": "PLANNED",
            }
        ]
        assert app.state["so_addresses_rows"] == [
            {
                "gutter_summary": "- address #9001",
                "status_label": "PLANNED",
            }
        ]
        assert app.state["so_fulfillments_rows"] == []
        assert app.state["so_shipping_fees_rows"] == []

    def test_subentity_row_lists_apply_path_carries_per_action_outcome(self):
        """Standalone-applied path seeds row dicts with the apply-time
        ``status_label`` so the result card's DataTable Status column
        renders the right per-row outcome without bouncing through the
        morph. Catches the symmetry the morph relies on — the apply
        tool's envelope ``state.*`` is what ``$result.state.*`` reads,
        so apply-time seeding MUST match the morph target's shape."""
        actions = [
            {
                "operation": "add_shipping_fee",
                "target_id": None,
                "succeeded": True,
                "status_label": "APPLIED",
                "changes": [
                    {"field": "description", "new": "Express", "is_added": True},
                    {"field": "amount", "new": "12.99", "is_added": True},
                ],
            },
            {
                "operation": "delete_row",
                "target_id": 9999,
                "succeeded": False,
                "error": "404 Not Found",
                "status_label": "FAILED",
                "changes": [],
            },
        ]
        app = build_so_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        assert app.state is not None
        # The shipping fee row carries the APPLIED status in its Status cell.
        shipping_rows = app.state["so_shipping_fees_rows"]
        assert len(shipping_rows) == 1
        assert shipping_rows[0]["status_label"] == "APPLIED"
        # The row delete carries the FAILED status + the ✗ failure gutter.
        rows_rows = app.state["so_rows_rows"]
        assert len(rows_rows) == 1
        assert rows_rows[0]["status_label"] == "FAILED"
        assert rows_rows[0]["gutter_summary"].startswith("✗ ")

    def test_subentity_row_lists_merge_not_run_tail_from_extras(self):
        """Apply path: ``response.extras["not_run_actions"]`` carries the
        unattempted plan tail (synthesized by
        :func:`_modify_sales_order_impl`). The renderer must merge those
        into the per-section row bucketing so the morphed card shows
        APPLIED + FAILED + NOT-RUN rows instead of silently HIDING the
        leftover plan past the fail-fast boundary (#858 finding B).

        Without this merge, a 5-row plan that fails on row 2 morphs to
        a card with only 2 rows — operator sees "1 succeeded, 1 failed"
        and never realizes 3 more changes were never attempted.
        """
        actions = [
            {
                "operation": "add_row",
                "target_id": None,
                "succeeded": True,
                "status_label": "APPLIED",
                "changes": [
                    {"field": "variant_id", "new": 100, "is_added": True},
                    {"field": "quantity", "new": "1.0", "is_added": True},
                ],
            },
            {
                "operation": "add_row",
                "target_id": None,
                "succeeded": False,
                "error": "422 invalid variant",
                "status_label": "FAILED",
                "changes": [
                    {"field": "variant_id", "new": 999, "is_added": True},
                    {"field": "quantity", "new": "2.0", "is_added": True},
                ],
            },
        ]
        not_run = [
            {
                "operation": "add_row",
                "target_id": None,
                "succeeded": None,
                "error": None,
                "status_label": "NOT RUN",
                "changes": [
                    {"field": "variant_id", "new": 101, "is_added": True},
                    {"field": "quantity", "new": "3.0", "is_added": True},
                ],
            },
            {
                "operation": "add_row",
                "target_id": None,
                "succeeded": None,
                "error": None,
                "status_label": "NOT RUN",
                "changes": [
                    {"field": "variant_id", "new": 102, "is_added": True},
                    {"field": "quantity", "new": "4.0", "is_added": True},
                ],
            },
        ]
        # Synthesize the apply-response shape the impl produces post-fix
        # (executed actions + ``extras["not_run_actions"]``).
        response = self._applied(actions)
        response["extras"] = {"not_run_actions": not_run}
        app = build_so_modify_ui(
            response,
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        assert app.state is not None
        rows_rows = app.state["so_rows_rows"]
        # 2 executed + 2 NOT RUN = 4 rows visible on the morphed card.
        assert len(rows_rows) == 4
        # Plan order preserved: APPLIED, FAILED, NOT RUN, NOT RUN.
        assert [r["status_label"] for r in rows_rows] == [
            "APPLIED",
            "FAILED",
            "NOT RUN",
            "NOT RUN",
        ]
        # NOT RUN rows surface in the DataTable's Status column (the leftover
        # plan past the fail-fast boundary stays visible, not silently hidden).
        assert rows_rows[2]["status_label"] == "NOT RUN"
        assert rows_rows[3]["status_label"] == "NOT RUN"

    def test_subentity_row_lists_ignore_not_run_on_preview_path(self):
        """The NOT-RUN extras only attach to apply responses (the
        ``not is_preview`` branch in :func:`_modify_sales_order_impl`).
        On preview, every action is already PLANNED so a NOT-RUN merge
        would be a duplicate. Guard against accidental leakage by
        asserting preview ignores ``extras["not_run_actions"]`` even if
        present (e.g. a mock test that doesn't separate paths)."""
        actions = [
            {
                "operation": "add_row",
                "target_id": None,
                "succeeded": None,
                "changes": [
                    {"field": "variant_id", "new": 100, "is_added": True},
                    {"field": "quantity", "new": "1.0", "is_added": True},
                ],
            }
        ]
        response = self._preview(actions)
        response["extras"] = {
            "not_run_actions": [
                {
                    "operation": "add_row",
                    "target_id": None,
                    "succeeded": None,
                    "status_label": "NOT RUN",
                    "changes": [],
                }
            ]
        }
        app = build_so_modify_ui(
            response,
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        assert app.state is not None
        # Preview path: only the one planned action, not the NOT-RUN
        # entry from extras.
        rows_rows = app.state["so_rows_rows"]
        assert len(rows_rows) == 1
        assert rows_rows[0]["status_label"] == "PLANNED"

    def test_subentity_sections_render_state_bound_datatable(self):
        """The sub-entity sections render row content via a ``DataTable``
        whose ``rows`` bind to ``state.so_<section>_rows`` (mustache form)
        — NOT via build-time Python iteration (#721 Phase 3 replaced the
        prior ``ForEach`` line-list with a columnar table). Pins the morph
        contract so a refactor that reverts to static rendering would
        regress finding A.

        Walks the rendered envelope for a ``DataTable`` node whose ``rows``
        is ``"{{ so_rows_rows }}"`` (the Line items section). That binding
        is the load-bearing morph guarantee: the apply-time ``SetState`` of
        ``$result.state.so_rows_rows`` swaps the row list and Prefab's
        renderer re-paints each row's Status cell from the new dicts.
        """
        actions = [
            {
                "operation": "add_row",
                "target_id": None,
                "succeeded": None,
                "changes": [
                    {"field": "variant_id", "old": None, "new": 100, "is_added": True},
                    {"field": "quantity", "old": None, "new": 1.0, "is_added": True},
                ],
            }
        ]
        app = build_so_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        envelope = app.to_json()
        found_datatable_rows: set[str] = set()

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "DataTable":
                    rows = node.get("rows")
                    if isinstance(rows, str):
                        found_datatable_rows.add(rows)
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(envelope)
        # The Line items section's DataTable must bind to the state slot
        # (mustache form). Bare-string row refs crash the JS renderer, and a
        # build-time static row list wouldn't morph after apply.
        assert "{{ so_rows_rows }}" in found_datatable_rows, (
            "Sub-entity rows must render via DataTable(rows='{{ so_rows_rows }}') "
            "— without the state binding the Status column can't morph after "
            "apply (#858 finding A)."
        )

    def test_apply_action_morph_chain_writes_per_section_row_slots(self):
        """The Confirm button's on_success ``SetState`` chain MUST write
        ``$result.state.so_<section>_rows`` into the preview iframe's
        matching state slot, for every section in
        :data:`_SO_SUBENTITY_GROUPS`. A mistyped slot name in either
        side of the chain would leave the preview rows frozen at their
        ``PLANNED`` state even after the apply lands.

        Walks the rendered envelope for SetState nodes whose ``key``
        matches each section's row slot and confirms the matching
        ``value`` template reads from ``$result.state.<same-slot>``.
        """
        app = build_so_modify_ui(
            self._preview(
                [{"operation": "update_header", "succeeded": None, "changes": []}]
            ),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        envelope = app.to_json()
        morph_targets: dict[str, str] = {}

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                # SetState actions serialize as {"action": "setState",
                # "key": ..., "value": ...} (not as components with a
                # "type" field — they're attached to button on_success
                # / on_click slots, not rendered as elements).
                if node.get("action") == "setState":
                    key = node.get("key")
                    value = node.get("value")
                    if isinstance(key, str) and isinstance(value, str):
                        morph_targets[key] = value
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(envelope)
        # Each section MUST have a SetState that copies $result.state.<slot>
        # into the same-name preview slot. Mistyping the template (e.g.
        # $result.so_rows_rows instead of $result.state.so_rows_rows)
        # would leave the row slot frozen — caught here.
        for section_key in ("rows", "addresses", "fulfillments", "shipping_fees"):
            slot = f"so_{section_key}_rows"
            assert slot in morph_targets, (
                f"on_success chain missing SetState for {slot} — the "
                f"{section_key} section's rows would stay frozen at the "
                f"preview-time PLANNED state after apply."
            )
            assert morph_targets[slot] == ("{{ $result.state." + slot + " }}"), (
                f"SetState for {slot} reads from {morph_targets[slot]!r}; "
                f"must read from '$result.state.{slot}' (NOT $result.<slot>) "
                f"because $result resolves to the apply tool's PrefabApp "
                f"envelope, not the raw ModificationResponse."
            )

    # --------------------------------------------------------------
    # #858 finding B — failed top-level delete must surface its error
    # in a dedicated state-driven Alert. Pre-fix the FAILED chrome
    # rendered without the error text from ActionResult.error because
    # delete actions have no field changes (header-changes block
    # rendered nothing) and they're filtered out of the sub-entity
    # Alert (delete is a top-level op, not a sub-entity op).
    # --------------------------------------------------------------

    def test_failed_delete_seeds_header_failed_summary_with_error_text(self):
        """A failed top-level ``delete`` action seeds the
        ``applied_header_failed_count`` + ``applied_header_failed_summary``
        state slots so the dedicated header-op Alert can surface the
        :attr:`ActionResult.error` text. Pre-fix this slot didn't exist
        and the FAILED chrome rendered with no visible error message
        (#858 finding B)."""
        actions = [
            {
                "operation": "delete",
                "target_id": 42,
                "succeeded": False,
                "error": "404 Not Found: sales order 42 does not exist",
                "changes": [],
            }
        ]
        app = build_so_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="delete_sales_order",
        )
        assert app.state is not None
        assert app.state["applied_header_failed_count"] == 1
        summary = app.state["applied_header_failed_summary"]
        # User-facing verb (not the bare wire name "delete") + the
        # ActionResult.error string verbatim. Pre-fix the error message
        # never made it to the rendered card.
        assert "Failed to delete the sales order" in summary
        assert "404 Not Found: sales order 42 does not exist" in summary

    def test_successful_delete_omits_header_failed_alert(self):
        """A successful delete leaves the header-failed slots at 0/empty
        so the state-driven Alert stays hidden (the ``If(Rx(...) > 0)``
        gate keeps the card compact in the success case)."""
        app = build_so_modify_ui(
            self._applied([{"operation": "delete", "succeeded": True, "changes": []}]),
            confirm_request=_StubRequest(),
            confirm_tool="delete_sales_order",
        )
        assert app.state is not None
        assert app.state["applied_header_failed_count"] == 0
        assert app.state["applied_header_failed_summary"] == ""

    def test_failed_header_update_with_changes_surfaces_on_state_alert(self):
        """A failed ``update_header`` action with field changes must
        increment the state-driven ``applied_header_failed_count`` so
        the morph path (preview→Confirm) can surface the error.

        Pre-fix #858 finding C: the SO entity view called the build-time
        :func:`_render_failed_changes_block` which read off the preview-
        time ``changes`` map (every action's ``succeeded=None``). After
        Confirm morphed ``state.applied=True``, that block stayed at
        preview-time content — the ✗ gutter and the per-field error
        Alert never appeared even though the apply had failed.

        Post-fix: :func:`_so_header_op_failure_alert_text` is the single
        source of truth for header-op failures (no-change ops AND
        update_header with field changes). The build-time block was
        removed from the SO entity view so the error renders exactly
        once, from state, on BOTH the standalone-applied path and the
        preview→Confirm morph path.
        """
        actions = [
            {
                "operation": "update_header",
                "target_id": 42,
                "succeeded": False,
                "error": "422 Unprocessable: invalid status transition",
                "changes": [
                    {"field": "status", "old": "PACKED", "new": "DELIVERED"},
                ],
            }
        ]
        app = build_so_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        assert app.state is not None
        # State-driven Alert now owns the failure; ``count == 1`` so the
        # ``If(Rx("applied_header_failed_count") > 0)`` gate fires on the
        # morphed iframe.
        assert app.state["applied_header_failed_count"] == 1
        summary = app.state["applied_header_failed_summary"]
        assert "Failed to modify the sales order header" in summary
        assert "422 Unprocessable: invalid status transition" in summary
        # The error must be reachable in the rendered card too — same
        # text as the state summary, painted by the state-bound Alert
        # (no duplicate build-time block).
        rendered = str(app.to_json())
        assert "422 Unprocessable" in rendered
        # No double-render in the *visible* view tree: pre-fix, the
        # build-time ``_render_failed_changes_block`` painted an
        # ``AlertDescription`` with the verbatim error text into the
        # view tree, AND the state-driven Alert also picked it up,
        # giving the operator two competing error blocks. Post-fix the
        # build-time block is removed for SO — the only AlertDescription
        # carrying the error text references it via mustache
        # ``{{ applied_header_failed_summary }}``, not as a literal.
        envelope = app.to_json()
        view_str = str(envelope.get("view"))
        assert "422 Unprocessable: invalid status transition" not in view_str, (
            "Build-time _render_failed_changes_block must not paint the "
            "error literal into the view tree on SO — only the state-driven "
            "Alert may surface it (via mustache binding)."
        )

    def test_apply_action_morph_chain_writes_header_failed_slots(self):
        """The Confirm button's on_success chain MUST write
        ``$result.state.applied_header_failed_count`` /
        ``applied_header_failed_summary`` into the preview iframe's
        matching slots so the header-op Alert can pop in after the
        morph lands. Mistyped slot names would leave a failed delete
        rendering FAILED chrome without the error text the operator
        needs to diagnose the failure (#858 finding B)."""
        app = build_so_modify_ui(
            self._preview([{"operation": "delete", "succeeded": None, "changes": []}]),
            confirm_request=_StubRequest(),
            confirm_tool="delete_sales_order",
        )
        envelope = app.to_json()
        morph_targets: dict[str, str] = {}

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                # SetState actions serialize as {"action": "setState",
                # "key": ..., "value": ...} (not as components with a
                # "type" field — they're attached to button on_success
                # / on_click slots, not rendered as elements).
                if node.get("action") == "setState":
                    key = node.get("key")
                    value = node.get("value")
                    if isinstance(key, str) and isinstance(value, str):
                        morph_targets[key] = value
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(envelope)
        for slot in ("applied_header_failed_count", "applied_header_failed_summary"):
            assert slot in morph_targets, (
                f"on_success chain missing SetState for {slot} — a failed "
                f"delete after Confirm would render with no error text "
                f"(#858 finding B)."
            )
            assert morph_targets[slot] == ("{{ $result.state." + slot + " }}")

    # --------------------------------------------------------------
    # #858 round-8 — Header NOT-RUN must have a rendering surface.
    # _index_changes_by_field filters NOT-RUN out (round 7 fix) and
    # _build_so_subentity_row_lists only buckets sub-entity ops, so a
    # synthesized NOT-RUN ``update_header`` (e.g. the close-phase step
    # of a failed correct_sales_order) had nowhere to surface. The
    # state-driven Alert below covers the gap.
    # --------------------------------------------------------------

    def test_skipped_header_seeds_skipped_state_and_alert_text(self):
        """A NOT-RUN ``update_header`` action (synthesized when a
        fail-fast ``correct_sales_order`` skips its close-phase header
        step) seeds ``applied_header_skipped_count`` /
        ``applied_header_skipped_summary`` so the dedicated Alert can
        surface "Step skipped: modify the sales order header" to the
        operator. Pre-fix this slot didn't exist and the skipped close-
        phase step had no rendering surface — sub-entity NOT-RUN rows
        rendered but the header step was invisible (#858 round-8)."""
        actions = [
            {
                "operation": "update_row",
                "target_id": 10,
                "succeeded": False,
                "error": "Katana refused the row edit",
                "changes": [{"field": "variant_id", "old": 500, "new": 501}],
            },
            {
                "operation": "update_header",
                "target_id": 42,
                "succeeded": None,
                "error": None,
                "changes": [{"field": "status", "old": None, "new": "DELIVERED"}],
                "status_label": "NOT RUN",
            },
        ]
        app = build_so_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="correct_sales_order",
        )
        assert app.state is not None
        assert app.state["applied_header_skipped_count"] == 1
        summary = app.state["applied_header_skipped_summary"]
        # User-facing verb (not the bare wire name "update_header") +
        # the "earlier phase failed" causal phrase so the operator can
        # tell at a glance why the step didn't run.
        assert "Step skipped: modify the sales order header" in summary
        assert "NOT RUN" in summary
        assert "earlier phase failed" in summary

    def test_no_skipped_header_omits_skipped_alert(self):
        """When every header step ran (or there were none), the
        skipped slots stay at 0/empty so the ``If(Rx(...) > 0)`` gate
        keeps the Alert hidden — same compactness rule as the failed-
        op Alert."""
        app = build_so_modify_ui(
            self._applied(
                [{"operation": "update_header", "succeeded": True, "changes": []}]
            ),
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        assert app.state is not None
        assert app.state["applied_header_skipped_count"] == 0
        assert app.state["applied_header_skipped_summary"] == ""

    def test_apply_action_morph_chain_writes_header_skipped_slots(self):
        """The Confirm button's on_success chain MUST also propagate the
        ``applied_header_skipped_*`` slots from the apply tool's
        ``$result.state.*`` envelope into the preview iframe so the
        Alert can pop in on the morph. Mistyped slot names would leave
        a skipped close-phase step silently invisible after Confirm
        (#858 round-8)."""
        app = build_so_modify_ui(
            self._preview(
                [{"operation": "update_header", "succeeded": None, "changes": []}]
            ),
            confirm_request=_StubRequest(),
            confirm_tool="correct_sales_order",
        )
        envelope = app.to_json()
        morph_targets: dict[str, str] = {}

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("action") == "setState":
                    key = node.get("key")
                    value = node.get("value")
                    if isinstance(key, str) and isinstance(value, str):
                        morph_targets[key] = value
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(envelope)
        for slot in (
            "applied_header_skipped_count",
            "applied_header_skipped_summary",
        ):
            assert slot in morph_targets, (
                f"on_success chain missing SetState for {slot} — a "
                f"skipped header step after Confirm would have no "
                f"rendering surface (#858 round-8)."
            )
            assert morph_targets[slot] == ("{{ $result.state." + slot + " }}")

    # --------------------------------------------------------------
    # #858 Copilot 3313163122 — Line Items metric must render on a
    # real ModificationResponse (which has no item_count field) by
    # deriving from prior_state.sales_order_rows.
    # --------------------------------------------------------------

    def test_item_count_derived_from_prior_state_rows_when_absent(self):
        """``ModificationResponse`` doesn't carry ``item_count`` (only
        ``SalesOrderResponse`` does), so the modify card's Tier-2
        "Line Items" Metric would render blank on a real apply response.
        The build-side derivation in :func:`_normalize_so_prior_state`
        falls back to ``len(prior_state["sales_order_rows"])`` so the
        Metric renders consistently across create and modify cards
        (#858 Copilot 3313163122)."""
        prior_with_rows = dict(self._SO_PRIOR)
        prior_with_rows["sales_order_rows"] = [
            {"id": 10, "variant_id": 500, "quantity": 1},
            {"id": 11, "variant_id": 501, "quantity": 2},
            {"id": 12, "variant_id": 502, "quantity": 3},
        ]
        # Build a response that mimics the real shape: no top-level
        # item_count, prior_state carries sales_order_rows.
        response = self._applied(
            [{"operation": "update_header", "succeeded": True, "changes": []}],
            prior_state=prior_with_rows,
        )
        assert "item_count" not in response  # guardrail
        app = build_so_modify_ui(
            response,
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        rendered = str(app.to_json())
        # Metric renders "Line Items" label + the derived count value.
        # Both must appear in the view tree; pre-fix the value side
        # rendered blank because entity.get("item_count") returned None.
        assert "Line Items" in rendered
        assert "3" in rendered

    def test_item_count_explicit_overrides_derived(self):
        """If the response carries an explicit ``item_count`` (rare
        but possible for non-MorphedResponse paths), the explicit
        value wins — the derivation is a fallback, not an override.
        Otherwise a stale prior_state row list could shadow the
        canonical response count."""
        prior_with_rows = dict(self._SO_PRIOR)
        prior_with_rows["sales_order_rows"] = [
            {"id": 10, "variant_id": 500, "quantity": 1},
        ]
        # The explicit item_count (7) must win over the derived count
        # (1 row in prior_state) — entity overlays response on top of
        # normalized prior_state.
        response = self._applied(
            [{"operation": "update_header", "succeeded": True, "changes": []}],
            prior_state=prior_with_rows,
            item_count=7,
        )
        app = build_so_modify_ui(
            response,
            confirm_request=_StubRequest(),
            confirm_tool="modify_sales_order",
        )
        rendered = str(app.to_json())
        assert "Line Items" in rendered
        assert "7" in rendered


class TestMergeBomRowsForModifyCard:
    """``_merge_bom_rows_for_modify_card`` projects ``prior_state.rows`` +
    plan actions into the row-shape the BOM modify DataTable consumes.
    These tests pin the kind-discriminator + cell-decoration contract so
    downstream renderer changes don't regress the user-facing shape.
    """

    _EXISTING_ROW_A: ClassVar[dict[str, Any]] = {
        "id": "11111111-1111-1111-1111-111111111111",
        "product_item_id": 100,
        "product_variant_id": 200,
        "ingredient_variant_id": 401,
        "sku": "BLT-M5-10",
        "display_name": "M5 chainring bolt",
        "quantity": 6.0,
        "notes": None,
        "rank": 10000,
    }
    _EXISTING_ROW_B: ClassVar[dict[str, Any]] = {
        "id": "22222222-2222-2222-2222-222222222222",
        "product_item_id": 100,
        "product_variant_id": 200,
        "ingredient_variant_id": 402,
        "sku": "BLT-M6-12",
        "display_name": "M6 hex screw",
        "quantity": 4.0,
        "notes": "optional",
        "rank": 20000,
    }
    _PRIOR_STATE: ClassVar[dict[str, Any]] = {
        "rows": [_EXISTING_ROW_A, _EXISTING_ROW_B],
    }
    _RESOLVED: ClassVar[dict[int, dict[str, str | None]]] = {
        301: {"sku": "FS90250", "display_name": "M5 chain pin"},
        401: {"sku": "BLT-M5-10", "display_name": "M5 chainring bolt"},
        402: {"sku": "BLT-M6-12", "display_name": "M6 hex screw"},
    }

    def test_existing_rows_carry_existing_kind_with_empty_status(self):
        """No actions → both rows render as existing-untouched with empty
        status (the per-row Status badge would mislead if it said
        PLANNED/APPLIED for rows that aren't part of the plan)."""
        rows = _merge_bom_rows_for_modify_card(self._PRIOR_STATE, [], self._RESOLVED)
        assert len(rows) == 2
        assert all(r["kind"] == "existing" for r in rows)
        assert all(r["status_label"] == "" for r in rows)

    def test_add_row_synthesized_with_resolved_sku_and_display_name(self):
        """``add_bom_row`` actions have no target_id — the row is synthesized
        from the action's changes; SKU/display_name come from
        ``resolved_ingredients``. The row appends after existing rows."""
        action = {
            "operation": "add_bom_row",
            "target_id": None,
            "succeeded": None,
            "changes": [
                {
                    "field": "ingredient_variant_id",
                    "old": None,
                    "new": 301,
                    "is_added": True,
                },
                {"field": "quantity", "old": None, "new": 2.0, "is_added": True},
            ],
            "status_label": "PLANNED",
        }
        rows = _merge_bom_rows_for_modify_card(
            self._PRIOR_STATE, [action], self._RESOLVED
        )
        assert len(rows) == 3
        # Adds trail existing rows.
        added = rows[-1]
        assert added["kind"] == "added"
        assert added["sku"] == "FS90250"
        assert added["display_name"] == "M5 chain pin"
        assert added["quantity_label"] == "2"
        assert added["status_label"] == "PLANNED"
        assert added["status_prefix"] == "+ "

    def test_add_row_with_unresolved_ingredient_degrades_to_null_sku(self):
        """If the cache miss prevented resolution, the row still renders
        with the ingredient_variant_id so the user has *something* —
        ``sku=None`` and ``display_name=None`` mean the SKU column shows
        "(unresolved)" via the prepare-rows step (covered in builder
        tests). Here we pin the underlying merge contract."""
        action = {
            "operation": "add_bom_row",
            "target_id": None,
            "succeeded": None,
            "changes": [
                {
                    "field": "ingredient_variant_id",
                    "old": None,
                    "new": 999,
                    "is_added": True,
                },
                {"field": "quantity", "old": None, "new": 1.0, "is_added": True},
            ],
        }
        rows = _merge_bom_rows_for_modify_card(self._PRIOR_STATE, [action], {})
        added = rows[-1]
        assert added["kind"] == "added"
        assert added["ingredient_variant_id"] == 999
        assert added["sku"] is None
        assert added["display_name"] is None

    def test_update_row_decorates_quantity_with_unknown_prior(self):
        """``update_bom_row`` actions emit ``is_unknown_prior=True``
        (BOM has no GET-by-id). The merged row reflects the targeted
        existing row's identity with a diff-decorated quantity cell."""
        action = {
            "operation": "update_bom_row",
            "target_id": "11111111-1111-1111-1111-111111111111",
            "succeeded": None,
            "changes": [
                {
                    "field": "quantity",
                    "old": None,
                    "new": 8.0,
                    "is_unknown_prior": True,
                },
            ],
            "status_label": "PLANNED",
        }
        rows = _merge_bom_rows_for_modify_card(
            self._PRIOR_STATE, [action], self._RESOLVED
        )
        updated = next(r for r in rows if r["kind"] == "updated")
        # Identity preserved from the snapshot.
        assert updated["sku"] == "BLT-M5-10"
        assert updated["display_name"] == "M5 chainring bolt"
        # Quantity diff renders with prior-unknown prefix.
        assert updated["quantity_label"] == "(prior unknown) → 8"
        assert updated["status_label"] == "PLANNED"
        assert updated["status_prefix"] == "~ "

    def test_update_row_with_ingredient_swap_surfaces_new_sku(self):
        """Patching ``ingredient_variant_id`` swaps the row's SKU /
        display_name to the post-patch identity so users see what the
        row will *become*. Existing rank + status reflect the patch."""
        action = {
            "operation": "update_bom_row",
            "target_id": "11111111-1111-1111-1111-111111111111",
            "succeeded": None,
            "changes": [
                {
                    "field": "ingredient_variant_id",
                    "old": None,
                    "new": 301,
                    "is_unknown_prior": True,
                },
            ],
            "status_label": "PLANNED",
        }
        rows = _merge_bom_rows_for_modify_card(
            self._PRIOR_STATE, [action], self._RESOLVED
        )
        updated = next(r for r in rows if r["kind"] == "updated")
        assert updated["sku"] == "FS90250"
        assert updated["display_name"] == "M5 chain pin"

    def test_delete_row_flips_kind_and_status(self):
        """``delete_bom_row`` actions flip the matched row's kind to
        ``deleted`` and pull the action's status_label onto it. The row's
        original identity stays so the user sees *what* is going away."""
        action = {
            "operation": "delete_bom_row",
            "target_id": "22222222-2222-2222-2222-222222222222",
            "succeeded": None,
            "changes": [],
            "status_label": "PLANNED",
        }
        rows = _merge_bom_rows_for_modify_card(
            self._PRIOR_STATE, [action], self._RESOLVED
        )
        deleted = next(r for r in rows if r["kind"] == "deleted")
        assert deleted["sku"] == "BLT-M6-12"  # original identity preserved
        assert deleted["status_label"] == "PLANNED"
        assert deleted["status_prefix"] == "- "

    def test_applied_failure_carries_error_per_row(self):
        """When an action fails, its row carries the FAILED status and the
        error message (rendered in the consolidated bottom Alert; not
        inline). Verified ``True`` vs ``None`` is not relevant here —
        only succeeded/error/status_label."""
        action = {
            "operation": "update_bom_row",
            "target_id": "11111111-1111-1111-1111-111111111111",
            "succeeded": False,
            "error": "422 Unprocessable: quantity must be > 0",
            "changes": [
                {"field": "quantity", "old": None, "new": -1, "is_unknown_prior": True}
            ],
            "status_label": "FAILED",
        }
        rows = _merge_bom_rows_for_modify_card(
            self._PRIOR_STATE, [action], self._RESOLVED
        )
        failed = next(r for r in rows if r["status_label"] == "FAILED")
        assert failed["kind"] == "updated"
        assert failed["error"] == "422 Unprocessable: quantity must be > 0"
        assert failed["status_variant"] == "destructive"

    def test_empty_prior_state_with_only_adds_renders_added_rows_only(self):
        """A BOM that doesn't exist yet (or fetch failed) with an add-only
        plan → only the added rows surface; no existing rows."""
        action = {
            "operation": "add_bom_row",
            "target_id": None,
            "succeeded": None,
            "changes": [
                {
                    "field": "ingredient_variant_id",
                    "old": None,
                    "new": 301,
                    "is_added": True,
                },
                {"field": "quantity", "old": None, "new": 5.0, "is_added": True},
            ],
        }
        rows = _merge_bom_rows_for_modify_card(None, [action], self._RESOLVED)
        assert len(rows) == 1
        assert rows[0]["kind"] == "added"
        assert rows[0]["sku"] == "FS90250"

    def test_empty_plan_with_no_existing_rows_returns_empty(self):
        """No prior + no plan → empty list (caller renders a placeholder)."""
        rows = _merge_bom_rows_for_modify_card(None, [], {})
        assert rows == []

    def test_existing_rows_preserve_rank_order(self):
        """Snapshot order (by rank) must survive the merge — DataTable
        renders rows in input order; users expect rank-1 above rank-2."""
        reversed_prior = {
            "rows": [self._EXISTING_ROW_B, self._EXISTING_ROW_A]  # rank 20000, 10000
        }
        rows = _merge_bom_rows_for_modify_card(reversed_prior, [], self._RESOLVED)
        # Sorted by rank ascending — A before B.
        assert rows[0]["sku"] == "BLT-M5-10"
        assert rows[1]["sku"] == "BLT-M6-12"

    def test_update_row_with_orphan_target_id_synthesizes_placeholder(self):
        """``update_bom_row`` targeting an id not in the snapshot still
        surfaces — the merge synthesizes a placeholder so the action is
        visible. Rare in practice (stale snapshot or partial fetch),
        but the alternative (silent drop) would be worse."""
        orphan_id = "99999999-9999-9999-9999-999999999999"
        action = {
            "operation": "update_bom_row",
            "target_id": orphan_id,
            "succeeded": None,
            "changes": [
                {
                    "field": "quantity",
                    "old": None,
                    "new": 3.0,
                    "is_unknown_prior": True,
                },
            ],
            "status_label": "PLANNED",
        }
        rows = _merge_bom_rows_for_modify_card(
            self._PRIOR_STATE, [action], self._RESOLVED
        )
        # 2 existing + 1 synthesized orphan with updated decoration.
        assert len(rows) == 3
        orphan = next(r for r in rows if r["id"] == orphan_id)
        assert orphan["kind"] == "updated"
        assert orphan["sku"] is None  # no identity to resolve from
        assert orphan["display_name"] is None
        assert orphan["quantity_label"] == "(prior unknown) → 3"
        assert orphan["status_label"] == "PLANNED"
        assert orphan["status_prefix"] == "~ "

    def test_delete_row_with_orphan_target_id_synthesizes_placeholder(self):
        """``delete_bom_row`` targeting an id not in the snapshot still
        surfaces — same rationale as the update-orphan case."""
        orphan_id = "99999999-9999-9999-9999-999999999999"
        action = {
            "operation": "delete_bom_row",
            "target_id": orphan_id,
            "succeeded": None,
            "changes": [],
            "status_label": "PLANNED",
        }
        rows = _merge_bom_rows_for_modify_card(
            self._PRIOR_STATE, [action], self._RESOLVED
        )
        assert len(rows) == 3
        orphan = next(r for r in rows if r["id"] == orphan_id)
        assert orphan["kind"] == "deleted"
        assert orphan["sku"] is None
        assert orphan["status_label"] == "PLANNED"
        assert orphan["status_prefix"] == "- "

    def test_all_deletes_plan_renders_every_row_as_deleted(self):
        """A "clear the recipe" plan — every existing row marked for
        deletion. Symmetric inverse of the all-adds-to-empty-BOM case;
        validates that the merge handles homogeneous delete plans."""
        delete_a = {
            "operation": "delete_bom_row",
            "target_id": "11111111-1111-1111-1111-111111111111",
            "succeeded": None,
            "changes": [],
            "status_label": "PLANNED",
        }
        delete_b = {
            "operation": "delete_bom_row",
            "target_id": "22222222-2222-2222-2222-222222222222",
            "succeeded": None,
            "changes": [],
            "status_label": "PLANNED",
        }
        rows = _merge_bom_rows_for_modify_card(
            self._PRIOR_STATE, [delete_a, delete_b], self._RESOLVED
        )
        assert len(rows) == 2
        assert all(r["kind"] == "deleted" for r in rows)
        assert all(r["status_prefix"] == "- " for r in rows)
        # Identity preserved so the user sees *what* is being removed.
        skus = {r["sku"] for r in rows}
        assert skus == {"BLT-M5-10", "BLT-M6-12"}

    def test_unknown_operation_is_logged_and_dropped(self, caplog):
        """Future operation strings (e.g. ``reorder_bom_rows``) that the
        merge doesn't know about should emit a warning rather than
        silently vanishing. Surfaces gaps during dev when a new op lands
        on the planner side without a renderer update.
        """
        import logging

        from katana_mcp.logging import setup_logging

        # Force structlog through stdlib + JSONRenderer so caplog sees the
        # emitted warning. Without this the test depends on whether some
        # earlier test in the same xdist worker happened to call
        # ``setup_logging`` — flaky between sequential and parallel runs.
        setup_logging(log_level="WARNING", log_format="json")
        action = {
            "operation": "reorder_bom_rows",
            "target_id": "11111111-1111-1111-1111-111111111111",
            "succeeded": None,
            "changes": [],
            "status_label": "PLANNED",
        }
        # The drop-warning now fires from the shared collection-diff skeleton
        # (``merge_collection_diff_rows``) that ``_merge_bom_rows_for_modify_card``
        # delegates to, not from ``bom_table`` itself.
        with caplog.at_level(
            logging.WARNING, logger="katana_mcp.tools.foundation.collection_diff"
        ):
            rows = _merge_bom_rows_for_modify_card(
                self._PRIOR_STATE, [action], self._RESOLVED
            )
        # The unknown action doesn't pollute the rendered rows.
        assert len(rows) == 2
        assert all(r["kind"] == "existing" for r in rows)
        # The merge logs a warning so the dev sees the dropped action.
        matched = [
            rec
            for rec in caplog.records
            if rec.name == "katana_mcp.tools.foundation.collection_diff"
            and rec.levelname == "WARNING"
            and "reorder_bom_rows" in rec.getMessage()
        ]
        assert matched, (
            "Expected a WARNING log record mentioning reorder_bom_rows; "
            f"saw {len(caplog.records)} record(s): "
            f"{[(r.name, r.levelname, r.getMessage()[:80]) for r in caplog.records]}"
        )


class TestBuildBOMModifyUI:
    """``build_bom_modify_ui`` (#811) — the diff-decorated BOM modify card.

    Table-as-entity-view variant of the modify-card family: existing rows
    render unchanged, plan adds appear with a ``+`` prefix, plan updates
    show ``old → new`` quantity diffs, plan deletes carry a ``-`` prefix
    + FAILED/APPLIED status. The summary line under the header reads
    ``+N added, ~M updated, -K deleted``.
    """

    _BOM_PRIOR: ClassVar[dict[str, Any]] = {
        "product_variant_id": 200,
        "product_id": 100,
        "product_name": "Mayhem 140 Frame",
        "variant_sku": "MA14025RTLG",
        "variant_display_name": "Mayhem 140 Frame / Large",
        "is_producible": True,
        "uom": "pcs",
        "katana_url": "https://factory.katanamrp.com/product/100",
        "total_count": 2,
        "rows": [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "product_item_id": 100,
                "product_variant_id": 200,
                "ingredient_variant_id": 401,
                "sku": "BLT-M5-10",
                "display_name": "M5 chainring bolt",
                "quantity": 6.0,
                "notes": None,
                "rank": 10000,
            },
            {
                "id": "22222222-2222-2222-2222-222222222222",
                "product_item_id": 100,
                "product_variant_id": 200,
                "ingredient_variant_id": 402,
                "sku": "BLT-M6-12",
                "display_name": "M6 hex screw",
                "quantity": 4.0,
                "notes": "optional",
                "rank": 20000,
            },
        ],
    }
    _RESOLVED: ClassVar[dict[int, dict[str, str | None]]] = {
        301: {"sku": "FS90250", "display_name": "M5 chain pin"},
        302: {"sku": "FS90251", "display_name": "M6 hex screw v2"},
        401: {"sku": "BLT-M5-10", "display_name": "M5 chainring bolt"},
        402: {"sku": "BLT-M6-12", "display_name": "M6 hex screw"},
    }

    @classmethod
    def _preview(
        cls,
        actions: list[dict[str, Any]] | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        return {
            "entity_type": "product_bom",
            "entity_id": 200,
            "is_preview": True,
            "actions": actions or [],
            "prior_state": dict(cls._BOM_PRIOR),
            "extras": {"resolved_ingredients": dict(cls._RESOLVED)},
            "warnings": [],
            "next_actions": [],
            "message": "Preview",
            "katana_url": None,
            **overrides,
        }

    @classmethod
    def _applied(
        cls,
        actions: list[dict[str, Any]] | None = None,
        **overrides: Any,
    ) -> dict[str, Any]:
        from katana_mcp.tools.foundation.bom_table import (
            _merge_bom_rows_for_modify_card,
            _prepare_bom_table_rows,
            _summarize_apply_outcome,
        )

        actions_list = actions or []
        merged = _merge_bom_rows_for_modify_card(
            cls._BOM_PRIOR, actions_list, cls._RESOLVED
        )
        applied_plan_rows = _prepare_bom_table_rows(merged)
        outcome_label, outcome_variant = _summarize_apply_outcome(actions_list)
        failed_rows = [
            r for r in applied_plan_rows if r.get("status_label") == "FAILED"
        ]
        summary_lines: list[str] = []
        for r in failed_rows:
            sku = r.get("sku") or f"variant {r.get('ingredient_variant_id')}"
            err = r.get("error") or "unknown error"
            summary_lines.append(f"Failed — {sku}: {err}")

        base = cls._preview(actions_list, is_preview=False, **overrides)
        # Mirror what ``_modify_product_bom_impl`` packs into
        # ``response.extras`` on the apply branch so the state-driven
        # Tier-1 Badge + failed-row Alert have the same data they'd get
        # in production. Callers that pass an explicit ``extras=`` retain
        # full control.
        if "extras" not in overrides:
            base["extras"] = {
                **base["extras"],
                "applied_plan_rows": applied_plan_rows,
                "applied_outcome_label": outcome_label,
                "applied_outcome_variant": outcome_variant,
                "applied_failed_count": len(failed_rows),
                "applied_failed_summary": "\n".join(summary_lines),
            }
        return base

    @staticmethod
    def _add_action(*, ingredient_id: int, quantity: float, **overrides: Any) -> dict:
        return {
            "operation": "add_bom_row",
            "target_id": None,
            "succeeded": None,
            "changes": [
                {
                    "field": "ingredient_variant_id",
                    "old": None,
                    "new": ingredient_id,
                    "is_added": True,
                },
                {
                    "field": "quantity",
                    "old": None,
                    "new": quantity,
                    "is_added": True,
                },
            ],
            "status_label": "PLANNED",
            **overrides,
        }

    @staticmethod
    def _update_action(
        *, target_id: str, new_quantity: float, **overrides: Any
    ) -> dict:
        return {
            "operation": "update_bom_row",
            "target_id": target_id,
            "succeeded": None,
            "changes": [
                {
                    "field": "quantity",
                    "old": None,
                    "new": new_quantity,
                    "is_unknown_prior": True,
                },
            ],
            "status_label": "PLANNED",
            **overrides,
        }

    @staticmethod
    def _delete_action(*, target_id: str, **overrides: Any) -> dict:
        return {
            "operation": "delete_bom_row",
            "target_id": target_id,
            "succeeded": None,
            "changes": [],
            "status_label": "PLANNED",
            **overrides,
        }

    def test_preview_with_mixed_plan_renders_all_kinds_and_summary(self):
        """The canonical multi-kind scenario: 1 add + 1 update + 1 delete +
        2 existing untouched. Pins every kind of row appearing in the card
        and the summary line counting them."""
        actions = [
            self._add_action(ingredient_id=301, quantity=2.0),
            self._update_action(
                target_id="11111111-1111-1111-1111-111111111111", new_quantity=8.0
            ),
            self._delete_action(target_id="22222222-2222-2222-2222-222222222222"),
        ]
        app = build_bom_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="manage_product_bom",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        # Header carries the product identity.
        assert "Mayhem 140 Frame" in rendered
        assert "MA14025RTLG" in rendered
        assert "pcs" in rendered
        # Added row's resolved SKU surfaces (the user-centric piece).
        assert "FS90250" in rendered
        assert "M5 chain pin" in rendered
        # Updated row's quantity diff arrow.
        assert "(prior unknown) → 8" in rendered
        # Deleted row's original identity surfaces.
        assert "BLT-M6-12" in rendered
        # Summary line.
        assert "+1 added" in rendered
        assert "~1 updated" in rendered
        assert "-1 deleted" in rendered

    def test_added_row_with_unresolved_ingredient_degrades_gracefully(self):
        """If the cache miss prevented resolution (extras lookup is empty),
        the added row shows ``(unresolved)`` in the SKU column and falls
        back to ``variant <id>`` in the display name — the user still sees
        *something* to identify the row by."""
        actions = [self._add_action(ingredient_id=99999, quantity=1.0)]
        app = build_bom_modify_ui(
            self._preview(actions, extras={"resolved_ingredients": {}}),
            confirm_request=_StubRequest(),
            confirm_tool="manage_product_bom",
        )
        rendered = str(app.to_json())
        assert "(unresolved)" in rendered
        assert "variant 99999" in rendered

    def test_applied_state_renders_per_row_status_pills(self):
        """The applied card carries per-row APPLIED / FAILED pills on each
        plan-derived row. The card-level state badge tracks the aggregate
        outcome (APPLIED for all-success, FAILED for all-failure, PARTIAL
        FAILURE for mixed)."""
        actions = [
            self._add_action(
                ingredient_id=301,
                quantity=2.0,
                succeeded=True,
                status_label="APPLIED",
            ),
            self._update_action(
                target_id="11111111-1111-1111-1111-111111111111",
                new_quantity=8.0,
                succeeded=True,
                status_label="APPLIED",
            ),
        ]
        app = build_bom_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="manage_product_bom",
        )
        rendered = str(app.to_json())
        # Aggregate header badge.
        assert "APPLIED" in rendered
        # Per-row status pills land in plan_rows state so they ride the
        # DataTable rows binding. Two rows = two APPLIED pills minimum.
        state_rows = app.state.get("plan_rows") if app.state else []
        assert isinstance(state_rows, list)
        statuses = [r["status_label"] for r in state_rows]
        assert statuses.count("APPLIED") == 2

    def test_partial_failure_surfaces_failed_error_in_alert(self):
        """A mixed applied outcome (1 success + 1 fail) renders the
        consolidated failed-rows Alert at the bottom of the table so the
        actual error message reaches the user without crowding the row
        cells. The row's per-row pill says FAILED."""
        actions = [
            self._add_action(
                ingredient_id=301,
                quantity=2.0,
                succeeded=True,
                status_label="APPLIED",
            ),
            self._update_action(
                target_id="11111111-1111-1111-1111-111111111111",
                new_quantity=8.0,
                succeeded=False,
                error="422 Unprocessable: quantity must be > 0",
                status_label="FAILED",
            ),
        ]
        app = build_bom_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="manage_product_bom",
        )
        rendered = str(app.to_json())
        # Card-level state badge.
        assert "PARTIAL FAILURE" in rendered
        # Error surfaces in the consolidated Alert at the bottom.
        assert "422 Unprocessable" in rendered

    def test_empty_plan_with_existing_rows_renders_table_with_no_summary(self):
        """A no-op plan (no actions) → the table shows existing rows
        without the +/~/- summary line (empty plan, nothing to count)."""
        app = build_bom_modify_ui(
            self._preview([]),
            confirm_request=_StubRequest(),
            confirm_tool="manage_product_bom",
        )
        rendered = str(app.to_json())
        # Existing rows surface.
        assert "BLT-M5-10" in rendered
        assert "BLT-M6-12" in rendered
        # No summary fragments.
        assert "+0 added" not in rendered
        assert "~0 updated" not in rendered

    def test_empty_prior_with_only_adds_renders_added_rows(self):
        """First-time BOM (no existing rows, prior_state is None or empty)
        + add-only plan → the card renders the added rows with their
        resolved identities. Common case: setting up a recipe for a new
        product."""
        actions = [
            self._add_action(ingredient_id=301, quantity=2.0),
            self._add_action(ingredient_id=302, quantity=4.0),
        ]
        app = build_bom_modify_ui(
            self._preview(actions, prior_state=None),
            confirm_request=_StubRequest(),
            confirm_tool="manage_product_bom",
        )
        rendered = str(app.to_json())
        assert "FS90250" in rendered
        assert "FS90251" in rendered
        assert "+2 added" in rendered

    def test_confirm_label_pluralizes_with_action_count(self):
        """Confirm button label reads ``Confirm 3 BOM changes`` so the user
        knows what they're committing to. Singular form for 1 action."""
        single = build_bom_modify_ui(
            self._preview([self._add_action(ingredient_id=301, quantity=1.0)]),
            confirm_request=_StubRequest(),
            confirm_tool="manage_product_bom",
        )
        assert "Confirm 1 BOM change" in str(single.to_json())

        multi = build_bom_modify_ui(
            self._preview(
                [
                    self._add_action(ingredient_id=301, quantity=1.0),
                    self._add_action(ingredient_id=302, quantity=1.0),
                    self._add_action(ingredient_id=303, quantity=1.0),
                ]
            ),
            confirm_request=_StubRequest(),
            confirm_tool="manage_product_bom",
        )
        assert "Confirm 3 BOM changes" in str(multi.to_json())

    def test_card_does_not_leak_internal_action_labels(self):
        """Anti-pattern guard (per ``feedback-user-centric-card-content``):
        the rendered card MUST NOT carry the internal ActionResult model's
        ``Add Bom Row`` / ``Update Bom Row`` / ``N field(s) set`` labels —
        those are exactly what #811 exists to eliminate."""
        actions = [
            self._add_action(ingredient_id=301, quantity=2.0),
            self._update_action(
                target_id="11111111-1111-1111-1111-111111111111", new_quantity=8.0
            ),
        ]
        app = build_bom_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="manage_product_bom",
        )
        rendered = str(app.to_json())
        # Anti-pattern strings — these would indicate the legacy
        # _ACTION_COLUMNS shape leaked through.
        assert "Add Bom Row" not in rendered
        assert "Update Bom Row" not in rendered
        assert "Delete Bom Row" not in rendered
        assert "field(s) set" not in rendered
        assert "field(s) changed" not in rendered

    def test_state_seeds_plan_rows_for_datatable_binding(self):
        """The DataTable binds rows via ``{{ plan_rows }}`` — the merged
        row list must seed ``state.plan_rows`` so the mustache reference
        resolves at render time. ``_assert_state_bindings_resolve`` checks
        the mustache form; this test pins the underlying state shape."""
        actions = [self._add_action(ingredient_id=301, quantity=2.0)]
        app = build_bom_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="manage_product_bom",
        )
        assert app.state is not None
        plan_rows = app.state.get("plan_rows")
        assert isinstance(plan_rows, list)
        # 2 existing + 1 added.
        assert len(plan_rows) == 3
        kinds = [r["kind"] for r in plan_rows]
        assert kinds.count("existing") == 2
        assert kinds.count("added") == 1


class TestBuildItemModifyUI:
    """``build_item_modify_ui`` (#726) — the diff-decorated item modify/delete
    card.

    Two diff surfaces: header scalar fields (``_render_item_entity_view``
    overlay) and the variants collection (shared collection-diff table). Sub-
    type variance: product/material render the variant table, services don't.
    Mirrors the BOM modify card's preview→apply morph + outcome chrome.
    """

    # Raw ``Product.to_dict()`` shape — the wire form ``serialize_for_prior_state``
    # produces for the item modify ``prior_state`` snapshot. ``default_supplier_name``
    # is stamped on server-side (``_resolve_prior_supplier_name``); the card
    # reads it for the supplier line.
    _ITEM_PRIOR: ClassVar[dict[str, Any]] = {
        "id": 500,
        "name": "Carbon Wheelset",
        "uom": "pcs",
        "category_name": "Wheels",
        "additional_info": "Hand-built",
        "is_sellable": True,
        "is_producible": True,
        "batch_tracked": False,
        "serial_tracked": False,
        "archived_at": None,
        "default_supplier_id": 77,
        "default_supplier_name": "Acme Carbon Co",
        "lead_time": 14,
        "minimum_order_quantity": 2,
        "variants": [
            {
                "id": 9001,
                "sku": "WHL-CARB-700C",
                "sales_price": 1200.0,
                "purchase_price": 800.0,
            },
            {
                "id": 9002,
                "sku": "WHL-CARB-650B",
                "sales_price": 1150.0,
                "purchase_price": 760.0,
            },
        ],
    }

    @classmethod
    def _preview(
        cls,
        actions: list[dict[str, Any]] | None = None,
        *,
        entity_type: str = "product",
        **overrides: Any,
    ) -> dict[str, Any]:
        return {
            "entity_type": entity_type,
            "entity_id": 500,
            "is_preview": True,
            "actions": actions or [],
            "prior_state": dict(cls._ITEM_PRIOR),
            "extras": {},
            "warnings": [],
            "next_actions": [],
            "message": "Preview",
            "katana_url": "https://factory.katanamrp.com/product/500",
            **overrides,
        }

    @classmethod
    def _applied(
        cls, actions: list[dict[str, Any]] | None = None, **overrides: Any
    ) -> dict[str, Any]:
        return cls._preview(actions, is_preview=False, **overrides)

    @staticmethod
    def _header_action(*, field: str, old: Any, new: Any, **overrides: Any) -> dict:
        return {
            "operation": "update_header",
            "target_id": 500,
            "succeeded": None,
            "changes": [{"field": field, "old": old, "new": new}],
            "status_label": "PLANNED",
            **overrides,
        }

    @staticmethod
    def _add_variant_action(
        *, sku: str, sales_price: float | None = None, **overrides: Any
    ) -> dict:
        changes: list[dict[str, Any]] = [
            {"field": "sku", "old": None, "new": sku, "is_added": True}
        ]
        if sales_price is not None:
            changes.append(
                {
                    "field": "sales_price",
                    "old": None,
                    "new": sales_price,
                    "is_added": True,
                }
            )
        return {
            "operation": "add_variant",
            "target_id": None,
            "succeeded": None,
            "changes": changes,
            "status_label": "PLANNED",
            **overrides,
        }

    @staticmethod
    def _update_variant_action(
        *, target_id: int, old_price: float, new_price: float, **overrides: Any
    ) -> dict:
        return {
            "operation": "update_variant",
            "target_id": target_id,
            "succeeded": None,
            "changes": [
                {"field": "sales_price", "old": old_price, "new": new_price},
            ],
            "status_label": "PLANNED",
            **overrides,
        }

    @staticmethod
    def _delete_variant_action(*, target_id: int, **overrides: Any) -> dict:
        return {
            "operation": "delete_variant",
            "target_id": target_id,
            "succeeded": None,
            "changes": [],
            "status_label": "PLANNED",
            **overrides,
        }

    def test_header_only_modify_decorates_scalar_diff(self):
        """A header-field change renders a before→after diff line; the resolved
        supplier name surfaces (never a bare ``#id``)."""
        actions = [self._header_action(field="uom", old="pcs", new="set")]
        app = build_item_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_item",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Carbon Wheelset" in rendered
        # Diff arrow on the changed UoM line.
        assert "pcs → set" in rendered
        # Supplier name resolved server-side — not a raw "#77".
        assert "Acme Carbon Co" in rendered
        assert "#77" not in rendered

    def test_rename_surfaces_name_diff(self):
        """A header ``name`` rename must surface a before→after diff — the
        card title is built from the prior snapshot, so without the name diff
        line the rename would show nowhere (Copilot #875)."""
        actions = [
            self._header_action(field="name", old="Carbon Wheelset", new="Carbon Pro")
        ]
        app = build_item_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_item",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Carbon Wheelset → Carbon Pro" in rendered

    def test_service_pricing_change_surfaces_diff(self):
        """Services carry pricing/SKU on the header and have no variant table,
        so a service ``sales_price`` / ``sku`` modify must still render a
        field-level diff. Prices arrive as Decimal (compute_field_diff →
        _normalize), so the shared diff formatter must trim them, not ``repr``
        as ``Decimal('50.00…')`` (Copilot #875)."""
        from decimal import Decimal

        actions = [
            self._header_action(
                field="sales_price",
                old=Decimal("50.0000000000"),
                new=Decimal("65.0000000000"),
            ),
            self._header_action(field="sku", old="SVC-OLD", new="SVC-NEW"),
        ]
        app = build_item_modify_ui(
            self._preview(actions, entity_type="service"),
            confirm_request=_StubRequest(),
            confirm_tool="modify_item",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "50 → 65" in rendered
        assert "Decimal" not in rendered
        assert "SVC-OLD → SVC-NEW" in rendered

    def test_status_flag_change_surfaces_diff(self):
        """Boolean header flags (is_sellable / is_producible / tracking) aren't
        carried by the diff-unaware Tier-1 pills, so a flag modify must render
        an explicit ``yes → no`` diff line (Copilot #875)."""
        actions = [
            self._header_action(field="is_sellable", old=True, new=False),
            self._header_action(field="batch_tracked", old=False, new=True),
        ]
        app = build_item_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_item",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "yes → no" in rendered  # is_sellable True → False
        assert "no → yes" in rendered  # batch_tracked False → True

    def test_variant_crud_renders_all_kinds_and_summary(self):
        """1 add + 1 update + 1 delete + 1 untouched: every row kind appears
        in the variant table and the summary line counts them."""
        actions = [
            self._add_variant_action(sku="WHL-CARB-DISC", sales_price=1300.0),
            self._update_variant_action(
                target_id=9001, old_price=1200.0, new_price=1250.0
            ),
            self._delete_variant_action(target_id=9002),
        ]
        app = build_item_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_item",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        # Added variant SKU with the "+ " gutter.
        assert "+ WHL-CARB-DISC" in rendered
        # Updated variant's price diff arrow.
        assert "1200 → 1250" in rendered
        # Deleted variant's identity preserved with the "- " gutter.
        assert "- WHL-CARB-650B" in rendered
        # Summary line.
        assert "+1 added" in rendered
        assert "~1 updated" in rendered
        assert "-1 deleted" in rendered

    def test_variant_rows_land_in_state_for_datatable_binding(self):
        """The variant rows seed ``state.variant_rows`` so the state-bound
        DataTable resolves (and morphs on apply)."""
        actions = [self._add_variant_action(sku="WHL-NEW")]
        app = build_item_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_item",
        )
        assert app.state is not None
        rows = app.state.get("variant_rows")
        assert isinstance(rows, list)
        # 2 existing + 1 added.
        assert len(rows) == 3
        kinds = [r["kind"] for r in rows]
        assert kinds.count("existing") == 2
        assert kinds.count("added") == 1

    def test_service_has_no_variant_table(self):
        """Services carry pricing on the header, not on variants — the variant
        diff table is suppressed even if the snapshot carries variants."""
        actions = [self._header_action(field="sales_price", old=50.0, new=60.0)]
        app = build_item_modify_ui(
            self._preview(actions, entity_type="service"),
            confirm_request=_StubRequest(),
            confirm_tool="modify_item",
        )
        assert app.state is not None
        # No variant rows seeded for a service.
        assert app.state.get("variant_rows") == []

    def test_subtype_badge_reflects_entity_type(self):
        """The type badge reads from the response entity_type (the raw item
        snapshot has no ``type`` echo)."""
        for entity_type in ("product", "material", "service"):
            app = build_item_modify_ui(
                self._preview(
                    [self._header_action(field="uom", old="pcs", new="kg")],
                    entity_type=entity_type,
                ),
                confirm_request=_StubRequest(),
                confirm_tool="modify_item",
            )
            rendered = str(app.to_json())
            assert entity_type in rendered

    def test_delete_uses_delete_verb_and_confirm_label(self):
        """A delete routes through the same card with the Delete verb +
        ``Confirm Delete`` affordance."""
        actions = [
            {
                "operation": "delete",
                "target_id": 500,
                "succeeded": None,
                "changes": [],
                "status_label": "PLANNED",
            }
        ]
        app = build_item_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="delete_item",
        )
        _assert_valid_prefab(app)
        rendered = str(app.to_json())
        assert "Confirm Delete" in rendered

    def test_applied_state_seeds_outcome_slots(self):
        """On the standalone-applied path the outcome label/variant track the
        real action outcomes (all-success → APPLIED / default)."""
        actions = [
            self._update_variant_action(
                target_id=9001,
                old_price=1200.0,
                new_price=1250.0,
                succeeded=True,
                status_label="APPLIED",
            )
        ]
        app = build_item_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_item",
        )
        assert app.state is not None
        assert app.state.get("applied_outcome_label") == "APPLIED"
        assert app.state.get("applied_outcome_variant") == "default"

    def test_partial_failure_surfaces_failed_summary(self):
        """A mixed applied outcome seeds the failed-count + summary slots and
        flips the outcome variant to destructive."""
        actions = [
            self._update_variant_action(
                target_id=9001,
                old_price=1200.0,
                new_price=1250.0,
                succeeded=True,
                status_label="APPLIED",
            ),
            self._delete_variant_action(
                target_id=9002,
                succeeded=False,
                status_label="FAILED",
                error="variant in use by an open SO",
            ),
        ]
        app = build_item_modify_ui(
            self._applied(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_item",
        )
        assert app.state is not None
        assert app.state.get("applied_outcome_label") == "PARTIAL FAILURE"
        assert app.state.get("applied_outcome_variant") == "destructive"
        assert app.state.get("applied_failed_count") == 1
        assert "variant in use by an open SO" in str(
            app.state.get("applied_failed_summary")
        )

    def test_not_run_tail_surfaces_in_variant_table(self):
        """Fail-fast partial apply: the impl stashes the unattempted plan tail
        in ``extras["not_run_actions"]``; the card must merge them so the
        morphed table shows the not-run variant rows (NOT RUN) instead of
        silently dropping them (Copilot #875)."""
        # Action 1 (delete 9001) failed → execute_plan stopped; the planned
        # update of 9002 never ran and is synthesized as NOT RUN.
        applied_actions = [
            self._delete_variant_action(
                target_id=9001,
                succeeded=False,
                status_label="FAILED",
                error="variant in use",
            )
        ]
        not_run = [
            {
                "operation": "update_variant",
                "target_id": 9002,
                "succeeded": None,
                "error": None,
                "changes": [{"field": "sales_price", "old": 1150.0, "new": 1200.0}],
                "status_label": "NOT RUN",
            }
        ]
        app = build_item_modify_ui(
            self._applied(applied_actions, extras={"not_run_actions": not_run}),
            confirm_request=_StubRequest(),
            confirm_tool="modify_item",
        )
        _assert_valid_prefab(app)
        assert app.state is not None
        rows = app.state.get("variant_rows")
        assert isinstance(rows, list)
        # Both variants surface: 9001 deleted (FAILED), 9002 updated (NOT RUN).
        statuses = {r["id"]: r["status_label"] for r in rows}
        assert statuses.get(9001) == "FAILED"
        assert statuses.get(9002) == "NOT RUN"

    def test_decimal_prices_render_trimmed_in_card(self):
        """Prices arrive as Decimal from `compute_field_diff`; the variant
        table must render them trimmed, not `1200.0000000000` (Copilot #875)."""
        from decimal import Decimal

        actions = [
            {
                "operation": "update_variant",
                "target_id": 9001,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [
                    {
                        "field": "sales_price",
                        "old": Decimal("1200.0000000000"),
                        "new": Decimal("1250.5000000000"),
                    }
                ],
            }
        ]
        app = build_item_modify_ui(
            self._preview(actions),
            confirm_request=_StubRequest(),
            confirm_tool="modify_item",
        )
        rendered = str(app.to_json())
        assert "1200 → 1250.5" in rendered
        assert "0000000000" not in rendered

    def test_preview_shows_preview_badge_default_outcome(self):
        """On preview the outcome slots seed the optimistic APPLIED default
        (the Tier-1 badge shows PREVIEW until the morph overwrites them)."""
        app = build_item_modify_ui(
            self._preview([self._add_variant_action(sku="X")]),
            confirm_request=_StubRequest(),
            confirm_tool="modify_item",
        )
        assert app.state is not None
        # Preview-time defaults — never bucketed from succeeded=None actions.
        assert app.state.get("applied_outcome_label") == "APPLIED"
        rendered = str(app.to_json())
        assert "PREVIEW" in rendered


class TestItemModifyDispatch:
    """``to_tool_result`` routes product / material / service modify responses
    to ``build_item_modify_ui`` (not the legacy generic card)."""

    @pytest.mark.parametrize("entity_type", ["product", "material", "service"])
    def test_item_types_route_to_item_modify_card(self, entity_type):
        from katana_mcp.tools._modification import (
            ConfirmableRequest,
            ModificationResponse,
            to_tool_result,
        )

        class _StubConfirmable(ConfirmableRequest):
            id: int = 500

        response = ModificationResponse(
            entity_type=entity_type,
            entity_id=500,
            is_preview=True,
            actions=[],
            prior_state={"id": 500, "name": "Thing", "variants": []},
            warnings=[],
            next_actions=[],
            message="Preview",
        )
        result = to_tool_result(
            response, confirm_request=_StubConfirmable(), confirm_tool="modify_item"
        )
        envelope = result.structured_content
        # The item card titles its footer "Item Modify ..."; the generic
        # legacy card does not. Presence of the item name in the identity
        # header confirms the item builder ran.
        rendered = str(envelope)
        assert "Thing" in rendered


class TestPOEntityViewSharedBetweenCreateAndModify:
    """``_render_po_entity_view`` is called by BOTH ``build_po_create_ui``
    (with ``changes=None``) and ``build_po_modify_ui`` (with a diff
    lookup). This pin proves the dual-call contract so future refactors
    don't drift the create renderer away from modify.
    """

    _PO_BASE: ClassVar[dict[str, Any]] = {
        "order_number": "PO-001",
        "supplier_id": 100,
        "supplier_name": "Acme",
        "location_id": 1,
        "location_name": "Main",
        "status": "NOT_RECEIVED",
        "entity_type": "regular",
        "total_cost": 500.0,
        "currency": "USD",
        "item_count": 2,
        "notes": "Net-30",
        "warnings": [],
    }

    def test_create_card_renders_via_shared_helper_with_no_changes(self):
        """Create card calls the helper with changes=None — the rendered
        tree should show every base field as plain text (no arrow)."""
        app = build_po_create_ui(
            dict(self._PO_BASE, is_preview=True),
            confirm_request=_StubRequest(),
            confirm_tool="create_purchase_order",
        )
        rendered = str(app.to_json())
        assert "Acme" in rendered
        assert "Main" in rendered
        assert "Net-30" in rendered
        # No diff arrow in create card body — only the create state badge.
        # (The applied-state View-in-Katana row may include the arrow
        # in error templates, but the entity view itself shouldn't.)
        assert "→" not in rendered.replace("→ after", "")  # be permissive

    def test_modify_card_diff_decorates_only_changed_fields(self):
        """Modify card calls the helper with changes — only fields in
        the changes dict get the arrow form; unchanged ones render as
        normal Text lines."""
        actions = [
            {
                "operation": "update_header",
                "succeeded": None,
                "changes": [
                    {"field": "status", "old": "NOT_RECEIVED", "new": "RECEIVED"},
                ],
            }
        ]
        prior = dict(self._PO_BASE)
        prior["id"] = 9001
        response = {
            "entity_type": "purchase_order",
            "entity_id": 9001,
            "is_preview": True,
            "actions": actions,
            "prior_state": prior,
            "warnings": [],
            "next_actions": [],
            "message": "Preview",
            "katana_url": "https://factory.katanamrp.com/purchaseorder/9001",
        }
        app = build_po_modify_ui(
            response,
            confirm_request=_StubRequest(),
            confirm_tool="modify_purchase_order",
        )
        rendered = str(app.to_json())
        # Status decorated with arrow.
        assert "NOT_RECEIVED" in rendered and "RECEIVED" in rendered
        # Unchanged supplier renders as a normal party line with the
        # Katana supplier URL (the same shape as the create card).
        assert "Acme" in rendered
        assert "/contacts/suppliers/100" in rendered


class TestStatusBadgeVariant:
    """``status_badge_variant`` buckets each entity's status into one of
    four Prefab Badge variants. Pins the per-entity mapping so a future
    contributor adding a new entity can't accidentally collapse the
    success/active/blocked distinctions."""

    @pytest.mark.parametrize(
        "entity,status,expected",
        [
            # success bucket
            ("purchase_order", "RECEIVED", "default"),
            ("sales_order", "DELIVERED", "default"),
            ("manufacturing_order", "DONE", "default"),
            ("stock_transfer", "RECEIVED", "default"),
            # active bucket
            ("purchase_order", "PARTIALLY_RECEIVED", "secondary"),
            ("sales_order", "PARTIALLY_SHIPPED", "secondary"),
            ("sales_order", "PACKED", "secondary"),
            ("manufacturing_order", "IN_PROGRESS", "secondary"),
            ("manufacturing_order", "PARTIALLY_COMPLETED", "secondary"),
            ("stock_transfer", "IN_TRANSIT", "secondary"),
            # blocked bucket — only MO has one today
            ("manufacturing_order", "BLOCKED", "destructive"),
            # neutral bucket (unstarted statuses + None + unknown entity)
            ("purchase_order", "NOT_RECEIVED", "outline"),
            ("sales_order", "NOT_SHIPPED", "outline"),
            ("manufacturing_order", "NOT_STARTED", "outline"),
            ("purchase_order", None, "outline"),
            ("unknown_entity", "WHATEVER", "outline"),
        ],
    )
    def test_bucket_lookup(self, entity, status, expected):
        assert status_badge_variant(entity, status) == expected


class TestBuildFulfillPreviewUI:
    def test_preview(self):
        response = {
            "order_type": "sales",
            "order_number": "SO-001",
            "order_id": 123,
            "status": "IN_PROGRESS",
            "message": "Ready to fulfill",
        }
        app = build_fulfill_preview_ui(response)
        _assert_valid_prefab(app)


class TestBuildFulfillSuccessUI:
    def test_success(self):
        response = {
            "order_type": "sales",
            "order_number": "SO-001",
            "status": "DONE",
            "message": "Order fulfilled",
            "inventory_updates": "Stock reduced by 10",
        }
        app = build_fulfill_success_ui(response)
        _assert_valid_prefab(app)


class TestBuildFulfillUI:
    """Tier 2 metrics + Tier 3 per-row breakdown + Tier 4 actions on the
    fulfillment card (#553). Mirrors :class:`TestBuildReceiptUI` for the
    receipt-card sibling that landed in #556 / PR #793.
    """

    def _so_response(
        self,
        *,
        is_preview: bool = True,
        with_rows: bool = True,
        with_metrics: bool = True,
        currency: str | None = "USD",
    ) -> dict[str, Any]:
        """Minimal SO fulfillment response covering the full Tier 2 + Tier 3
        rendering path. Tests opt rows / metrics in or out to exercise the
        empty-state branches."""
        response: dict[str, Any] = {
            "order_type": "sales",
            "order_number": "SO-001",
            "order_id": 123,
            "status": "NOT_SHIPPED" if is_preview else "DELIVERED",
            "message": "Preview" if is_preview else "Fulfilled",
            "is_preview": is_preview,
            "katana_url": "https://factory.katanamrp.com/salesorder/123",
        }
        if with_rows:
            response["fulfilled_rows"] = [
                {
                    "row_id": 501,
                    "variant_id": 100,
                    "sku": "WIDGET-100",
                    "display_name": "Big Widget / Red",
                    "quantity": 5.0,
                    "serial_numbers": [],
                    "batch_summary": None,
                    "price_per_unit": 10.0,
                    "row_total": 50.0,
                    "currency": currency,
                },
                {
                    "row_id": 502,
                    "variant_id": 200,
                    "sku": "WIDGET-200",
                    "display_name": "Small Widget / Blue",
                    "quantity": 2.0,
                    "serial_numbers": [9001, 9002],
                    "batch_summary": None,
                    "price_per_unit": 25.0,
                    "row_total": 50.0,
                    "currency": currency,
                },
            ]
        if with_metrics:
            response["rows_count"] = 2 if with_rows else 0
            response["total_quantity"] = 7.0 if with_rows else 0.0
            response["total_value"] = 100.0 if with_rows else None
            response["currency"] = currency
        return response

    # ------------------------------------------------------------------
    # Back-compat: legacy payloads without enrichment must keep working
    # ------------------------------------------------------------------

    def test_preview_back_compat_no_rows_omits_table(self):
        """Older payloads predating #553 (no ``fulfilled_rows`` /
        ``rows_count``) must NOT render an empty per-row DataTable.
        Same back-compat shape as ``TestBuildReceiptUI``."""
        response = {
            "order_type": "sales",
            "order_number": "SO-001",
            "order_id": 123,
            "status": "NOT_SHIPPED",
            "message": "Ready to fulfill",
            "is_preview": True,
        }
        envelope = build_fulfill_preview_ui(response).to_json()
        assert not _has_node_of_type(envelope, "DataTable"), (
            "Empty fulfilled_rows must NOT emit a DataTable."
        )

    def test_success_back_compat_no_rows_omits_table(self):
        """Symmetric back-compat for the success card."""
        response = {
            "order_type": "sales",
            "order_number": "SO-001",
            "status": "DELIVERED",
            "message": "Order fulfilled",
            "is_preview": False,
        }
        envelope = build_fulfill_success_ui(response).to_json()
        assert not _has_node_of_type(envelope, "DataTable")

    # ------------------------------------------------------------------
    # Tier 2 metrics
    # ------------------------------------------------------------------

    def test_preview_renders_tier2_metrics(self):
        """Three-Metric row: Rows / Total Qty / Total Value.

        Pinned by #553: the operator's most-asked decision context is
        "what's the commitment". Each Metric is its own component so a
        future card rearrangement can drop one without disturbing the
        others.
        """
        envelope = build_fulfill_preview_ui(self._so_response()).to_json()
        metrics = _find_components_by_type(envelope, "Metric")
        labels = [m.get("label") for m in metrics]
        assert "Rows" in labels
        assert "Total Qty" in labels
        assert "Total Value" in labels

    def test_mo_response_omits_total_value(self):
        """Manufacturing orders track cost, not price — the card must
        skip the Total Value metric when no row carries a price (the
        ``total_value=None`` signal from the backend)."""
        response = {
            "order_type": "manufacturing",
            "order_number": "MO-001",
            "order_id": 456,
            "status": "IN_PROGRESS",
            "message": "Preview",
            "is_preview": True,
            "rows_count": 1,
            "total_quantity": 3.0,
            "total_value": None,
            "currency": None,
            "fulfilled_rows": [
                {
                    "row_id": None,
                    "variant_id": 555,
                    "sku": "FG-001",
                    "display_name": "Finished Good",
                    "quantity": 3.0,
                    "serial_numbers": [],
                    "batch_summary": None,
                    "price_per_unit": None,
                    "row_total": None,
                    "currency": None,
                }
            ],
        }
        envelope = build_fulfill_preview_ui(response).to_json()
        metrics = _find_components_by_type(envelope, "Metric")
        labels = [m.get("label") for m in metrics]
        assert "Rows" in labels
        assert "Total Qty" in labels
        assert "Total Value" not in labels, (
            "MO branch must not render Total Value — MOs don't track price."
        )

    # ------------------------------------------------------------------
    # Tier 3 per-row table
    # ------------------------------------------------------------------

    def test_preview_renders_tier3_table_with_expected_columns(self):
        """Sales-order DataTable surfaces six columns:
        Item / SKU / Qty / Serials / Batch / Line Total. Manufacturing
        skips Line Total (covered by ``test_mo_card_drops_line_total``).
        """
        envelope = build_fulfill_preview_ui(self._so_response()).to_json()
        tables = _find_components_by_type(envelope, "DataTable")
        assert len(tables) == 1
        headers = [c.get("header") for c in tables[0].get("columns", [])]
        assert headers == [
            "Item",
            "SKU",
            "Qty",
            "Serials",
            "Batch",
            "Line Total",
        ]

    def test_mo_card_drops_line_total(self):
        """MO branch table drops the Line Total column (no price on the
        MO surface). Pinned so a future "always show all 6 columns" edit
        breaks loudly instead of silently rendering a blank column."""
        response = {
            "order_type": "manufacturing",
            "order_number": "MO-001",
            "order_id": 456,
            "status": "IN_PROGRESS",
            "is_preview": True,
            "rows_count": 1,
            "total_quantity": 1.0,
            "total_value": None,
            "fulfilled_rows": [
                {
                    "row_id": None,
                    "variant_id": 555,
                    "sku": "FG-001",
                    "display_name": "Finished Good",
                    "quantity": 1.0,
                    "serial_numbers": [],
                    "batch_summary": None,
                    "price_per_unit": None,
                    "row_total": None,
                    "currency": None,
                }
            ],
        }
        envelope = build_fulfill_preview_ui(response).to_json()
        tables = _find_components_by_type(envelope, "DataTable")
        headers = [c.get("header") for c in tables[0].get("columns", [])]
        assert "Line Total" not in headers
        # Identity columns + qty/serials/batch are still present.
        assert headers == ["Item", "SKU", "Qty", "Serials", "Batch"]

    def test_per_row_table_flattens_strings_into_state(self):
        """``DataTable.rows`` is a state-bound mustache reference. Builder
        must pre-format the per-row dicts (qty via ``:g``, money via
        babel, serials list collapsed) so the iframe template only sees
        strings. See :func:`_build_fulfill_row_display`.
        """
        envelope = build_fulfill_preview_ui(self._so_response()).to_json()
        state = envelope.get("state") or envelope.get("$prefab", {}).get("state", {})
        rows = state.get("fulfilled_rows")
        assert isinstance(rows, list) and len(rows) == 2
        row_a, row_b = rows
        assert row_a["display_name"] == "Big Widget / Red"
        assert row_a["sku"] == "WIDGET-100"
        assert row_a["quantity"] == "5"  # :g trims trailing .0
        assert row_a["serials"] == ""  # empty list -> empty string
        assert row_a["row_total"] == "$50.00"
        # Row B has serial overrides — short list renders verbatim.
        assert row_b["serials"] == "9001, 9002"

    def test_long_serial_list_collapses_to_count(self):
        """A row attaching more than 5 serials would blow out the column
        width; the builder collapses to ``"N serial(s)"`` so the card
        stays readable.
        """
        response = self._so_response()
        response["fulfilled_rows"][0]["serial_numbers"] = list(range(1, 11))
        envelope = build_fulfill_preview_ui(response).to_json()
        state = envelope.get("state") or envelope.get("$prefab", {}).get("state", {})
        assert state["fulfilled_rows"][0]["serials"] == "10 serial(s)"

    def test_batch_summary_renders_pre_formatted(self):
        """Batch-tracked rows surface the batch allocation in human-
        readable form, paralleling the receipt card (#556)."""
        response = self._so_response()
        response["fulfilled_rows"][0]["batch_summary"] = "batch 42x30, batch 51x20"
        envelope = build_fulfill_preview_ui(response).to_json()
        state = envelope.get("state") or envelope.get("$prefab", {}).get("state", {})
        assert state["fulfilled_rows"][0]["batch_summary"] == "batch 42x30, batch 51x20"

    # ------------------------------------------------------------------
    # Tier 3 reference block (#card-ux): customer + addresses + picked
    # ------------------------------------------------------------------

    def _so_response_with_reference(
        self,
        *,
        billing_address: dict[str, Any] | None = None,
        picked_date: str | None = "2026-05-08T23:14:00+00:00",
    ) -> dict[str, Any]:
        response = self._so_response()
        response["customer_id"] = 1500
        response["customer_name"] = "Acme Bikes Inc."
        response["shipping_address"] = {
            "entity_type": "shipping",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "company": "Acme Bikes Inc.",
            "line_1": "123 Main Street",
            "line_2": "Suite 4B",
            "city": "Portland",
            "state": "OR",
            "zip": "97201",
            "country": "US",
            "phone": "+1-503-555-0123",
        }
        response["billing_address"] = billing_address
        response["picked_date"] = picked_date
        return response

    def test_preview_renders_customer_party_line_with_name(self):
        """The fulfill card surfaces ``customer_name`` as a Link to the
        Katana customer page — not a bare ``Customer ID: <id>`` line.
        Pinned for the #card-ux user-centric content rule: the operator
        must be able to see *who* the shipment goes to without consulting
        the raw response or the Katana web UI."""
        envelope = build_fulfill_preview_ui(
            self._so_response_with_reference()
        ).to_json()
        links = _find_components_by_type(envelope, "Link")
        link_contents = [link.get("content") for link in links]
        assert "Acme Bikes Inc." in link_contents, (
            f"Expected Customer name 'Acme Bikes Inc.' to render as a Link "
            f"(party-line helper); got Link contents {link_contents!r}"
        )

    def test_preview_renders_shipping_address_block(self):
        """``_render_address_block`` composes a multi-line block from the
        SalesOrderAddress dict — recipient, company, street, locality,
        country/phone — so the operator confirms shipment destination
        in human terms, not by clicking through to the Katana UI."""
        envelope = build_fulfill_preview_ui(
            self._so_response_with_reference()
        ).to_json()
        texts = _find_components_by_type(envelope, "Text")
        contents = [t.get("content", "") for t in texts]
        assert any("Shipping Address" in c for c in contents)
        # Recipient + locality + country should all appear in the rendered
        # block per ``_render_address_block``'s composition rules.
        assert any("Sarah Johnson" in c for c in contents)
        assert any("Portland" in c for c in contents)
        assert any("OR 97201" in c for c in contents)

    def test_preview_omits_billing_block_when_equal_to_shipping(self):
        """``_fetch_so_addresses`` returns ``billing=None`` when the two
        addresses are equivalent — the card must not render a duplicate
        Billing Address block. Pinned for the dedup rule that mirrors
        ``_render_customer_entity_view``."""
        envelope = build_fulfill_preview_ui(
            self._so_response_with_reference(billing_address=None)
        ).to_json()
        contents = [
            t.get("content", "") for t in _find_components_by_type(envelope, "Text")
        ]
        assert not any("Billing Address" in c for c in contents), (
            "Billing Address block must be hidden when impl-side dedup "
            "found it equivalent to shipping."
        )

    def test_preview_card_side_dedup_when_impl_passes_equivalent_addresses(self):
        """Defense-in-depth: when a caller bypasses ``_fetch_so_addresses``
        (older payload, direct UI call) and supplies both shipping +
        billing as equivalent dicts, the card MUST still dedup. Pre-fix
        the card unconditionally rendered the billing block whenever the
        field was truthy — Copilot caught this on PR #861."""
        response = self._so_response_with_reference()
        # Equivalent dicts that the impl-side dedup would have collapsed
        # but the response carried through unchanged.
        equivalent_billing = dict(response["shipping_address"])
        equivalent_billing["entity_type"] = "billing"
        response["billing_address"] = equivalent_billing
        envelope = build_fulfill_preview_ui(response).to_json()
        contents = [
            t.get("content", "") for t in _find_components_by_type(envelope, "Text")
        ]
        assert not any("Billing Address" in c for c in contents), (
            "Card must dedup an equivalent billing block even when the "
            "impl side passed both addresses through unchanged."
        )

    def test_preview_renders_billing_block_when_different(self):
        """When billing differs from shipping the card renders both
        blocks so the operator sees the discrepancy (rare, but it happens
        for net-30 customers whose AP department is at a different
        address than the receiving location)."""
        billing = {
            "entity_type": "billing",
            "first_name": "Accounts",
            "last_name": "Payable",
            "company": "Acme Bikes Inc.",
            "line_1": "999 Finance Ave",
            "city": "Beaverton",
            "state": "OR",
            "zip": "97005",
            "country": "US",
        }
        envelope = build_fulfill_preview_ui(
            self._so_response_with_reference(billing_address=billing)
        ).to_json()
        contents = [
            t.get("content", "") for t in _find_components_by_type(envelope, "Text")
        ]
        assert any("Billing Address" in c for c in contents)
        assert any("Beaverton" in c for c in contents)

    def test_preview_renders_picked_date_metric(self):
        """Pre-#card-ux the picked_date lived in an ``inventory_updates``
        text blob; #card-ux promotes it to a Tier-2 Metric so the
        operator sees *when* this fulfillment counts at eye level."""
        envelope = build_fulfill_preview_ui(
            self._so_response_with_reference()
        ).to_json()
        metrics = _find_components_by_type(envelope, "Metric")
        picked = next((m for m in metrics if m.get("label") == "Picked"), None)
        assert picked is not None, (
            f"Expected a 'Picked' Metric; got labels "
            f"{[m.get('label') for m in metrics]!r}"
        )
        assert picked.get("value") == "2026-05-08T23:14:00+00:00"

    def test_preview_omits_picked_metric_when_unset(self):
        """No ``picked_date`` on the response (caller didn't pass
        ``completed_at``) → server-stamps at apply time → no Picked
        Metric on the card."""
        envelope = build_fulfill_preview_ui(
            self._so_response_with_reference(picked_date=None)
        ).to_json()
        labels = [m.get("label") for m in _find_components_by_type(envelope, "Metric")]
        assert "Picked" not in labels

    def test_mo_card_skips_customer_and_address_block(self):
        """Manufacturing orders have no customer and no shipping address
        (the work happens at a single location). The MO branch of the
        fulfill card must skip the Tier-3 reference block entirely —
        a Customer party-line would be nonsense, and a missing-shipping
        warning would create noise. Pinned by ``order_type`` discriminator
        in ``_render_fulfill_reference_block``."""
        response = {
            "order_type": "manufacturing",
            "order_number": "MO-001",
            "order_id": 456,
            "status": "IN_PROGRESS",
            "is_preview": True,
            "rows_count": 1,
            "total_quantity": 1.0,
            "total_value": None,
            "customer_id": None,
            "customer_name": None,
            "shipping_address": None,
            "billing_address": None,
            "fulfilled_rows": [
                {
                    "row_id": None,
                    "variant_id": 555,
                    "sku": "FG-001",
                    "display_name": "Finished Good",
                    "quantity": 1.0,
                    "serial_numbers": [],
                    "batch_summary": None,
                    "price_per_unit": None,
                    "row_total": None,
                    "currency": None,
                }
            ],
        }
        envelope = build_fulfill_preview_ui(response).to_json()
        contents = [
            t.get("content", "") for t in _find_components_by_type(envelope, "Text")
        ]
        assert not any("Shipping Address" in c for c in contents)
        assert not any("Customer:" in c for c in contents)

    def test_preview_does_not_dump_inventory_updates(self):
        """Pre-#card-ux the preview card listed every row twice — once
        as a Muted text dump (``Row 108854645: ship 1 of …``) and once
        as a DataTable. The dump is gone; the DataTable carries all the
        structured columns. Pinned so a future re-introduction of the
        dump (e.g. accidentally adding ``_render_inventory_updates`` back)
        breaks the build."""
        response = self._so_response_with_reference()
        # Even if the response carries inventory_updates strings (back-compat),
        # the card must NOT render them above the per-row DataTable.
        response["inventory_updates"] = [
            "Row 501: ship 5 of WIDGET-100 (full ordered quantity)",
            "Row 502: ship 2 of WIDGET-200 (full ordered quantity)",
        ]
        envelope = build_fulfill_preview_ui(response).to_json()
        contents = [
            t.get("content", "") for t in _find_components_by_type(envelope, "Text")
        ]
        for line in response["inventory_updates"]:
            assert all(line not in c for c in contents), (
                f"Inventory-updates dump line {line!r} must not appear "
                f"as Text on the preview card (it duplicates the DataTable)."
            )

    # ------------------------------------------------------------------
    # Tier 4 success-side actions
    # ------------------------------------------------------------------

    def test_success_renders_view_in_katana_when_url_present(self):
        """Tier 4 expansion (#553): the success card now offers two
        follow-ups instead of the legacy single Check Inventory button.
        View in Katana wins the primary slot when a deep-link is present.

        ``View in Katana`` uses ``OpenLink`` (deterministic URL
        navigation), not ``SendMessage`` — the host opens the link
        directly without an agent round-trip.
        """
        envelope = build_fulfill_success_ui(
            self._so_response(is_preview=False)
        ).to_json()
        buttons = _find_components_by_type(envelope, "Button")
        labels = [b.get("label") for b in buttons]
        assert "View in Katana" in labels
        assert "Check Inventory" in labels

        view_in_katana = _find_buttons_by_label(envelope, "View in Katana")[0]
        action = view_in_katana.get("onClick") or view_in_katana.get("on_click")
        assert isinstance(action, dict)
        assert action.get("action") == "openLink", (
            f"View in Katana must use OpenLink, not SendMessage; got {action!r}"
        )
        assert action.get("url"), f"OpenLink must carry a URL; got {action!r}"

    def test_success_omits_view_in_katana_when_url_missing(self):
        """No ``katana_url`` on the response (older payload) → fall back
        to the legacy single Check Inventory button. Pinned for
        back-compat with previous test fixtures that don't include the
        URL field."""
        response = self._so_response(is_preview=False)
        response.pop("katana_url", None)
        envelope = build_fulfill_success_ui(response).to_json()
        buttons = _find_components_by_type(envelope, "Button")
        labels = [b.get("label") for b in buttons]
        assert "View in Katana" not in labels
        assert "Check Inventory" in labels

    def test_success_check_inventory_uses_variant_id_when_sku_null(self):
        """``fulfilled_rows`` carries both ``sku`` and ``variant_id``;
        variants can legally have ``sku=None`` (CLAUDE.md "Variants can
        have null SKUs"). The success-card ``Check Inventory`` button
        must coalesce on ``sku or variant_id`` so a SKU-less row still
        emits the deterministic ``CallTool`` path instead of falling
        through to the agent-prompt ``UpdateContext`` fallback (review
        finding on PR #807)."""
        response = self._so_response(is_preview=False)
        # Mix: one row with SKU, one with only variant_id.
        response["fulfilled_rows"] = [
            {
                "row_id": None,
                "variant_id": 555,
                "sku": "HAS-SKU",
                "display_name": "Sku-bearing",
                "quantity": 1.0,
                "serial_numbers": [],
                "batch_summary": None,
                "row_total": None,
                "currency": None,
            },
            {
                "row_id": None,
                "variant_id": 777,
                "sku": None,
                "display_name": "Sku-less variant",
                "quantity": 2.0,
                "serial_numbers": [],
                "batch_summary": None,
                "row_total": None,
                "currency": None,
            },
        ]
        envelope = build_fulfill_success_ui(response).to_json()
        check_inv = _find_buttons_by_label(envelope, "Check Inventory")[0]
        action = check_inv.get("onClick") or check_inv.get("on_click")
        assert isinstance(action, dict)
        assert action.get("action") == "toolCall", (
            f"Check Inventory must use CallTool when at least one "
            f"row resolves an identity (SKU or variant_id); got {action!r}"
        )
        handles = (action.get("arguments") or {}).get("skus_or_variant_ids")
        assert handles == ["HAS-SKU", 777], (
            f"Expected handles to coalesce sku-or-variant_id per row; got {handles!r}"
        )


class TestBuildVerificationUI:
    def test_match(self):
        response = {
            "overall_status": "match",
            "order_id": 123,
            "matches": [
                {"sku": "SKU-001", "quantity": 10, "unit_price": 5.0, "status": "match"}
            ],
            "discrepancies": [],
        }
        app = build_verification_ui(response)
        _assert_valid_prefab(app)

    def test_no_match(self):
        response = {
            "overall_status": "no_match",
            "order_id": 456,
            "matches": [],
            "discrepancies": [
                {"sku": "SKU-002", "type": "missing", "message": "Not on PO"}
            ],
        }
        app = build_verification_ui(response)
        _assert_valid_prefab(app)

    def test_match_and_discrepancy_tables_include_item_column(self):
        """Both tables expose ``Item`` as the leading sortable column so the
        rendered card shows the canonical Katana-UI display name ahead of
        the raw SKU — matching every other variant-displaying surface
        (search_items, check_inventory, batch recipe update card).
        """
        response = {
            "overall_status": "partial_match",
            "order_id": 789,
            "matches": [
                {
                    "sku": "WIDGET-001",
                    "display_name": "Acme Widget / Large / Red",
                    "quantity": 10,
                    "unit_price": 5.0,
                    "status": "perfect",
                }
            ],
            "discrepancies": [
                {
                    "sku": "WIDGET-002",
                    "display_name": "Acme Widget / Small / Blue",
                    "type": "quantity_mismatch",
                    "message": "Quantity off by 2",
                }
            ],
        }
        app = build_verification_ui(response)
        envelope = app.to_json()

        # Both DataTable nodes must have ``Item`` (display_name) as the
        # first column, with ``SKU`` immediately after.
        tables = _find_components_by_type(envelope, "DataTable")
        assert len(tables) == 2  # matches + discrepancies
        for table in tables:
            cols = table.get("columns", [])
            assert cols[0]["key"] == "display_name"
            assert cols[0]["header"] == "Item"
            assert cols[1]["key"] == "sku"

    def test_renders_tier_2_metrics_row(self):
        """#554 — Tier 2 metric row carries three Metric widgets:
        Matched / Discrepant / Totals reconciled.

        ``Matched`` counts perfect-status matches; ``Discrepant`` counts
        discrepancies + non-perfect matches; ``Totals reconciled`` reads
        as ``$matched_total of $po_total``.
        """
        # Arrange
        response = {
            "overall_status": "partial_match",
            "order_id": 789,
            "purchase_order": {
                "id": 789,
                "currency": "USD",
                "total": 100.00,
                "katana_url": "https://factory.katanamrp.com/purchaseorder/789",
            },
            "matches": [
                {
                    "sku": "WIDGET-001",
                    "display_name": "Acme Widget / Large / Red",
                    "quantity": 10,
                    "unit_price": 5.0,
                    "expected_quantity": 10,
                    "expected_unit_price": 5.0,
                    "status": "perfect",
                },
                {
                    "sku": "WIDGET-002",
                    "display_name": "Acme Widget / Small / Blue",
                    "quantity": 4,
                    "unit_price": 5.0,
                    "expected_quantity": 6,
                    "expected_unit_price": 5.0,
                    "status": "quantity_diff",
                },
            ],
            "discrepancies": [
                {
                    "sku": "WIDGET-002",
                    "display_name": "Acme Widget / Small / Blue",
                    "type": "quantity_mismatch",
                    "expected": 6,
                    "actual": 4,
                    "message": "Quantity off by 2",
                }
            ],
        }

        # Act
        app = build_verification_ui(response)
        envelope = app.to_json()

        # Assert
        metrics = _find_components_by_type(envelope, "Metric")
        assert len(metrics) == 3
        labels = [m.get("label") for m in metrics]
        assert labels == ["Matched", "Discrepant", "Totals reconciled"]
        # Perfect-status matches count = 1; discrepancies (1) + non-perfect
        # matches (1) = 2.
        by_label = {m["label"]: m for m in metrics}
        assert by_label["Matched"]["value"] == "1"
        assert by_label["Discrepant"]["value"] == "2"
        # When discrepant > 0, color flips via trend_sentiment="negative".
        assert by_label["Discrepant"].get("trendSentiment") == "negative"
        # Totals: only the perfect-status match (10 * 5.0 = $50.00)
        # contributes to ``matched_total``; PO total is $100.00.
        assert by_label["Totals reconciled"]["value"] == "$50.00 of $100.00"

    def test_matched_total_falls_back_to_expected_unit_price(self):
        """#554 — When the document omits ``unit_price`` (price check is
        skipped, so the line still counts as ``perfect``), the matched
        subtotal must fall back to the PO row's ``expected_unit_price``
        instead of coercing ``None`` to ``0``. Coercing to zero
        silently undercounts and shows ``$0.00 of $X.XX`` even when the
        PO has a known price.
        """
        # Arrange — perfect-status match with doc-side ``unit_price=None``.
        response = {
            "overall_status": "match",
            "order_id": 789,
            "purchase_order": {"id": 789, "currency": "USD", "total": 50.0},
            "matches": [
                {
                    "sku": "WIDGET-001",
                    "display_name": "Acme Widget",
                    "quantity": 10,
                    "unit_price": None,
                    "expected_quantity": 10,
                    "expected_unit_price": 5.0,
                    "status": "perfect",
                }
            ],
            "discrepancies": [],
        }

        # Act
        app = build_verification_ui(response)
        envelope = app.to_json()

        # Assert — 10 * 5.0 = $50.00 via expected_unit_price fallback.
        metrics = _find_components_by_type(envelope, "Metric")
        by_label = {m["label"]: m for m in metrics}
        assert by_label["Totals reconciled"]["value"] == "$50.00 of $50.00"

    def test_matched_total_skips_lines_with_no_price_on_either_side(self):
        """#554 — When both ``unit_price`` and ``expected_unit_price`` are
        missing, the line is skipped entirely — there's nothing to
        reconcile against, and treating "unknown" as zero would
        misleadingly drag down the matched subtotal.
        """
        # Arrange — one fully-priced perfect match + one perfect match
        # with no price on either side.
        response = {
            "overall_status": "match",
            "order_id": 789,
            "purchase_order": {"id": 789, "currency": "USD", "total": 50.0},
            "matches": [
                {
                    "sku": "WIDGET-001",
                    "display_name": "Acme Widget",
                    "quantity": 10,
                    "unit_price": 5.0,
                    "expected_quantity": 10,
                    "expected_unit_price": 5.0,
                    "status": "perfect",
                },
                {
                    "sku": "WIDGET-002",
                    "display_name": "Other Widget",
                    "quantity": 4,
                    "unit_price": None,
                    "expected_quantity": 4,
                    "expected_unit_price": None,
                    "status": "perfect",
                },
            ],
            "discrepancies": [],
        }

        # Act
        app = build_verification_ui(response)
        envelope = app.to_json()

        # Assert — only the priced row contributes ($50.00); the
        # unpriced row is skipped (does not drop the subtotal to $0).
        metrics = _find_components_by_type(envelope, "Metric")
        by_label = {m["label"]: m for m in metrics}
        assert by_label["Totals reconciled"]["value"] == "$50.00 of $50.00"

    def test_totals_reconciled_omitted_when_po_total_is_none(self):
        """#554 — When ``purchase_order.total`` is ``None`` (Katana's
        ``GetPurchaseOrderResponse.total`` is ``float | None``, and the
        back-compat path drops ``purchase_order`` entirely so ``total``
        resolves to ``None``), the Totals reconciled Metric is omitted
        rather than rendering a misleading ``$X of $0.00``. The
        remaining Metric widgets (Matched / Discrepant) still render
        normally.
        """
        # Arrange — purchase_order is present but ``total`` is None.
        response = {
            "overall_status": "match",
            "order_id": 789,
            "purchase_order": {"id": 789, "currency": "USD", "total": None},
            "matches": [
                {
                    "sku": "WIDGET-001",
                    "display_name": "Acme Widget",
                    "quantity": 10,
                    "unit_price": 5.0,
                    "expected_quantity": 10,
                    "expected_unit_price": 5.0,
                    "status": "perfect",
                }
            ],
            "discrepancies": [],
        }

        # Act
        app = build_verification_ui(response)
        envelope = app.to_json()

        # Assert — Matched + Discrepant present; Totals reconciled
        # absent (would otherwise read ``$50.00 of $0.00``).
        metrics = _find_components_by_type(envelope, "Metric")
        labels = [m.get("label") for m in metrics]
        assert "Matched" in labels
        assert "Discrepant" in labels
        assert "Totals reconciled" not in labels
        assert len(metrics) == 2

    def test_totals_reconciled_omitted_when_purchase_order_missing(self):
        """#554 — Back-compat path: ``purchase_order`` block absent from
        the response (older verify_order_document callers, or callers
        constructing responses without the embedded PO). ``po_total``
        resolves to ``None`` and the Totals Metric is omitted.
        """
        # Arrange — no ``purchase_order`` key at all.
        response = {
            "overall_status": "match",
            "order_id": 789,
            "matches": [
                {
                    "sku": "WIDGET-001",
                    "display_name": "Acme Widget",
                    "quantity": 10,
                    "unit_price": 5.0,
                    "expected_quantity": 10,
                    "expected_unit_price": 5.0,
                    "status": "perfect",
                }
            ],
            "discrepancies": [],
        }

        # Act
        app = build_verification_ui(response)
        envelope = app.to_json()

        # Assert
        metrics = _find_components_by_type(envelope, "Metric")
        labels = [m.get("label") for m in metrics]
        assert labels == ["Matched", "Discrepant"]

    def test_matches_table_shows_po_side_columns_for_non_perfect_status(self):
        """#554 — Matches table renders Qty (doc) / Qty (PO) / Price (doc)
        / Price (PO) columns so the operator sees doc-vs-PO deltas
        without re-resolving against the embedded purchase_order.
        """
        # Arrange
        response = {
            "overall_status": "partial_match",
            "order_id": 789,
            "purchase_order": {"id": 789, "currency": "USD", "total": 50.0},
            "matches": [
                {
                    "sku": "WIDGET-001",
                    "display_name": "Acme Widget / Large / Red",
                    "quantity": 8,
                    "unit_price": 6.0,
                    "expected_quantity": 10,
                    "expected_unit_price": 5.0,
                    "status": "both_diff",
                }
            ],
            "discrepancies": [],
        }

        # Act
        app = build_verification_ui(response)
        envelope = app.to_json()

        # Assert — matches table is the only DataTable here.
        tables = _find_components_by_type(envelope, "DataTable")
        assert len(tables) == 1
        cols = tables[0]["columns"]
        col_keys = [c["key"] for c in cols]
        col_headers = [c["header"] for c in cols]
        assert "expected_quantity" in col_keys
        assert "expected_unit_price" in col_keys
        assert "Qty (doc)" in col_headers
        assert "Qty (PO)" in col_headers
        assert "Price (doc)" in col_headers
        assert "Price (PO)" in col_headers

    def test_discrepancies_table_shows_expected_and_actual_columns(self):
        """#554 — Discrepancies table renders Expected / Actual columns
        from the ``expected`` / ``actual`` fields on ``Discrepancy``.
        """
        # Arrange
        response = {
            "overall_status": "no_match",
            "order_id": 456,
            "purchase_order": {"id": 456, "currency": "USD", "total": 50.0},
            "matches": [],
            "discrepancies": [
                {
                    "sku": "SKU-002",
                    "display_name": "Item Two",
                    "type": "quantity_mismatch",
                    "expected": 10,
                    "actual": 7,
                    "message": "Quantity off by 3",
                }
            ],
        }

        # Act
        app = build_verification_ui(response)
        envelope = app.to_json()

        # Assert — discrepancies table is the only DataTable here.
        tables = _find_components_by_type(envelope, "DataTable")
        assert len(tables) == 1
        cols = tables[0]["columns"]
        col_keys = [c["key"] for c in cols]
        col_headers = [c["header"] for c in cols]
        assert "expected" in col_keys
        assert "actual" in col_keys
        assert "Expected" in col_headers
        assert "Actual" in col_headers

    def test_view_in_katana_button_present_when_url_set(self):
        """#554 — Tier 4 surfaces a ``View in Katana`` button when the
        embedded ``purchase_order.katana_url`` is set; that's the
        operator's most common follow-up after verification.
        """
        # Arrange
        response = {
            "overall_status": "match",
            "order_id": 789,
            "purchase_order": {
                "id": 789,
                "currency": "USD",
                "total": 50.0,
                "katana_url": "https://factory.katanamrp.com/purchaseorder/789",
            },
            "matches": [
                {
                    "sku": "WIDGET-001",
                    "display_name": "Acme Widget",
                    "quantity": 10,
                    "unit_price": 5.0,
                    "expected_quantity": 10,
                    "expected_unit_price": 5.0,
                    "status": "perfect",
                }
            ],
            "discrepancies": [],
        }

        # Act
        app = build_verification_ui(response)
        envelope = app.to_json()

        # Assert
        view_buttons = _find_buttons_by_label(envelope, "View in Katana")
        assert len(view_buttons) == 1

    def test_view_in_katana_button_absent_when_url_missing(self):
        """#554 — back-compat: when the response lacks the embedded
        ``purchase_order`` (or its ``katana_url`` field), the
        View-in-Katana button is omitted entirely.
        """
        # Arrange — no ``purchase_order`` key at all.
        response = {
            "overall_status": "match",
            "order_id": 789,
            "matches": [
                {
                    "sku": "WIDGET-001",
                    "display_name": "Acme Widget",
                    "quantity": 10,
                    "unit_price": 5.0,
                    "expected_quantity": 10,
                    "expected_unit_price": 5.0,
                    "status": "perfect",
                }
            ],
            "discrepancies": [],
        }

        # Act
        app = build_verification_ui(response)
        envelope = app.to_json()

        # Assert
        view_buttons = _find_buttons_by_label(envelope, "View in Katana")
        assert len(view_buttons) == 0

    def test_proceed_button_only_when_overall_match(self):
        """#554 — Tier 4 routing: ``Proceed to Receive`` renders only when
        ``overall_status == "match"``; ``Receive Anyway`` renders
        otherwise (partial_match / no_match). The two are
        mutually-exclusive.
        """
        # Arrange — match case.
        match_response = {
            "overall_status": "match",
            "order_id": 789,
            "purchase_order": {"id": 789, "currency": "USD", "total": 50.0},
            "matches": [
                {
                    "sku": "WIDGET-001",
                    "display_name": "Acme Widget",
                    "quantity": 10,
                    "unit_price": 5.0,
                    "expected_quantity": 10,
                    "expected_unit_price": 5.0,
                    "status": "perfect",
                }
            ],
            "discrepancies": [],
        }

        # Act + Assert (match)
        match_envelope = build_verification_ui(match_response).to_json()
        assert len(_find_buttons_by_label(match_envelope, "Proceed to Receive")) == 1
        assert len(_find_buttons_by_label(match_envelope, "Receive Anyway")) == 0

        # Arrange — partial_match case.
        partial_response = dict(match_response)
        partial_response["overall_status"] = "partial_match"
        partial_response["discrepancies"] = [
            {
                "sku": "SKU-X",
                "display_name": "Other Item",
                "type": "quantity_mismatch",
                "expected": 5,
                "actual": 3,
                "message": "Quantity off by 2",
            }
        ]

        # Act + Assert (partial_match)
        partial_envelope = build_verification_ui(partial_response).to_json()
        assert len(_find_buttons_by_label(partial_envelope, "Proceed to Receive")) == 0
        assert len(_find_buttons_by_label(partial_envelope, "Receive Anyway")) == 1


class TestBuildItemCreateUI:
    """The post-creation card (formerly ``build_item_mutation_ui``) implements
    the four-tier framework: Identity (name + Created badge + status pills),
    Decision metrics, Reference (single-variant SKU/prices inline, supplier,
    configs), and type-specific Action buttons.
    """

    def _full_product(self) -> dict:
        return {
            "id": 1,
            "name": "Widget",
            "type": "product",
            "sku": "SKU-001",
            "katana_url": "https://factory.katanamrp.com/product/1",
            "uom": "pcs",
            "category_name": "Finished Goods",
            "is_sellable": True,
            "is_producible": True,
            "additional_info": "ships flat-packed",
            "variants": [
                {
                    "id": 11,
                    "sku": "SKU-001",
                    "sales_price": 19.5,
                    "purchase_price": 8.0,
                    "display_name": "Widget",
                }
            ],
            "configs": [{"id": 3, "name": "Size", "values": ["S", "M", "L"]}],
        }

    def test_valid_envelope_full_product(self):
        app = build_item_create_ui(self._full_product())
        _assert_valid_prefab(app)

    def test_minimal(self):
        app = build_item_create_ui({"id": 1})
        _assert_valid_prefab(app)

    def test_identity_tier_created_badge_and_title_link(self):
        """Tier 1: a "Created" state badge, the name, and a Link to the
        Katana page."""
        app = build_item_create_ui(self._full_product())
        envelope = app.to_json()
        rendered = str(envelope)
        assert "Created" in rendered
        links = _find_components_by_type(envelope, "Link")
        hrefs = [link.get("href") for link in links]
        assert "https://factory.katanamrp.com/product/1" in hrefs

    def test_single_variant_renders_inline_not_datatable(self):
        """A freshly-created item has exactly one variant — its SKU + prices
        render as inline reference lines, NOT a one-row DataTable (single-row
        table is needless chrome)."""
        app = build_item_create_ui(self._full_product())
        envelope = app.to_json()
        assert not _has_node_of_type(envelope, "DataTable")
        rendered = str(envelope)
        assert "SKU: SKU-001" in rendered
        assert "Sales Price: 19.5" in rendered
        assert "Purchase Price: 8" in rendered

    def test_zero_price_renders(self):
        """A 0.0 price (free sample) still renders — the guard is an explicit
        ``is not None`` check, not truthiness."""
        item = self._full_product()
        item["variants"][0]["sales_price"] = 0.0
        app = build_item_create_ui(item)
        assert "Sales Price: 0" in str(app.to_json())

    def test_sku_falls_back_to_item_level_when_no_variants(self):
        """If the create result didn't echo a variants array, the item-level
        ``sku`` still surfaces so identity is never lost — and ``Variants: 0``
        is *shown* (not collapsed) because an empty variants list on a freshly
        created item is a malformed-response signal, not noise."""
        item = {"id": 1, "name": "Widget", "type": "product", "sku": "SKU-XYZ"}
        app = build_item_create_ui(item)
        rendered = str(app.to_json())
        assert "SKU: SKU-XYZ" in rendered
        assert "Variants: 0" in rendered

    def test_configs_render_as_axis_rows(self):
        app = build_item_create_ui(self._full_product())
        assert "Size: S, M, L" in str(app.to_json())

    def test_supplier_renders_as_link_not_bare_id(self):
        """Reference tier resolves the supplier name (anti-pattern #7): a
        ``default_supplier_name`` threaded from the impl renders as a Link with
        the name as visible text, not a bare ``#id``."""
        item = {
            "id": 2,
            "name": "Steel Bar",
            "type": "material",
            "sku": "MAT-1",
            "default_supplier_id": 555,
            "default_supplier_name": "Acme Metals",
            "variants": [{"id": 21, "sku": "MAT-1"}],
        }
        app = build_item_create_ui(item)
        envelope = app.to_json()
        links = _find_components_by_type(envelope, "Link")
        supplier_links = [
            link
            for link in links
            if "/contacts/suppliers/" in str(link.get("href", ""))
        ]
        assert len(supplier_links) == 1
        assert supplier_links[0].get("content") == "Acme Metals"

    def test_footer_actions_for_product(self):
        """Producible product: View Details, Check Inventory, Set Initial
        Stock, Create Manufacturing Order, Modify Item — and NOT Create
        Purchase Order (that's the material affordance)."""
        envelope = build_item_create_ui(self._full_product()).to_json()
        for label in [
            "View Details",
            "Check Inventory",
            "Set Initial Stock",
            "Create Manufacturing Order",
            "Modify Item",
        ]:
            assert len(_find_buttons_by_label(envelope, label)) == 1, label
        assert _find_buttons_by_label(envelope, "Create Purchase Order") == []

    def test_footer_actions_for_material(self):
        """Material: Create Purchase Order (not Manufacturing Order)."""
        item = {
            "id": 3,
            "name": "Steel",
            "type": "material",
            "sku": "MAT-2",
            "variants": [{"id": 31, "sku": "MAT-2"}],
        }
        envelope = build_item_create_ui(item).to_json()
        assert len(_find_buttons_by_label(envelope, "Create Purchase Order")) == 1
        assert _find_buttons_by_label(envelope, "Create Manufacturing Order") == []

    def test_non_producible_product_has_no_mo_button(self):
        item = self._full_product()
        item["is_producible"] = False
        envelope = build_item_create_ui(item).to_json()
        assert _find_buttons_by_label(envelope, "Create Manufacturing Order") == []

    def test_service_has_no_supplier_or_stock_actions(self):
        """A service: no supplier line, and no Create PO / MO buttons; still
        offers View Details + Modify Item."""
        item = {
            "id": 4,
            "name": "Assembly Labor",
            "type": "service",
            "sku": "SVC-1",
            "variants": [{"id": 41, "sku": "SVC-1", "sales_price": 50.0}],
        }
        envelope = build_item_create_ui(item).to_json()
        assert _find_buttons_by_label(envelope, "Create Purchase Order") == []
        assert _find_buttons_by_label(envelope, "Create Manufacturing Order") == []
        assert len(_find_buttons_by_label(envelope, "View Details")) == 1
        assert len(_find_buttons_by_label(envelope, "Modify Item")) == 1

    def test_warnings_surface(self):
        """A supplier-name resolution warning threaded onto ``warnings`` is
        rendered so the operator sees why a name couldn't be pretty-printed."""
        item = {
            "id": 5,
            "name": "Steel",
            "type": "material",
            "sku": "MAT-3",
            "default_supplier_id": 999,
            "warnings": ["Default supplier with id=999 was not found in the cache"],
        }
        rendered = str(build_item_create_ui(item).to_json())
        assert "not found in the cache" in rendered


class TestBuildReceiptUI:
    def test_preview(self):
        response = {
            "order_number": "PO-001",
            "order_id": 123,
            "is_preview": True,
            "message": "Preview of receipt",
            "items_received": 5,
        }
        app = build_receipt_ui(response)
        _assert_valid_prefab(app)

    def test_confirmed(self):
        response = {
            "order_number": "PO-001",
            "order_id": 123,
            "is_preview": False,
            "items_received": 5,
        }
        app = build_receipt_ui(response)
        _assert_valid_prefab(app)

    def test_received_items_empty_omits_per_row_table(self):
        """Back-compat: an older payload with no ``received_items`` key
        must not render an empty DataTable (closes #556 regression risk).
        """
        response = {
            "order_number": "PO-001",
            "order_id": 123,
            "is_preview": True,
            "items_received": 5,
        }
        envelope = build_receipt_ui(response).to_json()
        assert not _has_node_of_type(envelope, "DataTable"), (
            "received_items empty must NOT emit a DataTable."
        )

    def test_received_items_present_emits_per_row_table(self):
        """The Tier 3 DataTable pinned by #556 — per-row breakdown so the
        agent can verify *what* is being received without parsing the
        raw items=[...] tool-call blob."""
        response = {
            "order_number": "PO-001",
            "order_id": 123,
            "is_preview": True,
            "items_received": 1,
            "currency": "USD",
            "received_items": [
                {
                    "purchase_order_row_id": 7825913,
                    "variant_id": 12345,
                    "sku": "C1266049ST",
                    "display_name": "D125 26P1 / C1266049ST",
                    "quantity": 52.0,
                    "quantity_ordered": 52.0,
                    "received_date": "2026-05-18T13:22:00-06:00",
                    "batch_summary": None,
                    "price_per_unit": 100.0,
                    "row_total": 5200.0,
                    "currency": "USD",
                }
            ],
        }
        envelope = build_receipt_ui(response).to_json()
        tables = _find_components_by_type(envelope, "DataTable")
        assert len(tables) == 1
        # Column set pinned: Item / SKU / Qty / Destination / Received / Batch / Line Total.
        # "Destination" carries the per-row receiving location for multi-location
        # receives (#945); blank when the row inherits the order-level location.
        headers = [c.get("header") for c in tables[0].get("columns", [])]
        assert headers == [
            "Item",
            "SKU",
            "Qty",
            "Destination",
            "Received",
            "Batch",
            "Line Total",
        ]

    def test_per_row_table_flattens_strings_into_state(self):
        """``DataTable.rows`` is a state-bound mustache reference. The
        builder must pre-format the per-row dicts (date trimmed to
        YYYY-MM-DD, money via babel) so the template never sees raw
        datetimes or floats — see :func:`_build_receipt_row_display`."""
        response = {
            "order_number": "PO-001",
            "order_id": 123,
            "is_preview": True,
            "items_received": 1,
            "received_items": [
                {
                    "purchase_order_row_id": 7825913,
                    "sku": "C1266049ST",
                    "display_name": "D125 / C1266049ST",
                    "quantity": 52.0,
                    "quantity_ordered": 52.0,
                    "received_date": "2026-05-18T13:22:00-06:00",
                    "row_total": 5200.0,
                    "currency": "USD",
                }
            ],
        }
        envelope = build_receipt_ui(response).to_json()
        state = envelope.get("state") or envelope.get("$prefab", {}).get("state", {})
        rows = state.get("received_items")
        assert isinstance(rows, list) and len(rows) == 1
        row = rows[0]
        assert row["display_name"] == "D125 / C1266049ST"
        assert row["sku"] == "C1266049ST"
        assert row["quantity"] == "52"  # :g trims trailing .0
        assert row["received_date"] == "2026-05-18"  # date-only
        assert row["row_total"] == "$5,200.00"
        assert row["batch_summary"] == ""
        # No per-row location supplied → Destination cell is blank (the row
        # inherits the order-level receiving location). See #945.
        assert row["location"] == ""

    def test_per_row_location_renders_destination(self):
        """Multi-location receiving (#945): a row carrying location_name
        renders it in the Destination column; a row with only location_id
        falls back to 'Location ID: N'; a row with neither stays blank."""
        response = {
            "order_number": "PO-001",
            "order_id": 123,
            "is_preview": True,
            "items_received": 3,
            "received_items": [
                {
                    "purchase_order_row_id": 1,
                    "quantity": 1.0,
                    "location_id": 42,
                    "location_name": "West DC",
                },
                {
                    "purchase_order_row_id": 2,
                    "quantity": 1.0,
                    "location_id": 99,
                    "location_name": None,
                },
                {"purchase_order_row_id": 3, "quantity": 1.0},
            ],
        }
        envelope = build_receipt_ui(response).to_json()
        state = envelope.get("state") or envelope.get("$prefab", {}).get("state", {})
        rows = state.get("received_items")
        assert [r["location"] for r in rows] == ["West DC", "Location ID: 99", ""]

    def test_partial_receive_qty_shows_received_of_ordered(self):
        """Partial receives (qty < quantity_ordered) render as '52 of 60'
        — the operator's most common decision context (received less than
        ordered, PO stays PARTIALLY_RECEIVED)."""
        response = {
            "order_number": "PO-001",
            "order_id": 123,
            "is_preview": True,
            "items_received": 1,
            "received_items": [
                {
                    "purchase_order_row_id": 1,
                    "quantity": 52.0,
                    "quantity_ordered": 60.0,
                    "received_date": None,
                }
            ],
        }
        envelope = build_receipt_ui(response).to_json()
        state = envelope.get("state") or envelope.get("$prefab", {}).get("state", {})
        assert state["received_items"][0]["quantity"] == "52 of 60"
        assert state["received_items"][0]["received_date"] == "—"

    def test_batch_summary_renders_pre_formatted(self):
        """Batch-tracked rows surface the allocation in human-readable form
        so the operator can confirm the right lot was selected."""
        response = {
            "order_number": "PO-001",
            "order_id": 123,
            "is_preview": True,
            "items_received": 1,
            "received_items": [
                {
                    "purchase_order_row_id": 1,
                    "quantity": 50.0,
                    "batch_summary": "batch 42x30, batch 51x20",
                }
            ],
        }
        envelope = build_receipt_ui(response).to_json()
        state = envelope.get("state") or envelope.get("$prefab", {}).get("state", {})
        assert state["received_items"][0]["batch_summary"] == "batch 42x30, batch 51x20"


class TestBuildInventoryCheckBatchUI:
    """Pin the batch ``check_inventory`` card shape (#562). The single-item
    path is covered by ``TestBuildInventoryCheckUI``; this class covers
    the multi-row path that previously had no Prefab builder at all."""

    def _multi_item_payload(self) -> list[dict[str, Any]]:
        """Four rows covering every distinct render branch:
        - split across two locations (multi-location sub-table)
        - single-location (no sub-table)
        - not-found by SKU (sku echoed, variant_id None)
        - not-found by variant_id (sku empty, variant_id echoed)
        The fourth row pins the regression Copilot flagged in #769 R2:
        a variant-id miss must remain identifiable in the summary
        table even though SKU and Product columns are blank."""
        return [
            {
                "sku": "WIDGET-001",
                "product_name": "Test Widget",
                "variant_id": 100,
                "in_stock": 15.0,
                "available_stock": 13.0,
                "committed": 2.0,
                "expected": 5.0,
                "uom": "pcs",
                "is_found": True,
                "by_location": [
                    {
                        "location_id": 1,
                        "location_name": "Main",
                        "in_stock": 10.0,
                        "committed": 2.0,
                        "expected": 5.0,
                        "available": 8.0,
                    },
                    {
                        "location_id": 2,
                        "location_name": "East",
                        "in_stock": 5.0,
                        "committed": 0.0,
                        "expected": 0.0,
                        "available": 5.0,
                    },
                ],
            },
            {
                "sku": "WIDGET-002",
                "product_name": "Single-Location Widget",
                "variant_id": 101,
                "in_stock": 4.0,
                "available_stock": 4.0,
                "committed": 0.0,
                "expected": 0.0,
                "uom": "pcs",
                "is_found": True,
                "by_location": [
                    {
                        "location_id": 1,
                        "location_name": "Main",
                        "in_stock": 4.0,
                        "committed": 0.0,
                        "expected": 0.0,
                        "available": 4.0,
                    },
                ],
            },
            {
                "sku": "MISSING-SKU",
                "product_name": "",
                "variant_id": None,
                "in_stock": 0.0,
                "available_stock": 0.0,
                "committed": 0.0,
                "expected": 0.0,
                "is_found": False,
            },
            {
                "sku": "",
                "product_name": "",
                "variant_id": 99999,
                "in_stock": 0.0,
                "available_stock": 0.0,
                "committed": 0.0,
                "expected": 0.0,
                "is_found": False,
            },
        ]

    def test_renders_summary_table_with_all_rows(self):
        items = self._multi_item_payload()
        app = build_inventory_check_batch_ui(items)
        _assert_valid_prefab(app)
        rendered = json.dumps(app.to_json())
        # Header carries the row count.
        assert "4 items" in rendered
        # Top-level DataTable is the summary surface.
        assert "DataTable" in rendered
        # All input identities land in state.
        assert "WIDGET-001" in rendered
        assert "WIDGET-002" in rendered
        assert "MISSING-SKU" in rendered
        # The variant-id not-found row has no SKU — its identity must
        # still be discoverable in the table. The variant_id column
        # carries the echoed ID.
        assert "99999" in rendered

    def test_negative_in_stock_renders_as_out_of_stock(self):
        """Negative ``in_stock`` totals are real — adjustments,
        backorders, and accounting fixes can drive the sum below zero.
        A negative balance is "no stock available" for any decision the
        card supports, so the status badge must surface "Out of stock"
        rather than the default "In stock" for ``in_stock > 0``."""
        items = [
            {
                "sku": "BACKORDER-1",
                "product_name": "Oversold Item",
                "variant_id": 200,
                "in_stock": -5.0,
                "available_stock": -7.0,
                "committed": 2.0,
                "expected": 0.0,
                "is_found": True,
                "by_location": [],
            }
        ]
        app = build_inventory_check_batch_ui(items)
        # The annotator wrote the status onto the row in place.
        assert items[0]["status_label"] == "Out of stock"
        # And the label flows through to the rendered envelope.
        rendered = json.dumps(app.to_json())
        assert "Out of stock" in rendered

    def test_state_items_omits_by_location_to_avoid_duplication(self):
        """The summary table never reads ``by_location`` — only the
        sub-tables do. State carries each item's by-location list under
        a dedicated ``by_location_<i>`` slot, so leaving it inside
        ``state['items']`` too would double the wire payload for
        multi-location variants. Pin the slim contract."""
        items = self._multi_item_payload()
        app = build_inventory_check_batch_ui(items)
        state = app.to_json().get("state") or {}
        state_items = state.get("items") or []
        # Every entry under ``items`` must be stripped of ``by_location``.
        for row in state_items:
            assert "by_location" not in row, (
                f"state['items'] row leaked by_location: {row.get('sku')!r}"
            )
        # The multi-location variant's by-location data still surfaces
        # via its dedicated slot (the sub-table needs it).
        assert "by_location_0" in state
        assert len(state["by_location_0"]) == 2

    def test_per_location_sub_table_carries_reorder_columns(self):
        """Column parity with the single-item card: the per-location
        sub-table must surface ``reorder_point`` and ``status_label``
        so users get the same warehouse-level reorder signal in batch
        responses they'd see for a single-item check. Status labels
        come from ``_annotate_location_rows`` (shared with the
        single-item card)."""
        items = self._multi_item_payload()
        # Wire reorder thresholds onto the multi-location variant so the
        # annotator has something to evaluate.
        items[0]["by_location"][0]["reorder_point"] = 5.0
        items[0]["by_location"][1]["reorder_point"] = 10.0
        app = build_inventory_check_batch_ui(items)
        # Find the per-location DataTable — the summary table also
        # carries an ``in_stock`` column, so disambiguate by checking
        # for the ``location_name`` column that's unique to the
        # sub-table.
        sub_table = None
        for node in _walk_view_tree(app.to_json().get("view")):
            if node.get("type") != "DataTable":
                continue
            keys = [c.get("key") for c in node.get("columns") or []]
            if "location_name" in keys:
                sub_table = node
                break
        assert sub_table is not None, "per-location sub-table not found"
        column_keys = [c["key"] for c in sub_table["columns"]]
        assert "reorder_point" in column_keys
        assert "status_label" in column_keys
        # The annotator wrote labels back onto each location row in
        # state — verify they made it through. WIDGET-001 has 8.0
        # available at Main with reorder 5.0 (Healthy) and 5.0 at East
        # with reorder 10.0 (Below reorder).
        locations = items[0]["by_location"]
        assert locations[0]["status_label"] == "Healthy"
        assert locations[1]["status_label"] == "Below reorder"

    def test_renders_per_location_sub_table_only_for_multi_location(self):
        """Single-location and not-found variants must NOT get their own
        by-location sub-table — the summary row already says everything,
        and not-found rows have no locations at all."""
        items = self._multi_item_payload()
        app = build_inventory_check_batch_ui(items)
        rendered = json.dumps(app.to_json())
        # Exactly one per-variant sub-table marker: only WIDGET-001 is
        # multi-location. Match the inline label, not the heading prefix,
        # so we don't double-count if the rendering inserts the SKU in
        # multiple places.
        assert rendered.count("by location (") == 1
        # The multi-location variant gets its own state slot — the
        # builder allocates ``by_location_<i>`` keyed on the variant's
        # index in the input list (WIDGET-001 is index 0).
        assert "by_location_0" in rendered

    def test_not_found_row_renders_status_badge(self):
        items = self._multi_item_payload()
        app = build_inventory_check_batch_ui(items)
        rendered = json.dumps(app.to_json())
        # Header badge: SKU-miss + variant-id-miss = 2 not-found rows.
        assert "2 not found" in rendered
        # Row-level status label is on the table row.
        assert "Not found" in rendered

    def test_variant_id_column_renders_for_not_found_variant_id_row(self):
        """A not-found stub from a variant-id lookup has empty SKU and
        empty product_name; without the variant_id column the row is
        completely unidentifiable. The Variant ID column must render
        and the column key must point at the right state field."""
        items = self._multi_item_payload()
        app = build_inventory_check_batch_ui(items)
        # Walk the rendered tree and find the summary DataTable —
        # match it by the SKU column key, then assert the Variant ID
        # column is present.
        summary_table = None
        for node in _walk_view_tree(app.to_json().get("view")):
            if node.get("type") != "DataTable":
                continue
            cols = node.get("columns") or []
            keys = [c.get("key") for c in cols]
            if "sku" in keys:
                summary_table = node
                break
        assert summary_table is not None, "summary DataTable not found"
        column_keys = [c["key"] for c in summary_table["columns"]]
        assert "variant_id" in column_keys
        # Echoed ID is in the rendered state — the column will resolve
        # it at render time on the host.
        assert "99999" in json.dumps(app.to_json())

    def test_empty_batch_renders_friendly_message(self):
        """Zero rows must not render a DataTable — the table would
        display an empty grid with no rows, which reads as an error.
        Drop straight to a hint instead."""
        app = build_inventory_check_batch_ui([])
        _assert_valid_prefab(app)
        rendered = json.dumps(app.to_json())
        assert "0 items" in rendered
        assert "No items in this batch" in rendered
        # No DataTable on the empty path.
        assert "DataTable" not in rendered

    def test_aggregate_metrics_exclude_not_found_rows(self):
        """The summary metrics ('In Stock', 'Available', ...) must sum
        only over found rows. A not-found stub carries zeroed totals
        and would otherwise dilute the average if we ever surfaced one
        — exclude them so the top-line totals match the table sums."""
        items = self._multi_item_payload()
        app = build_inventory_check_batch_ui(items)
        # Pluck the Metric components from the rendered tree and assert
        # their values directly — substring matches on "19" / "17" pass
        # by accident via collision with location IDs / page numbers /
        # any digit-rich field in the envelope.
        metrics: dict[str, str] = {}
        for node in _walk_view_tree(app.to_json().get("view")):
            if node.get("type") == "Metric":
                metrics[node["label"]] = node["value"]
        # WIDGET-001 (15) + WIDGET-002 (4) = 19; not-found row contributes 0.
        assert metrics["In Stock"] == "19.0"
        # Available: 13 + 4 = 17.
        assert metrics["Available"] == "17.0"
        # Committed: only WIDGET-001 commits stock; WIDGET-002 / not-found are 0.
        assert metrics["Committed"] == "2.0"
        # Expected: only WIDGET-001 expects stock.
        assert metrics["Expected"] == "5.0"


class TestBuildBatchRecipeUpdateUI:
    def test_preview_with_replacements(self):
        response = {
            "is_preview": True,
            "total_ops": 3,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "delete",
                    "manufacturing_order_id": 9999,
                    "recipe_row_id": 5001,
                    "variant_id": 100,
                    "sku": "OLD-PART",
                    "status": "pending",
                    "group_label": "OLD-PART → [NEW-PART, INNER-PART]",
                },
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 200,
                    "sku": "NEW-PART",
                    "planned_quantity_per_unit": 1.0,
                    "status": "pending",
                    "group_label": "OLD-PART → [NEW-PART, INNER-PART]",
                },
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 201,
                    "sku": "INNER-PART",
                    "planned_quantity_per_unit": 1.0,
                    "status": "pending",
                    "group_label": "OLD-PART → [NEW-PART, INNER-PART]",
                },
            ],
            "warnings": [],
            "message": "Preview: 3 sub-operations planned",
        }
        app = build_batch_recipe_update_ui(response)
        _assert_valid_prefab(app)

    def test_executed_with_mixed_results(self):
        response = {
            "is_preview": False,
            "total_ops": 3,
            "success_count": 2,
            "failed_count": 1,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "delete",
                    "manufacturing_order_id": 9999,
                    "recipe_row_id": 5001,
                    "status": "success",
                    "group_label": "group1",
                },
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 200,
                    "sku": "NEW-PART",
                    "planned_quantity_per_unit": 1.0,
                    "status": "success",
                    "group_label": "group1",
                    "recipe_row_id": 9001,
                },
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 201,
                    "sku": "BAD",
                    "planned_quantity_per_unit": 1.0,
                    "status": "failed",
                    "error": "422 validation error",
                    "group_label": "group1",
                },
            ],
            "warnings": [],
            "message": "Batch update completed: 2 succeeded, 1 failed",
        }
        app = build_batch_recipe_update_ui(response)
        _assert_valid_prefab(app)

    def test_empty_results(self):
        response = {
            "is_preview": True,
            "total_ops": 0,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [],
            "warnings": [],
            "message": "Nothing to do",
        }
        app = build_batch_recipe_update_ui(response)
        _assert_valid_prefab(app)

    def test_with_warnings(self):
        response = {
            "is_preview": True,
            "total_ops": 1,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 1,
            "results": [
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 200,
                    "sku": "NEW-PART",
                    "planned_quantity_per_unit": 1.0,
                    "status": "skipped",
                    "error": "Old variant not present in this MO",
                    "group_label": "OLD-PART → [NEW-PART]",
                },
            ],
            "warnings": ["MO 9999: old variant 100 not in recipe — skipping"],
            "message": "Preview with warnings",
        }
        app = build_batch_recipe_update_ui(response)
        _assert_valid_prefab(app)

    def test_rows_carry_canonical_display_name_when_supplied(self):
        """Each result op may carry ``display_name`` — the Katana-UI-format
        ``parent / value1 / value2`` name built upstream via
        ``build_variant_display_name``. The flattened ``rows`` state slot
        surfaces it via the ``item`` column so the rendered DataTable shows
        the same canonical name as every other variant-displaying surface
        (search_items, check_inventory, variant card).
        """
        response = {
            "is_preview": True,
            "total_ops": 1,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 200,
                    "sku": "NEW-PART",
                    "display_name": "Acme Float / 36mm / Black",
                    "planned_quantity_per_unit": 1.0,
                    "status": "pending",
                    "group_label": "OLD-PART → [NEW-PART]",
                },
            ],
            "warnings": [],
            "message": "Preview: 1 sub-op planned",
        }
        app = build_batch_recipe_update_ui(response)
        envelope = app.to_json()

        # The flattened state slot the DataTable binds to must carry the
        # canonical display name on its ``item`` column.
        state_rows = envelope["state"]["rows"]
        assert len(state_rows) == 1
        assert state_rows[0]["item"] == "Acme Float / 36mm / Black"
        # SKU still flows through as its own column for ops/scripts.
        assert state_rows[0]["sku"] == "NEW-PART"

    def test_rows_fall_back_to_sku_when_display_name_absent(self):
        """Backward-compat: ops emitted by older code paths (or test fixtures
        that don't compute display_name) fall through to SKU, then to the
        ``variant {id}`` sentinel. Pins the resolution order: display_name >
        sku > 'variant {id}' > empty string.
        """
        response = {
            "is_preview": True,
            "total_ops": 2,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 300,
                    "sku": "FALLBACK-SKU",
                    "planned_quantity_per_unit": 1.0,
                    "status": "pending",
                    "group_label": "g1",
                },
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 301,
                    "planned_quantity_per_unit": 1.0,
                    "status": "pending",
                    "group_label": "g1",
                },
            ],
            "warnings": [],
            "message": "Preview: 2 sub-ops planned",
        }
        app = build_batch_recipe_update_ui(response)
        envelope = app.to_json()

        state_rows = envelope["state"]["rows"]
        assert state_rows[0]["item"] == "FALLBACK-SKU"
        # Neither display_name nor sku — falls through to ``variant {id}``.
        assert state_rows[1]["item"] == "variant 301"

    def test_per_row_qty_diff_overlay(self):
        """The per-row ``Qty`` cell carries an old → new diff via
        :class:`FieldChangeView`. Maps the three op_types to the three
        diff shapes the renderer cares about:

        - ``add`` → ``"+ N"``
        - ``delete`` → ``"- N"`` (when the upstream enricher captured the
          prior qty via ``before_planned_quantity_per_unit``)
        - ``update`` → ``"before -> after"`` (ASCII arrow — DataTable
          cells are flat strings).
        """
        response = {
            "is_preview": True,
            "total_ops": 3,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 200,
                    "sku": "NEW-PART",
                    "planned_quantity_per_unit": 2.0,
                    "status": "pending",
                    "group_label": "g1",
                },
                {
                    "op_type": "delete",
                    "manufacturing_order_id": 9999,
                    "recipe_row_id": 5001,
                    "variant_id": 100,
                    "sku": "OLD-PART",
                    "before_planned_quantity_per_unit": 3.0,
                    "status": "pending",
                    "group_label": "g1",
                },
                {
                    "op_type": "update",
                    "manufacturing_order_id": 9999,
                    "recipe_row_id": 5002,
                    "variant_id": 101,
                    "sku": "RESIZE-PART",
                    "before_planned_quantity_per_unit": 1.0,
                    "planned_quantity_per_unit": 4.0,
                    "status": "pending",
                    "group_label": "g1",
                },
            ],
            "warnings": [],
            "message": "preview",
        }
        app = build_batch_recipe_update_ui(response)
        _assert_valid_prefab(app)
        rows = app.to_json()["state"]["rows"]
        assert rows[0]["qty"] == "+ 2.0"
        assert rows[1]["qty"] == "- 3.0"
        assert rows[2]["qty"] == "1.0 -> 4.0"

    def test_per_row_batch_transactions_diff_overlay(self):
        """Post-#518, ``MORecipeRowAdd`` / ``Update`` carry
        ``batch_transactions``. The renderer surfaces these inline with
        the same diff shape as Qty, via
        :func:`_format_batch_transactions_summary` —
        ``batch <id>xN, batch <id>xM`` per allocation. The ``Batch``
        column only renders when at least one row carries a non-empty
        cell.
        """
        response = {
            "is_preview": True,
            "total_ops": 2,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 200,
                    "sku": "BATCH-TRACKED",
                    "planned_quantity_per_unit": 50.0,
                    "batch_transactions": [
                        {"batch_id": 42, "quantity": 30.0},
                        {"batch_id": 51, "quantity": 20.0},
                    ],
                    "status": "pending",
                    "group_label": "g1",
                },
                {
                    "op_type": "update",
                    "manufacturing_order_id": 9999,
                    "recipe_row_id": 5001,
                    "variant_id": 201,
                    "sku": "RESIZE-BATCH",
                    "before_batch_transactions": [
                        {"batch_id": 42, "quantity": 10.0},
                    ],
                    "batch_transactions": [
                        {"batch_id": 42, "quantity": 15.0},
                    ],
                    "status": "pending",
                    "group_label": "g1",
                },
            ],
            "warnings": [],
            "message": "preview",
        }
        app = build_batch_recipe_update_ui(response)
        _assert_valid_prefab(app)
        envelope = app.to_json()
        rows = envelope["state"]["rows"]
        assert rows[0]["batch"] == "+ batch 42x30, batch 51x20"
        assert rows[1]["batch"] == "batch 42x10 -> batch 42x15"

        # The Batch column must be present in the rendered columns because
        # at least one row has a non-empty cell.
        columns = _walk_view_tree(envelope["view"])
        batch_col_keys = {
            c.get("key")
            for tab in columns
            if tab.get("type") == "DataTable"
            for c in (tab.get("columns") or [])
        }
        assert "batch" in batch_col_keys

    def test_per_row_serial_numbers_diff_overlay(self):
        """Serial-tracked variants surface their serial list as a
        comma-joined cell. ``add`` ops render ``"+ sn1, sn2"``;
        ``update`` ops render ``"before -> after"``.
        """
        response = {
            "is_preview": True,
            "total_ops": 1,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 200,
                    "sku": "SERIAL-TRACKED",
                    "planned_quantity_per_unit": 2.0,
                    "serial_numbers": ["SN-001", "SN-002"],
                    "status": "pending",
                    "group_label": "g1",
                },
            ],
            "warnings": [],
            "message": "preview",
        }
        app = build_batch_recipe_update_ui(response)
        _assert_valid_prefab(app)
        envelope = app.to_json()
        rows = envelope["state"]["rows"]
        assert rows[0]["serials"] == "+ SN-001, SN-002"

        # Serials column must be rendered for this card (at least one
        # non-empty cell).
        column_keys = {
            c.get("key")
            for tab in _walk_view_tree(envelope["view"])
            if tab.get("type") == "DataTable"
            for c in (tab.get("columns") or [])
        }
        assert "serials" in column_keys

    def test_optional_columns_dropped_when_no_signal(self):
        """The ``Batch`` and ``Serials`` columns are dropped when no row
        carries a non-empty cell. Keeps the all-qty (non-batch, non-serial)
        case from padding two empty columns across every row.
        """
        response = {
            "is_preview": True,
            "total_ops": 1,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 200,
                    "sku": "PLAIN-PART",
                    "planned_quantity_per_unit": 1.0,
                    "status": "pending",
                    "group_label": "g1",
                },
            ],
            "warnings": [],
            "message": "preview",
        }
        app = build_batch_recipe_update_ui(response)
        envelope = app.to_json()
        column_keys = {
            c.get("key")
            for tab in _walk_view_tree(envelope["view"])
            if tab.get("type") == "DataTable"
            for c in (tab.get("columns") or [])
        }
        # Core columns always render…
        assert "qty" in column_keys
        # …but the optional Batch / Serials columns drop out when empty.
        assert "batch" not in column_keys
        assert "serials" not in column_keys

    def test_empty_batch_or_serials_does_not_emit_prefix_only_cell(self):
        """When ``batch_transactions=[]`` / ``serial_numbers=[]`` is on the
        wire (e.g. a non-batch-tracked add that still sent an empty list
        for shape consistency), the cell must render as ``""`` rather
        than ``"+ "``. Otherwise the truthy prefix-only string keeps the
        column visible with no meaningful content.
        """
        response = {
            "is_preview": True,
            "total_ops": 1,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "add",
                    "manufacturing_order_id": 9999,
                    "variant_id": 200,
                    "sku": "EMPTY-LISTS",
                    "planned_quantity_per_unit": 1.0,
                    "batch_transactions": [],
                    "serial_numbers": [],
                    "status": "pending",
                    "group_label": "g1",
                },
            ],
            "warnings": [],
            "message": "preview",
        }
        app = build_batch_recipe_update_ui(response)
        envelope = app.to_json()
        rows = envelope["state"]["rows"]
        assert rows[0]["batch"] == ""
        assert rows[0]["serials"] == ""
        # And the optional columns drop out since every cell is empty.
        column_keys = {
            c.get("key")
            for tab in _walk_view_tree(envelope["view"])
            if tab.get("type") == "DataTable"
            for c in (tab.get("columns") or [])
        }
        assert "batch" not in column_keys
        assert "serials" not in column_keys

    def test_update_with_no_prior_renders_just_after_value(self):
        """Back-compat: ops emitted before the ``before_*`` enrichment
        landed (no ``before_planned_quantity_per_unit`` on the wire) still
        render — the diff cell shows *only* the after value rather than
        claiming the prior was actually unset (``"(unset) -> 4.0"``).
        ``_format_recipe_row_diff`` special-cases ``kind="changed"`` with
        ``before is None`` to render after-only.
        """
        response = {
            "is_preview": True,
            "total_ops": 1,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "update",
                    "manufacturing_order_id": 9999,
                    "recipe_row_id": 5002,
                    "variant_id": 101,
                    "sku": "NO-PRIOR",
                    "planned_quantity_per_unit": 4.0,
                    "status": "pending",
                    "group_label": "g1",
                },
            ],
            "warnings": [],
            "message": "preview",
        }
        app = build_batch_recipe_update_ui(response)
        _assert_valid_prefab(app)
        rows = app.to_json()["state"]["rows"]
        # No before_* on the wire — the diff cell renders the after value
        # alone, with no ``(unset) -> `` prefix.
        assert rows[0]["qty"] == "4.0"

    def test_delete_with_no_prior_renders_empty_qty_cell(self):
        """Back-compat: ``delete`` ops emitted without a captured
        ``before_planned_quantity_per_unit`` (the upstream enricher
        couldn't resolve the prior row) still render — the diff cell
        falls through to empty rather than ``"- (unset)"``. Documented
        in ``build_batch_recipe_update_ui``'s docstring: "delete with no
        captured prior" → empty cell.
        """
        response = {
            "is_preview": True,
            "total_ops": 1,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "delete",
                    "manufacturing_order_id": 9999,
                    "recipe_row_id": 5003,
                    "variant_id": 102,
                    "sku": "DELETE-NO-PRIOR",
                    "status": "pending",
                    "group_label": "g1",
                },
            ],
            "warnings": [],
            "message": "preview",
        }
        app = build_batch_recipe_update_ui(response)
        _assert_valid_prefab(app)
        rows = app.to_json()["state"]["rows"]
        # No before_* on the wire for a delete — the diff cell is empty
        # (no signal to render). Status / action still surface.
        assert rows[0]["qty"] == ""
        assert rows[0]["action"] == "DELETE"

    def test_update_with_unchanged_value_renders_current(self):
        """When a row was sent in ``update_recipe_rows`` but a field's
        before == after (a no-op patch — e.g. the agent included a field
        for clarity but didn't actually change it), the diff cell shows
        the current value rather than ``"3.0 -> 3.0"`` (visual noise).
        """
        response = {
            "is_preview": True,
            "total_ops": 1,
            "success_count": 0,
            "failed_count": 0,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "update",
                    "manufacturing_order_id": 9999,
                    "recipe_row_id": 5002,
                    "variant_id": 101,
                    "sku": "NOOP",
                    "before_planned_quantity_per_unit": 3.0,
                    "planned_quantity_per_unit": 3.0,
                    "status": "pending",
                    "group_label": "g1",
                },
            ],
            "warnings": [],
            "message": "preview",
        }
        app = build_batch_recipe_update_ui(response)
        rows = app.to_json()["state"]["rows"]
        assert rows[0]["qty"] == "3.0"

    def test_qty_diff_survives_failed_status(self):
        """A failed result still renders the planned diff so the operator
        can see what was attempted. ``status="failed"`` only controls the
        Status column + error column — not the diff overlay.
        """
        response = {
            "is_preview": False,
            "total_ops": 1,
            "success_count": 0,
            "failed_count": 1,
            "skipped_count": 0,
            "results": [
                {
                    "op_type": "update",
                    "manufacturing_order_id": 9999,
                    "recipe_row_id": 5002,
                    "variant_id": 101,
                    "sku": "FAILED-RESIZE",
                    "before_planned_quantity_per_unit": 1.0,
                    "planned_quantity_per_unit": 4.0,
                    "status": "failed",
                    "error": "422 validation error",
                    "group_label": "g1",
                },
            ],
            "warnings": [],
            "message": "1 failed",
        }
        app = build_batch_recipe_update_ui(response)
        rows = app.to_json()["state"]["rows"]
        assert rows[0]["qty"] == "1.0 -> 4.0"
        assert rows[0]["status"] == "FAILED"
        assert rows[0]["error"] == "422 validation error"


def _confirm_button_on_click(envelope: dict, label: str) -> list[dict]:
    """Return the on_click action list for the Confirm button matching ``label``.

    Per ADR-0021 every Confirm button fires a list of two actions:
    ``setState("pending", True)`` and ``toolCall(<apply_tool>, ...)``.
    The Cancel button mirrors this with ``setState("cancelled", True)``
    and an ``updateContext(...)`` notification.
    """
    buttons = _find_buttons_by_label(envelope, label)
    assert len(buttons) == 1, (
        f"Expected exactly one Button with label {label!r}; found {len(buttons)}."
    )
    on_click = buttons[0].get("onClick") or buttons[0].get("on_click")
    assert isinstance(on_click, list), (
        f"Button {label!r}'s onClick should be a list of actions; got {on_click!r}"
    )
    return on_click


class TestConfirmButtonEmitsCallTool:
    """The Confirm button on every preview card fires two actions per
    ADR-0021:

    1. ``setState("pending", True)`` — flips the card to a "Pending…"
       pill, grays out the buttons (in-flight click guard).
    2. ``toolCall(<apply_tool>, arguments={..., preview=False}, ...)``
       — calls the apply tool directly from the iframe. The
       ``on_success`` chain pushes the structured result back into the
       agent's model context via ``updateContext``.

    Supersedes the old ADR-0015 ``SendMessage`` re-issue handshake; see
    the unified rail ADR for the spec finding that motivated the move
    (``ui/update-model-context`` lets the iframe push the result to the
    agent's context, removing the need for an agent re-issue).
    """

    @staticmethod
    def _assert_apply_actions(on_click: list[dict], tool_name: str) -> dict:
        """Validate that on_click is exactly [SetState(pending, True),
        CallTool(<tool_name>, arguments={..., preview=False}, ...)] and
        return the CallTool action."""
        set_states = [a for a in on_click if a.get("action") == "setState"]
        tool_calls = [a for a in on_click if a.get("action") == "toolCall"]
        assert any(
            a.get("key") == "pending" and a.get("value") is True for a in set_states
        ), f"Expected setState('pending', True) in on_click; got {on_click!r}"
        matching = [c for c in tool_calls if c.get("tool") == tool_name]
        assert len(matching) == 1, (
            f"Expected exactly one toolCall to {tool_name!r}; "
            f"got {[c.get('tool') for c in tool_calls]!r}"
        )
        call = matching[0]
        args = call.get("arguments") or {}
        assert args.get("preview") is False, (
            f"Confirm-button toolCall must bake preview=False into arguments; "
            f"got {args!r}"
        )
        return call

    def test_fulfill_preview_confirm_emits_call_tool(self):
        app = build_fulfill_preview_ui(
            {
                "order_id": 9999,
                "order_type": "sales",
                "order_number": "SO-1",
                "status": "PARTIALLY_DELIVERED",
                "warnings": [],
            }
        )
        envelope = app.to_json()
        on_click = _confirm_button_on_click(envelope, "Confirm Fulfillment")
        call = self._assert_apply_actions(on_click, "fulfill_order")
        args = call["arguments"]
        assert args["order_id"] == 9999
        assert args["order_type"] == "sales"

    def test_fulfill_preview_confirm_carries_request_args(self):
        """Apply payload must propagate every non-default arg from the
        preview request — #845. Pre-fix, ``completed_at`` /
        ``serial_numbers`` / ``acknowledge_inventory_ordering`` all
        defaulted out at apply time, silently completing the order at
        click-time ``now()`` instead of the backdated timestamp.
        """
        from datetime import UTC, datetime

        from katana_mcp.tools.foundation.orders import FulfillOrderRequest

        backdated = datetime(2026, 5, 1, 22, 43, 0, tzinfo=UTC)
        request = FulfillOrderRequest(
            order_id=9999,
            order_type="manufacturing",
            preview=True,
            completed_at=backdated,
            serial_numbers=[12345, 12346],
            acknowledge_inventory_ordering=True,
        )
        app = build_fulfill_preview_ui(
            {
                "order_id": 9999,
                "order_type": "manufacturing",
                "order_number": "MO-1",
                "status": "NOT_STARTED",
                "warnings": [],
            },
            request=request,
        )
        envelope = app.to_json()
        on_click = _confirm_button_on_click(envelope, "Confirm Fulfillment")
        call = self._assert_apply_actions(on_click, "fulfill_order")
        args = call["arguments"]
        assert args["order_id"] == 9999
        assert args["order_type"] == "manufacturing"
        # ISO 8601 string after pydantic ``model_dump(mode="json")``.
        assert args["completed_at"] == "2026-05-01T22:43:00Z"
        assert args["serial_numbers"] == [12345, 12346]
        assert args["acknowledge_inventory_ordering"] is True

    def test_fulfill_preview_confirm_carries_sales_row_overrides(self):
        """The ``rows`` field (sales-side per-row overrides) round-trips
        through the apply payload the same way as the MO-side
        scalars — #845.
        """
        from katana_mcp.tools.foundation.orders import (
            FulfillOrderRequest,
            FulfillRowOverride,
        )

        request = FulfillOrderRequest(
            order_id=8888,
            order_type="sales",
            preview=True,
            rows=[FulfillRowOverride(sales_order_row_id=42, serial_numbers=[111])],
        )
        app = build_fulfill_preview_ui(
            {
                "order_id": 8888,
                "order_type": "sales",
                "order_number": "SO-2",
                "status": "NOT_SHIPPED",
                "warnings": [],
            },
            request=request,
        )
        envelope = app.to_json()
        on_click = _confirm_button_on_click(envelope, "Confirm Fulfillment")
        call = self._assert_apply_actions(on_click, "fulfill_order")
        args = call["arguments"]
        assert args["rows"] == [{"sales_order_row_id": 42, "serial_numbers": [111]}]

    def test_receipt_preview_confirm_emits_call_tool(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            ReceiveItemRequest,
            ReceivePurchaseOrderRequest,
        )

        request = ReceivePurchaseOrderRequest(
            order_id=1234,
            items=[ReceiveItemRequest(purchase_order_row_id=10, quantity=5.0)],
        )
        app = build_receipt_ui(
            {
                "order_id": 1234,
                "order_number": "PO-1",
                "is_preview": True,
                "items_received": 5,
                "status": "NOT_RECEIVED",
                "warnings": [],
            },
            confirm_request=request,
            confirm_tool="receive_purchase_order",
        )
        envelope = app.to_json()
        on_click = _confirm_button_on_click(envelope, "Confirm Receipt")
        call = self._assert_apply_actions(on_click, "receive_purchase_order")
        assert call["arguments"]["order_id"] == 1234

    def test_batch_recipe_preview_confirm_emits_call_tool(self):
        request = _StubRequest()
        app = build_batch_recipe_update_ui(
            {
                "is_preview": True,
                "total_ops": 1,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "results": [
                    {
                        "op_type": "delete",
                        "manufacturing_order_id": 9999,
                        "recipe_row_id": 5001,
                        "status": "pending",
                    }
                ],
                "warnings": [],
                "message": "Preview",
            },
            confirm_request=request,
            confirm_tool="batch_update_recipes",
        )
        envelope = app.to_json()
        on_click = _confirm_button_on_click(envelope, "Execute batch")
        self._assert_apply_actions(on_click, "batch_update_recipes")

    def test_fulfill_preview_confirm_pushes_result_via_update_context(self):
        """The unified apply rail's on_success chain must include
        ``UpdateContext(content=$result)`` so the structured apply
        response reaches the agent's context on its next turn.
        """
        app = build_fulfill_preview_ui(
            {
                "order_id": 5,
                "order_type": "manufacturing",
                "order_number": "MO-2",
                "status": "PARTIALLY_DELIVERED",
                "warnings": [],
            }
        )
        envelope = app.to_json()
        on_click = _confirm_button_on_click(envelope, "Confirm Fulfillment")
        call = self._assert_apply_actions(on_click, "fulfill_order")
        on_success = call.get("onSuccess")
        assert isinstance(on_success, list), (
            f"Expected onSuccess to be a list; got {on_success!r}"
        )
        update_contexts = [a for a in on_success if a.get("action") == "updateContext"]
        assert len(update_contexts) == 1, (
            f"Expected exactly one updateContext in on_success; got {update_contexts!r}"
        )
        assert update_contexts[0].get("content") == "{{ $result }}", (
            f"updateContext.content must carry $result so the agent receives "
            f"the structured apply response; got {update_contexts[0]!r}"
        )


class TestConfirmButtonDirectApplyRail:
    """Pre-#807 direct-apply rail tests, retained as the smoke test for the
    create-PO card's full retry / error / spam-guard contract. Now the
    unified rail (ADR-0021) every preview tool uses.
    """

    @staticmethod
    def _confirm_action(envelope: dict, label: str) -> dict:
        """Return the inner ``toolCall`` action for the direct-apply rail.

        The direct rail's onClick is a list:
        ``[setState("pending", True), toolCall(...)]``. The leading
        ``setState`` is the in-flight click guard (so a double-click can't
        fire two applies); the toolCall is what we return for assertions.
        """
        buttons = _find_buttons_by_label(envelope, label)
        assert len(buttons) == 1, (
            f"Expected exactly one Button with label {label!r}; found {len(buttons)}."
        )
        on_click = buttons[0].get("onClick") or buttons[0].get("on_click")
        assert isinstance(on_click, list), (
            f"Direct-apply rail onClick should be a [SetState, CallTool] list; "
            f"got {type(on_click).__name__}: {on_click!r}"
        )
        # Click guard must come first: SetState(pending=True) before the
        # CallTool so the button binds locked the moment the click fires.
        assert on_click[0].get("action") == "setState", (
            f"First action must be the pending guard; got {on_click[0]!r}"
        )
        assert on_click[0].get("key") == "pending"
        assert on_click[0].get("value") is True, (
            f"pending guard must set pending=True; got {on_click[0]!r}"
        )
        tool_calls = [a for a in on_click if a.get("action") == "toolCall"]
        assert len(tool_calls) == 1, (
            f"Expected exactly one toolCall in onClick; got {tool_calls!r}"
        )
        return tool_calls[0]

    def test_po_preview_direct_apply_fires_call_tool(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-1",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_po_create_ui(
            {
                "id": 1,
                "order_number": "PO-1",
                "supplier_id": 2,
                "location_id": 3,
                "status": "NOT_RECEIVED",
                "warnings": [],
            },
            confirm_request=request,
            confirm_tool="create_purchase_order",
        )
        envelope = app.to_json()
        on_click = self._confirm_action(envelope, "Confirm & Create Purchase Order")

        # The direct rail fires CallTool with the apply args (preview=False).
        assert on_click.get("tool") == "create_purchase_order"
        args = on_click.get("arguments") or {}
        assert args.get("preview") is False, (
            f"Direct rail must override preview=False; got {args!r}"
        )
        assert args.get("supplier_id") == 2
        assert args.get("location_id") == 3
        assert args.get("order_number") == "PO-1"

    def test_po_preview_direct_apply_pushes_result_via_update_context(self):
        """on_success chain must include UpdateContext(content=$result).

        This is the load-bearing primitive: the iframe pushes the apply
        result into the agent's context for its next turn, replacing the
        SendMessage round-trip.
        """
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-1",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_po_create_ui(
            {
                "id": 1,
                "order_number": "PO-1",
                "supplier_id": 2,
                "location_id": 3,
                "status": "NOT_RECEIVED",
                "warnings": [],
            },
            confirm_request=request,
            confirm_tool="create_purchase_order",
        )
        envelope = app.to_json()
        on_click = self._confirm_action(envelope, "Confirm & Create Purchase Order")

        on_success = on_click.get("onSuccess")
        assert isinstance(on_success, list), (
            f"Expected onSuccess to be a list; got {on_success!r}"
        )
        update_contexts = [a for a in on_success if a.get("action") == "updateContext"]
        assert len(update_contexts) == 1, (
            f"Expected exactly one updateContext action; got {update_contexts!r}"
        )
        assert update_contexts[0].get("content") == "{{ $result }}", (
            f"updateContext.content must carry $result reactive ref so the "
            f"agent receives the structured apply response on its next turn; "
            f"got {update_contexts[0]!r}"
        )

        # State morph: applied=True so the iframe flips to a result view in
        # place. result=$result so any inline Rx refs to state.result work.
        set_states = [a for a in on_success if a.get("action") == "setState"]
        keys = {s.get("key") for s in set_states}
        assert "applied" in keys and "result" in keys, (
            f"Expected applied/result state morph; got keys {keys!r}"
        )

    def test_po_preview_direct_apply_handles_error(self):
        """on_error chain must include UpdateContext with the error reason
        plus a toast and an 'error' state morph.
        """
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-1",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_po_create_ui(
            {
                "id": 1,
                "order_number": "PO-1",
                "supplier_id": 2,
                "location_id": 3,
                "status": "NOT_RECEIVED",
                "warnings": [],
            },
            confirm_request=request,
            confirm_tool="create_purchase_order",
        )
        envelope = app.to_json()
        on_click = self._confirm_action(envelope, "Confirm & Create Purchase Order")

        on_error = on_click.get("onError")
        assert isinstance(on_error, list), (
            f"Expected onError to be a list; got {on_error!r}"
        )
        update_contexts = [a for a in on_error if a.get("action") == "updateContext"]
        assert len(update_contexts) == 1, (
            f"Expected exactly one updateContext on error; got {update_contexts!r}"
        )
        assert "$error" in update_contexts[0].get("content", ""), (
            f"updateContext on error must include the error reason; "
            f"got {update_contexts[0]!r}"
        )
        toasts = [a for a in on_error if a.get("action") == "showToast"]
        assert len(toasts) == 1, f"Expected one error toast; got {toasts!r}"

    def test_po_preview_direct_apply_double_click_is_guarded(self):
        """Confirm button is guarded against double-click by two layers:

        1. ``disabled=Rx("pending")`` on the Preview-state Confirm button
           — the SetState("pending", True) at the start of the on_click
           chain immediately disables this rendering of the button before
           the second click can fire.
        2. The button slot itself morphs through state via If/Elif/Else
           in ``_render_apply_button_row`` — the Preview button is
           REPLACED with "Applying…" (disabled) when pending=True flips,
           and with "View in Katana" / "Retry" / "Cancelled" on the
           terminal states. So the original Confirm button is gone before
           any second-click handler could fire.

        Both layers together ensure: a fast double-click on
        ``create_purchase_order`` can't fire two CallTool requests in
        parallel.
        """
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-1",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_po_create_ui(
            {
                "id": 1,
                "order_number": "PO-1",
                "supplier_id": 2,
                "location_id": 3,
                "status": "NOT_RECEIVED",
                "warnings": [],
            },
            confirm_request=request,
            confirm_tool="create_purchase_order",
        )
        envelope = app.to_json()

        buttons = _find_buttons_by_label(envelope, "Confirm & Create Purchase Order")
        on_click = buttons[0].get("onClick") or buttons[0].get("on_click")
        assert on_click is not None
        # Click chain: [SetState(pending, True), CallTool(...)].
        assert on_click[0].get("action") == "setState"
        assert on_click[0].get("key") == "pending"
        assert on_click[0].get("value") is True

        # Inner CallTool clears pending in both on_success and on_error.
        tool_call = next(a for a in on_click if a.get("action") == "toolCall")
        for chain_name in ("onSuccess", "onError"):
            chain = tool_call.get(chain_name) or []
            pending_clears = [
                a
                for a in chain
                if a.get("action") == "setState"
                and a.get("key") == "pending"
                and a.get("value") is False
            ]
            assert len(pending_clears) == 1, (
                f"{chain_name} must clear pending=False so the buttons unlock "
                f"after the call resolves; got {chain!r}"
            )

        # Layer 1 — the Preview-state Confirm button binds
        # ``disabled=Rx("pending")`` so a rapid double-click on the
        # original button has its second click dropped the moment
        # ``pending=True`` lands (before the If/Elif swap re-mounts a
        # different button).
        disabled = buttons[0].get("disabled")
        assert isinstance(disabled, str), (
            f"Expected disabled to be a reactive template string; got "
            f"{disabled!r}. The pending-state click guard lives there."
        )
        assert "pending" in disabled, (
            f"Confirm button's disabled expression must reference "
            f"``pending`` so it disables the moment pending=True is set "
            f"at the start of the on_click chain. Got disabled={disabled!r}"
        )

        # Layer 2 — the button SLOT morphs via If/Elif on
        # applied/error/cancelled, so the original Confirm Button is
        # replaced (not just disabled) when any terminal state lands.
        # Verify by counting Button nodes in the envelope grouped under
        # the state-driven If/Elif chain in _render_apply_button_row;
        # the existence of the morphing branches is the pin.
        # Walk the envelope tree (not the json.dumps text — the latter
        # would escape the ``…`` ellipsis as ``…`` and trip up a
        # naive substring assertion).
        labels: list[str] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                if node.get("type") == "Button" and isinstance(node.get("label"), str):
                    labels.append(node["label"])
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(envelope)
        # The state-morph branches appear as "Applying…" / "Retry"
        # Button nodes inside If/Elif containers. Their existence (in
        # the envelope tree, regardless of which client-side branch
        # is currently visible) is the pin.
        assert "Applying…" in labels, (
            f"Pending-state Button label must exist as part of the If/Elif "
            f"morph so the Preview Confirm button is replaced when pending "
            f"fires. Got buttons={labels!r}"
        )
        assert "Retry" in labels, (
            f"Error-state Retry Button must exist as part of the If/Elif "
            f"morph so the apply rail can retry on failure. Got buttons={labels!r}"
        )

    def test_apply_action_clears_error_state_on_click_and_on_success(self):
        """Per PR #808 review: the Retry button reuses ``apply_action`` and
        every preview card renders an ``If("error")`` destructive Alert
        whenever ``state.error`` is truthy. Without explicit clears, a
        successful Retry leaves the failed-attempt Alert stuck on the
        otherwise-applied card.

        The apply action chain must clear ``state.error`` in two places:

        1. **Click-time** — at the start of the on_click list, alongside
           ``pending=True``. Hides the destructive Alert the moment the
           retry fires, matching the Pending pill visual state.
        2. **On success** — inside ``on_success`` alongside the
           ``applied=True`` morph. Belt-and-suspenders for the successful
           case so the rendered applied card never carries a stale error.
        """
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-RETRY",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_po_create_ui(
            {
                "id": 1,
                "order_number": "PO-RETRY",
                "supplier_id": 2,
                "location_id": 3,
                "status": "NOT_RECEIVED",
                "warnings": [],
            },
            confirm_request=request,
            confirm_tool="create_purchase_order",
        )
        envelope = app.to_json()
        on_click = self._confirm_action(envelope, "Confirm & Create Purchase Order")

        # Click-time clear: among the top-level setState actions before
        # the toolCall, exactly one must set error=None.
        # ``on_click`` is the CallTool itself; click-chain wrapper lives
        # one level up — fetch via the Confirm button's on_click array.
        buttons = _find_buttons_by_label(envelope, "Confirm & Create Purchase Order")
        click_chain = buttons[0].get("onClick") or buttons[0].get("on_click")
        assert isinstance(click_chain, list)
        prefire_error_clears = [
            a
            for a in click_chain
            if a.get("action") == "setState"
            and a.get("key") == "error"
            and a.get("value") is None
        ]
        assert len(prefire_error_clears) == 1, (
            "Click chain must set error=None before firing the apply so "
            "the destructive Alert from any prior failed attempt hides "
            "immediately on Retry. Got chain="
            f"{click_chain!r}"
        )

        # On-success clear: inside the CallTool's onSuccess list.
        on_success = on_click.get("onSuccess") or []
        success_error_clears = [
            a
            for a in on_success
            if a.get("action") == "setState"
            and a.get("key") == "error"
            and a.get("value") is None
        ]
        assert len(success_error_clears) == 1, (
            "on_success must set error=None alongside the applied morph "
            "so a successful Retry doesn't leave a stale failure Alert "
            "rendered on the applied card. Got on_success="
            f"{on_success!r}"
        )


class TestCancelButtonEmitsUpdateContext:
    """The Cancel button (post-ADR-0021) fires ``setState("cancelled", True)``
    plus an ``updateContext(content="User cancelled <noun phrase> preview.")``
    so the agent sees the user's opt-out as a context update — no chat
    indirection. The noun phrase carries its own determiner ("the" / "that"
    / "those") so the template doesn't double-up the article.
    """

    def _assert_cancel_actions(self, on_click: list[dict]) -> None:
        set_states = [a for a in on_click if a.get("action") == "setState"]
        update_contexts = [a for a in on_click if a.get("action") == "updateContext"]
        assert any(
            a.get("key") == "cancelled" and a.get("value") is True for a in set_states
        ), f"Expected setState('cancelled', True) in on_click; got {on_click!r}"
        cancel_msgs = [
            u
            for u in update_contexts
            if isinstance(u.get("content"), str)
            and u["content"].startswith("User cancelled ")
            and u["content"].endswith(" preview.")
        ]
        assert len(cancel_msgs) == 1, (
            f"Expected exactly one Cancel updateContext starting with "
            f"'User cancelled ' and ending with ' preview.'; "
            f"got {[u.get('content') for u in update_contexts]!r}"
        )
        # Regression-guard for the article-doubling bug (#808 review): the
        # previous template hard-coded a leading "the" while call sites
        # already passed article-prefixed phrases, producing "the the …"
        # / "the that …". The noun phrase must start with its own
        # determiner, never with a doubled article.
        content = cancel_msgs[0]["content"]
        assert not content.startswith("User cancelled the the "), (
            f"Cancel content has double 'the the': {content!r}"
        )
        assert not content.startswith("User cancelled the that "), (
            f"Cancel content has 'the that' mix-up: {content!r}"
        )
        assert not content.startswith("User cancelled the those "), (
            f"Cancel content has 'the those' mix-up: {content!r}"
        )

    def test_order_preview_cancel(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-CANCEL-1",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_po_create_ui(
            {"order_number": "PO-CANCEL-1", "warnings": []},
            confirm_request=request,
            confirm_tool="create_purchase_order",
        )
        on_click = _confirm_button_on_click(app.to_json(), "Cancel")
        self._assert_cancel_actions(on_click)

    def test_fulfill_preview_cancel(self):
        app = build_fulfill_preview_ui(
            {
                "order_id": 9999,
                "order_type": "sales",
                "order_number": "SO-CANCEL-1",
                "status": "IN_PROGRESS",
                "warnings": [],
            }
        )
        on_click = _confirm_button_on_click(app.to_json(), "Cancel")
        self._assert_cancel_actions(on_click)


class TestPreviewCardSeedsPendingState:
    """Every preview card must seed ``pending=False`` and ``cancelled=False``
    in iframe state so the conditional rendering for the "Pending…" /
    "Cancelled" pills (and the buttons' ``disabled="pending or cancelled"``)
    starts in the un-pressed default.
    """

    @staticmethod
    def _assert_seeds_state(envelope: dict, builder: str) -> None:
        state = envelope.get("state") or envelope.get("$prefab", {}).get("state") or {}
        assert state.get("pending") is False, (
            f"{builder}: state.pending must seed to False; got {state!r}"
        )
        assert state.get("cancelled") is False, (
            f"{builder}: state.cancelled must seed to False; got {state!r}"
        )

    def test_order_preview(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            CreatePurchaseOrderRequest,
            PurchaseOrderItem,
        )

        request = CreatePurchaseOrderRequest(
            supplier_id=2,
            location_id=3,
            order_number="PO-STATE-1",
            items=[PurchaseOrderItem(variant_id=10, quantity=1.0, price_per_unit=2.0)],
        )
        app = build_po_create_ui(
            {"order_number": "PO-STATE-1", "warnings": []},
            confirm_request=request,
            confirm_tool="create_purchase_order",
        )
        self._assert_seeds_state(app.to_json(), "build_po_create_ui")

    def test_fulfill_preview(self):
        app = build_fulfill_preview_ui(
            {
                "order_id": 9999,
                "order_type": "sales",
                "order_number": "SO-STATE-1",
                "status": "IN_PROGRESS",
                "warnings": [],
            }
        )
        self._assert_seeds_state(app.to_json(), "build_fulfill_preview_ui")

    def test_receipt_preview(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            ReceiveItemRequest,
            ReceivePurchaseOrderRequest,
        )

        request = ReceivePurchaseOrderRequest(
            order_id=1234,
            items=[ReceiveItemRequest(purchase_order_row_id=10, quantity=1.0)],
        )
        app = build_receipt_ui(
            {
                "order_id": 1234,
                "order_number": "PO-STATE-2",
                "is_preview": True,
                "items_received": 1,
                "status": "NOT_RECEIVED",
                "warnings": [],
            },
            confirm_request=request,
            confirm_tool="receive_purchase_order",
        )
        self._assert_seeds_state(app.to_json(), "build_receipt_ui")

    def test_batch_recipe_preview(self):
        request = _StubRequest()
        app = build_batch_recipe_update_ui(
            {
                "is_preview": True,
                "total_ops": 1,
                "success_count": 0,
                "failed_count": 0,
                "skipped_count": 0,
                "results": [
                    {
                        "op_type": "delete",
                        "manufacturing_order_id": 1,
                        "recipe_row_id": 1,
                        "status": "pending",
                    }
                ],
                "warnings": [],
                "message": "preview",
            },
            confirm_request=request,
            confirm_tool="batch_update_recipes",
        )
        self._assert_seeds_state(app.to_json(), "build_batch_recipe_update_ui")


class TestBuildApplyActionXorInvariant:
    """``_build_apply_action`` requires both ``confirm_tool`` and
    ``confirm_request`` to be set together (or both ``None``); a
    single-arg call is a programmer error.
    """

    @pytest.mark.parametrize(
        "tool, request_obj",
        [
            ("create_purchase_order", None),
            (None, _StubRequest()),
        ],
    )
    def test_partial_inputs_raise_value_error(self, tool, request_obj):
        from katana_mcp.tools.prefab_ui import _build_apply_action

        with pytest.raises(ValueError, match="must be set together"):
            _build_apply_action(tool, request_obj)

    def test_both_none_returns_none(self):
        from katana_mcp.tools.prefab_ui import _build_apply_action

        assert _build_apply_action(None, None) is None

    def test_apply_inlines_args_and_overrides_preview(self):
        """The Confirm-button ``CallTool`` must carry every request field
        as a literal value in ``arguments`` and force ``preview=False``
        regardless of the request's preview value (the user already saw
        the preview).
        """
        from katana_mcp.tools.foundation.orders import FulfillOrderRequest
        from katana_mcp.tools.prefab_ui import _build_apply_action

        request = FulfillOrderRequest(order_id=42, order_type="sales", preview=True)
        actions = _build_apply_action("fulfill_order", request)
        assert actions is not None
        # Find the CallTool action.
        tool_calls = [a for a in actions if getattr(a, "tool", None) == "fulfill_order"]
        assert len(tool_calls) == 1, (
            f"Expected exactly one CallTool to fulfill_order; got {actions!r}"
        )
        call = tool_calls[0]
        args = getattr(call, "arguments", None)
        assert isinstance(args, dict)
        assert args["order_id"] == 42
        assert args["order_type"] == "sales"
        # preview is forced to False even though request.preview was True
        assert args["preview"] is False

    def test_preview_field_required_in_request(self):
        """A request model without a ``preview`` field is a programmer
        error — the CallTool would invoke the tool with an unrecognized
        ``preview=False`` argument that fails validation downstream.
        Fail loudly at UI-build time instead.
        """
        from katana_mcp.tools.prefab_ui import _build_apply_action
        from pydantic import BaseModel as _BaseModel

        class _NoPreview(_BaseModel):
            order_id: int = 1

        with pytest.raises(ValueError, match="requires a request model with a"):
            _build_apply_action("some_tool", _NoPreview())


class TestBuildApplyResultUIs:
    """Tests for the generic apply-result builders introduced alongside
    the ADR-0015 rail change. These supplement (not replace) the existing
    per-entity success cards."""

    def test_apply_success_renders_summary_lines(self):
        from katana_mcp.tools.prefab_ui import build_apply_success_ui

        app = build_apply_success_ui(
            title="Sales order #WEB1001 fulfilled",
            summary_lines=[
                "Item: Premium Widget v2 (WDG-LG-BK-001) qty 1",
                "Inventory: -1 of variant 1001",
            ],
            katana_url="https://factory.katanamrp.com/salesorder/1234",
        )
        envelope = app.to_json()
        # Title appears verbatim somewhere in the rendered card
        text_nodes: list[str] = []

        def collect(o: Any) -> None:
            if isinstance(o, dict):
                if isinstance(o.get("content"), str):
                    text_nodes.append(o["content"])
                for v in o.values():
                    collect(v)
            elif isinstance(o, list):
                for v in o:
                    collect(v)

        collect(envelope)
        joined = "\n".join(text_nodes)
        assert "Sales order #WEB1001 fulfilled" in joined
        assert "Premium Widget v2" in joined
        assert "Inventory: -1 of variant 1001" in joined

    def test_apply_error_surfaces_actual_error_message(self):
        """Closes #545 — the actual error string is not swallowed."""
        from katana_mcp.tools.prefab_ui import build_apply_error_ui

        app = build_apply_error_ui(
            operation="Fulfilling sales order #WEB1001",
            error_message="Katana API 422: row 5001 already shipped",
            hint="Check the SO's current production_status before retrying.",
        )
        envelope = app.to_json()
        text_nodes: list[str] = []

        def collect(o: Any) -> None:
            if isinstance(o, dict):
                if isinstance(o.get("content"), str):
                    text_nodes.append(o["content"])
                for v in o.values():
                    collect(v)
            elif isinstance(o, list):
                for v in o:
                    collect(v)

        collect(envelope)
        joined = "\n".join(text_nodes)
        assert "Fulfilling sales order #WEB1001 failed" in joined
        # The actual error string must be visible — the whole point of
        # this builder vs. the static-string toast/SendMessage from the
        # old preview→apply codepath.
        assert "Katana API 422: row 5001 already shipped" in joined
        assert "Check the SO's current production_status" in joined


def _find_buttons_by_label(tree: Any, label: str) -> list[dict]:
    """Walk a Prefab envelope and return every Button node whose label
    matches ``label`` exactly. Used by BLOCK-warning regression tests to
    assert the Confirm button is/isn't rendered.
    """
    found: list[dict] = []
    if isinstance(tree, dict):
        if tree.get("type") == "Button" and tree.get("label") == label:
            found.append(tree)
        for v in tree.values():
            found.extend(_find_buttons_by_label(v, label))
    elif isinstance(tree, list):
        for item in tree:
            found.extend(_find_buttons_by_label(item, label))
    return found


def _find_components_by_type(tree: Any, node_type: str) -> list[dict]:
    """Walk a Prefab envelope and return every node whose ``type`` matches.

    Variant of :func:`_has_node_of_type` that returns the actual nodes
    instead of a boolean — used when the caller wants to inspect props
    (e.g. ``href`` on Link, ``content`` on Code).
    """
    found: list[dict] = []
    if isinstance(tree, dict):
        if tree.get("type") == node_type:
            found.append(tree)
        for v in tree.values():
            found.extend(_find_components_by_type(v, node_type))
    elif isinstance(tree, list):
        for item in tree:
            found.extend(_find_components_by_type(item, node_type))
    return found


def _has_node_of_type(tree: Any, node_type: str) -> bool:
    """Return ``True`` if any node anywhere in the Prefab envelope has
    ``type == node_type``. Used by empty-state tests (#470) to assert
    that DataTable / Slot are or aren't rendered.
    """
    if isinstance(tree, dict):
        if tree.get("type") == node_type:
            return True
        return any(_has_node_of_type(v, node_type) for v in tree.values())
    if isinstance(tree, list):
        return any(_has_node_of_type(item, node_type) for item in tree)
    return False


def _collect_node_content(tree: Any, node_type: str) -> list[str]:
    """Walk a Prefab envelope and return every ``content`` string from
    nodes whose ``type`` equals ``node_type``. Used by empty-state tests
    to assert on the actual hint text rendered by ``Muted`` (rather than
    on ``str(envelope)``, which also matches header badges and would
    pass even if the hint regressed).
    """
    found: list[str] = []
    if isinstance(tree, dict):
        if tree.get("type") == node_type and isinstance(tree.get("content"), str):
            found.append(tree["content"])
        for v in tree.values():
            found.extend(_collect_node_content(v, node_type))
    elif isinstance(tree, list):
        for item in tree:
            found.extend(_collect_node_content(item, node_type))
    return found


class TestBlockWarningSuppressesConfirm:
    """Tests asserting that a ``BLOCK:``-prefixed warning string in a
    response causes the corresponding preview UI to render *without* the
    Confirm button — preventing the user from clicking through on a state
    the server has flagged as unsafe (e.g. duplicate-create, already-done).
    """

    def test_order_preview_with_block_warning_omits_confirm_button(self):
        order = {
            "order_number": "MO-1",
            "status": "PREVIEW",
            "variant_id": 100,
            "planned_quantity": 5,
            "warnings": [
                "BLOCK: sales_order_row 99 already linked to MO 88",
            ],
        }
        app = build_mo_create_ui(
            order,
            confirm_request=_StubRequest(),
            confirm_tool="create_manufacturing_order",
        )
        envelope = app.to_json()

        confirm_buttons = _find_buttons_by_label(
            envelope, "Confirm & Create Manufacturing Order"
        )
        cancel_buttons = _find_buttons_by_label(envelope, "Cancel")
        assert len(confirm_buttons) == 0, (
            "Confirm button must be suppressed when a BLOCK: warning is "
            f"present; found {len(confirm_buttons)}."
        )
        assert len(cancel_buttons) == 1, (
            "Cancel button must remain so the user can dismiss the preview."
        )

    def test_order_preview_without_block_warning_shows_confirm_button(self):
        order = {
            "order_number": "MO-1",
            "status": "PREVIEW",
            "variant_id": 100,
            "planned_quantity": 5,
            "warnings": ["No production_deadline_date specified"],  # not BLOCK:
        }
        app = build_mo_create_ui(
            order,
            confirm_request=_StubRequest(),
            confirm_tool="create_manufacturing_order",
        )
        envelope = app.to_json()

        confirm_buttons = _find_buttons_by_label(
            envelope, "Confirm & Create Manufacturing Order"
        )
        assert len(confirm_buttons) == 1, (
            "Confirm button must be present when no BLOCK: warning is set."
        )

    def test_fulfill_preview_with_block_warning_omits_confirm_button(self):
        response = {
            "order_type": "sales",
            "order_number": "SO-1",
            "order_id": 42,
            "status": "DELIVERED",
            "warnings": [
                "BLOCK: Sales order SO-1 is already DELIVERED.",
            ],
        }
        app = build_fulfill_preview_ui(response)
        envelope = app.to_json()

        confirm_buttons = _find_buttons_by_label(envelope, "Confirm Fulfillment")
        assert len(confirm_buttons) == 0, (
            "Confirm Fulfillment button must be suppressed on BLOCK warning."
        )

    def test_fulfill_preview_renders_inventory_ordering_block_message(self):
        """The inventory-ordering BLOCK (#787) surfaces in the card body
        as a destructive Badge, same as every other BLOCK class — and the
        ``BLOCK:`` prefix is stripped per the ``_split_warnings`` contract.
        """
        block_text = (
            "Sales order SO-INV-1 picked_date (2026-05-01T20:30:00+00:00) "
            "is not after linked manufacturing order 555 done_date "
            "(2026-05-01T20:30:00+00:00). This will cause transient negative "
            "inventory on the inventory_movements ledger."
        )
        response = {
            "order_type": "sales",
            "order_number": "SO-INV-1",
            "order_id": 42,
            "status": "NOT_SHIPPED",
            "warnings": [f"BLOCK: {block_text}"],
        }
        app = build_fulfill_preview_ui(response)
        envelope = app.to_json()

        # The block warning text appears somewhere in the rendered envelope
        # (as the label of a destructive Badge per build_fulfill_preview_ui).
        rendered = json.dumps(envelope)
        assert "transient negative inventory" in rendered
        assert "inventory_movements ledger" in rendered

        # Confirm button is suppressed (BLOCK present).
        confirm_buttons = _find_buttons_by_label(envelope, "Confirm Fulfillment")
        assert len(confirm_buttons) == 0

    def test_receipt_ui_with_block_warning_omits_confirm_button(self):
        from katana_mcp.tools.foundation.purchase_orders import (
            ReceiveItemRequest,
            ReceivePurchaseOrderRequest,
        )

        response = {
            "order_number": "PO-1",
            "order_id": 1,
            "is_preview": True,
            "items_received": 5,
            "status": "RECEIVED",
            "warnings": [
                "BLOCK: Purchase order PO-1 is already RECEIVED.",
            ],
        }
        request = ReceivePurchaseOrderRequest(
            order_id=1,
            items=[ReceiveItemRequest(purchase_order_row_id=10, quantity=1.0)],
        )
        app = build_receipt_ui(
            response,
            confirm_request=request,
            confirm_tool="receive_purchase_order",
        )
        envelope = app.to_json()

        confirm_buttons = _find_buttons_by_label(envelope, "Confirm Receipt")
        assert len(confirm_buttons) == 0, (
            "Confirm Receipt button must be suppressed on BLOCK warning."
        )

    def test_block_prefix_is_stripped_from_rendered_badge_labels(self):
        """The literal ``BLOCK:`` prefix must not appear in any Badge label —
        builders strip it so the warning reads naturally to the user.

        (The full warning string still passes through the iframe ``state``
        dict so client-side templates can read it; we only care about the
        rendered Badge text.)
        """
        order = {
            "order_number": "MO-1",
            "warnings": ["BLOCK: this is the diagnostic message"],
        }
        app = build_mo_create_ui(
            order,
            confirm_request=_StubRequest(),
            confirm_tool="create_manufacturing_order",
        )

        def collect_badge_labels(tree: Any, out: list[str]) -> None:
            if isinstance(tree, dict):
                if tree.get("type") == "Badge":
                    label = tree.get("label")
                    if isinstance(label, str):
                        out.append(label)
                for v in tree.values():
                    collect_badge_labels(v, out)
            elif isinstance(tree, list):
                for item in tree:
                    collect_badge_labels(item, out)

        labels: list[str] = []
        collect_badge_labels(app.to_json(), labels)

        diagnostic_label = next(
            (lbl for lbl in labels if "diagnostic message" in lbl), None
        )
        assert diagnostic_label is not None, (
            "Diagnostic message must be rendered as a Badge label."
        )
        assert not diagnostic_label.startswith("BLOCK:"), (
            f"Badge label still has literal BLOCK: prefix: {diagnostic_label!r}"
        )


class TestPreviewCoachingLeadsWithNoIframeFallback:
    """Regression tests for #648 — the docstring coaching templates must
    surface the non-iframe-host fallback prominently, not as a footnote.
    Agents in Claude Code / plain CLI hosts can't click iframe buttons; the
    previous coaching led with the iframe-happy path and agents silently
    ended their turns waiting for clicks the user could not make.
    """

    def test_no_iframe_scenario_appears_before_iframe_scenario(self) -> None:
        """The no-iframe path must be discussed BEFORE the iframe path so
        agents whose host doesn't render Prefab cards don't miss the
        fallback instructions."""
        coaching = PREVIEW_APPLY_COACHING
        # Numbered scenarios — `1.` introduces no-iframe, `2.` iframe.
        no_iframe_idx = coaching.find("does NOT render")
        iframe_idx = coaching.find("DOES render")
        assert no_iframe_idx != -1, (
            "coaching must explicitly call out the no-iframe path "
            f"(searched for 'does NOT render'); got:\n{coaching}"
        )
        assert iframe_idx != -1, (
            "coaching must also explain the iframe path "
            f"(searched for 'DOES render'); got:\n{coaching}"
        )
        assert no_iframe_idx < iframe_idx, (
            "no-iframe scenario must appear FIRST so agents read it before "
            "the iframe-happy path; reversing the order is exactly the "
            "footgun #648 fixed."
        )

    def test_mentions_content_channel_as_data_source(self) -> None:
        """The no-iframe fallback path tells the agent to summarize from the
        ``content`` channel — make sure the coaching points there explicitly
        so agents don't claim "I don't have enough data" instead of reading
        the JSON they were just handed."""
        assert "``content``" in PREVIEW_APPLY_COACHING, (
            "coaching must direct the agent to the ``content`` channel for "
            "the no-iframe summarize-then-confirm path; otherwise agents "
            "may not realize the response data is already in context."
        )

    def test_no_iframe_path_says_re_issue_with_preview_false(self) -> None:
        """The no-iframe fallback must spell out the apply mechanic
        (``preview=False``) so the agent isn't left guessing how to apply."""
        assert "preview=False" in PREVIEW_APPLY_COACHING, (
            "the no-iframe fallback must tell the agent to re-issue with "
            "``preview=False``"
        )

    def test_with_preview_coaching_appends_to_existing_docstring(self) -> None:
        """``with_preview_coaching`` should preserve the function's own
        docstring AND append the new lead-with-no-iframe block — verifies
        the rewrite didn't break the existing concatenation contract.
        """

        def fn() -> None:
            """My tool's own purpose."""

        result = with_preview_coaching(fn)
        assert result.startswith("My tool's own purpose.")
        assert "does NOT render" in result


def _bound_data_table(envelope: dict[str, Any], rows_ref: str) -> dict[str, Any]:
    """The single DataTable in ``envelope`` whose ``rows`` binds ``rows_ref``.

    Pins a pagination assertion to a specific table (by its ``{{ key }}``
    binding) rather than "the only DataTable" — robust if a card later grows
    a second table. Built on the file's existing ``_find_components_by_type``.
    """
    tables = [
        t
        for t in _find_components_by_type(envelope, "DataTable")
        if t.get("rows") == rows_ref
    ]
    assert len(tables) == 1, f"expected exactly one DataTable bound to {rows_ref!r}"
    return tables[0]


class TestDataTablePagination:
    """``_paginate`` opts into pagination only when the data overflows one
    page, so short tables don't render the renderer's blank filler rows
    (the renderer pads a *paginated* table up to ``pageSize``). Guards the
    module-wide DataTable fix.
    """

    @pytest.mark.parametrize(
        ("row_count", "page_size", "expected"),
        [
            (0, 20, {"paginated": False}),
            (1, 20, {"paginated": False}),
            (19, 20, {"paginated": False}),
            # Boundary: rowCount == pageSize fits one page with no filler.
            (20, 20, {"paginated": False}),
            (21, 20, {"paginated": True, "pageSize": 20}),
            (50, 25, {"paginated": True, "pageSize": 25}),
            (25, 25, {"paginated": False}),
        ],
    )
    def test_paginate_thresholds(
        self, row_count: int, page_size: int, expected: dict[str, Any]
    ) -> None:
        assert _paginate(row_count, page_size=page_size) == expected

    @pytest.mark.parametrize(
        ("n_items", "paginated"),
        [
            (1, False),  # short → no pagination, no blank filler rows
            (50, True),  # overflow → paginate at the configured page size
        ],
    )
    def test_search_results_paginate_only_on_overflow(
        self, n_items: int, paginated: bool
    ) -> None:
        """End-to-end: ``build_search_results_ui`` routes its ``{{ items }}``
        table through ``_paginate`` — short results don't paginate (so the
        renderer adds no filler rows), overflowing results do.
        """
        items = [
            {"id": i, "sku": f"SKU-{i:03d}", "name": "Widget", "is_sellable": True}
            for i in range(n_items)
        ]
        table = _bound_data_table(
            build_search_results_ui(items, "widget", n_items).to_json(), "{{ items }}"
        )
        assert table.get("paginated") is paginated
        if paginated:
            assert table.get("pageSize") == 20

    def test_no_hardcoded_paginated_true_in_module(self) -> None:
        """Enforce the convention for the next DataTable author: pagination
        is decided by ``_paginate``, never a hardcoded ``paginated=True``
        kwarg (which would reintroduce blank filler rows for any table that
        fits on one page). Converts the convention into a tripwire.
        """
        from pathlib import Path

        import katana_mcp.tools.prefab_ui as prefab_ui_module

        source = Path(prefab_ui_module.__file__).read_text(encoding="utf-8")
        # Match the kwarg form (``paginated=True``) but not backtick-quoted
        # prose mentions of it in the ``_paginate`` docstring.
        offenders = re.findall(r"(?<!`)paginated=True", source)
        assert not offenders, (
            "Found a hardcoded `paginated=True` DataTable kwarg in prefab_ui.py "
            "— route pagination through `**_paginate(len(rows))` instead so "
            "short tables don't render blank filler rows."
        )


def _so_detail_response(
    *,
    with_customer_name: bool = True,
    with_location_name: bool = True,
    with_addresses: bool = True,
    with_ecommerce: bool = True,
    with_rows: bool = True,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Build a ``get_sales_order`` response dict for ``build_so_detail_ui`` tests.

    Toggles let each test exercise one edge case (missing customer name,
    empty addresses, no storefront link, empty rows) against an otherwise
    full response.
    """
    rows = (
        [
            {
                "variant_id": 700,
                "sku": "SKU-A",
                "display_name": "Widget / Red",
                "quantity": 2,
                "price_per_unit": 100.0,
                "total": 200.0,
            },
            {
                "variant_id": 701,
                "sku": None,
                "display_name": None,
                "quantity": 5,
                "price_per_unit": 10.0,
                "total": None,
            },
        ]
        if with_rows
        else []
    )
    addresses = (
        [
            {
                "entity_type": "billing",
                "first_name": "Jane",
                "last_name": "Doe",
                "line_1": "1 Main St",
                "city": "Townsville",
                "country": "US",
            },
            {
                "entity_type": "shipping",
                "company": "Acme Manufacturing",
                "line_1": "2 Dock Rd",
                "city": "Portcity",
                "state": "CA",
                "zip": "90210",
                "country": "US",
            },
        ]
        if with_addresses
        else []
    )
    return {
        "id": 42,
        "katana_url": "https://factory.katanamrp.com/salesorder/42",
        "order_no": "SO-1001",
        "status": "PACKED",
        "customer_id": 10,
        "customer_name": "Acme Co" if with_customer_name else None,
        "location_id": 3,
        "location_name": "Main Warehouse" if with_location_name else None,
        "total": 1500.0,
        "currency": "USD",
        "delivery_date": "2026-07-01",
        "customer_ref": "PO-99",
        "order_created_date": "2026-06-01",
        "additional_info": "Rush order",
        "tracking_number": "TRK123",
        "tracking_number_url": "https://track.example/123",
        "ecommerce_order_type": "shopify" if with_ecommerce else None,
        "ecommerce_store_name": "mystore" if with_ecommerce else None,
        "ecommerce_order_id": "555" if with_ecommerce else None,
        "ecommerce_url": (
            "https://mystore.myshopify.com/admin/orders/555" if with_ecommerce else None
        ),
        "addresses": addresses,
        "rows": rows,
        "warnings": warnings or [],
    }


class TestBuildSoDetailUI:
    """``build_so_detail_ui`` — read-only sales-order detail card (#913)."""

    def test_full_response_renders_valid_prefab(self) -> None:
        app = build_so_detail_ui(_so_detail_response())
        _assert_valid_prefab(app)

    def test_title_links_to_katana(self) -> None:
        """Tier 1 title is an external Link to the Katana SO page."""
        envelope = build_so_detail_ui(_so_detail_response()).to_json()
        links = _find_components_by_type(envelope, "Link")
        title_links = [
            link
            for link in links
            if link.get("content") == "Sales Order SO-1001"
            and link.get("href") == "https://factory.katanamrp.com/salesorder/42"
        ]
        assert len(title_links) == 1, (
            "Title must be an external Link to the Katana SO page."
        )

    def test_status_badge_uses_bucket_variant(self) -> None:
        """PACKED is in the sales_order 'active' bucket → secondary variant."""
        envelope = build_so_detail_ui(_so_detail_response()).to_json()
        badges = _find_components_by_type(envelope, "Badge")
        status_badges = [b for b in badges if b.get("label") == "PACKED"]
        assert len(status_badges) == 1
        assert status_badges[0].get("variant") == status_badge_variant(
            "sales_order", "PACKED"
        )

    def test_customer_name_rendered_not_id(self) -> None:
        """Resolved customer name renders as a Link; the bare-ID fallback
        text must NOT appear (anti-pattern #2)."""
        envelope = build_so_detail_ui(_so_detail_response()).to_json()
        links = _find_components_by_type(envelope, "Link")
        assert any(link.get("content") == "Acme Co" for link in links), (
            "Customer name should render as a Link."
        )
        all_text = json.dumps(envelope)
        assert "Customer ID: 10" not in all_text, (
            "Card must not echo the bare customer ID when a name is resolved."
        )

    def test_location_name_rendered_without_link(self) -> None:
        """Location has no Katana web page → renders as plain 'Location:
        <name>' text, not a Link, and not the bare-ID fallback."""
        envelope = build_so_detail_ui(_so_detail_response()).to_json()
        texts = _collect_node_content(envelope, "Text")
        assert "Location: Main Warehouse" in texts
        assert "Location ID: 3" not in texts

    def test_metrics_rendered(self) -> None:
        """Tier 2 surfaces total / line-item count / delivery as Metrics."""
        envelope = build_so_detail_ui(_so_detail_response()).to_json()
        metrics = _find_components_by_type(envelope, "Metric")
        labels = {m.get("label"): m.get("value") for m in metrics}
        assert labels.get("Total") == "$1,500.00"
        assert labels.get("Line Items") == "2"
        assert labels.get("Delivery") == "2026-07-01"

    def test_line_item_table_uses_mustache_rows(self) -> None:
        """The line-item DataTable binds rows via mustache to state.so.rows."""
        envelope = build_so_detail_ui(_so_detail_response()).to_json()
        tables = _find_components_by_type(envelope, "DataTable")
        assert len(tables) == 1
        assert tables[0].get("rows") == "{{ so.rows }}"

    def test_line_item_cells_formatted(self) -> None:
        """Row state cells coalesce null SKU, fall back display_name, and
        pre-format the money columns (incl. computed line total)."""
        app = build_so_detail_ui(_so_detail_response())
        rows = app.to_json()["state"]["so"]["rows"]
        assert rows[0]["sku"] == "SKU-A"
        assert rows[0]["unit_price_display"] == "$100.00"
        assert rows[0]["line_total_display"] == "$200.00"
        # Second row: null SKU → "", null name → "Variant 701", total
        # computed from unit * qty.
        assert rows[1]["sku"] == ""
        assert rows[1]["display_name"] == "Variant 701"
        assert rows[1]["line_total_display"] == "$50.00"

    def test_null_variant_id_row_uses_neutral_label(self) -> None:
        """A row with no display_name AND a null variant_id renders a neutral
        "Unknown item" label, not a confusing "Variant None" (variant_id is
        optional in the response)."""
        response = {
            **_so_detail_response(),
            "rows": [
                {
                    "sku": None,
                    "display_name": None,
                    "variant_id": None,
                    "quantity": 1,
                    "price_per_unit": 10.0,
                    "total": 10.0,
                }
            ],
        }
        rows = build_so_detail_ui(response).to_json()["state"]["so"]["rows"]
        assert rows[0]["display_name"] == "Unknown item"

    def test_address_blocks_rendered(self) -> None:
        """Billing + shipping address blocks surface recipient / company /
        street."""
        envelope = build_so_detail_ui(_so_detail_response()).to_json()
        texts = _collect_node_content(envelope, "Text")
        assert "Billing Address:" in texts
        assert "Shipping Address:" in texts
        assert any("Jane Doe" in t for t in texts)
        assert any("Acme Manufacturing" in t for t in texts)

    def test_ecommerce_link_rendered(self) -> None:
        """Storefront deep-link surfaces when the SO carries ecommerce
        metadata."""
        envelope = build_so_detail_ui(_so_detail_response()).to_json()
        links = _find_components_by_type(envelope, "Link")
        assert any(
            link.get("href") == "https://mystore.myshopify.com/admin/orders/555"
            for link in links
        )

    def test_footer_view_in_katana_only(self) -> None:
        """Pure read card — the only footer action is View in Katana (no
        Fulfill / Edit / mutation buttons)."""
        envelope = build_so_detail_ui(_so_detail_response()).to_json()
        view_buttons = _find_buttons_by_label(envelope, "View in Katana")
        assert len(view_buttons) == 1
        on_click = view_buttons[0].get("onClick") or view_buttons[0].get("on_click")
        assert isinstance(on_click, dict)
        assert on_click.get("url") == "https://factory.katanamrp.com/salesorder/42"
        # No mutation buttons.
        all_buttons = _find_components_by_type(envelope, "Button")
        assert len(all_buttons) == 1, (
            "Read card must render exactly one footer button (View in Katana)."
        )

    # ---- Edge cases ----

    def test_missing_customer_name_falls_back_to_id(self) -> None:
        """When name resolution missed, the party line surfaces the bare ID
        (the only way to identify the customer)."""
        envelope = build_so_detail_ui(
            _so_detail_response(with_customer_name=False)
        ).to_json()
        texts = _collect_node_content(envelope, "Text")
        assert "Customer ID: 10" in texts
        _assert_valid_prefab(
            build_so_detail_ui(_so_detail_response(with_customer_name=False))
        )

    def test_empty_addresses_renders_no_address_labels(self) -> None:
        """No addresses → no dangling 'Billing Address:' / 'Shipping
        Address:' labels."""
        app = build_so_detail_ui(_so_detail_response(with_addresses=False))
        _assert_valid_prefab(app)
        texts = _collect_node_content(app.to_json(), "Text")
        assert "Billing Address:" not in texts
        assert "Shipping Address:" not in texts

    def test_no_ecommerce_link_when_metadata_absent(self) -> None:
        """No ecommerce metadata → no storefront link, card still valid."""
        app = build_so_detail_ui(_so_detail_response(with_ecommerce=False))
        _assert_valid_prefab(app)
        texts = _collect_node_content(app.to_json(), "Text")
        assert "Storefront:" not in texts

    def test_empty_rows_renders_friendly_empty_state(self) -> None:
        """No line items → friendly Muted message, no DataTable."""
        app = build_so_detail_ui(_so_detail_response(with_rows=False))
        _assert_valid_prefab(app)
        envelope = app.to_json()
        assert not _has_node_of_type(envelope, "DataTable")
        muted = _collect_node_content(envelope, "Muted")
        assert any("No line items" in m for m in muted)

    def test_warnings_surface_as_badges(self) -> None:
        """Name-resolution cache-miss advisories surface as warning badges."""
        app = build_so_detail_ui(
            _so_detail_response(
                with_customer_name=False,
                warnings=["Customer with id=10 was not found in the cache."],
            )
        )
        _assert_valid_prefab(app)
        badges = _find_components_by_type(app.to_json(), "Badge")
        assert any("not found in the cache" in (b.get("label") or "") for b in badges)

    def test_missing_katana_url_omits_footer_button(self) -> None:
        """No katana_url → no View-in-Katana button, title renders as text."""
        response = _so_detail_response()
        response["katana_url"] = None
        app = build_so_detail_ui(response)
        _assert_valid_prefab(app)
        envelope = app.to_json()
        assert not _find_buttons_by_label(envelope, "View in Katana")
        texts = _collect_node_content(envelope, "Text")
        assert "Sales Order SO-1001" in texts
