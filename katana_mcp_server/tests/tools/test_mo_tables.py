"""Tests for the MO collection diff tables (#721 Phase 4).

Recipe rows (ingredients), operation rows, and production records each project
onto the shared collection-diff skeleton with their own cell builders.
"""

from typing import ClassVar

from katana_mcp.tools.foundation.mo_tables import (
    merge_operation_rows_for_modify_card,
    merge_productions_for_modify_card,
    merge_recipe_rows_for_modify_card,
    prepare_operation_table_rows,
    prepare_production_table_rows,
    prepare_recipe_table_rows,
)


class TestRecipeRows:
    _PRIOR: ClassVar[dict] = {
        "recipe_rows": [
            {
                "id": 11,
                "variant_id": 401,
                "sku": "BOLT",
                "display_name": "M5 bolt",
                "planned_quantity_per_unit": 4.0,
            },
            {
                "id": 12,
                "variant_id": 402,
                "sku": "NUT",
                "display_name": "M5 nut",
                "planned_quantity_per_unit": 4.0,
            },
        ]
    }
    _RESOLVED: ClassVar[dict] = {403: {"sku": "WASHER", "display_name": "M5 washer"}}

    def _merge(self, actions):
        return prepare_recipe_table_rows(
            merge_recipe_rows_for_modify_card(self._PRIOR, actions, self._RESOLVED)
        )

    def test_existing_rows_carry_resolved_names(self):
        rows = self._merge([])
        assert [r["sku"] for r in rows] == ["BOLT", "NUT"]
        assert all(r["sku_label"].startswith("  ") for r in rows)

    def test_add_resolves_variant(self):
        action = {
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
        }
        added = self._merge([action])[-1]
        assert added["kind"] == "added"
        assert added["sku_label"] == "+ WASHER"
        assert added["display_name"] == "M5 washer"
        assert added["quantity_label"] == "2"

    def test_update_decorates_quantity(self):
        action = {
            "operation": "update_recipe_row",
            "target_id": 11,
            "succeeded": True,
            "status_label": "APPLIED",
            "changes": [{"field": "planned_quantity_per_unit", "old": 4.0, "new": 6.0}],
        }
        row = next(r for r in self._merge([action]) if r["id"] == 11)
        assert row["kind"] == "updated"
        assert row["quantity_label"] == "4 → 6"

    def test_delete_keeps_identity(self):
        action = {
            "operation": "delete_recipe_row",
            "target_id": 12,
            "succeeded": True,
            "status_label": "APPLIED",
            "changes": [],
        }
        row = next(r for r in self._merge([action]) if r["id"] == 12)
        assert row["kind"] == "deleted"
        assert row["sku_label"] == "- NUT"

    def test_unresolved_add_falls_back(self):
        action = {
            "operation": "add_recipe_row",
            "target_id": None,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [
                {"field": "variant_id", "old": None, "new": 999, "is_added": True}
            ],
        }
        added = prepare_recipe_table_rows(
            merge_recipe_rows_for_modify_card(self._PRIOR, [action], {})
        )[-1]
        assert added["sku_label"] == "+ (unresolved)"
        assert added["display_name"] == "variant 999"

    def test_other_collection_ops_filtered(self):
        # An operation-row action must not appear in the recipe table.
        action = {
            "operation": "add_operation_row",
            "target_id": None,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [],
        }
        rows = self._merge([action])
        assert [r["kind"] for r in rows] == ["existing", "existing"]


class TestOperationRows:
    _PRIOR: ClassVar[dict] = {
        "operation_rows": [
            {"id": 21, "operation_name": "Cut", "status": "NOT_STARTED"},
            {"id": 22, "operation_name": "Weld", "status": "IN_PROGRESS"},
        ]
    }

    def _merge(self, actions):
        return prepare_operation_table_rows(
            merge_operation_rows_for_modify_card(self._PRIOR, actions)
        )

    def test_existing_rows(self):
        rows = self._merge([])
        assert [r["operation_label"] for r in rows] == ["Cut", "Weld"]
        assert [r["op_status_label"] for r in rows] == ["NOT_STARTED", "IN_PROGRESS"]

    def test_add_operation(self):
        action = {
            "operation": "add_operation_row",
            "target_id": None,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [
                {
                    "field": "operation_name",
                    "old": None,
                    "new": "Paint",
                    "is_added": True,
                },
                {
                    "field": "status",
                    "old": None,
                    "new": "NOT_STARTED",
                    "is_added": True,
                },
            ],
        }
        added = self._merge([action])[-1]
        assert added["operation_label_gutter"] == "+ Paint"
        assert added["op_status_label"] == "NOT_STARTED"

    def test_update_status_diff(self):
        action = {
            "operation": "update_operation_row",
            "target_id": 21,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [{"field": "status", "old": "NOT_STARTED", "new": "COMPLETED"}],
        }
        row = next(r for r in self._merge([action]) if r["id"] == 21)
        assert row["op_status_label"] == "NOT_STARTED → COMPLETED"
        assert row["operation_label_gutter"] == "~ Cut"

    def test_delete(self):
        action = {
            "operation": "delete_operation_row",
            "target_id": 22,
            "succeeded": True,
            "status_label": "APPLIED",
            "changes": [],
        }
        row = next(r for r in self._merge([action]) if r["id"] == 22)
        assert row["kind"] == "deleted"
        assert row["operation_label_gutter"] == "- Weld"


class TestProductions:
    _PRIOR: ClassVar[dict] = {
        "productions": [
            {"id": 31, "quantity": 10.0, "production_date": "2026-05-01T00:00:00Z"},
        ]
    }

    def _merge(self, actions):
        return prepare_production_table_rows(
            merge_productions_for_modify_card(self._PRIOR, actions)
        )

    def test_existing_row(self):
        row = self._merge([])[0]
        assert row["quantity_label_gutter"] == "  10"
        assert row["date_label"] == "2026-05-01"

    def test_add_production_reads_completed_fields(self):
        action = {
            "operation": "add_production",
            "target_id": None,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [
                {
                    "field": "completed_quantity",
                    "old": None,
                    "new": 5.0,
                    "is_added": True,
                },
                {
                    "field": "completed_date",
                    "old": None,
                    "new": "2026-05-08T12:00:00Z",
                    "is_added": True,
                },
            ],
        }
        added = self._merge([action])[-1]
        assert added["quantity_label_gutter"] == "+ 5"
        assert added["date_label"] == "2026-05-08"

    def test_update_date_diff(self):
        action = {
            "operation": "update_production",
            "target_id": 31,
            "succeeded": None,
            "status_label": "PLANNED",
            "changes": [
                {
                    "field": "production_date",
                    "old": "2026-05-01T00:00:00Z",
                    "new": "2026-05-09T00:00:00Z",
                }
            ],
        }
        row = next(r for r in self._merge([action]) if r["id"] == 31)
        assert row["date_label"] == "2026-05-01 → 2026-05-09"

    def test_missing_prior_yields_empty(self):
        assert merge_productions_for_modify_card(None, []) == []
