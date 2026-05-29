"""Tests for the entity-agnostic collection-diff element.

Exercises the shared merge skeleton / status vocabulary / summary line that
every modify card's collection table is built on (BOM rows, item variants, SO
sub-entities, …). Uses a tiny synthetic entity so the tests are independent of
any one card's column set.
"""

import logging
from typing import ClassVar

import pytest
from katana_mcp.tools.foundation.collection_diff import (
    STATUS_PREFIX,
    STATUS_VARIANTS,
    CollectionDiffSpec,
    collection_diff_summary,
    derive_status_label,
    merge_collection_diff_rows,
    summarize_apply_outcome,
)

# ---------------------------------------------------------------------------
# Synthetic entity: a "widget" collection with id + name + a single value cell.
# The cell-builder closures mirror what a real card supplies.
# ---------------------------------------------------------------------------


def _existing_row(snapshot: dict) -> dict:
    return {
        "id": snapshot["id"],
        "name": snapshot.get("name"),
        "value_label": str(snapshot.get("value", "—")),
        "kind": "existing",
        "status_prefix": STATUS_PREFIX["existing"],
    }


def _synth_orphan(key: str) -> dict:
    return {
        "id": key,
        "name": None,
        "value_label": "—",
        "kind": "existing",
        "status_prefix": STATUS_PREFIX["existing"],
    }


def _add_row(action, *, status_label, status_variant, error) -> dict:
    new = {c["field"]: c.get("new") for c in action.get("changes", [])}
    return {
        "id": "",
        "name": new.get("name"),
        "value_label": str(new.get("value", "—")),
        "kind": "added",
        "status_prefix": STATUS_PREFIX["added"],
        "status_label": status_label,
        "status_variant": status_variant,
        "error": error,
    }


def _apply_update(row, action, *, status_label, status_variant, error) -> None:
    row["kind"] = "updated"
    row["status_prefix"] = STATUS_PREFIX["updated"]
    row["status_label"] = status_label
    row["status_variant"] = status_variant
    row["error"] = error
    for c in action.get("changes", []):
        if c["field"] == "value":
            row["value_label"] = f"{c.get('old')} → {c.get('new')}"


def _apply_delete(row, action, *, status_label, status_variant, error) -> None:
    row["kind"] = "deleted"
    row["status_prefix"] = STATUS_PREFIX["deleted"]
    row["status_label"] = status_label
    row["status_variant"] = status_variant
    row["error"] = error


_WIDGET_SPEC = CollectionDiffSpec(
    add_ops=frozenset({"add_widget"}),
    update_ops=frozenset({"update_widget"}),
    delete_ops=frozenset({"delete_widget"}),
    key_of=lambda r: r["id"] if isinstance(r.get("id"), str) else None,
    existing_row=_existing_row,
    synth_orphan=_synth_orphan,
    add_row=_add_row,
    apply_update=_apply_update,
    apply_delete=_apply_delete,
    sort_key=lambda r: r.get("name") or "",
)


def _merge(prior_rows, actions):
    return merge_collection_diff_rows(
        prior_rows=prior_rows, actions=actions, spec=_WIDGET_SPEC
    )


class TestDeriveStatusLabel:
    @pytest.mark.parametrize(
        "action,expected",
        [
            ({"succeeded": None}, "PLANNED"),
            ({"succeeded": True}, "APPLIED"),
            ({"succeeded": True, "verified": True}, "APPLIED (verified)"),
            (
                {"succeeded": True, "verified": False},
                "APPLIED (verification mismatch)",
            ),
            ({"succeeded": False}, "FAILED"),
        ],
    )
    def test_labels(self, action, expected):
        assert derive_status_label(action) == expected

    def test_every_label_has_a_variant(self):
        for label in [
            "PLANNED",
            "APPLIED",
            "APPLIED (verified)",
            "APPLIED (verification mismatch)",
            "FAILED",
            "NOT RUN",
            "",
        ]:
            assert label in STATUS_VARIANTS


class TestSummarizeApplyOutcome:
    def test_empty_is_applied(self):
        assert summarize_apply_outcome([]) == ("APPLIED", "default")

    def test_all_succeeded(self):
        actions = [{"succeeded": True}, {"succeeded": True}]
        assert summarize_apply_outcome(actions) == ("APPLIED", "default")

    def test_all_failed(self):
        assert summarize_apply_outcome([{"succeeded": False}]) == (
            "FAILED",
            "destructive",
        )

    def test_mixed_is_partial_failure(self):
        actions = [{"succeeded": True}, {"succeeded": False}]
        assert summarize_apply_outcome(actions) == ("PARTIAL FAILURE", "destructive")


class TestCollectionDiffSummary:
    def test_no_changes_is_empty(self):
        rows = [{"kind": "existing"}, {"kind": "existing"}]
        assert collection_diff_summary(rows) == ""

    def test_omits_zero_buckets(self):
        rows = [{"kind": "added"}, {"kind": "added"}, {"kind": "existing"}]
        assert collection_diff_summary(rows) == "+2 added"

    def test_full_line(self):
        rows = [
            {"kind": "added"},
            {"kind": "updated"},
            {"kind": "updated"},
            {"kind": "deleted"},
            {"kind": "existing"},
        ]
        assert collection_diff_summary(rows) == "+1 added, ~2 updated, -1 deleted"


