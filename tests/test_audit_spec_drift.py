"""Tests for ``scripts/audit_spec_drift.py`` — the spec-drift auditor and its
override registry.

The override engine's whole value is *narrow* matching: an override pins the
exact (endpoint, kind, field, values) of the finding it suppresses, so a spec
change that alters the divergence resurfaces it as new drift instead of staying
silently hidden. These tests pin that contract, plus registry validation and
the committed-registry-keeps-the-gate-green guarantee.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml
from scripts.audit_spec_drift import (
    DEFAULT_LIVE,
    DEFAULT_LOCAL,
    DEFAULT_OVERRIDES,
    apply_overrides,
    audit,
    load_overrides,
    load_spec,
    main,
)


def _spec(dto_name: str, schema: dict[str, Any], *, path: str, method: str) -> dict:
    """Build a minimal OpenAPI spec with one request-body DTO."""
    return {
        "paths": {
            path: {
                method: {
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{dto_name}"}
                            }
                        }
                    }
                }
            }
        },
        "components": {"schemas": {dto_name: schema}},
    }


# ----------------------------------------------------------------------
# Registry validation
# ----------------------------------------------------------------------


class TestLoadOverrides:
    def _write(self, tmp_path: Path, entries: list[dict]) -> Path:
        p = tmp_path / "ov.yaml"
        p.write_text(yaml.safe_dump({"overrides": entries}), encoding="utf-8")
        return p

    def test_valid_type_diff_entry(self, tmp_path: Path) -> None:
        p = self._write(
            tmp_path,
            [
                {
                    "endpoint": "POST /x",
                    "kind": "type_diff",
                    "field": "f",
                    "live": "object",
                    "local": "$ref:F",
                    "category": "intentional_local_divergence",
                    "reason": "typed ref is more precise",
                }
            ],
        )
        [ov] = load_overrides(p)
        assert ov.endpoint == "POST /x"
        assert ov.field_name == "f"
        assert ov.live == "object" and ov.local == "$ref:F"

    def test_reason_is_whitespace_collapsed(self, tmp_path: Path) -> None:
        p = self._write(
            tmp_path,
            [
                {
                    "endpoint": "POST /x",
                    "kind": "only_local",
                    "field": "f",
                    "category": "intentional_local_divergence",
                    "reason": "line one\n  line two",
                }
            ],
        )
        [ov] = load_overrides(p)
        assert ov.reason == "line one line two"

    def test_bad_kind_rejected(self, tmp_path: Path) -> None:
        p = self._write(
            tmp_path,
            [
                {
                    "endpoint": "POST /x",
                    "kind": "bogus",
                    "category": "intentional_local_divergence",
                    "reason": "r",
                }
            ],
        )
        with pytest.raises(ValueError, match="kind"):
            load_overrides(p)

    def test_bad_category_rejected(self, tmp_path: Path) -> None:
        p = self._write(
            tmp_path,
            [
                {
                    "endpoint": "POST /x",
                    "kind": "only_local",
                    "field": "f",
                    "category": "made_up",
                    "reason": "r",
                }
            ],
        )
        with pytest.raises(ValueError, match="category"):
            load_overrides(p)

    def test_local_wrong_requires_fix_tracked_in(self, tmp_path: Path) -> None:
        p = self._write(
            tmp_path,
            [
                {
                    "endpoint": "POST /x",
                    "kind": "only_live",
                    "field": "f",
                    "category": "upstream_correct_local_wrong",
                    "reason": "we are missing this",
                }
            ],
        )
        with pytest.raises(ValueError, match="fix_tracked_in"):
            load_overrides(p)

    def test_type_diff_requires_field_and_values(self, tmp_path: Path) -> None:
        p = self._write(
            tmp_path,
            [
                {
                    "endpoint": "POST /x",
                    "kind": "type_diff",
                    "field": "f",
                    "category": "intentional_local_divergence",
                    "reason": "r",
                }
            ],
        )
        with pytest.raises(ValueError, match=r"live.*local"):
            load_overrides(p)

    def test_non_string_field_rejected(self, tmp_path: Path) -> None:
        p = self._write(
            tmp_path,
            [
                {
                    "endpoint": "POST /x",
                    "kind": "only_local",
                    "field": 123,  # not a string — would never match
                    "category": "intentional_local_divergence",
                    "reason": "r",
                }
            ],
        )
        with pytest.raises(ValueError, match="non-empty string"):
            load_overrides(p)

    def test_scalar_required_rejected(self, tmp_path: Path) -> None:
        """A bare scalar where a list is expected — `live_required: resource_id`
        would otherwise become a tuple of characters and never match."""
        p = self._write(
            tmp_path,
            [
                {
                    "endpoint": "POST /x",
                    "kind": "required_diff",
                    "live_required": "resource_id",  # scalar, not a list
                    "local_required": ["resource_id", "extra"],
                    "category": "local_correct_upstream_wrong",
                    "reason": "r",
                }
            ],
        )
        with pytest.raises(ValueError, match="list of strings"):
            load_overrides(p)


# ----------------------------------------------------------------------
# Matching semantics
# ----------------------------------------------------------------------


class TestApplyOverrides:
    def _report_with_type_diff(self) -> Any:
        local = _spec(
            "Req",
            {"properties": {"filter": {"$ref": "#/components/schemas/Filter"}}},
            path="/sales_orders/search",
            method="post",
        )
        local["components"]["schemas"]["Filter"] = {"type": "object"}
        live = _spec(
            "LiveReq",
            {"properties": {"filter": {"type": "object"}}},
            path="/sales_orders/search",
            method="post",
        )
        return audit(local, live)

    def test_matching_type_diff_suppressed(self, tmp_path: Path) -> None:
        report = self._report_with_type_diff()
        assert report.drifted_endpoints  # drift present before overrides

        ov = load_overrides(
            self._write(
                tmp_path,
                endpoint="POST /sales_orders/search",
                field="filter",
                live="object",
                local="$ref:Filter",
            )
        )
        apply_overrides(report, ov)

        assert report.drifted_endpoints == []  # fully suppressed
        assert len(report.suppressed) == 1
        assert report.stale_overrides == []

    def test_changed_type_resurfaces_and_override_goes_stale(
        self, tmp_path: Path
    ) -> None:
        """The narrow-matching safety property: if the local type changes, the
        old override no longer matches — drift resurfaces, override is stale."""
        report = self._report_with_type_diff()
        ov = load_overrides(
            self._write(
                tmp_path,
                endpoint="POST /sales_orders/search",
                field="filter",
                live="object",
                local="$ref:SomethingElse",  # no longer matches actual local
            )
        )
        apply_overrides(report, ov)

        assert report.drifted_endpoints  # NOT suppressed — new drift surfaces
        assert report.suppressed == []
        assert len(report.stale_overrides) == 1

    def test_stale_override_counts_toward_strict_gate(self, tmp_path: Path) -> None:
        """A stale override is the only "drift" — total_drift_count must still be
        nonzero so --strict fails closed (the entry needs removing). This matters
        on spec-only PRs where CI runs audit-spec-strict but skips the test suite."""
        clean = _spec(
            "Req",
            {"properties": {"a": {"type": "string"}}},
            path="/x",
            method="post",
        )
        report = audit(clean, clean)
        assert report.drifted_endpoints == []  # no real drift
        assert report.total_drift_count == 0

        ov = load_overrides(
            self._write(
                tmp_path,
                endpoint="POST /nonexistent",
                field="ghost",
                live="object",
                local="$ref:Gone",
            )
        )
        apply_overrides(report, ov)
        assert len(report.stale_overrides) == 1
        assert report.total_drift_count == 1  # fails --strict

    def test_required_diff_suppression_exact_set_match(self, tmp_path: Path) -> None:
        local = _spec(
            "Req",
            {"properties": {"a": {"type": "string"}}, "required": ["a", "b"]},
            path="/serial_numbers",
            method="post",
        )
        live = _spec(
            "LiveReq",
            {"properties": {"a": {"type": "string"}}, "required": ["a"]},
            path="/serial_numbers",
            method="post",
        )
        report = audit(local, live)
        assert report.drifted_endpoints

        p = tmp_path / "ov.yaml"
        p.write_text(
            yaml.safe_dump(
                {
                    "overrides": [
                        {
                            "endpoint": "POST /serial_numbers",
                            "kind": "required_diff",
                            "live_required": ["a"],
                            "local_required": ["a", "b"],
                            "category": "local_correct_upstream_wrong",
                            "reason": "upstream under-documents required keys",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        apply_overrides(report, load_overrides(p))
        assert report.drifted_endpoints == []
        assert len(report.suppressed) == 1

    def test_partial_suppression_keeps_unmatched_finding_active(
        self, tmp_path: Path
    ) -> None:
        """An endpoint with two findings, one overridden — the other stays."""
        local = _spec(
            "Req",
            {
                "properties": {
                    "filter": {"$ref": "#/components/schemas/Filter"},
                    "extra": {"type": "string"},
                }
            },
            path="/x/search",
            method="post",
        )
        local["components"]["schemas"]["Filter"] = {"type": "object"}
        live = _spec(
            "LiveReq",
            {"properties": {"filter": {"type": "object"}}},
            path="/x/search",
            method="post",
        )
        report = audit(local, live)
        # two findings: filter type_diff + `extra` only_local
        ov = load_overrides(
            self._write(
                tmp_path,
                endpoint="POST /x/search",
                field="filter",
                live="object",
                local="$ref:Filter",
            )
        )
        apply_overrides(report, ov)

        assert len(report.drifted_endpoints) == 1
        ed = report.drifted_endpoints[0]
        assert ed.only_local_fields == ["extra"]  # unmatched finding kept
        assert ed.type_diffs == []  # matched finding removed
        assert len(report.suppressed) == 1

    def _write(
        self,
        tmp_path: Path,
        *,
        endpoint: str,
        field: str,
        live: str,
        local: str,
    ) -> Path:
        p = tmp_path / "ov.yaml"
        p.write_text(
            yaml.safe_dump(
                {
                    "overrides": [
                        {
                            "endpoint": endpoint,
                            "kind": "type_diff",
                            "field": field,
                            "live": live,
                            "local": local,
                            "category": "intentional_local_divergence",
                            "reason": "typed ref is more precise",
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        return p


# ----------------------------------------------------------------------
# Integration — the committed registry keeps the gate green
# ----------------------------------------------------------------------


class TestCommittedRegistry:
    def test_registry_is_valid(self) -> None:
        overrides = load_overrides(DEFAULT_OVERRIDES)
        assert overrides  # populated

    def test_strict_audit_is_green_with_committed_registry(self) -> None:
        """`audit-spec --strict` against committed specs + registry exits 0.

        This is the contract that lets the gate live in `poe check` / CI. If a
        new divergence appears (or an override goes stale and a finding
        resurfaces), this fails — exactly the intended signal.
        """
        report = audit(load_spec(DEFAULT_LOCAL), load_spec(DEFAULT_LIVE))
        apply_overrides(report, load_overrides(DEFAULT_OVERRIDES))
        assert report.drifted_endpoints == [], (
            "New spec drift not covered by the override registry — either fix "
            "the spec or add an override entry. See the report for details."
        )
        assert report.stale_overrides == [], (
            "Stale override(s) — the suppressed drift is gone; remove them from "
            "docs/upstream-specs/audit-overrides.yaml."
        )

    def test_main_strict_exit_zero(self) -> None:
        assert main(["--strict"]) == 0

    def test_main_no_overrides_surfaces_raw_drift(self) -> None:
        assert main(["--strict", "--no-overrides"]) == 1

    def test_main_explicit_missing_overrides_path_errors(self, tmp_path: Path) -> None:
        """A typo'd --overrides PATH must error, not silently run unsuppressed."""
        assert main(["--overrides", str(tmp_path / "nope.yaml")]) == 2

    def test_main_malformed_yaml_registry_returns_2(self, tmp_path: Path) -> None:
        """Broken YAML in the registry exits 2 (config error), not a traceback."""
        bad = tmp_path / "bad.yaml"
        bad.write_text("overrides: [unbalanced: {", encoding="utf-8")
        assert main(["--overrides", str(bad)]) == 2
