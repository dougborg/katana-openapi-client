"""Prefab UI builders for Katana MCP Server tool responses.

Provides reusable Prefab component builders that produce rich interactive UIs
for MCP Apps-capable hosts (Claude Desktop, etc.) via the
``ui://prefab/renderer.html`` resource auto-registered by fastmcp 3.x.

Usage::

    from katana_mcp.tools.prefab_ui import (
        build_search_results_ui,
        build_item_detail_ui,
        build_po_create_ui,
        build_so_create_ui,
        build_mo_create_ui,
    )

    # In a tool's *_to_tool_result function:
    items_dicts = [item.model_dump() for item in response.items]
    app = build_search_results_ui(items_dicts, query, response.total_count)
    return make_tool_result(response, ui=app)

Design conventions
------------------

**Link Katana entities wherever possible.** When a card displays a
field that maps to a Katana entity with a known web URL (suppliers,
customers, products, materials, orders, etc. — see
``katana_mcp.web_urls.EntityKind``), render it as a ``Link`` with
``href`` pointing at the Katana page, not as plain ``Text``.

A real anchor tag is a one-click path to the source of truth, costs
nothing in agent tokens or chat noise, and stays correct regardless
of which host renders the iframe. The variant card uses this pattern
twice (parent product/material on the title; default supplier in
the reference section); future card work should follow the same
shape. If a field corresponds to a Katana entity not yet in
``EntityKind``, add the path template in ``web_urls.py`` and wire
the link.

**Action primitive selection.** Card actions choose between four
host primitives based on intent:

- ``CallTool(tool, arguments={...})`` — deterministic tool re-invocation
  when every required argument is resolvable at card-build time, either
  from the response dict the builder receives or from a
  ``{{ result.<field> }}`` template that resolves against the apply-
  response state. ``Check Inventory`` (with a known SKU) and
  ``View Variant Details`` (with a known sku/variant_id) are the
  canonical follow-up shape. This is also the preview→apply rail:
  the Confirm button fires ``tools/call`` with the original args +
  ``preview=False`` and pushes the structured result back to the
  agent's model context via ``ui/update-model-context``. See ADR-0021
  for the rationale.
- ``OpenLink(url=...)`` — URL navigation; the host opens the link
  directly with no agent round-trip. Used for every ``View in Katana``
  button across the cards.
- ``UpdateContext(content="...")`` — push a chat-context update so the
  agent composes the next call itself. Right primitive when the next-
  step tool needs args the card can't produce (PO needs supplier +
  location + items; "MOs using this material" has no ingredient filter
  today — #758; receive needs per-row items; open-ended modifies). Also
  used on the Cancel button to signal the user opted out without
  polluting the chat history.
- ``SendMessage(...)`` — legacy chat-prompt primitive. Reserved for
  fallback uses where the agent needs to *speak* (rare; usually prefer
  ``UpdateContext``).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, Any, Literal

if TYPE_CHECKING:
    from katana_mcp.tools.foundation.orders import FulfillOrderRequest

from babel.numbers import format_currency
from prefab_ui.actions import Action, SetState, ShowToast
from prefab_ui.actions.mcp import CallTool, UpdateContext
from prefab_ui.actions.navigation import OpenLink
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    H3,
    Alert,
    AlertDescription,
    AlertTitle,
    Badge,
    Button,
    Card,
    CardContent,
    CardFooter,
    CardHeader,
    CardTitle,
    Code,
    Column,
    DataTable,
    DataTableColumn,
    Link,
    Metric,
    Muted,
    Row,
    Separator,
    Text,
)
from prefab_ui.components.control_flow import Elif, Else, If
from prefab_ui.components.slot import Slot
from prefab_ui.rx import EVENT, RESULT, Rx
from pydantic import BaseModel

from katana_mcp.logging import get_logger
from katana_mcp.tools._addresses import addresses_are_equivalent
from katana_mcp.tools.foundation.bin_row_table import (
    merge_bin_row_rows_for_modify_card,
    prepare_bin_row_table_rows,
)
from katana_mcp.tools.foundation.bom_table import (
    _derive_status_label,
    _merge_bom_rows_for_modify_card,
    _prepare_bom_table_rows,
    _summarize_apply_outcome,
)
from katana_mcp.tools.foundation.collection_diff import collection_diff_summary
from katana_mcp.tools.foundation.item_variant_table import (
    merge_variant_rows_for_modify_card,
    prepare_variant_table_rows,
)
from katana_mcp.tools.foundation.mo_tables import (
    merge_operation_rows_for_modify_card,
    merge_productions_for_modify_card,
    merge_recipe_rows_for_modify_card,
    prepare_operation_table_rows,
    prepare_production_table_rows,
    prepare_recipe_table_rows,
)
from katana_mcp.tools.foundation.po_row_table import (
    merge_po_row_rows_for_modify_card,
    prepare_po_row_table_rows,
)
from katana_mcp.tools.tool_result_utils import BLOCK_WARNING_PREFIX, float_or_none
from katana_mcp.web_urls import (
    EntityKind,
    ecommerce_platform_label,
    ecommerce_storefront_url,
    katana_web_url,
)

logger = get_logger(__name__)

# Default rows-per-page for the module's DataTables. See ``_paginate`` for why
# pagination is opt-in rather than always-on.
_DEFAULT_TABLE_PAGE_SIZE = 20


def _paginate(
    row_count: int, *, page_size: int = _DEFAULT_TABLE_PAGE_SIZE
) -> dict[str, Any]:
    """DataTable pagination kwargs that avoid blank filler rows.

    The renderer pads a *paginated* table with empty filler rows up to
    ``pageSize`` to keep height stable across pages, and there's no prop to
    disable that — so a short table that fits on one page renders blank rows
    below its data (the renderer gate is ``paginated && rowCount < pageSize``).
    The only lever we control is whether to paginate at all.

    Returns ``paginated=True`` (with ``pageSize``) only when ``row_count``
    overflows a single page; otherwise pagination — and the filler rows and
    now-pointless ``Page 1 of 1`` footer — is disabled. Pass the length of the
    Python list backing the table's ``rows`` (whatever it's named at the call
    site), then spread the result into ``DataTable``::

        DataTable(columns=..., rows="{{ items }}", **_paginate(len(items)))
    """
    if row_count > page_size:
        return {"paginated": True, "pageSize": page_size}
    return {"paginated": False}


def with_display_rows(
    entity: dict[str, Any],
    cells: list[dict[str, Any]],
    *,
    display_key: str = "rows_display",
) -> dict[str, Any]:
    """Attach pre-formatted DataTable display cells to an entity's card state
    WITHOUT clobbering its authoritative row data.

    A detail card binds its line-item DataTable to a mustache key in
    ``PrefabApp(state=...)``. The natural-but-wrong shape is
    ``{**entity, "rows": cells}`` — overwriting the authoritative rows (which
    carry row ``id`` / ``variant_id`` / discounts / tax IDs) with display-only
    cells. That drops the identifiers a follow-up mutation keys on
    (``update_rows`` / ``delete_row_ids`` …). It only *looks* harmless because
    the full row data still rides in the ToolResult ``content`` channel — but
    some hosts forward **only** ``structured_content`` to the model and drop
    ``content`` (anthropics/claude-code#55677), so a display-only reduction
    there strips the IDs from model context. (This is what sent an agent
    scraping the Katana web UI for sales-order row data.)

    This helper enforces the fix: it writes ``cells`` to a **separate**
    ``display_key`` (bind the DataTable to that) and leaves the entity's own
    authoritative keys untouched. It refuses to overwrite an existing
    ``display_key`` so a future caller can't reintroduce the clobber by accident.

    Bind the table to ``{{ <entity>.<display_key> }}`` and let the model read
    identifiers from the entity's authoritative row key. See
    :func:`build_so_detail_ui` for the canonical call site.
    """
    if display_key in entity:
        raise ValueError(
            f"with_display_rows: {display_key!r} already present on entity — "
            f"refusing to overwrite (would risk clobbering authoritative data)."
        )
    return {**entity, display_key: cells}


def _split_warnings(
    warnings: list[str] | None,
) -> tuple[list[str], list[str]]:
    """Split a warnings list into (block_warnings, regular_warnings).

    Block warnings have the ``BLOCK:`` prefix stripped so they render as plain
    user-facing text. Their presence tells the caller to omit the Confirm
    button. Regular warnings render as informational badges only.
    """
    if not warnings:
        return [], []
    blocks: list[str] = []
    regulars: list[str] = []
    for w in warnings:
        if w.startswith(BLOCK_WARNING_PREFIX):
            blocks.append(w[len(BLOCK_WARNING_PREFIX) :].lstrip())
        else:
            regulars.append(w)
    return blocks, regulars


# Status-bucket mapping per entity. Each entity's terminal-success / active
# (in-progress) / blocked statuses go in their respective sets; statuses
# absent from every set fall through to "neutral" (the not-started bucket).
_StatusBucket = Literal["success", "active", "blocked", "neutral"]
_STATUS_BUCKETS: dict[str, dict[_StatusBucket, set[str]]] = {
    "purchase_order": {
        "success": {"RECEIVED"},
        "active": {"PARTIALLY_RECEIVED"},
        "blocked": set(),
        "neutral": set(),
    },
    "sales_order": {
        "success": {"DELIVERED"},
        "active": {"PARTIALLY_SHIPPED", "PACKED"},
        "blocked": set(),
        "neutral": set(),
    },
    "manufacturing_order": {
        "success": {"DONE"},
        "active": {"IN_PROGRESS", "PARTIALLY_COMPLETED"},
        "blocked": {"BLOCKED"},
        "neutral": set(),
    },
    "stock_transfer": {
        "success": {"RECEIVED"},
        "active": {"IN_TRANSIT"},
        "blocked": set(),
        "neutral": set(),
    },
    "bin_transfer": {
        "success": {"DONE"},
        "active": {"IN_TRANSIT"},
        "blocked": set(),
        "neutral": {"CREATED"},
    },
}
_BUCKET_TO_VARIANT: dict[_StatusBucket, str] = {
    "success": "default",  # green — terminal happy path
    "active": "secondary",  # gray — in progress
    "blocked": "destructive",  # red — needs attention
    "neutral": "outline",  # neutral — not yet started
}


def status_badge_variant(entity: str, status: str | None) -> str:
    """Return the Prefab ``Badge`` variant string for an entity's status.

    Generic buckets:
    - ``default`` (green) — terminal-success states (PO RECEIVED, SO DELIVERED,
      MO DONE).
    - ``secondary`` (gray) — active / in-progress states (PARTIALLY_*, PACKED,
      IN_PROGRESS).
    - ``destructive`` (red) — blocked / problem states (MO BLOCKED).
    - ``outline`` (neutral) — unstarted / unknown statuses (NOT_RECEIVED,
      NOT_SHIPPED, NOT_STARTED, ``None``, unknown entity).

    Used by every preview/apply card's Tier 1 status badge. Follow-up card
    families extend ``_STATUS_BUCKETS`` with their entity's statuses.
    """
    if status is None:
        return "outline"
    buckets = _STATUS_BUCKETS.get(entity, {})
    for bucket_name, members in buckets.items():
        if status in members:
            return _BUCKET_TO_VARIANT[bucket_name]
    return "outline"


# Coaching text appended to every preview-mode write tool's description.
# The agent's host may or may not render MCP Apps iframes — lead with the
# no-iframe path because it's the footgun: in iframe hosts the buttons
# handle the UX with no agent help, but in non-iframe hosts an agent that
# follows the iframe-happy-path coaching ends its turn waiting for clicks
# that never come (see #648). Mention the iframe path second.
#
# The unified Confirm-fires-CallTool / Cancel-fires-UpdateContext rail
# rationale lives in ADR-0021 (supersedes ADR-0015's SendMessage rail).
PREVIEW_APPLY_COACHING = (
    "Preview→apply pattern: when ``preview=True`` (default) the tool returns "
    "a Prefab card describing the planned change. The ``content`` channel of "
    "the tool result carries the response JSON, so you always have the data "
    "even if the card itself doesn't render. Handle both host scenarios:\n\n"
    "1. If the host does NOT render MCP Apps iframes (Claude Code, plain CLI "
    "clients, etc.) — common signal: the user says they can't see the card, "
    "or you have no other evidence the card was rendered — the Prefab card "
    "is invisible. Summarize the planned change in chat from the ``content`` "
    "JSON (what's changing, key field values), ask the user to confirm, then "
    "re-issue the call with ``preview=False`` yourself. Do NOT end your turn "
    "waiting for a button click — there is none.\n\n"
    "2. If the host DOES render iframes (Claude Desktop, Claude.ai, Cowork, "
    "etc.), the card has Confirm/Cancel buttons the user clicks. When the "
    "user clicks Confirm in the iframe, the iframe fires the apply call "
    "directly and morphs in place to a result card. The structured apply "
    "response (id, status, etc.) arrives in your context on your next turn "
    "via ``ui/update-model-context``. Treat it as you would any tool-call "
    "result — acknowledge completion, suggest next steps. Do NOT re-narrate "
    "the preview card, do NOT ask for confirmation in chat (the buttons "
    "handle that), and Do NOT re-issue the call after the iframe already "
    "applied. End your turn after the preview response. If you receive an "
    "``UpdateContext`` notification that the user cancelled the preview, "
    "acknowledge briefly without re-issuing."
)


def with_preview_coaching(fn: Any) -> str:
    """Build a FastMCP tool description by appending preview→apply coaching
    to the function's docstring.

    All preview-mode write tools share a single coaching variant: Confirm
    fires the apply ``tools/call`` directly and pushes the result via
    ``ui/update-model-context``; the agent does not re-issue.

    Most callers should use :func:`register_preview_tool` rather than
    calling this directly.
    """
    base = (fn.__doc__ or "").strip()
    return f"{base}\n\n{PREVIEW_APPLY_COACHING}" if base else PREVIEW_APPLY_COACHING


def register_preview_tool(
    mcp: Any,
    fn: Any,
    *,
    tags: set[str],
    annotations: Any,
    meta: Any = None,
) -> None:
    """Register a preview-mode write tool with standard coaching applied.

    All preview tools use the unified direct-apply rail (Confirm fires
    ``tools/call`` directly and pushes the structured result back via
    ``ui/update-model-context``); see ADR-0021 for the architectural
    rationale.
    """
    mcp.tool(
        description=with_preview_coaching(fn),
        tags=tags,
        annotations=annotations,
        meta=meta,
    )(fn)


def _build_apply_action(
    confirm_tool: str | None,
    confirm_request: BaseModel | None,
    *,
    extra_on_success: list[Action] | None = None,
) -> list[Action] | None:
    """Construct the Confirm-button click action chain, or ``None`` when
    both inputs are ``None``.

    The chain is ``[SetState(pending, True), CallTool(...)]``. Setting
    ``pending=True`` synchronously before the call fires is the spam guard:
    the buttons bind ``disabled=Rx("pending") | ...`` so a second click
    while the call is in flight is dropped (no duplicate POs). The
    ``on_success`` / ``on_error`` chains clear ``pending`` and flip
    ``applied`` / ``error`` for the in-place morph.

    On success the iframe pushes the structured result back to the agent's
    model context via ``ui/update-model-context`` (MCP Apps spec,
    SEP-1865, 2026-01-26). The agent sees the result on its next turn —
    no re-issue needed.

    On error the iframe shows the error inline and pushes the error
    reason into model context so the agent can react on its next turn.

    The ``UpdateContext.content`` field (text channel) is the spec-correct
    one for agent-visible context: per the MCP Apps spec, ``content``
    reaches the model; ``structuredContent`` is for UI rendering and is
    not guaranteed in model context.

    See ``docs/adr/0021-unified-direct-apply-rail.md`` for the
    architectural rationale (supersedes ADR-0015's SendMessage rail).

    ``confirm_tool`` and ``confirm_request`` must be both set or both
    ``None`` (the latter for builders that render their non-preview
    branch — no Confirm button to wire).
    """
    if confirm_tool is None and confirm_request is None:
        return None
    if confirm_tool is None or confirm_request is None:
        raise ValueError(
            "confirm_tool and confirm_request must be set together (or both None)"
        )
    args = confirm_request.model_dump(mode="json")
    if "preview" not in args:
        raise ValueError(
            f"_build_apply_action requires a request model with a "
            f"`preview` field; {type(confirm_request).__name__} has none. "
            f"Without that field the CallTool would re-issue {confirm_tool} "
            f"with an unrecognized preview=False argument, failing "
            f"validation downstream."
        )
    args["preview"] = False
    # The on_success chain runs the caller's extras BEFORE the generic
    # flags so a builder that pushes RESULT.actions into a state slot (e.g.
    # the modification card binding ``state.plan_actions`` for live-tick row
    # updates) sees its row data land before the iframe morphs to its
    # ``applied=True`` rendering.
    #
    # ``SetState("error", None)`` on success is the retry-cleanup: every
    # preview card renders an ``If("error")`` destructive Alert whenever
    # ``state.error`` is truthy, so a successful Retry click after an
    # earlier failure would leave the "Apply failed" Alert stuck on the
    # otherwise-applied card. Clearing the slot keeps the rendered state
    # internally consistent.
    on_success: list[Action] = [
        *(extra_on_success or []),
        SetState("pending", False),
        SetState("error", None),
        # ``result`` MUST land before ``applied`` flips — the applied-state
        # tree binds Buttons to ``{{ result.id }}`` / ``{{ result.katana_url }}``
        # templates (see ``_render_preview_footer``). Setting ``applied=True``
        # first would let the iframe render the morph with empty bindings
        # before ``result`` arrives.
        SetState("result", RESULT),
        SetState("applied", True),
        UpdateContext(content=RESULT),
    ]
    return [
        # Click guard — disables the button immediately so a double-click
        # in the iframe can't fire two applies (which would create
        # duplicate POs etc.). Cleared in on_success/on_error.
        SetState("pending", True),
        # Clear any prior error before re-firing the apply (this same
        # action chain backs the Retry button after an apply failure —
        # see ``_render_apply_button_row``). Without this the destructive
        # Alert from the failed previous attempt would stay visible
        # while the retry is in flight, contradicting the Pending pill.
        SetState("error", None),
        CallTool(
            tool=confirm_tool,
            arguments=args,
            on_success=on_success,
            on_error=[
                SetState("pending", False),
                SetState("error", "{{ $error }}"),
                ShowToast("{{ $error }}", variant="error"),
                UpdateContext(content="Apply failed: {{ $error }}"),
            ],
        ),
    ]


def _build_cancel_action(operation_label: str) -> list[Action]:
    """Construct the Cancel-button click action.

    Marks the preview card as ``cancelled`` (so the buttons gray out + a
    "Cancelled" pill appears) and pushes a context update so the agent
    knows the user opted out. The agent's tool description coaches it to
    acknowledge briefly and move on without re-issuing.

    ``operation_label`` is a human-readable phrase that already carries
    its own determiner — ``"the fulfillment"`` / ``"that purchase order"``
    / ``"the receipt for PO-123"`` / ``"those purchase order changes"`` —
    so the template embeds it verbatim. The previous template hard-coded
    a leading "the" which doubled up on every existing call site
    (``"User cancelled the the stock adjustment preview."``); fixed
    inline by letting the call site own the determiner.

    See ``docs/adr/0021-unified-direct-apply-rail.md`` for the
    architectural rationale (supersedes ADR-0015's ``SendMessage`` cancel
    indirection).
    """
    return [
        SetState("cancelled", True),
        UpdateContext(content=f"User cancelled {operation_label} preview."),
    ]


def _render_apply_button_row(
    *,
    confirm_label: str,
    apply_action: list[Action] | None,
    cancel_action: list[Action],
    disabled: bool = False,
) -> None:
    """Render the preview-card button row with state-aware visuals.

    States driven by iframe state (post-ADR-0021 unified rail):

    - **Default** — Confirm + Cancel buttons enabled.
    - **Pending…** — pill rendered, both buttons disabled. Set on click as
      the in-flight click guard so a double-click cannot fire two applies.
      Cleared in on_success / on_error.
    - **Applied** — pill rendered, both buttons disabled. Apply succeeded
      and the iframe morphed in place.
    - **Error** — pill rendered, both buttons disabled. Apply failed; the
      error reason is in iframe state and was pushed to the agent via
      ``ui/update-model-context``.
    - **Cancelled** — pill rendered, both buttons disabled, after Cancel
      click. The cancel action pushes an ``UpdateContext`` notification so
      the agent knows the user opted out.

    ``disabled=True`` is the block-warning fallback: only the Cancel button
    is offered (no Confirm). The Cancel button still binds
    ``disabled=Rx("cancelled")`` and renders a "Cancelled" pill on click,
    matching the spam-protection contract of the non-block-warning rail.
    """
    if disabled or apply_action is None:
        with Row(gap=2):
            with If("cancelled"):
                Badge(label="Cancelled", variant="secondary")
            Button(
                label="Cancel",
                variant="outline",
                on_click=cancel_action,
                disabled=Rx("cancelled"),
            )
        return

    # The primary button slot morphs through the state machine — same
    # DOM position across all states (layout-stable), but the label /
    # variant / on_click change to reflect what action is relevant for
    # the current state. Header Badge keeps showing the overall card
    # state (PREVIEW / APPLIED / FAILED) separately; the button is
    # specifically about "what action ran or can run next."
    #
    # State machine (unified direct-apply rail, ADR-0021):
    # - Preview:           ``Confirm Changes`` (default) → fires apply
    # - Pending:           ``Applying…`` (default + ``loader`` icon,
    #                      disabled)
    # - Applied + url:     ``View in Katana`` (success + ``external-link``
    #                      icon) → opens URL
    # - Applied no url:    ``Applied`` (success + ``check`` icon,
    #                      disabled) — successful delete nulls
    #                      katana_url
    # - Error:             ``Retry`` (warning + ``rotate-cw`` icon) →
    #                      re-fires apply; warning (amber) not
    #                      destructive (red) per the /ui-review audit —
    #                      destructive variant implies "this will
    #                      delete data" which is semantically wrong
    #                      for a retry affordance
    # - Cancelled:         ``Cancelled`` (outline, disabled)
    with Row(gap=2):
        with If("pending"):
            # Loader icon + spinner-style label conveys in-flight
            # state more clearly than the bare "Applying…" text.
            Button(
                label="Applying…",
                variant="default",
                icon="loader",
                disabled=True,
            )
        with Elif("applied"):
            with If("result.katana_url"):
                # Success variant (green) + external-link icon —
                # primary affordance on a successful apply is to
                # see the result in Katana.
                Button(
                    label="View in Katana",
                    variant="success",
                    icon="external-link",
                    on_click=OpenLink(url="{{ result.katana_url }}"),
                )
            with Else():
                # No URL (typically a successful delete) — keep
                # the success variant + check icon so the user
                # gets unambiguous confirmation the action ran.
                Button(
                    label="Applied",
                    variant="success",
                    icon="check",
                    disabled=True,
                )
        with Elif("error"):
            # Warning variant (amber) + rotate icon signals "the
            # previous attempt failed, click to redo." Destructive
            # variant (red) would imply "this will delete data" —
            # semantically wrong for a retry affordance (per the
            # /ui-review audit). The action re-fires apply_action,
            # which resets the rail via SetState("error", None) and
            # restarts the apply chain.
            Button(
                label="Retry",
                variant="warning",
                icon="rotate-cw",
                on_click=apply_action,
            )
        with Elif("cancelled"):
            Button(label="Cancelled", variant="outline", disabled=True)
        with Else():
            # Preview state — explicit ``disabled=Rx("pending")`` is
            # the belt-and-suspenders double-click guard: the
            # SetState("pending", True) at the start of the on_click
            # chain disables the button before If/Elif has a chance
            # to swap it. Both layers protect against rapid
            # double-click firing two CallTools.
            Button(
                label=confirm_label,
                variant="default",
                on_click=apply_action,
                disabled=Rx("pending"),
            )
        # Cancel button — disabled in all terminal states so the row
        # width stays constant (two buttons always visible). Cancel
        # only does anything in Preview.
        cancel_locked: Any = (
            Rx("pending") | Rx("cancelled") | Rx("applied") | Rx("error")
        )
        Button(
            label="Cancel",
            variant="outline",
            on_click=cancel_action,
            disabled=cancel_locked,
        )


def _check_inventory_action(
    handles: list[str | int] | list[str],
    *,
    fallback_content: str,
) -> Action:
    """Build the ``Check Inventory`` button click action.

    ``check_inventory`` accepts SKUs OR variant_ids in the same
    ``skus_or_variant_ids`` arg, so when at least one handle resolves at
    card-build time we emit ``CallTool`` for deterministic re-invocation.
    Otherwise we hand the agent an ``UpdateContext`` with
    ``fallback_content`` — every card has its own wording for the
    null-identity case (search-results vs low-stock vs fulfill-success).
    The fallback path is rare (variants can legally have ``sku=None``
    per CLAUDE.md, but rows with neither SKU nor variant_id are
    extremely uncommon).
    """
    if handles:
        return CallTool(
            "check_inventory",
            arguments={"skus_or_variant_ids": list(handles)},
        )
    return UpdateContext(content=fallback_content)


def _variant_details_action(
    sku: str | None,
    variant_id: int | None,
) -> Action | None:
    """Build the ``View Variant Details`` button click action.

    ``get_variant_details`` accepts either ``sku`` (string) or
    ``variant_id`` (int) — prefer SKU when present (clearer in the
    resulting tool call), else fall back to ``variant_id``. Returns
    ``None`` when neither identity is resolvable so callers can skip
    rendering the button entirely.
    """
    if sku:
        return CallTool("get_variant_details", arguments={"sku": sku})
    if variant_id is not None:
        return CallTool(
            "get_variant_details",
            arguments={"variant_id": variant_id},
        )
    return None


# ============================================================================
# Search & Browse UIs
# ============================================================================


def build_search_results_ui(
    items: list[dict[str, Any]],
    query: str,
    total_count: int,
) -> PrefabApp:
    """Build an interactive search results table with drill-down.

    Features:
    - Sortable, searchable DataTable (paginated only when results overflow
      one page — see ``_paginate``)
    - Row-click fires CallTool to get_variant_details, renders in Slot
    - Summary badges for query and count

    When ``total_count == 0``, drops the DataTable / drill-down Slot /
    "Check inventory" button — they all reference nonexistent results — and
    renders a friendly hint suggesting partial-SKU / name fallbacks. Closes
    #470.

    The "Check inventory for search results" button invokes
    ``check_inventory`` via ``CallTool`` with SKUs collected at card-build
    time. Falls back to ``UpdateContext`` if every result is SKU-less,
    asking the agent to resolve variant IDs.
    """
    with (
        PrefabApp(
            state={"items": items, "detail": None},
            css_class="p-4",
        ) as app,
        Column(gap=4),
    ):
        with Row(gap=2):
            H3(content="Search Results")
            Badge(label=f"Query: {query}", variant="outline")
            Badge(label=f"{total_count} items", variant="secondary")

        if total_count == 0:
            Muted(
                content=(
                    f'No items match "{query}". Try a partial SKU, variant '
                    "name, or parent product/material name — search uses "
                    "FTS5 with fuzzy fallback."
                )
            )
            return app

        DataTable(
            columns=[
                DataTableColumn(key="sku", header="SKU", sortable=True),
                DataTableColumn(key="name", header="Name", sortable=True),
                DataTableColumn(
                    key="is_sellable",
                    header="Sellable",
                    sortable=True,
                ),
                DataTableColumn(
                    key="is_archived",
                    header="Archived",
                    sortable=True,
                ),
            ],
            rows="{{ items }}",
            search=True,
            **_paginate(len(items)),
            # Per-row binding via ``$event``: the renderer spreads the
            # clicked row's dict into the action-scope as ``$event``, so
            # ``{{ $event.sku }}`` resolves to the row's SKU. The naive
            # form ``{{ sku }}`` does NOT work — only top-level scope keys
            # ($event, $result, $error, state keys) are direct lookups;
            # the row dict itself is not spread (#494, verified by browser
            # test ``test_search_results_row_click_passes_clicked_sku``).
            # ``{{ $error }}`` works because $error IS a top-level key.
            #
            # ``RESULT.view`` (not bare ``RESULT``) on the success path:
            # the tool returns a full PrefabApp envelope
            # (``{$prefab, view, defs, state}``) and the Slot renderer
            # expects a single component dict with a top-level ``type``.
            # Setting ``state.detail = $result.view`` extracts the
            # root view component so the Slot can render it (#494).
            onRowClick=CallTool(
                "get_variant_details",
                arguments={"sku": str(EVENT.sku)},
                on_success=SetState("detail", RESULT.view),
                on_error=ShowToast("{{ $error }}", variant="error"),
            ),
        )

        with Slot(name="detail"):
            Muted(content="Click a row to see variant details")

        # Collect SKUs at card-build time so Check Inventory becomes a
        # deterministic ``CallTool``; fall back to ``UpdateContext`` when
        # every result is SKU-less (rare legacy NetSuite-import shape —
        # see CLAUDE.md "Variants can have null SKUs").
        search_result_skus: list[str | int] = [
            item["sku"] for item in items if item.get("sku")
        ]
        with Row(gap=2):
            Button(
                label="Check inventory for search results",
                variant="outline",
                on_click=_check_inventory_action(
                    search_result_skus,
                    fallback_content=(
                        "User wants to check inventory for the items in the "
                        "search results, but none of the results carry a SKU. "
                        "Resolve variant IDs from the search and call "
                        "check_inventory with skus_or_variant_ids set to "
                        "those IDs."
                    ),
                ),
            )
    return app


def _variant_header_section(variant: dict[str, Any]) -> None:
    """Render variant card header: title (linked when a parent URL exists),
    badges, and config-attribute pills.

    ``display_name`` carries the Katana-UI-format name
    (``parent_name / value1 / value2``) computed via
    ``build_variant_display_name`` upstream, so we don't need a separate
    ``Part of:`` line — the parent name is the leading segment of the
    title. The ``katana_url`` on the response is the parent product /
    material URL (variants don't have their own page in Katana's web
    app); wrapping the title in a ``Link`` makes it an actual external
    anchor — clicking opens the parent page directly, no chat
    round-trip.
    """
    katana_url = variant.get("katana_url")
    # ``display_name`` is the canonical title. Falls back to legacy
    # ``name`` then SKU for safety — every code path through
    # ``_dict_to_variant_details`` populates ``display_name``, but this
    # guards against tests / future call sites that build the dict by
    # hand without it.
    title_content = (
        variant.get("display_name") or variant.get("name") or variant.get("sku") or ""
    )
    with Row(gap=2):
        with CardTitle():
            if katana_url:
                Link(content=title_content, href=katana_url, target="_blank")
            else:
                Text(content=title_content)
        Badge(label=variant.get("sku", ""), variant="outline")
        if variant.get("type"):
            Badge(label=variant["type"], variant="secondary")
        if variant.get("is_batch_tracked"):
            Badge(label="Batch tracked", variant="secondary")
    # Config-attribute pills label each axis ("Color: Red", "Size: Large")
    # explicitly. The slash-joined values in the title give scan-friendly
    # identity matching Katana's UI; these pills give axis context the
    # title can't convey.
    config_attrs = variant.get("config_attributes") or []
    if config_attrs:
        with Row(gap=2):
            for attr in config_attrs:
                if not isinstance(attr, dict):
                    continue
                label = attr.get("config_name") or ""
                value = attr.get("config_value") or ""
                if label and value:
                    Badge(label=f"{label}: {value}", variant="outline")


def _default_supplier_line(name: str | None, sid: int | None) -> None:
    """Render a "Default Supplier:" row.

    The name links to the Katana supplier page when the id is known —
    same external-link pattern the variant card title uses for its
    parent product / material. The supplier ID parenthetical was
    dropped; ID-as-text is available via ``structured_content`` for
    tooling.
    """
    if name and sid:
        supplier_url = katana_web_url("supplier", sid)
        if supplier_url:
            with Row(gap=1):
                Text(content="Default Supplier:")
                Link(content=name, href=supplier_url, target="_blank")
        else:
            Text(content=f"Default Supplier: {name}")
    elif name:
        Text(content=f"Default Supplier: {name}")
    elif sid:
        Text(content=f"Default Supplier ID: {sid}")


def _variant_supplier_line(variant: dict[str, Any]) -> None:
    _default_supplier_line(
        variant.get("default_supplier_name"),
        variant.get("default_supplier_id"),
    )


def _variant_barcode_line(variant: dict[str, Any]) -> None:
    """Render the barcode text row when at least one barcode is set."""
    parts = []
    if variant.get("internal_barcode"):
        parts.append(f"internal={variant['internal_barcode']}")
    if variant.get("registered_barcode"):
        parts.append(f"registered={variant['registered_barcode']}")
    if parts:
        Text(content=f"Barcodes: {', '.join(parts)}")


def _variant_purchase_uom_line(variant: dict[str, Any]) -> None:
    """Render the purchase-UoM conversion row when it differs from the stock UoM.

    Stays quiet in the common case (purchase and stock UoM match) so the
    card doesn't carry a noisy redundant row. Surfaces ``"Purchase UoM:
    kit (x4 pcs)"`` when an item is purchased in packs (kits, boxes,
    cases) and stocked as individual units — the conversion factor is
    the actionable bit for anyone drafting a PO.
    """
    purchase_uom = variant.get("purchase_uom")
    if not purchase_uom:
        return
    stock_uom = variant.get("uom")
    if purchase_uom == stock_uom:
        return
    # Katana returns this conversion rate as a fixed-precision decimal string
    # on item reads (e.g. "12.00000000000"); coalesce to float for display.
    rate = float_or_none(variant.get("purchase_uom_conversion_rate"))
    if rate is None:
        Text(content=f"Purchase UoM: {purchase_uom}")
        return
    rate_str = f"{rate:g}"
    suffix = f" {stock_uom}" if stock_uom else ""
    Text(content=f"Purchase UoM: {purchase_uom} (x{rate_str}{suffix})")


def _variant_supplier_codes_line(variant: dict[str, Any]) -> None:
    """Render supplier codes inline using monospace ``Code`` chips.

    Each code lands as its own ``Code`` element with a comma between —
    consistent with the inline ``Barcodes:`` row above and matching the
    fixed-width-font convention for codes / identifiers. The previous
    rendering used a separate ``Muted`` label + ``ForEach`` block, which
    pushed each code onto its own row and broke the otherwise-tight
    reference section.
    """
    codes = variant.get("supplier_item_codes") or []
    if not codes:
        return
    with Row(gap=1):
        Text(content="Supplier Codes:")
        for i, code in enumerate(codes):
            if i > 0:
                Text(content=",")
            Code(content=str(code))


def _variant_reference_section(variant: dict[str, Any]) -> None:
    """Render the reference data block (UoM, supplier, lead time, codes).

    The raw IDs row (``variant_id=... · material_id=...``) was dropped
    intentionally — IDs are noise for human readers, and tooling that
    needs them reads from the JSON ``structured_content`` channel
    directly. Cross-references to other Katana objects belong in
    typed actions / links, not bare ID text.
    """
    if variant.get("uom"):
        Text(content=f"UoM: {variant['uom']}")
    _variant_purchase_uom_line(variant)
    _variant_supplier_line(variant)
    if variant.get("lead_time") is not None:
        Text(content=f"Lead Time: {variant['lead_time']} days")
    if variant.get("minimum_order_quantity") is not None:
        Text(content=f"Min Order Qty: {variant['minimum_order_quantity']}")
    _variant_barcode_line(variant)
    _variant_supplier_codes_line(variant)


def _variant_footer_section(variant: dict[str, Any]) -> None:
    """Render footer action buttons.

    "View in Katana" used to live here as a ``SendMessage`` button that
    asked the agent to surface the URL. Replaced by a real external
    ``Link`` wrapping the card title — clicking the title opens the
    parent's Katana page directly, no agent round-trip needed.

    Action wiring:
    - **Check Inventory** — ``CallTool("check_inventory", ...)`` with the
      SKU resolved at card-build time. Deterministic re-invocation, no
      agent composition.
    - **Create Purchase Order** — ``UpdateContext``: PO creation needs
      ``supplier_id`` + ``location_id`` + ``order_number`` + ``items``,
      none of which are resolvable from the variant card. The agent has
      to ask the user for those before it can call ``create_purchase_order``.
    - **List MOs Using This** (materials only) — ``UpdateContext``: no
      tool answers "MOs that consume this variant" in one call;
      ``list_manufacturing_orders.variant_ids`` filters by *finished
      good* (what the MO produces), and there is no
      ``ingredient_variant_id`` filter today. Tracked in #758.

    Renders nothing when the variant has neither ``sku`` nor ``id`` (truly
    orphan — rare but legal on the wire). Without a stable identity every
    downstream prompt would have to read ``variant_id None`` and the
    CallTool path can't resolve a target, so we drop the whole footer
    rather than render misleading affordances.
    """
    # Variants can legally have ``sku=None`` (see CLAUDE.md "Variants
    # can have null SKUs"), so prefer SKU then fall back to variant_id.
    # ``check_inventory`` accepts both in the same arg; the PO copy
    # uses the matching label so the agent's prompt and any CallTool
    # args agree on the identity. When neither identity is resolvable
    # (truly orphan variant — rare but legal on the wire) we skip every
    # footer action button: a "Create Purchase Order" prompt that says
    # ``variant_id None`` would be actively misleading to the agent, and
    # the downstream PO/MO workflows have no stable identity to anchor
    # to. Better to render no actions than broken ones.
    sku = variant.get("sku")
    variant_id = variant.get("id")
    handle: str | int | None = sku if sku else variant_id
    if handle is None:
        return
    handle_label = f"SKU {sku}" if sku else f"variant_id {variant_id}"
    Button(
        label="Check Inventory",
        variant="outline",
        on_click=CallTool(
            "check_inventory",
            arguments={"skus_or_variant_ids": [handle]},
        ),
    )
    Button(
        label="Create Purchase Order",
        variant="outline",
        on_click=UpdateContext(
            content=(
                f"User wants to draft a purchase order for {handle_label}. "
                "Ask for the supplier, location, order number, and quantity "
                "(or look them up from the variant's default supplier), then "
                "call create_purchase_order with preview=True."
            ),
        ),
    )
    if variant.get("type") == "material" and variant_id is not None:
        Button(
            label="List MOs Using This",
            variant="outline",
            on_click=UpdateContext(
                content=(
                    f"User wants to list manufacturing orders that use "
                    f"variant_id {variant_id} as an ingredient. "
                    "list_manufacturing_orders filters by finished-good "
                    "variant, not by ingredient — call list_blocking_ingredients "
                    "or page through recent MOs and filter their recipes "
                    "client-side."
                ),
            ),
        )


def build_variant_details_ui(
    variant: dict[str, Any],
) -> PrefabApp:
    """Build a detail card for a variant.

    Designed for the "should I order more / where is this used / how is
    it tracked" decisions. Surfaces the facts an inventory-aware agent
    needs first (UoM, default supplier, batch tracking, config
    attributes), with raw IDs deprioritized to a footer-style row. See
    #538 for the design rationale.

    Variant prices (``sales_price`` / ``purchase_price``) are tenant-wide
    and don't carry a per-record currency on the wire — they're
    denominated in ``Factory.base_currency_code``. The caller threads
    the resolved value through ``variant["base_currency_code"]`` (see
    :func:`resolve_factory_base_currency`); the card falls back to USD
    when the field is missing (cold cache / pre-#751 fixtures), so
    rendering stays robust.
    """
    uom = variant.get("uom")
    base_currency = variant.get("base_currency_code")

    def _price_display(p: float | None) -> str:
        if p is None:
            return "N/A"
        suffix = f" / {uom}" if uom and uom not in ("pcs", "ea") else ""
        return f"{_format_money(p, base_currency)}{suffix}"

    with PrefabApp(state={"variant": variant}, css_class="p-4") as app, Card():
        with CardHeader(), Column(gap=1):
            _variant_header_section(variant)

        with CardContent(), Column(gap=3):
            with Row(gap=4):
                Metric(
                    label="Sales Price",
                    value=_price_display(variant.get("sales_price")),
                )
                Metric(
                    label="Purchase Price",
                    value=_price_display(variant.get("purchase_price")),
                )
            Separator()
            _variant_reference_section(variant)

        with CardFooter(), Row(gap=2):
            _variant_footer_section(variant)
    return app


def build_variant_batch_ui(
    payload: dict[str, Any],
) -> PrefabApp:
    """Build a summary card for a batch ``get_variant_details`` response.

    The single-variant card (``build_variant_details_ui``) covers the
    common case; this builder handles every other shape the tool can
    return — multi-variant batches, mixed found+not_found, all-not-found.
    Pre-fix the batch path returned ``ToolResult(structured_content=<dict>)``
    with no PrefabApp, so the host stalled on "Waiting for content..."
    (the #810 sibling bug — ``get_variant_details`` is registered with
    ``meta=UI_META``, so the host polls indefinitely for a tree).

    Tier 1: count badges in the header (``N found`` + ``M not found``
    when present). No external Link — batches span many variants.
    Tier 3: a DataTable for the found variants (click-through to the
    single-variant card via ``CallTool``) plus a separate Alert listing
    not-found inputs so the agent can decide whether to fall back to
    ``search_items`` or fix typos.
    """
    found = payload.get("variants") or []
    not_found = payload.get("not_found") or []

    # The DataTable rows pull from the SAME ``VariantDetailsResponse``
    # shape as the single-variant card, just in list form. Project to a
    # flat row dict so the table doesn't have to deal with nested keys.
    # The primary key on ``VariantDetailsResponse.model_dump()`` is
    # ``id`` (not ``variant_id``) — mirror that here so the onRowClick
    # binding below can read ``EVENT.id`` cleanly, matching the
    # ``_item_variants_table`` convention.
    rows = [
        {
            "id": v.get("id"),
            "sku": v.get("sku"),
            "display_name": v.get("display_name"),
            "uom": v.get("uom"),
            "sales_price": v.get("sales_price"),
            "purchase_price": v.get("purchase_price"),
        }
        for v in found
    ]

    with (
        PrefabApp(state={"rows": rows, "detail": None}, css_class="p-4") as app,
        Card(),
    ):
        with CardHeader(), Row(gap=2):
            with CardTitle():
                Text(content="Variant lookup")
            Badge(label=f"{len(found)} found", variant="secondary")
            if not_found:
                Badge(label=f"{len(not_found)} not found", variant="destructive")

        with CardContent(), Column(gap=3):
            if rows:
                DataTable(
                    columns=[
                        DataTableColumn(key="sku", header="SKU", sortable=True),
                        DataTableColumn(
                            key="display_name", header="Name", sortable=True
                        ),
                        DataTableColumn(key="uom", header="UoM"),
                        DataTableColumn(
                            key="sales_price",
                            header="Sales Price",
                            sortable=True,
                            align="right",
                        ),
                        DataTableColumn(
                            key="purchase_price",
                            header="Purchase Price",
                            sortable=True,
                            align="right",
                        ),
                    ],
                    rows="{{ rows }}",
                    search=True,
                    **_paginate(len(rows)),
                    # Drill into the single-variant card by id (the
                    # row dict's ``id`` is the variant's primary key
                    # from ``VariantDetailsResponse.model_dump()``).
                    # SKU may be None (legacy NetSuite imports — see
                    # CLAUDE.md "Variants can have null SKUs"); id is
                    # always present on the wire.
                    onRowClick=CallTool(
                        "get_variant_details",
                        arguments={"variant_id": str(EVENT.id)},
                        on_success=SetState("detail", RESULT.view),
                        on_error=ShowToast("{{ $error }}", variant="error"),
                    ),
                )
                with Slot(name="detail"):
                    Muted(content="Click a row to see variant details")
            else:
                Muted(content="No variants resolved.")

            if not_found:
                Separator()
                with Alert(variant="destructive"):
                    AlertTitle(content="Not found")
                    # Each ``not_found`` entry carries one of ``sku`` /
                    # ``variant_id`` echoing the input. Render them as
                    # a compact comma-separated list — the agent uses
                    # this to decide between fixing typos and falling
                    # back to ``search_items``.
                    missing_labels = ", ".join(
                        str(n.get("sku") or n.get("variant_id") or "?")
                        for n in not_found
                    )
                    AlertDescription(content=missing_labels)
    return app


def _item_header_section(
    item: dict[str, Any], *, state_badge: str | None = None
) -> None:
    """Render item card header: title (linked to Katana page), type badge,
    and status pills.

    Title wraps in a real ``Link`` to ``katana_url`` so clicking opens
    the Katana product / material / service page directly — same
    convention as the variant card (see module docstring on linking
    Katana entities).

    ``state_badge`` renders a leading state pill (e.g. ``"Created"``) for the
    post-action create card; the detail card omits it.

    Status badges vary by sub-type:
    - Sellable / Not Sellable (all types)
    - Producible / Not Producible (Product only)
    - Batch tracked (Product / Material)
    - Serial tracked (Product / Material)
    - Archived (all types when ``is_archived`` is True)
    """
    katana_url = item.get("katana_url")
    title_content = item.get("name", "Unknown")
    item_type = item.get("type", "")

    with Row(gap=2):
        with CardTitle():
            if katana_url:
                Link(content=title_content, href=katana_url, target="_blank")
            else:
                Text(content=title_content)
        if state_badge:
            # Post-action state pill (e.g. "Created"); the detail card
            # passes None — it's a steady-state read, not a mutation result.
            Badge(label=state_badge, variant="default")
        if item_type:
            Badge(label=str(item_type), variant="secondary")
        if item.get("is_archived"):
            Badge(label="Archived", variant="secondary")

    _item_status_pills_row(item)


def _item_status_pills_row(item: dict[str, Any]) -> None:
    """Render the sub-type status-pills row (sellable / producible / batch /
    serial tracked).

    Order chosen to match the agent's typical decision sequence — sellable
    first (can this be sold?), then producible (can this be made?), then
    tracking flags (will I need to specify a batch / serial when
    transacting?). Shared between :func:`_item_header_section` (create /
    detail cards) and :func:`build_item_modify_ui`'s header so the modify
    card carries the same identity signal alongside its reactive state badge.

    Must be called inside a ``CardHeader`` column block.
    """
    with Row(gap=2):
        if item.get("is_sellable") is not None:
            Badge(
                label="Sellable" if item["is_sellable"] else "Not Sellable",
                variant="default" if item["is_sellable"] else "secondary",
            )
        if item.get("is_producible") is not None:
            Badge(
                label="Producible" if item["is_producible"] else "Not Producible",
                variant="default" if item["is_producible"] else "secondary",
            )
        if item.get("batch_tracked"):
            Badge(label="Batch tracked", variant="secondary")
        if item.get("serial_tracked"):
            Badge(label="Serial tracked", variant="secondary")


def _item_metrics_section(
    item: dict[str, Any],
    *,
    collapse_single_variant: bool = False,
    changes: dict[str, FieldChangeView] | None = None,
) -> None:
    """Render Tier 2 — decision metrics as text rows (not Metric components).

    Items typically have ≤3 numeric facts (variant count, lead time, MOQ),
    so the Metric layout would be visually heavy for a sparse row. Plain
    text rows still give the agent the facts without competing visually
    with the more important variants table below.

    ``collapse_single_variant`` is set by the create card: a freshly-created
    item always has exactly one variant, so "Variants: 1" is noise (the
    single variant's SKU surfaces inline in the reference section instead).
    The count still renders for genuine multi-variant items — and for
    ``Variants: 0``, which is *not* hidden even when collapsing: an empty
    variants list on a just-created item is an unexpected/malformed response
    worth surfacing, not noise to suppress.

    ``changes`` (modify card) decorates the editable scalar lines with their
    before→after diff, plus a leading ``Name`` diff line on a rename (the card
    title is built from the prior snapshot, so a rename would otherwise surface
    nowhere) and ``yes → no`` diff lines for changed boolean status flags
    (``is_sellable`` / ``is_producible`` / tracking flags — the Tier-1 pills
    render the prior snapshot and aren't diff-aware). The variant *count* is
    never editable, so it never decorates. When ``changes`` is empty (create /
    detail cards) every line falls through to its plain ``Text`` form —
    byte-identical to before.
    """
    changes = changes or {}
    # Name diff (modify card only) — the card title is built from the prior
    # snapshot, so a rename would otherwise surface nowhere. Diff-only: on
    # create/detail ``changes`` is empty and the title carries the name.
    name_change = changes.get("name")
    if name_change is not None and name_change.kind != "unchanged":
        _render_field_diff_line("Name", change=name_change)
    # Boolean status-flag diffs (modify card only). The Tier-1 status pills
    # render from the prior snapshot and aren't diff-aware, so a header change
    # to ``is_sellable`` / ``is_producible`` / tracking flags etc. would show
    # the stale pill (or nothing). Surface each changed flag as an explicit
    # ``yes → no`` diff line. Diff-only: empty ``changes`` (create/detail)
    # renders nothing here — the pills carry the steady-state signal.
    for flag_field, flag_label in (
        ("is_sellable", "Sellable"),
        ("is_producible", "Producible"),
        ("is_purchasable", "Purchasable"),
        ("is_auto_assembly", "Auto-assembly"),
        ("batch_tracked", "Batch tracked"),
        ("serial_tracked", "Serial tracked"),
        ("operations_in_sequence", "Operations in sequence"),
        ("is_archived", "Archived"),
    ):
        flag_change = changes.get(flag_field)
        if flag_change is not None and flag_change.kind != "unchanged":
            _render_field_diff_line(flag_label, change=flag_change)
    variants = item.get("variants") or []
    if not (collapse_single_variant and len(variants) == 1):
        Text(content=f"Variants: {len(variants)}")
    lead_time_change = changes.get("lead_time")
    if lead_time_change is not None and lead_time_change.kind != "unchanged":
        _render_field_diff_line("Lead Time", change=lead_time_change)
    elif item.get("lead_time") is not None:
        Text(content=f"Lead Time: {item['lead_time']} days")
    moq_change = changes.get("minimum_order_quantity")
    if moq_change is not None and moq_change.kind != "unchanged":
        _render_field_diff_line("Min Order Qty", change=moq_change)
    elif item.get("minimum_order_quantity") is not None:
        Text(content=f"Min Order Qty: {item['minimum_order_quantity']}")


def _item_supplier_line(
    item: dict[str, Any], *, changes: dict[str, FieldChangeView] | None = None
) -> None:
    """Render the default supplier — preferring the nested ``supplier``
    dict (carries name + id), falling back to the flat
    ``default_supplier_id`` field when the nested record is absent.

    Real materials commonly have ``supplier=None`` while
    ``default_supplier_id`` is set (see ``_FULL_MATERIAL_DICT`` in the
    test fixtures) — Katana only embeds the nested object when the
    relationship is fully populated. Without this fallback the card
    would silently omit any supplier reference for a common shape.

    Render hierarchy:

    1. Nested ``supplier`` with both ``name`` and ``id`` → ``Link``
       (name as visible text, href to ``/contacts/suppliers/{id}``).
    2. Nested ``supplier`` with only ``name`` → plain text.
    3. Flat ``default_supplier_id`` only → ``Link`` using ``#<id>`` as
       the visible text (no name available, but the ID is the
       authoritative identifier and the link still works).

    Supplier appears on Products and Materials (not Services).

    ``changes`` (modify card): when ``default_supplier_id`` is changing,
    render the before→after party-diff line via :func:`_render_party_diff_line`
    instead of the Link form (mirrors ``_render_po_entity_view``'s supplier
    branch). The before-side name comes from the nested supplier / the
    ``default_supplier_name`` prior; the after name from the
    ``default_supplier_name`` FieldChange when present.
    """
    changes = changes or {}
    supplier = item.get("supplier")
    nested_name = supplier.get("name") if isinstance(supplier, dict) else None
    nested_id = supplier.get("id") if isinstance(supplier, dict) else None

    supplier_change = changes.get("default_supplier_id")
    if supplier_change is not None and supplier_change.kind != "unchanged":
        _render_party_diff_line(
            "Default Supplier",
            id_change=supplier_change,
            name_change=changes.get("default_supplier_name"),
            prior_name=nested_name or item.get("default_supplier_name"),
        )
        return

    if nested_name and nested_id:
        supplier_url = katana_web_url("supplier", nested_id)
        if supplier_url:
            with Row(gap=1):
                Text(content="Default Supplier:")
                Link(content=nested_name, href=supplier_url, target="_blank")
        else:
            Text(content=f"Default Supplier: {nested_name}")
        return
    if nested_name:
        Text(content=f"Default Supplier: {nested_name}")
        return

    # No nested supplier dict (or it lacks both fields) — fall back to
    # the flat top-level default_supplier_id. Common for materials
    # where Katana doesn't embed the supplier object even though the
    # FK is set.
    #
    # Anti-pattern #7 (helper-fallback masking): when the nested object
    # is absent the impl should resolve the supplier name via the typed
    # cache (``resolve_entity_name(catalog, CachedSupplier, id, …)``)
    # and feed the resolved name through so this fallback never shows a
    # raw ``#<id>``. ``get_item`` / ``search_items`` / ``modify_item``
    # all funnel through ``_item_supplier_line``; threading a resolved
    # name through each is a follow-up — until then the link works (it
    # navigates to the right supplier) but the visible text is the ID.
    fallback_sid = item.get("default_supplier_id")
    if fallback_sid:
        # Prefer a sibling-resolved ``default_supplier_name`` when the
        # caller threaded one through — keeps existing callers (which
        # pass only the ID) backward-compatible while letting newer
        # callers fill in the user-facing name.
        fallback_name = item.get("default_supplier_name")
        link_text = fallback_name or f"#{fallback_sid}"
        supplier_url = katana_web_url("supplier", fallback_sid)
        if supplier_url:
            with Row(gap=1):
                Text(content="Default Supplier:")
                Link(
                    content=link_text,
                    href=supplier_url,
                    target="_blank",
                )
        elif fallback_name:
            Text(content=f"Default Supplier: {fallback_name}")
        else:
            Text(content=f"Default Supplier ID: {fallback_sid}")


def _item_configs_section(item: dict[str, Any]) -> None:
    """Render configuration axis definitions as ``"Axis: val1, val2, val3"``
    text rows — one per axis. Only Product / Material items have
    configs; Services skip silently. Drops when the list is empty.
    """
    configs = item.get("configs") or []
    for cfg in configs:
        if not isinstance(cfg, dict):
            continue
        name = cfg.get("name") or ""
        values = cfg.get("values") or []
        if name and values:
            joined = ", ".join(str(v) for v in values)
            Text(content=f"{name}: {joined}")


def _item_variants_table(item: dict[str, Any]) -> None:
    """Render the nested-variants DataTable.

    Per-row click invokes ``get_variant_details`` directly via
    ``CallTool`` (mirrors ``build_search_results_ui``) — Katana has no
    per-variant page so a Link isn't an option, but ``CallTool`` is
    cleaner than ``SendMessage`` here because the action is fully
    deterministic ("show me variant Y") and doesn't need agent
    composition. The variant card it triggers will show the same
    canonical ``display_name`` rendering, with its own Link back to
    the parent.

    ``ItemVariantSummary`` carries id / sku / sales_price / purchase_price
    / type. The DataTable renders cells as plain strings — custom
    per-column formatting (monospace SKUs, currency-prefixed prices)
    is a follow-up if the Prefab component grows a per-column renderer
    hook. Hidden when the item has no variants (defensive — Katana
    always returns at least one variant per item in practice).
    """
    variants = item.get("variants") or []
    if not variants:
        return
    DataTable(
        columns=[
            DataTableColumn(key="sku", header="SKU", sortable=True),
            DataTableColumn(
                key="sales_price",
                header="Sales Price",
                sortable=True,
            ),
            DataTableColumn(
                key="purchase_price",
                header="Purchase Price",
                sortable=True,
            ),
        ],
        rows="{{ item.variants }}",
        search=True,
        **_paginate(len(variants)),
        # Per-row click invokes get_variant_details using the row's
        # variant id, not its SKU. ``ItemVariantSummary.sku`` is
        # nullable (Katana allows variants without a SKU on the wire),
        # so binding by SKU would reject every SKU-less row with the
        # tool's "must provide at least one of: sku, variant_id, skus,
        # variant_ids" error. ``id`` is always present on the
        # ``ItemVariantSummary`` shape, so this path stays clickable
        # for every row. Per-row substitution uses ``EVENT.id`` (which
        # compiles to ``{{ $event.id }}``) because the row dict isn't
        # spread into scope — see the comment on the search_results
        # DataTable for the full reasoning (#494).
        onRowClick=CallTool(
            "get_variant_details",
            arguments={"variant_id": str(EVENT.id)},
            on_success=SetState("detail", RESULT.view),
            on_error=ShowToast("{{ $error }}", variant="error"),
        ),
    )
    with Slot(name="detail"):
        Muted(content="Click a row to see variant details")


def _item_single_variant_lines(
    *, sku: str | None, variant: dict[str, Any] | None
) -> None:
    """Render a single variant's facts as inline reference lines.

    Used by the create card (and any single-variant entity view) in place of
    a one-row DataTable — a searchable/paginated table for one row is heavy
    chrome (anti-pattern: single-row table). Surfaces the same three facts the
    multi-variant table column-set carries: SKU, sales price, purchase price.
    Prices render plain (``:g`` trims trailing zeros) to match the table's
    currency-less cells; ``0.0`` prices (free samples) still render because the
    guard is an explicit ``is not None`` check, not truthiness.
    """
    if sku:
        Text(content=f"SKU: {sku}")
    if variant:
        if variant.get("sales_price") is not None:
            Text(content=f"Sales Price: {variant['sales_price']:g}")
        if variant.get("purchase_price") is not None:
            Text(content=f"Purchase Price: {variant['purchase_price']:g}")


def _item_reference_section(
    item: dict[str, Any],
    *,
    collapse_single_variant: bool = False,
    changes: dict[str, FieldChangeView] | None = None,
    suppress_variants: bool = False,
) -> None:
    """Render Tier 3 reference data: UoM, category, purchase UoM,
    default supplier (Linked), configs, additional info, and the
    nested variants table.

    When ``collapse_single_variant`` is set (create card) and the item has a
    single variant, render that variant's SKU + prices inline instead of a
    one-row DataTable. Falls back to the item-level ``sku`` when the create
    result didn't echo a variants array so the SKU is never lost.

    ``changes`` (modify card) decorates the editable scalar lines (UoM,
    Category, Notes), the supplier line, and the service-only pricing/SKU
    fields (``sku`` / ``sales_price`` / ``default_cost`` — services have no
    variant table to carry them) with before→after diffs. Purchase UoM (a
    composite line) and config axes (a nested collection) keep their plain
    rendering for now; the product/material variants collection diffs via the
    separate variant diff-table the modify card renders below this section.
    Empty ``changes`` → every line falls through to its plain form.

    ``suppress_variants`` (modify card) skips the embedded read-only variants
    table entirely — the modify card renders the per-row variant *diff* table
    in its place, so rendering both would duplicate the collection.
    """
    changes = changes or {}
    uom_change = changes.get("uom")
    if uom_change is not None and uom_change.kind != "unchanged":
        _render_field_diff_line("UoM", change=uom_change)
    elif item.get("uom"):
        Text(content=f"UoM: {item['uom']}")
    category_change = changes.get("category_name")
    if category_change is not None and category_change.kind != "unchanged":
        _render_field_diff_line("Category", change=category_change)
    elif item.get("category_name"):
        Text(content=f"Category: {item['category_name']}")
    _variant_purchase_uom_line(item)
    _item_supplier_line(item, changes=changes)
    _item_configs_section(item)
    notes_change = changes.get("additional_info")
    if notes_change is not None and notes_change.kind != "unchanged":
        _render_field_diff_line("Notes", change=notes_change)
    elif item.get("additional_info"):
        Text(content=f"Notes: {item['additional_info']}")
    # Service-only header pricing/SKU diffs (modify card). Services carry SKU +
    # pricing on the header itself and have no variant table, so without these
    # lines a service price/SKU modify would surface no field-level diff. Diff-
    # only: products/materials never set these header fields, and on create/
    # detail ``changes`` is empty, so this loop renders nothing there.
    for field_name, label in (
        ("sku", "SKU"),
        ("sales_price", "Sales Price"),
        ("default_cost", "Default Cost"),
    ):
        field_change = changes.get(field_name)
        if field_change is not None and field_change.kind != "unchanged":
            _render_field_diff_line(label, change=field_change)
    if suppress_variants:
        # Modify card: the per-row variant diff table replaces the embedded
        # read-only table; rendering both would duplicate the collection.
        return
    variants = item.get("variants") or []
    if collapse_single_variant and len(variants) <= 1:
        variant = variants[0] if variants else None
        sku = (variant or {}).get("sku") or item.get("sku")
        _item_single_variant_lines(sku=sku, variant=variant)
    else:
        _item_variants_table(item)


def _item_footer_section(item: dict[str, Any]) -> None:
    """Render Tier 4 action buttons keyed off item type.

    Action wiring (all use ``UpdateContext`` rather than ``CallTool`` —
    each downstream tool needs request fields the item card can't
    populate from item state alone):

    - **Create Purchase Order** (materials) — ``create_purchase_order``
      needs ``supplier_id`` + ``location_id`` + ``order_number`` + a
      variant-keyed ``items`` list, none of which are determined by the
      parent item.
    - **List MOs Using This** (materials) — no tool answers "MOs
      consuming this item" directly today. Tracked in #758.
    - **Create Manufacturing Order** (producible products) —
      ``create_manufacturing_order`` needs ``variant_id`` (not
      ``item_id``), plus ``planned_quantity`` and ``location_id``. A
      producible product can have many variants; the agent has to ask
      which one.
    - **Modify Item** (all) — open-ended; the user hasn't said which
      field to change yet.

    The title's external Link already covers "open in Katana", so no
    footer button for that.
    """
    item_id = item.get("id")
    item_type = item.get("type") or "item"
    if item_id is None:
        return

    if item_type == "material":
        Button(
            label="Create Purchase Order",
            variant="outline",
            on_click=UpdateContext(
                content=(
                    f"User wants to draft a purchase order for material_id "
                    f"{item_id}. Resolve the variant_id, default supplier, "
                    "and location, then call create_purchase_order with "
                    "preview=True."
                ),
            ),
        )
        Button(
            label="List MOs Using This",
            variant="outline",
            on_click=UpdateContext(
                content=(
                    f"User wants to list manufacturing orders that use "
                    f"material_id {item_id} as an ingredient. "
                    "list_manufacturing_orders filters by finished-good "
                    "variant, not by ingredient — call list_blocking_ingredients "
                    "or page through recent MOs and filter their recipes "
                    "client-side."
                ),
            ),
        )
    elif item_type == "product" and item.get("is_producible"):
        Button(
            label="Create Manufacturing Order",
            variant="outline",
            on_click=UpdateContext(
                content=(
                    f"User wants to draft a manufacturing order for "
                    f"product_id {item_id}. Resolve the target variant_id "
                    "(the product may have multiple), planned_quantity, "
                    "and location, then call create_manufacturing_order "
                    "with preview=True."
                ),
            ),
        )

    Button(
        label="Modify Item",
        variant="outline",
        on_click=UpdateContext(
            content=(
                f"User wants to modify {item_type} {item_id}. Ask which "
                "fields to change, then call modify_item with preview=True."
            ),
        ),
    )


def _render_item_entity_view(
    item: dict[str, Any],
    *,
    changes: dict[str, FieldChangeView] | None = None,
    collapse_single_variant: bool = False,
    suppress_variants: bool = False,
) -> list[str]:
    """Render the item entity view (Tier 2 metrics + Tier 3 reference),
    returning the block-warning list for the caller to surface/gate on.

    The item analogue of :func:`_render_po_entity_view`: shared between
    ``build_item_detail_ui`` (multi-variant read card, ``collapse_single_variant
    =False``), ``build_item_create_ui`` (a freshly-created single-variant item,
    ``collapse_single_variant=True``), and ``build_item_modify_ui`` (which passes
    ``changes`` to overlay before→after diffs on the editable header/reference
    lines, plus ``suppress_variants=True`` so its per-row variant *diff* table
    replaces the embedded read-only one, #726). Empty ``changes`` → plain
    rendering, byte-identical to the create/detail cards.

    Must be called inside ``with CardContent(), Column(gap=3):``.
    """
    _item_metrics_section(
        item, collapse_single_variant=collapse_single_variant, changes=changes
    )
    Separator()
    _item_reference_section(
        item,
        collapse_single_variant=collapse_single_variant,
        changes=changes,
        suppress_variants=suppress_variants,
    )
    return _render_warnings_block(item.get("warnings"))


def build_item_detail_ui(
    item: dict[str, Any],
) -> PrefabApp:
    """Build a detail card for an item (product / material / service).

    Implements the four-tier framework from #537 with sub-type variance
    in the metrics, reference, and footer sections:

    - **Tier 1 — Identity**: title as external ``Link`` to the Katana
      product / material / service page (no per-variant page in
      Katana's web app — items DO have one); type badge; status pills
      that vary by sub-type (sellable / producible / batch /
      serial / archived).
    - **Tier 2 — Decision metrics**: variant count (always), lead time
      and MOQ (Product only). Text rows, not Metric components —
      items have too few numeric facts to warrant the visual weight.
    - **Tier 3 — Reference**: UoM, category, purchase UoM (P/M),
      default supplier (P/M, rendered as Link to the Katana supplier
      page), config-axis definitions (P/M), additional info, and the
      nested variants table — a DataTable with per-row CallTool
      drilling into ``get_variant_details``.
    - **Tier 4 — Actions**: sub-type-specific buttons backed by
      ``UpdateContext`` (composing the args is on the agent because the
      item card lacks the variant / location / supplier / target-field
      context the underlying tools need): ``Create Purchase Order`` +
      ``List MOs Using This`` (materials), ``Create Manufacturing Order``
      (producible products), ``Modify Item`` (all). No "View in Katana"
      footer button — the title link replaces it.

    Reference example: the variant card (#542 / #696) established the
    same shape on a single-row entity; this card extends the pattern
    to a parent entity with embedded children.
    """
    # ``detail: None`` is seeded for the variants DataTable's
    # ``Slot(name="detail")`` + ``on_success=SetState("detail", RESULT)``
    # pattern. Without an explicit None seed the slot binds to an
    # undefined key, which works in current Prefab renderers but matches
    # the explicit-is-better-than-implicit contract from
    # ``build_search_results_ui``'s state init and avoids edge cases
    # around missing keys.
    with (
        PrefabApp(state={"item": item, "detail": None}, css_class="p-4") as app,
        Card(),
    ):
        with CardHeader(), Column(gap=2):
            _item_header_section(item)

        with CardContent(), Column(gap=3):
            # block_warnings return discarded — read-only detail card, no
            # Confirm gate to disable.
            _render_item_entity_view(item)

        with CardFooter(), Row(gap=2):
            _item_footer_section(item)
    return app


# ============================================================================
# BOM (Bill of Materials) UI
# ============================================================================


def _bom_header_section(bom: dict[str, Any]) -> None:
    """Tier 1 — title (linked to parent product page when available),
    variant SKU pill, producible status, and a row-count badge.

    Title links through to the parent product page because variants
    don't have their own page in Katana's web app (same convention as
    ``_inventory_header_section`` / ``_variant_header_section``). Falls
    back to the variant id when the cache miss left ``product_name``
    unresolved so the card is still meaningfully labeled.
    """
    katana_url = bom.get("katana_url")
    title_content = (
        bom.get("product_name")
        or bom.get("variant_display_name")
        or f"BOM for variant {bom.get('product_variant_id')}"
    )
    sku = bom.get("variant_sku")
    is_producible = bom.get("is_producible")
    total_count = bom.get("total_count", 0)

    with Row(gap=2):
        with CardTitle():
            if katana_url:
                Link(content=title_content, href=katana_url, target="_blank")
            else:
                Text(content=title_content)
        if sku:
            Badge(label=sku, variant="outline")
        if is_producible is False:
            # Surface the mismatch — a non-producible variant with BOM
            # rows is unusual; flag it. Producible=True is the expected
            # case for the standard recipe-edit workflow, so skip the
            # badge to keep the header uncluttered.
            Badge(label="Not Producible", variant="destructive")
        Badge(
            label=f"{total_count} {'ingredient' if total_count == 1 else 'ingredients'}",
            variant="secondary",
        )


def _bom_rows_table(bom: dict[str, Any]) -> None:
    """Tier 3 — DataTable of BOM rows.

    Per-row click invokes ``get_variant_details`` directly on the
    ingredient's variant id — same pattern as ``_item_variants_table``.
    The ingredient SKU + display_name are pre-resolved from the typed
    cache during the response build, so the rows render with
    user-meaningful identifiers (the per-row ``feedback-user-centric-card-content``
    memory: card content answers "what does the user care about?", not
    "internal IDs"). Falls back to a friendly empty-state when the
    variant has no recipe.
    """
    rows = bom.get("rows") or []
    if not rows:
        Muted(
            content=(
                "No BOM rows for this variant. Use ``manage_product_bom`` "
                "with ``add_bom_rows`` to add ingredients."
            )
        )
        return
    DataTable(
        columns=[
            DataTableColumn(key="sku", header="Ingredient SKU", sortable=True),
            DataTableColumn(key="display_name", header="Name", sortable=True),
            DataTableColumn(
                key="quantity", header="Qty per Unit", sortable=True, align="right"
            ),
            DataTableColumn(key="notes", header="Notes"),
        ],
        rows="{{ bom.rows }}",
        search=True,
        **_paginate(len(rows)),
        # Per-row click drills into the ingredient's variant card.
        # ``EVENT.ingredient_variant_id`` is always present on
        # ``BomRowInfo`` — every row carries the FK, even when the
        # cached SKU lookup missed (sku=None). Binding by id (not sku)
        # keeps SKU-less rows clickable. Mirrors ``_item_variants_table``.
        onRowClick=CallTool(
            "get_variant_details",
            arguments={"variant_id": str(EVENT.ingredient_variant_id)},
            on_success=SetState("detail", RESULT.view),
            on_error=ShowToast("{{ $error }}", variant="error"),
        ),
    )
    with Slot(name="detail"):
        Muted(content="Click a row to see ingredient variant details")


def _bom_footer_section(bom: dict[str, Any]) -> None:
    """Tier 4 — [Manage BOM] action.

    Uses ``UpdateContext`` (not ``CallTool``) because ``manage_product_bom``
    needs a sub-payload — the user hasn't said yet which rows to add /
    update / delete. The agent prompts for that, then issues the call
    with ``preview=True`` so the preview/apply gate fires.
    """
    variant_id = bom.get("product_variant_id")
    if variant_id is None:
        return
    Button(
        label="Manage BOM",
        variant="outline",
        on_click=UpdateContext(
            content=(
                f"User wants to modify the BOM for product_variant_id "
                f"{variant_id}. Ask which rows to add, update, or delete, "
                "then call manage_product_bom with preview=True."
            ),
        ),
    )


def build_product_bom_ui(
    bom: dict[str, Any],
) -> PrefabApp:
    """Build a detail card for a product variant's BOM (Bill of Materials).

    Implements the four-tier framework from #537 with the
    "nested-row-table on a parent entity" shape established by
    ``build_item_detail_ui``:

    - **Tier 1 — Identity**: title as external ``Link`` to the parent
      product page (variants don't have their own page in Katana's web
      app); variant SKU badge; ingredient-count badge. ``Not Producible``
      badge surfaces the mismatch when a non-producible variant
      somehow has BOM rows.
    - **Tier 2 — Decision metrics**: skipped. BOMs are reference data,
      not transactional, so there's no obvious numeric fact that beats
      the ingredient-count badge already in tier 1. The variant card
      (``build_variant_details_ui``) made the same choice on the same
      reasoning.
    - **Tier 3 — Reference**: the BOM rows DataTable. Columns are the
      user-facing fields (ingredient SKU, display name, quantity,
      notes) — NOT the internal BOM-row UUID or the
      ``product_item_id`` / ``product_variant_id`` echo. Per-row click
      drills into ``get_variant_details`` for the ingredient variant.
    - **Tier 4 — Actions**: [Manage BOM] only. Pushed through
      ``UpdateContext`` because the modify payload (add/update/delete
      rows) isn't deterministic from the card's data alone.

    Closes #810 — pre-fix the tool was registered with ``meta=UI_META``
    but returned ``make_json_result`` (no PrefabApp), so cards rendered
    as "Waiting for content..." indefinitely.
    """
    with (
        PrefabApp(state={"bom": bom, "detail": None}, css_class="p-4") as app,
        Card(),
    ):
        with CardHeader(), Column(gap=2):
            _bom_header_section(bom)

        with CardContent(), Column(gap=3):
            _bom_rows_table(bom)

        with CardFooter(), Row(gap=2):
            _bom_footer_section(bom)
    return app


# ============================================================================
# Inventory UIs
# ============================================================================


# Per-location reorder status, written by `_annotate_location_rows` and read by
# both the per-row DataTable column and the header low-stock badge.
_STATUS_BELOW_REORDER = "Below reorder"
_STATUS_AT_REORDER = "At reorder"
_STATUS_HEALTHY = "Healthy"

# Per-variant status used by the batch inventory card, written by
# ``_annotate_batch_summary_row``. Kept separate from the per-location
# reorder buckets above — the batch row reports presence + zero-stock,
# not reorder thresholds.
_STATUS_NOT_FOUND = "Not found"
_STATUS_OUT_OF_STOCK = "Out of stock"
_STATUS_IN_STOCK = "In stock"


_LOW_STOCK_STATUSES = frozenset({_STATUS_BELOW_REORDER, _STATUS_AT_REORDER})


def _inventory_below_reorder(stock: dict[str, Any]) -> bool:
    """True when any location's annotated status hits the reorder threshold.

    Reads the per-row status that ``_annotate_location_rows`` wrote, so
    the header badge and the per-row Status column never disagree.
    Reorder-point semantics fire when ``available <= reorder_point`` —
    both ``Below reorder`` (strictly less) and ``At reorder`` (exact
    equality) need the same headline alert.
    """
    return any(
        isinstance(loc, dict) and loc.get("status_label") in _LOW_STOCK_STATUSES
        for loc in stock.get("by_location") or []
    )


def _inventory_header_section(stock: dict[str, Any]) -> None:
    """Tier 1 — title (linked to parent when ``katana_url`` is set), SKU, UoM,
    low-stock badge, multi-location count.

    Title links through to the parent product / material page rather
    than the variant — variants don't have their own page in Katana's
    web app.
    """
    katana_url = stock.get("katana_url")
    title_content = stock.get("product_name") or stock.get("sku") or "Unknown"
    by_location = stock.get("by_location") or []
    uom = stock.get("uom")
    with Row(gap=2):
        with CardTitle():
            if katana_url:
                Link(content=title_content, href=katana_url, target="_blank")
            else:
                Text(content=title_content)
        if stock.get("sku"):
            Badge(label=stock["sku"], variant="outline")
        if uom:
            Badge(label=uom, variant="outline")
        if _inventory_below_reorder(stock):
            Badge(label="Low Stock", variant="destructive")
        if len(by_location) > 1:
            Badge(
                label=f"{len(by_location)} locations",
                variant="secondary",
            )


def _inventory_metrics_section(stock: dict[str, Any]) -> None:
    with Row(gap=4):
        Metric(label="In Stock", value=str(stock.get("in_stock", 0)))
        Metric(label="Available", value=str(stock.get("available_stock", 0)))
        Metric(label="Committed", value=str(stock.get("committed", 0)))
        Metric(label="Expected", value=str(stock.get("expected", 0)))


def _inventory_supplier_line(stock: dict[str, Any]) -> None:
    _default_supplier_line(
        stock.get("default_supplier_name"),
        stock.get("default_supplier_id"),
    )


def _inventory_reference_section(stock: dict[str, Any]) -> None:
    """Tier 3 — per-location breakdown DataTable + default-supplier line.

    Single-location is the common case; rendering a one-row table just
    repeats the metrics. Skip it and let the supplier line carry the
    reference data.
    """
    by_location = stock.get("by_location") or []
    if len(by_location) > 1:
        Separator()
        Muted(content="By location:")
        # ``location_name`` is allowed to be ``None`` when the location
        # cache misses; that's the case where the impl side should be
        # resolving the name (typed cache lookup), not the card adding
        # an ID column. Pre-#card-ux this section carried a permanent
        # ``location_id`` "ID" column "so rows are never unidentifiable"
        # — that's exactly anti-pattern #2 (raw IDs as a user surface).
        DataTable(
            columns=[
                DataTableColumn(key="location_name", header="Location"),
                DataTableColumn(key="in_stock", header="In Stock", align="right"),
                DataTableColumn(key="available", header="Available", align="right"),
                DataTableColumn(key="committed", header="Committed", align="right"),
                DataTableColumn(key="expected", header="Expected", align="right"),
                DataTableColumn(
                    key="reorder_point", header="Reorder Pt", align="right"
                ),
                DataTableColumn(key="status_label", header="Status"),
            ],
            rows="{{ stock.by_location }}",
        )
    _inventory_supplier_line(stock)


def _inventory_footer_section(stock: dict[str, Any]) -> None:
    """Tier 4 — [Create PO] + [View Variant Details].

    Variants can have a null SKU (legacy NetSuite imports are a common
    source — see CLAUDE.md "Variants can have null SKUs"); fall back to
    ``variant_id`` for both prompts and the button-render gate so
    SKU-less rows still get actionable buttons instead of degrading to
    a broken "for SKU " prompt.

    The "List MOs Using This" button (still on the variant card at
    ``_variant_footer_section``) was not carried over here because no
    available tool answers "what MOs consume this material" in a single
    call: ``list_manufacturing_orders.variant_ids`` filters finished
    goods (the MO produces these), and ``list_blocking_ingredients``
    has no per-variant filter. Tracked in #758 — re-add once a proper
    filter ships. Parent-page link lives on the title (Tier 1), not as
    a separate footer button.
    """
    # ``StockInfo.is_found=False`` stubs echo the input back in ``sku`` /
    # ``variant_id`` so the JSON envelope still names the missing row,
    # but actionable buttons must NOT render — they would target a
    # variant the server already told us does not exist. Default to
    # found-true so legacy callers / dict fixtures that omit the flag
    # keep working.
    if not stock.get("is_found", True):
        return
    sku = stock.get("sku")
    variant_id = stock.get("variant_id")
    # Identity for the agent prompts: prefer SKU (human-friendly), fall
    # back to variant_id, render nothing if neither is set.
    if sku:
        identity = f"SKU {sku}"
    elif variant_id:
        identity = f"variant_id {variant_id}"
    else:
        return
    # PO drafting needs supplier_id + location_id + order_number + items —
    # none of which are derivable from a stock-check card alone — so the
    # button hands the agent an UpdateContext prompt. "View Variant
    # Details" is a deterministic re-invocation, so it's a CallTool keyed
    # on whichever identity the row carries.
    Button(
        label="Create PO",
        variant="outline",
        on_click=UpdateContext(
            content=(
                f"User wants to draft a purchase order for {identity}. "
                "Resolve the default supplier and target location, then "
                "call create_purchase_order with preview=True."
            ),
        ),
    )
    details_action = _variant_details_action(sku, variant_id)
    if details_action is not None:
        Button(
            label="View Variant Details",
            variant="outline",
            on_click=details_action,
        )


def _annotate_location_rows(stock: dict[str, Any]) -> None:
    """Mutate ``stock['by_location']`` to add ``status_label`` per row.

    The DataTable templates against the state dict — per-row badge text
    has to live on the row itself, since the template engine can't
    derive it at render time. Empty string when no threshold is set on
    that location (a missing threshold is a missing signal, not a
    license to flag every warehouse).
    """
    for loc in stock.get("by_location") or []:
        if not isinstance(loc, dict):
            continue
        rp = loc.get("reorder_point")
        if rp is None:
            loc["status_label"] = ""
            continue
        available = loc.get("available") or 0
        if available < rp:
            loc["status_label"] = _STATUS_BELOW_REORDER
        elif available == rp:
            loc["status_label"] = _STATUS_AT_REORDER
        else:
            loc["status_label"] = _STATUS_HEALTHY


def build_inventory_check_ui(
    stock: dict[str, Any],
) -> PrefabApp:
    """Build an inventory check card.

    Designed for the "do I need to order more / where is it / who's the
    supplier" decisions. Surfaces parent-derived UoM in the header so
    unit-of-measure questions answer themselves; the per-location
    DataTable carries reorder thresholds so warehouse-level reorder
    decisions don't need a separate ``get_item`` call. The "what MOs
    consume this" affordance is intentionally absent — see #758 and the
    note on ``_inventory_footer_section`` — because no supported
    tool answers that in a single call today. See #549.
    """
    _annotate_location_rows(stock)
    with PrefabApp(state={"stock": stock}, css_class="p-4") as app, Card():
        with CardHeader():
            _inventory_header_section(stock)

        with CardContent(), Column(gap=3):
            _inventory_metrics_section(stock)
            _inventory_reference_section(stock)

        with CardFooter(), Row(gap=2):
            _inventory_footer_section(stock)
    return app


def _annotate_batch_summary_row(item: dict[str, Any]) -> None:
    """Mutate a batch summary row in place with derived presentation fields.

    ``location_count`` and ``status_label`` aren't on the ``StockInfo``
    wire shape — they're presentation-only — so compute them here rather
    than pushing them onto the response model. Status uses the
    ``is_found`` flag (added in #549) to distinguish echoed not-found
    stubs from real zero-stock variants; without the explicit
    indicator the two collapse to "0 in stock" in the table.
    """
    item["location_count"] = len(item.get("by_location") or [])
    if not item.get("is_found", True):
        item["status_label"] = _STATUS_NOT_FOUND
    elif (item.get("in_stock") or 0) <= 0:
        # ``<= 0`` not ``== 0`` — Katana sums inventory points directly,
        # and adjustments / backorders / accounting fixes can drive the
        # total negative. A negative balance is "no stock available" for
        # any decision the card supports, so collapse it into the same
        # out-of-stock bucket rather than masquerading as "In stock".
        item["status_label"] = _STATUS_OUT_OF_STOCK
    else:
        item["status_label"] = _STATUS_IN_STOCK


_BATCH_METRIC_KEYS: tuple[str, ...] = (
    "in_stock",
    "available_stock",
    "committed",
    "expected",
)


def build_inventory_check_batch_ui(
    items: list[dict[str, Any]],
) -> PrefabApp:
    """Build a batch inventory-check card with summary metrics + per-variant table.

    Mirrors :func:`build_batch_recipe_update_ui`: flat top table with one
    row per variant, plus an inline by-location sub-table for each
    variant whose stock is split across more than one warehouse. Each
    sub-table binds to its own state slot (``by_location_<i>``) rather
    than a bracket-indexed mustache path (``items[i].by_location``) —
    Prefab's mustache resolver rejects bracket subscripts, and the
    state-validation harness fails the build if one slips in.

    Single-location variants don't render a sub-table (the row in the
    summary table already carries everything). Not-found stubs
    (``is_found == False``) surface as a "Not found" status badge so the
    table doesn't silently collapse them into zero-stock rows.

    Empty input renders a "no items" hint. Mutates each ``item`` in
    place via ``_annotate_batch_summary_row`` — callers must pass
    throwaway dicts (e.g. ``model_dump()`` output). See #562.
    """
    # Single pass: annotate + aggregate + count not-found in one loop
    # rather than four genexps over the same list. Sums only count
    # found rows so a not-found stub (zeroed totals) doesn't dilute
    # per-found averages if we ever surface them. ``_annotate_location_rows``
    # is reused from the single-item card so per-warehouse status labels
    # (Below reorder / At reorder / Healthy) stay consistent across both
    # surfaces.
    not_found_count = 0
    totals: dict[str, float] = dict.fromkeys(_BATCH_METRIC_KEYS, 0.0)
    for item in items:
        _annotate_batch_summary_row(item)
        _annotate_location_rows(item)
        if not item.get("is_found", True):
            not_found_count += 1
            continue
        for key in _BATCH_METRIC_KEYS:
            totals[key] += float(item.get(key) or 0)
    total_items = len(items)

    # Per-variant by-location sub-tables need their own state keys so
    # the validator (and the JS renderer) can resolve the mustache path
    # without bracket-indexing into ``items[i]`` — the harness rejects
    # bracket subscripts because Prefab's runtime can't traverse them.
    # The render loop emits a Separator + label above each slot's
    # DataTable so the sub-tables visually attach to the right variant.
    #
    # The summary table only reads top-level item fields, never
    # ``by_location``. Slim each row down before putting it in state so
    # the by-location data doesn't get serialized twice (once under
    # ``items[i].by_location``, once under ``by_location_<i>``) — wire
    # payload would otherwise scale with N*L for multi-location batches.
    summary_items = [
        {k: v for k, v in item.items() if k != "by_location"} for item in items
    ]
    state: dict[str, Any] = {"items": summary_items}
    multi_location_slots: list[tuple[str, dict[str, Any]]] = []
    for i, item in enumerate(items):
        if len(item.get("by_location") or []) > 1:
            slot = f"by_location_{i}"
            state[slot] = item["by_location"]
            multi_location_slots.append((slot, item))

    with (
        PrefabApp(state=state, css_class="p-4") as app,
        Column(gap=4),
    ):
        with Row(gap=2):
            H3(content="Inventory Check")
            Badge(label=f"{total_items} items", variant="outline")
            if not_found_count:
                Badge(
                    label=f"{not_found_count} not found",
                    variant="destructive",
                )

        if total_items == 0:
            Muted(content="No items in this batch.")
            return app

        with Row(gap=4):
            Metric(label="In Stock", value=str(totals["in_stock"]))
            Metric(label="Available", value=str(totals["available_stock"]))
            Metric(label="Committed", value=str(totals["committed"]))
            Metric(label="Expected", value=str(totals["expected"]))

        # Variant ID column is reserved for the unidentifiable-row case:
        # a row that lacks BOTH ``sku`` AND ``product_name`` has no
        # human-facing identity (e.g., a variant-ID lookup that resolved
        # no row, or a stub from a deleted variant). A SKU-less variant
        # that still has a ``product_name`` (legitimate NetSuite import,
        # per CLAUDE.md "Variants can have null SKUs") is identifiable
        # via the Product column — the variant_id column would just
        # surface a raw wire ID (anti-pattern #2). Only fall back when
        # the row genuinely has nothing else to anchor the operator.
        needs_variant_id_column = any(
            not r.get("sku") and not r.get("product_name") for r in summary_items
        )
        columns: list[Any] = [
            DataTableColumn(key="sku", header="SKU", sortable=True),
        ]
        if needs_variant_id_column:
            columns.append(
                DataTableColumn(
                    key="variant_id",
                    header="Variant ID",
                    sortable=True,
                    align="right",
                )
            )
        columns.extend(
            [
                DataTableColumn(key="product_name", header="Product", sortable=True),
                DataTableColumn(key="uom", header="UoM"),
                DataTableColumn(
                    key="in_stock", header="In Stock", sortable=True, align="right"
                ),
                DataTableColumn(
                    key="available_stock",
                    header="Available",
                    sortable=True,
                    align="right",
                ),
                DataTableColumn(
                    key="committed", header="Committed", sortable=True, align="right"
                ),
                DataTableColumn(
                    key="expected", header="Expected", sortable=True, align="right"
                ),
                DataTableColumn(
                    key="location_count",
                    header="Locations",
                    sortable=True,
                    align="right",
                ),
                DataTableColumn(key="status_label", header="Status", sortable=True),
            ]
        )
        DataTable(
            columns=columns,
            rows="{{ items }}",
            search=True,
            **_paginate(total_items, page_size=25),
        )

        for slot, item in multi_location_slots:
            Separator()
            label = (
                item.get("sku")
                or item.get("product_name")
                or (
                    f"variant_id {item['variant_id']}"
                    if item.get("variant_id")
                    else "(unknown)"
                )
            )
            Muted(content=f"{label} — by location ({len(item['by_location'])}):")
            DataTable(
                columns=[
                    DataTableColumn(key="location_name", header="Location"),
                    DataTableColumn(key="in_stock", header="In Stock", align="right"),
                    DataTableColumn(key="available", header="Available", align="right"),
                    DataTableColumn(key="committed", header="Committed", align="right"),
                    DataTableColumn(key="expected", header="Expected", align="right"),
                    # Column parity with ``_inventory_reference_section``
                    # in the single-item card — batch users need the same
                    # warehouse-level reorder signal when a variant spans
                    # multiple locations. ``status_label`` is populated by
                    # ``_annotate_location_rows`` above.
                    DataTableColumn(
                        key="reorder_point", header="Reorder Pt", align="right"
                    ),
                    DataTableColumn(key="status_label", header="Status"),
                ],
                rows=f"{{{{ {slot} }}}}",
            )
    return app


def build_low_stock_ui(
    items: list[dict[str, Any]],
    threshold: int,
    total_count: int,
) -> PrefabApp:
    """Build a low stock report following the four-tier card framework (#537).

    Tier 1 — Header with title, threshold + count badges.
    Tier 2 — Three at-a-glance Metric widgets (below threshold, critically
    low, suppliers involved) for a fast snapshot of restock urgency.
    Tier 3 — DataTable enriched with item, SKU, UoM, stock, threshold,
    lead time, supplier, and minimum-order-quantity columns.
    Tier 4 — Action row: "Create Restock Orders" + "Check Inventory".

    When ``total_count == 0``, drops the metrics row, DataTable, and
    action buttons — they reference nonexistent items — and renders a
    friendly "all clear" hint instead.
    """
    # Tier 2 metric inputs — derived from the row set so the builder
    # stays self-contained for testing.
    critically_low_count = sum(1 for item in items if item.get("current_stock") == 0)
    supplier_count = len(
        {sid for item in items if (sid := item.get("default_supplier_id")) is not None}
    )

    with (
        PrefabApp(
            state={"items": items},
            css_class="p-4",
        ) as app,
        Column(gap=4),
    ):
        with Row(gap=2):
            H3(content="Low Stock Report")
            Badge(label=f"Threshold: {threshold}", variant="outline")
            Badge(
                label=f"{total_count} items",
                variant="destructive" if total_count > 0 else "secondary",
            )

        if total_count == 0:
            Muted(
                content=(
                    f"No items below the threshold of {threshold}. "
                    "Inventory levels are healthy."
                )
            )
            return app

        # All three Tier 2 metrics describe the rendered rows so the
        # populations stay internally consistent — when ``total_count >
        # len(items)`` (request.limit truncated the full set), the
        # full count still surfaces on the Tier 1 badge above.
        # ``Critically low`` uses ``trendSentiment="negative"`` for the
        # destructive visual on stock-outs; Metric has no ``variant``
        # parameter like Badge does.
        with Row(gap=2):
            Metric(label="Below threshold", value=str(len(items)))
            Metric(
                label="Critically low",
                value=str(critically_low_count),
                trendSentiment="negative" if critically_low_count > 0 else "neutral",
            )
            Metric(label="Suppliers involved", value=str(supplier_count))

        # Column order follows the decision sequence: identify (name,
        # SKU, UoM), see the depletion signal (stock vs threshold),
        # then act (lead time + supplier + MOQ).
        DataTable(
            columns=[
                DataTableColumn(key="display_name", header="Item", sortable=True),
                DataTableColumn(key="sku", header="SKU", sortable=True),
                DataTableColumn(key="uom", header="UoM"),
                DataTableColumn(
                    key="current_stock",
                    header="In Stock",
                    sortable=True,
                    align="right",
                ),
                DataTableColumn(key="threshold", header="Threshold", align="right"),
                DataTableColumn(
                    key="lead_time_days",
                    header="Lead Time (d)",
                    sortable=True,
                    align="right",
                ),
                DataTableColumn(
                    key="default_supplier_name", header="Supplier", sortable=True
                ),
                DataTableColumn(
                    key="minimum_order_quantity", header="Min Order", align="right"
                ),
            ],
            rows="{{ items }}",
            search=True,
            # Deliberate per-card policy: 10 rows/page (smaller than the
            # module's 20 because the restock list is meant to be scanned and
            # acted on, not browsed). This was the prior behavior — the table
            # carried no explicit pageSize and the component defaults to 10 —
            # now pinned explicitly so it's independent of component updates.
            **_paginate(len(items), page_size=10),
        )

        # "Create Restock Orders" is batch-composition work (group rows
        # by supplier, decide order numbers, resolve per-row quantities)
        # — UpdateContext. "Check Inventory" is deterministic when at
        # least one row carries an identity — CallTool via the helper.
        low_stock_handles: list[str | int] = [
            handle
            for item in items
            if (handle := item.get("sku") or item.get("variant_id"))
        ]
        with Row(gap=2):
            Button(
                label="Create Restock Orders",
                variant="default",
                on_click=UpdateContext(
                    content=(
                        "User wants to create purchase orders to restock all "
                        "low-stock items. Group the rows by supplier, "
                        "resolve order numbers and per-row quantities, then "
                        "call create_purchase_order with preview=True for "
                        "each supplier."
                    ),
                ),
            )
            Button(
                label="Check Inventory",
                variant="default",
                on_click=_check_inventory_action(
                    low_stock_handles,
                    fallback_content=(
                        "User wants to check inventory for the low-stock items "
                        "in the report, but none of them carry a SKU or "
                        "variant_id. Resolve identities from the report rows "
                        "and call check_inventory."
                    ),
                ),
            )
    return app


def _inventory_at_table_rows(
    items: list[dict[str, Any]],
    currency: str | None,
) -> list[dict[str, Any]]:
    """Flatten the response shape into one row per (variant, location).

    Variants with empty ``by_location`` (no movements before ``as_of``)
    render a single row with location ``"—"`` and zeroed values so the
    user sees they were checked but had no history. The table groups
    naturally by SKU when sorted on it.
    """
    rows: list[dict[str, Any]] = []
    for item in items:
        sku = item.get("sku") or ""
        display_name = item.get("display_name", "")
        variant_id = item.get("variant_id")
        by_location = item.get("by_location") or []
        if not by_location:
            rows.append(
                {
                    "sku": sku,
                    "display_name": display_name,
                    "variant_id": variant_id,
                    "location_name": "—",
                    "balance_label": "—",
                    "value_label": "—",
                    "cost_label": "—",
                    "last_movement_date": "—",
                }
            )
            continue
        for loc in by_location:
            rows.append(
                {
                    "sku": sku,
                    "display_name": display_name,
                    "variant_id": variant_id,
                    "location_name": loc.get("location_name")
                    or f"Location {loc.get('location_id')}",
                    "balance_label": f"{float(loc.get('balance_at', 0)):.2f}",
                    "value_label": _format_money(
                        loc.get("value_in_stock_at"), currency
                    ),
                    "cost_label": _format_money(loc.get("average_cost_at"), currency),
                    "last_movement_date": _iso_date_only(
                        loc.get("last_movement_date", "")
                    ),
                }
            )
    return rows


def build_inventory_at_ui(
    items: list[dict[str, Any]],
    as_of: str,
    location_id: int | None = None,
    location_name: str | None = None,
    not_found: list[str | int] | None = None,
    currency: str | None = None,
) -> PrefabApp:
    """Build the point-in-time inventory card.

    Header surfaces the ``as_of`` instant + item count and (when scoped)
    the location filter. The body is a flat DataTable with one row per
    (variant, location); variants with no history before ``as_of`` get a
    single row with ``"—"`` placeholders so the caller sees they were
    checked. Totals strip aggregates across all items.

    Mirrors the ``check_inventory`` card's structural conventions: header
    badges, conditional Muted "not found" hint, action buttons that
    surface the obvious next-step tools.
    """
    not_found_list = list(not_found or [])
    rows = _inventory_at_table_rows(items, currency)
    total_balance = sum(
        float(loc.get("balance_at", 0))
        for item in items
        for loc in (item.get("by_location") or [])
    )
    total_value = sum(
        float(loc.get("value_in_stock_at", 0))
        for item in items
        for loc in (item.get("by_location") or [])
    )

    is_single = len(items) == 1
    as_of_date = _iso_date_only(as_of)

    with (
        PrefabApp(state={"rows": rows}, css_class="p-4") as app,
        Card(),
    ):
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"Inventory as of {as_of_date}")
            Badge(
                label=f"{len(items)} item{'s' if len(items) != 1 else ''}",
                variant="secondary",
            )
            if location_id is not None:
                # Use the resolved ``location_name`` when supplied —
                # ``"Warehouse A"`` reads better than ``"Location 17"``
                # (anti-pattern #2). Fallback to the bare ID only when
                # the caller couldn't resolve a name.
                badge_label = location_name or f"Location {location_id}"
                Badge(label=badge_label, variant="outline")
            if is_single and items:
                only = items[0]
                Badge(label=only.get("sku") or "(no SKU)", variant="outline")

        with CardContent(), Column(gap=3):
            with Row(gap=4):
                Metric(label="Total Balance", value=f"{total_balance:.2f}")
                Metric(
                    label="Total Value",
                    value=_format_money(total_value, currency),
                )

            if not rows:
                Muted(
                    content=("No items resolved — every input is in `not_found` below.")
                )
            else:
                Separator()
                # Single-variant: drop SKU/Item columns (already in header).
                # Batch: include them so the table reads as a flat ledger.
                columns: list[DataTableColumn] = []
                if not is_single:
                    columns.append(
                        DataTableColumn(key="sku", header="SKU", sortable=True)
                    )
                    columns.append(
                        DataTableColumn(
                            key="display_name", header="Item", sortable=True
                        )
                    )
                columns.extend(
                    [
                        DataTableColumn(
                            key="location_name", header="Location", sortable=True
                        ),
                        DataTableColumn(
                            key="balance_label",
                            header="Balance",
                            align="right",
                            sortable=True,
                        ),
                        DataTableColumn(
                            key="value_label", header="Value", align="right"
                        ),
                        DataTableColumn(
                            key="cost_label", header="Avg Cost", align="right"
                        ),
                        DataTableColumn(
                            key="last_movement_date",
                            header="Last Movement",
                            sortable=True,
                        ),
                    ]
                )
                DataTable(columns=columns, rows="{{ rows }}")

            if not_found_list:
                Separator()
                Muted(
                    content=(
                        f"Could not resolve {len(not_found_list)} "
                        f"input{'s' if len(not_found_list) != 1 else ''}: "
                        f"{', '.join(str(x) for x in not_found_list)}"
                    )
                )

        with CardFooter(), Row(gap=2):
            # First resolved handle drives both follow-up actions; falls
            # back to variant_id when the variant has no SKU.
            # ``get_inventory_movements`` only accepts ``sku`` (string),
            # so an integer variant_id forces the UpdateContext path
            # there even when check_inventory's CallTool path is fine.
            first_handle: str | int = ""
            if items:
                first_handle = items[0].get("sku") or items[0].get("variant_id") or ""

            handles: list[str | int] = [first_handle] if first_handle else []
            movements_action: Action
            if isinstance(first_handle, str) and first_handle:
                movements_action = CallTool(
                    "get_inventory_movements",
                    arguments={"sku": first_handle},
                )
            elif first_handle:
                # first_handle is a variant_id (int) — get_inventory_movements
                # has no variant_id arg, so prompt the agent to resolve.
                movements_action = UpdateContext(
                    content=(
                        f"User wants to see inventory movements for "
                        f"variant_id {first_handle}. Resolve the SKU via "
                        "get_variant_details, then call get_inventory_movements."
                    ),
                )
            else:
                movements_action = UpdateContext(
                    content="Show recent inventory movements for the "
                    "items in the inventory-at report.",
                )

            Button(
                label="Check Current Inventory",
                variant="outline",
                on_click=_check_inventory_action(
                    handles,
                    fallback_content="Check current inventory levels for "
                    "the items in the inventory-at report.",
                ),
            )
            Button(
                label="View Movements",
                variant="outline",
                on_click=movements_action,
            )
    return app


# ============================================================================
# Stock Adjustment UIs (Create / Update / Delete)
# ============================================================================


_STOCK_ADJUSTMENT_ROW_COLUMNS: list[DataTableColumn] = [
    DataTableColumn(key="sku", header="SKU"),
    DataTableColumn(key="display_name", header="Item"),
    DataTableColumn(key="quantity_label", header="Qty Change", align="right"),
    DataTableColumn(key="cost_label", header="Cost / unit", align="right"),
]

_STOCK_ADJUSTMENT_FIELD_DIFF_COLUMNS: list[DataTableColumn] = [
    DataTableColumn(key="field", header="Field"),
    # Before column added post-#card-ux (anti-pattern #5: a diff without
    # the before-side is uninterpretable — the operator can't tell if
    # they're changing a field or restating its current value). When the
    # impl can't resolve the prior_state (e.g., the SA was created before
    # this enrichment landed), the cell shows "(prior unknown)".
    DataTableColumn(key="old_value", header="Before"),
    DataTableColumn(key="new_value", header="After"),
]


def _format_qty_change(qty: float) -> str:
    """Format a quantity change with leading sign (e.g., ``+1.0``, ``-3.5``)."""
    return f"{qty:+.1f}"


def _format_cost(cost: float | int | None) -> str:
    """Format a per-unit cost; ``—`` when omitted.

    Intentionally bare-decimal — no currency symbol, no ISO code. This
    is the per-row DataTable cell formatter (Stock Adjustment rows,
    PO/SO/MO rows in cards), where the column header already conveys
    "Cost / unit" and the parent card carries the currency. Adding
    Babel-aware formatting here would clutter dense rows with
    repeated symbols (``$437.50``, ``$5.10``, ``$92.00`` x N rows) and
    duplicate information the header already provides.

    Per #751 acceptance criterion 5: revisit only if multi-currency
    mixing within a single table causes confusion. The Metric-level
    "Total" still uses :func:`_format_money` for the parent-card
    aggregate, so the currency stays visible at the right granularity.
    """
    if cost is None:
        return "—"
    return f"{cost:.2f}"


def _format_money(amount: float | int | Decimal | None, currency: str | None) -> str:
    """Format a Metric ``Total`` value using ISO 4217 currency-aware rules.

    Delegates to :func:`babel.numbers.format_currency` so the rendered string
    picks up the right symbol, decimal-digit count, and grouping for the
    currency (``$1,500.00`` for USD, ``€1,500.00`` for EUR, ``¥1,500`` for
    JPY with no decimals). Integer ``amount`` is passed through unchanged
    — Babel handles ``int``, ``float``, and ``Decimal`` identically (and
    actually rounds exact-decimal sums correctly when passed as
    :class:`~decimal.Decimal`, so call sites accumulating money should
    pass Decimal here rather than coercing back to float and reintroducing
    binary-representation drift).

    Katana has two currency concepts:

    - **Transaction currency** — ``SalesOrder.currency`` / ``PurchaseOrder.currency``;
      the currency the line totals (``total``, ``total_cost``, ``price_per_unit``)
      are denominated in. Pass this when formatting per-order amounts.
    - **Factory base currency** — ``Factory.base_currency_code``; the tenant's
      home currency. Pass this when formatting ``*_in_base_currency`` amounts
      (converted totals).

    Falls back to ``USD`` when ``currency`` is missing so the widget reads
    cleanly even on the path where the response hasn't populated the field.
    Unlike :func:`_format_cost`, never returns ``—`` — every Total-style
    metric has a value to show (``$0.00`` for unset).
    """
    return format_currency(
        0 if amount is None else amount,
        currency or "USD",
        locale="en_US",
    )


def _iso_date_only(value: object) -> str:
    """Trim a serialized ISO datetime to its ``YYYY-MM-DD`` prefix.

    ``model_dump(mode="json")`` renders ``datetime`` fields as ISO strings.
    The user-facing card surfaces them as dates; the time component is
    noise.
    """
    if isinstance(value, str):
        return value.split("T")[0]
    return str(value)


# ============================================================================
# Field-level diff helpers — shared between create and modify cards (#722).
# ============================================================================
#
# Modify cards render the same entity view as create cards (#728), with three
# overlays: before→after for changed fields, leading ✗ + inline error line for
# failed fields, +/- prefixes for added/removed nested rows. The card-level
# header Badge carries the all-applied / partial-failure status; per-field
# decoration only appears when it carries information (the changed fields and
# the failed ones).
#
# The wire shape is ``ActionResult.changes: list[FieldChange]`` (server side,
# in ``_modification.py``). ``FieldChangeView`` is the renderer-facing
# projection — it pre-resolves the bookkeeping the renderer needs without
# leaking the wire shape into the entity view's render code.


class FieldChangeView(BaseModel):
    """Per-field diff projection scoped to the modify-card renderer.

    Pre-resolves ``ActionResult.changes`` items into the shape the entity-view
    helpers consume: a side-by-side ``before`` / ``after`` plus a ``kind``
    discriminator and a ``failed`` flag that drives the leading ``✗`` glyph
    + trailing error line on failed actions.

    ``unknown_prior`` carries the wire's ``FieldChange.is_unknown_prior``
    forward — set when the best-effort fetch for the prior entity state
    failed, so the renderer should display ``(prior unknown) → new``
    rather than ``(unset) → new`` (the latter would imply the field had
    been blank, which we can't actually attest to).

    ``label`` is unused by the renderer today (the entity view picks the
    user-facing label per field) but carries the human-readable name for
    test assertions and any future generic renderer that doesn't know the
    field-name-to-label mapping at build time.
    """

    field: str
    before: Any | None = None
    after: Any | None = None
    kind: Literal["changed", "added", "removed", "unchanged"] = "changed"
    failed: bool = False
    error: str | None = None
    unknown_prior: bool = False
    label: str | None = None


def _index_changes_by_field(
    actions: list[dict[str, Any]],
    *,
    include_operations: frozenset[str] | None = None,
) -> dict[str, FieldChangeView]:
    """Flatten ``ActionResult.changes`` lists into a field-name keyed map.

    Each ActionResult carries a ``changes: list[FieldChange]`` (wire shape).
    The modify-card renderer wants a single lookup by field name so each
    entity-view line can ask ``changes.get("expected_arrival_date")`` and
    decorate inline.

    Maps each ``FieldChange`` to a ``FieldChangeView``, propagating the
    parent action's ``succeeded`` / ``error`` so failed actions surface
    per-field on every field they were going to write. A field appearing
    in two actions (rare) takes the last write — the iteration order
    matches the action plan's execution order, so the last write is the
    one that ran (or would have run) most recently.

    ``include_operations`` restricts the flatten to actions whose
    ``operation`` value (case-insensitive) is in the set — used by the SO
    modify card to keep header-field rendering from picking up sub-entity
    changes whose field names overlap header names (``status``,
    ``picked_date``, ``tracking_number`` exist on both fulfillments and
    the SO header). When ``None`` (the default), every action contributes
    — same behavior as before this parameter was added, keeps PO/test
    call sites unchanged.

    Synthesized NOT-RUN actions (``status_label == "NOT RUN"``, emitted by
    :func:`_synthesize_correction_not_run_actions` and the per-tool
    NOT-RUN synthesizers for the unattempted phase tail of a failed
    correction) are filtered out — these are placeholders for plan steps
    that never ran, not real diffs. Last-write-wins on the field map
    would otherwise let a synthesized late ``update_header`` (e.g., the
    close-phase header step in a sales-order correction) overwrite an
    earlier EXECUTED ``update_header`` diff and render as an applied
    scalar change with no NOT RUN indication. NOT RUN status surfaces
    via row-level chrome (the NOT RUN Badge on the per-action row),
    not via the header field diff map. Caught by Copilot review on #858.
    """
    out: dict[str, FieldChangeView] = {}
    for action in actions:
        if include_operations is not None:
            op = str(action.get("operation") or "").lower()
            if op not in include_operations:
                continue
        # NOT-RUN synthesized actions are plan placeholders, not real
        # diffs — never let them write into the field map (would mask
        # an earlier executed action's diff via last-write-wins).
        if str(action.get("status_label") or "") == "NOT RUN":
            continue
        succeeded = action.get("succeeded")
        action_error = action.get("error")
        # ``succeeded`` is None during preview, True/False after apply.
        # A failed action's writes never landed — render the field's
        # intended change with the ✗ glyph + error.
        failed = succeeded is False
        for change in action.get("changes") or []:
            if not isinstance(change, dict):
                continue
            field = change.get("field")
            if not isinstance(field, str):
                continue
            is_added = bool(change.get("is_added"))
            is_unchanged = bool(change.get("is_unchanged"))
            unknown_prior = bool(change.get("is_unknown_prior"))
            new_val = change.get("new")
            old_val = change.get("old")
            kind: Literal["changed", "added", "removed", "unchanged"]
            if is_unchanged:
                kind = "unchanged"
            elif is_added:
                kind = "added"
            elif new_val is None and old_val is not None:
                # No explicit "is_removed" flag today — see the
                # FieldChange docstring; a None new with non-None old
                # only appears in synthesized reverts.
                kind = "removed"
            else:
                kind = "changed"
            out[field] = FieldChangeView(
                field=field,
                before=old_val,
                after=new_val,
                kind=kind,
                failed=failed,
                error=action_error if failed else None,
                unknown_prior=unknown_prior,
            )
    return out


def _format_diff_value(value: Any) -> str:
    """Coerce a diff-side value (old or new) to display text.

    Wire shape allows None, str, int, float, bool, Decimal, list, dict; the
    entity view renders each as text. Strings, ints, and booleans render
    directly; lists/dicts fall back to ``repr`` (rare — the diff producer
    avoids nested types). None renders as ``(unset)`` so a transition from
    blank to populated reads naturally as ``(unset) → Net-30``.

    ``Decimal`` renders trimmed via ``:g`` — every modify diff flows through
    ``compute_field_diff`` → ``_normalize``, which coerces numeric /
    decimal-looking values (prices, quantities, costs) to
    :class:`~decimal.Decimal`. Without the explicit branch a price change would
    ``repr`` as ``Decimal('50.0000000000')`` instead of ``50``. ``float`` keeps
    its plain ``str`` form (raw test fixtures; production values are already
    Decimal by the time they reach here).
    """
    if value is None:
        return "(unset)"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, Decimal):
        return f"{float(value):g}"
    if isinstance(value, (int, float, str)):
        return str(value)
    return repr(value)


def _render_field_diff_line(
    label: str,
    *,
    value: Any = None,
    change: FieldChangeView | None = None,
) -> None:
    """Render one field row.

    Output modes:

    - ``change`` is None → ``Label: value``. The create-card path, plus
      modify-card lines for fields that aren't changing.
    - ``change.kind == "unchanged"`` → same as ``change=None``, but the
      display value comes from ``change.after``/``change.before`` if the
      caller didn't pass ``value`` (no-op diffs from ``compute_field_diff``
      carry the field's current value on the change itself).
    - ``change`` set, not failed → ``  Label: before → after`` (leading
      2-char gutter so the failed-state ``✗ `` glyph doesn't shift the
      field text position; see ``_render_apply_button_row`` layout-
      stability note).
    - ``change.failed`` is True → ``✗ Label: before → after``. The
      actual error message is NOT rendered inline — it aggregates into
      the consolidated bottom Alert via ``_render_failed_changes_block``
      so the diff lines above don't reflow when the apply outcome lands.
    - ``change.unknown_prior`` is True → the before side renders as
      ``(prior unknown)`` instead of the formatted before value.
      Distinguishes "we couldn't read the prior" from "the prior was
      unset" — see FieldChange's ``is_unknown_prior`` docstring.

    The leading ``✗`` glyph is the only inline per-field status marker.
    Successful applies render exactly like preview (no badges, no glyphs)
    because the card-level header Badge already carries that signal —
    avoids the visual chatter of a status pill on every changed field.
    """
    if change is None or change.kind == "unchanged":
        # When ``compute_field_diff`` emits ``is_unchanged=True``, the
        # field's current value rides on the change itself (before ==
        # after). Prefer that over ``value=None`` so a no-op update
        # doesn't mislead the user with ``(unset)`` when the field
        # actually has a value — the caller would otherwise need to
        # thread the entity value alongside ``change`` just to avoid
        # this case.
        display: Any = value
        if display is None and change is not None and change.kind == "unchanged":
            display = change.after if change.after is not None else change.before
        Text(
            content=f"{label}: "
            f"{_format_diff_value(display) if display is not None else '(unset)'}"
        )
        return
    before_txt = (
        "(prior unknown)" if change.unknown_prior else _format_diff_value(change.before)
    )
    after_txt = _format_diff_value(change.after)
    # Always reserve a 2-char gutter on the leading edge so a failure-state
    # ``✗ `` glyph doesn't shift the field text position when the apply
    # outcome lands. Non-failed lines use two spaces; failed lines swap to
    # the glyph + space — same horizontal offset either way.
    prefix = "✗ " if change.failed else "  "
    Text(content=f"{prefix}{label}: {before_txt} → {after_txt}")
    # Per-field error line is NOT rendered inline — errors aggregate
    # into a consolidated block at the bottom of the entity view (see
    # ``_render_failed_changes_block``) so the diff lines above don't
    # reflow when an apply fails.


# Initial state slots written by the unified apply rail's Confirm/Cancel
# action chains (ADR-0021). Every preview card seeds these to ``False`` /
# ``None`` so the iframe's If/Elif blocks have something to bind to before
# the first click. ``SetState`` mutations from
# ``_build_apply_action`` / ``_build_cancel_action`` flip them.
_APPLY_RAIL_STATE_INIT: dict[str, Any] = {
    "pending": False,
    "cancelled": False,
    "applied": False,
    "error": None,
}


def _stock_adjustment_rows_for_table(
    rows: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Project StockAdjustmentRowSummary dicts onto the DataTable row shape.

    Trusts the upstream pydantic model's type guarantees — the dict comes
    from ``StockAdjustmentResponse.model_dump()`` so ``sku`` /
    ``display_name`` / ``quantity`` are already correctly typed.
    """
    return [
        {
            "sku": r["sku"],
            "display_name": r["display_name"],
            "quantity_label": _format_qty_change(r["quantity"]),
            "cost_label": _format_cost(r.get("cost_per_unit")),
        }
        for r in (rows or [])
    ]


def build_stock_adjustment_create_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the create-stock-adjustment preview card with direct-apply rail.

    Used for both the ``preview=True`` branch (Confirm + Cancel buttons,
    direct-apply morph) and the ``preview=False`` branch (no buttons,
    "View in Katana" link). The same builder handles both via the
    ``is_preview`` flag — symmetric with how the modification card
    pair is structured.
    """
    is_preview = bool(response.get("is_preview"))
    rows = _stock_adjustment_rows_for_table(response.get("rows"))
    state: dict[str, Any] = {"plan_rows": rows}
    apply_action: list[Action] | None = None
    cancel_action: list[Action] | None = None
    if is_preview:
        state.update(_APPLY_RAIL_STATE_INIT)
        apply_action = _build_apply_action(confirm_tool, confirm_request)
        cancel_action = _build_cancel_action("the stock adjustment")

    location_id = response.get("location_id")
    location_name = response.get("location_name")
    adj_id = response.get("id")
    reason = response.get("reason")

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content="Stock Adjustment")
            if adj_id is not None:
                Badge(label=f"#{adj_id}", variant="outline")
            if location_id is not None:
                # Resolved ``location_name`` when impl-side filled it,
                # else fall back to ``"Location <id>"`` (anti-pattern #2
                # fallback acknowledged in the audit catalog).
                badge_label = location_name or f"Location {location_id}"
                Badge(label=badge_label, variant="outline")
            Badge(
                label="PREVIEW" if is_preview else "APPLIED",
                variant="secondary" if is_preview else "default",
            )

        with CardContent(), Column(gap=3):
            if response.get("message"):
                Text(content=response["message"])
            if reason:
                Muted(content=f"Reason: {reason}")

            if rows:
                DataTable(
                    columns=_STOCK_ADJUSTMENT_ROW_COLUMNS,
                    rows="{{ plan_rows }}",
                )

            # Surface cache-miss advisories so the operator sees *why*
            # the Tier-1 badge fell back to ``"Location <id>"`` when
            # impl-side location name resolution missed. Pre-fix the
            # warnings were emitted by the impl but never rendered.
            _render_warnings_block(response.get("warnings"))

            if is_preview:
                with If("error"):
                    Separator()
                    with Alert(variant="destructive", icon="circle-alert"):
                        AlertTitle(content="Apply failed")
                        AlertDescription(content="{{ error }}")

        with CardFooter(), Row(gap=2):
            if apply_action is not None and cancel_action is not None:
                with If("applied"):
                    Muted(content="Stock adjustment created.")
                with Elif("error"):
                    Muted(content="Apply failed — see error above.")
                with Elif("cancelled"):
                    Muted(content="Cancelled. No changes were made.")
                with Else():
                    Muted(content="This is a preview. No changes have been made.")
                _render_apply_button_row(
                    confirm_label="Confirm & Create",
                    apply_action=apply_action,
                    cancel_action=cancel_action,
                )
            elif response.get("katana_url"):
                Button(
                    label="View in Katana",
                    variant="outline",
                    on_click=OpenLink(url=response["katana_url"]),
                )
    return app


_PRIOR_UNSET = object()


def _stock_adjustment_diff_cell(
    field: str,
    label: str,
    display_value: Any,
    *,
    prior_state: dict[str, Any],
    prior_override: Any = _PRIOR_UNSET,
) -> dict[str, str]:
    """Build one Before/After diff row for the stock-adjustment update card.

    Three Before-side states:

    - ``prior_override`` supplied (anything, including ``None``) wins —
      the caller did its own resolution. Used by the Location row,
      which threads in the resolved prior location name. ``None``
      means the caller tried to resolve but couldn't (cache miss).
    - ``field`` is a key on ``prior_state`` → that value. A stored
      ``None`` renders as ``"(blank)"`` (the field WAS resolved, it
      was just empty — distinct from "we couldn't resolve at all";
      Copilot finding on PR #861).
    - ``field`` is NOT a key on ``prior_state`` → ``"(prior unknown)"``.
      prior_state was either missing entirely or omitted this field
      (impl-side pre-fetch failure / forward-compat for a new field
      that lands after this snapshot was taken).
    """
    if prior_override is not _PRIOR_UNSET:
        old_value = "(prior unknown)" if prior_override is None else str(prior_override)
    elif field in prior_state:
        prior_value = prior_state[field]
        old_value = "(blank)" if prior_value is None else str(prior_value)
    else:
        old_value = "(prior unknown)"
    return {
        "field": label,
        "old_value": old_value,
        "new_value": str(display_value),
    }


def _build_stock_adjustment_diff_rows(
    response: dict[str, Any], prior_state: dict[str, Any]
) -> list[dict[str, str]]:
    """Project the response + prior_state into per-field Before/After rows.

    Pre-#card-ux the diff table carried a ``Location ID`` row with the
    raw integer ID — anti-pattern #2. Post-#card-ux: location surfaces
    via the ``location_name`` field (resolved impl-side); the row in
    the diff table reads "Location" with the resolved name.
    """
    diff_rows: list[dict[str, str]] = []
    for field, label in (
        ("stock_adjustment_number", "Number"),
        ("stock_adjustment_date", "Date"),
        ("reason", "Reason"),
        ("additional_info", "Additional Info"),
    ):
        value = response.get(field)
        if value is not None:
            diff_rows.append(
                _stock_adjustment_diff_cell(
                    field, label, value, prior_state=prior_state
                )
            )
    if response.get("location_id") is not None:
        # Before-side reads ``prior_state["location_name"]`` so the
        # Before/After columns compare resolved name against resolved
        # name (review item #10).
        new_location = response.get("location_name") or (
            f"Location ID: {response['location_id']}"
        )
        prior_loc_id = prior_state.get("location_id")
        prior_loc_name = prior_state.get("location_name")
        if prior_loc_name:
            prior_location: str | None = prior_loc_name
        elif prior_loc_id is not None:
            prior_location = f"Location ID: {prior_loc_id}"
        else:
            prior_location = None
        diff_rows.append(
            _stock_adjustment_diff_cell(
                "location_id",
                "Location",
                new_location,
                prior_state=prior_state,
                prior_override=prior_location,
            )
        )
    return diff_rows


def build_stock_adjustment_update_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the update-stock-adjustment preview card with direct-apply rail.

    Renders the requested header field changes as a small DataTable so
    the user can sanity-check what's about to be patched.
    """
    is_preview = bool(response.get("is_preview"))
    prior_state = response.get("prior_state") or {}
    diff_rows = _build_stock_adjustment_diff_rows(response, prior_state)

    state: dict[str, Any] = {"diff_rows": diff_rows}
    apply_action: list[Action] | None = None
    cancel_action: list[Action] | None = None
    if is_preview:
        state.update(_APPLY_RAIL_STATE_INIT)
        apply_action = _build_apply_action(confirm_tool, confirm_request)
        cancel_action = _build_cancel_action("the stock-adjustment update")

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content="Update Stock Adjustment")
            if response.get("id") is not None:
                Badge(label=f"#{response['id']}", variant="outline")
            Badge(
                label="PREVIEW" if is_preview else "UPDATED",
                variant="secondary" if is_preview else "default",
            )

        with CardContent(), Column(gap=3):
            if response.get("message"):
                Text(content=response["message"])
            if diff_rows:
                DataTable(
                    columns=_STOCK_ADJUSTMENT_FIELD_DIFF_COLUMNS,
                    rows="{{ diff_rows }}",
                )
            else:
                Muted(content="No field changes supplied.")

            # Surface cache-miss advisories so the operator sees *why*
            # the Location row may render as ``"Location ID: <id>"`` or
            # the Before column as ``"(prior unknown)"``. Pre-fix the
            # warnings were emitted by the impl but never rendered.
            _render_warnings_block(response.get("warnings"))

            if is_preview:
                with If("error"):
                    Separator()
                    with Alert(variant="destructive", icon="circle-alert"):
                        AlertTitle(content="Apply failed")
                        AlertDescription(content="{{ error }}")

        with CardFooter(), Row(gap=2):
            if apply_action is not None and cancel_action is not None:
                with If("applied"):
                    Muted(content="Stock adjustment updated.")
                with Elif("error"):
                    Muted(content="Apply failed — see error above.")
                with Elif("cancelled"):
                    Muted(content="Cancelled. No changes were made.")
                with Else():
                    Muted(content="This is a preview. No changes have been made.")
                _render_apply_button_row(
                    confirm_label="Confirm & Update",
                    apply_action=apply_action,
                    cancel_action=cancel_action,
                )
            elif response.get("katana_url"):
                Button(
                    label="View in Katana",
                    variant="outline",
                    on_click=OpenLink(url=response["katana_url"]),
                )
    return app


def build_stock_adjustment_delete_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the delete-stock-adjustment preview card with direct-apply rail.

    Surfaces the identifying details (number, location, row count) so the
    user can sanity-check before confirming. Apply path reverses the
    associated inventory movements server-side — that consequence is
    called out in the footer copy.
    """
    is_preview = bool(response.get("is_preview"))
    state: dict[str, Any] = {}
    apply_action: list[Action] | None = None
    cancel_action: list[Action] | None = None
    if is_preview:
        state = dict(_APPLY_RAIL_STATE_INIT)
        apply_action = _build_apply_action(confirm_tool, confirm_request)
        cancel_action = _build_cancel_action("the stock-adjustment deletion")

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content="Delete Stock Adjustment")
            if response.get("id") is not None:
                Badge(label=f"#{response['id']}", variant="outline")
            Badge(
                label="PREVIEW" if is_preview else "DELETED",
                variant="secondary" if is_preview else "destructive",
            )

        with CardContent(), Column(gap=3):
            if response.get("message"):
                Text(content=response["message"])

            with Row(gap=4):
                Metric(
                    label="Number",
                    value=str(response.get("stock_adjustment_number") or "—"),
                )
                # Location is not a number that belongs on a Metric;
                # pre-#card-ux it rendered the raw ``location_id`` here
                # which was meaningless to the operator (anti-pattern #2).
                # The resolved location name now ships as its own
                # party-line below.
                Metric(
                    label="Rows",
                    value=str(response.get("row_count", 0)),
                )

            # Location party-line below the Metric row — same Tier-3
            # convention as the fulfill and receipt cards. Falls back to
            # ``"Location ID: <id>"`` only when impl-side resolution couldn't
            # fill ``location_name``.
            _render_party_line(
                "Location",
                name=response.get("location_name"),
                entity_id=response.get("location_id"),
            )

            # Surface cache-miss advisories so the operator sees *why*
            # the Location party-line may have fallen back to
            # ``"Location ID: <id>"``. Pre-fix the warnings were emitted
            # by the impl but never rendered.
            _render_warnings_block(response.get("warnings"))

            if is_preview:
                Muted(
                    content=(
                        "Deleting reverses the associated inventory "
                        "movements server-side. This cannot be undone."
                    )
                )
                with If("error"):
                    Separator()
                    with Alert(variant="destructive", icon="circle-alert"):
                        AlertTitle(content="Apply failed")
                        AlertDescription(content="{{ error }}")

        with CardFooter(), Row(gap=2):
            if apply_action is not None and cancel_action is not None:
                with If("applied"):
                    Muted(content="Stock adjustment deleted.")
                with Elif("error"):
                    Muted(content="Apply failed — see error above.")
                with Elif("cancelled"):
                    Muted(content="Cancelled. No changes were made.")
                with Else():
                    Muted(content="This is a preview. No changes have been made.")
                _render_apply_button_row(
                    confirm_label="Confirm & Delete",
                    apply_action=apply_action,
                    cancel_action=cancel_action,
                )
    return app


# ============================================================================
# Order UIs (Preview + Created)
# ============================================================================


def _render_preview_header(
    *,
    title_prefix: str,
    entity: str,
    order_number: str,
    status: str | None,
    extra_badges: tuple[tuple[str, str], ...] = (),
    applied_title_suffix: str = "Created",
    applied_state_label: str = "CREATED",
    applied_state_variant: str = "default",
) -> None:
    """Tier 1: CardHeader for a preview/apply card.

    Renders the title (toggles ``"X Preview"`` ↔ ``"X {applied_title_suffix}"``
    on ``state.applied``), an order-number Badge, a PREVIEW/{applied_state_label}
    state Badge (toggle on ``state.applied``), the entity status Badge with
    the bucket-driven variant from ``status_badge_variant``, and any
    caller-provided extras (e.g. ``[("outsourced", "outline")]`` for PO
    entity_type).

    Create cards default to ``"Created"`` / ``"CREATED"`` with the
    ``"default"`` (green) variant. Modify / delete / correct cards should
    pass ``applied_title_suffix="Applied"`` and ``applied_state_label="APPLIED"``
    so the rendered copy matches the actual operation.

    Partial-failure / failure outcomes on the standalone-applied path
    (where the response payload tells us the outcome at build time)
    override ``applied_state_label`` to ``"FAILED"`` / ``"PARTIAL FAILURE"``
    AND pass ``applied_state_variant="destructive"`` so the rendered chrome
    is single, internally consistent, and visually matches the outcome.
    The in-place morph path can't predict failure at build time and so
    keeps the defaults — failed actions surface there via the per-field
    ``✗`` glyphs ``_render_field_diff_line`` emits.

    ``extra_badges`` is reserved for orthogonal entity-shape signals
    (e.g. ``[("outsourced", "outline")]`` for a PO with
    ``entity_type="outsourced"``) — NOT for apply-outcome status, which
    goes on ``applied_state_label`` / ``applied_state_variant``.

    Must be called inside ``with PrefabApp(...) as app, Card():`` —
    the helper does NOT open the Card; it only adds the CardHeader row.
    """
    # Reserve a fixed-width slot for the state Badge so the in-place
    # morph (PREVIEW → APPLIED / FAILED / PARTIAL FAILURE) doesn't reflow
    # the rest of the header — order-number badge, status badge, and
    # extra badges to the right of the state Badge stay put across the
    # state transition. ``min-w-32`` ≈ 8rem, comfortable for the longest
    # current label "PARTIAL FAILURE"; ``text-center`` keeps shorter
    # labels centered within the slot.
    _state_badge_css = "min-w-32 text-center"
    with CardHeader(), Row(gap=2):
        with If("applied"):
            CardTitle(content=f"{title_prefix} {applied_title_suffix}")
        with Else():
            CardTitle(content=f"{title_prefix} Preview")
        Badge(label=order_number, variant="outline")
        with If("applied"):
            Badge(
                label=applied_state_label,
                variant=applied_state_variant,
                css_class=_state_badge_css,
            )
        with Else():
            Badge(label="PREVIEW", variant="secondary", css_class=_state_badge_css)
        if status:
            Badge(label=status, variant=status_badge_variant(entity, status))
        for label, variant in extra_badges:
            Badge(label=label, variant=variant)


def _render_warnings_block(warnings: list[str] | None) -> list[str]:
    """Render the warnings section of Tier 3 and return the block-warning list.

    Block warnings render as destructive Badges (the ``BLOCK:`` prefix is
    stripped); regular warnings render as secondary Badges. A ``Separator``
    precedes the badges only when at least one warning exists.

    Returns the unprefixed block-warning list so the caller can pass it to
    ``_render_apply_button_row(disabled=bool(block_warnings))`` — block
    warnings gate the Confirm button (and the Tier-4 message swaps from
    "preview" to "cannot proceed" accordingly).

    Must be called inside the ``CardContent`` column block.
    """
    block_warnings, regular_warnings = _split_warnings(warnings)
    if block_warnings or regular_warnings:
        Separator()
        for w in block_warnings:
            Badge(label=w, variant="destructive")
        for w in regular_warnings:
            Badge(label=w, variant="secondary")
    return block_warnings


def _render_preview_footer(
    *,
    title_prefix: str,
    block_warnings: list[str],
    confirm_label: str,
    apply_action: list[Action] | None,
    cancel_action: list[Action],
    next_action_buttons: tuple[tuple[str, Action], ...] = (),
    applied_verb: str = "created",
) -> None:
    """Tier 4: CardFooter for a preview/apply card.

    ``applied_verb`` controls the muted body line in applied state — create
    cards default to ``"created"`` ("Purchase Order created."); modify cards
    should pass ``"applied"`` ("Purchase Order Modify applied.") so the user-
    visible copy matches the actual operation.

    ``next_action_buttons`` is a tuple of ``(label, action)`` pairs — the
    action is an ``Action`` instance (``CallTool``, ``OpenLink``, or
    ``UpdateContext``). The footer simply emits each as a button; callers
    decide the action shape based on whether the next-step tool's args
    are resolvable from the apply response (CallTool) or need agent
    composition (UpdateContext).

    The applied-state View-in-Katana link and the per-entity next-action
    buttons bind to ``{{ result.<field> }}`` templates so they work in
    both entry paths:

    - In-place morph: the preview response has no ``id`` / ``katana_url``,
      but the direct-apply rail's on_success chain writes the apply
      response into ``state.result`` before flipping ``applied=True``, so
      the buttons resolve correctly at render time.
    - Standalone-applied (``is_preview=False``): :func:`_init_create_card_state`
      pre-seeds ``state.result`` from the response, so the same templates
      resolve there too.

    The View-in-Katana button is gated by ``If("result.katana_url")`` so
    it hides when the apply response carries no URL (defensive — every
    create_* tool sets one today; successful deletes null it out upstream).

    Must be called inside ``with PrefabApp(...) as app, Card():``.
    """
    with CardFooter(), Column(gap=2):
        if block_warnings:
            Muted(
                content="Cannot proceed — see warnings above. No changes have been made."
            )
            _render_apply_button_row(
                confirm_label=confirm_label,
                apply_action=None,
                cancel_action=cancel_action,
                disabled=True,
            )
            return
        with If("applied"):
            Muted(content=f"{title_prefix} {applied_verb}.")
            with Row(gap=2):
                with If("result.katana_url"):
                    Button(
                        label="View in Katana",
                        variant="outline",
                        on_click=OpenLink(url="{{ result.katana_url }}"),
                    )
                for label, action in next_action_buttons:
                    Button(
                        label=label,
                        variant="outline",
                        on_click=action,
                    )
        with Elif("error"):
            Muted(content="Apply failed — see error above.")
        with Elif("cancelled"):
            Muted(content="Cancelled. No changes were made.")
        with Else():
            Muted(content="This is a preview. No changes have been made.")
            _render_apply_button_row(
                confirm_label=confirm_label,
                apply_action=apply_action,
                cancel_action=cancel_action,
            )


def _init_create_card_state(response: dict[str, Any]) -> dict[str, Any]:
    """Seed iframe state for a create card.

    The direct-apply rail flips ``applied=True`` (and optionally
    ``error="…"``) on Confirm success/failure; the in-place morph
    re-renders the same Prefab tree against the new state. When the
    response enters with ``is_preview=False`` (the standalone post-apply
    path), we seed ``applied=True`` at construction time so the same
    builder serves both entry paths.

    ``state.result`` carries the apply-response data used by the
    applied-state Buttons (``{{ result.katana_url }}`` etc.). On the
    standalone-applied path we seed it from the response here; on the
    in-place morph path the on_success chain in
    :func:`_build_apply_action` populates it via
    ``SetState("result", RESULT)`` before flipping ``applied=True``.
    """
    applied = not response.get("is_preview", True)
    state: dict[str, Any] = {**_APPLY_RAIL_STATE_INIT, "applied": applied}
    if applied:
        state["result"] = response
    return state


def _render_ecommerce_link(entity: dict[str, Any]) -> None:
    """Render the 'Open in {platform}' storefront link for a sales order, or
    nothing.

    Reads the precomputed ``ecommerce_url`` (set impl-side on the
    ``get_sales_order`` detail response) and falls back to deriving it from the
    raw ``ecommerce_order_type`` / ``ecommerce_store_name`` /
    ``ecommerce_order_id`` fields — the shape the modify card's ``prior_state``
    snapshot (``SalesOrder.to_dict()``) carries, where ``ecommerce_url`` is
    absent. Renders nothing when the order has no recognized storefront link
    (unrecognized integration such as an eBay order imported via middleware, or
    a missing store/order id), so callers invoke it unconditionally.

    Must be called inside a ``Column`` / ``CardContent`` context.
    """
    order_type = entity.get("ecommerce_order_type")
    url = entity.get("ecommerce_url") or ecommerce_storefront_url(
        order_type,
        entity.get("ecommerce_store_name"),
        entity.get("ecommerce_order_id"),
    )
    if not url:
        return
    label = ecommerce_platform_label(order_type) or "storefront"
    with Row(gap=1):
        Text(content="Storefront:")
        Link(content=f"Open in {label}", href=url, target="_blank")


def _render_party_line(
    label: str,
    *,
    name: str | None,
    entity_id: int | None,
    entity_kind: EntityKind | None = None,
) -> None:
    """Render a 'Supplier:' / 'Customer:' / 'Location:' line.

    Three render shapes, in order:

    1. ``name`` + ``entity_kind`` (which yields a web URL) → ``<label>:
       <Link name>``. The Link is the user's click-through to the
       source-of-truth Katana page. Used for Customer / Supplier /
       Product / Material parties that have per-entity web pages.
    2. ``name`` only (no ``entity_kind``, or ``entity_kind`` has no web
       URL) → ``<label>: <name>``. Used for Location / Variant — entity
       types Katana doesn't expose per-page in the web UI. The
       entity_id is still on the response for programmatic use, but the
       card text doesn't echo it (anti-pattern #2: don't double-print
       a raw ID next to its resolved name when there's no click-through
       to anchor).
    3. No name → ``<label> ID: <entity_id>``. The fallback when impl-side
       name resolution couldn't fill ``name``; surfacing the ID is the
       only way the operator can identify the entity at all. The matching
       impl path should also append a cache-miss advisory to ``warnings``
       so the operator sees *why* the name is missing.

    Skips entirely when ``entity_id`` is None.
    """
    if entity_id is None:
        return
    url = katana_web_url(entity_kind, entity_id) if entity_kind else None
    if name and url:
        with Row(gap=1):
            Text(content=f"{label}:")
            Link(content=name, href=url, target="_blank")
    elif name:
        Text(content=f"{label}: {name}")
    else:
        Text(content=f"{label} ID: {entity_id}")


def _render_party_diff_line(
    label: str,
    *,
    id_change: FieldChangeView,
    name_change: FieldChangeView | None,
    prior_name: str | None,
) -> None:
    """Render the composite ``<label>: <before-name> (<before-id>) → <after-name> (<after-id>)``
    line for a party (supplier / customer / location) whose linked entity
    is changing.

    Hides the create-card-style Link decoration on diff lines — once a
    field is changing, the user's attention is on what's changing, not
    on click-through to the source. The Link form returns when the field
    is unchanged (see :func:`_render_party_line`).

    Before/after name resolution:

    - **before**: prefer ``name_change.before``; fall back to ``prior_name``
      (= ``entity.get("<field>_name")`` sourced from ``prior_state``).
      The prior is correct for the before side regardless of whether
      the name itself appears in the diff.
    - **after**: prefer ``name_change.after``. When ``name_change`` is
      absent AND the ID genuinely swapped (``id_change.before !=
      id_change.after``), the after-side name is **unknown** at render
      time — fall through to the bare ``#<id>`` form rather than reusing
      ``prior_name``, which would show the OLD supplier's name labelled
      as the new one (the second-order bug Copilot caught on #755). The
      common case where ``compute_field_diff`` emits only ``supplier_id``
      changes (because ``supplier_name`` isn't a request field) lands
      here.
    - **synthesized no-op ID diff** (``before == after``): use
      ``prior_name`` for both sides.
    """
    if id_change.unknown_prior:
        before_label = "(prior unknown)"
    else:
        before_name = name_change.before if name_change is not None else prior_name
        before_label = (
            f"{before_name} ({id_change.before})"
            if before_name
            else f"#{id_change.before}"
        )
    if name_change is not None:
        after_name: str | None = name_change.after
    elif id_change.before == id_change.after:
        after_name = prior_name
    else:
        after_name = None
    after_label = (
        f"{after_name} ({id_change.after})" if after_name else f"#{id_change.after}"
    )
    # 2-char gutter — same rationale as ``_render_field_diff_line``;
    # error messages aggregate into the bottom block, not inline.
    prefix = "✗ " if id_change.failed else "  "
    Text(content=f"{prefix}{label}: {before_label} → {after_label}")


def _render_failed_changes_block(
    changes: dict[str, FieldChangeView],
    *,
    field_label_overrides: dict[str, str] | None = None,
) -> None:
    """Render a consolidated Alert block listing every failed field and
    its error, at the bottom of the entity view.

    Per the layout-stability design: per-field ``✗`` glyphs surface
    inline next to each failed field (via the 2-char gutter in
    ``_render_field_diff_line``), but the actual error message is NOT
    rendered inline — it lives here, in a single Alert at the bottom of
    the card body. This way a failed apply doesn't push the unchanged
    diff lines around when the in-place morph fires: the diff lines
    stay put, an Alert appears below.

    ``field_label_overrides`` lets the caller map wire field names to
    user-facing labels (e.g. ``"additional_info"`` → ``"Notes"``,
    ``"supplier_id"`` → ``"Supplier"``) so the block reads as
    user-facing labels instead of wire names. Falls back to the
    ``FieldChangeView.label`` then the bare field name.

    Renders nothing when no failed changes are present, so the bottom
    of the card stays compact in the success case.
    """
    overrides = field_label_overrides or {}
    failed = [c for c in changes.values() if c.failed and c.error]
    if not failed:
        return
    with Alert(variant="destructive", icon="circle-alert"):
        n = len(failed)
        AlertTitle(content=f"{n} failed change{'s' if n != 1 else ''}")
        for change in failed:
            label = (
                overrides.get(change.field)
                or change.label
                or change.field.replace("_", " ").title()
            )
            # Word prefix "Failed — " instead of a bare ``✗`` glyph: the
            # Alert already carries the failure semantic via its
            # destructive variant + circle-alert icon, and a word prefix
            # reads cleanly aloud (per the /ui-review audit — the
            # ``✗`` glyph would announce as "ballot x" or be skipped
            # entirely by some screen readers).
            AlertDescription(content=f"Failed — {label}: {change.error}")


def _normalize_po_prior_state(prior_state: dict[str, Any] | None) -> dict[str, Any]:
    """Map a PO ``prior_state`` snapshot from the wire shape produced by
    ``RegularPurchaseOrder.to_dict()`` (server-side) to the response shape
    ``_render_po_entity_view`` consumes.

    The two shapes differ on key names because ``ModificationResponse.prior_state``
    is the raw entity snapshot (for revert reference) while the response
    payload uses friendlier display-oriented names:

    - ``order_no`` (wire) → ``order_number`` (response shape)
    - ``total`` (wire) → ``total_cost`` (response shape)
    - ``additional_info`` (wire) → ``notes`` (response shape)
    - ``supplier`` nested object → flat ``supplier_name`` (the looked-up
      display value the response-layer adds)

    ``item_count`` (response-only) is not derivable from the snapshot at
    the entity level — the row count would require descending into
    ``purchase_order_rows`` which the renderer doesn't need today.

    Without this adapter the modify card renders mostly-empty header
    rows in production: ``entity.get("order_number")`` falls through to
    ``None`` because the wire-shape snapshot only has ``order_no``.
    Caught by Copilot review on #755.
    """
    if not prior_state:
        return {}
    # Pass through fields whose names already match (id, supplier_id,
    # location_id, status, entity_type, currency, expected_arrival_date,
    # warnings — though warnings is response-only and won't be in the
    # snapshot). Then map renamed fields explicitly.
    out = dict(prior_state)
    if "order_no" in prior_state and "order_number" not in out:
        out["order_number"] = prior_state["order_no"]
    if "total" in prior_state and "total_cost" not in out:
        out["total_cost"] = prior_state["total"]
    if "additional_info" in prior_state and "notes" not in out:
        out["notes"] = prior_state["additional_info"]
    # Nested supplier object → flat supplier_name. ``to_dict()`` on the
    # nested attrs Supplier produces a dict (or UNSET sentinel when not
    # populated); ``supplier_name`` already in out wins.
    supplier_obj = prior_state.get("supplier")
    if (
        isinstance(supplier_obj, dict)
        and "name" in supplier_obj
        and "supplier_name" not in out
    ):
        out["supplier_name"] = supplier_obj["name"]
    return out


def _render_po_entity_view(
    entity: dict[str, Any],
    *,
    changes: dict[str, FieldChangeView] | None = None,
) -> list[str]:
    """Render the purchase-order entity view (Tier 2 metrics + Tier 3
    reference fields + warnings).

    Shared between ``build_po_create_ui`` (no diff overlay) and
    ``build_po_modify_ui`` (diff overlay via ``changes``). Returns the
    block-warning list so callers can gate the Confirm button.

    Diff-decoration rules (when ``changes`` is set):
    - Each rendered field line looks up ``changes.get("<wire_field>")``
      and, if present, swaps its rendering for the before→after form.
    - Unchanged fields render the same as the create card.
    - The Total Metric shows ``entity["total_cost"]``. On the apply path
      the caller overlays the dispatcher's post-apply header snapshot
      (``extras["post_apply_state"]``, carrying Katana's server-recomputed
      ``total``) so line-item adds/removes/qty edits are reflected; on the
      preview path it's the pre-modify ``prior_state`` total.

    Must be called inside ``with PrefabApp(...) as app, Card(): with
    CardContent(), Column(gap=3):``.
    """
    changes = changes or {}
    total_cost = entity.get("total_cost")
    currency = entity.get("currency")
    item_count = entity.get("item_count")

    # Tier 2 — Decision metrics. Metrics stay un-decorated; the bottom
    # entity-view rows surface the actual before→after for changed
    # fields. Showing two diffs of total_cost (Metric + line) would
    # double-count visual weight.
    if total_cost is not None or item_count is not None:
        with Row(gap=4):
            if total_cost is not None:
                Metric(label="Total", value=_format_money(total_cost, currency))
            if item_count is not None:
                Metric(label="Line Items", value=str(item_count))

    # Tier 3 — Reference fields. Each line looks up its wire-field
    # change; missing entries render as unchanged.

    # Supplier / Location — composite lines pull both _id and _name
    # changes; today the supplier_id change is the trigger (the name
    # follows from the lookup), so we key off supplier_id but show the
    # name in the decorated form. ``ModificationResponse.model_dump()``
    # does not carry the post-change ``supplier_name`` / ``location_name``
    # at top level — ``entity`` is composed from ``prior_state``, so
    # ``entity.get("supplier_name")`` is the OLD name. The after-side
    # name MUST come from the ``supplier_name`` FieldChange when the
    # supplier swaps; only fall back to entity (= prior) when the diff
    # didn't include a name change (rare — name unchanged means before
    # == after, so the prior is the right value for both sides).
    # ``kind="unchanged"`` is treated identically to "no change present" —
    # a no-op id patch (request set supplier_id=100 when it was already
    # 100) shouldn't surface a "Acme (100) → Acme (100)" diff line; fall
    # through to the regular party-line Link rendering instead.
    supplier_change = changes.get("supplier_id")
    prior_supplier_name = entity.get("supplier_name")
    if supplier_change is not None and supplier_change.kind != "unchanged":
        _render_party_diff_line(
            "Supplier",
            id_change=supplier_change,
            name_change=changes.get("supplier_name"),
            prior_name=prior_supplier_name,
        )
    else:
        _render_party_line(
            "Supplier",
            name=prior_supplier_name,
            entity_id=entity.get("supplier_id"),
            entity_kind="supplier",
        )

    location_change = changes.get("location_id")
    prior_location_name = entity.get("location_name")
    if location_change is not None and location_change.kind != "unchanged":
        _render_party_diff_line(
            "Location",
            id_change=location_change,
            name_change=changes.get("location_name"),
            prior_name=prior_location_name,
        )
    else:
        _render_party_line(
            "Location",
            name=prior_location_name,
            entity_id=entity.get("location_id"),
        )

    # Scalar header fields rendered via the shared field-diff helper.
    # ``additional_info`` is the wire name; the request schema exposes it
    # as ``notes`` for create, but modify's FieldChange surfaces the wire
    # name. Look up under both so a card built from a create-shape
    # response decorates the right line too.
    notes_change = changes.get("additional_info") or changes.get("notes")
    notes_value = entity.get("notes") or entity.get("additional_info")
    if notes_change is not None or notes_value:
        _render_field_diff_line("Notes", value=notes_value, change=notes_change)

    expected_arrival_change = changes.get("expected_arrival_date")
    if expected_arrival_change is not None:
        _render_field_diff_line(
            "Expected arrival",
            change=expected_arrival_change,
        )

    status_change = changes.get("status")
    if status_change is not None:
        # Status changes already surface in the Tier 1 header Badge, but
        # decorate the diff line for explicitness — the badge shows
        # "after" only; the body line shows "before → after" so the
        # transition is unambiguous.
        _render_field_diff_line("Status", change=status_change)

    # Trailer — consolidated failure block (only renders when any field
    # failed; the per-field ✗ glyphs above carry the inline signal).
    # Field-name → user-facing label map keeps the failure block reading
    # in card vocabulary, not wire vocabulary.
    _render_failed_changes_block(
        changes,
        field_label_overrides={
            "supplier_id": "Supplier",
            "location_id": "Location",
            "additional_info": "Notes",
            "notes": "Notes",
            "expected_arrival_date": "Expected arrival",
            "order_no": "Order #",
            "order_number": "Order #",
        },
    )

    # Trailer — warnings (returns the block-warning list for the caller
    # to gate Confirm).
    return _render_warnings_block(entity.get("warnings"))


def build_po_create_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the create-purchase-order card. Handles both preview
    (``is_preview=True`` → PREVIEW Badge + Confirm/Cancel + direct-apply
    morph) and applied (``is_preview=False`` → CREATED Badge + View in
    Katana + next-action buttons) states. Reads
    ``PurchaseOrderResponse.model_dump()`` directly.

    Four-tier framework (#537):
    - Tier 1 — Identity: title, order_number badge, PREVIEW/CREATED state
      badge, status badge, entity_type badge (regular/outsourced).
    - Tier 2 + 3 — content from ``_render_po_entity_view`` (shared with
      ``build_po_modify_ui``; create cards pass ``changes=None`` so no
      diff overlay). Total Metric formats via :func:`_format_money` —
      Babel picks the symbol + decimal precision from the ISO 4217 code.
    - Tier 4 — Actions: Confirm + Cancel via the direct-apply rail
      (Confirm fires ``tools/call`` directly and pushes the structured
      apply response back via ``ui/update-model-context``); applied state
      surfaces View in Katana + Receive Items + Verify Document buttons.
    """
    order_number = response.get("order_number") or "N/A"
    status = response.get("status")
    entity_type = response.get("entity_type")

    apply_action = _build_apply_action(confirm_tool, confirm_request)
    cancel_action = _build_cancel_action("that purchase order")
    extra_badges: tuple[tuple[str, str], ...] = (
        ((entity_type, "outline"),) if entity_type and entity_type != "regular" else ()
    )

    with (
        PrefabApp(state=_init_create_card_state(response), css_class="p-4") as app,
        Card(),
    ):
        _render_preview_header(
            title_prefix="Purchase Order",
            entity="purchase_order",
            order_number=order_number,
            status=status,
            extra_badges=extra_badges,
        )
        with CardContent(), Column(gap=3):
            block_warnings = _render_po_entity_view(response)
        _render_preview_footer(
            title_prefix="Purchase Order",
            block_warnings=block_warnings,
            confirm_label="Confirm & Create Purchase Order",
            apply_action=apply_action,
            cancel_action=cancel_action,
            next_action_buttons=(
                # Both follow-ups need request fields the PO-create
                # response can't supply (per-row receive items;
                # document_items to verify against), so they hand off to
                # the agent via UpdateContext rather than calling the
                # tool directly. ``{{ result.id }}`` resolves against
                # the create response's state at render time.
                (
                    "Receive Items",
                    UpdateContext(
                        content=(
                            "User wants to receive items for purchase order "
                            "{{ result.id }}. Ask which rows to receive and "
                            "in what quantities, then call "
                            "receive_purchase_order with preview=True."
                        ),
                    ),
                ),
                (
                    "Verify Document",
                    UpdateContext(
                        content=(
                            "User wants to verify a supplier document against "
                            "purchase order {{ result.id }}. Ask the user to "
                            "share the document line items (sku, quantity, "
                            "unit_price), then call verify_order_document."
                        ),
                    ),
                ),
            ),
        )
    return app


def _render_address_block(label: str, address: dict[str, Any]) -> bool:
    """Render one labeled multi-line address block (billing or shipping).

    Surfaces the fields a user actually verifies before committing: who the
    package is for (recipient name + company), the street lines, the city /
    state / zip, the country, and the contact phone. Skips blank components
    silently so a partial address (e.g. country-only) renders as one tight
    block rather than five empty lines.

    Returns ``True`` if the block rendered; ``False`` if every field
    except ``entity_type`` was empty (caller can decide whether to skip
    the whole address section).

    Must be called inside a ``CardContent`` column block.
    """
    name_parts = [p for p in (address.get("first_name"), address.get("last_name")) if p]
    recipient = " ".join(name_parts) if name_parts else None
    company = address.get("company")
    line_1 = address.get("line_1")
    line_2 = address.get("line_2")
    city = address.get("city")
    state = address.get("state")
    # Wire name is ``zip``; the attrs model exposes it as ``zip_`` but
    # ``model_dump()`` emits the wire name, so we read ``zip`` here.
    postal = address.get("zip")
    country = address.get("country")
    phone = address.get("phone")

    street = ", ".join(p for p in (line_1, line_2) if p)
    locality_parts: list[str] = []
    if city:
        locality_parts.append(city)
    state_zip = " ".join(p for p in (state, postal) if p)
    if state_zip:
        locality_parts.append(state_zip)
    locality = ", ".join(locality_parts)
    country_phone = " • ".join(p for p in (country, phone) if p)

    body_lines = [
        line for line in (recipient, company, street, locality, country_phone) if line
    ]
    # Skip rendering entirely when every meaningful field is empty —
    # otherwise the card surfaces a dangling "Billing Address:" label
    # with no content underneath, which reads as broken.
    if not body_lines:
        return False
    with Column(gap=0):
        Text(content=f"{label}:")
        for line in body_lines:
            Text(content=f"  {line}")
    return True


# Re-export so existing call sites in this module keep working. The real
# helper now lives in ``_addresses`` so impl-side ``foundation/*`` modules
# can use it without depending on the Prefab UI module (avoids a latent
# circular import; ``prefab_ui`` already imports several foundation
# modules).
_addresses_are_equivalent = addresses_are_equivalent


def _render_customer_entity_view(
    entity: dict[str, Any],
    *,
    changes: dict[str, Any] | None = None,
) -> list[str]:
    """Render the customer entity view (Tier 3 reference fields + addresses).

    Shared shape with :func:`_render_po_entity_view`: a future
    ``build_customer_modify_ui`` will pass ``changes`` to decorate each
    scalar field with ``before → after``. ``changes`` is typed loosely as
    ``dict[str, Any]`` for now because the modify-card framework's
    ``FieldChangeView`` will land with #721's customer card; the
    create-card path always passes ``changes=None``.

    Customer cards skip Tier 2 metrics entirely — there's no money or count
    aggregate worth promoting to a metric. The decision the operator makes
    is "this person/company exists in our system," reviewed via the Tier 3
    fields directly.

    Returns the block-warning list (always empty for now; reserved for
    future business-rule blocks such as duplicate-email warnings).

    Must be called inside ``with PrefabApp(...) as app, Card(): with
    CardContent(), Column(gap=3):``.
    """
    changes = changes or {}
    rendered_any = False

    contact_lines = (
        ("Email", entity.get("email")),
        ("Phone", entity.get("phone")),
        ("Company", entity.get("company")),
        ("Currency", entity.get("currency")),
        ("Category", entity.get("category")),
        ("Reference ID", entity.get("reference_id")),
    )
    for label, value in contact_lines:
        change = changes.get(_customer_change_key(label))
        if change is not None or value:
            _render_field_diff_line(label, value=value, change=change)
            rendered_any = True

    discount_rate = entity.get("discount_rate")
    discount_change = changes.get("discount_rate")
    if discount_change is not None or discount_rate is not None:
        # ``:g`` switches to scientific notation outside ~1e-5..1e+6;
        # an operator fat-finger like ``discount_rate=1000000`` would
        # then render as "1e+06%" — a deliberate-looking technical
        # value rather than the obvious red flag the operator needs.
        # ``:.4f`` with trailing-zero strip keeps fixed-point in all
        # realistic discount ranges.
        if isinstance(discount_rate, bool) or not isinstance(
            discount_rate, (int, float)
        ):
            display: Any = discount_rate
        else:
            display = f"{discount_rate:.4f}".rstrip("0").rstrip(".") + "%"
        _render_field_diff_line("Discount Rate", value=display, change=discount_change)
        rendered_any = True

    comment = entity.get("comment")
    comment_change = changes.get("comment")
    if comment_change is not None or comment:
        _render_field_diff_line("Notes", value=comment, change=comment_change)
        rendered_any = True

    addresses = entity.get("addresses") or []
    if addresses:
        # Sort billing before shipping so the visual order matches operator
        # expectation. Unknown entity_types sort last in stable insert order.
        order = {"billing": 0, "shipping": 1}
        sorted_addresses = sorted(
            addresses, key=lambda a: order.get(a.get("entity_type") or "", 2)
        )
        # Collect ALL billing addresses for dedup, not just the last —
        # a customer with multiple billings shouldn't fail dedup when
        # shipping matches the first billing but not the most recently
        # rendered one. Loop matches each shipping against any prior billing.
        rendered_billings: list[dict[str, Any]] = []
        for addr in sorted_addresses:
            entity_type = (addr.get("entity_type") or "").lower()
            label = (
                "Billing Address"
                if entity_type == "billing"
                else "Shipping Address"
                if entity_type == "shipping"
                else "Address"
            )
            if entity_type == "shipping" and any(
                _addresses_are_equivalent(b, addr) for b in rendered_billings
            ):
                Text(content="Shipping Address: (same as billing)")
                rendered_any = True
                continue
            if _render_address_block(label, addr):
                rendered_any = True
                if entity_type == "billing":
                    rendered_billings.append(addr)

    # Empty-card defense: a minimal create_customer(name='X') has no
    # Tier 3 content to surface. Without this fallback the CardContent
    # column would be empty and the card would read as broken (header
    # + blank body + footer).
    if not rendered_any:
        Muted(content="No additional contact details provided.")

    return _render_warnings_block(entity.get("warnings"))


_CUSTOMER_FIELD_TO_WIRE = {
    "Email": "email",
    "Phone": "phone",
    "Company": "company",
    "Currency": "currency",
    "Category": "category",
    "Reference ID": "reference_id",
    "Discount Rate": "discount_rate",
    # "Notes" surfaces the wire field ``comment`` (see
    # ``_render_customer_entity_view`` — the label is operator-friendly,
    # the diff key still has to match the wire-shape).
    "Notes": "comment",
}


def _customer_change_key(label: str) -> str:
    """Map a user-facing label to the wire field name a future modify card
    would key its diff lookup off. Kept inline to keep the create-card
    helper self-contained; the eventual modify card will read the same map.

    Fallback normalizes spaces → underscores so any label not explicitly
    mapped still produces a wire-shaped key (``"Two Word"`` → ``"two_word"``)
    rather than a literal lowercase with embedded space.
    """
    return _CUSTOMER_FIELD_TO_WIRE.get(label, label.lower().replace(" ", "_"))


def build_customer_create_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the create-customer card. Handles both preview
    (``is_preview=True`` → PREVIEW Badge + Confirm/Cancel + direct-apply
    morph) and applied (``is_preview=False`` → CREATED Badge + View in
    Katana + next-action buttons) states. Reads
    ``CreateCustomerResponse.model_dump()`` directly.

    Four-tier framework (#537), pioneer per-entity card for #817:

    - Tier 1 — Identity: title, **customer name** as the headline Badge
      (the ``_render_preview_header(order_number=...)`` slot — the helper
      param name is historical from PO/SO/MO; for customer the name itself
      is the headline), PREVIEW/CREATED state badge, currency badge when
      set.
    - Tier 2 — *omitted* — customer creates have no money/count aggregate
      worth promoting to a Metric.
    - Tier 3 — content from :func:`_render_customer_entity_view` (shared
      with the future ``build_customer_modify_ui`` per the #721 design;
      create cards pass ``changes=None`` so no diff overlay).
    - Tier 4 — Actions: Confirm & Create + Cancel via the direct-apply
      rail; applied state surfaces View in Katana + "Create Sales Order"
      next-action button.
    """
    name = response.get("name") or "Customer"
    # Truncate the headline Badge to keep Tier 1 layout stable. Katana
    # accepts free-text ``name`` of arbitrary length; PO/SO/MO never
    # exercised this slot with anything longer than ~20 chars, so the
    # helper assumed short headlines. 48 chars fits a typical company
    # name; longer ones surface in the Tier 3 Notes / contact body
    # where the operator can read them in full.
    badge_name = name if len(name) <= 48 else name[:45] + "…"
    currency = response.get("currency")
    apply_action = _build_apply_action(confirm_tool, confirm_request)
    cancel_action = _build_cancel_action("that customer")
    extra_badges: tuple[tuple[str, str], ...] = (
        ((currency, "secondary"),) if currency else ()
    )

    with (
        PrefabApp(state=_init_create_card_state(response), css_class="p-4") as app,
        Card(),
    ):
        _render_preview_header(
            title_prefix="Customer",
            entity="customer",
            order_number=badge_name,
            status=None,
            extra_badges=extra_badges,
        )
        with CardContent(), Column(gap=3):
            block_warnings = _render_customer_entity_view(response)
        _render_preview_footer(
            title_prefix="Customer",
            block_warnings=block_warnings,
            confirm_label="Confirm & Create Customer",
            apply_action=apply_action,
            cancel_action=cancel_action,
            next_action_buttons=(
                # ``create_sales_order`` needs items + quantities that the
                # customer-create response can't supply. Per ADR-0021,
                # that's an ``UpdateContext`` (agent composes the call)
                # rather than a deterministic ``CallTool``. Matches the
                # PO card's "Receive Items" follow-up shape.
                (
                    "Create Sales Order",
                    UpdateContext(
                        content=(
                            "User wants to create a sales order for "
                            "customer {{ result.id }} ({{ result.name }}). "
                            "Ask which items and quantities, then call "
                            "create_sales_order with preview=True."
                        ),
                    ),
                ),
            ),
        )
    return app


def _init_modify_card_state(response: dict[str, Any]) -> dict[str, Any]:
    """Seed iframe state for a modify card.

    Mirrors :func:`_init_create_card_state` but adds nothing extra — the
    modify card uses the same applied/pending/cancelled/error booleans
    and the same ``result`` slot on the standalone-applied path so the
    direct-apply on_success chain (``SetState("result", RESULT)``)
    populates the post-apply data uniformly.
    """
    return _init_create_card_state(response)


def _render_apply_outcome_badge(*, css_class: str = "min-w-32 text-center") -> None:
    """Render the reactive Tier-1 state Badge for a collection modify card.

    Shows ``PREVIEW`` until the apply lands, then morphs to the outcome label
    (``APPLIED`` / ``PARTIAL FAILURE`` / ``FAILED``) with the variant tracking
    the outcome (``destructive`` for partial/total failure, ``default`` for
    success). Reads the state slots ``applied`` / ``applied_outcome_label`` /
    ``applied_outcome_variant`` — seeded by the builder with preview-time
    defaults and overwritten by the apply ``on_success`` SetState chain from
    ``$result.state.<slot>``.

    Badge.variant isn't reactive on its own, so the success/failure split is
    rendered as parallel components under an ``If`` chain and the renderer
    picks the right one at morph time. Shared by ``build_bom_modify_ui`` and
    ``build_item_modify_ui`` (both render a collection diff table whose header
    needs the same morphing outcome pill). Must be called inside a header Row.
    """
    with If("applied"):
        with If(Rx("applied_outcome_variant") == "destructive"):
            Badge(
                label="{{ applied_outcome_label }}",
                variant="destructive",
                css_class=css_class,
            )
        with Else():
            Badge(
                label="{{ applied_outcome_label }}",
                variant="default",
                css_class=css_class,
            )
    with Else():
        Badge(label="PREVIEW", variant="secondary", css_class=css_class)


def _coerce_resolved_id_map(value: Any) -> dict[int, dict[str, str | None]]:
    """Coerce a wire ``{variant_id: {sku, display_name}}`` map back to int keys.

    ``model_dump`` round-trips a ``dict[int, ...]`` with string keys on the
    wire; coerce them back so the row-table merge's ``int`` variant-id lookups
    hit. Non-int keys / non-dict values are skipped. Shared shape with the BOM
    card's ``resolved_ingredients`` coercion.
    """
    out: dict[int, dict[str, str | None]] = {}
    if not isinstance(value, dict):
        # Missing / malformed extras (None, list, …) → no resolved names; the
        # table still renders with the ``variant <id>`` fallback.
        return out
    for key, val in value.items():
        try:
            int_key = int(key)
        except (TypeError, ValueError):
            continue
        if isinstance(val, dict):
            out[int_key] = {
                "sku": val.get("sku"),
                "display_name": val.get("display_name"),
            }
    return out


def _modify_confirm_label(verb_label: str, n_actions: int) -> str:
    """Confirm-button label for a modify card — ``Confirm Delete`` for deletes,
    else scaled with the action count (``Confirm 4 changes`` / ``Confirm
    Changes``). Shared by the PO + MO modify cards.
    """
    if verb_label == "Delete":
        return "Confirm Delete"
    return f"Confirm {n_actions} changes" if n_actions > 1 else "Confirm Changes"


def _modify_applied_state_labels(
    verb_label: str, *, is_preview: bool, actions: list[dict[str, Any]]
) -> tuple[str, str, str, str]:
    """Compute ``(title_suffix, state_label, state_variant, verb)`` for a
    modify card's applied-state chrome (shared by the PO + MO modify cards).

    Delete reads "Deleted" / "deleted"; modify / correct read "Applied" /
    "applied". On the standalone-applied path (``is_preview=False``) the actual
    outcome overrides — a fully-failed apply reads "Failed" / FAILED /
    destructive, a partial reads "Partially Applied" / PARTIAL FAILURE /
    destructive — so the title + badge + footer verb never contradict the
    outcome. The in-place-morph path keeps the optimistic defaults (#760).
    """
    if verb_label == "Delete":
        title_suffix, state_label, verb = "Deleted", "DELETED", "deleted"
    else:
        title_suffix, state_label, verb = "Applied", "APPLIED", "applied"
    variant = "default"
    if not is_preview:
        outcome_label, outcome_variant = _summarize_apply_outcome(actions)
        if outcome_label != "APPLIED":
            state_label, variant = outcome_label, outcome_variant
            if outcome_label == "FAILED":
                title_suffix, verb = "Failed", "failed"
            else:  # PARTIAL FAILURE
                title_suffix, verb = "Partially Applied", "partially applied"
    return title_suffix, state_label, variant, verb


_PO_ROW_OP_NAMES = frozenset({"add_row", "update_row", "delete_row"})


def _po_modify_row_rows(
    prior_state: dict[str, Any] | None,
    actions: list[dict[str, Any]],
    *,
    extras: dict[str, Any],
) -> tuple[list[dict[str, Any]], str]:
    """Build the PO line-item diff rows + summary, short-circuiting when the
    plan has no row CRUD.

    A header-only / additional-cost-only modify never touches the rows, so we
    skip the merge entirely (no projection over a large PO's row snapshot) and
    return ``([], "")`` — the card then renders just the header diffs. Resolved
    SKU / name come from ``extras["resolved_variants"]`` (the impl's batched
    cache lookup); JSON re-stringifies the int keys, which
    :func:`_coerce_resolved_id_map` coerces back.
    """
    if not any(
        str(a.get("operation") or "").lower() in _PO_ROW_OP_NAMES for a in actions
    ):
        return [], ""
    resolved_variants = _coerce_resolved_id_map(extras.get("resolved_variants"))
    rows = prepare_po_row_table_rows(
        merge_po_row_rows_for_modify_card(prior_state, actions, resolved_variants)
    )
    return rows, collection_diff_summary(rows)


# DataTable columns for the PO modify card's line-item diff table. SKU carries
# the kind gutter (``+ ``/``- ``/``~ ``/``  ``); Status renders plain text
# (PLANNED / APPLIED / FAILED / NOT RUN). Mirrors the BOM / item variant tables.
_PO_MODIFY_ROW_COLUMNS: list[DataTableColumn] = [
    DataTableColumn(key="sku_label", header="SKU"),
    DataTableColumn(key="display_name", header="Item"),
    DataTableColumn(key="quantity_label", header="Qty", align="right", width="9rem"),
    DataTableColumn(
        key="price_label", header="Unit Price", align="right", width="11rem"
    ),
    DataTableColumn(key="status_label", header="Status", width="7rem"),
]
_PO_MODIFY_ROW_KEY = "po_row_rows"
_PO_MODIFY_ROW_REF = f"{{{{ {_PO_MODIFY_ROW_KEY} }}}}"


def build_po_modify_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the modify-/delete-/correct-purchase-order card.

    Handles every PO write path that returns a :class:`ModificationResponse`:
    ``modify_purchase_order``, ``delete_purchase_order``,
    ``correct_purchase_order``. Title verb derives from ``confirm_tool``
    via :func:`_verb_label` (``Modify`` / ``Delete`` / ``Correct``).

    Shares ``_render_po_entity_view`` with ``build_po_create_ui`` — the
    entity-view content (Tier 2 metrics + Tier 3 reference fields +
    warnings) is identical between the two surfaces. Modify cards pass
    a ``changes`` dict keyed by field name (flattened from every
    ``ActionResult.changes`` via :func:`_index_changes_by_field`); each
    field-level line looks up its wire-name and decorates with
    ``before → after`` plus a leading ``✗`` glyph + inline error on
    failed actions. The card-level state Badge in the header carries
    the all-applied / partial-failure / etc. status.

    Source of unchanged-field values: the response itself (which
    carries the post-change state when applied) supplemented by
    ``response["prior_state"]`` for any field absent from the top-level
    response payload (rare — `ModificationResponse` keeps the full
    pre-change snapshot for revert reference and for renderer use).
    """
    is_preview = bool(response.get("is_preview", True))
    # Apply path: extend with the unattempted plan tail (synthesized NOT-RUN
    # actions in ``extras``) so a fail-fast partial doesn't drop the not-run
    # row actions from the morphed line-item table. Inert on preview.
    actions = _actions_with_not_run_tail(response, is_preview=is_preview)
    entity_id = response.get("entity_id")
    # ``prior_state`` arrives in the wire shape from ``serialize_for_prior_state``
    # (``RegularPurchaseOrder.to_dict()`` etc.) — ``order_no``, ``total``,
    # ``additional_info``, nested ``supplier``, ``purchase_order_rows``.
    # Normalize to the response shape the entity-view renderer reads so
    # unchanged-field rows surface real values in the rendered card.
    raw_prior_state = response.get("prior_state")
    prior_state = _normalize_po_prior_state(raw_prior_state)
    # Apply path: the dispatcher stashes the post-modify header snapshot
    # (server-recomputed ``total`` and friends) under
    # ``extras["post_apply_state"]``. Normalize it the same way as
    # prior_state and overlay it below so the Total metric reflects the
    # *applied* PO, not the pre-modify snapshot. Empty on the preview path
    # (nothing applied yet) — the card then falls back to prior_state.
    post_apply_state = _normalize_po_prior_state(
        (response.get("extras") or {}).get("post_apply_state")
    )
    # Note: katana_url is read from RESULT via the Prefab template
    # ``{{ result.katana_url }}`` in _render_preview_footer's
    # applied-state View-in-Katana button — no need to pass it through
    # the Python layer here. ``response["katana_url"]`` is None on
    # successful delete (entity gone) which the template handles via
    # the If("result.katana_url") gate.

    verb_label = _verb_label(confirm_tool)
    # Compose the entity view's source-of-truth dict by overlaying the
    # response on top of the normalized prior_state. Preview: prior_state
    # is the full pre-change snapshot; response-level scalars (warnings,
    # katana_url) win. Applied: the response carries the post-change
    # scalars too — the same overlay yields the post-change entity,
    # modulo nested collections which the dispatcher already updated.
    entity = {
        **prior_state,
        **post_apply_state,
        **{k: v for k, v in response.items() if v is not None},
    }
    # ``entity_id`` from the response is the PO's identity; surface it
    # under the same key the create-card pattern uses so the header
    # Badge picks it up regardless of which payload populated it.
    if entity_id is not None:
        entity.setdefault("id", entity_id)

    # NOTE: in-place-morph apply-outcome rendering limitation (#760).
    # ``changes_by_field`` is computed ONCE at server build time from
    # ``response.actions``. On the preview→Confirm→apply path, the
    # response we build from has ``actions[*].succeeded=None`` (preview
    # state), so ``failed`` flags in the indexed view are all False —
    # even if the apply returns failures. After the iframe morphs
    # (``state.applied=True``, ``state.result=RESULT``), the entity
    # view's ✗ glyphs / consolidated failure Alert / header outcome
    # badge are static from the preview render and DON'T surface the
    # apply outcome. The agent's chat does (via ``UpdateContext`` push)
    # and the Confirm button morphs to Retry on error, but the card
    # body itself stays optimistic. Fixing this properly needs either
    # Prefab Rx-bound rendering of every field-level decision from
    # ``state.result.actions`` or a rebuild-on-morph primitive. Tracked
    # at #760 — see issue for design options.
    # Scope header field diffs to ``update_header`` so row / additional-cost
    # changes (which share field names like ``currency``) don't leak into the
    # header entity-view lines — they belong in the line-item table below.
    changes_by_field = _index_changes_by_field(
        actions, include_operations=frozenset({"update_header"})
    )

    # PO line-item diff table — the content-drop fix (#722 follow-up): the card
    # previously rendered header scalar diffs only and silently dropped every
    # row CRUD action. ``_po_modify_row_rows`` short-circuits to ``([], "")``
    # for header-only / additional-cost-only plans (no merge over a large PO's
    # rows). When the table renders, we seed ``state.po_row_rows`` + wire the
    # apply-morph SetState; otherwise neither, avoiding copying the row
    # snapshot into UI state for no benefit.
    po_row_rows, po_row_summary = _po_modify_row_rows(
        raw_prior_state, actions, extras=response.get("extras") or {}
    )
    show_row_table = bool(po_row_summary)

    apply_action = _build_apply_action(
        confirm_tool,
        confirm_request,
        # Morph the line-item table in place on apply — the apply rebuild seeds
        # ``state.po_row_rows`` with the merged-with-outcomes rows; this copies
        # them off the apply tool's envelope (``$result.state.<key>``). Only
        # wired when the table is rendered.
        extra_on_success=(
            [SetState(_PO_MODIFY_ROW_KEY, "{{ $result.state.po_row_rows }}")]
            if show_row_table
            else None
        ),
    )
    # ``_build_cancel_action`` interpolates its arg into "Cancel: do not
    # apply X.", so the noun phrase has to read naturally there. Verb
    # forms like ``"that purchase order modify"`` (the previous shape)
    # are grammatically awkward; map to noun-shaped phrases instead.
    if verb_label == "Delete":
        cancel_operation_label = "that purchase order deletion"
    elif verb_label == "Correct":
        cancel_operation_label = "those purchase order corrections"
    else:
        cancel_operation_label = "those purchase order changes"
    cancel_action = _build_cancel_action(cancel_operation_label)

    # State-badge label depends on the entry path: preview enters with
    # PREVIEW, standalone-applied (is_preview=False) enters with the
    # outcome summary, which we set as ``applied_state_label`` below.
    # The in-place morph flips applied=True via the rail's on_success;
    # the rendered state-badge in Tier 1 is the create-card-style
    # PREVIEW → APPLIED (or DELETED / FAILED / PARTIAL FAILURE) switch.

    state = _init_modify_card_state(response)
    if show_row_table:
        state[_PO_MODIFY_ROW_KEY] = po_row_rows

    with (
        PrefabApp(state=state, css_class="p-4") as app,
        Card(),
    ):
        (
            applied_title_suffix,
            applied_state_label,
            applied_state_variant,
            applied_verb,
        ) = _modify_applied_state_labels(
            verb_label, is_preview=is_preview, actions=actions
        )

        _render_preview_header(
            title_prefix=f"{verb_label} Purchase Order",
            entity="purchase_order",
            order_number=str(entity.get("order_number") or entity_id or "N/A"),
            status=entity.get("status"),
            applied_title_suffix=applied_title_suffix,
            applied_state_label=applied_state_label,
            applied_state_variant=applied_state_variant,
        )
        with CardContent(), Column(gap=3):
            if response.get("message"):
                Muted(content=response["message"])
            block_warnings = _render_po_entity_view(entity, changes=changes_by_field)
            # Line-item diff table — rendered only when the plan actually
            # changes a row (``po_row_summary`` is non-empty). A header-only /
            # additional-cost-only modify leaves the existing rows untouched,
            # so listing them here would be noise; the header diffs above
            # carry the change. The full merged list (existing + changed)
            # seeds ``state.po_row_rows`` so when the table shows, unchanged
            # rows provide context alongside the diffs (BOM-style), and the
            # per-row Status morphs in place on apply.
            if show_row_table:
                Separator()
                Muted(content="Line items:")
                Text(content=po_row_summary)
                DataTable(
                    columns=_PO_MODIFY_ROW_COLUMNS,
                    rows=_PO_MODIFY_ROW_REF,
                    **_paginate(len(po_row_rows)),
                )
        # Confirm label scales with the number of planned actions —
        # ``Confirm 4 changes`` is more informative than the generic
        # form. Delete cards say "Delete" not "Confirm" to mirror the
        # destructive-affordance pattern from the modification rail.
        n_actions = len(actions)
        if verb_label == "Delete":
            confirm_label = "Confirm Delete"
        elif n_actions > 1:
            confirm_label = f"Confirm {n_actions} changes"
        else:
            confirm_label = "Confirm Changes"
        _render_preview_footer(
            title_prefix=f"Purchase Order {verb_label}",
            block_warnings=block_warnings,
            confirm_label=confirm_label,
            apply_action=apply_action,
            cancel_action=cancel_action,
            # No next-action buttons on modify cards by default — the
            # user already had the PO they wanted to change; surfacing
            # "Receive Items" here would be noise. Delete operations
            # also have nothing useful to suggest (the PO is gone).
            next_action_buttons=(),
            applied_verb=applied_verb,
        )
    return app


# ============================================================================
# BOM modify card — table-as-entity-view variant of the modify-card family
# (#811). Unlike PO/SO/MO/etc. which modify scalar header fields, a BOM
# modify plan is N row creates / row updates / row deletes on a list. The
# entity view here IS the table — each plan action projects onto a row in
# the merged before-state + planned-changes view.
#
# The row-shaping + status-bucket helpers live in
# ``katana_mcp.tools.foundation.bom_table`` (extracted in #850 so the
# tool-impl path can precompute ``extras["applied_plan_rows"]`` without
# importing UI internals). Only the rendering glue stays here.
# ============================================================================


# DataTable columns for the BOM modify card. The Status column renders
# plain text (PLANNED / APPLIED / FAILED) — DataTable doesn't expose a
# Badge component per cell, so kind discrimination is carried by the
# SKU column's leading 2-char gutter (``+ ``/``- ``/``~ ``/``  ``) glued
# on in ``_prepare_bom_table_rows``. ``status_variant`` is still computed
# per merged row, but currently only consumed by the consolidated failure
# Alert (``_render_bom_failed_rows_block``), not the table itself.
_BOM_MODIFY_COLUMNS: list[DataTableColumn] = [
    DataTableColumn(key="rank_label", header="Rank", width="4rem"),
    DataTableColumn(key="sku_label", header="Ingredient SKU"),
    DataTableColumn(key="display_name", header="Display Name"),
    DataTableColumn(
        key="quantity_label", header="Quantity", align="right", width="9rem"
    ),
    DataTableColumn(key="notes_label", header="Notes"),
    DataTableColumn(key="status_label", header="Status", width="7rem"),
]

_BOM_MODIFY_PLAN_KEY = "plan_rows"
_BOM_MODIFY_PLAN_REF = f"{{{{ {_BOM_MODIFY_PLAN_KEY} }}}}"


def _resolve_bom_table_rows(
    *,
    is_preview: bool,
    prior_state: dict[str, Any] | None,
    actions: list[dict[str, Any]],
    resolved_ingredients: dict[int, dict[str, str | None]],
    extras: dict[str, Any],
) -> list[dict[str, Any]]:
    """Pick the right source for the BOM DataTable rows.

    On the apply path ``_modify_product_bom_impl`` already ran the same
    ``_merge → _prepare`` pipeline against the resolved actions and
    stuffed the result into ``extras["applied_plan_rows"]`` (also visible
    to the LLM via the response.content channel). Reuse it instead of
    recomputing — avoids drift between two computation paths.

    Preview path has no precomputed list, so fall back to local merge.
    Also fall back if the extras list is missing/malformed (defensive
    — shouldn't happen with the current impl but keeps the renderer
    robust to future schema changes).
    """
    extras_applied_plan_rows = extras.get("applied_plan_rows")
    if (
        not is_preview
        and isinstance(extras_applied_plan_rows, list)
        and all(isinstance(r, dict) for r in extras_applied_plan_rows)
    ):
        return extras_applied_plan_rows
    merged_rows = _merge_bom_rows_for_modify_card(
        prior_state, actions, resolved_ingredients
    )
    return _prepare_bom_table_rows(merged_rows)


def build_bom_modify_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the manage-product-BOM modify card (#811).

    Table-as-entity-view variant of the modify-card family (#721). Unlike
    PO/SO/MO/etc. which modify scalar header fields, a BOM modify plan is
    N row creates / updates / deletes on a list. The entity view IS the
    table — existing rows render unchanged, ``add_bom_row`` actions appear
    as new rows with an ``added`` kind, ``update_bom_row`` actions show
    the original row with diff-decorated quantity / notes / ingredient,
    and ``delete_bom_row`` actions render with a ``deleted`` kind.

    The pre-action BOM snapshot arrives in ``response["prior_state"]``
    (populated by ``_modify_product_bom_impl`` via ``existing_snapshot``).
    The ingredient SKU + display_name resolution for *added* rows comes
    from ``response["extras"]["resolved_ingredients"]`` — the impl batches
    a single cache lookup across every variant id touched by the plan,
    so the renderer reads the result without a second hit at build time.

    Four-tier structure (#537):

    - Tier 1 — Identity: product name (linked to Katana), variant SKU pill,
      UoM badge, state badge (PREVIEW / APPLIED / PARTIAL / FAILED).
    - Tier 2 — Decision metrics: ``+N added, ~M updated, -K deleted``
      summary line above the table.
    - Tier 3 — Reference: the diff-decorated DataTable.
    - Tier 4 — Actions: Confirm / Cancel (preview); applied-state footer
      (applied / failed / cancelled).
    """
    actions = response.get("actions") or []
    is_preview = bool(response.get("is_preview", True))
    prior_state: dict[str, Any] | None = response.get("prior_state")
    extras: dict[str, Any] = response.get("extras") or {}
    resolved_ingredients_raw = extras.get("resolved_ingredients") or {}
    # JSON keys arrive as strings (pydantic round-trips dict[int, Any] as
    # str keys on the wire); coerce back to int for in-Python lookup.
    resolved_ingredients: dict[int, dict[str, str | None]] = {}
    for key, value in resolved_ingredients_raw.items():
        try:
            int_key = int(key)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            resolved_ingredients[int_key] = {
                "sku": value.get("sku"),
                "display_name": value.get("display_name"),
            }

    table_rows = _resolve_bom_table_rows(
        is_preview=is_preview,
        prior_state=prior_state,
        actions=actions,
        resolved_ingredients=resolved_ingredients,
        extras=extras,
    )
    # ``collection_diff_summary`` reads ``kind`` per row which is preserved
    # through ``_prepare_bom_table_rows``, so it works against
    # table_rows directly.
    summary_line = collection_diff_summary(table_rows)

    # Header content — pulled from the prior_state snapshot (the wire
    # shape of ``GetProductBomResponse.model_dump()``, populated by
    # ``_modify_product_bom_impl``). Falls back gracefully when fetch
    # failed (prior_state is None).
    snapshot = prior_state or {}
    product_name = (
        snapshot.get("product_name")
        or snapshot.get("variant_display_name")
        or f"BOM for variant {response.get('entity_id')}"
    )
    variant_sku = snapshot.get("variant_sku")
    uom = snapshot.get("uom")
    katana_url = snapshot.get("katana_url")

    # Footer ``applied_verb`` is passed to ``_render_preview_footer`` as
    # a mustache template (``"{{ applied_verb }}"``); the underlying
    # ``Muted(content=f"{title_prefix} {applied_verb}.")`` then resolves
    # against ``state.applied_verb`` at iframe render time. This makes
    # the footer body morph in lockstep with the Tier-1 state Badge —
    # otherwise the build-time-fixed verb would read "BOM applied."
    # even when ``applied_outcome_label`` morphed to FAILED / PARTIAL
    # FAILURE on the preview iframe's in-place apply.

    n_actions = len(actions)
    confirm_label = (
        f"Confirm {n_actions} BOM change{'s' if n_actions != 1 else ''}"
        if n_actions
        else "Confirm Changes"
    )

    # The apply response (when the iframe re-issues with preview=false)
    # carries multiple precomputed extras the iframe needs to morph the
    # whole applied-state chrome, not just the table rows.
    #
    # Data flow:
    # 1. ``_modify_product_bom_impl`` (apply path) computes
    #    ``response.extras.applied_plan_rows``, ``applied_outcome_label``,
    #    ``applied_outcome_variant``, ``applied_failed_count``, and
    #    ``applied_failed_summary``.
    # 2. The apply-time call to ``build_bom_modify_ui`` seeds these
    #    values into its OWN ``state.*`` slots (see ``state[...]`` block
    #    below). So the apply card's PrefabApp envelope carries them in
    #    ``state``, NOT ``extras``.
    # 3. The preview iframe's ``on_success`` SetState chain reads
    #    ``{{ $result.state.<slot> }}`` and writes into the preview
    #    iframe's matching state slot, morphing the rendered chrome.
    #
    # Without the SetStates below the preview iframe would morph
    # ``state.applied=True`` but every other applied-state visual would
    # stay frozen at preview-time defaults:
    # - DataTable stuck on PLANNED rows.
    # - Header Badge stuck on "APPLIED" / default even when some or all
    #   actions failed.
    # - Failed-row Alert never rendered because the build-time guard
    #   was ``if not is_preview`` (which is False under the preview
    #   render). Now we render the Alert under ``If("applied")`` driven
    #   by ``state.applied_failed_count`` and its summary description.
    #
    # ``$result`` in the on_success Rx context resolves to the apply
    # tool's wire-shape ``structured_content`` — a PrefabApp envelope
    # keyed by ``$prefab`` / ``view`` / ``state``, NOT the raw
    # :class:`~katana_mcp.tools._modification.ModificationResponse`. Same
    # limitation documented in ``test_apply_button_morphs_card_to_applied_state``.
    # So we read from ``$result.state.<slot>`` — never ``$result.extras``,
    # which doesn't exist at the envelope's top level.
    apply_action = _build_apply_action(
        confirm_tool,
        confirm_request,
        extra_on_success=[
            SetState(_BOM_MODIFY_PLAN_KEY, "{{ $result.state.plan_rows }}"),
            SetState(
                "applied_outcome_label",
                "{{ $result.state.applied_outcome_label }}",
            ),
            SetState(
                "applied_outcome_variant",
                "{{ $result.state.applied_outcome_variant }}",
            ),
            SetState(
                "applied_failed_count",
                "{{ $result.state.applied_failed_count }}",
            ),
            SetState(
                "applied_failed_summary",
                "{{ $result.state.applied_failed_summary }}",
            ),
            SetState(
                "applied_verb",
                "{{ $result.state.applied_verb }}",
            ),
        ],
    )
    cancel_action = _build_cancel_action("those BOM changes")

    state = _init_modify_card_state(response)
    state[_BOM_MODIFY_PLAN_KEY] = table_rows
    # Seed the apply-outcome state slots with preview-time defaults so the
    # If-branches below render cleanly even before the apply lands. The
    # apply ``on_success`` chain overwrites these with the real outcome
    # values from ``$result.state.<slot>`` (read off the apply tool's
    # envelope — see the rationale on ``extra_on_success`` above).
    state["applied_outcome_label"] = (
        response.get("extras", {}).get("applied_outcome_label") or "APPLIED"
    )
    state["applied_outcome_variant"] = (
        response.get("extras", {}).get("applied_outcome_variant") or "default"
    )
    state["applied_failed_count"] = (
        response.get("extras", {}).get("applied_failed_count") or 0
    )
    state["applied_failed_summary"] = (
        response.get("extras", {}).get("applied_failed_summary") or ""
    )
    state["applied_verb"] = response.get("extras", {}).get("applied_verb") or "applied"

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        # Tier 1 — Identity header. Same shape as the read-side BOM card
        # (``_bom_header_section``): product name linked to Katana, SKU
        # pill, UoM badge, then the state badge so the modify-vs-preview
        # signal lives in the same visual slot as the other modify cards.
        #
        # The applied-state Badge fans out across three branches so the
        # variant tracks the outcome (default for success, destructive
        # for PARTIAL FAILURE / FAILED). Badge.variant isn't reactive on
        # its own — we render parallel components and let the If chain
        # pick the right one at morph time.
        with CardHeader(), Row(gap=2):
            with CardTitle():
                if katana_url:
                    Link(content=product_name, href=katana_url, target="_blank")
                else:
                    Text(content=product_name)
            if variant_sku:
                Badge(label=variant_sku, variant="outline")
            if uom:
                Badge(label=uom, variant="secondary")
            _render_apply_outcome_badge()

        # Tier 2 — Decision summary. Reads "+N added, ~M updated, -K
        # deleted" so the user knows the shape of the plan before
        # scanning the table.
        with CardContent(), Column(gap=3):
            if response.get("message"):
                Muted(content=response["message"])
            if summary_line:
                Text(content=summary_line)

            # Tier 3 — Diff-decorated table. Bound to ``state.plan_rows``
            # via mustache (the same contract every state-bound DataTable
            # in this module uses; bare-string refs crash the renderer).
            if table_rows:
                DataTable(
                    columns=_BOM_MODIFY_COLUMNS,
                    rows=_BOM_MODIFY_PLAN_REF,
                    **_paginate(len(table_rows)),
                )
            else:
                Muted(
                    content=(
                        "No rows in the BOM and no planned changes. "
                        "Provide add_bom_rows / update_bom_rows / "
                        "delete_bom_row_ids to manage the recipe."
                    )
                )

            block_warnings = _render_warnings_block(response.get("warnings"))

            # Consolidated failed-rows Alert — driven by state so the
            # preview iframe's in-place morph after Confirm can surface
            # failures (the previous ``if not is_preview`` guard was
            # build-time and stayed False through the morph). Pre-formatted
            # ``applied_failed_summary`` string seeded into the apply
            # card's ``state`` slot by the builder below; the morph picks
            # it up via SetState from ``$result.state.applied_failed_summary``.
            # Each line is ``Failed — <sku>: <error>``.
            with (
                If(Rx("applied_failed_count") > 0),
                Alert(variant="destructive", icon="circle-alert"),
            ):
                AlertTitle(content="{{ applied_failed_count }} failed row(s)")
                AlertDescription(content="{{ applied_failed_summary }}")

            if is_preview:
                with If("error"):
                    Separator()
                    with Alert(variant="destructive", icon="circle-alert"):
                        AlertTitle(content="Apply failed")
                        AlertDescription(content="{{ error }}")

        # Tier 4 — Footer. Reuse the shared preview-footer helper so the
        # apply/cancel/morph state machine and the next-action buttons
        # match the rest of the modify-card family. No next-action
        # buttons today — BOM operations don't have a deterministic
        # follow-up tool (the user already had the recipe they wanted to
        # change).
        _render_preview_footer(
            title_prefix="BOM",
            block_warnings=block_warnings,
            confirm_label=confirm_label,
            apply_action=apply_action,
            cancel_action=cancel_action,
            next_action_buttons=(),
            # Mustache template against ``state.applied_verb`` (seeded
            # above + overwritten by the on_success chain) so the footer
            # body morphs to "BOM partially applied." / "BOM failed." in
            # lockstep with the Tier-1 outcome Badge.
            applied_verb="{{ applied_verb }}",
        )
    return app


# ============================================================================
# Item modify / delete card (#726) — the second collection-bearing modify card
# (after BOM). Header scalar fields diff via the shared
# ``_render_item_entity_view`` overlay (#555); the variants collection diffs via
# the shared collection-diff table element (``item_variant_table`` →
# ``merge_collection_diff_rows``). Mirrors ``build_po_modify_ui`` for the
# preview→apply rail and ``build_bom_modify_ui`` for the diff-table morph.
# ============================================================================


# DataTable columns for the item modify card's variant diff table. The SKU
# column carries the kind gutter (``+ ``/``- ``/``~ ``/``  ``) glued on in
# ``prepare_variant_table_rows``; the Status column renders plain text
# (PLANNED / APPLIED / FAILED) since DataTable has no per-cell Badge.
_ITEM_MODIFY_VARIANT_COLUMNS: list[DataTableColumn] = [
    DataTableColumn(key="sku_label", header="SKU"),
    DataTableColumn(
        key="sales_price_label", header="Sales Price", align="right", width="11rem"
    ),
    DataTableColumn(
        key="purchase_price_label",
        header="Purchase Price",
        align="right",
        width="11rem",
    ),
    DataTableColumn(key="status_label", header="Status", width="7rem"),
]

_ITEM_MODIFY_VARIANT_KEY = "variant_rows"
_ITEM_MODIFY_VARIANT_REF = f"{{{{ {_ITEM_MODIFY_VARIANT_KEY} }}}}"


def _normalize_item_prior_state(prior_state: dict[str, Any] | None) -> dict[str, Any]:
    """Map an item ``prior_state`` snapshot (wire shape of
    ``Product`` / ``Material`` / ``Service`` ``.to_dict()``) to the shape the
    item entity-view renderer consumes.

    The attrs snapshot mostly shares field names with the render shape
    (``name`` / ``uom`` / ``category_name`` / ``additional_info`` /
    ``default_supplier_id`` / ``variants`` / ``configs`` / the status flags),
    so it passes through. The two derivations the renderer needs:

    - ``is_archived`` ← ``archived_at is not None`` (the snapshot carries the
      timestamp; the card renders a boolean badge).
    - ``default_supplier_name`` is *not* on the raw snapshot — only the FK is.
      ``_modify_item_impl`` resolves it server-side via the typed cache
      (anti-pattern #7) and stamps it onto ``prior_state`` before the response
      leaves the impl, so it's already present here when resolution succeeded.

    Returns ``{}`` for a missing snapshot (failed diff fetch) so the renderer
    falls back to whatever the response payload carries.
    """
    if not prior_state:
        return {}
    out = dict(prior_state)
    if "archived_at" in prior_state and "is_archived" not in out:
        out["is_archived"] = prior_state.get("archived_at") is not None
    return out


def _item_failed_summary(actions: list[dict[str, Any]]) -> str:
    """Pre-format the consolidated failed-action summary for the morph Alert.

    One ``Failed — <op> <target>: <error>`` line per failed action. Empty on
    preview (no action has ``succeeded is False`` yet) and on a clean apply.
    """
    lines: list[str] = []
    for a in actions:
        if a.get("succeeded") is not False:
            continue
        op = str(a.get("operation") or "change").replace("_", " ")
        target_id = a.get("target_id")
        label = f"{op} {target_id}" if target_id is not None else op
        err = a.get("error") or "unknown error"
        lines.append(f"Failed — {label}: {err}")
    return "\n".join(lines)


def _item_applied_verb(verb_label: str, outcome_label: str) -> str:
    """Footer verb for the applied state — tracks both the operation and the
    outcome so the copy never contradicts the Tier-1 badge.
    """
    if outcome_label == "FAILED":
        return "failed"
    if outcome_label == "PARTIAL FAILURE":
        return "partially applied"
    return "deleted" if verb_label == "Delete" else "applied"


def _item_modify_labels(verb_label: str, n_actions: int) -> tuple[str, str]:
    """Return ``(confirm_label, cancel_operation_label)`` for the item card.

    Delete cards say "Confirm Delete" + "that item deletion"; modify cards
    scale the confirm label with the action count and read "those item
    changes" for the cancel phrasing.
    """
    if verb_label == "Delete":
        return "Confirm Delete", "that item deletion"
    confirm = f"Confirm {n_actions} changes" if n_actions > 1 else "Confirm Changes"
    return confirm, "those item changes"


def _render_item_modify_header(entity: dict[str, Any], *, entity_id: Any) -> None:
    """Render the item modify card's Tier-1 header.

    Item name (linked to Katana when a URL is present), the sub-type badge,
    an archived badge, then the reactive PREVIEW → outcome state badge; the
    sub-type status-pills row follows (shared with the create / detail cards).
    Must be called inside ``with PrefabApp(...) as app, Card():``.
    """
    katana_url = entity.get("katana_url")
    title_content = entity.get("name") or f"Item {entity_id}"
    item_type = entity.get("type")
    with CardHeader(), Column(gap=2):
        with Row(gap=2):
            with CardTitle():
                if katana_url:
                    Link(content=title_content, href=katana_url, target="_blank")
                else:
                    Text(content=title_content)
            if item_type:
                Badge(label=str(item_type), variant="secondary")
            if entity.get("is_archived"):
                Badge(label="Archived", variant="secondary")
            _render_apply_outcome_badge()
        _item_status_pills_row(entity)


def build_item_modify_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the modify-/delete-item card (#726).

    Handles every item write path that returns a :class:`ModificationResponse`:
    ``modify_item`` (header + variant CRUD) and ``delete_item``. Sub-type
    variance (product / material / service) shows in the type badge + status
    pills; the variant diff table renders only for product / material (services
    carry pricing on the header, not on variants).

    Two diff surfaces, both from the shared modify-card machinery:

    - **Header scalars** — ``_render_item_entity_view`` with the per-field
      ``changes`` overlay (built from the ``update_header`` action's
      ``changes`` via :func:`_index_changes_by_field`, scoped to that
      operation so variant-field diffs don't leak into header lines).
    - **Variants collection** — the shared collection-diff table
      (:func:`merge_variant_rows_for_modify_card`): existing variants render
      plain, ``add_variant`` rows append with a ``+ `` gutter, ``update_variant``
      rows show before→after on SKU / prices, ``delete_variant`` rows mark
      ``- ``. The table is state-bound (``state.variant_rows``) and morphs in
      place on apply via the SetState chain reading ``$result.state.variant_rows``.

    The preview→Confirm→apply rail mirrors ``build_po_modify_ui`` /
    ``build_bom_modify_ui``: a build-time ``summarize_apply_outcome`` seeds the
    outcome label/variant/failed-summary state slots (preview-time defaults on
    the preview render; real outcome on the apply rebuild), and the apply
    ``on_success`` chain copies them from ``$result.state.<slot>`` so the whole
    applied-state chrome morphs in lockstep. Inherits the #760 in-place-morph
    optimism for per-field ``✗`` glyphs (build-time-fixed from the preview
    actions); the table rows + header/footer outcome chrome do morph.
    """
    is_preview = bool(response.get("is_preview", True))
    # Apply path: extend with the unattempted plan tail (synthesized NOT-RUN
    # actions in ``extras``) so a fail-fast partial doesn't silently drop the
    # not-run variant rows from the morphed table. Inert on preview.
    actions = _actions_with_not_run_tail(response, is_preview=is_preview)
    entity_id = response.get("entity_id")
    entity_type = response.get("entity_type")
    verb_label = _verb_label(confirm_tool)

    prior_state = _normalize_item_prior_state(response.get("prior_state"))
    # Compose the entity-view source: prior_state (full pre-change snapshot)
    # overlaid with non-None response scalars (katana_url, warnings). Same
    # overlay shape as ``build_po_modify_ui``.
    entity = {**prior_state, **{k: v for k, v in response.items() if v is not None}}
    if entity_id is not None:
        entity.setdefault("id", entity_id)
    # Raw ``Product``/``Material``/``Service`` snapshots have no ``type`` echo
    # the header badge can read; seed it from the response's entity_type.
    if entity_type:
        entity.setdefault("type", entity_type)

    # Header field diffs — scope to ``update_header`` so variant-field changes
    # (sku / sales_price / lead_time / MOQ, which overlap header-ish names)
    # never decorate the header lines; they belong in the variant table.
    changes_by_field = _index_changes_by_field(
        actions, include_operations=frozenset({"update_header"})
    )

    # Variant diff table — product / material only (services have no variant
    # CRUD; their pricing diffs surface on the header lines instead).
    show_variant_table = entity_type in ("product", "material")
    variant_rows = (
        prepare_variant_table_rows(
            merge_variant_rows_for_modify_card(prior_state, actions)
        )
        if show_variant_table
        else []
    )
    summary_line = collection_diff_summary(variant_rows)

    # Outcome chrome. On the standalone-applied path and the apply rebuild the
    # actions carry real succeeded flags, so ``summarize_apply_outcome`` gives
    # the true label; on the preview render every action is ``succeeded=None``
    # (which ``summarize_apply_outcome`` can't bucket), so seed the optimistic
    # ``APPLIED`` default — the Tier-1 badge shows PREVIEW until the morph
    # overwrites these slots from ``$result.state.<slot>`` anyway.
    if is_preview:
        outcome_label, outcome_variant = "APPLIED", "default"
    else:
        outcome_label, outcome_variant = _summarize_apply_outcome(actions)
    applied_verb = _item_applied_verb(verb_label, outcome_label)
    failed_summary = _item_failed_summary(actions)
    failed_count = sum(1 for a in actions if a.get("succeeded") is False)

    apply_action = _build_apply_action(
        confirm_tool,
        confirm_request,
        extra_on_success=[
            SetState(_ITEM_MODIFY_VARIANT_KEY, "{{ $result.state.variant_rows }}"),
            SetState(
                "applied_outcome_label", "{{ $result.state.applied_outcome_label }}"
            ),
            SetState(
                "applied_outcome_variant",
                "{{ $result.state.applied_outcome_variant }}",
            ),
            SetState(
                "applied_failed_count", "{{ $result.state.applied_failed_count }}"
            ),
            SetState(
                "applied_failed_summary",
                "{{ $result.state.applied_failed_summary }}",
            ),
            SetState("applied_verb", "{{ $result.state.applied_verb }}"),
        ],
    )
    confirm_label, cancel_operation_label = _item_modify_labels(
        verb_label, len(actions)
    )
    cancel_action = _build_cancel_action(cancel_operation_label)

    state = _init_modify_card_state(response)
    state[_ITEM_MODIFY_VARIANT_KEY] = variant_rows
    state["applied_outcome_label"] = outcome_label
    state["applied_outcome_variant"] = outcome_variant
    state["applied_failed_count"] = failed_count
    state["applied_failed_summary"] = failed_summary
    state["applied_verb"] = applied_verb

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        _render_item_modify_header(entity, entity_id=entity_id)

        with CardContent(), Column(gap=3):
            if response.get("message"):
                Muted(content=response["message"])

            # Tier 2 + 3 — header metrics + reference fields with diff overlay.
            # Variants suppressed here; the diff table below replaces them.
            block_warnings = _render_item_entity_view(
                entity, changes=changes_by_field, suppress_variants=True
            )

            # Variant diff table (product / material). Summary line first so
            # the user sees "+N ~M -K" before scanning the rows.
            if show_variant_table:
                if summary_line:
                    Text(content=summary_line)
                if variant_rows:
                    DataTable(
                        columns=_ITEM_MODIFY_VARIANT_COLUMNS,
                        rows=_ITEM_MODIFY_VARIANT_REF,
                        **_paginate(len(variant_rows)),
                    )

            # Consolidated failed-rows Alert — state-driven so the in-place
            # morph after Confirm surfaces failures (mirrors the BOM card).
            with (
                If(Rx("applied_failed_count") > 0),
                Alert(variant="destructive", icon="circle-alert"),
            ):
                AlertTitle(content="{{ applied_failed_count }} failed action(s)")
                AlertDescription(content="{{ applied_failed_summary }}")

            if is_preview:
                with If("error"):
                    Separator()
                    with Alert(variant="destructive", icon="circle-alert"):
                        AlertTitle(content="Apply failed")
                        AlertDescription(content="{{ error }}")

        # Tier 4 — Footer. Shared apply/cancel/morph rail. No next-action
        # buttons (the user already had the item they wanted to change; a
        # deleted item has nothing useful to suggest).
        _render_preview_footer(
            title_prefix=f"Item {verb_label}",
            block_warnings=block_warnings,
            confirm_label=confirm_label,
            apply_action=apply_action,
            cancel_action=cancel_action,
            next_action_buttons=(),
            applied_verb="{{ applied_verb }}",
        )
    return app


def _render_so_shipping_fees_section(
    outcomes: list[dict[str, Any]],
    *,
    is_preview: bool,
    currency: str | None,
) -> None:
    """Render the inline shipping-fees sub-section for ``build_so_create_ui``.

    Layout:
    - Section header with a Separator + ``Shipping fees`` muted label
      (collapses fee block into a clearly demarcated Tier-3 sub-section).
    - Preview rows (and apply rows still pending) — ``  description:
      amount`` (formatted via :func:`_format_money` with the SO currency),
      tax_rate_id when present. Leading 2-char gutter reserves space so an
      applied-state morph to ``✗`` doesn't reflow the row horizontally.
    - Applied / success rows — same row text plus an ``APPLIED`` status
      Badge (variant=default).
    - Applied / failure rows — ``✗ `` glyph prefix on the row text plus a
      ``FAILED`` Badge (variant=destructive); the per-row error message
      tails the row text. When at least one fee failed, a destructive
      Alert below the section coaches the operator toward retrying via
      ``modify_sales_order(id=<so_id>, add_shipping_fees=[...])``.
    - No fees: caller skips this helper entirely.

    The ``✗`` failure glyph matches the convention from
    :func:`_render_field_diff_line` (failure-row prefix; non-failed rows
    reserve the 2-char gutter). The per-row ``APPLIED`` / ``FAILED`` Badge
    is *additional* to that convention — diff lines on scalar-field modify
    cards omit it because the card-header Badge already carries the signal,
    but the shipping-fees section is a list of multiple parallel outcomes
    so each one needs its own status pill.

    Monetary totals accumulate via :class:`~decimal.Decimal` for the same
    reason the rest of this codebase uses Decimal for sums — float
    addition can drift on common shipping amounts (``0.1 + 0.2`` etc.).
    """
    if not outcomes:
        return

    Separator()
    Muted(content="Shipping fees:")

    failed_outcomes: list[dict[str, Any]] = []
    # Two running totals because preview vs. apply have different "what's
    # in the total" semantics:
    # - Preview: ``planned_total`` = sum of every parseable fee. There's
    #   no succeeded info yet; the total represents what the user will
    #   be charged if everything attaches.
    # - Apply: ``succeeded_total`` = sum of fees that actually landed.
    #   Summing failed fees too would misrepresent the SO's final state
    #   — "$30 total" when only $20 attached is a wrong number, not a
    #   "planned" number. Render rule below switches between them.
    planned_total = Decimal("0")
    planned_parseable_count = 0
    succeeded_total = Decimal("0")
    succeeded_parseable_count = 0
    succeeded_count = 0

    for outcome in outcomes:
        description = outcome.get("description") or "Shipping fee"
        amount_str = outcome.get("amount")
        tax_rate_id = outcome.get("tax_rate_id")
        succeeded = outcome.get("succeeded")
        error = outcome.get("error")
        created_id = outcome.get("created_id")

        if succeeded is True:
            succeeded_count += 1

        # Parse the wire-shape decimal string into Decimal once so both
        # the per-row label and the running totals format from the same
        # exact value — passing ``float(amount_str)`` to ``_format_money``
        # would defeat the Decimal accumulation by reintroducing binary-
        # representation drift in the per-row text (and the totals then
        # disagree with the sum-of-displayed-rows the user can mentally
        # verify).
        #
        # ``Decimal("NaN")`` / ``Decimal("Infinity")`` parse without
        # raising but pollute the totals (NaN + Decimal → NaN) and would
        # render as a garbage formatted-money string. Guard with
        # ``is_finite()`` so non-finite values fall through to the
        # raw-string label and are excluded from both totals. The
        # validator emits BLOCK warnings for these on the request side,
        # so they only reach the renderer when an agent bypassed preview
        # — defensive belt + suspenders.
        amount_dec: Decimal | None = None
        if amount_str is not None:
            try:
                parsed = Decimal(str(amount_str))
            except (TypeError, ValueError, InvalidOperation):
                parsed = None
            if parsed is not None and parsed.is_finite():
                amount_dec = parsed
                planned_total += amount_dec
                planned_parseable_count += 1
                if succeeded is True:
                    succeeded_total += amount_dec
                    succeeded_parseable_count += 1
        amount_label = (
            _format_money(amount_dec, currency)
            if amount_dec is not None
            else (str(amount_str) if amount_str is not None else "—")
        )

        tax_suffix = f" · tax rate #{tax_rate_id}" if tax_rate_id is not None else ""

        if is_preview:
            # Preview row: leading 2-char gutter matches the diff-line
            # convention so an applied-state morph would shift to ``✗``
            # without reflowing the row text horizontally.
            Text(content=f"  {description}: {amount_label}{tax_suffix}")
            continue

        if succeeded is None:
            # Apply path with an outcome not yet resolved (defensive — the
            # apply pipeline always sets succeeded True/False before
            # returning, but the renderer shouldn't crash on a partially
            # populated outcome dict).
            Text(content=f"  {description}: {amount_label}{tax_suffix}")
            continue

        if succeeded is True:
            id_suffix = f" (id={created_id})" if created_id is not None else ""
            with Row(gap=2):
                Text(content=f"  {description}: {amount_label}{tax_suffix}{id_suffix}")
                Badge(label="APPLIED", variant="default")
        else:
            failed_outcomes.append(outcome)
            error_suffix = f" — {error}" if error else ""
            with Row(gap=2):
                Text(
                    content=f"✗ {description}: {amount_label}{tax_suffix}{error_suffix}"
                )
                Badge(label="FAILED", variant="destructive")

    # Render the running total. Three rules cover the cases:
    #
    # 1. *Preview* / no apply outcomes yet — show the planned total when
    #    every fee parsed. A partial parse-sum would be misleading
    #    (BLOCK warnings surface the unparseable rows separately;
    #    showing "Total shipping: $X · 3 fee(s)" when only 2 of the 3
    #    amounts contributed implies the plan totals to $X — it doesn't).
    #
    # 2. *Apply, all succeeded* — same shape as preview but the
    #    counter reads "applied" so the user knows the SO actually
    #    carries this total.
    #
    # 3. *Apply, partial failure* — show ONLY the succeeded subset so
    #    the number reflects what landed on the SO. Showing the planned
    #    total would misrepresent the SO's actual state ("$30 total"
    #    when only $20 attached is a wrong number, not a "planned"
    #    number). Label calls out the M-of-N shape explicitly.
    #
    # Pass Decimal directly to ``_format_money`` so the formatted total
    # stays exact (no float-conversion rounding drift between the per-row
    # labels and the total).
    n_outcomes = len(outcomes)
    failed_count = len(failed_outcomes)
    if is_preview or failed_count == 0:
        # Preview path or all-succeeded apply path: show planned/applied
        # total when every parseable.
        if planned_parseable_count and planned_parseable_count == n_outcomes:
            total_label = _format_money(planned_total, currency)
            counter = (
                f"{n_outcomes} fee(s)" if is_preview else f"{n_outcomes} fee(s) applied"
            )
            Muted(content=f"  Total shipping: {total_label} · {counter}")
    elif succeeded_count and succeeded_parseable_count == succeeded_count:
        # Partial failure: show only the succeeded subset, labeled
        # explicitly so the user doesn't confuse it with the requested
        # total. Skip entirely if no succeeded amounts parsed (rare).
        total_label = _format_money(succeeded_total, currency)
        Muted(
            content=(
                f"  Total shipping applied: {total_label} · "
                f"{succeeded_count} of {n_outcomes} fee(s) applied"
            )
        )

    if failed_outcomes and not is_preview:
        with Alert(variant="destructive", icon="circle-alert"):
            n = len(failed_outcomes)
            AlertTitle(
                content=(
                    f"{n} of {len(outcomes)} shipping fee(s) failed — "
                    f"sales order itself was created"
                )
            )
            AlertDescription(
                content=(
                    "Retry the failed fees via "
                    "modify_sales_order(id=<so_id>, add_shipping_fees=[...]) — "
                    "the SO ID is shown above. Each failed fee preserves its "
                    "description / amount / tax_rate_id in the row above so "
                    "you can copy them straight into the modify call."
                )
            )


def _so_shipping_fees_apply_state(
    outcomes: list[dict[str, Any]],
    *,
    so_id: int | None = None,
) -> dict[str, Any]:
    """Pre-compute the apply-outcome state slots for the SO shipping
    fees section so the preview→Confirm in-place morph can surface the
    actual result.

    The build-time ``_render_so_shipping_fees_section`` paints rows
    once at preview time and won't repaint on morph (Python-time
    ``is_preview`` stays True under the iframe's morphed state). We
    instead bind a state-driven ``If("applied")`` summary block to
    these slots; the preview-side ``on_success`` chain SetStates them
    from ``$result.state.*`` after the apply lands.

    Why state slots + ``$result.state.*`` references and not
    ``$result.<field>`` directly: ``$result`` in the on_success Rx
    context resolves to the apply tool's wire-shape ``structured_content``
    — a PrefabApp envelope keyed by ``$prefab`` / ``view`` / ``state``,
    NOT the raw ``SalesOrderResponse``. So the apply-time builder seeds
    these slots into its own ``state.*``, and the preview iframe reads
    off ``$result.state.*`` to morph (documented in
    ``test_apply_button_morphs_card_to_applied_state``).

    Returns a dict with:
    - ``applied_fees_summary`` — operator-facing one-liner.
    - ``applied_fees_failed_count`` — int gating the failed-fees Alert.
    - ``applied_fees_failed_summary`` — pre-formatted multi-line string
      with ``Failed — <description>: <error>`` per failed fee, then a
      retry-coaching line referencing the SO id so the operator knows
      how to recover. The build-time
      :func:`_render_so_shipping_fees_section` Alert carries the same
      coaching but doesn't morph; embedding it here means the
      preview→Confirm morph keeps the recovery instructions visible.
    """
    total = len(outcomes)
    succeeded = sum(1 for o in outcomes if o.get("succeeded") is True)
    failed_outcomes = [o for o in outcomes if o.get("succeeded") is False]
    failed = len(failed_outcomes)
    if total == 0 or (succeeded == 0 and failed == 0):
        # Preview path or no fees — empty summary; the If("applied")
        # gating + If(Rx("applied_fees_failed_count") > 0) gating keep
        # the block hidden until the apply lands.
        return {
            "applied_fees_summary": "",
            "applied_fees_failed_count": 0,
            "applied_fees_failed_summary": "",
        }
    if failed == 0:
        summary = f"All {total} shipping fee(s) applied successfully."
    elif succeeded == 0:
        summary = f"0 of {total} shipping fee(s) applied — every fee failed."
    else:
        summary = f"{succeeded} of {total} shipping fee(s) applied — {failed} failed."
    failed_lines: list[str] = []
    for o in failed_outcomes:
        desc = o.get("description") or "Shipping fee"
        err = o.get("error") or "unknown error"
        failed_lines.append(f"Failed — {desc}: {err}")
    if failed_lines:
        # Retry coaching — referencing the literal SO id so the operator
        # can copy/paste the modify call without bouncing through the
        # response object. ``so_id is None`` falls back to a placeholder
        # since the preview path doesn't have an SO yet (and won't have
        # failed fees either, so the path is unreachable in practice).
        so_ref = str(so_id) if so_id is not None else "<so_id>"
        failed_lines.append("")
        failed_lines.append(
            f"Retry the failed fee(s) via modify_sales_order(id={so_ref}, "
            f"add_shipping_fees=[...]). Each failed row above preserves its "
            f"description / amount / tax_rate_id — copy them straight in."
        )
    return {
        "applied_fees_summary": summary,
        "applied_fees_failed_count": failed,
        "applied_fees_failed_summary": "\n".join(failed_lines),
    }


def build_so_create_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the create-sales-order card. Handles both preview and
    applied states (see ``build_po_create_ui`` for the dual-state shape).
    Reads ``SalesOrderResponse.model_dump()`` directly.

    Four-tier content:
    - Tier 1: title, order_number, PREVIEW/CREATED, status (variant from
      ``status_badge_variant("sales_order", status)``).
    - Tier 2: Total, Line Items, Delivery date.
    - Tier 3: customer, location (ID-only — SO response has no
      ``location_name``), inline shipping-fees sub-section (#818) when
      ``shipping_fee_outcomes`` is non-empty, warnings, state-driven
      apply-outcome summary block (visible after morph).
    - Tier 4: Confirm/Cancel (preview) or View in Katana + Fulfill Order
      (applied).

    Shipping fees (#818): the apply path creates the SO first, then
    fires ``POST /sales_order_shipping_fee`` per fee. The card surfaces
    each planned fee at preview time. After Confirm the iframe's
    in-place morph reveals an ``If("applied")``-gated state-driven
    summary block (per-fee badges still don't morph — the Python tree
    is paint-once — but the operator-facing summary + failed-fee retry
    coaching DO morph correctly via SetState from ``$result.state.*``).
    """
    order_number = response.get("order_number") or "N/A"
    status = response.get("status")
    total = response.get("total")
    currency = response.get("currency")
    item_count = response.get("item_count")
    delivery_date = response.get("delivery_date")
    is_preview = bool(response.get("is_preview", True))
    shipping_fee_outcomes: list[dict[str, Any]] = (
        response.get("shipping_fee_outcomes") or []
    )
    # Pass ``so_id`` so the apply-time failed-fees summary can embed the
    # exact ``modify_sales_order(id=…, add_shipping_fees=[…])`` call for
    # retry. On preview the response has no ``id`` yet (the SO isn't
    # created) — falls back to ``<so_id>`` placeholder text, which is
    # only reachable if there are also failed fees (impossible on the
    # preview path).
    applied_fees_state = _so_shipping_fees_apply_state(
        shipping_fee_outcomes,
        so_id=response.get("id"),
    )

    # The apply response's PrefabApp envelope carries these slots in
    # ``state`` (initialized below); the preview iframe's on_success
    # chain reads ``$result.state.*`` to morph the summary block.
    apply_action = _build_apply_action(
        confirm_tool,
        confirm_request,
        extra_on_success=[
            SetState(
                "applied_fees_summary",
                "{{ $result.state.applied_fees_summary }}",
            ),
            SetState(
                "applied_fees_failed_count",
                "{{ $result.state.applied_fees_failed_count }}",
            ),
            SetState(
                "applied_fees_failed_summary",
                "{{ $result.state.applied_fees_failed_summary }}",
            ),
        ],
    )
    cancel_action = _build_cancel_action("that sales order")

    state = _init_create_card_state(response)
    state.update(applied_fees_state)

    with (
        PrefabApp(state=state, css_class="p-4") as app,
        Card(),
    ):
        _render_preview_header(
            title_prefix="Sales Order",
            entity="sales_order",
            order_number=order_number,
            status=status,
        )
        with CardContent(), Column(gap=3):
            if total is not None or item_count is not None or delivery_date:
                with Row(gap=4):
                    if total is not None:
                        Metric(label="Total", value=_format_money(total, currency))
                    if item_count is not None:
                        Metric(label="Line Items", value=str(item_count))
                    if delivery_date:
                        Metric(label="Delivery", value=str(delivery_date))
            _render_party_line(
                "Customer",
                name=response.get("customer_name"),
                entity_id=response.get("customer_id"),
                entity_kind="customer",
            )
            _render_party_line(
                "Location",
                name=response.get("location_name"),
                entity_id=response.get("location_id"),
            )
            _render_so_shipping_fees_section(
                shipping_fee_outcomes,
                is_preview=is_preview,
                currency=currency,
            )

            # State-driven apply-outcome surface — visible after the
            # in-place morph (the per-row badges painted by
            # ``_render_so_shipping_fees_section`` above don't morph
            # because they're built at Python time; the summary line
            # + failed-fee Alert below DO morph via SetState).
            with If("applied"):
                Muted(content="{{ applied_fees_summary }}")
                with (
                    If(Rx("applied_fees_failed_count") > 0),
                    Alert(variant="destructive", icon="circle-alert"),
                ):
                    AlertTitle(
                        content=(
                            "{{ applied_fees_failed_count }} shipping fee(s) "
                            "failed — sales order itself was created"
                        )
                    )
                    AlertDescription(content="{{ applied_fees_failed_summary }}")

            block_warnings = _render_warnings_block(response.get("warnings"))
        _render_preview_footer(
            title_prefix="Sales Order",
            block_warnings=block_warnings,
            confirm_label="Confirm & Create Sales Order",
            apply_action=apply_action,
            cancel_action=cancel_action,
            next_action_buttons=(
                # Fulfill takes order_id + order_type, both knowable from
                # the create response, so it's a deterministic CallTool.
                # ``{{ result.id }}`` resolves against state.result at
                # render time.
                (
                    "Fulfill Order",
                    CallTool(
                        "fulfill_order",
                        arguments={
                            "order_id": "{{ result.id }}",
                            "order_type": "sales",
                            "preview": True,
                        },
                    ),
                ),
            ),
        )
    return app


# ============================================================================
# Sales-order modify card — diff-decorated SO modify/delete/correct card
# (#723). Reuses ``_render_field_diff_line`` / ``_render_party_diff_line``
# from the PO modify card, but intentionally does NOT call
# ``_render_failed_changes_block`` — all header-failure rendering is
# routed through the state-driven ``applied_header_failed_*`` Alert (seeded
# by :func:`_so_header_op_failure_alert_text`) so the preview→Confirm
# in-place morph has a single source of truth. Adds dedicated sub-sections
# for SO's parallel-outcome sub-entities (rows, addresses, fulfillments,
# shipping fees). Each sub-section follows the BOM modify card's
# table-as-entity-view pattern adapted to a per-section row list with
# per-action status pills.
# ============================================================================


# Wire field → user-facing label map for the consolidated failed-changes
# Alert. Reads "Failed — Customer: 422 Bad Request" instead of the wire-
# name "Failed — customer_id: ...". Keys cover every SOHeaderPatch field
# the API can produce a FieldChange for; missing keys fall through to
# a Title-cased version of the wire name inside
# :func:`_so_header_op_failure_alert_text`.
_SO_HEADER_LABEL_OVERRIDES: dict[str, str] = {
    "customer_id": "Customer",
    "customer_name": "Customer",
    "location_id": "Location",
    "location_name": "Location",
    "additional_info": "Notes",
    "notes": "Notes",
    "order_no": "Order #",
    "order_number": "Order #",
    "delivery_date": "Delivery date",
    "picked_date": "Picked date",
    "order_created_date": "Order created date",
    "currency": "Currency",
    "conversion_rate": "Conversion rate",
    "conversion_date": "Conversion date",
    "customer_ref": "Customer ref",
    "tracking_number": "Tracking #",
    "tracking_number_url": "Tracking URL",
    "status": "Status",
}


def _normalize_so_prior_state(prior_state: dict[str, Any] | None) -> dict[str, Any]:
    """Map an SO ``prior_state`` snapshot from the wire shape produced by
    ``SalesOrder.to_dict()`` (server-side) to the response shape
    :func:`_render_so_entity_view` consumes.

    Field renames between the wire snapshot and the response shape:

    - ``order_no`` (wire) → ``order_number`` (response shape; SO create
      response surfaces it under ``order_number``).
    - ``additional_info`` (wire) → also kept under ``notes`` so the
      renderer can read either key.

    Derived metrics:

    - ``item_count`` — :class:`ModificationResponse` doesn't carry
      ``item_count`` (only :class:`SalesOrderResponse` does), so the
      modify card's Tier-2 "Line Items" Metric would render blank on a
      real apply response. Derive it from ``len(prior_state["sales_order_rows"])``
      when ``item_count`` is missing so the Metric renders consistently
      across the create and modify cards (#858 Copilot finding —
      comment 3313163122).

    SO's wire snapshot does NOT carry a nested ``customer`` object the way
    PO carries ``supplier``; it only has ``customer_id``. The
    ``customer_name`` lookup the response shape may surface is added by
    upstream cache-merge; if the snapshot doesn't have it, the renderer
    falls back to ``#<id>``.

    Without this adapter the modify card renders mostly-empty header rows
    in production: ``entity.get("order_number")`` falls through to ``None``
    because the wire-shape snapshot only has ``order_no``. Same shape-
    mismatch bug Copilot caught on PO #755.
    """
    if not prior_state:
        return {}
    out = dict(prior_state)
    if "order_no" in prior_state and "order_number" not in out:
        out["order_number"] = prior_state["order_no"]
    if "additional_info" in prior_state and "notes" not in out:
        out["notes"] = prior_state["additional_info"]
    if "item_count" not in out:
        rows = prior_state.get("sales_order_rows")
        if isinstance(rows, list):
            out["item_count"] = len(rows)
    return out


def _so_change_new(changes: list[Any], field: str) -> Any:
    """Pluck the ``new`` value for ``field`` from an action's changes list,
    or ``None`` if the field isn't present. Helper for the SO sub-entity
    summary formatters."""
    for c in changes:
        if isinstance(c, dict) and c.get("field") == field:
            return c.get("new")
    return None


def _format_so_diff_pairs(
    changes: list[Any],
    *,
    address_style: bool = False,
) -> list[str]:
    """Format an action's changes list into ``field: before → after`` (or
    ``field: (prior unknown) → after``) strings.

    Used by the ``update_*`` formatters across rows / addresses /
    fulfillments / shipping fees. ``address_style=True`` skips the diff
    arrow and renders only the after value — address updates always
    carry ``is_unknown_prior=True`` (no per-address GET), so the
    arrow form would always read ``(prior unknown) → new``; collapsing
    to the bare ``field: new`` form keeps the summary line compact.
    """
    diffs: list[str] = []
    for c in changes:
        if not isinstance(c, dict):
            continue
        field = c.get("field")
        if not isinstance(field, str):
            continue
        new = c.get("new")
        if address_style:
            diffs.append(f"{field}: {_format_diff_value(new)}")
            continue
        old = c.get("old")
        unknown_prior = bool(c.get("is_unknown_prior"))
        after = _format_diff_value(new)
        if unknown_prior:
            diffs.append(f"{field}: (prior unknown) → {after}")
        else:
            diffs.append(f"{field}: {_format_diff_value(old)} → {after}")
    return diffs


def _so_anchor_with_diffs(
    *,
    kind: str,
    target_id: Any,
    diffs: list[str],
) -> str:
    """Compose ``<kind> #<target_id> — <diff>, <diff>`` (or the bare
    anchor when no diffs are present). Shared anchor-builder for the
    SO ``update_*`` / ``delete_*`` summary formatters.
    """
    anchor = f"{kind} #{target_id}" if target_id is not None else kind
    if diffs:
        return f"{anchor} — {', '.join(diffs)}"
    return anchor


def _format_so_add_row(changes: list[Any]) -> str:
    """One-line summary for an ``add_row`` action."""
    variant_id = _so_change_new(changes, "variant_id")
    quantity = _so_change_new(changes, "quantity")
    bits: list[str] = []
    if variant_id is not None:
        bits.append(f"variant {variant_id}")
    if quantity is not None:
        bits.append(f"qty {quantity}")
    return ", ".join(bits) or "new line item"


def _format_so_add_address(changes: list[Any]) -> str:
    """One-line summary for an ``add_address`` action."""
    entity_type = _so_change_new(changes, "entity_type") or "address"
    city = _so_change_new(changes, "city")
    zip_ = _so_change_new(changes, "zip")
    bits: list[str] = []
    if city:
        bits.append(str(city))
    if zip_:
        bits.append(str(zip_))
    return f"{entity_type}: {', '.join(bits)}" if bits else str(entity_type)


def _format_so_add_fulfillment(changes: list[Any]) -> str:
    """One-line summary for an ``add_fulfillment`` action.

    Labels are field-specific — ``status`` and ``picked_date`` get their
    own ``status <value>`` / ``picked <value>`` prefixes so the rendered
    summary doesn't read ``status 2026-05-08T14:30:00Z`` when only the
    pick timestamp is supplied (the old first-truthy fallback conflated
    the two and surfaced a timestamp under the ``status`` label).
    """
    status = _so_change_new(changes, "status")
    picked = _so_change_new(changes, "picked_date")
    tracking = _so_change_new(changes, "tracking_number")
    bits: list[str] = []
    if status:
        bits.append(f"status {status}")
    if picked:
        bits.append(f"picked {picked}")
    if tracking:
        bits.append(f"tracking {tracking}")
    return ", ".join(bits) or "new fulfillment"


def _format_so_add_shipping_fee(changes: list[Any]) -> str:
    """One-line summary for an ``add_shipping_fee`` action."""
    description = _so_change_new(changes, "description") or "shipping fee"
    amount = _so_change_new(changes, "amount")
    if amount is not None:
        return f"{description}: {amount}"
    return str(description)


# Dispatch table for ``add_*`` summaries — keeps the main formatter
# under ruff's complexity budget. ``update_*`` and ``delete_*`` ops use
# the shared :func:`_so_anchor_with_diffs` helper so they don't need
# per-kind entries.
_SO_ADD_FORMATTERS: dict[str, Callable[[list[Any]], str]] = {
    "add_row": _format_so_add_row,
    "add_address": _format_so_add_address,
    "add_fulfillment": _format_so_add_fulfillment,
    "add_shipping_fee": _format_so_add_shipping_fee,
}


# Map of ``update_*`` / ``delete_*`` op → (kind label, address_style).
# ``address_style`` flips the diff renderer to the unknown-prior-friendly
# bare-after form for address updates.
_SO_KIND_FOR_OP: dict[str, tuple[str, bool]] = {
    "update_row": ("row", False),
    "delete_row": ("row", False),
    "update_address": ("address", True),
    "delete_address": ("address", False),
    "update_fulfillment": ("fulfillment", False),
    "delete_fulfillment": ("fulfillment", False),
    "update_shipping_fee": ("shipping fee", False),
    "delete_shipping_fee": ("shipping fee", False),
}


def _format_so_action_summary(action: dict[str, Any]) -> str:
    """Build a one-line label summarizing an SO sub-entity action.

    Picks the most identifying field from the action's changes to anchor
    the line — e.g. ``variant_id`` for row adds, ``id`` (target_id) for
    row updates, etc. Falls back to ``target_id`` (the wire row UUID/id)
    when no obvious anchor field is present, then to a generic counter.

    Dispatched via two tables:

    - :data:`_SO_ADD_FORMATTERS` handles ``add_*`` ops (each kind has its
      own identifying fields — variant_id+quantity, city+zip, etc.).
    - :data:`_SO_KIND_FOR_OP` covers ``update_*`` / ``delete_*`` via the
      shared anchor builder. ``update_address`` uses the
      ``address_style=True`` path because Katana has no per-address GET,
      so every diff carries ``is_unknown_prior=True`` and the bare-after
      form reads better than ``(prior unknown) → X`` per field.

    The output is the *body* of the per-action row text — callers prefix
    it with the kind gutter (``+ `` / ``~ `` / ``- ``).
    """
    op = str(action.get("operation") or "").lower()
    target_id = action.get("target_id")
    changes = action.get("changes") or []

    if op in _SO_ADD_FORMATTERS:
        return _SO_ADD_FORMATTERS[op](changes)

    if op in _SO_KIND_FOR_OP:
        kind, address_style = _SO_KIND_FOR_OP[op]
        if op.startswith("delete_"):
            # Delete summaries are just the anchor — no field diffs to
            # surface (the action carries empty ``changes``; the kind
            # gutter already signals the removal).
            return _so_anchor_with_diffs(kind=kind, target_id=target_id, diffs=[])
        diffs = _format_so_diff_pairs(changes, address_style=address_style)
        return _so_anchor_with_diffs(kind=kind, target_id=target_id, diffs=diffs)

    # Fallback — operation name + target_id when nothing else fits.
    if target_id is not None:
        return f"{op} #{target_id}"
    return op or "(action)"


# Per-sub-entity ``operation`` prefix for grouping actions into sections.
# Section headers read "Line items", "Addresses", "Fulfillments", "Shipping
# fees" so the modify card scans naturally; the grouping is keyed off the
# wire ``operation`` enum so future schema additions land in a sensible
# bucket without renderer churn.
_SO_SUBENTITY_GROUPS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "rows",
        "Line items",
        ("add_row", "update_row", "delete_row"),
    ),
    (
        "addresses",
        "Addresses",
        ("add_address", "update_address", "delete_address"),
    ),
    (
        "fulfillments",
        "Fulfillments",
        ("add_fulfillment", "update_fulfillment", "delete_fulfillment"),
    ),
    (
        "shipping_fees",
        "Shipping fees",
        ("add_shipping_fee", "update_shipping_fee", "delete_shipping_fee"),
    ),
)


# Derived set of every operation that belongs to a sub-entity row group.
# Used by :func:`_so_subentity_failed_summary` to gate the sub-entity Alert
# on operations that actually render in the sub-entity sections —
# ``update_header`` / ``delete_sales_order`` failures are surfaced by the
# state-driven ``applied_header_failed_*`` Alert (seeded by
# :func:`_so_header_op_failure_alert_text`) instead, so including them in
# the sub-entity Alert would double-render the same error.
_SO_SUBENTITY_OPS: frozenset[str] = frozenset(
    op for _key, _label, ops in _SO_SUBENTITY_GROUPS for op in ops
)


# Header-level operations for the SO modify card. Used to filter
# :func:`_index_changes_by_field` so the header-field scalar-diff
# rendering doesn't pick up sub-entity field changes (sub-entity actions
# for fulfillments / rows / shipping fees can carry field names like
# ``status``, ``picked_date``, ``tracking_number``, ``description``,
# ``amount``, ``quantity`` that overlap or look-like header names —
# flattening them into the header map would render a stale
# "Status: PACKED → DELIVERED" header diff driven by a fulfillment
# update).
#
# ``delete`` is the top-level SO delete operation emitted by
# ``delete_sales_order``; ``update_header`` covers ``modify_sales_order``
# header writes and the header-touching legs of ``correct_sales_order``.
_SO_HEADER_OPS: frozenset[str] = frozenset({"update_header", "delete"})


def _so_action_kind_gutter(operation: str) -> str:
    """Return the 2-char gutter prefix for an SO sub-entity action.

    Mirrors the BOM modify card's ``status_prefix`` convention: adds get
    ``+ ``, updates ``~ ``, deletes ``- ``. The leading 2 chars reserve
    visual space so a status-pill morph doesn't reflow the row.
    """
    if operation.startswith("add_"):
        return "+ "
    if operation.startswith("update_"):
        return "~ "
    if operation.startswith("delete_"):
        return "- "
    return "  "


def _build_so_subentity_row(action: dict[str, Any]) -> dict[str, Any]:
    """Project one sub-entity action onto the DataTable row-dict shape
    consumed by the state-bound table (see :func:`_render_so_subentity_section`).

    Columnar since #721 Phase 3: each row is a cell dict keyed to
    :data:`_SO_SUBENTITY_COLUMNS`. The rows are state-bound (``DataTable
    rows="{{ so_<section>_rows }}"``) so the preview→Confirm apply-time
    morph swaps in a new row list via ``SetState`` from
    ``$result.state.so_<section>_rows`` and the Status column re-paints in
    lockstep with the apply outcome — the same contract every other modify
    card's diff table uses.

    Schema:

    - ``gutter_summary`` — ``"<gutter><summary>"`` (the "Change" column).
      The 2-char gutter encodes both kind (``+ ``/``~ ``/``- ``) and outcome
      (``✗ `` when failed), mirroring the kind-prefix every other card puts
      on its key column.
    - ``status_label`` — ``"PLANNED" / "APPLIED" / "FAILED" / "NOT RUN"``
      or ``""`` when unknown (the "Status" column). Bucketed via
      :func:`_derive_status_label`. Unlike the prior line-list, PLANNED
      renders in the Status column at preview time — consistent with the
      BOM/PO/MO/item diff tables (the card-level Badge no longer needs to
      be the sole planned-state signal). DataTable cells can't carry the
      colored per-row Badge the line-list used; the kind gutter + text
      Status column carry the signal (#721 Phase 3 tradeoff).

    Shared between preview-time row seeding and apply-time row recompute
    so the wire shape matches across the morph.
    """
    op = str(action.get("operation") or "").lower()
    gutter = _so_action_kind_gutter(op)
    succeeded = action.get("succeeded")
    # Failed actions get the failure glyph in the gutter slot (replacing
    # the +/~/- kind glyph) so the failure is at-a-glance visible. The
    # kind is still readable from the section header + the diff body.
    if succeeded is False:
        gutter = "✗ "
    summary = _format_so_action_summary(action)
    status_label = action.get("status_label") or _derive_status_label(action) or ""
    return {
        "gutter_summary": f"{gutter}{summary}",
        "status_label": status_label,
    }


def _build_so_subentity_row_lists(
    actions: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Bucket SO actions into per-section row-dict lists keyed by the
    :data:`_SO_SUBENTITY_GROUPS` section key (``rows`` / ``addresses`` /
    ``fulfillments`` / ``shipping_fees``).

    Threads :func:`_build_so_subentity_row` over each action and groups
    by operation prefix. Used by :func:`build_so_modify_ui` to seed
    ``state.so_<section>_rows`` slots at build time; the apply-time call
    recomputes against the apply response's actions, and the on_success
    ``SetState`` chain reads ``{{ $result.state.so_<section>_rows }}``
    so the preview iframe morphs each section's rows in lockstep with
    the apply outcome.

    The returned dict always contains all four section keys (empty list
    when the section had no actions) so the renderer can bind
    unconditionally without ``None``-guards.
    """
    by_section: dict[str, list[dict[str, Any]]] = {
        section_key: [] for section_key, _label, _ops in _SO_SUBENTITY_GROUPS
    }
    for action in actions:
        op = str(action.get("operation") or "").lower()
        for section_key, _label, section_ops in _SO_SUBENTITY_GROUPS:
            if op in section_ops:
                by_section[section_key].append(_build_so_subentity_row(action))
                break
    return by_section


# Columns for the SO sub-entity diff tables (#721 Phase 3). The kind-
# prefixed free-text "Change" summary plus a text Status column — the same
# two-axis shape (what-changed + outcome) every other modify card's diff
# table uses. DataTable cells can't carry the colored per-row Badge the
# old line-list rendered, so Status is plain text; the gutter glyph
# (``+``/``~``/``-``/``✗``) carries the kind + failure signal.
_SO_SUBENTITY_COLUMNS: list[DataTableColumn] = [
    DataTableColumn(key="gutter_summary", header="Change"),
    DataTableColumn(key="status_label", header="Status", width="7rem"),
]


def _render_so_subentity_section(
    section_label: str,
    section_key: str,
    actions: list[dict[str, Any]],
) -> None:
    """Render one sub-entity action section (Line items / Addresses /
    Fulfillments / Shipping fees) inside the SO modify card body.

    Columnar since #721 Phase 3 — a state-bound ``DataTable`` (rows
    ``"{{ so_<section_key>_rows }}"``) replaces the prior ``ForEach``
    line-list, so every modify card renders its collection diffs through
    the same widget. The state binding preserves the preview→Confirm
    in-place morph: the on_success ``SetState`` chain overwrites
    ``so_<section_key>_rows`` from ``$result.state.so_<section_key>_rows``
    so the Status column re-paints from the apply outcome (#858 finding A
    contract, unchanged).

    Each row lives in ``state.so_<section_key>_rows[i]`` as a cell dict
    (see :func:`_build_so_subentity_row`): a kind-prefixed ``gutter_summary``
    "Change" cell + a text ``status_label``. The per-row colored Badge the
    line-list carried is gone (DataTable cells can't hold one) — the gutter
    glyph + Status column carry the signal (#721 Phase 3 tradeoff).

    The failed-row error message is NOT rendered in the table — it
    aggregates into the consolidated state-driven Alert via
    :func:`_so_subentity_failed_summary` (sub-entity ops) and (for
    header-level ops) :func:`_so_header_op_failure_alert_text`.

    The ``actions`` arg only gates whether the section renders (an empty
    plan section stays absent so the card doesn't paint a "Fulfillments:"
    header + empty table). The row content itself comes from state, not
    from ``actions`` at render time.

    Called inside ``CardContent`` → ``Column(gap=3)``.
    """
    if not actions:
        return

    Separator()
    Muted(content=f"{section_label}:")
    # State-bound rows — the same slot the on_success chain writes from
    # ``$result.state.so_<section>_rows``, so the Status column morphs
    # in-place when the apply lands. Mustache form is mandatory for
    # state-bound DataTable rows (bare strings crash the JS renderer).
    # ``len(actions)`` is the build-time row count for this section (one row
    # per action, including any synthesized NOT-RUN tail) — routed through
    # ``_paginate`` so a short section doesn't render blank filler rows.
    DataTable(
        columns=_SO_SUBENTITY_COLUMNS,
        rows=f"{{{{ so_{section_key}_rows }}}}",
        **_paginate(len(actions)),
    )


def _so_subentity_failed_summary(
    actions: list[dict[str, Any]],
    *,
    so_id: int | None,
    confirm_tool: str | None = None,
) -> tuple[int, str]:
    """Pre-format the consolidated sub-entity failed-action summary text.

    Walks the applied actions, picks the ones with ``succeeded is False``,
    and emits one ``Failed — <op> #<target>: <error>`` line each. Returns
    ``(failed_count, summary_lines_joined)``.

    The retry-coaching tail mirrors the SO create card's shipping-fees
    summary (#818): tells the operator how to re-run the failed sub-
    entity operations through the same tool they invoked. The recovery
    tool is derived from ``confirm_tool`` so that a partial failure on
    ``correct_sales_order`` doesn't misdirect the operator to
    ``modify_sales_order`` (#858 review follow-up). ``delete_sales_order``
    is atomic and shouldn't reach this code path, but if it ever does
    we fall back to a generic "Retry the failed action(s)" phrasing.

    Used to seed ``state.applied_subentity_failed_count`` /
    ``state.applied_subentity_failed_summary`` so the in-place morph
    after Confirm can surface failures (the per-action DataTable rows
    above carry the ✗ gutter + FAILED Status cell, but the textual error
    messages aggregate into the morph-bound Alert below).

    Filters to operations in :data:`_SO_SUBENTITY_OPS` only — a failed
    ``update_header`` or top-level ``delete`` would otherwise render in
    BOTH this sub-entity Alert and the state-driven
    ``applied_header_failed_*`` Alert (seeded by
    :func:`_so_header_op_failure_alert_text`), double-surfacing the same
    error under a misleading "sub-entity failure(s)" title.
    """
    failed = [
        a
        for a in actions
        if a.get("succeeded") is False
        and str(a.get("operation") or "").lower() in _SO_SUBENTITY_OPS
    ]
    if not failed:
        return 0, ""
    lines: list[str] = []
    for action in failed:
        op = str(action.get("operation") or "(action)")
        target = action.get("target_id")
        error = action.get("error") or "unknown error"
        anchor = f"{op} #{target}" if target is not None else op
        lines.append(f"Failed — {anchor}: {error}")
    if so_id is not None:
        retry_tool = _so_retry_tool_for(confirm_tool)
        lines.append("")
        if retry_tool is not None:
            lines.append(
                f"Retry the failed action(s) via {retry_tool}(id={so_id}, "
                "<sub-payload>=[...]). The original request kwargs are still "
                "valid — re-supply only the failed entries."
            )
        else:
            lines.append(
                "Retry the failed action(s) by re-issuing the original "
                "request with only the failed entries."
            )
    return len(failed), "\n".join(lines)


# Maps the SO write tool the operator invoked to the tool they should
# re-issue to recover from a partial sub-entity failure. ``correct_*``
# corrections must round-trip back through ``correct_sales_order`` —
# the partial-failure rows belong to the correction plan, not to a
# regular modify, and the two paths have different downstream side
# effects (correction emits a different audit trail). ``delete_*`` is
# atomic; it shouldn't reach the sub-entity failure code path, but if
# it ever does we drop the tool-specific phrasing rather than misdirect.
_SO_RETRY_TOOLS: dict[str, str] = {
    "modify_sales_order": "modify_sales_order",
    "correct_sales_order": "correct_sales_order",
}


def _so_retry_tool_for(confirm_tool: str | None) -> str | None:
    """Return the tool name to suggest in the sub-entity retry tail.

    Returns ``None`` when ``confirm_tool`` doesn't have a meaningful
    retry path (e.g. ``delete_sales_order``, or an unrecognized tool).
    Callers fall back to a generic phrasing in that case.
    """
    if confirm_tool is None:
        return None
    return _SO_RETRY_TOOLS.get(confirm_tool)


# Verb labels for the header-level op failure Alert. Keeps the user-facing
# language ("Failed to delete the sales order: <error>") aligned with the
# tool the operator called; "modify" is the catch-all for the
# update_header leg (used by both ``modify_sales_order`` and the
# header-touching legs of ``correct_sales_order``).
_SO_HEADER_OP_VERBS: dict[str, str] = {
    "delete": "delete the sales order",
    "update_header": "modify the sales order header",
}


def _so_header_op_failure_alert_text(
    actions: list[dict[str, Any]],
) -> tuple[int, str]:
    """Pre-format the consolidated header-level failed-op summary text.

    Walks the applied actions, picks the ones with ``succeeded is False``
    AND whose operation is in :data:`_SO_HEADER_OPS`. This is the
    state-driven Alert that fires on the preview→Confirm morph path
    (gated by ``If(Rx("applied_header_failed_count") > 0)``); it owns
    every header-op failure surface so the build-time-only
    :func:`_render_failed_changes_block` doesn't need to be called from
    the SO entity view at all (avoids double-rendering and prevents the
    morph path's stale build-time block from misrepresenting the apply
    outcome — #858 finding C).

    Two failure shapes:

    - **No-change ops** (``delete``; ``update_header`` with no fields):
      one ``"Failed to <verb>: <error>"`` line per failed op.
    - **update_header with field changes**: one ``"Failed to <verb>:
      <error>"`` action-level line PLUS one ``"Failed — <Field>:
      <field_error>"`` line per changed field carrying a per-field
      error. The action-level error already covers the canonical
      Katana 4xx for a header PATCH (a single error for the whole
      PATCH), but Katana occasionally returns per-field
      ``validation_errors`` on a 422 — surface those when present so
      the operator sees which field failed validation. Pre-fix #858
      finding C: failed ``update_header`` actions WITH changes morphed
      to ``applied=True`` with neither the ✗ gutter nor the field-
      level error visible because the build-time
      ``_render_failed_changes_block`` was painted from preview
      actions (``succeeded=None``) and stayed at "no failures" after
      the morph.

    Returns ``(failure_count, alert_text)``. The alert text reads as
    ``"Failed to <verb>: <error>"`` one line per failed op; the empty
    string when no header ops failed (the Alert is gated by
    ``If(Rx("applied_header_failed_count") > 0)``).
    """
    failed = [
        a
        for a in actions
        if a.get("succeeded") is False
        and str(a.get("operation") or "").lower() in _SO_HEADER_OPS
    ]
    if not failed:
        return 0, ""
    lines: list[str] = []
    for action in failed:
        op = str(action.get("operation") or "").lower()
        verb = _SO_HEADER_OP_VERBS.get(op, op or "(action)")
        error = action.get("error") or "unknown error"
        lines.append(f"Failed to {verb}: {error}")
        # Per-field errors (rare — Katana usually returns a single
        # error string on header PATCHes; this picks up the
        # ``validation_errors``-style cases).
        for change in action.get("changes") or []:
            field_error = change.get("error") if isinstance(change, dict) else None
            if not field_error:
                continue
            field_name = (
                change.get("field") if isinstance(change, dict) else None
            ) or "(field)"
            label = _SO_HEADER_LABEL_OVERRIDES.get(
                field_name, field_name.replace("_", " ").title()
            )
            lines.append(f"Failed — {label}: {field_error}")
    return len(failed), "\n".join(lines)


def _so_header_op_skipped_alert_text(
    actions: list[dict[str, Any]],
) -> tuple[int, str]:
    """Pre-format the consolidated header-level NOT-RUN summary text.

    Walks the merged action list (executed + synthesized NOT-RUN tail, see
    :func:`_actions_with_not_run_tail`), picks the ones whose
    ``status_label == "NOT RUN"`` AND whose operation is in
    :data:`_SO_HEADER_OPS`. Emits one ``"Step skipped: <verb> (NOT RUN —
    earlier phase failed before this step ran)."`` line per skipped op.

    Mirrors :func:`_so_header_op_failure_alert_text`'s shape so the
    state-driven Alert pattern is symmetric (failed / skipped). Header
    NOT-RUN actions have no other rendering surface today:
    :func:`_index_changes_by_field` filters them out (last-write-wins
    would let a skipped close-phase update_header overwrite the executed
    revert-phase update_header diff — #858 round 7), and
    :func:`_build_so_subentity_row_lists` only buckets sub-entity ops
    (rows / addresses / fulfillments / shipping fees). Without this
    helper a failed ``correct_sales_order`` whose close-phase
    ``update_header`` is skipped renders only sub-entity NOT-RUN rows —
    the operator can't tell the SO close/restore step never ran. Round-8
    follow-up to #858, restoring the option-(B) surface the round-6
    reviewer originally suggested.

    Returns ``(skipped_count, alert_text)``. Empty string when no header
    ops were skipped — the Alert is gated by
    ``If(Rx("applied_header_skipped_count") > 0)`` so it stays hidden in
    that case.
    """
    skipped = [
        a
        for a in actions
        if str(a.get("status_label") or "") == "NOT RUN"
        and str(a.get("operation") or "").lower() in _SO_HEADER_OPS
    ]
    if not skipped:
        return 0, ""
    lines: list[str] = []
    for action in skipped:
        op = str(action.get("operation") or "").lower()
        verb = _SO_HEADER_OP_VERBS.get(op, op or "(action)")
        lines.append(
            f"Step skipped: {verb} "
            "(NOT RUN — earlier phase failed before this step ran)."
        )
    return len(skipped), "\n".join(lines)


# Header scalar field-spec: (label, change-key fallbacks, value-key
# fallbacks, render_when_unchanged). When ``render_when_unchanged`` is
# True the field renders even with no change present, as long as the
# entity carries a truthy value for it — keeps the card showing
# meaningful context (Notes, Tracking #) without padding it with empty
# "Delivery date: (unset)" lines for fields the user isn't modifying.
#
# A field appears at most once per render: the first change-key that
# resolves wins, and the first value-key that resolves wins. Fall-back
# chains exist because ``additional_info`` (wire) and ``notes``
# (response shape) both alias to the same display label, and
# ``order_no`` / ``order_number`` likewise. Picking the right value-key
# matters for unchanged fields — both lookups are nearly free, so a
# fall-back chain is cheaper than a normalization pass.
_SO_HEADER_FIELD_SPEC: tuple[
    tuple[str, tuple[str, ...], tuple[str, ...], bool], ...
] = (
    ("Notes", ("additional_info", "notes"), ("notes", "additional_info"), True),
    ("Delivery date", ("delivery_date",), (), False),
    ("Picked date", ("picked_date",), (), False),
    ("Order created date", ("order_created_date",), (), False),
    ("Currency", ("currency",), (), False),
    # ``conversion_rate`` / ``conversion_date`` are SOHeaderPatch fields but
    # they don't surface a steady-state value worth rendering on every card
    # (Katana's SO response shape doesn't include them on read), so
    # ``render_when_unchanged=False`` — they only appear in the diff body
    # when the user is actively patching them. Pre-fix #858 finding A:
    # omitting them from the spec meant a header-only conversion-rate /
    # conversion-date update rendered NO diff lines on the card.
    ("Conversion rate", ("conversion_rate",), (), False),
    ("Conversion date", ("conversion_date",), (), False),
    ("Customer ref", ("customer_ref",), ("customer_ref",), True),
    ("Tracking #", ("tracking_number",), ("tracking_number",), True),
    ("Tracking URL", ("tracking_number_url",), (), False),
    ("Order #", ("order_no", "order_number"), (), False),
    ("Status", ("status",), (), False),
)


def _render_so_header_scalar_diffs(
    entity: dict[str, Any],
    changes: dict[str, FieldChangeView],
) -> None:
    """Walk :data:`_SO_HEADER_FIELD_SPEC` and emit a field-diff line per
    entry that has either a present change or a truthy unchanged value.

    Each spec row reads ``(label, change_keys, value_keys, render_when_unchanged)``:

    - ``label`` is the user-facing field name.
    - ``change_keys`` is the ordered candidates for ``changes.get(...)`` —
      first non-None wins. Lets Notes pick up either ``additional_info``
      (wire) or ``notes`` (response shape) without two separate lookups.
    - ``value_keys`` is the ordered candidates for the unchanged-value
      fall-back; empty tuple means "no fallback — only render on change".
    - ``render_when_unchanged`` gates rendering of fields that should
      surface their current value even when not part of the modify plan
      (Notes, Customer ref, Tracking #).

    Extracted from :func:`_render_so_entity_view` to keep the main entity
    view under ruff's complexity budget. The table-driven shape is also
    cheaper to evolve as Katana adds new header fields — add a tuple,
    no branch.
    """
    for label, change_keys, value_keys, render_unchanged in _SO_HEADER_FIELD_SPEC:
        change: FieldChangeView | None = None
        for key in change_keys:
            candidate = changes.get(key)
            if candidate is not None:
                change = candidate
                break
        value: Any = None
        if render_unchanged:
            for key in value_keys:
                candidate_value = entity.get(key)
                if candidate_value:
                    value = candidate_value
                    break
        if change is None and value is None:
            continue
        _render_field_diff_line(label, value=value, change=change)


def _render_so_entity_view(
    entity: dict[str, Any],
    *,
    actions: list[dict[str, Any]],
    changes: dict[str, FieldChangeView] | None = None,
) -> list[str]:
    """Render the sales-order entity view (Tier 2 metrics + Tier 3
    reference fields + per-sub-entity action sections + warnings).

    Companion to :func:`_render_po_entity_view` for the SO modify card.
    Unlike the PO entity view which is shared with ``build_po_create_ui``,
    the SO create card today uses a tighter inline shape (no notes /
    delivery-date diff lines, dedicated shipping-fees section). This
    helper is modify-specific — create cards keep their existing inline
    rendering until/unless a future consolidation pass merges them.

    Diff-decoration rules (when ``changes`` is set, same as PO):

    - Each rendered field line looks up ``changes.get("<wire_field>")``
      and, if present, swaps its rendering for the before→after form.
    - Unchanged fields render the same as the create card.
    - Sub-entity actions (rows / addresses / fulfillments / shipping fees)
      render grouped by section under their own labelled header, each
      action becoming one summary line with kind gutter + per-action
      status Badge (applied path only).

    Returns the block-warning list so callers can gate the Confirm
    button. Must be called inside
    ``with PrefabApp(...) as app, Card(): with CardContent(), Column(gap=3):``.
    """
    changes = changes or {}
    total = entity.get("total")
    currency = entity.get("currency")
    item_count = entity.get("item_count")
    delivery_date = entity.get("delivery_date")

    # Tier 2 — Decision metrics (un-decorated; the per-field rows below
    # carry the diff signal for changed scalars).
    if total is not None or item_count is not None or delivery_date:
        with Row(gap=4):
            if total is not None:
                Metric(label="Total", value=_format_money(total, currency))
            if item_count is not None:
                Metric(label="Line Items", value=str(item_count))
            if delivery_date:
                Metric(label="Delivery", value=str(delivery_date))

    # Tier 3 — Reference fields. Customer + Location handled as party
    # lines; everything else via the shared field-diff helper.
    customer_change = changes.get("customer_id")
    prior_customer_name = entity.get("customer_name")
    if customer_change is not None and customer_change.kind != "unchanged":
        _render_party_diff_line(
            "Customer",
            id_change=customer_change,
            name_change=changes.get("customer_name"),
            prior_name=prior_customer_name,
        )
    else:
        _render_party_line(
            "Customer",
            name=prior_customer_name,
            entity_id=entity.get("customer_id"),
            entity_kind="customer",
        )

    location_change = changes.get("location_id")
    prior_location_name = entity.get("location_name")
    if location_change is not None and location_change.kind != "unchanged":
        _render_party_diff_line(
            "Location",
            id_change=location_change,
            name_change=changes.get("location_name"),
            prior_name=prior_location_name,
        )
    else:
        # SalesOrderResponse has no location_name today — pass None for
        # the name; ``_render_party_line`` falls back to the ID-only
        # form.
        _render_party_line(
            "Location",
            name=prior_location_name,
            entity_id=entity.get("location_id"),
        )

    # Storefront deep-link — when the SO came from a native ecommerce
    # integration (Shopify / WooCommerce / BigCommerce). No-op otherwise.
    _render_ecommerce_link(entity)

    # Header scalar diffs — driven by ``_SO_HEADER_FIELD_SPEC``. Each
    # entry maps a user-facing label to (change-key candidates,
    # entity-value keys, render_value_when_unchanged). The renderer
    # emits the diff line only when the field is changing OR carries a
    # value worth showing (so the card stays compact on a small modify
    # plan but still surfaces unchanged context for the long-form
    # update).
    _render_so_header_scalar_diffs(entity, changes)

    # Per-sub-entity sections — Line items / Addresses / Fulfillments /
    # Shipping fees. Each group reads the operation prefix off the
    # action's ``operation`` field and renders the section only when
    # actions of that kind are present. The section's rows render from
    # ``state.so_<section_key>_rows`` (state-bound ``DataTable``) so
    # the preview→Confirm morph re-paints the Status column — see
    # :func:`_render_so_subentity_section`.
    for section_key, label, ops in _SO_SUBENTITY_GROUPS:
        section_actions = [
            a for a in actions if str(a.get("operation") or "").lower() in ops
        ]
        _render_so_subentity_section(label, section_key, section_actions)

    # NOTE: SO has no build-time ``_render_failed_changes_block`` call.
    # The state-driven ``applied_header_failed_*`` Alert (seeded by
    # :func:`_so_header_op_failure_alert_text`) is the single source of
    # truth for every header-op failure — no-change ops AND update_header
    # with field changes — so both the preview→Confirm morph path and the
    # standalone-applied path render the failure exactly once, from state.
    # Pre-fix #858 finding C: the build-time block was painted from
    # preview actions (``succeeded=None``) and stayed at "no failures"
    # after the morph, leaving a failed ``update_header`` with changes
    # rendering ``applied=True`` chrome with no error text. Sub-entity
    # failures still aggregate into their own state-driven Alert (see
    # ``build_so_modify_ui``).

    return _render_warnings_block(entity.get("warnings"))


# State slots the SO modify card's apply on_success chain must propagate
# from ``$result.state.*`` (the apply tool's PrefabApp envelope) into the
# preview iframe's matching slots so the preview→Confirm in-place morph
# re-paints from the apply outcome. Centralized here so adding a new
# state slot (e.g. ``applied_header_skipped_*`` in #858 round-8) is a
# one-line edit rather than three concurrent edits across seed, render,
# and morph-chain sites. The ``so_*_rows`` slots drive the per-sub-entity
# section ``DataTable`` rows; everything else drives state-bound Badge /
# Alert / mustache strings.
_SO_MODIFY_MORPH_STATE_SLOTS: tuple[str, ...] = (
    "applied_outcome_label",
    "applied_outcome_variant",
    "applied_subentity_failed_count",
    "applied_subentity_failed_summary",
    "applied_header_failed_count",
    "applied_header_failed_summary",
    "applied_header_skipped_count",
    "applied_header_skipped_summary",
    "so_rows_rows",
    "so_addresses_rows",
    "so_fulfillments_rows",
    "so_shipping_fees_rows",
    "applied_verb",
)


def _so_modify_morph_setstate_chain() -> list[Action]:
    """Build the ``on_success`` SetState chain that morphs the preview
    iframe's state slots from the apply tool's ``$result.state.*``
    envelope.

    Mustache form ``{{ $result.state.<slot> }}`` is mandatory — bare
    ``$result.<slot>`` resolves to the apply tool's PrefabApp envelope's
    top level (not the raw :class:`ModificationResponse`), which would
    leave every slot empty after the morph. Pinned by
    ``test_apply_action_morph_chain_writes_*_slots`` in
    :file:`test_prefab_ui.py`.

    Returns ``list[Action]`` (not ``list[SetState]``) to match
    :func:`_build_apply_action`'s ``extra_on_success`` contract — the
    apply-action builder accepts any :class:`Action`, and SetState is
    just the concrete one we emit today.
    """
    return [
        SetState(slot, f"{{{{ $result.state.{slot} }}}}")
        for slot in _SO_MODIFY_MORPH_STATE_SLOTS
    ]


@dataclass(frozen=True)
class _SOModifyStateSeed:
    """Pre-computed state-slot values for the SO modify card.

    Bundled into a dataclass because the slot list has grown over time
    (#858 round-8 added ``applied_header_skipped_*``) and a flat keyword
    arg list exceeded ruff's :data:`PLR0913` threshold. The dataclass is
    construction-only; the caller passes it to
    :func:`_seed_so_modify_card_state` which writes the values into the
    PrefabApp state dict.
    """

    outcome_label: str
    outcome_variant: str
    subentity_failed_count: int
    subentity_failed_summary: str
    header_failed_count: int
    header_failed_summary: str
    header_skipped_count: int
    header_skipped_summary: str
    applied_verb: str
    subentity_row_lists: dict[str, list[dict[str, Any]]]


def _seed_so_modify_card_state(
    response: dict[str, Any],
    *,
    is_preview: bool,
    seed: _SOModifyStateSeed,
) -> dict[str, Any]:
    """Seed the SO modify card's state slots with build-time pre-morph
    defaults.

    Extracted from :func:`build_so_modify_ui` to keep that builder under
    ruff's complexity budget — the slot list has grown over time
    (#858 round-8 added ``applied_header_skipped_*``) and centralizing
    the seeding here means a new slot is a one-line edit, not a 3-site
    edit across seed + morph chain + render.

    On the preview path (``is_preview=True``), the outcome slots seed
    with ``"APPLIED"`` / ``"default"`` so the preview-time render shows
    success chrome by default and the on_success ``SetState`` chain
    morphs them to the actual apply outcome. On the standalone-applied
    path (``is_preview=False``), the seeded values match the actual
    outcome so a fully-failed apply doesn't show success chrome.

    The ``so_<section_key>_rows`` slots are bound 1:1 to the ``DataTable``
    inside :func:`_render_so_subentity_section`; the on_success chain
    copies ``$result.state.so_<section>_rows`` straight in.
    """
    state = _init_modify_card_state(response)
    state["applied_outcome_label"] = seed.outcome_label if not is_preview else "APPLIED"
    state["applied_outcome_variant"] = (
        seed.outcome_variant if not is_preview else "default"
    )
    state["applied_subentity_failed_count"] = seed.subentity_failed_count
    state["applied_subentity_failed_summary"] = seed.subentity_failed_summary
    state["applied_header_failed_count"] = seed.header_failed_count
    state["applied_header_failed_summary"] = seed.header_failed_summary
    state["applied_header_skipped_count"] = seed.header_skipped_count
    state["applied_header_skipped_summary"] = seed.header_skipped_summary
    state["applied_verb"] = seed.applied_verb
    for section_key, row_list in seed.subentity_row_lists.items():
        state[f"so_{section_key}_rows"] = row_list
    return state


def _actions_with_not_run_tail(
    response: dict[str, Any],
    *,
    is_preview: bool,
) -> list[dict[str, Any]]:
    """Return a modify card's effective action list, extended (on the apply
    path only) with the unattempted plan tail synthesized by the impl.

    ``execute_plan`` is fail-fast — ``response.actions`` ends at the first
    failed action. The impl stashes the leftover :class:`ActionSpec` entries
    under ``response.extras["not_run_actions"]`` so they participate in the
    collection-table row merge (classified by ``operation`` the same way
    executed actions are, rendered with the ``NOT RUN`` status pill). Without
    this merge the morph path would overwrite the preview's full row list with
    the apply response's SHORTER list, silently HIDING every planned action
    past the failure (#858 finding B / Copilot #875; same family as the BOM
    fix in ``_modify_product_bom_impl``).

    Shared by ``build_so_modify_ui`` and ``build_item_modify_ui`` — both feed
    the result into their collection-diff merge. On the preview path the extras
    are deliberately ignored (every action is already PLANNED) — guards against
    accidental leakage from a test or future code path that puts NOT-RUN
    entries on a preview response.
    """
    actions: list[dict[str, Any]] = list(response.get("actions") or [])
    if is_preview:
        return actions
    extras = response.get("extras") or {}
    not_run_actions = extras.get("not_run_actions") or []
    if not_run_actions:
        actions.extend(not_run_actions)
    return actions


def build_so_modify_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the modify-/delete-/correct-sales-order card (#723).

    Handles every SO write path that returns a :class:`ModificationResponse`:
    ``modify_sales_order``, ``delete_sales_order``, ``correct_sales_order``.
    Title verb derives from ``confirm_tool`` via :func:`_verb_label`
    (``Modify`` / ``Delete`` / ``Correct``).

    SO is more complex than PO because the modify plan can touch multiple
    sub-entity types in parallel (header, rows, addresses, fulfillments,
    shipping fees). Each sub-entity group renders as its own section
    under the entity-view body, grouped by ``operation`` prefix:

    - **Line items** — ``add_row`` / ``update_row`` / ``delete_row``.
    - **Addresses** — ``add_address`` / ``update_address`` /
      ``delete_address``. Updates render as bare ``field: new`` (no
      arrow) because Katana has no per-address GET endpoint to diff
      against — every address update would otherwise read
      ``(prior unknown) → new`` for every changed field, which is
      visual noise that just restates the unknown-prior fact. The
      ``address_style=True`` branch in :func:`_format_so_diff_pairs`
      collapses to the new-only form so address summary lines stay
      compact.
    - **Fulfillments** — ``add_fulfillment`` / ``update_fulfillment``
      / ``delete_fulfillment``.
    - **Shipping fees** — ``add_shipping_fee`` / ``update_shipping_fee``
      / ``delete_shipping_fee``.

    Apply-state morph (per the BOM modify card's pattern, #811):

    - Header Badge variant: ``state.applied_outcome_label`` /
      ``applied_outcome_variant`` flip between APPLIED / PARTIAL
      FAILURE / FAILED on the morph; on_success chain SetState reads
      ``{{ $result.state.applied_outcome_label }}`` (NOT
      ``$result.<field>``; ``$result`` resolves to the apply tool's
      PrefabApp envelope, not the raw ``ModificationResponse``).
    - Sub-entity failed-action Alert: gated by
      ``If(Rx("applied_subentity_failed_count") > 0)``; its summary
      text seeds via ``applied_subentity_failed_summary``.
    - Footer body verb: passed as ``"{{ applied_verb }}"`` mustache so
      it morphs in lockstep with the outcome Badge.
    """
    is_preview = bool(response.get("is_preview", True))
    actions: list[dict[str, Any]] = _actions_with_not_run_tail(
        response, is_preview=is_preview
    )
    entity_id = response.get("entity_id")
    prior_state = _normalize_so_prior_state(response.get("prior_state"))

    verb_label = _verb_label(confirm_tool)
    # Compose the entity view's source-of-truth dict by overlaying the
    # response on top of the normalized prior_state. Same shape as the
    # PO modify card.
    entity = {**prior_state, **{k: v for k, v in response.items() if v is not None}}
    if entity_id is not None:
        entity.setdefault("id", entity_id)

    # Header-only changes map — drives the header scalar-diff rendering
    # (:func:`_render_so_header_scalar_diffs`) only. Header failures are
    # NOT painted from this map; they flow through the state-driven
    # ``applied_header_failed_*`` Alert seeded by
    # :func:`_so_header_op_failure_alert_text`. Sub-entity actions render
    # in their own sections via ``_SO_SUBENTITY_GROUPS`` — including their
    # field changes here would let sub-entity field names that overlap
    # header names (``status``, ``picked_date``, ``tracking_number`` on
    # fulfillments) overwrite real header diffs.
    changes_by_field = _index_changes_by_field(
        actions, include_operations=_SO_HEADER_OPS
    )

    # Sub-entity failed-action summary — pre-formatted at build time and
    # seeded into state slots so the preview→Confirm in-place morph can
    # surface failures (the Python-painted per-action rows above carry
    # ✗ glyphs but the textual errors aggregate here).
    subentity_failed_count, subentity_failed_summary = _so_subentity_failed_summary(
        actions,
        so_id=entity_id if isinstance(entity_id, int) else None,
        confirm_tool=confirm_tool,
    )

    # Header-level failed-op summary — the SINGLE source of truth for
    # header failures on the SO modify card. Intentionally includes
    # failed ``update_header`` actions WITH field changes (round 8) as
    # well as failed top-level ``delete`` actions; sub-entity failures
    # are surfaced separately by ``_so_subentity_failed_summary``
    # (which filters out header ops to avoid double-rendering).
    header_failed_count, header_failed_summary = _so_header_op_failure_alert_text(
        actions
    )

    # Header-level NOT-RUN (skipped) summary — covers the round-8 gap
    # left by ``_index_changes_by_field`` filtering NOT-RUN ops out of
    # the header field map (#858 round 7) combined with
    # :func:`_build_so_subentity_row_lists` only bucketing sub-entity
    # ops. Without this Alert, a failed ``correct_sales_order`` whose
    # close-phase ``update_header`` is skipped renders only sub-entity
    # NOT-RUN rows — the operator can't tell the SO close/restore step
    # never ran.
    header_skipped_count, header_skipped_summary = _so_header_op_skipped_alert_text(
        actions
    )

    # Per-sub-entity row dicts — seed every section's row list with the
    # build-time view (PLANNED at preview, APPLIED/FAILED on the
    # standalone-applied path). The on_success ``SetState`` chain below
    # reads ``$result.state.so_<section>_rows`` to overwrite these on
    # the in-place morph so per-row chrome (gutter glyph, status Badge)
    # updates from the apply outcome — see #858 Copilot finding A.
    subentity_row_lists = _build_so_subentity_row_lists(actions)

    # Outcome bucketing — same vocabulary as PO modify (APPLIED /
    # PARTIAL FAILURE / FAILED).
    outcome_label, outcome_variant = _summarize_apply_outcome(actions)

    # SetState chain is extracted into ``_so_modify_morph_setstate_chain``
    # so the per-slot ``{{ $result.state.<slot> }}`` mustache pattern stays
    # centralized. See :data:`_SO_MODIFY_MORPH_STATE_SLOTS` for the
    # canonical slot list and the Rx-context contract that drives every
    # state-bound Badge, Alert, and section row-list on this card.
    apply_action = _build_apply_action(
        confirm_tool,
        confirm_request,
        extra_on_success=_so_modify_morph_setstate_chain(),
    )
    # ``_build_cancel_action`` interpolates its arg into "Cancel: do not
    # apply X." — noun-phrase forms so the message reads naturally. Same
    # pattern as PO #755.
    if verb_label == "Delete":
        cancel_operation_label = "that sales order deletion"
    elif verb_label == "Correct":
        cancel_operation_label = "those sales order corrections"
    else:
        cancel_operation_label = "those sales order changes"
    cancel_action = _build_cancel_action(cancel_operation_label)

    # Delete cards say "Deleted" / "DELETED" / "deleted." in applied
    # state; modify and correct cards say "Applied" / "APPLIED" /
    # "applied.". Failure overrides the applied copy below.
    if verb_label == "Delete":
        applied_title_suffix = "Deleted"
        applied_state_label = "DELETED"
        applied_verb = "deleted"
    else:
        applied_title_suffix = "Applied"
        applied_state_label = "APPLIED"
        applied_verb = "applied"
    applied_state_variant: str = "default"

    # Standalone-applied path (is_preview=False): drive the state
    # label + variant + title + verb from the actual outcome so a
    # fully-failed apply doesn't render with success chrome. Same
    # contract as PO modify (caught by Copilot on #755).
    if not is_preview and outcome_label != "APPLIED":
        applied_state_label = outcome_label
        applied_state_variant = outcome_variant
        if outcome_label == "FAILED":
            applied_title_suffix = "Failed"
            applied_verb = "failed"
        else:  # PARTIAL FAILURE
            applied_title_suffix = "Partially Applied"
            applied_verb = "partially applied"

    # State seeding is extracted into ``_seed_so_modify_card_state`` to
    # keep this builder under ruff's complexity budget — the slot list
    # has grown (#858 round-8 added ``applied_header_skipped_*``) and a
    # future addition shouldn't force a refactor each time. The seeded
    # values are the build-time pre-morph defaults; the on_success
    # ``SetState`` chain (see :func:`_so_modify_morph_setstate_chain`)
    # overwrites them from ``$result.state.*`` on the morph.
    state = _seed_so_modify_card_state(
        response,
        is_preview=is_preview,
        seed=_SOModifyStateSeed(
            outcome_label=outcome_label,
            outcome_variant=outcome_variant,
            subentity_failed_count=subentity_failed_count,
            subentity_failed_summary=subentity_failed_summary,
            header_failed_count=header_failed_count,
            header_failed_summary=header_failed_summary,
            header_skipped_count=header_skipped_count,
            header_skipped_summary=header_skipped_summary,
            applied_verb=applied_verb,
            subentity_row_lists=subentity_row_lists,
        ),
    )

    with (
        PrefabApp(state=state, css_class="p-4") as app,
        Card(),
    ):
        _render_preview_header(
            title_prefix=f"{verb_label} Sales Order",
            entity="sales_order",
            order_number=str(entity.get("order_number") or entity_id or "N/A"),
            status=entity.get("status"),
            applied_title_suffix=applied_title_suffix,
            applied_state_label=applied_state_label,
            applied_state_variant=applied_state_variant,
        )
        with CardContent(), Column(gap=3):
            if response.get("message"):
                Muted(content=response["message"])
            block_warnings = _render_so_entity_view(
                entity,
                actions=actions,
                changes=changes_by_field,
            )

            # State-driven sub-entity failed-action Alert. Mirrors the
            # BOM modify card's ``applied_failed_count`` / ``applied_failed_summary``
            # pattern — gated by ``If(Rx(...) > 0)`` so it stays hidden
            # at preview time and after a fully-successful apply, then
            # pops in after a partial/full failure morph. Seeded from
            # ``$result.state.*`` so the preview→Confirm in-place morph
            # surfaces failures the build-time render couldn't predict.
            with (
                If(Rx("applied_subentity_failed_count") > 0),
                Alert(variant="destructive", icon="circle-alert"),
            ):
                AlertTitle(
                    content="{{ applied_subentity_failed_count }} sub-entity failure(s)"
                )
                AlertDescription(content="{{ applied_subentity_failed_summary }}")

            # State-driven header-op failure Alert (#858 finding B).
            # SINGLE source of truth for header failures on the SO modify
            # card — covers BOTH failed top-level ``delete`` actions AND
            # failed ``update_header`` actions WITH field changes (round
            # 8). ``_so_subentity_failed_summary`` filters out header ops
            # so this Alert is the only surface they appear on. Gated
            # separately from the sub-entity Alert so header failures
            # surface under a truthful "header op" title instead of being
            # misattributed as a sub-entity failure.
            with (
                If(Rx("applied_header_failed_count") > 0),
                Alert(variant="destructive", icon="circle-alert"),
            ):
                AlertTitle(content="Sales order operation failed")
                AlertDescription(content="{{ applied_header_failed_summary }}")

            # State-driven header-op NOT-RUN Alert (#858 round-8 follow-up).
            # Mirrors the failed-op Alert above but for skipped header
            # steps — fires when a fail-fast ``correct_sales_order`` halts
            # before its close-phase ``update_header`` runs. Variant
            # ``info`` (neutral, the closest fit in :data:`AlertVariant` to
            # "didn't happen") so the destructive variant above keeps
            # exclusive ownership of the failure surface. Without this
            # Alert the operator couldn't tell the SO close/restore step
            # never ran — sub-entity NOT-RUN rows render in their own
            # section but a skipped header op had no rendering surface
            # (header field map filters NOT-RUN out per round 7, and the
            # sub-entity row lists only bucket sub-entity ops).
            with (
                If(Rx("applied_header_skipped_count") > 0),
                Alert(variant="info", icon="circle-info"),
            ):
                AlertTitle(
                    content="{{ applied_header_skipped_count }} header step(s) skipped"
                )
                AlertDescription(content="{{ applied_header_skipped_summary }}")

            if is_preview:
                with If("error"):
                    Separator()
                    with Alert(variant="destructive", icon="circle-alert"):
                        AlertTitle(content="Apply failed")
                        AlertDescription(content="{{ error }}")

        # Confirm label scales with the planned-action count. Delete
        # cards use "Confirm Delete" to mirror the destructive
        # affordance.
        n_actions = len(actions)
        if verb_label == "Delete":
            confirm_label = "Confirm Delete"
        elif n_actions > 1:
            confirm_label = f"Confirm {n_actions} changes"
        else:
            confirm_label = "Confirm Changes"

        _render_preview_footer(
            title_prefix=f"Sales Order {verb_label}",
            block_warnings=block_warnings,
            confirm_label=confirm_label,
            apply_action=apply_action,
            cancel_action=cancel_action,
            # No next-action buttons on modify cards by default — same
            # rationale as PO. The user already had the SO they wanted
            # to change; surfacing "Fulfill Order" here would be noise.
            next_action_buttons=(),
            # Mustache template against ``state.applied_verb`` (seeded
            # above + overwritten by the on_success chain) so the footer
            # body morphs to "Sales Order partially applied." / "Sales
            # Order failed." in lockstep with the Tier-1 outcome Badge.
            applied_verb="{{ applied_verb }}",
        )
    return app


# ============================================================================
# Sales Order detail (read) card — build_so_detail_ui (#913)
# ============================================================================


# Tier-3 scalar reference fields rendered on the SO detail card, in order.
# Each entry is ``(label, response_key)``; the line renders only when the
# response carries a truthy value, so a sparse SO stays compact. Mirrors the
# user-facing subset of ``_SO_HEADER_FIELD_SPEC`` that's worth surfacing on a
# read card (the modify card's diff-overlay machinery doesn't apply here).
_SO_DETAIL_SCALAR_FIELDS: tuple[tuple[str, str], ...] = (
    ("Customer ref", "customer_ref"),
    ("Order date", "order_created_date"),
    ("Picked date", "picked_date"),
    ("Notes", "additional_info"),
)


def _so_detail_header_section(so: dict[str, Any]) -> None:
    """Tier 1 — title (linked to the Katana SO page when available) + status
    badge.

    The title links straight to the source-of-truth Katana sales-order page
    (``katana_url``), so the footer needs no separate "View in Katana" button
    — but the product spec for this card calls for an explicit footer link, so
    we keep the title link AND the footer button (the link is the one-click
    affordance; the footer button is the conventional read-card action slot).
    Falls back to plain text when ``katana_url`` is missing.
    """
    order_no = so.get("order_no")
    title_content = f"Sales Order {order_no}" if order_no else "Sales Order"
    katana_url = so.get("katana_url")
    status = so.get("status")

    with Row(gap=2):
        with CardTitle():
            if katana_url:
                Link(content=title_content, href=katana_url, target="_blank")
            else:
                Text(content=title_content)
        if status:
            Badge(
                label=status,
                variant=status_badge_variant("sales_order", status),
            )


def _so_detail_metrics_section(so: dict[str, Any]) -> None:
    """Tier 2 — decision metrics: order Total, line-item count, delivery date.

    Each Metric renders only when its underlying value is present, so a draft
    SO with no delivery date doesn't paint an empty "Delivery" tile. The row
    is skipped entirely when none of the three are available.
    """
    total = so.get("total")
    currency = so.get("currency")
    rows = so.get("rows") or []
    delivery_date = so.get("delivery_date")

    has_any = total is not None or rows or delivery_date
    if not has_any:
        return
    with Row(gap=4):
        if total is not None:
            Metric(label="Total", value=_format_money(total, currency))
        if rows:
            Metric(label="Line Items", value=str(len(rows)))
        if delivery_date:
            Metric(label="Delivery", value=str(delivery_date))


def _so_detail_rows_table(so: dict[str, Any]) -> None:
    """Tier 3 — line-item DataTable (SKU, name, qty, unit price, line total).

    Static inline table — no per-row drill-down (the SO is the destination;
    row detail is inline, per the #913 product decision). The table binds to
    ``state.so.rows_display`` — pre-formatted display cells carrying
    ``unit_price_display`` / ``line_total_display`` strings so the money columns
    render currency-aware without a renderer-side formatter. The authoritative
    ``state.so.rows`` (full row data incl. ``id`` / ``total_discount`` /
    ``variant_id`` / ``tax_rate_id``) is kept separately so the model still sees
    row identifiers when the host forwards only ``structured_content`` — see
    :func:`build_so_detail_ui`. Renders a friendly empty-state when the SO has
    no line items.
    """
    rows = so.get("rows") or []
    if not rows:
        Separator()
        Muted(content="No line items on this sales order.")
        return
    Separator()
    Muted(content="Line items:")
    DataTable(
        columns=[
            DataTableColumn(key="sku", header="SKU", sortable=True),
            DataTableColumn(key="display_name", header="Name", sortable=True),
            DataTableColumn(key="quantity", header="Qty", sortable=True, align="right"),
            DataTableColumn(
                key="unit_price_display", header="Unit Price", align="right"
            ),
            DataTableColumn(
                key="line_total_display", header="Line Total", align="right"
            ),
        ],
        rows="{{ so.rows_display }}",
        **_paginate(len(rows)),
    )


def _so_detail_row_cells(so: dict[str, Any]) -> list[dict[str, Any]]:
    """Pre-compute per-row display cells for the line-item DataTable.

    These cells are stored under ``state.so.rows_display`` (via
    :func:`with_display_rows`) and the DataTable binds to
    ``{{ so.rows_display }}`` — kept separate from the authoritative
    ``state.so.rows`` so the reduction here never strips row identifiers. Each
    cell needs the rendered ``sku`` / ``display_name`` / ``quantity`` plus two
    pre-formatted money strings:

    - ``unit_price_display`` — ``price_per_unit`` formatted via
      ``_format_money`` in the SO currency (``"—"`` when null).
    - ``line_total_display`` — the row ``total`` when Katana supplied it,
      else ``price_per_unit * quantity`` as a fallback (``"—"`` when neither
      is computable).

    SKU coalesces to ``""`` (variants can have null SKUs — CLAUDE.md), and
    ``display_name`` falls back to a ``"Variant <id>"`` label so a cache-miss
    row still reads meaningfully instead of blank — or to a neutral
    ``"Unknown item"`` when even ``variant_id`` is null (avoids a confusing
    ``"Variant None"`` cell, since ``variant_id`` is optional in the response).
    """
    currency = so.get("currency")
    cells: list[dict[str, Any]] = []
    for r in so.get("rows") or []:
        qty = r.get("quantity")
        unit = float_or_none(r.get("price_per_unit"))
        total = float_or_none(r.get("total"))
        if total is None and unit is not None and qty is not None:
            total = unit * qty
        variant_id = r.get("variant_id")
        display_name = r.get("display_name") or (
            f"Variant {variant_id}" if variant_id is not None else "Unknown item"
        )
        cells.append(
            {
                "sku": r.get("sku") or "",
                "display_name": display_name,
                "quantity": qty,
                "unit_price_display": (
                    _format_money(unit, currency) if unit is not None else "—"
                ),
                "line_total_display": (
                    _format_money(total, currency) if total is not None else "—"
                ),
            }
        )
    return cells


def build_so_detail_ui(so: dict[str, Any]) -> PrefabApp:
    """Build a read-only detail card for a sales order (``get_sales_order``).

    Implements the four-tier framework from #537 for a pure read surface
    (#913) — no Confirm/Cancel rail, no mutation buttons:

    - **Tier 1 — Identity**: title as an external ``Link`` to the Katana
      sales-order page; status Badge with the bucket-driven variant from
      ``status_badge_variant("sales_order", ...)``.
    - **Tier 2 — Decision metrics**: order Total (currency-aware via
      ``_format_money``), line-item count, and delivery date — the facts an
      operator scans first on an order. Rendered as ``Metric`` tiles.
    - **Tier 3 — Reference**: Customer + Location party lines (resolved names
      via ``_render_party_line``, never bare IDs — the impl side fills
      ``customer_name`` / ``location_name`` from the typed cache), the
      storefront deep-link (``_render_ecommerce_link``), scalar header fields
      (customer ref / order date / picked date / notes), the billing +
      shipping address blocks (``_render_address_block``), and the static
      line-item ``DataTable`` (SKU / name / qty / unit price / line total —
      no row drill-down). Any name-resolution cache-miss advisories surface
      as warning badges.
    - **Tier 4 — Actions**: a single "View in Katana" link button. Pure read
      card — no Fulfill / Edit / mutation buttons (#913 product decision).

    Reference template: ``build_item_detail_ui`` (parent entity with an
    embedded child table) and ``build_variant_details_ui`` (Metric-row Tier 2
    on a read card).
    """
    # The line-item DataTable binds to ``state.so.rows_display`` (pre-formatted
    # display cells) while ``state.so.rows`` stays authoritative (row ``id`` /
    # ``total_discount`` / ``variant_id`` / ``tax_rate_id``). ``with_display_rows``
    # enforces the non-clobber invariant so the identifiers survive on a host
    # that forwards only ``structured_content`` (see the helper's docstring).
    # Shallow-copy ``so`` so the caller's response dict isn't mutated.
    so_state = with_display_rows(so, _so_detail_row_cells(so))

    with PrefabApp(state={"so": so_state}, css_class="p-4") as app, Card():
        with CardHeader(), Column(gap=1):
            _so_detail_header_section(so)

        with CardContent(), Column(gap=3):
            # Tier 2 — metrics.
            _so_detail_metrics_section(so)
            Separator()

            # Tier 3 — reference. Party lines first (the "who"), then
            # storefront link, scalar header fields, addresses, and the
            # line-item table.
            _render_party_line(
                "Customer",
                name=so.get("customer_name"),
                entity_id=so.get("customer_id"),
                entity_kind="customer",
            )
            # Location has no per-entity Katana web page (same as the SO
            # create / modify cards) — pass no ``entity_kind`` so the party
            # line renders ``"Location: <name>"`` without a dead link.
            _render_party_line(
                "Location",
                name=so.get("location_name"),
                entity_id=so.get("location_id"),
            )
            _render_ecommerce_link(so)

            for label, key in _SO_DETAIL_SCALAR_FIELDS:
                value = so.get(key)
                if value:
                    Text(content=f"{label}: {value}")

            # Tracking — render as a Link when a URL is present, else plain
            # text, else nothing.
            tracking_number = so.get("tracking_number")
            tracking_url = so.get("tracking_number_url")
            if tracking_number and tracking_url:
                with Row(gap=1):
                    Text(content="Tracking:")
                    Link(content=tracking_number, href=tracking_url, target="_blank")
            elif tracking_number:
                Text(content=f"Tracking: {tracking_number}")

            # Address blocks — billing + shipping, in that order. Each block
            # self-skips when empty (returns False), so a partial / absent
            # address set renders no dangling labels.
            addresses = so.get("addresses") or []
            for entity_type, label in (
                ("billing", "Billing Address"),
                ("shipping", "Shipping Address"),
            ):
                addr = next(
                    (a for a in addresses if a.get("entity_type") == entity_type),
                    None,
                )
                if addr is not None:
                    _render_address_block(label, addr)

            # Line-item table (Tier 3 decision driver) — last so the scalar
            # reference context sits above it.
            _so_detail_rows_table(so)

            # Name-resolution cache-miss advisories, if any.
            _render_warnings_block(so.get("warnings"))

        with CardFooter(), Row(gap=2):
            katana_url = so.get("katana_url")
            if katana_url:
                Button(
                    label="View in Katana",
                    variant="outline",
                    on_click=OpenLink(url=katana_url),
                )
    return app


def _render_mo_identity_lines(
    mo: dict[str, Any], changes: dict[str, FieldChangeView]
) -> None:
    """Render the MO Variant + Location identity lines (diff-aware).

    Variants have no per-variant page in Katana web UI (their parent product /
    material page owns the variant configuration), so the line stays plain
    text; a SKU-less variant still drops a ``Variant ID: <id>`` fallback via
    :func:`_render_party_line`. Location resolves to ``location_name``
    impl-side (anti-pattern #7); the fallback shows ``Location ID: <id>`` only
    on a cache miss. A swap on either renders the composite before→after party
    diff. Extracted from :func:`_render_mo_entity_view` to keep it under the
    branch limit.
    """
    variant_change = changes.get("variant_id")
    if variant_change is not None and variant_change.kind != "unchanged":
        _render_party_diff_line(
            "Variant",
            id_change=variant_change,
            name_change=changes.get("variant_name"),
            prior_name=mo.get("sku"),
        )
    elif mo.get("sku"):
        Text(content=f"Variant: {mo['sku']}")
    else:
        _render_party_line("Variant", name=None, entity_id=mo.get("variant_id"))

    location_change = changes.get("location_id")
    if location_change is not None and location_change.kind != "unchanged":
        _render_party_diff_line(
            "Location",
            id_change=location_change,
            name_change=changes.get("location_name"),
            prior_name=mo.get("location_name"),
        )
    else:
        _render_party_line(
            "Location",
            name=mo.get("location_name"),
            entity_id=mo.get("location_id"),
        )


def _render_mo_entity_view(
    mo: dict[str, Any],
    *,
    changes: dict[str, FieldChangeView] | None = None,
) -> list[str]:
    """Render the MO entity view (Tier 2 metrics + Tier 3 reference fields +
    warnings), returning the block-warning list for the caller to gate on.

    Shared between ``build_mo_create_ui`` (no diff overlay) and
    ``build_mo_modify_ui`` (``changes`` overlay, #721 Phase 4). When ``changes``
    is empty every line falls through to its plain form — byte-identical to the
    create card. Changing scalar header fields (planned_quantity / deadline /
    status / order_no / variant / location / notes) render their before→after
    diff instead; ``planned_quantity`` / ``Deadline`` drop their Metric when
    changing (the diff line carries the value) and stay Metrics otherwise.

    Must be called inside ``with CardContent(), Column(gap=3):``.
    """
    changes = changes or {}
    planned_change = changes.get("planned_quantity")
    deadline_change = changes.get("production_deadline_date")
    planned_changing = planned_change is not None and planned_change.kind != "unchanged"
    deadline_changing = (
        deadline_change is not None and deadline_change.kind != "unchanged"
    )

    # Tier 2 — Metrics row, for the metric fields that AREN'T changing (a
    # changing one renders as a before→after diff line below so old→new shows).
    metric_items: list[tuple[str, str]] = []
    if not planned_changing and mo.get("planned_quantity") is not None:
        metric_items.append(("Planned Qty", str(mo["planned_quantity"])))
    if not deadline_changing and mo.get("production_deadline_date"):
        metric_items.append(
            ("Deadline", _iso_date_only(mo["production_deadline_date"]))
        )
    if metric_items:
        with Row(gap=4):
            for label, value in metric_items:
                Metric(label=label, value=value)

    # Changing scalar header diffs.
    if planned_changing:
        _render_field_diff_line("Planned Qty", change=planned_change)
    if deadline_changing:
        _render_field_diff_line("Deadline", change=deadline_change)
    status_change = changes.get("status")
    if status_change is not None and status_change.kind != "unchanged":
        _render_field_diff_line("Status", change=status_change)
    order_no_change = changes.get("order_no")
    if order_no_change is not None and order_no_change.kind != "unchanged":
        _render_field_diff_line("Order No", change=order_no_change)

    _render_mo_identity_lines(mo, changes)

    if mo.get("order_created_date"):
        Text(content=f"Created: {_iso_date_only(mo['order_created_date'])}")
    notes_change = changes.get("additional_info")
    if notes_change is not None and notes_change.kind != "unchanged":
        _render_field_diff_line("Notes", change=notes_change)
    elif mo.get("additional_info"):
        Text(content=f"Notes: {mo['additional_info']}")

    return _render_warnings_block(mo.get("warnings"))


def build_mo_create_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the create-manufacturing-order card. Handles both preview and
    applied states. Reads ``ManufacturingOrderResponse.model_dump()`` —
    note that MO uses ``order_no`` (NOT ``order_number``) and
    ``additional_info`` (NOT ``notes``).

    Four-tier content:
    - Tier 1: title, order_no badge, PREVIEW/CREATED, status (variant from
      ``status_badge_variant("manufacturing_order", status)``).
    - Tier 2 + 3: :func:`_render_mo_entity_view` (Planned Qty / Deadline
      metrics; variant / location / created / notes; warnings) — shared with
      ``build_mo_modify_ui``.
    - Tier 4: Confirm/Cancel (preview) or View in Katana + Complete Order
      (applied).
    """
    order_number = response.get("order_no") or "N/A"
    status = response.get("status")

    apply_action = _build_apply_action(confirm_tool, confirm_request)
    cancel_action = _build_cancel_action("that manufacturing order")

    with (
        PrefabApp(state=_init_create_card_state(response), css_class="p-4") as app,
        Card(),
    ):
        _render_preview_header(
            title_prefix="Manufacturing Order",
            entity="manufacturing_order",
            order_number=order_number,
            status=status,
        )
        with CardContent(), Column(gap=3):
            block_warnings = _render_mo_entity_view(response)
        _render_preview_footer(
            title_prefix="Manufacturing Order",
            block_warnings=block_warnings,
            confirm_label="Confirm & Create Manufacturing Order",
            apply_action=apply_action,
            cancel_action=cancel_action,
            next_action_buttons=(
                # Completing an MO is a fulfill call with
                # order_type="manufacturing"; serial-tracked finished
                # goods need ``serial_numbers``, but the agent can ask
                # for those after seeing the preview. Same CallTool /
                # ``{{ result.id }}`` template pattern as the SO card.
                (
                    "Complete Order",
                    CallTool(
                        "fulfill_order",
                        arguments={
                            "order_id": "{{ result.id }}",
                            "order_type": "manufacturing",
                            "preview": True,
                        },
                    ),
                ),
            ),
        )
    return app


# ============================================================================
# MO modify / delete card (#721 Phase 4) — header entity-view + three
# collection diff tables (recipe rows / operation rows / productions), each on
# the shared collection-diff element (``mo_tables``). Replaces the generic
# ActionResult table for modify_/delete_manufacturing_order.
# ============================================================================

_MO_RECIPE_COLUMNS: list[DataTableColumn] = [
    DataTableColumn(key="sku_label", header="SKU"),
    DataTableColumn(key="display_name", header="Ingredient"),
    DataTableColumn(
        key="quantity_label", header="Qty / unit", align="right", width="11rem"
    ),
    DataTableColumn(key="status_label", header="Status", width="7rem"),
]
_MO_OPERATION_COLUMNS: list[DataTableColumn] = [
    DataTableColumn(key="operation_label_gutter", header="Operation"),
    DataTableColumn(key="op_status_label", header="Op Status"),
    DataTableColumn(key="status_label", header="Status", width="7rem"),
]
_MO_PRODUCTION_COLUMNS: list[DataTableColumn] = [
    DataTableColumn(
        key="quantity_label_gutter", header="Quantity", align="right", width="11rem"
    ),
    DataTableColumn(key="date_label", header="Date", width="12rem"),
    DataTableColumn(key="status_label", header="Status", width="7rem"),
]
_MO_RECIPE_KEY = "mo_recipe_rows"
_MO_OPERATION_KEY = "mo_operation_rows"
_MO_PRODUCTION_KEY = "mo_production_rows"


def _mo_recipe_rows(
    prior_state: dict[str, Any] | None,
    actions: list[dict[str, Any]],
    extras: dict[str, Any],
) -> tuple[list[dict[str, Any]], str]:
    """Recipe-row diff rows + summary, short-circuiting when no recipe CRUD."""
    if not any(
        str(a.get("operation") or "").lower()
        in ("add_recipe_row", "update_recipe_row", "delete_recipe_row")
        for a in actions
    ):
        return [], ""
    rows = prepare_recipe_table_rows(
        merge_recipe_rows_for_modify_card(
            prior_state,
            actions,
            _coerce_resolved_id_map(extras.get("resolved_variants")),
        )
    )
    return rows, collection_diff_summary(rows)


def _mo_operation_rows(
    prior_state: dict[str, Any] | None, actions: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], str]:
    """Operation-row diff rows + summary, short-circuiting when no op CRUD."""
    if not any(
        str(a.get("operation") or "").lower()
        in ("add_operation_row", "update_operation_row", "delete_operation_row")
        for a in actions
    ):
        return [], ""
    rows = prepare_operation_table_rows(
        merge_operation_rows_for_modify_card(prior_state, actions)
    )
    return rows, collection_diff_summary(rows)


def _mo_production_rows(
    prior_state: dict[str, Any] | None, actions: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], str]:
    """Production diff rows + summary, short-circuiting when no production CRUD."""
    if not any(
        str(a.get("operation") or "").lower()
        in ("add_production", "update_production", "delete_production")
        for a in actions
    ):
        return [], ""
    rows = prepare_production_table_rows(
        merge_productions_for_modify_card(prior_state, actions)
    )
    return rows, collection_diff_summary(rows)


def _render_mo_collection_table(
    *,
    summary: str,
    label: str,
    columns: list[DataTableColumn],
    state_key: str,
    row_count: int,
) -> None:
    """Render one MO collection diff table (summary line + state-bound table).

    Caller gates on ``summary`` being non-empty (the collection changed).
    ``row_count`` is the collection's row count, used to suppress the
    renderer's blank filler rows when the table fits on one page.
    """
    Separator()
    Muted(content=label)
    Text(content=summary)
    DataTable(
        columns=columns,
        rows=f"{{{{ {state_key} }}}}",
        **_paginate(row_count),
    )


def _mo_modify_rail(
    response: dict[str, Any],
    shown: list[tuple[Any, ...]],
    *,
    verb_label: str,
    confirm_tool: str,
    confirm_request: BaseModel,
) -> tuple[list[Action] | None, list[Action], dict[str, Any]]:
    """Build the MO modify card's apply/cancel actions + seeded state.

    The apply ``on_success`` morph-wires only the shown collections'
    state keys; ``state`` seeds those same collections' rows. Factored out
    to keep ``build_mo_modify_ui`` under the branch limit.
    """
    apply_action = _build_apply_action(
        confirm_tool,
        confirm_request,
        extra_on_success=[
            SetState(key, f"{{{{ $result.state.{key} }}}}") for _, _, key, _, _ in shown
        ]
        or None,
    )
    cancel_label = (
        "that manufacturing order deletion"
        if verb_label == "Delete"
        else "those manufacturing order changes"
    )
    cancel_action = _build_cancel_action(cancel_label)
    state = _init_modify_card_state(response)
    for _, rows, key, _, _ in shown:
        state[key] = rows
    return apply_action, cancel_action, state


def build_mo_modify_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the modify-/delete-manufacturing-order card (#721 Phase 4).

    Header scalar diffs share :func:`_render_mo_entity_view` with
    ``build_mo_create_ui`` (the ``changes`` overlay decorates planned_quantity /
    deadline / status / variant / location / notes). The three editable
    collections — recipe rows, operation rows, production records — each render
    a diff table on the shared collection-diff element (:mod:`mo_tables`),
    shown only when that collection changes; a header-only modify shows just
    the header diffs. Tables are state-bound and morph in place on apply.

    Replaces the generic ActionResult card for ``modify_manufacturing_order`` /
    ``delete_manufacturing_order``.
    """
    is_preview = bool(response.get("is_preview", True))
    actions = _actions_with_not_run_tail(response, is_preview=is_preview)
    entity_id = response.get("entity_id")
    verb_label = _verb_label(confirm_tool)

    raw_prior_state = response.get("prior_state")
    prior_state = raw_prior_state if isinstance(raw_prior_state, dict) else {}
    entity = {**prior_state, **{k: v for k, v in response.items() if v is not None}}
    if entity_id is not None:
        entity.setdefault("id", entity_id)

    changes_by_field = _index_changes_by_field(
        actions, include_operations=frozenset({"update_header"})
    )

    extras = response.get("extras") or {}
    recipe_rows, recipe_summary = _mo_recipe_rows(raw_prior_state, actions, extras)
    operation_rows, operation_summary = _mo_operation_rows(raw_prior_state, actions)
    production_rows, production_summary = _mo_production_rows(raw_prior_state, actions)

    # (summary, rows, state_key, columns, section_label) per collection — each
    # rendered / seeded / morph-wired only when its summary is non-empty (the
    # collection changed). Looping over the shown ones keeps the three
    # collections from tripling the function's branch count.
    collections = [
        (
            recipe_summary,
            recipe_rows,
            _MO_RECIPE_KEY,
            _MO_RECIPE_COLUMNS,
            "Recipe (ingredients):",
        ),
        (
            operation_summary,
            operation_rows,
            _MO_OPERATION_KEY,
            _MO_OPERATION_COLUMNS,
            "Operations:",
        ),
        (
            production_summary,
            production_rows,
            _MO_PRODUCTION_KEY,
            _MO_PRODUCTION_COLUMNS,
            "Productions:",
        ),
    ]
    shown = [c for c in collections if c[0]]
    apply_action, cancel_action, state = _mo_modify_rail(
        response,
        shown,
        verb_label=verb_label,
        confirm_tool=confirm_tool,
        confirm_request=confirm_request,
    )
    confirm_label = _modify_confirm_label(verb_label, len(actions))

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        title_suffix, state_label, state_variant, applied_verb = (
            _modify_applied_state_labels(
                verb_label, is_preview=is_preview, actions=actions
            )
        )
        _render_preview_header(
            title_prefix=f"{verb_label} Manufacturing Order",
            entity="manufacturing_order",
            order_number=str(entity.get("order_no") or entity_id or "N/A"),
            status=entity.get("status"),
            applied_title_suffix=title_suffix,
            applied_state_label=state_label,
            applied_state_variant=state_variant,
        )
        with CardContent(), Column(gap=3):
            if response.get("message"):
                Muted(content=response["message"])
            block_warnings = _render_mo_entity_view(entity, changes=changes_by_field)
            for summary, rows, key, columns, label in shown:
                _render_mo_collection_table(
                    summary=summary,
                    label=label,
                    columns=columns,
                    state_key=key,
                    row_count=len(rows),
                )
        _render_preview_footer(
            title_prefix=f"Manufacturing Order {verb_label}",
            block_warnings=block_warnings,
            confirm_label=confirm_label,
            apply_action=apply_action,
            cancel_action=cancel_action,
            next_action_buttons=(),
            applied_verb=applied_verb,
        )
    return app


# ============================================================================
# Stock-transfer modify / delete card (#721 Phase 5) — header-only. Stock
# transfer rows are immutable post-creation (Katana exposes no row-CRUD
# endpoints), so unlike MO/PO/item this card has NO collection diff tables —
# just the header scalar diffs + the preview/apply rail. Replaces the generic
# ActionResult table for modify_/delete_stock_transfer, the last entity that
# routed through it.
# ============================================================================

# (wire_field, label) for the stock-transfer header scalar diffs, in display
# order. ``new_status`` is the field name ``compute_field_diff`` emits for the
# ``update_status`` sub-payload (StockTransferStatusPatch.new_status); it
# renders as the "Status" line. Stock transfers have no GET-by-id endpoint, so
# every line renders ``(prior unknown) → new`` — there is no prior snapshot to
# diff against (see ``_modify_stock_transfer_impl``'s ``unknown_prior=True``).
_ST_HEADER_FIELDS: tuple[tuple[str, str], ...] = (
    ("stock_transfer_number", "Transfer No"),
    ("transfer_date", "Transfer Date"),
    ("expected_arrival_date", "Expected Arrival"),
    ("additional_info", "Notes"),
    ("new_status", "Status"),
)


def _render_stock_transfer_entity_view(
    st: dict[str, Any],
    *,
    changes: dict[str, FieldChangeView] | None = None,
) -> list[str]:
    """Render the stock-transfer entity view (header scalar diffs + warnings),
    returning the block-warning list for the caller to gate the Confirm button.

    Modify-specific today — there is no ``build_stock_transfer_create_ui`` to
    share it with (stock transfers are created via ``create_stock_transfer``
    which renders its own card). The ``changes`` overlay + ``changes=None``
    default mirror the other entity views so a future create card can adopt it
    without a signature change.

    Each ``_ST_HEADER_FIELDS`` entry renders its before→after diff when the
    field is changing, else its plain value when present. In practice the plain
    branch rarely fires: stock transfers have no GET endpoint, so the response
    carries no prior field values — every shown line is a changing diff
    (``(prior unknown) → new``). A delete plan has no field changes, so the
    loop renders nothing and the card body falls back to ``response.message``.

    Must be called inside ``with CardContent(), Column(gap=3):``.
    """
    changes = changes or {}
    for field, label in _ST_HEADER_FIELDS:
        change = changes.get(field)
        if change is not None and change.kind != "unchanged":
            _render_field_diff_line(label, change=change)
        elif st.get(field) is not None:
            _render_field_diff_line(label, value=st.get(field))

    # Trailer — consolidated failure block (only renders when an action
    # failed; the per-field ✗ glyphs above carry the inline signal, but the
    # error TEXT lives here so a failed/partial apply is interpretable). The
    # label map reuses _ST_HEADER_FIELDS so the block reads in card vocabulary
    # ("Status", "Transfer No") rather than wire field names.
    _render_failed_changes_block(changes, field_label_overrides=dict(_ST_HEADER_FIELDS))
    return _render_warnings_block(st.get("warnings"))


def build_stock_transfer_modify_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the modify-/delete-stock-transfer card (#721 Phase 5).

    Header-only — stock-transfer rows are immutable post-creation, so there are
    no collection diff tables (the simplest modify card in the family). Header
    scalar diffs (transfer number / transfer & expected-arrival dates / notes /
    status) render via :func:`_render_stock_transfer_entity_view`. Title verb
    derives from ``confirm_tool`` via :func:`_verb_label` (``Modify`` /
    ``Delete``).

    Stock transfers have no GET-by-id endpoint, so ``prior_state`` is always
    ``None`` and every diff line reads ``(prior unknown) → new``. No status
    Badge renders in the header — not by explicit suppression, but because the
    ``entity`` dict carries no ``status`` field (``ModificationResponse`` has
    none and there's no prior-state fetch), so ``_render_preview_header``'s
    ``if status:`` guard skips it. Replaces the generic ActionResult card for
    ``modify_stock_transfer`` / ``delete_stock_transfer``.
    """
    is_preview = bool(response.get("is_preview", True))
    # Apply path: extend with the unattempted plan tail so a fail-fast partial
    # doesn't drop not-run actions from the count/outcome. Inert on preview and
    # for the header-only shape, but kept for parity with the other cards.
    actions = _actions_with_not_run_tail(response, is_preview=is_preview)
    entity_id = response.get("entity_id")
    verb_label = _verb_label(confirm_tool)

    # ``prior_state`` is always None for stock transfers (no GET endpoint);
    # overlay the response scalars so the header/identity lines pick up
    # whatever the response carries.
    raw_prior_state = response.get("prior_state")
    prior_state = raw_prior_state if isinstance(raw_prior_state, dict) else {}
    entity = {**prior_state, **{k: v for k, v in response.items() if v is not None}}
    if entity_id is not None:
        entity.setdefault("id", entity_id)

    # Header + status field diffs both belong on the header view; scope to the
    # two header-ish operations so any future field-name overlap can't leak.
    changes_by_field = _index_changes_by_field(
        actions, include_operations=frozenset({"update_header", "update_status"})
    )

    # Tier-1 identity: prefer a human-readable transfer number over the raw ID.
    # There's no GET endpoint, so the entity dict never carries the current
    # number — but a rename plan puts the new value in
    # ``changes_by_field["stock_transfer_number"].after``. Use it when present
    # so the header reads "ST-002" rather than the bare id (anti-pattern #2;
    # ``_render_preview_header`` renders ``order_number`` verbatim, so the
    # fallback shows "42", not "#42"). A status-/dates-only modify has no
    # number to show, so the ID is the honest fallback.
    number_change = changes_by_field.get("stock_transfer_number")
    header_number = (
        entity.get("stock_transfer_number")
        or (number_change.after if number_change is not None else None)
        or entity_id
        or "N/A"
    )

    apply_action = _build_apply_action(confirm_tool, confirm_request)
    cancel_label = (
        "that stock transfer deletion"
        if verb_label == "Delete"
        else "those stock transfer changes"
    )
    cancel_action = _build_cancel_action(cancel_label)
    confirm_label = _modify_confirm_label(verb_label, len(actions))
    state = _init_modify_card_state(response)

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        title_suffix, state_label, state_variant, applied_verb = (
            _modify_applied_state_labels(
                verb_label, is_preview=is_preview, actions=actions
            )
        )
        _render_preview_header(
            title_prefix=f"{verb_label} Stock Transfer",
            entity="stock_transfer",
            order_number=str(header_number),
            status=entity.get("status"),
            applied_title_suffix=title_suffix,
            applied_state_label=state_label,
            applied_state_variant=state_variant,
        )
        with CardContent(), Column(gap=3):
            if response.get("message"):
                Muted(content=response["message"])
            block_warnings = _render_stock_transfer_entity_view(
                entity, changes=changes_by_field
            )
        _render_preview_footer(
            title_prefix=f"Stock Transfer {verb_label}",
            block_warnings=block_warnings,
            confirm_label=confirm_label,
            apply_action=apply_action,
            cancel_action=cancel_action,
            next_action_buttons=(),
            applied_verb=applied_verb,
        )
    return app


# ============================================================================
# Bin-transfer modify / delete card (#943) — header entity-view + one
# collection diff table (rows). Unlike stock transfers, bin transfer rows are
# fully mutable post-creation, and a GET-by-id endpoint exists — so this card
# is the PO-card shape (real prior-state diffs + a line-item table) rather
# than the stock-transfer header-only shape.
# ============================================================================

# (wire_field, label) for the bin-transfer header scalar diffs, in display
# order. ``new_status`` is the field name ``compute_field_diff`` emits for the
# ``update_status`` sub-payload (BinTransferStatusPatch.new_status); it
# renders as the "Status" line.
_BT_HEADER_FIELDS: tuple[tuple[str, str], ...] = (
    ("bin_transfer_number", "Transfer No"),
    ("location_id", "Location"),
    ("created_date", "Created Date"),
    ("departed_at", "Departed At"),
    ("arrived_at", "Arrived At"),
    ("additional_info", "Notes"),
    ("new_status", "Status"),
)


def _bt_location_display(value: Any, names: dict[int, str]) -> Any:
    """Render a location id as ``Name (id=N)`` when resolvable, else as-is."""
    if value is None:
        return None
    try:
        key = int(value)
    except (TypeError, ValueError):
        return value
    name = names.get(key)
    return f"{name} (id={key})" if name else value


def _render_bin_transfer_entity_view(
    bt: dict[str, Any],
    *,
    changes: dict[str, FieldChangeView] | None = None,
    location_names: dict[int, str] | None = None,
) -> list[str]:
    """Render the bin-transfer entity view (header scalar diffs + warnings),
    returning the block-warning list for the caller to gate the Confirm button.

    Each ``_BT_HEADER_FIELDS`` entry renders its before→after diff when the
    field is changing, else its plain value when present. Bin transfers have a
    GET-by-id endpoint, so unlike stock transfers the plain branch fires for
    unchanged header fields — the prior snapshot provides real context around
    the diff lines. The Location line resolves ids to names via
    ``location_names`` (``extras["resolved_locations"]``) so the operator can
    confirm without cross-referencing Katana; misses fall back to the raw id.

    Must be called inside ``with CardContent(), Column(gap=3):``.
    """
    changes = changes or {}
    names = location_names or {}
    for field, label in _BT_HEADER_FIELDS:
        change = changes.get(field)
        value = bt.get(field)
        if field == "location_id":
            if change is not None:
                change = change.model_copy(
                    update={
                        "before": _bt_location_display(change.before, names),
                        "after": _bt_location_display(change.after, names),
                    }
                )
            value = _bt_location_display(value, names)
        if change is not None and change.kind != "unchanged":
            _render_field_diff_line(label, change=change)
        elif value is not None:
            _render_field_diff_line(label, value=value)

    _render_failed_changes_block(changes, field_label_overrides=dict(_BT_HEADER_FIELDS))
    return _render_warnings_block(bt.get("warnings"))


_BIN_ROW_OP_NAMES = frozenset({"add_row", "update_row", "delete_row"})

# DataTable columns for the bin-transfer modify card's line-item diff table.
# SKU carries the kind gutter (``+ ``/``- ``/``~ ``/``  ``); the bin columns
# render resolved names ("A-01") with ``bin <id>`` / em-dash fallbacks.
_BIN_MODIFY_ROW_COLUMNS: list[DataTableColumn] = [
    DataTableColumn(key="sku_label", header="SKU"),
    DataTableColumn(key="display_name", header="Item"),
    DataTableColumn(key="quantity_label", header="Qty", align="right", width="9rem"),
    DataTableColumn(key="source_bin_label", header="From Bin", width="11rem"),
    DataTableColumn(key="target_bin_label", header="To Bin", width="11rem"),
    DataTableColumn(key="status_label", header="Status", width="7rem"),
]
_BIN_MODIFY_ROW_KEY = "bin_row_rows"
_BIN_MODIFY_ROW_REF = f"{{{{ {_BIN_MODIFY_ROW_KEY} }}}}"


def _coerce_resolved_bins(value: Any) -> dict[int, str]:
    """Coerce a wire ``{bin_id: bin_name}`` map back to int keys.

    Same wire round-trip as :func:`_coerce_resolved_id_map` (JSON stringifies
    int keys) but for the flat bin-name lookup the bin row table reads.
    """
    out: dict[int, str] = {}
    if not isinstance(value, dict):
        return out
    for key, val in value.items():
        try:
            int_key = int(key)
        except (TypeError, ValueError):
            continue
        if isinstance(val, str):
            out[int_key] = val
    return out


def _bin_modify_row_rows(
    prior_state: dict[str, Any] | None,
    actions: list[dict[str, Any]],
    *,
    extras: dict[str, Any],
) -> tuple[list[dict[str, Any]], str]:
    """Build the bin-transfer line-item diff rows + summary, short-circuiting
    when the plan has no row CRUD (header-/status-only modifies render just
    the header diffs)."""
    if not any(
        str(a.get("operation") or "").lower() in _BIN_ROW_OP_NAMES for a in actions
    ):
        return [], ""
    rows = prepare_bin_row_table_rows(
        merge_bin_row_rows_for_modify_card(
            prior_state,
            actions,
            _coerce_resolved_id_map(extras.get("resolved_variants")),
            _coerce_resolved_bins(extras.get("resolved_bins")),
        )
    )
    return rows, collection_diff_summary(rows)


def build_bin_transfer_modify_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Build the modify-/delete-bin-transfer card (#943).

    Header scalar diffs (transfer number / location / dates / notes / status)
    render via :func:`_render_bin_transfer_entity_view`; the row collection —
    mutable for bin transfers, unlike stock transfers — renders a diff table
    on the shared collection-diff skeleton (:mod:`bin_row_table`), shown only
    when the plan touches rows. Bin transfers have a GET-by-id endpoint, so
    ``prior_state`` carries a real snapshot and diff lines read
    ``before → after``. Title verb derives from ``confirm_tool`` via
    :func:`_verb_label` (``Modify`` / ``Delete``).
    """
    is_preview = bool(response.get("is_preview", True))
    # Apply path: extend with the unattempted plan tail so a fail-fast partial
    # doesn't drop not-run row actions from the morphed line-item table.
    actions = _actions_with_not_run_tail(response, is_preview=is_preview)
    entity_id = response.get("entity_id")
    verb_label = _verb_label(confirm_tool)

    raw_prior_state = response.get("prior_state")
    prior_state = raw_prior_state if isinstance(raw_prior_state, dict) else {}
    entity = {**prior_state, **{k: v for k, v in response.items() if v is not None}}
    if entity_id is not None:
        entity.setdefault("id", entity_id)

    # Header + status field diffs both belong on the header view; scope to the
    # two header-ish operations so row-level field names (quantity, bins)
    # can't leak into the header lines.
    changes_by_field = _index_changes_by_field(
        actions, include_operations=frozenset({"update_header", "update_status"})
    )

    extras = response.get("extras") or {}
    bin_row_rows, bin_row_summary = _bin_modify_row_rows(
        raw_prior_state, actions, extras=extras
    )
    show_row_table = bool(bin_row_summary)
    # Same wire shape as resolved_bins ({id: name}) — reuse the coercer.
    location_names = _coerce_resolved_bins(extras.get("resolved_locations"))

    number_change = changes_by_field.get("bin_transfer_number")
    header_number = (
        entity.get("bin_transfer_number")
        or (number_change.after if number_change is not None else None)
        or entity_id
        or "N/A"
    )

    apply_action = _build_apply_action(
        confirm_tool,
        confirm_request,
        # Morph the line-item table in place on apply (PO-card pattern).
        extra_on_success=(
            [
                SetState(
                    _BIN_MODIFY_ROW_KEY,
                    f"{{{{ $result.state.{_BIN_MODIFY_ROW_KEY} }}}}",
                )
            ]
            if show_row_table
            else None
        ),
    )
    cancel_label = (
        "that bin transfer deletion"
        if verb_label == "Delete"
        else "those bin transfer changes"
    )
    cancel_action = _build_cancel_action(cancel_label)
    confirm_label = _modify_confirm_label(verb_label, len(actions))
    state = _init_modify_card_state(response)
    if show_row_table:
        state[_BIN_MODIFY_ROW_KEY] = bin_row_rows

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        title_suffix, state_label, state_variant, applied_verb = (
            _modify_applied_state_labels(
                verb_label, is_preview=is_preview, actions=actions
            )
        )
        _render_preview_header(
            title_prefix=f"{verb_label} Bin Transfer",
            entity="bin_transfer",
            order_number=str(header_number),
            status=entity.get("status"),
            applied_title_suffix=title_suffix,
            applied_state_label=state_label,
            applied_state_variant=state_variant,
        )
        with CardContent(), Column(gap=3):
            if response.get("message"):
                Muted(content=response["message"])
            block_warnings = _render_bin_transfer_entity_view(
                entity, changes=changes_by_field, location_names=location_names
            )
            if show_row_table:
                Separator()
                Muted(content="Line items:")
                Text(content=bin_row_summary)
                DataTable(
                    columns=_BIN_MODIFY_ROW_COLUMNS,
                    rows=_BIN_MODIFY_ROW_REF,
                    **_paginate(len(bin_row_rows)),
                )
        _render_preview_footer(
            title_prefix=f"Bin Transfer {verb_label}",
            block_warnings=block_warnings,
            confirm_label=confirm_label,
            apply_action=apply_action,
            cancel_action=cancel_action,
            next_action_buttons=(),
            applied_verb=applied_verb,
        )
    return app


# ============================================================================
# Fulfillment & Receipt UIs
# ============================================================================


def _extract_fulfill_fields(
    response: dict[str, Any],
) -> tuple[str, str, str]:
    """Extract common fulfillment display fields."""
    return (
        response.get("order_type", "order").title(),
        response.get("order_number", "N/A"),
        response.get("status", "N/A"),
    )


def _render_fulfill_reference_block(response: dict[str, Any]) -> None:
    """Render Tier-3 reference data on the fulfill card.

    Two branches:

    - **Sales order** (``order_type == "sales"``): Customer party-line +
      shipping address (+ billing block when it differs from shipping
      via ``_addresses_are_equivalent``). The operator-anchoring "who
      does this ship to / where" facts the #card-ux fulfill card is
      built around.
    - **Manufacturing order** (``order_type == "manufacturing"``):
      ``inventory_updates`` rendered as a side-effects list (review
      item #6). MOs have no customer or shipping address, but they DO
      have inventory side-effects the operator needs to confirm
      ("Raw materials will be consumed from inventory based on BOM",
      finished-good serial attach, etc.). Pre-fix the MO branch
      silently dropped this content — the SO-branch deletion was
      correct (the per-row DataTable carried the same data); the
      MO-branch loss was a regression.
    """
    order_type = response.get("order_type")
    if order_type == "sales":
        _render_party_line(
            "Customer",
            name=response.get("customer_name"),
            entity_id=response.get("customer_id"),
            entity_kind="customer",
        )
        shipping = response.get("shipping_address")
        if shipping:
            _render_address_block("Shipping Address", shipping)
        billing = response.get("billing_address")
        # Defense-in-depth dedup: the impl side
        # (``_fetch_so_addresses`` in ``foundation/orders.py``) already
        # returns ``billing=None`` when the two addresses are
        # equivalent, but older/direct UI payloads that bypass that
        # impl path can still carry both. Hide the duplicate block here
        # — mirrors the customer-entity-view's card-side dedup.
        if billing and not (shipping and addresses_are_equivalent(shipping, billing)):
            _render_address_block("Billing Address", billing)
        return
    if order_type == "manufacturing":
        # Drop the now-redundant "completed_date will be set to ..." line —
        # ``picked_date`` is its own Metric on the card. Same for the
        # serial-attach line, which lands as a row in the per-row table.
        # What remains is genuinely useful BOM-consumption context.
        updates = response.get("inventory_updates") or []
        if not updates:
            return
        filtered = [
            u
            for u in updates
            if isinstance(u, str)
            and not u.startswith("completed_date / done_date will be set to")
            and not u.startswith("Finished-good serials to attach:")
        ]
        if not filtered:
            return
        Muted(content="Side effects:")
        for line in filtered:
            Text(content=f"  {line}")


# Max serial IDs to render verbatim in the fulfill card's "Serials" column
# before collapsing to a count. The DataTable column is sized for short
# manufacturing-run serial blocks; longer lists (e.g., bulk SO fulfillments
# with 50+ serials) would blow out the column width. The receipt card sibling
# uses its own literal — convergence is tracked as a follow-up.
_SERIAL_DISPLAY_THRESHOLD = 5


def _build_fulfill_row_display(row: dict[str, Any]) -> dict[str, Any]:
    """Flatten one ``FulfilledRowInfo`` dict into DataTable-ready strings.

    Parallel to ``_build_receipt_row_display`` (#556 / PR #793): the
    iframe template renders pure strings, so the builder owns money /
    qty / serial / batch formatting. Display rules:

    - ``quantity`` renders via ``:g`` so ``5.0 -> '5'`` while preserving
      ``2.5``.
    - ``serial_numbers`` collapses the list to its count when it grows
      past :data:`_SERIAL_DISPLAY_THRESHOLD` (``[1, 2, ..., 99]`` would
      blow out the column width); short lists render verbatim so the
      operator can sanity-check the IDs.
    - ``row_total`` renders through :func:`_format_money` (USD fallback)
      so the column stays consistent across currencies. Empty string when
      the row carries no price (MO branch).
    """

    def _serials_display() -> str:
        serials = row.get("serial_numbers") or []
        if not serials:
            return ""
        if len(serials) <= _SERIAL_DISPLAY_THRESHOLD:
            return ", ".join(str(s) for s in serials)
        return f"{len(serials)} serial(s)"

    row_total = row.get("row_total")
    qty = row.get("quantity")
    return {
        "display_name": row.get("display_name") or "",
        "sku": row.get("sku") or "",
        "quantity": f"{qty:g}" if isinstance(qty, int | float) else "",
        "serials": _serials_display(),
        "batch_summary": row.get("batch_summary") or "",
        "row_total": (
            _format_money(row_total, row.get("currency"))
            if row_total is not None
            else ""
        ),
    }


def _render_fulfill_metrics(response: dict[str, Any]) -> None:
    """Render the Tier 2 metric row for the fulfill card (#553).

    Four metrics:
    - **Rows** — count of rows being fulfilled (always present, never zero
      on a real response — the MO branch synthesizes a single-row entry).
    - **Total Qty** — sum of quantities across rows, rendered via ``:g``.
    - **Total Value** — sum of ``row_total`` across rows, formatted via
      babel. Omitted when no row carries a price (MO branch — MOs track
      cost, not price; the cost ledger lives on a separate surface).
    - **Picked** (or **Completed** on MO) — the backdated timestamp the
      caller supplied via ``completed_at``. Omitted when the caller didn't
      supply one (server-stamps at apply time).

    Skipped entirely when the response carries no enrichment
    (back-compat with older payloads that pre-dated #553).
    """
    rows_count = response.get("rows_count")
    if rows_count is None:
        return
    total_qty = response.get("total_quantity")
    total_value = response.get("total_value")
    currency = response.get("currency")
    picked_date = response.get("picked_date")
    # Pre-#card-ux the picked_date lived in an ``inventory_updates`` text
    # blob ("picked_date will be set to …") that rendered above the
    # per-row table. Promoting to a Metric puts the most operator-relevant
    # field — when does this fulfillment count? — at eye level alongside
    # row count + qty + value, instead of buried in a side panel.
    date_label = (
        "Completed" if response.get("order_type") == "manufacturing" else "Picked"
    )
    with Row(gap=4):
        Metric(label="Rows", value=str(rows_count))
        if isinstance(total_qty, int | float):
            Metric(label="Total Qty", value=f"{total_qty:g}")
        if total_value is not None:
            Metric(label="Total Value", value=_format_money(total_value, currency))
        if picked_date:
            Metric(label=date_label, value=str(picked_date))


def _render_fulfill_per_row_table(
    fulfilled_rows_display: list[dict[str, Any]],
    *,
    order_type: str,
    is_preview: bool,
) -> None:
    """Render the Tier 3 per-row DataTable for the fulfill card (#553).

    Skipped when ``fulfilled_rows_display`` is empty (back-compat for older
    payloads that pre-dated this enrichment).

    The column set varies by order type:
    - **Sales** orders carry a Line Total column (price * qty in the
      order currency) — the operator's most-asked decision context is
      "what does this fulfillment commit to".
    - **Manufacturing** orders drop the Line Total column (MOs track
      cost on a separate surface) and re-allocate that space to the
      serials column for the serial-tracked-finished-good case.
    """
    if not fulfilled_rows_display:
        return
    Separator()
    if is_preview:
        Muted(content="Rows being fulfilled:")
    else:
        Muted(content="Rows fulfilled:")
    columns: list[Any] = [
        DataTableColumn(key="display_name", header="Item", sortable=True),
        DataTableColumn(key="sku", header="SKU", sortable=True),
        DataTableColumn(key="quantity", header="Qty", align="right"),
        DataTableColumn(key="serials", header="Serials"),
        DataTableColumn(key="batch_summary", header="Batch"),
    ]
    if order_type == "sales":
        columns.append(
            DataTableColumn(key="row_total", header="Line Total", align="right")
        )
    DataTable(columns=columns, rows="{{ fulfilled_rows }}")


def build_fulfill_preview_ui(
    response: dict[str, Any],
    *,
    request: FulfillOrderRequest | None = None,
) -> PrefabApp:
    """Build a fulfillment preview card.

    The "Confirm Fulfillment" button re-invokes ``fulfill_order`` with
    ``preview=False`` and the original request args inlined. ``request``
    is the original ``FulfillOrderRequest`` — passing it preserves every
    non-default arg the user supplied (``completed_at``,
    ``serial_numbers``, ``acknowledge_inventory_ordering``, ``rows``).
    The default ``None`` is for back-compat with any caller that still
    builds the card from response-only data; new callsites must pass
    ``request=``. See #845.

    No LLM round-trip.

    Layout follows the #537 four-tier framework (#553):

    - **Tier 1** — title + order number badge + status badge.
    - **Tier 2** — Metric row: Rows / Total Qty / Total Value. Skipped on
      back-compat payloads that lack ``rows_count``.
    - **Tier 3** — per-row DataTable (Item / SKU / Qty / Serials / Batch
      [/ Line Total]). Skipped when ``fulfilled_rows`` is empty.
    - **Tier 4** — Confirm / Cancel button rail (driven by ``BLOCK:``
      warnings — disabled when any are present).
    """
    from katana_mcp.tools.foundation.orders import FulfillOrderRequest

    # `order_type_display` is .title()-cased ("Sales" / "Manufacturing") for
    # use in user-facing strings; `raw_order_type` is the lowercase enum
    # value ("sales" / "manufacturing") that FulfillOrderRequest expects.
    # Keep them named distinctly so a future edit can't quietly substitute
    # the display value into the request constructor.
    order_type_display, order_number, status = _extract_fulfill_fields(response)
    # Direct lookup, not ``.get()`` — ``FulfillOrderResponse`` declares
    # both fields required. A missing key signals a malformed response
    # dict and we want to fail at preview-build time, not at click time.
    # Run BEFORE the if/else so both branches enjoy the same fail-fast
    # contract (the pre-#845 code path constructed from these fields
    # unconditionally; now ``order_id`` is only referenced by the
    # back-compat fallback, so probe it explicitly here too).
    response_order_id = response["order_id"]
    raw_order_type = response["order_type"]
    # The confirm_request must carry every non-default arg the user supplied
    # to the preview call — otherwise the Confirm button's apply payload
    # defaults them out and the order completes at click-time `now()` rather
    # than the backdated `completed_at` the preview promised (#845). Pass
    # the original request through when available; fall back to the
    # response-only reconstruction for back-compat with any caller still
    # invoking ``build_fulfill_preview_ui(response)`` directly.
    if isinstance(request, FulfillOrderRequest):
        # ``preview=True`` is forced — ``_build_apply_action`` flips it to
        # False when materializing the apply payload, so the source value
        # would be ignored either way. Setting it explicitly here keeps
        # the iframe state's request snapshot consistent with the card's
        # "PREVIEW" rendering.
        confirm_request = request.model_copy(update={"preview": True})
    else:
        confirm_request = FulfillOrderRequest(
            order_id=response_order_id,
            order_type=raw_order_type,
            preview=True,
        )
    block_warnings, regular_warnings = _split_warnings(response.get("warnings"))
    apply_action = _build_apply_action("fulfill_order", confirm_request)
    cancel_action = _build_cancel_action(
        f"the {raw_order_type} order {order_number} fulfillment"
    )

    # Pre-flatten per-row rendering into state so the iframe template
    # never sees raw floats / lists — see #553 / PR #793.
    fulfilled_rows = response.get("fulfilled_rows") or []
    fulfilled_rows_display = [_build_fulfill_row_display(r) for r in fulfilled_rows]

    # Seed the full apply-rail state shape so the unified
    # ``_render_apply_button_row`` Rx bindings (``applied`` / ``error``)
    # resolve against present slots — see ADR-0021.
    state: dict[str, Any] = {
        **_APPLY_RAIL_STATE_INIT,
        "response": response,
        "fulfilled_rows": fulfilled_rows_display,
    }

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"Fulfill {order_type_display} Order")
            Badge(label=order_number, variant="outline")
            Badge(label=status, variant="secondary")

        with CardContent(), Column(gap=2):
            _render_fulfill_metrics(response)
            _render_fulfill_reference_block(response)
            _render_fulfill_per_row_table(
                fulfilled_rows_display,
                order_type=raw_order_type,
                is_preview=True,
            )

            if block_warnings or regular_warnings:
                Separator()
                for warning in block_warnings:
                    Badge(label=warning, variant="destructive")
                for warning in regular_warnings:
                    Badge(label=warning, variant="secondary")

        with CardFooter():
            _render_apply_button_row(
                confirm_label="Confirm Fulfillment",
                apply_action=apply_action,
                cancel_action=cancel_action,
                disabled=bool(block_warnings),
            )
    return app


def build_fulfill_success_ui(
    response: dict[str, Any],
) -> PrefabApp:
    """Build a fulfillment success card.

    Mirrors :func:`build_fulfill_preview_ui` minus the Confirm/Cancel
    rail, plus an expanded Tier 4 action set (#553):

    - **View in Katana** — deep-links to the order via ``katana_url``
      (omitted when the response carries no URL).
    - **Check Inventory** — the legacy follow-up; remains the default
      next action when no URL is available.
    """
    order_type, order_number, status = _extract_fulfill_fields(response)
    raw_order_type = response.get("order_type", "sales")
    katana_url = response.get("katana_url")

    # Pre-flatten the per-row rendering into state, same as the preview
    # path — the success card surfaces *what landed* on the wire, which
    # answers the agent's next-most-likely question ("did the right
    # serials attach?") without forcing a second tool call.
    fulfilled_rows = response.get("fulfilled_rows") or []
    fulfilled_rows_display = [_build_fulfill_row_display(r) for r in fulfilled_rows]

    state: dict[str, Any] = {
        "response": response,
        "fulfilled_rows": fulfilled_rows_display,
    }

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"{order_type} Order Fulfilled")
            Badge(label=order_number, variant="outline")
            Badge(label=status, variant="default")

        with CardContent(), Column(gap=2):
            if response.get("message"):
                Text(content=response["message"])
            _render_fulfill_metrics(response)
            _render_fulfill_reference_block(response)
            _render_fulfill_per_row_table(
                fulfilled_rows_display,
                order_type=raw_order_type,
                is_preview=False,
            )
            # Surface cache-miss advisories so the operator sees *why*
            # a Customer / Location party-line may have fallen back to
            # the raw-ID rendering. Both SO and MO impls populate the
            # advisories on the success response, but pre-fix the
            # success card never rendered them — a direct ``preview=
            # false`` caller would see ``"Customer ID: <id>"`` with no
            # explanation. Mirrors the preview-card warnings block.
            _render_warnings_block(response.get("warnings"))

        # ``check_inventory`` accepts SKUs OR variant_ids in the same arg
        # (``skus_or_variant_ids``), so coalesce on ``sku or variant_id``
        # per row — variants can legally have ``sku=None`` (CLAUDE.md
        # "Variants can have null SKUs"), and a SKU-less row still has a
        # variant_id that resolves the same lookup. Previous SKU-only
        # collection forced the fallback ``UpdateContext`` whenever any
        # fulfilled row was SKU-less, even though a deterministic
        # ``CallTool`` path existed.
        fulfilled_handles: list[str | int] = [
            handle
            for row in fulfilled_rows
            if (handle := row.get("sku") or row.get("variant_id")) is not None
        ]
        with CardFooter(), Row(gap=2):
            # Tier 4 actions (#553): two follow-ups. View in Katana wins
            # the primary slot when a deep-link is available (operator's
            # most common next move on a successful fulfill is to verify
            # in the web UI); inventory check stays the secondary action.
            if katana_url:
                Button(
                    label="View in Katana",
                    variant="default",
                    on_click=OpenLink(url=katana_url),
                )
            Button(
                label="Check Inventory",
                variant="outline",
                on_click=_check_inventory_action(
                    fulfilled_handles,
                    fallback_content=(
                        "User wants to check current inventory levels for the "
                        "items just fulfilled. Resolve identities from the "
                        "fulfilled rows and call check_inventory."
                    ),
                ),
            )
    return app


# ============================================================================
# Verification UI
# ============================================================================


def build_verification_ui(
    response: dict[str, Any],
) -> PrefabApp:
    """Build a verification results card with matches and discrepancies.

    Layout follows the #537 four-tier framework (#554):

    - **Tier 1 — Identity**: H3 title + PO badge + overall-status badge.
    - **Tier 2 — Decision metrics**: two or three Metric widgets —
      Matched count, Discrepant count (renders in red via
      ``trendSentiment="negative"`` when >0 — ``Metric`` has no
      Badge-style ``variant`` kwarg), and (when ``purchase_order.total``
      is known) Totals reconciled (``$matched_total of $po_total``)
      using :func:`_format_money` with the PO's currency. The Totals
      Metric is omitted entirely when ``po_total is None`` (back-compat
      path or PO with no recorded total) rather than showing a
      misleading ``$0.00`` placeholder.
    - **Tier 3 — Reference data**: two DataTables with explicit
      doc-vs-PO side-by-side columns (Qty/Price doc vs PO on matches;
      Expected / Actual columns on discrepancies).
    - **Tier 4 — Actions**: ``Row(gap=2)`` with three conditional
      buttons — View in Katana (when ``purchase_order.katana_url`` is
      set), Proceed to Receive (when ``overall_status == "match"``),
      Receive Anyway (otherwise).
    """
    overall_status = response.get("overall_status", "unknown")
    order_id = response.get("order_id", "")

    status_variant = {
        "match": "default",
        "partial_match": "secondary",
        "no_match": "destructive",
    }.get(overall_status, "secondary")

    matches = response.get("matches", [])
    discrepancies = response.get("discrepancies", [])
    purchase_order = response.get("purchase_order") or {}
    currency = purchase_order.get("currency")
    po_total = purchase_order.get("total")
    katana_url = purchase_order.get("katana_url")

    # Tier 2 — Decision metrics. ``matched_total`` only sums lines that
    # genuinely tie out (status == "perfect"); discrepant lines contribute
    # to the Discrepant count instead. Both totals format through
    # :func:`_format_money` so the symbol + decimal precision tracks the
    # PO's transaction currency.
    #
    # Price-fallback rule: ``_verify_order_document_impl`` skips the
    # price-mismatch check when ``doc_item.unit_price is None`` (document
    # omitted price), so a perfect-status match can still carry
    # ``unit_price=None``. Coercing that to ``0`` would silently undercount
    # the matched subtotal — e.g. ``$0.00 of $X.XX`` for a PO whose row
    # actually has a known price. Fall back to ``expected_unit_price``
    # (the PO row's ``price_per_unit``) when the document side is missing;
    # if both are unknown the line is skipped entirely.
    perfect_count = 0
    non_perfect_count = 0
    matched_total = 0.0
    for m in matches:
        if m.get("status") == "perfect":
            perfect_count += 1
            unit_price = m.get("unit_price")
            if unit_price is None:
                unit_price = m.get("expected_unit_price")
            if unit_price is not None:
                matched_total += (m.get("quantity") or 0) * unit_price
        else:
            non_perfect_count += 1
    discrepant_count = len(discrepancies) + non_perfect_count
    # ``Totals reconciled`` is only rendered when the PO side has a known
    # total. ``GetPurchaseOrderResponse.total`` is ``float | None`` and
    # the back-compat path can omit ``purchase_order`` entirely; in
    # either case ``_format_money(None, ...)`` would render ``$0.00`` and
    # produce a misleading ``$X of $0.00`` metric. Skip the widget
    # outright rather than show a fake zero — the operator can still
    # spot-check against ``View in Katana``.
    show_totals_reconciled = po_total is not None
    matched_total_formatted = _format_money(matched_total, currency)
    po_total_formatted = (
        _format_money(po_total, currency) if show_totals_reconciled else ""
    )

    with (
        PrefabApp(
            state={"matches": matches, "discrepancies": discrepancies},
            css_class="p-4",
        ) as app,
        Column(gap=4),
    ):
        # Tier 1 — Identity.
        with Row(gap=2):
            H3(content="Document Verification")
            Badge(label=f"PO {order_id or 'N/A'}", variant="outline")
            Badge(
                label=overall_status.replace("_", " ").title(), variant=status_variant
            )

        # Tier 2 — Decision metrics. ``Discrepant`` flips to red via
        # ``trendSentiment="negative"`` (Metric's color hook — no
        # Badge-style ``variant`` kwarg exists). The JSON alias form is
        # required for static type-check: ``Metric`` lacks the
        # ``**kwargs: Any`` overload that ``Button`` carries, so pyright
        # only sees the alias name through pydantic's generated init.
        with Row(gap=2):
            Metric(label="Matched", value=str(perfect_count))
            Metric(
                label="Discrepant",
                value=str(discrepant_count),
                trendSentiment="negative" if discrepant_count > 0 else "neutral",
            )
            if show_totals_reconciled:
                Metric(
                    label="Totals reconciled",
                    value=f"{matched_total_formatted} of {po_total_formatted}",
                )

        # Tier 3 — Reference data.
        # Matches table — explicit Qty/Price (doc) vs Qty/Price (PO)
        # side-by-side columns so non-perfect statuses show the delta
        # directly. ``Item`` column shows the canonical Katana-UI-format
        # display name (parent / config1 / config2), ``SKU`` remains as a
        # secondary identity column for ops + scripts.
        if matches:
            Muted(content="Matched Items:")
            DataTable(
                columns=[
                    DataTableColumn(key="display_name", header="Item", sortable=True),
                    DataTableColumn(key="sku", header="SKU", sortable=True),
                    DataTableColumn(key="quantity", header="Qty (doc)", align="right"),
                    DataTableColumn(
                        key="expected_quantity", header="Qty (PO)", align="right"
                    ),
                    DataTableColumn(
                        key="unit_price", header="Price (doc)", align="right"
                    ),
                    DataTableColumn(
                        key="expected_unit_price",
                        header="Price (PO)",
                        align="right",
                    ),
                    DataTableColumn(key="status", header="Status"),
                ],
                rows="{{ matches }}",
            )

        # Discrepancies table — same ``Item`` / ``SKU`` ordering for
        # visual consistency with the matches table above. Explicit
        # Expected / Actual columns surface the delta numerics that
        # ``Discrepancy.message`` previously folded into a string.
        if discrepancies:
            Muted(content="Discrepancies:")
            DataTable(
                columns=[
                    DataTableColumn(key="display_name", header="Item"),
                    DataTableColumn(key="sku", header="SKU"),
                    DataTableColumn(key="type", header="Type"),
                    DataTableColumn(key="expected", header="Expected", align="right"),
                    DataTableColumn(key="actual", header="Actual", align="right"),
                    DataTableColumn(key="message", header="Details"),
                ],
                rows="{{ discrepancies }}",
            )

        # Tier 4 — Actions. View-in-Katana wins the primary slot when a
        # deep-link is available (operator's most common follow-up is to
        # eyeball the PO in the web UI); Proceed / Receive Anyway gate on
        # ``overall_status``. Per the file-level convention, Katana URLs
        # use ``OpenLink`` for one-click navigation rather than
        # ``SendMessage`` indirection through the agent.
        #
        # Both Proceed / Receive Anyway hand the agent an
        # ``UpdateContext`` rather than calling ``receive_purchase_order``
        # directly: receive needs a per-row ``items`` array (quantities,
        # optional batch allocations, received_date), none of which the
        # verification response can pre-fill — the agent has to ask the
        # user (or mirror the document items) before invoking the tool.
        with Row(gap=2):
            if katana_url:
                Button(
                    label="View in Katana",
                    variant="default",
                    on_click=OpenLink(url=katana_url),
                )
            if overall_status == "match":
                Button(
                    label="Proceed to Receive",
                    variant="outline" if katana_url else "default",
                    on_click=UpdateContext(
                        content=(
                            f"User wants to receive items for purchase "
                            f"order {order_id}. The document matched the "
                            "PO — mirror the matched quantities into the "
                            "items array and call receive_purchase_order "
                            "with preview=True."
                        ),
                    ),
                )
            else:
                Button(
                    label="Receive Anyway",
                    variant="outline",
                    on_click=UpdateContext(
                        content=(
                            f"User wants to receive items for purchase "
                            f"order {order_id} despite discrepancies. "
                            "Confirm the per-row quantities with the user "
                            "first (the document and PO did not fully "
                            "agree), then call receive_purchase_order "
                            "with preview=True."
                        ),
                    ),
                )
    return app


# ============================================================================
# Generic Modification Preview/Result UIs (modify_*/delete_*/correct_*)
# ============================================================================


# Display labels for the verb in modification card titles. The verb is
# derived from the registered tool name (its first underscore-delimited
# token), so ``modify_item`` → "Modify", ``delete_item`` → "Delete", etc.
# Fallback for unrecognized verbs is "Modify" so the title still reads
# sensibly even if a new tool prefix is introduced before this map is
# updated.
_VERB_DISPLAY: dict[str, str] = {
    "modify": "Modify",
    "delete": "Delete",
    "correct": "Correct",
    "update": "Update",
}


def _verb_label(tool_name: str | None) -> str:
    """Pick the human-readable verb for the modification card title.

    Used to render ``"Modify Product"`` / ``"Delete Product"`` /
    ``"Correct Purchase Order"`` titles correctly across the modification
    rail. ``None`` (or any unrecognized prefix) falls back to "Modify".
    """
    if not tool_name:
        return "Modify"
    return _VERB_DISPLAY.get(tool_name.split("_", 1)[0], "Modify")


# ============================================================================
# Item Created/Updated/Deleted UIs
# ============================================================================


def _item_create_footer_section(item: dict[str, Any]) -> None:
    """Render Tier 4 actions for the create card.

    The agent just shipped a SKU to Katana; the likely next steps are to
    inspect it, set its opening stock, or put it to work. SKU-keyed actions
    (View Details / Check Inventory) fire ``CallTool`` directly — both tools
    accept a SKU and need no further composition. Set Initial Stock and the
    type-specific actions hand off via ``UpdateContext`` because the
    underlying tools need fields the create response can't supply (quantity,
    location, target variant). The title's external Link covers "open in
    Katana", so there's no footer button for that.
    """
    variants = item.get("variants") or []
    sku = item.get("sku") or (variants[0].get("sku") if variants else None)
    item_id = item.get("id")
    item_type = item.get("type") or "item"

    if sku:
        Button(
            label="View Details",
            variant="outline",
            on_click=CallTool("get_variant_details", arguments={"sku": sku}),
        )
        Button(
            label="Check Inventory",
            variant="outline",
            on_click=CallTool(
                "check_inventory", arguments={"skus_or_variant_ids": [sku]}
            ),
        )
        Button(
            label="Set Initial Stock",
            variant="outline",
            on_click=UpdateContext(
                content=(
                    f"User just created {item_type} '{sku}' and wants to set "
                    "its opening stock level. Ask for the quantity and "
                    "location, then call create_stock_adjustment with "
                    "preview=True."
                ),
            ),
        )

    if item_type == "material" and item_id is not None:
        Button(
            label="Create Purchase Order",
            variant="outline",
            on_click=UpdateContext(
                content=(
                    f"User wants to draft a purchase order for material_id "
                    f"{item_id}. Resolve the variant_id, default supplier, "
                    "and location, then call create_purchase_order with "
                    "preview=True."
                ),
            ),
        )
    elif item_type == "product" and item.get("is_producible") and item_id is not None:
        Button(
            label="Create Manufacturing Order",
            variant="outline",
            on_click=UpdateContext(
                content=(
                    f"User wants to draft a manufacturing order for "
                    f"product_id {item_id}. Resolve the target variant_id "
                    "(the product may have multiple), planned_quantity, and "
                    "location, then call create_manufacturing_order with "
                    "preview=True."
                ),
            ),
        )

    if item_id is not None:
        Button(
            label="Modify Item",
            variant="outline",
            on_click=UpdateContext(
                content=(
                    f"User wants to modify {item_type} {item_id}. Ask which "
                    "fields to change, then call modify_item with preview=True."
                ),
            ),
        )


def build_item_create_ui(item: dict[str, Any]) -> PrefabApp:
    """Build the post-creation card for ``create_product`` / ``create_material``
    / ``create_item``.

    Four-tier framework (#537), mirroring ``build_item_detail_ui`` but for a
    just-created single-variant item:

    - **Tier 1 — Identity:** name linked to ``katana_url``, a ``"Created"``
      state badge, type badge, and the sub-type status pills
      (sellable / producible / batch / serial).
    - **Tier 2 + 3:** :func:`_render_item_entity_view` with
      ``collapse_single_variant=True`` — a freshly-created item has exactly one
      variant, so its SKU + prices render inline instead of as a one-row table.
    - **Tier 4 — Actions:** :func:`_item_create_footer_section` (View Details,
      Check Inventory, Set Initial Stock, plus type-specific next steps).

    The ``create_*`` tools don't preview, so this is a success card with no
    Confirm gate. Replaces the former ``build_item_mutation_ui`` — modify /
    delete route through the generic modification cards (#615), so the only
    live path was always "Created".
    """
    with (
        PrefabApp(state={"item": item, "detail": None}, css_class="p-4") as app,
        Card(),
    ):
        with CardHeader(), Column(gap=2):
            _item_header_section(item, state_badge="Created")

        with CardContent(), Column(gap=3):
            # block_warnings return discarded — success card, no Confirm gate
            # to disable. Warnings still render inside the entity view.
            _render_item_entity_view(item, collapse_single_variant=True)

        with CardFooter(), Row(gap=2):
            _item_create_footer_section(item)
    return app


# ============================================================================
# Receipt UI
# ============================================================================


def _build_receipt_row_display(item: dict[str, Any]) -> dict[str, Any]:
    """Flatten one ``ReceivedItemInfo`` dict into DataTable-ready strings.

    The card-side template only renders pre-formatted strings — the
    builder owns money/date/qty formatting so a future style change is a
    one-line edit here instead of a hunt across the mustache template.

    Three display rules pinned by tests:

    - ``quantity`` renders as ``"{recv:g} of {ordered:g}"`` whenever both
      sides are present and differ (partial-receive case); otherwise just
      the receive quantity. Trailing-zero trimming via ``:g`` keeps
      ``5.0 → '5'`` while preserving ``2.5``.
    - ``received_date`` is trimmed to ``YYYY-MM-DD`` via
      :func:`_iso_date_only` — the time component is noise on a receipt.
    - ``row_total`` always renders through :func:`_format_money` (uses
      ``USD`` fallback) so the column is never blank when a price is
      present.
    """

    def _qty_display() -> str:
        recv = item.get("quantity")
        ordered = item.get("quantity_ordered")
        if recv is None:
            return ""
        recv_str = f"{recv:g}"
        if ordered is not None and float(ordered) != float(recv):
            return f"{recv_str} of {float(ordered):g}"
        return recv_str

    def _location_display() -> str:
        # Blank when the row inherits the order-level location (the common
        # case) — the column only carries signal for multi-location receives.
        name = item.get("location_name")
        if name:
            return str(name)
        loc_id = item.get("location_id")
        return f"Location ID: {loc_id}" if loc_id is not None else ""

    received_date = item.get("received_date")
    row_total = item.get("row_total")
    return {
        "display_name": item.get("display_name") or "",
        "sku": item.get("sku") or "",
        "quantity": _qty_display(),
        "location": _location_display(),
        "received_date": _iso_date_only(received_date) if received_date else "—",
        "batch_summary": item.get("batch_summary") or "",
        "row_total": (
            _format_money(row_total, item.get("currency"))
            if row_total is not None
            else ""
        ),
    }


def build_receipt_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel | None = None,
    confirm_tool: str | None = None,
) -> PrefabApp:
    """Build a receipt card for received purchase order items.

    On the preview branch, pass ``confirm_request`` (the original Pydantic
    input) and ``confirm_tool`` (the matching tool name) to wire the
    "Confirm Receipt" button. Both kwargs are optional because the same
    builder is reused for the non-preview render where no confirm button
    is shown — must be set together (enforced by ``_build_apply_action``).
    """
    order_number = response.get("order_number", "N/A")
    is_preview = response.get("is_preview", True)
    apply_action = _build_apply_action(confirm_tool, confirm_request)
    cancel_action = _build_cancel_action(f"the receipt for {order_number}")

    # Per-row Tier 3 DataTable rows are pre-flattened into the state so
    # the iframe mustache template renders pure strings — see #556.
    received_items = response.get("received_items") or []
    received_items_display = [_build_receipt_row_display(it) for it in received_items]

    # Seed the full apply-rail state shape so the unified
    # ``_render_apply_button_row`` Rx bindings (``applied`` / ``error``)
    # resolve against present slots — see ADR-0021.
    state: dict[str, Any] = {
        **_APPLY_RAIL_STATE_INIT,
        "response": response,
        "received_items": received_items_display,
    }

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content="Purchase Order Receipt")
            Badge(label=order_number, variant="outline")
            Badge(
                label="PREVIEW" if is_preview else "RECEIVED",
                variant="secondary" if is_preview else "default",
            )

        with CardContent(), Column(gap=2):
            if response.get("message"):
                Text(content=response["message"])
            Metric(
                label="Items Received",
                value=str(response.get("items_received", 0)),
            )
            if response.get("status"):
                Text(content=f"PO Status: {response['status']}")
            # Pre-#card-ux the supplier line manually built
            # ``"Supplier: <name> (ID: <id>)"``, bypassing
            # ``_render_party_line``. Using the helper picks up the
            # Katana web Link decoration for free and routes the
            # name-resolution fallback through the documented path.
            _render_party_line(
                "Supplier",
                name=response.get("supplier_name"),
                entity_id=response.get("supplier_id"),
                entity_kind="supplier",
            )
            # Receiving location: shows where the goods physically land.
            # Pre-#card-ux the receipt card surfaced no Location at all —
            # the operator confirming a receipt couldn't tell which
            # warehouse they were committing inventory into.
            _render_party_line(
                "Location",
                name=response.get("location_name"),
                entity_id=response.get("location_id"),
            )
            if response.get("total_cost") is not None:
                Metric(
                    label="PO Total",
                    value=_format_money(
                        response["total_cost"], response.get("currency")
                    ),
                )

            # Tier 3 — per-row breakdown so the agent can verify *what*
            # is being received without parsing the raw items=[...]
            # tool-call blob below the card. Only render when the
            # response carries enrichment (back-compat with older
            # payloads that pre-dated #556).
            if received_items_display:
                Separator()
                Muted(
                    content="Items being received:" if is_preview else "Items received:"
                )
                DataTable(
                    columns=[
                        DataTableColumn(
                            key="display_name", header="Item", sortable=True
                        ),
                        DataTableColumn(key="sku", header="SKU", sortable=True),
                        DataTableColumn(key="quantity", header="Qty", align="right"),
                        DataTableColumn(key="location", header="Destination"),
                        DataTableColumn(key="received_date", header="Received"),
                        DataTableColumn(key="batch_summary", header="Batch"),
                        DataTableColumn(
                            key="row_total", header="Line Total", align="right"
                        ),
                    ],
                    rows="{{ received_items }}",
                )

            block_warnings, regular_warnings = _split_warnings(response.get("warnings"))
            if block_warnings or regular_warnings:
                Separator()
                for warning in block_warnings:
                    Badge(label=warning, variant="destructive")
                for warning in regular_warnings:
                    Badge(label=warning, variant="secondary")

        # Collect SKUs from the receipt rows for the Check Inventory
        # CallTool; falls back to UpdateContext when the response carries
        # no SKUs (rare — per-row enrichment normally ships sku).
        received_skus: list[str | int] = [
            row["sku"] for row in received_items_display if row.get("sku")
        ]
        with CardFooter():
            if is_preview and apply_action is not None:
                _render_apply_button_row(
                    confirm_label="Confirm Receipt",
                    apply_action=apply_action,
                    cancel_action=cancel_action,
                    disabled=bool(block_warnings),
                )
            else:
                Button(
                    label="Check Inventory",
                    variant="outline",
                    on_click=_check_inventory_action(
                        received_skus,
                        fallback_content=(
                            "User wants to check current inventory levels "
                            "after the receipt. Resolve the SKUs from the "
                            "received items and call check_inventory."
                        ),
                    ),
                )
    return app


# ============================================================================
# Batch Recipe Update UI
# ============================================================================


def _format_batch_transactions_summary(
    transactions: list[dict[str, Any]] | None,
) -> str:
    """Collapse a ``batch_transactions`` list into a single display string.

    Wire shape is ``[{batch_id: int, quantity: float}, ...]``. The summary
    renders as ``"batch 42x30, batch 51x20"`` (ASCII ``x`` per the
    RUF001 / RUF002 ambiguous-unicode rule; the multiplication sign
    U+00D7 trips the linter). Empty / missing transactions return the
    empty string — callers decide whether to render the empty cell or
    skip the column.
    """
    if not transactions:
        return ""
    parts: list[str] = []
    for bt in transactions:
        if not isinstance(bt, dict):
            continue
        batch_id = bt.get("batch_id")
        qty = bt.get("quantity")
        if batch_id is None:
            continue
        qty_str = f"{qty:g}" if isinstance(qty, (int, float)) else str(qty or "")
        parts.append(f"batch {batch_id}x{qty_str}" if qty_str else f"batch {batch_id}")
    return ", ".join(parts)


def _format_serial_numbers_summary(serials: list[Any] | None) -> str:
    """Collapse a serial-number list into a single display string.

    Mirrors :func:`_format_batch_transactions_summary` shape — empty input
    returns the empty string. Non-string serials are coerced via ``str``
    for defensiveness against odd inputs (the wire model is ``list[str]``).
    """
    if not serials:
        return ""
    return ", ".join(str(s) for s in serials if s is not None and str(s).strip())


def _build_recipe_row_diff_view(
    field: str,
    *,
    op_type: str,
    before: Any,
    after: Any,
    label: str,
) -> FieldChangeView | None:
    """Project a per-row before/after pair onto a ``FieldChangeView``.

    Maps the recipe-row ``op_type`` (``add`` / ``update`` / ``delete``)
    onto :class:`FieldChangeView`'s ``kind`` discriminator so the diff
    string formatter can share the rendering rules used by the modify-
    card entity views:

    - ``add`` → ``kind="added"`` with ``before=None``
    - ``delete`` → ``kind="removed"`` with ``after=None``
    - ``update`` → ``kind="changed"`` when ``before != after``,
      ``kind="unchanged"`` when they match (the row was sent but the
      field wasn't actually patched — the formatter renders the current
      value rather than the noisy ``"N -> N"``).

    Returns ``None`` when the before/after pair has nothing to render
    (both unset and not an add/delete signal) so the caller can drop
    the cell to an empty string rather than emit ``(unset) -> (unset)``.
    """
    op_norm = (op_type or "").lower()
    if op_norm == "add":
        if after is None:
            return None
        return FieldChangeView(
            field=field, before=None, after=after, kind="added", label=label
        )
    if op_norm == "delete":
        if before is None:
            return None
        return FieldChangeView(
            field=field, before=before, after=None, kind="removed", label=label
        )
    # ``update`` (and unknown op_types fall through here so the caller
    # still gets a diff if both sides are populated).
    if before is None and after is None:
        return None
    if before == after:
        return FieldChangeView(
            field=field, before=before, after=after, kind="unchanged", label=label
        )
    return FieldChangeView(
        field=field, before=before, after=after, kind="changed", label=label
    )


def _format_recipe_row_diff(
    change: FieldChangeView | None,
    *,
    formatter: Any = None,
) -> str:
    """Render a per-row diff projection as a single DataTable cell string.

    Unlike :func:`_render_field_diff_line` (which emits a ``Text``
    component into a Column layout), this returns a flat string suitable
    for embedding in a DataTable cell. Output shapes:

    - ``change is None`` → ``""`` (no signal, empty cell).
    - ``kind == "added"`` → ``"+ after"`` (or ``""`` when the formatter
      returns an empty string — e.g. ``batch_transactions=[]`` — so the
      optional column drop-out still kicks in).
    - ``kind == "removed"`` → ``"- before"`` (same empty-cell rule).
    - ``kind == "unchanged"`` → ``"after"`` (the field rode along on the
      patch but didn't change — render the current value, not a no-op
      diff).
    - ``kind == "changed"`` with ``before is None`` → ``"after"``. This
      is the back-compat path for ``update`` ops emitted before the
      ``before_*`` enricher landed: we don't know the prior value, so we
      render only the after side rather than implying the prior was
      actually unset (``"(unset) -> 4.0"``).
    - ``kind == "changed"`` otherwise → ``"before -> after"`` (ASCII
      arrow, since this string lands in a DataTable cell rather than a
      ``Text`` component, and the cell text is sometimes copy-pasted
      into ops scripts where the unicode arrow is less ergonomic).

    ``formatter`` overrides :func:`_format_diff_value` for value-side
    rendering — used to render ``batch_transactions`` and
    ``serial_numbers`` via their list formatters instead of the
    generic ``repr`` fallback.
    """
    if change is None:
        return ""
    fmt = formatter if formatter is not None else _format_diff_value
    if change.kind == "added":
        formatted = fmt(change.after)
        return f"+ {formatted}" if formatted else ""
    if change.kind == "removed":
        formatted = fmt(change.before)
        return f"- {formatted}" if formatted else ""
    if change.kind == "unchanged":
        return fmt(change.after) if change.after is not None else fmt(change.before)
    # ``changed``. Back-compat: when the prior snapshot wasn't threaded
    # through (``before is None``) for an ``update`` op, render only the
    # after value — claiming the prior was ``(unset)`` is misleading.
    if change.before is None:
        return fmt(change.after)
    # ASCII arrow keeps the cell copy-paste friendly and sidesteps RUF001
    # entirely for this string-valued cell path.
    return f"{fmt(change.before)} -> {fmt(change.after)}"


def _build_batch_recipe_row(op: dict[str, Any], *, group_label: str) -> dict[str, Any]:
    """Flatten a result-op dict into the DataTable row shape.

    Splits out the per-row qty / batch_transactions / serial_numbers
    diffs via :class:`FieldChangeView` so the cell strings reuse the
    same projection vocabulary the modify-card entity views consume.
    """
    op_type = op.get("op_type") or ""
    display = (
        op.get("display_name")
        or op.get("sku")
        or (f"variant {op['variant_id']}" if op.get("variant_id") else "")
    )

    qty_after = op.get("planned_quantity_per_unit")
    qty_before = op.get("before_planned_quantity_per_unit")
    qty_change = _build_recipe_row_diff_view(
        "planned_quantity_per_unit",
        op_type=op_type,
        before=qty_before,
        after=qty_after,
        label="Qty",
    )

    batch_after = op.get("batch_transactions")
    batch_before = op.get("before_batch_transactions")
    batch_change = _build_recipe_row_diff_view(
        "batch_transactions",
        op_type=op_type,
        before=batch_before,
        after=batch_after,
        label="Batch",
    )

    serial_after = op.get("serial_numbers")
    serial_before = op.get("before_serial_numbers")
    serial_change = _build_recipe_row_diff_view(
        "serial_numbers",
        op_type=op_type,
        before=serial_before,
        after=serial_after,
        label="Serials",
    )

    return {
        "group": group_label,
        "mo_id": op.get("manufacturing_order_id"),
        "action": op_type.upper(),
        "row_id": op.get("recipe_row_id") or "(new)",
        "sku": op.get("sku") or "",
        "item": display,
        "qty": _format_recipe_row_diff(qty_change),
        "batch": _format_recipe_row_diff(
            batch_change, formatter=_format_batch_transactions_summary
        ),
        "serials": _format_recipe_row_diff(
            serial_change, formatter=_format_serial_numbers_summary
        ),
        "status": (op.get("status") or "pending").upper(),
        "error": op.get("error") or "",
    }


def build_batch_recipe_update_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel | None = None,
    confirm_tool: str | None = None,
) -> PrefabApp:
    """Build a batch recipe update card with per-group tables and summary metrics.

    Shows one row per planned sub-op grouped by replacement group_label.
    Preview mode shows all ops as PENDING; executed mode shows SUCCESS/FAILED/SKIPPED.

    Per-row diff columns surface what each sub-op changes about the
    underlying recipe row:

    - ``Qty`` — ``planned_quantity_per_unit`` before vs after. ``add``
      ops show ``+ N``; ``delete`` ops show ``- N`` (when the upstream
      enricher resolved the prior value); ``update`` ops show
      ``before -> after``.
    - ``Batch`` — ``batch_transactions`` allocations, post-#518. Same
      diff shape as Qty, formatted as ``batch <id>x<qty>, ...``.
    - ``Serials`` — ``serial_numbers``, formatted as comma-joined.

    The diff overlay uses :class:`FieldChangeView` internally so the
    projection logic shares vocabulary with the modify-card entity
    views (PR #755). DataTable cells render flat strings rather than
    components — see :func:`_format_recipe_row_diff` for the
    ``+`` / ``-`` / ``before -> after`` shapes.

    Back-compat: per-row diff inputs (``before_planned_quantity_per_unit``,
    ``before_batch_transactions``, ``before_serial_numbers``) are
    optional. Result ops without a ``before`` snapshot still render —
    the diff cells just show ``+ after`` (for add) or empty (for
    delete with no captured prior).

    On the preview branch, pass ``confirm_request`` (the original Pydantic
    input) and ``confirm_tool`` (the matching tool name) to wire the
    "Execute batch" button. Both kwargs are optional because the same
    builder is reused for the non-preview render — must be set together
    (enforced by ``_build_apply_action``).
    """
    is_preview = response.get("is_preview", True)
    results = response.get("results", [])
    warnings = response.get("warnings", [])
    message = response.get("message", "")

    # Group sub-ops by group_label for display
    groups: dict[str, list[dict[str, Any]]] = {}
    for op in results:
        label = op.get("group_label") or "Other"
        groups.setdefault(label, []).append(op)

    # Augment each row with display-friendly fields (flatten nested structure).
    # ``item`` column prefers the canonical ``display_name`` (Katana-UI format
    # ``parent / value1 / value2`` built upstream via
    # ``build_variant_display_name``), then SKU, then a ``variant {id}``
    # fallback so the row always renders something meaningful even on
    # cold-cache calls where neither is resolved. Per-row diff columns
    # (qty / batch / serials) are projected via ``FieldChangeView`` —
    # see :func:`_build_batch_recipe_row`.
    flat_rows: list[dict[str, Any]] = []
    for label, ops in groups.items():
        for op in ops:
            flat_rows.append(_build_batch_recipe_row(op, group_label=label))

    # Decide whether to render the optional ``Batch`` / ``Serials`` columns.
    # Most batch recipe payloads don't touch batch tracking or serial
    # tracking; padding every card with two empty columns is a waste of
    # horizontal real estate. Render the column only when at least one
    # row carries a non-empty cell.
    has_batch_signal = any(r["batch"] for r in flat_rows)
    has_serial_signal = any(r["serials"] for r in flat_rows)

    total = response.get("total_ops", 0)
    success = response.get("success_count", 0)
    failed = response.get("failed_count", 0)
    skipped = response.get("skipped_count", 0)

    mode_label = "PREVIEW" if is_preview else "RESULTS"
    mode_variant = (
        "secondary" if is_preview else ("destructive" if failed > 0 else "default")
    )

    # Seed the full apply-rail state shape so the unified
    # ``_render_apply_button_row`` Rx bindings (``applied`` / ``error``)
    # resolve against present slots — see ADR-0021.
    state: dict[str, Any] = {
        **_APPLY_RAIL_STATE_INIT,
        "rows": flat_rows,
        "summary": {
            "total": total,
            "success": success,
            "failed": failed,
            "skipped": skipped,
        },
        "is_preview": is_preview,
        "warnings": warnings,
        "groups": list(groups.keys()),
    }
    apply_action = _build_apply_action(confirm_tool, confirm_request)
    cancel_action = _build_cancel_action(
        f"the batch recipe update ({total} planned operation(s))"
    )

    # The pre-#card-ux table carried a separate "Row ID" column rendering
    # the raw ``recipe_row_id`` (or "(new)"). That ID has no user value —
    # the ``Action`` column already says ADD/UPDATE/DELETE which captures
    # the new-vs-existing distinction the integer was standing in for —
    # and the structured response carries the ID for any programmatic
    # follow-up. The ``MO`` column still surfaces ``manufacturing_order_id``
    # as a per-row anchor; resolving it to the MO's order_no via the
    # typed cache is a follow-up (CachedManufacturingOrder lookup at the
    # response builder, similar to how customer_name is resolved for
    # the fulfill card).
    columns = [
        DataTableColumn(key="group", header="Group", sortable=True),
        DataTableColumn(key="mo_id", header="MO", sortable=True),
        DataTableColumn(key="action", header="Action"),
        DataTableColumn(key="item", header="Item"),
        DataTableColumn(key="sku", header="SKU"),
        DataTableColumn(key="qty", header="Qty", align="right"),
    ]
    if has_batch_signal:
        columns.append(DataTableColumn(key="batch", header="Batch"))
    if has_serial_signal:
        columns.append(DataTableColumn(key="serials", header="Serials"))
    columns.extend(
        [
            DataTableColumn(key="status", header="Status", sortable=True),
            DataTableColumn(key="error", header="Error"),
        ]
    )

    with (
        PrefabApp(
            state=state,
            css_class="p-4",
        ) as app,
        Column(gap=4),
    ):
        with Row(gap=2):
            H3(content="Batch Recipe Edits")
            Badge(label=mode_label, variant=mode_variant)
            Badge(label=f"{total} ops", variant="outline")

        with Row(gap=4):
            Metric(label="Total", value=str(total))
            if not is_preview:
                Metric(label="Success", value=str(success))
                Metric(label="Failed", value=str(failed))
                Metric(label="Skipped", value=str(skipped))

        # One big table with all ops, grouped visually by the group column.
        # ``Item`` shows the canonical Katana-UI display name (parent / value1
        # / value2) when the upstream caller resolved a variant; ``SKU`` keeps
        # the raw SKU as a secondary identity column for ops + scripts.
        # The ``Qty`` / ``Batch`` / ``Serials`` columns carry the per-row
        # diff overlay (old -> new) so the agent can verify each sub-op's
        # effect before clicking Execute.
        DataTable(
            columns=columns,
            rows="{{ rows }}",
            search=True,
            **_paginate(len(flat_rows), page_size=25),
        )

        if warnings:
            Muted(content=f"Warnings ({len(warnings)}):")
            for w in warnings:
                Text(content=f"- {w}")

        Text(content=message)

        # Action buttons
        if is_preview and apply_action is not None:
            _render_apply_button_row(
                confirm_label="Execute batch",
                apply_action=apply_action,
                cancel_action=cancel_action,
                disabled=False,
            )
        elif failed > 0:
            # Open-ended: the agent has to triage which failures are
            # retryable, surface the root cause, and suggest specific
            # corrective tool calls — that's UpdateContext, not a
            # deterministic CallTool.
            with Row(gap=2):
                Button(
                    label="Review failed ops",
                    variant="outline",
                    on_click=UpdateContext(
                        content=(
                            "List the failed sub-operations from the last "
                            "batch update and suggest recovery steps. Look "
                            "at the per-row error messages in the batch "
                            "result and recommend either a retry, a manual "
                            "correction, or skipping the op."
                        ),
                    ),
                )
        else:
            # Verification is judgment-driven (which MOs to re-check,
            # which fields), so it's UpdateContext as well.
            with Row(gap=2):
                Button(
                    label="Verify recipes",
                    variant="outline",
                    on_click=UpdateContext(
                        content=(
                            "Verify the updated manufacturing order recipes. "
                            "Pick the MOs touched by the batch update, "
                            "fetch each recipe via "
                            "get_manufacturing_order_recipe, and confirm "
                            "the changes landed correctly."
                        ),
                    ),
                )

    return app


# ============================================================================
# Generic Apply-Result UIs
# ============================================================================


def build_apply_success_ui(
    *,
    title: str,
    summary_lines: list[str],
    katana_url: str | None = None,
) -> PrefabApp:
    """Generic success card for an applied (non-preview) write operation.

    ``title`` is the card title (e.g. ``"Sales order #WEB1001 fulfilled"``).
    ``summary_lines`` are rendered verbatim as ``Text`` rows in the card
    body. ``katana_url``, when set, surfaces a "View in Katana" link button
    in the footer.
    """
    with PrefabApp(state={}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=title)
            Badge(label="APPLIED", variant="default")

        with CardContent(), Column(gap=2):
            for line in summary_lines:
                Text(content=line)

        if katana_url:
            with CardFooter(), Row(gap=2):
                Button(
                    label="View in Katana",
                    variant="outline",
                    on_click=OpenLink(url=katana_url),
                )
    return app


def build_apply_error_ui(
    *,
    operation: str,
    error_message: str,
    hint: str | None = None,
) -> PrefabApp:
    """Generic error card for a failed (non-preview) write operation.

    Surfaces the actual error reason verbatim — closes #545 by ensuring
    the apply error is never swallowed by a static "failed" string.
    ``operation`` is a human-readable phrase like
    ``"Fulfilling sales order #WEB1001"``. ``hint``, when set, renders
    a remediation suggestion (e.g. ``"Check the supplier ID"``).
    """
    with PrefabApp(state={}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"{operation} failed")
            Badge(label="ERROR", variant="destructive")

        with CardContent(), Column(gap=2):
            with Alert(variant="destructive", icon="circle-alert"):
                AlertTitle(content="Error")
                AlertDescription(content=error_message)
            if hint:
                Muted(content=hint)
    return app
