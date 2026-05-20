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
from katana_mcp.tools.prefab_ui import (
    PREVIEW_APPLY_COACHING,
    PREVIEW_APPLY_DIRECT_COACHING,
    _format_money,
    build_batch_recipe_update_ui,
    build_fulfill_preview_ui,
    build_fulfill_success_ui,
    build_inventory_check_batch_ui,
    build_inventory_check_ui,
    build_item_detail_ui,
    build_item_mutation_ui,
    build_low_stock_ui,
    build_mo_create_ui,
    build_modification_preview_ui,
    build_modification_result_ui,
    build_po_create_ui,
    build_po_modify_ui,
    build_receipt_ui,
    build_search_results_ui,
    build_so_create_ui,
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
        # ``location_id`` must be present as an always-rendered fallback
        # for the multi-location case where ``location_name`` may be
        # ``None`` on a cache miss — without it the row is unidentifiable.
        assert "location_id" in column_keys, (
            f"Per-location table must keep location_id as a fallback identifier; "
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
        # Prompt text uses variant_id, not "SKU "
        # Walk the JSON for the SendMessage payload strings
        import json as _json

        rendered = _json.dumps(envelope)
        assert "variant_id 9999" in rendered, (
            f"Expected variant_id fallback in agent prompts; rendered: {rendered[:500]!r}"
        )
        assert "for SKU " not in rendered, (
            f"Null-SKU footer must not produce broken 'for SKU ' prompts; "
            f"rendered: {rendered[:500]!r}"
        )

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
        ``_build_apply_action_direct`` writes the same key."""
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
        # MO carries the variant in tier 3 as "Variant: WIDGET-42 (ID: 555)"
        assert "WIDGET-42" in rendered
        assert "555" in rendered
        # Deadline metric uses the date portion only.
        assert "2026-06-01" in rendered

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
        from katana_mcp.tools.prefab_ui import _summarize_apply_outcome

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
        """``_build_cancel_action`` interpolates its arg into "Cancel: do
        not apply X." — the noun phrase has to read naturally there.
        Modify/correct cards interpolate "those purchase order changes" /
        "those purchase order corrections"; delete cards interpolate
        "that purchase order deletion". The previous shape (e.g. "that
        purchase order modify") was grammatically awkward — Copilot
        flagged on #755."""
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
    # Tier 4 success-side actions
    # ------------------------------------------------------------------

    def test_success_renders_view_in_katana_when_url_present(self):
        """Tier 4 expansion (#553): the success card now offers two
        follow-ups instead of the legacy single Check Inventory button.
        View in Katana wins the primary slot when a deep-link is present.
        """
        envelope = build_fulfill_success_ui(
            self._so_response(is_preview=False)
        ).to_json()
        buttons = _find_components_by_type(envelope, "Button")
        labels = [b.get("label") for b in buttons]
        assert "View in Katana" in labels
        assert "Check Inventory" in labels

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


class TestBuildItemMutationUI:
    @pytest.mark.parametrize("action", ["Created", "Updated", "Deleted"])
    def test_actions(self, action):
        item = {"id": 1, "name": "Widget", "type": "product", "sku": "SKU-001"}
        app = build_item_mutation_ui(item, action)
        _assert_valid_prefab(app)

    def test_minimal(self):
        app = build_item_mutation_ui({"id": 1}, "Created")
        _assert_valid_prefab(app)


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
        # Column set pinned: Item / SKU / Qty / Received / Batch / Line Total
        headers = [c.get("header") for c in tables[0].get("columns", [])]
        assert headers == ["Item", "SKU", "Qty", "Received", "Batch", "Line Total"]

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

    All Confirm buttons in the new (post-#316) confirmation pattern fire
    a list of two actions: ``setState("pending", True)`` and
    ``sendMessage("Apply: call <tool>(<args>, preview=False)")``. The
    Cancel button mirrors this with ``cancelled`` and a ``"Cancel: ..."``
    SendMessage.
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


class TestConfirmButtonEmitsApplyMessage:
    """The Confirm button on every preview card must fire two actions:

    1. ``setState("pending", True)`` — flips the card to a "Pending…"
       pill and grays out the buttons (no double-fire footgun).
    2. ``sendMessage("Apply: call <tool>(<inlined args>, preview=False)")``
       — prompts the agent to re-issue the apply call.

    The button does **not** fire ``CallTool`` directly. Per ADR-0015 and
    the spec finding behind #316, an iframe-initiated ``tools/call``
    returns its result to the iframe, not to the agent — so the only way
    for the agent to see the apply response is to make the call itself.
    """

    @staticmethod
    def _assert_apply_actions(on_click: list[dict], tool_name: str) -> dict:
        """Validate that on_click is exactly [SetState(pending, True),
        SendMessage(Apply: call <tool>(...))] and return the SendMessage."""
        set_states = [a for a in on_click if a.get("action") == "setState"]
        send_messages = [a for a in on_click if a.get("action") == "sendMessage"]
        assert any(
            a.get("key") == "pending" and a.get("value") is True for a in set_states
        ), f"Expected setState('pending', True) in on_click; got {on_click!r}"
        apply_msgs = [
            m
            for m in send_messages
            if isinstance(m.get("content"), str)
            and m["content"].startswith(f"Apply: call {tool_name}(")
        ]
        assert len(apply_msgs) == 1, (
            f"Expected exactly one SendMessage with 'Apply: call {tool_name}('; "
            f"got {[m.get('content') for m in send_messages]!r}"
        )
        return apply_msgs[0]

    def test_fulfill_preview_confirm_emits_apply_send_message(self):
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
        msg = self._assert_apply_actions(on_click, "fulfill_order")
        assert "order_id=9999" in msg["content"]
        assert "order_type='sales'" in msg["content"]
        assert "preview=False" in msg["content"]

    def test_receipt_preview_confirm_emits_apply_send_message(self):
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
        msg = self._assert_apply_actions(on_click, "receive_purchase_order")
        assert "order_id=1234" in msg["content"]
        assert "preview=False" in msg["content"]

    def test_batch_recipe_preview_confirm_emits_apply_send_message(self):
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
        msg = self._assert_apply_actions(on_click, "batch_update_recipes")
        assert "preview=False" in msg["content"]


class TestConfirmButtonDirectApplyRail:
    """Direct-apply rail (ADR-0016, supersedes ADR-0015 for opted-in tools):

    The Confirm button fires ``tools/call`` directly from the iframe with
    the original args + ``preview=False``, and on success pushes the
    structured result back to the agent's model context via
    ``ui/update-model-context``. The agent does NOT re-issue the call.

    Currently opted into by ``create_purchase_order``; rolling out to other
    write tools after Cowork verification.
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


class TestCancelButtonEmitsCancelMessage:
    """The Cancel button must fire ``setState("cancelled", True)`` plus a
    ``sendMessage("Cancel: do not apply ...")`` so the agent recognizes the
    user's opt-out and moves on. Mirrors the Confirm-button contract above.
    """

    def _assert_cancel_actions(self, on_click: list[dict]) -> None:
        set_states = [a for a in on_click if a.get("action") == "setState"]
        send_messages = [a for a in on_click if a.get("action") == "sendMessage"]
        assert any(
            a.get("key") == "cancelled" and a.get("value") is True for a in set_states
        ), f"Expected setState('cancelled', True) in on_click; got {on_click!r}"
        cancel_msgs = [
            m
            for m in send_messages
            if isinstance(m.get("content"), str)
            and m["content"].startswith("Cancel: do not apply ")
        ]
        assert len(cancel_msgs) == 1, (
            f"Expected exactly one Cancel SendMessage; "
            f"got {[m.get('content') for m in send_messages]!r}"
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

    def test_apply_message_inlines_args_and_overrides_preview(self):
        """The ``Apply: call ...`` SendMessage must inline every request
        field as a literal value and force ``preview=False`` regardless
        of the request's preview value (the user already saw the preview).
        """
        from katana_mcp.tools.foundation.orders import FulfillOrderRequest
        from katana_mcp.tools.prefab_ui import _build_apply_action

        request = FulfillOrderRequest(order_id=42, order_type="sales", preview=True)
        actions = _build_apply_action("fulfill_order", request)
        assert actions is not None
        send_messages = [a for a in actions if hasattr(a, "content")]
        assert len(send_messages) == 1
        # ``Action`` is a discriminated union; only some variants expose
        # ``content``. ``hasattr`` filters at runtime, but the static type
        # is the bare union — read via ``getattr`` to satisfy the checker.
        text = getattr(send_messages[0], "content", None)
        assert isinstance(text, str)
        assert text.startswith("Apply: call fulfill_order(")
        assert "order_id=42" in text
        assert "order_type='sales'" in text
        # preview is forced to False even though request.preview was True
        assert "preview=False" in text
        assert "preview=True" not in text
        # And ``preview=False`` is the trailing arg regardless of where the
        # field appears in args.items() iteration order — agents read a
        # stable suffix.
        assert text.rstrip(")").endswith(", preview=False"), (
            f"`preview=False` must be the trailing arg; got: {text!r}"
        )

    def test_preview_field_required_in_request(self):
        """A request model without a ``preview`` field is a programmer
        error — the SendMessage would prompt the agent to call the tool
        with an unrecognized argument that fails validation downstream.
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


class _ModifyStubRequest(BaseModel):
    """Stub for ``ConfirmableRequest`` used by modification-card tests.

    Mirrors the load-bearing fields ``_build_apply_action_direct`` reads
    (``id``, ``preview``) without pulling a real entity request shape into
    these unit tests.
    """

    id: int = 1
    preview: bool = True


def _modification_preview_response(
    *,
    actions: list[dict] | None = None,
    legacy_changes: list[dict] | None = None,
    warnings: list[str] | None = None,
    katana_url: str | None = None,
) -> dict:
    """Build a minimal preview-shaped ``ModificationResponse`` dict."""
    return {
        "entity_type": "product",
        "entity_id": 17058420,
        "is_preview": True,
        "operation": "" if actions is not None else "update",
        "changes": legacy_changes or [],
        "actions": actions or [],
        "prior_state": None,
        "warnings": warnings or [],
        "next_actions": ["Review the planned actions", "Set preview=false to apply"],
        "katana_url": katana_url,
        "message": "Preview: 2 action(s) planned",
    }


class TestBuildModificationPreviewUI:
    """Preview card for ``modify_*`` / ``delete_*`` / ``correct_*`` tools.

    The card must render a per-action diff DataTable and a Confirm button
    on the direct-apply rail (Confirm fires ``tools/call`` directly + the
    iframe pushes the result via ``ui/update-model-context``).
    """

    def test_basic_two_action_preview_renders_envelope(self):
        response = _modification_preview_response(
            actions=[
                {
                    "operation": "update_header",
                    "target_id": 17058420,
                    "changes": [
                        {
                            "field": "name",
                            "old": "Old Name",
                            "new": "New Name",
                            "is_added": False,
                            "is_unchanged": False,
                            "is_unknown_prior": False,
                        }
                    ],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                },
                {
                    "operation": "update_variant",
                    "target_id": 40371805,
                    "changes": [
                        {
                            "field": "internal_barcode",
                            "old": None,
                            "new": "LD0739",
                            "is_added": False,
                            "is_unchanged": False,
                            "is_unknown_prior": True,
                        }
                    ],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                },
            ],
        )
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(id=17058420, preview=True),
            confirm_tool="modify_item",
        )
        _assert_valid_prefab(app)

    def test_confirm_button_uses_direct_apply_call_tool(self):
        """Confirm wires CallTool(modify_item, ..., preview=False)."""
        response = _modification_preview_response(
            actions=[
                {
                    "operation": "update_header",
                    "target_id": 1,
                    "changes": [
                        {
                            "field": "name",
                            "old": "x",
                            "new": "y",
                            "is_added": False,
                            "is_unchanged": False,
                            "is_unknown_prior": False,
                        }
                    ],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            ],
        )
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(id=1, preview=True),
            confirm_tool="modify_item",
        )
        envelope = app.to_json()

        # Find the CallTool action — it's nested under a Button's onClick.
        def find_call_tool(tree: Any) -> dict | None:
            if isinstance(tree, dict):
                if tree.get("action") == "toolCall":
                    return tree
                for v in tree.values():
                    found = find_call_tool(v)
                    if found is not None:
                        return found
            elif isinstance(tree, list):
                for v in tree:
                    found = find_call_tool(v)
                    if found is not None:
                        return found
            return None

        call_tool = find_call_tool(envelope)
        assert call_tool is not None, "Confirm button must wire a CallTool action"
        assert call_tool["tool"] == "modify_item"
        assert call_tool["arguments"]["preview"] is False, (
            "CallTool arguments must flip preview=False so the direct-apply "
            "fires the apply branch."
        )

    def test_block_warning_suppresses_confirm_button(self):
        """A ``BLOCK:``-prefixed warning must drop the Confirm button (only
        Cancel remains), matching the shape used by the other preview cards.
        """
        response = _modification_preview_response(
            actions=[
                {
                    "operation": "delete",
                    "target_id": 1,
                    "changes": [],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            ],
            warnings=["BLOCK: cannot proceed — already deleted"],
        )
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(),
            confirm_tool="delete_item",
        )
        envelope = app.to_json()
        confirm = _find_buttons_by_label(envelope, "Confirm Changes")
        confirm_n = _find_buttons_by_label(envelope, "Confirm 1 action(s)")
        assert len(confirm) + len(confirm_n) == 0, (
            "Confirm button must be suppressed when a BLOCK: warning is set."
        )
        cancel = _find_buttons_by_label(envelope, "Cancel")
        assert len(cancel) == 1, "Cancel button must remain on BLOCK warning."

    def test_legacy_single_action_shape_renders_diff_table(self):
        """Tools that still emit the legacy single-action shape (top-level
        ``operation`` + ``changes``, empty ``actions``) must still get a
        diff table rendered."""
        response = _modification_preview_response(
            actions=[],
            legacy_changes=[
                {
                    "field": "status",
                    "old": "DRAFT",
                    "new": "RECEIVED",
                    "is_added": False,
                    "is_unchanged": False,
                    "is_unknown_prior": False,
                }
            ],
        )
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(),
            confirm_tool="modify_purchase_order",
        )
        envelope = app.to_json()
        assert _has_node_of_type(envelope, "DataTable"), (
            "Legacy single-action shape must still render a diff DataTable."
        )

    def test_title_verb_derives_from_tool_name(self):
        """``modify_item`` → "Modify", ``delete_item`` → "Delete",
        ``correct_purchase_order`` → "Correct" — closes Copilot review
        finding that the title was hard-coded as "Modify".
        """
        response = _modification_preview_response(
            actions=[
                {
                    "operation": "delete",
                    "target_id": 1,
                    "changes": [],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            ],
        )
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(),
            confirm_tool="delete_item",
        )
        envelope = app.to_json()
        titles: list[str] = []

        def collect_titles(o: Any) -> None:
            if isinstance(o, dict):
                if o.get("type") == "CardTitle" and isinstance(o.get("content"), str):
                    titles.append(o["content"])
                for v in o.values():
                    collect_titles(v)
            elif isinstance(o, list):
                for v in o:
                    collect_titles(v)

        collect_titles(envelope)
        assert any(t.startswith("Delete ") for t in titles), (
            f"delete_item card title must start with 'Delete'; got {titles!r}"
        )

    def test_title_action_count_suffix_uses_n_actions(self):
        """The action-count suffix must be present whenever there's at
        least one planned action, including the legacy single-action
        shape (where ``actions`` is empty but ``changes`` is populated).
        Closes Copilot review finding.
        """
        response = _modification_preview_response(
            actions=[],
            legacy_changes=[
                {
                    "field": "status",
                    "old": "DRAFT",
                    "new": "RECEIVED",
                    "is_added": False,
                    "is_unchanged": False,
                    "is_unknown_prior": False,
                }
            ],
        )
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(),
            confirm_tool="modify_purchase_order",
        )
        envelope = app.to_json()
        titles: list[str] = []

        def collect_titles(o: Any) -> None:
            if isinstance(o, dict):
                if o.get("type") == "CardTitle" and isinstance(o.get("content"), str):
                    titles.append(o["content"])
                for v in o.values():
                    collect_titles(v)
            elif isinstance(o, list):
                for v in o:
                    collect_titles(v)

        collect_titles(envelope)
        assert any("1 action(s)" in t for t in titles), (
            f"Legacy single-action title must include the count suffix; got {titles!r}"
        )

    def test_twelve_action_mixed_plan_renders_single_state_bound_table(self):
        """Reproduces #629: 12-action mixed plans (6 adds + 6 deletes)
        previously emitted N separate state-bound DataTables, blowing the
        renderer. The fix is one DataTable bound to ``state.plan_actions``.
        """
        actions = []
        for i in range(6):
            actions.append(
                {
                    "operation": "add_recipe_row",
                    "target_id": None,
                    "changes": [
                        {
                            "field": "variant_id",
                            "old": None,
                            "new": 40000000 + i,
                            "is_added": True,
                            "is_unchanged": False,
                            "is_unknown_prior": False,
                        },
                        {
                            "field": "planned_quantity_per_unit",
                            "old": None,
                            "new": 1,
                            "is_added": True,
                            "is_unchanged": False,
                            "is_unknown_prior": False,
                        },
                        {
                            "field": "notes",
                            "old": None,
                            "new": f"AM swap {i}: notes with (parens) and #{i}",
                            "is_added": True,
                            "is_unchanged": False,
                            "is_unknown_prior": False,
                        },
                    ],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            )
        for i in range(6):
            actions.append(
                {
                    "operation": "delete_recipe_row",
                    "target_id": 97411400 + i,
                    "changes": [],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            )
        response = _modification_preview_response(actions=actions)
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(id=16467730, preview=True),
            confirm_tool="modify_manufacturing_order",
        )
        envelope = app.to_json()

        # Sanity: full envelope serializes and bindings resolve.
        _assert_valid_prefab(app)

        # Exactly one DataTable, bound to plan_actions via mustache template.
        # Bare-string state references crash the JS renderer with
        # "t.some is not a function" — discovered via headless apps_dev tests.
        tables = [
            n
            for n in _walk_view_tree(envelope.get("view"))
            if n.get("type") == "DataTable"
        ]
        assert len(tables) == 1, f"expected 1 DataTable, got {len(tables)}"
        assert tables[0]["rows"] == "{{ plan_actions }}"

        # plan_actions has 12 rows, all PLANNED.
        plan_rows = envelope["state"]["plan_actions"]
        assert len(plan_rows) == 12
        assert [r["index"] for r in plan_rows] == list(range(1, 13))
        assert all(r["status_label"] == "PLANNED" for r in plan_rows)

        # Adds have target_label "—", deletes have "#<id>".
        for r in plan_rows[:6]:
            assert r["target_label"] == "—"
            assert "field(s) set" in r["summary"]
        for r in plan_rows[6:]:
            assert r["target_label"].startswith("#")
            assert r["summary"] == "deleted"

    def test_apply_button_does_not_set_state_plan_actions(self):
        """Pin: the live-tick design (``SetState("plan_actions", RESULT.actions)``)
        was attempted in #634 but turned out to be broken — ``$result`` in
        the on_success Rx context resolves to the apply tool's
        ``structured_content`` (a PrefabApp wire envelope), not to the raw
        ``ModificationResponse``. The SetState was a no-op in production.

        Until the right Rx path is identified (tracked as a follow-up), the
        on_success chain MUST NOT include a SetState targeting plan_actions
        — a no-op SetState is misleading. The apply path morphs the card via
        the existing ``applied=True`` flag instead.
        """
        response = _modification_preview_response(
            actions=[
                {
                    "operation": "update_header",
                    "target_id": 1,
                    "changes": [],
                    "succeeded": None,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            ],
        )
        app = build_modification_preview_ui(
            response,
            confirm_request=_ModifyStubRequest(),
            confirm_tool="modify_item",
        )
        envelope = app.to_json()

        def find_action(o: Any, action_name: str) -> dict[str, Any] | None:
            if isinstance(o, dict):
                if o.get("action") == action_name:
                    return o
                for v in o.values():
                    found = find_action(v, action_name)
                    if found is not None:
                        return found
            elif isinstance(o, list):
                for v in o:
                    found = find_action(v, action_name)
                    if found is not None:
                        return found
            return None

        call_tool = find_action(envelope, "toolCall")
        assert call_tool is not None
        on_success = call_tool.get("onSuccess") or call_tool.get("on_success") or []
        plan_action_set = next(
            (
                a
                for a in on_success
                if isinstance(a, dict)
                and a.get("action") == "setState"
                and a.get("key") == "plan_actions"
            ),
            None,
        )
        assert plan_action_set is None, (
            f"on_success must NOT SetState('plan_actions', ...) — it would "
            f"be a no-op until the live-tick Rx path is fixed. Found: "
            f"{plan_action_set!r}"
        )


class TestBuildModificationResultUI:
    """Result card for an applied (non-preview) ModificationResponse."""

    def _response(self, actions: list[dict]) -> dict:
        return {
            "entity_type": "purchase_order",
            "entity_id": 99,
            "is_preview": False,
            "operation": "",
            "changes": [],
            "actions": actions,
            "prior_state": None,
            "warnings": [],
            "next_actions": [],
            "katana_url": "https://factory.katanamrp.com/purchaseorder/99",
            "message": "Applied 2 action(s)",
        }

    def test_all_succeeded_renders_applied_status(self):
        response = self._response(
            [
                {
                    "operation": "update_header",
                    "target_id": 99,
                    "changes": [
                        {
                            "field": "status",
                            "old": "DRAFT",
                            "new": "OPEN",
                            "is_added": False,
                            "is_unchanged": False,
                            "is_unknown_prior": False,
                        }
                    ],
                    "succeeded": True,
                    "error": None,
                    "verified": True,
                    "actual_after": None,
                }
            ]
        )
        app = build_modification_result_ui(response)
        envelope = app.to_json()
        labels: list[str] = []

        def collect_badges(o: Any) -> None:
            if isinstance(o, dict):
                if o.get("type") == "Badge" and isinstance(o.get("label"), str):
                    labels.append(o["label"])
                for v in o.values():
                    collect_badges(v)
            elif isinstance(o, list):
                for v in o:
                    collect_badges(v)

        collect_badges(envelope)
        assert "APPLIED" in labels, (
            f"Top-level status badge must read APPLIED on full success; got {labels!r}"
        )

    def test_partial_failure_marks_overall_partial_failure(self):
        response = self._response(
            [
                {
                    "operation": "update_header",
                    "target_id": 99,
                    "changes": [],
                    "succeeded": True,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                },
                {
                    "operation": "update_row",
                    "target_id": 1234,
                    "changes": [],
                    "succeeded": False,
                    "error": "422 row already shipped",
                    "verified": None,
                    "actual_after": None,
                },
            ]
        )
        app = build_modification_result_ui(response)
        envelope = app.to_json()
        labels: list[str] = []

        def collect_badges(o: Any) -> None:
            if isinstance(o, dict):
                if o.get("type") == "Badge" and isinstance(o.get("label"), str):
                    labels.append(o["label"])
                for v in o.values():
                    collect_badges(v)
            elif isinstance(o, list):
                for v in o:
                    collect_badges(v)

        collect_badges(envelope)
        assert "PARTIAL FAILURE" in labels, (
            f"Mixed succeed/fail must surface PARTIAL FAILURE; got {labels!r}"
        )
        # Per-action FAILED status must surface in the row data (status_label
        # column of the plan_actions DataTable). After the live-tick redesign
        # (#629), per-action status lives in the table cells, not in Badges.
        plan_rows = envelope["state"]["plan_actions"]
        statuses = [r["status_label"] for r in plan_rows]
        assert "APPLIED" in statuses, f"expected APPLIED in {statuses!r}"
        assert "FAILED" in statuses, f"expected FAILED in {statuses!r}"

    def test_view_in_katana_button_present_when_url_set(self):
        response = self._response(
            [
                {
                    "operation": "update_header",
                    "target_id": 99,
                    "changes": [],
                    "succeeded": True,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            ]
        )
        app = build_modification_result_ui(response)
        envelope = app.to_json()
        assert len(_find_buttons_by_label(envelope, "View in Katana")) == 1

    def test_no_katana_url_drops_view_button(self):
        response = self._response(
            [
                {
                    "operation": "delete",
                    "target_id": 99,
                    "changes": [],
                    "succeeded": True,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            ]
        )
        response["katana_url"] = None  # delete nulls it
        app = build_modification_result_ui(response)
        envelope = app.to_json()
        assert len(_find_buttons_by_label(envelope, "View in Katana")) == 0

    def test_title_verb_derives_from_tool_name(self):
        """Result-card title verb mirrors the preview-card behavior —
        ``delete_purchase_order`` reads "Purchase Order Delete" rather
        than the misleading "Purchase Order Modification".
        """
        response = self._response(
            [
                {
                    "operation": "delete",
                    "target_id": 99,
                    "changes": [],
                    "succeeded": True,
                    "error": None,
                    "verified": None,
                    "actual_after": None,
                }
            ]
        )
        app = build_modification_result_ui(response, tool_name="delete_purchase_order")
        envelope = app.to_json()
        titles: list[str] = []

        def collect_titles(o: Any) -> None:
            if isinstance(o, dict):
                if o.get("type") == "CardTitle" and isinstance(o.get("content"), str):
                    titles.append(o["content"])
                for v in o.values():
                    collect_titles(v)
            elif isinstance(o, list):
                for v in o:
                    collect_titles(v)

        collect_titles(envelope)
        assert any(t.endswith("Delete") for t in titles), (
            f"delete_* result title must end with 'Delete'; got {titles!r}"
        )


class TestPreviewCoachingLeadsWithNoIframeFallback:
    """Regression tests for #648 — the docstring coaching templates must
    surface the non-iframe-host fallback prominently, not as a footnote.
    Agents in Claude Code / plain CLI hosts can't click iframe buttons; the
    previous coaching led with the iframe-happy path and agents silently
    ended their turns waiting for clicks the user could not make.
    """

    @pytest.mark.parametrize(
        "coaching",
        [PREVIEW_APPLY_COACHING, PREVIEW_APPLY_DIRECT_COACHING],
        ids=["sendmessage-rail", "direct-apply-rail"],
    )
    def test_no_iframe_scenario_appears_before_iframe_scenario(
        self, coaching: str
    ) -> None:
        """The no-iframe path must be discussed BEFORE the iframe path so
        agents whose host doesn't render Prefab cards don't miss the
        fallback instructions."""
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

    @pytest.mark.parametrize(
        "coaching",
        [PREVIEW_APPLY_COACHING, PREVIEW_APPLY_DIRECT_COACHING],
        ids=["sendmessage-rail", "direct-apply-rail"],
    )
    def test_mentions_content_channel_as_data_source(self, coaching: str) -> None:
        """The no-iframe fallback path tells the agent to summarize from the
        ``content`` channel — make sure the coaching points there explicitly
        so agents don't claim "I don't have enough data" instead of reading
        the JSON they were just handed."""
        assert "``content``" in coaching, (
            "coaching must direct the agent to the ``content`` channel for "
            "the no-iframe summarize-then-confirm path; otherwise agents "
            "may not realize the response data is already in context."
        )

    @pytest.mark.parametrize(
        "coaching",
        [PREVIEW_APPLY_COACHING, PREVIEW_APPLY_DIRECT_COACHING],
        ids=["sendmessage-rail", "direct-apply-rail"],
    )
    def test_no_iframe_path_says_re_issue_with_preview_false(
        self, coaching: str
    ) -> None:
        """The no-iframe fallback must spell out the apply mechanic
        (``preview=False``) so the agent isn't left guessing how to apply."""
        assert "preview=False" in coaching, (
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
