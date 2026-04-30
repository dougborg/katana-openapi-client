"""Unit tests for the shared entity-modification helpers.

These cover the pure-Python diff/render layer in
``katana_mcp.tools._modification``. The modifier-tool integration tests live
alongside their entity (e.g. ``test_purchase_orders.py``) and exercise the
helper through the actual tool flow.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from unittest.mock import MagicMock

from katana_mcp.tools._modification import (
    FieldChange,
    ModificationResponse,
    compute_field_diff,
    render_modification_md,
    to_tool_result,
)
from pydantic import BaseModel

from katana_public_api_client.client_types import UNSET


class _SampleEnum(StrEnum):
    DRAFT = "DRAFT"
    DONE = "DONE"


class _SampleRequest(BaseModel):
    id: int
    name: str | None = None
    qty: int | None = None
    when: datetime | None = None
    state: _SampleEnum | None = None
    confirm: bool = False


def test_compute_field_diff_skips_id_and_confirm_by_default():
    request = _SampleRequest(id=1, name="x", confirm=True)
    diff = compute_field_diff(None, request)
    assert {c.field for c in diff} == {"name"}


def test_compute_field_diff_marks_added_when_existing_field_is_none():
    existing = MagicMock()
    existing.name = UNSET  # treated as None via unwrap_unset
    request = _SampleRequest(id=1, name="new")
    diff = compute_field_diff(existing, request)
    assert len(diff) == 1
    assert diff[0].is_added is True
    assert diff[0].old is None
    assert diff[0].new == "new"


def test_compute_field_diff_marks_replacement_when_both_set_and_different():
    existing = MagicMock()
    existing.name = "old"
    request = _SampleRequest(id=1, name="new")
    diff = compute_field_diff(existing, request)
    assert diff[0].is_added is False
    assert diff[0].is_unchanged is False
    assert diff[0].old == "old"
    assert diff[0].new == "new"


def test_compute_field_diff_marks_unchanged_when_values_match():
    existing = MagicMock()
    existing.qty = 5
    request = _SampleRequest(id=1, qty=5)
    diff = compute_field_diff(existing, request)
    assert diff[0].is_unchanged is True


def test_compute_field_diff_normalizes_datetime_to_iso():
    when = datetime(2026, 5, 1, tzinfo=UTC)
    existing = MagicMock()
    existing.when = when
    request = _SampleRequest(id=1, when=when)
    diff = compute_field_diff(existing, request)
    assert diff[0].is_unchanged is True
    assert diff[0].old == when.isoformat()


def test_compute_field_diff_normalizes_enum_to_value():
    existing = MagicMock()
    existing.state = _SampleEnum.DRAFT
    request = _SampleRequest(id=1, state=_SampleEnum.DONE)
    diff = compute_field_diff(existing, request)
    assert diff[0].old == "DRAFT"
    assert diff[0].new == "DONE"


def test_compute_field_diff_field_map_renames_attr_lookup():
    existing = MagicMock()
    existing.real_name = "old"  # entity uses `real_name`, request uses `name`
    request = _SampleRequest(id=1, name="new")
    diff = compute_field_diff(existing, request, field_map={"name": "real_name"})
    assert diff[0].old == "old"
    assert diff[0].new == "new"


def test_compute_field_diff_unknown_prior_marks_changes_distinctly():
    """``unknown_prior=True`` distinguishes "fetch failed" from "create"."""
    request = _SampleRequest(id=1, name="new", qty=5)
    diff = compute_field_diff(None, request, unknown_prior=True)
    assert len(diff) == 2
    for change in diff:
        assert change.is_unknown_prior is True
        assert change.is_added is False
        assert change.old is None


def test_compute_field_diff_unknown_prior_ignored_when_existing_present():
    """If we DID get the entity, ``unknown_prior`` doesn't override actual diff."""
    existing = MagicMock()
    existing.name = "old"
    existing.qty = 5
    request = _SampleRequest(id=1, name="new", qty=5)
    diff = compute_field_diff(existing, request, unknown_prior=True)
    by_field = {c.field: c for c in diff}
    assert by_field["name"].old == "old"  # real diff, not unknown
    assert by_field["name"].is_unknown_prior is False
    assert by_field["qty"].is_unchanged is True


def test_render_modification_md_unknown_prior_label():
    response = ModificationResponse(
        entity_type="purchase_order",
        entity_id=42,
        operation="update",
        is_preview=True,
        message="Preview: update (prior unknown)",
        changes=[
            FieldChange(field="qty", old=None, new=5, is_unknown_prior=True),
        ],
    )
    md = render_modification_md(response)
    # Distinct from `(set) → ...` which would imply prior=empty.
    assert "`qty`: (prior unknown) → 5" in md


def test_render_modification_md_preview_label():
    response = ModificationResponse(
        entity_type="purchase_order",
        entity_id=42,
        operation="update",
        is_preview=True,
        message="Preview: update",
        changes=[FieldChange(field="qty", old=1, new=2)],
        next_actions=["Set confirm=true"],
    )
    md = render_modification_md(response)
    assert "## Purchase Order Update (PREVIEW)" in md
    assert "**ID**: 42" in md
    assert "`qty`: 1 → 2" in md
    assert "Set confirm=true" in md


def test_render_modification_md_confirmed_label_uses_operation():
    response = ModificationResponse(
        entity_type="purchase_order",
        entity_id=42,
        operation="delete",
        is_preview=False,
        message="Successfully deleted",
    )
    md = render_modification_md(response)
    assert "## Purchase Order Delete (DELETE)" in md


def test_render_modification_md_includes_parent_id_when_set():
    response = ModificationResponse(
        entity_type="purchase_order_row",
        entity_id=555,
        parent_entity_id=42,
        operation="update_row",
        is_preview=False,
        message="ok",
    )
    md = render_modification_md(response)
    assert "**Parent ID**: 42" in md


def test_to_tool_result_serializes_response_as_structured_data():
    response = ModificationResponse(
        entity_type="purchase_order",
        entity_id=1,
        operation="update",
        is_preview=False,
        message="ok",
    )
    result = to_tool_result(response)
    # The structured payload mirrors the response model — downstream callers
    # rely on the shape via ``structured_content``.
    assert result.structured_content is not None
    assert result.structured_content["entity_type"] == "purchase_order"
    assert result.structured_content["operation"] == "update"
