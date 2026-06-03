"""Unit tests for the shared entity-modification helpers.

These cover the pure-Python diff/render layer in
``katana_mcp.tools._modification``. The modifier-tool integration tests live
alongside their entity (e.g. ``test_purchase_orders.py``) and exercise the
helper through the actual tool flow.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from katana_mcp.tools._modification import (
    ActionResult,
    ConfirmableRequest,
    FieldChange,
    ModificationResponse,
    compute_field_diff,
    make_response_verifier,
    render_modification_md,
    to_tool_result,
)
from katana_mcp.tools._modification_dispatch import (
    ActionSpec,
    CacheMerge,
    EntityNaming,
    execute_plan,
    plan_to_preview_results,
    run_modify_plan,
    serialize_for_prior_state,
)
from katana_mcp.typed_cache import TypedCacheEngine

from katana_public_api_client.client_types import UNSET


class _SampleEnum(StrEnum):
    DRAFT = "DRAFT"
    DONE = "DONE"


class _SampleRequest(ConfirmableRequest):
    name: str | None = None
    qty: int | None = None
    when: datetime | None = None
    state: _SampleEnum | None = None
    # ``preview: bool`` is inherited from ConfirmableRequest with default
    # ``True``; no need to re-declare here.


class _AttrsStub:
    """Mutable stand-in for a generated attrs response model.

    Used in the post-apply overlay tests where we need the dispatcher's
    ``getattr``/``setattr`` contract to behave like a real attrs class —
    ``MagicMock(spec=...)`` answers ``hasattr`` truthy for arbitrary
    attributes and would mask the very ``_MISSING`` sentinel guard the
    overlay relies on.
    """

    def __init__(self, **kw: Any) -> None:
        for k, v in kw.items():
            setattr(self, k, v)


def test_compute_field_diff_skips_id_and_preview_by_default():
    request = _SampleRequest(id=1, name="x", preview=False)
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


def test_compute_field_diff_numeric_string_matches_int_request():
    # Katana returns monetary fields as zero-padded decimal strings
    # (e.g. ``"1100.0000000000"``); request supplies plain ints/floats.
    # Without numeric normalization the diff would mark these as changed.
    existing = MagicMock()
    existing.qty = "1100.0000000000"
    request = _SampleRequest(id=1, qty=1100)
    diff = compute_field_diff(existing, request)
    assert diff[0].is_unchanged is True


def test_compute_field_diff_zero_string_matches_zero_request():
    # Mirrors the production case where ``total_discount: 0`` is sent and
    # Katana stores ``"0.0000000000"``.
    existing = MagicMock()
    existing.qty = "0.0000000000"
    request = _SampleRequest(id=1, qty=0)
    diff = compute_field_diff(existing, request)
    assert diff[0].is_unchanged is True


def test_compute_field_diff_non_numeric_strings_compare_as_strings():
    # Decimal coercion must fall back gracefully for arbitrary strings —
    # SKUs, names, etc. should still compare exactly.
    existing = MagicMock()
    existing.name = "M14025LG4STRLB"
    request = _SampleRequest(id=1, name="M14025LG4STRLB")
    diff = compute_field_diff(existing, request)
    assert diff[0].is_unchanged is True


def test_compute_field_diff_preserves_leading_zeros_in_integer_strings():
    # Digit-only strings (order numbers, ZIP codes, zero-padded SKUs) must
    # NOT coerce to Decimal — that would drop leading zeros and silently
    # mask real mismatches like ``"00123"`` vs ``"123"``. Only strings
    # containing a decimal point (Katana's monetary format) are coerced.
    existing = MagicMock()
    existing.name = "00123"
    request = _SampleRequest(id=1, name="123")
    diff = compute_field_diff(existing, request)
    assert diff[0].is_unchanged is False
    assert diff[0].old == "00123"
    assert diff[0].new == "123"


@pytest.mark.asyncio
async def test_response_verifier_passes_when_decimal_string_equals_int():
    # The verifier closure compares the post-update API response (which
    # carries decimal strings on monetary fields) against the
    # pre-normalized ``FieldChange.new`` from the request. Without
    # numeric normalization this read as ``"1100.0000000000" != 1100``
    # and produced a spurious "verification mismatch" status. See the
    # session that triggered the fix — modify_sales_order on
    # SO 44256191 set total_discount and the verifier flagged it
    # despite the value landing correctly server-side.
    diff = compute_field_diff(
        MagicMock(qty=0),
        _SampleRequest(id=1, qty=1100),
    )
    verify = make_response_verifier(diff)
    response_outcome = MagicMock()
    response_outcome.qty = "1100.0000000000"
    verified, actual = await verify(response_outcome)
    assert verified is True
    assert actual is None


@pytest.mark.asyncio
async def test_response_verifier_transforms_bridge_wire_vs_literal():
    """``transforms`` canonicalizes both sides so a wire-vs-literal value
    verifies cleanly.

    The stock-transfer status case: the request carries the tool-facing literal
    ``IN_TRANSIT`` (on the patch field ``new_status``) while Katana echoes the
    wire value ``inTransit`` (on the response attr ``status``). ``field_map``
    bridges the name; the transform maps both representations to the wire form,
    so verification passes. Without it the verifier read ``inTransit != IN_TRANSIT``
    and reported a spurious mismatch (the reason the action skipped verify).
    """
    wire = {"IN_TRANSIT": "inTransit", "DRAFT": "draft", "RECEIVED": "received"}

    def to_wire(value: Any) -> Any:
        return wire.get(value, value)

    diff = [FieldChange(field="new_status", old=None, new="IN_TRANSIT")]
    verify = make_response_verifier(
        diff, field_map={"new_status": "status"}, transforms={"new_status": to_wire}
    )
    outcome = MagicMock()
    outcome.status = "inTransit"
    verified, actual = await verify(outcome)
    assert verified is True
    assert actual is None


@pytest.mark.asyncio
async def test_response_verifier_transforms_still_flags_real_divergence():
    """A genuine post-canonicalization divergence still reports a mismatch."""
    wire = {"IN_TRANSIT": "inTransit", "RECEIVED": "received"}

    def to_wire(value: Any) -> Any:
        return wire.get(value, value)

    diff = [FieldChange(field="new_status", old=None, new="IN_TRANSIT")]
    verify = make_response_verifier(
        diff, field_map={"new_status": "status"}, transforms={"new_status": to_wire}
    )
    outcome = MagicMock()
    outcome.status = "received"  # server landed a different status than requested
    verified, actual = await verify(outcome)
    assert verified is False
    assert actual == {"new_status": "received"}


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
        next_actions=["Set preview=false"],
    )
    md = render_modification_md(response)
    assert "## Purchase Order Update (PREVIEW)" in md
    assert "**ID**: 42" in md
    assert "`qty`: 1 → 2" in md
    assert "Set preview=false" in md


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


def test_to_tool_result_emits_prefab_envelope_and_response_in_content():
    """to_tool_result wires the Prefab modification card.

    Per the MCP Apps spec (SEP-1865) and ``make_tool_result``: the
    response JSON lives in ``content`` (model context — what the LLM
    reads), and the Prefab envelope lives in ``structured_content`` (for
    iframe rendering). The card shape itself is covered by
    ``test_prefab_ui.py``; here we just verify the wiring.
    """
    import json as _json

    from katana_mcp.tools._modification import ConfirmableRequest

    response = ModificationResponse(
        entity_type="purchase_order",
        entity_id=1,
        operation="update",
        is_preview=False,
        message="ok",
    )
    confirm_request = ConfirmableRequest(id=1, preview=False)
    result = to_tool_result(
        response,
        confirm_request=confirm_request,
        confirm_tool="modify_purchase_order",
    )

    # content carries the response JSON for the LLM.
    assert result.content
    first_content = result.content[0]
    from mcp.types import TextContent

    assert isinstance(first_content, TextContent)
    text = first_content.text
    payload = _json.loads(text)
    assert payload["entity_type"] == "purchase_order"
    assert payload["operation"] == "update"

    # structured_content carries the Prefab envelope for the iframe.
    assert result.structured_content is not None
    assert "$prefab" in result.structured_content
    assert "view" in result.structured_content


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


class TestDeriveSummary:
    """ActionResult ``@model_validator`` populates ``summary`` via
    :func:`_modification._derive_summary`. The post-#card-ux derivation
    is content-rich (field names + ``old → new`` inline) — pinned here
    against the production path (the model validator), not against a
    duplicate dict-side helper that the prefab UI used to carry.
    """

    def test_single_change_renders_inline_old_to_new(self):
        action = ActionResult(
            operation="update_header",
            target_id=42,
            changes=[
                FieldChange(field="status", old="DRAFT", new="ACTIVE"),
            ],
        )
        assert action.summary == "status: DRAFT → ACTIVE"

    def test_multi_change_surfaces_field_names_with_overflow_tail(self):
        action = ActionResult(
            operation="update_header",
            target_id=42,
            changes=[FieldChange(field=f"f{i}", old="a", new="b") for i in range(5)],
        )
        assert action.summary == "f0, f1, f2 (+2 more)"
        assert "field(s) changed" not in action.summary

    def test_add_operation_lists_field_names_not_count(self):
        action = ActionResult(
            operation="add_recipe_row",
            target_id=None,
            changes=[
                FieldChange(field="variant_id", new=100, is_added=True),
                FieldChange(field="quantity", new=2, is_added=True),
            ],
        )
        assert action.summary == "added: variant_id, quantity"
        assert "field(s) set" not in action.summary

    def test_delete_operation_summary(self):
        action = ActionResult(operation="delete_recipe_row", target_id=5)
        assert action.summary == "deleted"

    def test_unknown_prior_renders_with_explicit_marker_not_em_dash(self):
        """`is_unknown_prior` must be visually distinct from a `None`
        prior value. Otherwise the operator can't tell whether the
        field was blank or just unresolvable."""
        action = ActionResult(
            operation="update_addresses",
            target_id=42,
            changes=[
                FieldChange(
                    field="line_1",
                    old=None,
                    new="123 Main St",
                    is_unknown_prior=True,
                ),
            ],
        )
        assert action.summary == "line_1: (prior unknown) → 123 Main St"
        # The em-dash must NOT appear — it would mean "the field was blank
        # before" which is a different statement than "we don't know".
        assert "—" not in action.summary

    def test_no_changes_renders_em_dash(self):
        action = ActionResult(operation="update_header", target_id=42, changes=[])
        assert action.summary == "—"

    def test_all_unchanged_renders_no_change(self):
        action = ActionResult(
            operation="update_header",
            target_id=42,
            changes=[
                FieldChange(
                    field="status", old="DRAFT", new="DRAFT", is_unchanged=True
                ),
            ],
        )
        assert action.summary == "no change"

    def test_validator_does_not_overwrite_explicit_summary(self):
        """A caller-supplied summary string wins over the derived one —
        the validator only fills when ``summary`` is empty."""
        action = ActionResult(
            operation="update_header",
            target_id=42,
            changes=[FieldChange(field="status", old="A", new="B")],
            summary="custom note",
        )
        assert action.summary == "custom note"


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


# ============================================================================
# make_delete_apply — idempotent 404 semantics (#777)
# ============================================================================


def _build_delete_endpoint_mock(*, status_code: int, name: str = "delete_endpoint"):
    """Build a fake DELETE endpoint module exposing ``asyncio_detailed``.

    Mirrors the shape :func:`make_delete_apply` expects: an object with
    a ``__name__`` and an ``asyncio_detailed`` async callable returning a
    ``Response``-like object whose ``status_code`` matches the scenario.
    """
    from http import HTTPStatus

    from katana_public_api_client.client_types import Response

    response: Response[Any] = Response(
        status_code=HTTPStatus(status_code),
        content=b"",
        headers={},
        parsed=None,
    )
    endpoint = MagicMock()
    endpoint.__name__ = name
    endpoint.asyncio_detailed = AsyncMock(return_value=response)
    return endpoint, response


def _build_services_mock():
    services = MagicMock()
    services.client = MagicMock()
    return services


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "endpoint_name",
    [
        "delete_purchase_order_row",
        "delete_sales_order_row",
        "delete_manufacturing_order_recipe_row",
    ],
)
async def test_make_delete_apply_treats_404_as_success(endpoint_name: str):
    """Regression for #777: 404 on DELETE means the row is already gone,
    which is the desired end state. ``apply()`` must return None
    (not raise), so a fail-fast plan can keep marching.

    Parametrized across endpoint names to confirm the conflation lives
    at the dispatch layer and applies uniformly across every entity
    that routes through :func:`make_delete_apply`.
    """
    # Arrange
    from katana_mcp.tools._modification_dispatch import make_delete_apply

    services = _build_services_mock()
    endpoint, _response = _build_delete_endpoint_mock(
        status_code=404, name=endpoint_name
    )

    # Act
    apply = make_delete_apply(endpoint, services, target_id=42)
    result = await apply()

    # Assert
    assert result is None
    endpoint.asyncio_detailed.assert_awaited_once()
    call_kwargs = endpoint.asyncio_detailed.await_args.kwargs
    assert call_kwargs["id"] == 42
    assert call_kwargs["client"] is services.client


@pytest.mark.asyncio
async def test_make_delete_apply_204_remains_success():
    """Control case: a normal 204 No Content still returns None and the
    fast-path (no error) is preserved.
    """
    from katana_mcp.tools._modification_dispatch import make_delete_apply

    services = _build_services_mock()
    endpoint, _response = _build_delete_endpoint_mock(status_code=204)

    apply = make_delete_apply(endpoint, services, target_id=7)
    result = await apply()

    assert result is None


@pytest.mark.asyncio
async def test_make_delete_apply_400_still_raises():
    """Control case: 4xx that isn't 404 must still surface as an error
    so the dispatcher can fail-fast — only 404 gets the idempotent
    treatment.
    """
    from katana_mcp.tools._modification_dispatch import make_delete_apply

    from katana_public_api_client.utils import APIError

    services = _build_services_mock()
    endpoint, _response = _build_delete_endpoint_mock(status_code=400)

    apply = make_delete_apply(endpoint, services, target_id=7)

    with pytest.raises(APIError):
        await apply()


@pytest.mark.asyncio
async def test_make_delete_apply_500_still_raises():
    """Control case: server errors (5xx) must still surface so the
    dispatcher fails fast and the caller learns Katana is unhappy.
    """
    from katana_mcp.tools._modification_dispatch import make_delete_apply

    from katana_public_api_client.utils import APIError

    services = _build_services_mock()
    endpoint, _response = _build_delete_endpoint_mock(status_code=500)

    apply = make_delete_apply(endpoint, services, target_id=7)

    with pytest.raises(APIError):
        await apply()


@pytest.mark.asyncio
async def test_execute_plan_with_mixed_204_and_404_marks_both_succeeded():
    """Integration-ish: with two deletes where the first lands at 204
    and the second hits 404 (already gone), both ActionResults should
    show ``succeeded=True``. This is the bug-report scenario from #777
    — stale tombstone IDs in a delete batch should no longer abort the
    plan.
    """
    from katana_mcp.tools._modification_dispatch import make_delete_apply

    services = _build_services_mock()
    live_endpoint, _ = _build_delete_endpoint_mock(status_code=204, name="delete_live")
    gone_endpoint, _ = _build_delete_endpoint_mock(status_code=404, name="delete_gone")

    plan = [
        ActionSpec(
            operation="delete_recipe_row",
            target_id=5001,
            apply=make_delete_apply(live_endpoint, services, target_id=5001),
        ),
        ActionSpec(
            operation="delete_recipe_row",
            target_id=5002,
            apply=make_delete_apply(gone_endpoint, services, target_id=5002),
        ),
    ]

    results = await execute_plan(plan)

    assert len(results) == 2
    assert all(r.succeeded is True for r in results)
    assert all(r.error is None for r in results)


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


# ============================================================================
# run_modify_plan — post-apply cache write-through (Bug #2)
#
# After execute_plan succeeds, if ``cache`` + ``refetch_for_merge`` are
# provided, the dispatcher must re-fetch the parent and merge it via
# ``merge_filtered_fetch`` so the typed cache stays in sync without a
# rebuild_cache. Pre-2026-05-12 the cache went stale until next sync.
# ============================================================================


@pytest.mark.asyncio
async def test_run_modify_plan_post_apply_merge_fires_on_success(monkeypatch):
    """When cache + refetch_for_merge are wired and the plan succeeds,
    the dispatcher refetches the parent and calls merge_filtered_fetch
    with the matching EntitySpec.
    """
    from katana_mcp.tools._modification_dispatch import run_modify_plan

    captured: dict[str, object] = {}

    async def fake_merge(cache, spec, attrs_objs):
        captured["cache"] = cache
        captured["spec_key"] = spec.entity_key
        captured["attrs_objs"] = list(attrs_objs)

    monkeypatch.setattr("katana_mcp.typed_cache.sync.merge_filtered_fetch", fake_merge)

    refetched_parent = object()

    async def fake_apply():
        return object()

    async def fake_refetch(eid: int):
        captured["refetched_id"] = eid
        return refetched_parent

    request = _SampleRequest(id=42, name="x", preview=False)
    plan = [
        ActionSpec(
            operation="update_header",
            target_id=42,
            diff=[FieldChange(field="status", old="DRAFT", new="DONE")],
            apply=fake_apply,
            verify=None,
        )
    ]

    fake_cache = cast(TypedCacheEngine, object())
    response = await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="purchase_order",
            entity_label="purchase order 42",
            tool_name="modify_purchase_order",
        ),
        web_url_kind=None,
        existing=None,
        plan=plan,
        has_get_endpoint=False,
        cache_merge=CacheMerge(cache=fake_cache, refetch_for_merge=fake_refetch),
    )

    assert response.is_preview is False
    assert captured == {
        "cache": fake_cache,
        "spec_key": "purchase_order",
        "attrs_objs": [refetched_parent],
        "refetched_id": 42,
    }


@pytest.mark.asyncio
async def test_run_modify_plan_overlays_patch_response_on_stale_refetch(monkeypatch):
    """Bug #2b: defeat Katana read-replica lag on the post-apply refetch.

    Setup: the PATCH apply returns a fresh outcome with ``name="FRESH"``,
    but the cache-merge refetch (simulating a stale read replica) returns
    a parent with ``name="STALE"``. Without the overlay the cache would be
    silently corrupted with the pre-modify value — the regression we saw
    on 2026-05-18 in the supplier-code session.

    Asserts: the attrs object passed to ``merge_filtered_fetch`` carries
    the FRESH value, because the dispatcher copied it from the PATCH
    response body onto the stale GET refetch before merge.
    """
    from katana_mcp.tools._modification_dispatch import run_modify_plan

    fresh_outcome = _AttrsStub(name="FRESH")
    stale_parent = _AttrsStub(name="STALE")

    captured: dict[str, Any] = {}

    async def fake_merge(cache, spec, attrs_objs):
        captured["attrs_objs"] = list(attrs_objs)

    monkeypatch.setattr("katana_mcp.typed_cache.sync.merge_filtered_fetch", fake_merge)

    async def fake_apply():
        return fresh_outcome

    async def fake_refetch(_eid: int):
        return stale_parent

    request = _SampleRequest(id=42, name="FRESH", preview=False)
    plan = [
        ActionSpec(
            operation="update_header",
            target_id=42,  # matches request.id — parent-level action
            diff=[FieldChange(field="name", old="STALE", new="FRESH")],
            apply=fake_apply,
            verify=None,
        )
    ]

    fake_cache = cast(TypedCacheEngine, object())
    await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="purchase_order",
            entity_label="purchase order 42",
            tool_name="modify_purchase_order",
        ),
        web_url_kind=None,
        existing=None,
        plan=plan,
        has_get_endpoint=False,
        cache_merge=CacheMerge(cache=fake_cache, refetch_for_merge=fake_refetch),
    )

    # The merged object IS the stale refetch (same identity), but its
    # ``name`` attribute has been overwritten in-place by the overlay.
    merged = captured["attrs_objs"][0]
    assert merged is stale_parent
    assert merged.name == "FRESH"


@pytest.mark.asyncio
async def test_run_modify_plan_overlay_skips_row_level_actions(monkeypatch):
    """Parent overlay only applies to actions whose ``target_id`` matches
    the request's entity id. Row-level actions (e.g. ``update_row`` on a
    PO row, target_id=row_id != po_id) must NOT contribute to the parent
    overlay — their fields belong on a row class, not the parent class.
    """
    from katana_mcp.tools._modification_dispatch import run_modify_plan

    # Outcome from a row-level PATCH — has a ``quantity`` field that
    # happens to also exist on the parent (coincidence). If we naively
    # overlaid, the parent's quantity would be clobbered by the row's.
    row_outcome = _AttrsStub(quantity=999)
    parent_refetch = _AttrsStub(quantity=42)

    captured: dict[str, Any] = {}

    async def fake_merge(cache, spec, attrs_objs):
        captured["attrs_objs"] = list(attrs_objs)

    monkeypatch.setattr("katana_mcp.typed_cache.sync.merge_filtered_fetch", fake_merge)

    async def fake_apply():
        return row_outcome

    async def fake_refetch(_eid: int):
        return parent_refetch

    request = _SampleRequest(id=42, qty=10, preview=False)
    plan = [
        ActionSpec(
            operation="update_row",
            target_id=999,  # row id — does NOT match request.id (42)
            diff=[FieldChange(field="quantity", old=42, new=999)],
            apply=fake_apply,
            verify=None,
        )
    ]

    fake_cache = cast(TypedCacheEngine, object())
    await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="purchase_order",
            entity_label="purchase order 42",
            tool_name="modify_purchase_order",
        ),
        web_url_kind=None,
        existing=None,
        plan=plan,
        has_get_endpoint=False,
        cache_merge=CacheMerge(cache=fake_cache, refetch_for_merge=fake_refetch),
    )

    merged = captured["attrs_objs"][0]
    assert merged is parent_refetch
    assert merged.quantity == 42  # untouched — overlay skipped the row action


@pytest.mark.asyncio
async def test_run_modify_plan_overlay_skips_unset_values(monkeypatch):
    """UNSET on the PATCH response means "Katana didn't echo this field"
    — we should NOT overlay UNSET onto the GET value. The GET stays.
    """
    from katana_mcp.tools._modification_dispatch import run_modify_plan

    # Outcome echoes ``name`` but not ``qty`` (qty is UNSET — Katana
    # didn't include it in the response body for some reason).
    outcome = _AttrsStub(name="FRESH_NAME", qty=UNSET)
    refetched = _AttrsStub(name="STALE_NAME", qty=7)

    captured: dict[str, Any] = {}

    async def fake_merge(cache, spec, attrs_objs):
        captured["attrs_objs"] = list(attrs_objs)

    monkeypatch.setattr("katana_mcp.typed_cache.sync.merge_filtered_fetch", fake_merge)

    async def fake_apply():
        return outcome

    async def fake_refetch(_eid: int):
        return refetched

    request = _SampleRequest(id=42, name="FRESH_NAME", qty=7, preview=False)
    plan = [
        ActionSpec(
            operation="update_header",
            target_id=42,
            diff=[
                FieldChange(field="name", old="STALE_NAME", new="FRESH_NAME"),
                FieldChange(field="qty", old=7, new=7, is_unchanged=True),
            ],
            apply=fake_apply,
            verify=None,
        )
    ]

    fake_cache = cast(TypedCacheEngine, object())
    await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="purchase_order",
            entity_label="purchase order 42",
            tool_name="modify_purchase_order",
        ),
        web_url_kind=None,
        existing=None,
        plan=plan,
        has_get_endpoint=False,
        cache_merge=CacheMerge(cache=fake_cache, refetch_for_merge=fake_refetch),
    )

    merged = captured["attrs_objs"][0]
    assert merged.name == "FRESH_NAME"  # overlaid (non-UNSET)
    assert merged.qty == 7  # UNSET in outcome — GET value preserved


@pytest.mark.asyncio
async def test_run_modify_plan_no_merge_when_cache_or_refetch_missing(monkeypatch):
    """The merge code path is gated on BOTH cache and refetch_for_merge
    being non-None — either missing skips the merge silently. Lets tools
    opt out without ceremony (e.g. stock_transfers, which lacks a GET).
    """
    from katana_mcp.tools._modification_dispatch import run_modify_plan

    call_count = {"merge": 0}

    async def fake_merge(_cache, _spec, _objs):
        call_count["merge"] += 1

    monkeypatch.setattr("katana_mcp.typed_cache.sync.merge_filtered_fetch", fake_merge)

    async def fake_apply():
        return None

    plan = [ActionSpec(operation="add_row", target_id=1, apply=fake_apply, verify=None)]
    request = _SampleRequest(id=1, name="x", preview=False)

    # Neither wired (no cache_merge):
    await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="purchase_order",
            entity_label="purchase order 1",
            tool_name="modify_purchase_order",
        ),
        web_url_kind=None,
        existing=None,
        plan=plan,
        has_get_endpoint=False,
    )

    assert call_count["merge"] == 0


@pytest.mark.asyncio
async def test_run_modify_plan_no_merge_when_action_failed(monkeypatch):
    """Cache merge must not fire if any action in the plan failed —
    the partial post-state would corrupt the cache.
    """
    call_count = {"merge": 0}

    async def fake_merge(_cache, _spec, _objs):
        call_count["merge"] += 1

    monkeypatch.setattr("katana_mcp.typed_cache.sync.merge_filtered_fetch", fake_merge)

    async def bad_apply():
        raise ValueError("apply failed")

    async def fake_refetch(_eid: int):
        return object()

    plan = [ActionSpec(operation="add_row", target_id=1, apply=bad_apply, verify=None)]
    request = _SampleRequest(id=1, name="x", preview=False)

    await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="purchase_order",
            entity_label="purchase order 1",
            tool_name="modify_purchase_order",
        ),
        web_url_kind=None,
        existing=None,
        plan=plan,
        has_get_endpoint=False,
        cache_merge=CacheMerge(
            cache=cast(TypedCacheEngine, object()),
            refetch_for_merge=fake_refetch,
        ),
    )

    assert call_count["merge"] == 0


@pytest.mark.asyncio
async def test_run_modify_plan_merge_skips_silently_for_uncached_entity(
    monkeypatch,
):
    """If entity_type isn't in ENTITY_SPECS (e.g. a custom non-cached
    entity), the merge step skips without raising. Tool's API write is
    still authoritative.
    """
    call_count = {"merge": 0}

    async def fake_merge(_cache, _spec, _objs):
        call_count["merge"] += 1

    monkeypatch.setattr("katana_mcp.typed_cache.sync.merge_filtered_fetch", fake_merge)

    async def fake_apply():
        return None

    async def fake_refetch(_eid: int):
        return object()

    plan = [ActionSpec(operation="add_row", target_id=1, apply=fake_apply, verify=None)]
    request = _SampleRequest(id=1, name="x", preview=False)

    response = await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="not_a_real_entity",
            entity_label="bogus 1",
            tool_name="modify_bogus",
        ),
        web_url_kind=None,
        existing=None,
        plan=plan,
        has_get_endpoint=False,
        cache_merge=CacheMerge(
            cache=cast(TypedCacheEngine, object()),
            refetch_for_merge=fake_refetch,
        ),
    )

    assert call_count["merge"] == 0
    assert response.is_preview is False  # the modify response itself still succeeds


@pytest.mark.asyncio
async def test_run_modify_plan_merge_failure_does_not_break_response(monkeypatch):
    """If the post-apply merge raises (e.g. cache lock contention,
    transient DB error), the dispatcher logs and returns the successful
    modify response — the API write already landed, the only loss is
    cache freshness.
    """

    async def boom_merge(_cache, _spec, _objs):
        raise RuntimeError("cache I/O failed")

    monkeypatch.setattr("katana_mcp.typed_cache.sync.merge_filtered_fetch", boom_merge)

    async def fake_apply():
        return None

    async def fake_refetch(_eid: int):
        return object()

    plan = [ActionSpec(operation="add_row", target_id=1, apply=fake_apply, verify=None)]
    request = _SampleRequest(id=1, name="x", preview=False)

    response = await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="purchase_order",
            entity_label="purchase order 1",
            tool_name="modify_purchase_order",
        ),
        web_url_kind=None,
        existing=None,
        plan=plan,
        has_get_endpoint=False,
        cache_merge=CacheMerge(
            cache=cast(TypedCacheEngine, object()),
            refetch_for_merge=fake_refetch,
        ),
    )

    # Modify response still reports success — merge is best-effort.
    assert response.is_preview is False
    assert response.actions[0].succeeded is True


@pytest.mark.asyncio
async def test_run_modify_plan_preview_does_not_merge(monkeypatch):
    """``preview=True`` must short-circuit before the cache merge — the
    cache should never observe a planned-but-not-applied change.
    Structural guarantee via the early return at the preview gate;
    pinned here so a future refactor can't move the merge above it.
    """
    call_count = {"merge": 0, "refetch": 0}

    async def fake_merge(_cache, _spec, _objs):
        call_count["merge"] += 1

    monkeypatch.setattr("katana_mcp.typed_cache.sync.merge_filtered_fetch", fake_merge)

    async def fake_apply():
        return None

    async def fake_refetch(_eid: int):
        call_count["refetch"] += 1
        return object()

    plan = [ActionSpec(operation="add_row", target_id=1, apply=fake_apply, verify=None)]
    request = _SampleRequest(id=1, name="x", preview=True)

    response = await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="purchase_order",
            entity_label="purchase order 1",
            tool_name="modify_purchase_order",
        ),
        web_url_kind=None,
        existing=None,
        plan=plan,
        has_get_endpoint=False,
        cache_merge=CacheMerge(
            cache=cast(TypedCacheEngine, object()),
            refetch_for_merge=fake_refetch,
        ),
    )

    assert response.is_preview is True
    assert call_count == {"merge": 0, "refetch": 0}


@pytest.mark.asyncio
async def test_run_modify_plan_refetch_related_fans_out_to_related_specs(monkeypatch):
    """When a tool wires ``refetch_related``, the dispatcher refetches and
    merges each related spec's rows after the parent merge. Closes the
    MO recipe-row gap: ``MANUFACTURING_ORDER_SPEC.related_specs`` points
    at ``manufacturing_order_recipe_row`` (separate endpoint, not
    embedded in the MO parent fetch).
    """
    merges: list[str] = []

    async def fake_merge(_cache, spec, attrs_objs):
        merges.append(f"{spec.entity_key}:{len(list(attrs_objs))}")

    monkeypatch.setattr("katana_mcp.typed_cache.sync.merge_filtered_fetch", fake_merge)

    async def fake_apply():
        return None

    async def fake_refetch_parent(_eid: int):
        return object()  # parent attrs (content irrelevant for this test)

    async def fake_refetch_recipe_rows(_eid: int):
        return [object(), object()]  # two recipe rows

    plan = [ActionSpec(operation="add_row", target_id=1, apply=fake_apply, verify=None)]
    request = _SampleRequest(id=1, name="x", preview=False)

    await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="manufacturing_order",
            entity_label="manufacturing order 1",
            tool_name="modify_manufacturing_order",
        ),
        web_url_kind=None,
        existing=None,
        plan=plan,
        has_get_endpoint=False,
        cache_merge=CacheMerge(
            cache=cast(TypedCacheEngine, object()),
            refetch_for_merge=fake_refetch_parent,
            refetch_related=(
                ("manufacturing_order_recipe_row", fake_refetch_recipe_rows),
            ),
        ),
    )

    # Parent merged first, then related rows. Two recipe rows on the
    # related-spec merge call.
    assert merges == ["manufacturing_order:1", "manufacturing_order_recipe_row:2"]


@pytest.mark.asyncio
async def test_run_modify_plan_refetch_related_error_does_not_break(monkeypatch):
    """A failure inside one ``refetch_related`` refetcher logs and is
    skipped — it shouldn't roll back the parent merge or the modify
    response.
    """
    merges: list[str] = []

    async def fake_merge(_cache, spec, _objs):
        merges.append(spec.entity_key)

    monkeypatch.setattr("katana_mcp.typed_cache.sync.merge_filtered_fetch", fake_merge)

    async def fake_apply():
        return None

    async def fake_refetch_parent(_eid: int):
        return object()

    async def bad_refetch_related(_eid: int):
        raise RuntimeError("recipe-row fetch failed")

    plan = [ActionSpec(operation="add_row", target_id=1, apply=fake_apply, verify=None)]
    request = _SampleRequest(id=1, name="x", preview=False)

    response = await run_modify_plan(
        request=request,
        naming=EntityNaming(
            entity_type="manufacturing_order",
            entity_label="manufacturing order 1",
            tool_name="modify_manufacturing_order",
        ),
        web_url_kind=None,
        existing=None,
        plan=plan,
        has_get_endpoint=False,
        cache_merge=CacheMerge(
            cache=cast(TypedCacheEngine, object()),
            refetch_for_merge=fake_refetch_parent,
            refetch_related=(("manufacturing_order_recipe_row", bad_refetch_related),),
        ),
    )

    # Parent merge still fired; related merge skipped but no exception
    # bubbled up. Modify response itself still succeeds.
    assert merges == ["manufacturing_order"]
    assert response.is_preview is False
