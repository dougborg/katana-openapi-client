"""Tests for the bin-transfer line-item collection-diff table (#943).

Exercises the bin-row cell builders + merge wiring on the shared
collection-diff skeleton: SKU / variant-name / quantity / from-bin / to-bin
cells, the kind gutter on the SKU column, resolved-variant and resolved-bin
lookups, and the add/update/delete projection from row-CRUD actions + a
prior-state snapshot.
"""

from typing import ClassVar

from katana_mcp.tools.foundation.bin_row_table import (
    _bin_label,
    _bin_label_diff,
    merge_bin_row_rows_for_modify_card,
    prepare_bin_row_table_rows,
)


class TestBinLabel:
    _BINS: ClassVar[dict] = {7: "A-01", 9: "C-03"}

    def test_none_is_em_dash(self):
        assert _bin_label(self._BINS, None) == "—"

    def test_resolved_name(self):
        assert _bin_label(self._BINS, 7) == "A-01"

    def test_miss_falls_back_to_bin_id(self):
        assert _bin_label(self._BINS, 99) == "bin 99"

    def test_decimal_id_coerces(self):
        from decimal import Decimal

        assert _bin_label(self._BINS, Decimal("7")) == "A-01"

    def test_diff_form(self):
        assert _bin_label_diff(self._BINS, 9, 7, unknown_prior=False) == "C-03 → A-01"

    def test_diff_unknown_prior(self):
        assert (
            _bin_label_diff(self._BINS, None, 7, unknown_prior=True)
            == "(prior unknown) → A-01"
        )


class TestMergeBinRows:
    _PRIOR: ClassVar[dict] = {
        "bin_transfer_rows": [
            {
                "id": 11,
                "variant_id": 401,
                "quantity": "2.5",
                "source_bin_location_id": 7,
                "target_bin_location_id": 9,
            },
            {
                "id": 12,
                "variant_id": 402,
                "quantity": "1",
                "source_bin_location_id": 7,
                "target_bin_location_id": None,
            },
        ]
    }
    _RESOLVED: ClassVar[dict] = {
        401: {"sku": "BOLT-M5", "display_name": "M5 bolt"},
        402: {"sku": "NUT-M5", "display_name": "M5 nut"},
        403: {"sku": "WASHER-M5", "display_name": "M5 washer"},
    }
    _BINS: ClassVar[dict] = {7: "A-01", 8: "B-02", 9: "C-03"}

    def _merge(self, actions):
        return prepare_bin_row_table_rows(
            merge_bin_row_rows_for_modify_card(
                self._PRIOR, actions, self._RESOLVED, self._BINS
            )
        )

    def test_existing_rows_resolve_identities_and_bins(self):
        rows = self._merge([])
        assert [r["sku"] for r in rows] == ["BOLT-M5", "NUT-M5"]
        assert rows[0]["quantity_label"] == "2.5"
        assert rows[0]["source_bin_label"] == "A-01"
        assert rows[0]["target_bin_label"] == "C-03"
        # Unassigned target renders as an em-dash, not "bin None".
        assert rows[1]["target_bin_label"] == "—"
        assert all(r["kind"] == "existing" for r in rows)

    def test_add_row_resolves_variant_and_bins(self):
        action = {
            "operation": "add_row",
            "target_id": None,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [
                {"field": "variant_id", "old": None, "new": 403, "is_added": True},
                {"field": "quantity", "old": None, "new": 4.0, "is_added": True},
                {
                    "field": "target_bin_location_id",
                    "old": None,
                    "new": 8,
                    "is_added": True,
                },
            ],
        }
        rows = self._merge([action])
        added = rows[-1]
        assert added["kind"] == "added"
        assert added["sku_label"] == "+ WASHER-M5"
        assert added["display_name"] == "M5 washer"
        assert added["quantity_label"] == "4"
        # Source omitted on the add → unassigned em-dash.
        assert added["source_bin_label"] == "—"
        assert added["target_bin_label"] == "B-02"

    def test_update_row_decorates_quantity_and_bin_diffs(self):
        action = {
            "operation": "update_row",
            "target_id": 11,
            "succeeded": True,
            "status_label": "APPLIED",
            "changes": [
                {"field": "quantity", "old": "2.5", "new": 5.0},
                {"field": "target_bin_location_id", "old": 9, "new": 8},
            ],
        }
        rows = self._merge([action])
        updated = next(r for r in rows if r["id"] == 11)
        assert updated["kind"] == "updated"
        assert updated["sku_label"] == "~ BOLT-M5"
        assert updated["quantity_label"] == "2.5 → 5"
        assert updated["target_bin_label"] == "C-03 → B-02"
        # Untouched bin cell keeps its plain resolved name.
        assert updated["source_bin_label"] == "A-01"

    def test_delete_row_marks_deleted_and_keeps_identity(self):
        action = {
            "operation": "delete_row",
            "target_id": 12,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [],
        }
        rows = self._merge([action])
        deleted = next(r for r in rows if r["id"] == 12)
        assert deleted["kind"] == "deleted"
        assert deleted["sku_label"] == "- NUT-M5"
        assert deleted["quantity_label"] == "1"
        assert deleted["source_bin_label"] == "A-01"

    def test_unresolved_variant_falls_back(self):
        action = {
            "operation": "add_row",
            "target_id": None,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [
                {"field": "variant_id", "old": None, "new": 999, "is_added": True},
                {"field": "quantity", "old": None, "new": 1.0, "is_added": True},
            ],
        }
        rows = self._merge([action])
        added = rows[-1]
        assert added["sku_label"] == "+ (unresolved)"
        assert added["display_name"] == "variant 999"

    def test_header_and_status_ops_filtered_without_warning(self, caplog):
        import logging

        actions = [
            {
                "operation": "update_header",
                "target_id": 42,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [{"field": "bin_transfer_number", "old": "a", "new": "b"}],
            },
            {
                "operation": "update_status",
                "target_id": 42,
                "succeeded": None,
                "status_label": "PLANNED",
                "changes": [{"field": "new_status", "old": "CREATED", "new": "DONE"}],
            },
        ]
        with caplog.at_level(logging.WARNING):
            rows = self._merge(actions)
        assert all(r["kind"] == "existing" for r in rows)
        assert "collection diff dropped action" not in caplog.text

    def test_missing_prior_state_yields_only_adds(self):
        action = {
            "operation": "add_row",
            "target_id": None,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [
                {"field": "variant_id", "old": None, "new": 401, "is_added": True},
            ],
        }
        rows = prepare_bin_row_table_rows(
            merge_bin_row_rows_for_modify_card(None, [action], self._RESOLVED, None)
        )
        assert len(rows) == 1
        assert rows[0]["kind"] == "added"