class TestMergeCollectionDiffRows:
    _PRIOR: ClassVar[list[dict]] = [
        {"id": "a", "name": "Alpha", "value": 1},
        {"id": "b", "name": "Bravo", "value": 2},
    ]

    def test_no_actions_yields_existing_rows_sorted(self):
        rows = _merge(self._PRIOR, [])
        assert [r["id"] for r in rows] == ["a", "b"]
        assert all(r["kind"] == "existing" for r in rows)
        assert all(r["status_prefix"] == "  " for r in rows)

    def test_add_appends_with_added_kind_and_status(self):
        action = {
            "operation": "add_widget",
            "succeeded": None,
            "changes": [
                {"field": "name", "new": "Gamma"},
                {"field": "value", "new": 9},
            ],
        }
        rows = _merge(self._PRIOR, [action])
        # Existing rows first, add trails.
        assert [r["kind"] for r in rows] == ["existing", "existing", "added"]
        added = rows[-1]
        assert added["name"] == "Gamma"
        assert added["value_label"] == "9"
        assert added["status_prefix"] == "+ "
        assert added["status_label"] == "PLANNED"
        assert added["status_variant"] == STATUS_VARIANTS["PLANNED"]

    def test_update_decorates_matched_row(self):
        action = {
            "operation": "update_widget",
            "target_id": "b",
            "succeeded": True,
            "verified": True,
            "changes": [{"field": "value", "old": 2, "new": 5}],
        }
        rows = _merge(self._PRIOR, [action])
        updated = next(r for r in rows if r["id"] == "b")
        assert updated["kind"] == "updated"
        assert updated["value_label"] == "2 → 5"
        assert updated["status_prefix"] == "~ "
        assert updated["status_label"] == "APPLIED (verified)"

    def test_delete_decorates_and_keeps_row(self):
        action = {"operation": "delete_widget", "target_id": "a", "succeeded": True}
        rows = _merge(self._PRIOR, [action])
        deleted = next(r for r in rows if r["id"] == "a")
        assert deleted["kind"] == "deleted"
        assert deleted["status_prefix"] == "- "
        # Identity is preserved so the user sees *what* is going away.
        assert deleted["name"] == "Alpha"

    def test_failed_action_carries_error(self):
        action = {
            "operation": "update_widget",
            "target_id": "b",
            "succeeded": False,
            "error": "boom",
            "changes": [{"field": "value", "old": 2, "new": 5}],
        }
        rows = _merge(self._PRIOR, [action])
        updated = next(r for r in rows if r["id"] == "b")
        assert updated["status_label"] == "FAILED"
        assert updated["status_variant"] == "destructive"
        assert updated["error"] == "boom"

    def test_orphan_update_target_synthesized(self):
        action = {
            "operation": "update_widget",
            "target_id": "ghost",
            "succeeded": None,
            "changes": [{"field": "value", "old": None, "new": 7}],
        }
        rows = _merge(self._PRIOR, [action])
        ghost = next((r for r in rows if r["id"] == "ghost"), None)
        assert ghost is not None
        assert ghost["kind"] == "updated"

    def test_orphan_delete_target_synthesized(self):
        # Symmetric with the update-orphan path: a delete whose target_id
        # isn't in the snapshot (stale id / partial fetch) still surfaces.
        action = {
            "operation": "delete_widget",
            "target_id": "ghost",
            "succeeded": True,
        }
        rows = _merge(self._PRIOR, [action])
        ghost = next((r for r in rows if r["id"] == "ghost"), None)
        assert ghost is not None
        assert ghost["kind"] == "deleted"
        assert ghost["status_prefix"] == "- "

    def test_unknown_operation_is_dropped_and_logged(self, caplog):
        from katana_mcp.logging import setup_logging

        # Route structlog through stdlib + JSONRenderer so caplog sees the
        # warning regardless of prior test ordering (mirrors the BOM merge
        # drop-warning test).
        setup_logging(log_level="WARNING", log_format="json")
        action = {"operation": "reorder_widget", "target_id": "a", "succeeded": None}
        with caplog.at_level(
            logging.WARNING, logger="katana_mcp.tools.foundation.collection_diff"
        ):
            rows = _merge(self._PRIOR, [action])
        # Unknown op doesn't pollute the rows.
        assert all(r["kind"] == "existing" for r in rows)
        assert any(
            "reorder_widget" in rec.getMessage()
            for rec in caplog.records
            if rec.levelname == "WARNING"
        )

    def test_missing_target_on_update_is_dropped(self):
        action = {"operation": "update_widget", "succeeded": None, "changes": []}
        rows = _merge(self._PRIOR, [action])
        assert all(r["kind"] == "existing" for r in rows)
