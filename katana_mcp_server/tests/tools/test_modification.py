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

import pytest
from katana_mcp.tools._modification import (
    ActionResult,
    FieldChange,
    ModificationResponse,
    compute_field_diff,
    render_modification_md,
    to_tool_result,
)
from katana_mcp.tools._modification_dispatch import (
    ActionSpec,
    execute_plan,
    plan_to_preview_results,
    serialize_for_prior_state,
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


# ============================================================================
# Multi-action shape (ActionResult + dispatcher integration)
# ============================================================================


def test_action_result_preview_shape_succeeded_is_none():
    """Preview-shaped ActionResults carry succeeded=None to signal 'planned'."""
    result = ActionResult(operation="update_header", target_id=42)
    assert result.succeeded is None
    assert result.verified is None
    assert result.error is None


def test_modification_response_renders_multi_action_when_actions_populated():
    response = ModificationResponse(
        entity_type="purchase_order",
        entity_id=42,
        is_preview=True,
        actions=[
            ActionResult(
                operation="update_header",
                changes=[FieldChange(field="status", old="DRAFT", new="RECEIVED")],
            ),
            ActionResult(
                operation="add_row",
                target_id=None,
                changes=[
                    FieldChange(field="variant_id", old=None, new=100, is_added=True)
                ],
            ),
        ],
        message="Preview: 2 actions",
    )
    md = render_modification_md(response)
    # Multi-action header
    assert "## Modify Purchase Order (PREVIEW) — 2 actions" in md
    # Each action rendered as its own sub-section, all PLANNED
    assert "#### 1. Update Header — PLANNED" in md
    assert "#### 2. Add Row — PLANNED" in md
    assert "`status`: DRAFT → RECEIVED" in md


def test_modification_response_renders_legacy_single_action_when_actions_empty():
    """When ``actions`` is empty the legacy ``operation`` + ``changes`` shape renders."""
    response = ModificationResponse(
        entity_type="purchase_order",
        entity_id=42,
        operation="update",
        is_preview=False,
        changes=[FieldChange(field="qty", old=1, new=2)],
        message="Updated",
    )
    md = render_modification_md(response)
    assert "## Purchase Order Update (UPDATE)" in md
    assert "`qty`: 1 → 2" in md


def test_render_action_block_status_labels():
    """Action status labels distinguish planned / applied / applied-verified / failed."""
    cases = [
        (ActionResult(operation="x", succeeded=None), "PLANNED"),
        (ActionResult(operation="x", succeeded=True), "APPLIED"),
        (
            ActionResult(operation="x", succeeded=True, verified=True),
            "APPLIED (verified)",
        ),
        (
            ActionResult(operation="x", succeeded=True, verified=False),
            "APPLIED (verification mismatch)",
        ),
        (ActionResult(operation="x", succeeded=False, error="boom"), "FAILED"),
    ]
    for action, expected_label in cases:
        response = ModificationResponse(
            entity_type="purchase_order",
            is_preview=False,
            actions=[action],
            message="x",
        )
        md = render_modification_md(response)
        assert expected_label in md, f"missing {expected_label} for {action}"


def test_render_includes_prior_state_block_when_set():
    response = ModificationResponse(
        entity_type="purchase_order",
        entity_id=1,
        is_preview=False,
        actions=[
            ActionResult(operation="update_header", succeeded=True, verified=True)
        ],
        prior_state={"status": "DRAFT", "supplier_id": 4001},
        message="ok",
    )
    md = render_modification_md(response)
    assert "### Prior State (for manual revert)" in md


# ============================================================================
# execute_plan — dispatcher executor
# ============================================================================


@pytest.mark.asyncio
async def test_execute_plan_runs_all_actions_in_order():
    """Plan executes sequentially; each action's verify runs after apply."""
    call_log: list[str] = []

    async def make_apply(name: str):
        call_log.append(f"apply:{name}")
        return name

    async def make_verify(_outcome: object):
        call_log.append("verify")
        return True, {"k": "v"}

    plan = [
        ActionSpec(
            operation="update_header",
            target_id=None,
            apply=lambda: make_apply("a"),
            verify=make_verify,
        ),
        ActionSpec(
            operation="add_row",
            target_id=None,
            apply=lambda: make_apply("b"),
            verify=make_verify,
        ),
    ]
    results = await execute_plan(plan)

    assert len(results) == 2
    assert all(r.succeeded is True for r in results)
    assert all(r.verified is True for r in results)
    # Verify ordering: apply-a, verify, apply-b, verify
    assert call_log == ["apply:a", "verify", "apply:b", "verify"]


@pytest.mark.asyncio
async def test_execute_plan_fails_fast_on_first_apply_error():
    attempted: list[str] = []

    async def good():
        attempted.append("good")
        return None

    async def bad():
        attempted.append("bad")
        raise ValueError("boom")

    async def never():
        attempted.append("never")
        return None

    plan = [
        ActionSpec(operation="op1", target_id=1, apply=good),
        ActionSpec(operation="op2", target_id=2, apply=bad),
        ActionSpec(operation="op3", target_id=3, apply=never),
    ]
    results = await execute_plan(plan)

    # First two run; third never attempted (fail-fast)
    assert attempted == ["good", "bad"]
    assert len(results) == 2
    assert results[0].succeeded is True
    assert results[1].succeeded is False
    assert "boom" in (results[1].error or "")


@pytest.mark.asyncio
async def test_execute_plan_verification_failure_does_not_halt_plan():
    """Verification failure surfaces as verified=False, plan keeps going."""

    async def apply_ok():
        return None

    async def verify_fails(_outcome: object):
        return False, {"actual": "different"}

    async def verify_succeeds(_outcome: object):
        return True, None

    plan = [
        ActionSpec(operation="op1", apply=apply_ok, verify=verify_fails, target_id=1),
        ActionSpec(
            operation="op2", apply=apply_ok, verify=verify_succeeds, target_id=2
        ),
    ]
    results = await execute_plan(plan)

    assert len(results) == 2
    assert results[0].succeeded is True
    assert results[0].verified is False
    assert results[0].actual_after == {"actual": "different"}
    assert results[1].verified is True


@pytest.mark.asyncio
async def test_execute_plan_verification_exception_marks_unverified():
    async def apply_ok():
        return None

    async def verify_raises(_outcome: object):
        raise RuntimeError("fetch failed")

    plan = [
        ActionSpec(operation="op", apply=apply_ok, verify=verify_raises, target_id=1)
    ]
    results = await execute_plan(plan)
    assert len(results) == 1
    assert results[0].succeeded is True
    assert results[0].verified is False
    assert results[0].actual_after is None


def test_plan_to_preview_results_has_all_succeeded_none():
    plan = [
        ActionSpec(operation="op1", target_id=1, diff=[FieldChange(field="x", new=1)]),
        ActionSpec(operation="op2", target_id=None),
    ]
    results = plan_to_preview_results(plan)
    assert len(results) == 2
    for r in results:
        assert r.succeeded is None
        assert r.verified is None
    assert results[0].changes[0].field == "x"


def test_serialize_for_prior_state_uses_to_dict_when_available():
    class FakeAttrs:
        def to_dict(self) -> dict:
            return {"id": 1, "status": "DRAFT"}

    snapshot = serialize_for_prior_state(FakeAttrs())
    assert snapshot == {"id": 1, "status": "DRAFT"}


def test_serialize_for_prior_state_falls_back_to_model_dump():
    from pydantic import BaseModel as PydanticBase

    class FakePydantic(PydanticBase):
        id: int
        status: str

    snapshot = serialize_for_prior_state(FakePydantic(id=1, status="DRAFT"))
    assert snapshot == {"id": 1, "status": "DRAFT"}


def test_serialize_for_prior_state_returns_none_for_unsupported():
    assert serialize_for_prior_state(None) is None
    assert serialize_for_prior_state("a string") is None
