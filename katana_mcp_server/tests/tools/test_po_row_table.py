"""Tests for the PO line-item collection-diff table (#722 follow-up / #721).

Exercises the PO-row cell builders + merge wiring on the shared collection-diff
skeleton: SKU / variant-name / quantity / unit-price cells, the kind gutter on
the SKU column, resolved-variant lookup, and the add/update/delete projection
from row-CRUD actions + a prior-state snapshot.
"""

import logging
from decimal import Decimal
from typing import ClassVar

from katana_mcp.tools.foundation.po_row_table import (
    _format_number,
    _format_number_diff,
    merge_po_row_rows_for_modify_card,
    prepare_po_row_table_rows,
)


class TestFormatNumber:
    def test_none_is_em_dash(self):
        assert _format_number(None) == "—"

    def test_trims_trailing_zeros(self):
        assert _format_number(25.0) == "25"
        assert _format_number(2.5) == "2.5"

    def test_decimal_trimmed(self):
        assert _format_number(Decimal("25.0000000000")) == "25"
        assert _format_number(Decimal("2.50")) == "2.5"

    def test_numeric_string_coerced(self):
        assert _format_number("40.00") == "40"

    def test_diff_form(self):
        assert _format_number_diff(10.0, 15.0, unknown_prior=False) == "10 → 15"

    def test_diff_unknown_prior(self):
        assert (
            _format_number_diff(None, 15.0, unknown_prior=True)
            == "(prior unknown) → 15"
        )


class TestMergePORows:
    _PRIOR: ClassVar[dict] = {
        "purchase_order_rows": [
            {"id": 7001, "variant_id": 401, "quantity": 10.0, "price_per_unit": 25.0},
            {"id": 7002, "variant_id": 402, "quantity": 5.0, "price_per_unit": 40.0},
        ]
    }
    _RESOLVED: ClassVar[dict] = {
        401: {"sku": "BOLT-M5", "display_name": "M5 bolt"},
        402: {"sku": "NUT-M5", "display_name": "M5 nut"},
        403: {"sku": "WASHER-M5", "display_name": "M5 washer"},
    }

    def _merge(self, actions):
        return prepare_po_row_table_rows(
            merge_po_row_rows_for_modify_card(self._PRIOR, actions, self._RESOLVED)
        )

    def test_existing_rows_resolve_sku_and_name(self):
        rows = self._merge([])
        assert [r["sku"] for r in rows] == ["BOLT-M5", "NUT-M5"]
        assert [r["display_name"] for r in rows] == ["M5 bolt", "M5 nut"]
        assert all(r["kind"] == "existing" for r in rows)
        assert all(r["sku_label"].startswith("  ") for r in rows)

    def test_add_row_resolves_variant_and_appends(self):
        action = {
            "operation": "add_row",
            "target_id": None,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [
                {"field": "variant_id", "old": None, "new": 403, "is_added": True},
                {"field": "quantity", "old": None, "new": 20.0, "is_added": True},
                {"field": "price_per_unit", "old": None, "new": 2.5, "is_added": True},
            ],
        }
        rows = self._merge([action])
        added = rows[-1]
        assert added["kind"] == "added"
        assert added["sku_label"] == "+ WASHER-M5"
        assert added["display_name"] == "M5 washer"
        assert added["quantity_label"] == "20"
        assert added["price_label"] == "2.5"

    def test_update_row_decorates_quantity_diff(self):
        action = {
            "operation": "update_row",
            "target_id": 7001,
            "succeeded": True,
            "status_label": "APPLIED",
            "changes": [{"field": "quantity", "old": 10.0, "new": 15.0}],
        }
        rows = self._merge([action])
        updated = next(r for r in rows if r["id"] == 7001)
        assert updated["kind"] == "updated"
        assert updated["sku_label"] == "~ BOLT-M5"
        assert updated["quantity_label"] == "10 → 15"

    def test_update_row_variant_swap_reresolves_name(self):
        action = {
            "operation": "update_row",
            "target_id": 7001,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [{"field": "variant_id", "old": 401, "new": 403}],
        }
        rows = self._merge([action])
        updated = next(r for r in rows if r["id"] == 7001)
        assert updated["sku"] == "WASHER-M5"
        assert updated["display_name"] == "M5 washer"

    def test_delete_row_marks_deleted_and_keeps_identity(self):
        action = {
            "operation": "delete_row",
            "target_id": 7002,
            "succeeded": True,
            "status_label": "APPLIED",
            "changes": [],
        }
        rows = self._merge([action])
        deleted = next(r for r in rows if r["id"] == 7002)
        assert deleted["kind"] == "deleted"
        assert deleted["sku_label"] == "- NUT-M5"

    def test_unresolved_variant_falls_back(self):
        action = {
            "operation": "add_row",
            "target_id": None,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [
                {"field": "variant_id", "old": None, "new": 99999, "is_added": True},
                {"field": "quantity", "old": None, "new": 1.0, "is_added": True},
            ],
        }
        rows = prepare_po_row_table_rows(
            merge_po_row_rows_for_modify_card(self._PRIOR, [action], {})
        )
        added = rows[-1]
        assert added["sku_label"] == "+ (unresolved)"
        assert added["display_name"] == "variant 99999"

    def test_non_row_ops_filtered_without_warning(self, caplog):
        """Header / additional-cost ops in the same plan must be filtered before
        the shared merge so it doesn't log a spurious unknown-op warning."""
        from katana_mcp.logging import setup_logging

        setup_logging(log_level="WARNING", log_format="json")
        actions = [
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
        with caplog.at_level(
            logging.WARNING, logger="katana_mcp.tools.foundation.collection_diff"
        ):
            rows = self._merge(actions)
        assert [r["kind"] for r in rows] == ["existing", "existing"]
        assert not any("dropped action" in rec.getMessage() for rec in caplog.records)

    def test_missing_prior_state_yields_empty(self):
        assert merge_po_row_rows_for_modify_card(None, [], {}) == []
