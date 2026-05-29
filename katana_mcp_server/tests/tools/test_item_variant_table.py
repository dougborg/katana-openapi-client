"""Tests for the item-variant collection-diff table (#726).

Exercises the variant-specific cell builders + merge wiring layered on top of
the shared collection-diff skeleton: SKU / sales-price / purchase-price cells,
the kind gutter on the SKU column, and the add/update/delete projection from
variant-CRUD actions + a prior-state snapshot.
"""

from decimal import Decimal
from typing import ClassVar

from katana_mcp.tools.foundation.item_variant_table import (
    _format_price,
    _format_price_diff,
    merge_variant_rows_for_modify_card,
    prepare_variant_table_rows,
)


class TestFormatPrice:
    def test_none_is_em_dash(self):
        assert _format_price(None) == "—"

    def test_trims_trailing_zeros(self):
        assert _format_price(299.0) == "299"
        assert _format_price(2.5) == "2.5"

    def test_numeric_string_coerced(self):
        assert _format_price("150.00") == "150"

    def test_decimal_trimmed(self):
        # Real modify diffs normalize prices to Decimal (compute_field_diff →
        # _normalize). Must trim like floats, not render "1200.0000000000".
        assert _format_price(Decimal("1200.0000000000")) == "1200"
        assert _format_price(Decimal("2.50")) == "2.5"

    def test_decimal_diff_form(self):
        assert (
            _format_price_diff(
                Decimal("100.00"), Decimal("125.50"), unknown_prior=False
            )
            == "100 → 125.5"
        )

    def test_non_numeric_string_passthrough(self):
        assert _format_price("free") == "free"

    def test_diff_form(self):
        assert _format_price_diff(100.0, 120.0, unknown_prior=False) == "100 → 120"

    def test_diff_unknown_prior(self):
        assert _format_price_diff(None, 120.0, unknown_prior=True) == (
            "(prior unknown) → 120"
        )


class TestMergeVariantRows:
    _PRIOR: ClassVar[dict] = {
        "variants": [
            {"id": 9001, "sku": "AAA", "sales_price": 100.0, "purchase_price": 60.0},
            {"id": 9002, "sku": "BBB", "sales_price": 110.0, "purchase_price": 70.0},
        ]
    }

    def _merge(self, actions):
        return prepare_variant_table_rows(
            merge_variant_rows_for_modify_card(self._PRIOR, actions)
        )

    def test_no_actions_yields_existing_rows_sorted_by_sku(self):
        rows = self._merge([])
        assert [r["sku"] for r in rows] == ["AAA", "BBB"]
        assert all(r["kind"] == "existing" for r in rows)
        # Existing rows reserve the 2-char gutter (no visible marker).
        assert all(r["sku_label"].startswith("  ") for r in rows)

    def test_add_variant_appends_with_added_kind_and_prices(self):
        action = {
            "operation": "add_variant",
            "target_id": None,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [
                {"field": "sku", "old": None, "new": "CCC", "is_added": True},
                {"field": "sales_price", "old": None, "new": 130.0, "is_added": True},
            ],
        }
        rows = self._merge([action])
        assert [r["kind"] for r in rows] == ["existing", "existing", "added"]
        added = rows[-1]
        assert added["sku_label"] == "+ CCC"
        assert added["sales_price_label"] == "130"
        # No purchase price supplied → em-dash.
        assert added["purchase_price_label"] == "—"
        assert added["status_label"] == "PLANNED"

    def test_update_variant_decorates_price_diff(self):
        action = {
            "operation": "update_variant",
            "target_id": 9001,
            "succeeded": True,
            "status_label": "APPLIED",
            "changes": [{"field": "sales_price", "old": 100.0, "new": 125.0}],
        }
        rows = self._merge([action])
        updated = next(r for r in rows if r["id"] == 9001)
        assert updated["kind"] == "updated"
        assert updated["sku_label"] == "~ AAA"
        assert updated["sales_price_label"] == "100 → 125"
        assert updated["status_label"] == "APPLIED"

    def test_update_variant_sku_change_shows_arrow(self):
        action = {
            "operation": "update_variant",
            "target_id": 9001,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [{"field": "sku", "old": "AAA", "new": "AAA-V2"}],
        }
        rows = self._merge([action])
        updated = next(r for r in rows if r["id"] == 9001)
        assert updated["sku_label"] == "~ AAA → AAA-V2"

    def test_delete_variant_marks_deleted_and_keeps_identity(self):
        action = {
            "operation": "delete_variant",
            "target_id": 9002,
            "succeeded": True,
            "status_label": "APPLIED",
            "changes": [],
        }
        rows = self._merge([action])
        deleted = next(r for r in rows if r["id"] == 9002)
        assert deleted["kind"] == "deleted"
        assert deleted["sku_label"] == "- BBB"

    def test_failed_action_carries_error(self):
        action = {
            "operation": "delete_variant",
            "target_id": 9001,
            "succeeded": False,
            "status_label": "FAILED",
            "error": "in use",
            "changes": [],
        }
        rows = self._merge([action])
        row = next(r for r in rows if r["id"] == 9001)
        assert row["status_label"] == "FAILED"
        assert row["error"] == "in use"

    def test_sku_less_variant_renders_no_sku_placeholder(self):
        prior = {"variants": [{"id": 9003, "sku": None, "sales_price": 5.0}]}
        rows = prepare_variant_table_rows(merge_variant_rows_for_modify_card(prior, []))
        assert rows[0]["sku_label"] == "  (no SKU)"

    def test_missing_prior_state_yields_empty(self):
        assert merge_variant_rows_for_modify_card(None, []) == []

    def test_non_variant_ops_filtered_without_warning(self, caplog):
        """The item action list also carries ``update_header`` / ``delete``
        (handled outside the variant table). These must be filtered before the
        shared merge so it doesn't log a spurious "dropped action — unknown
        operation" warning on every header-only modify (Copilot #875). Existing
        variant rows still render."""
        import logging

        from katana_mcp.logging import setup_logging

        setup_logging(log_level="WARNING", log_format="json")
        actions = [
            {
                "operation": "update_header",
                "target_id": 500,
                "succeeded": None,
                "changes": [{"field": "uom", "old": "pcs", "new": "kg"}],
            },
            {"operation": "delete", "target_id": 500, "succeeded": None, "changes": []},
        ]
        with caplog.at_level(
            logging.WARNING, logger="katana_mcp.tools.foundation.collection_diff"
        ):
            rows = self._merge(actions)
        # Existing variants still render, untouched.
        assert [r["kind"] for r in rows] == ["existing", "existing"]
        # No "dropped action" warning leaked from the shared merge.
        assert not any("dropped action" in rec.getMessage() for rec in caplog.records)

    def test_orphan_update_target_synthesized(self):
        action = {
            "operation": "update_variant",
            "target_id": 99999,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [{"field": "sales_price", "old": None, "new": 9.0}],
        }
        rows = self._merge([action])
        ghost = next((r for r in rows if str(r["id"]) == "99999"), None)
        assert ghost is not None
        assert ghost["kind"] == "updated"
