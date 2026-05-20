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
``href`` pointing at the Katana page, not as plain ``Text`` or a
``SendMessage`` button that asks the agent to surface the URL.

A real anchor tag is a one-click path to the source of truth, costs
nothing in agent tokens or chat noise, and stays correct regardless
of which host renders the iframe. The variant card uses this pattern
twice (parent product/material on the title; default supplier in
the reference section); future card work should follow the same
shape. If a field corresponds to a Katana entity not yet in
``EntityKind``, add the path template in ``web_urls.py`` and wire
the link — don't fall back to ``SendMessage`` indirection.

The agent-prompt rail (``SendMessage(...)``) is reserved for follow-up
*actions* that need the agent to invoke another tool (e.g.
``Check Inventory`` → triggers ``check_inventory`` for the SKU). It's
the wrong primitive for "open this URL".
"""

from __future__ import annotations

from typing import Any, Literal

from babel.numbers import format_currency
from prefab_ui.actions import Action, SetState, ShowToast
from prefab_ui.actions.mcp import CallTool, SendMessage, UpdateContext
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

from katana_mcp.tools.tool_result_utils import BLOCK_WARNING_PREFIX
from katana_mcp.web_urls import EntityKind, katana_web_url


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
# The rationale for the chat-message rail lives in ADR-0015; the
# Confirm-then-iframe-handles-everything UX in ADR-0016.
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
    "etc.), the card has Confirm/Cancel buttons the user clicks. Do NOT "
    "re-narrate the card or ask for confirmation in chat — the buttons "
    "handle that. End your turn after the preview response. If you later "
    "receive a chat message starting with ``Apply: call <tool>(...)`` or "
    "``Cancel: do not apply ...``, that is a button click from a previous "
    "preview: for Apply re-issue the tool call exactly as written; for "
    "Cancel acknowledge briefly without re-issuing."
)


# Coaching text for tools using the direct-apply rail (Confirm button fires
# ``tools/call`` directly + iframe pushes the structured result back via
# ``ui/update-model-context``). The agent does not re-issue the call — it
# receives the apply result automatically on its next turn. See
# ``docs/adr/0016-direct-apply-confirm-button-rail.md`` (forthcoming).
#
# Same no-iframe-first lead as PREVIEW_APPLY_COACHING (see #648).
PREVIEW_APPLY_DIRECT_COACHING = (
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
    "applied. End your turn after the preview response. If you receive a "
    "chat message starting with ``Cancel: do not apply ...``, the user "
    "opted out — acknowledge briefly without re-issuing."
)


def with_preview_coaching(fn: Any, *, direct: bool = False) -> str:
    """Build a FastMCP tool description by appending preview→apply coaching
    to the function's docstring.

    Two coaching variants:

    - ``direct=False`` (default): tools using the SendMessage rail. Confirm
      fires a ``Apply: call <tool>(...)`` chat message; agent re-issues.
    - ``direct=True``: tools using the direct-apply rail. Confirm fires
      ``tools/call`` directly and pushes the result via
      ``ui/update-model-context``; agent does not re-issue.

    Most callers should use :func:`register_preview_tool` rather than
    calling this directly.
    """
    coaching = PREVIEW_APPLY_DIRECT_COACHING if direct else PREVIEW_APPLY_COACHING
    base = (fn.__doc__ or "").strip()
    return f"{base}\n\n{coaching}" if base else coaching


def register_preview_tool(
    mcp: Any,
    fn: Any,
    *,
    tags: set[str],
    annotations: Any,
    meta: Any = None,
    direct: bool = False,
) -> None:
    """Register a preview-mode write tool with standard coaching applied.

    Set ``direct=True`` for tools whose preview UI uses the direct-apply
    rail (Confirm button fires ``tools/call`` directly and pushes the
    structured result back via ``ui/update-model-context``). Default
    ``direct=False`` uses the SendMessage rail (Confirm fires a chat
    ``Apply: call ...`` for the agent to re-issue).
    """
    mcp.tool(
        description=with_preview_coaching(fn, direct=direct),
        tags=tags,
        annotations=annotations,
        meta=meta,
    )(fn)


def _build_apply_message(tool_name: str, args: dict[str, Any]) -> str:
    """Format the SendMessage text the Confirm button emits to prompt the
    agent to re-issue the apply tool call.

    Shape (uniform across all preview-mode write tools)::

        Apply: call <tool_name>(<key>=<value>, ..., preview=False)

    The message is human-readable and machine-parseable: the agent's tool
    description coaches it to recognize the ``Apply:`` prefix and re-invoke
    ``<tool_name>`` with the inlined args verbatim. ``preview=False`` is
    placed last regardless of where ``preview`` appears in ``args.items()``
    iteration order — for ``ConfirmableRequest`` subclasses the base-class
    ``preview`` field can appear in the middle, but the agent should read
    a stable trailing ``, preview=False)``.

    ``args`` comes from ``request.model_dump(mode="json")``, so values are
    already JSON primitives (str, None, bool, int/float, list, dict) — we
    can use built-in ``repr`` for byte-identical Python-source rendering.
    """
    body = ", ".join(
        f"{key}={value!r}" for key, value in args.items() if key != "preview"
    )
    suffix = "preview=False"
    inner = f"{body}, {suffix}" if body else suffix
    return f"Apply: call {tool_name}({inner})"


def _build_apply_action(
    confirm_tool: str | None,
    confirm_request: BaseModel | None,
) -> list[Action] | None:
    """Construct the Confirm-button click action, or ``None`` when both
    inputs are ``None``.

    The action does **not** call the apply tool directly. By MCP spec, an
    iframe-initiated ``tools/call`` returns its result to the iframe, not to
    the agent's context — so the agent would never see the structured apply
    response. Instead, the click marks the preview card as ``pending`` and
    sends a ``SendMessage`` instructing the agent to re-issue the call. The
    agent then makes the real tool call through its own tool-calling loop
    and gets the full structured response back.

    See ``docs/adr/0015-confirmation-pattern-for-write-tools.md`` for the
    architectural rationale.

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
            f"Without that field the SendMessage would tell the agent to "
            f"re-issue {confirm_tool} with an unrecognized preview=False "
            f"argument, failing validation downstream."
        )
    args["preview"] = False
    return [
        SetState("pending", True),
        SendMessage(_build_apply_message(confirm_tool, args)),
    ]


def _build_apply_action_direct(
    confirm_tool: str | None,
    confirm_request: BaseModel | None,
    *,
    extra_on_success: list[Action] | None = None,
) -> list[Action] | None:
    """Construct the direct-apply Confirm-button click action chain.

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

    See ``docs/adr/0016-direct-apply-confirm-button-rail.md`` (forthcoming)
    for the architectural rationale; supersedes ADR-0015 for tools that
    opt into this rail.

    ``confirm_tool`` and ``confirm_request`` must be both set or both
    ``None`` (the latter for builders that render their non-preview branch).
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
            f"_build_apply_action_direct requires a request model with a "
            f"`preview` field; {type(confirm_request).__name__} has none."
        )
    args["preview"] = False
    # The on_success chain runs the caller's extras BEFORE the generic
    # flags so a builder that pushes RESULT.actions into a state slot (e.g.
    # the modification card binding ``state.plan_actions`` for live-tick row
    # updates) sees its row data land before the iframe morphs to its
    # ``applied=True`` rendering.
    on_success: list[Action] = [
        *(extra_on_success or []),
        SetState("pending", False),
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
    "Cancelled" pill appears) and sends a ``SendMessage`` so the agent
    knows the user opted out. The agent's tool description coaches it to
    acknowledge briefly and move on without re-issuing.

    ``operation_label`` is a human-readable phrase like ``"the fulfillment"``
    or ``"that preview"`` — embedded in the SendMessage text so the agent
    has enough context to acknowledge specifically.
    """
    return [
        SetState("cancelled", True),
        SendMessage(f"Cancel: do not apply {operation_label}."),
    ]


def _render_apply_button_row(
    *,
    confirm_label: str,
    apply_action: list[Action] | None,
    cancel_action: list[Action],
    disabled: bool = False,
    direct_apply: bool = False,
) -> None:
    """Render the preview-card button row with state-aware visuals.

    States driven by iframe state:

    - **Default** — Confirm + Cancel buttons enabled.
    - **Pending…** — pill rendered, both buttons disabled. Set on click for
      both rails: SendMessage rail uses it as the re-issue handoff signal;
      direct-apply rail uses it as the in-flight click guard so a
      double-click cannot fire two applies. Cleared in on_success /
      on_error for direct rail; persists for SendMessage rail (the agent
      re-issue replaces the card).
    - **Applied** — pill rendered, both buttons disabled. Direct-apply rail
      only (``direct_apply=True``); apply succeeded and the iframe morphed.
    - **Error** — pill rendered, both buttons disabled. Direct-apply rail
      only; apply failed. The error reason is in iframe state and was
      pushed to the agent via ``ui/update-model-context``.
    - **Cancelled** — pill rendered, both buttons disabled, after Cancel
      click.

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
    # State machine (direct-apply rail):
    # - Preview:           ``Confirm Changes`` (default, + loader icon
    #                      ``loader`` on the pending replacement) →
    #                      fires apply
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
    #
    # The SendMessage-rail (``direct_apply=False``) variant only
    # transitions Preview → Pending; the agent re-issue replaces the
    # card so applied/error/cancelled are out-of-process.
    with Row(gap=2):
        if direct_apply:
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
        else:
            # SendMessage rail — simpler state machine, only
            # Preview ↔ Pending ↔ Cancelled visible (agent re-issue
            # replaces the card for terminal apply outcomes).
            with If("pending"):
                Button(
                    label="Pending…",
                    variant="default",
                    icon="loader",
                    disabled=True,
                )
            with Elif("cancelled"):
                Button(label="Cancelled", variant="outline", disabled=True)
            with Else():
                Button(
                    label=confirm_label,
                    variant="default",
                    on_click=apply_action,
                    disabled=Rx("pending") | Rx("cancelled"),
                )
        # Cancel button — disabled in all terminal states so the row
        # width stays constant (two buttons always visible). Cancel
        # only does anything in Preview.
        cancel_locked: Any = Rx("pending") | Rx("cancelled")
        if direct_apply:
            cancel_locked = cancel_locked | Rx("applied") | Rx("error")
        Button(
            label="Cancel",
            variant="outline",
            on_click=cancel_action,
            disabled=cancel_locked,
        )


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
    - Sortable, searchable, paginated DataTable
    - Row-click fires CallTool to get_variant_details, renders in Slot
    - Summary badges for query and count

    When ``total_count == 0``, drops the DataTable / drill-down Slot /
    "Check inventory" button — they all reference nonexistent results — and
    renders a friendly hint suggesting partial-SKU / name fallbacks. Closes
    #470.
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
            paginated=True,
            pageSize=20,
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

        with Row(gap=2):
            Button(
                label="Check inventory for search results",
                variant="outline",
                on_click=SendMessage(
                    "Check inventory levels for the items in my search results"
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
    rate = variant.get("purchase_uom_conversion_rate")
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
    """
    sku = variant.get("sku", "")
    Button(
        label="Check Inventory",
        variant="outline",
        on_click=SendMessage(f"Check inventory for SKU {sku}"),
    )
    Button(
        label="Create Purchase Order",
        variant="outline",
        on_click=SendMessage(f"Draft a purchase order for SKU {sku}"),
    )
    if variant.get("type") == "material" and variant.get("id"):
        Button(
            label="List MOs Using This",
            variant="outline",
            on_click=SendMessage(
                f"List manufacturing orders that use variant_id {variant['id']}"
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


def _item_header_section(item: dict[str, Any]) -> None:
    """Render item card header: title (linked to Katana page), type badge,
    and status pills.

    Title wraps in a real ``Link`` to ``katana_url`` so clicking opens
    the Katana product / material / service page directly — same
    convention as the variant card (see module docstring on linking
    Katana entities).

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
        if item_type:
            Badge(label=str(item_type), variant="secondary")
        if item.get("is_archived"):
            Badge(label="Archived", variant="secondary")

    # Status pills row. Order chosen to match the agent's typical
    # decision sequence — sellable first (can this be sold?), then
    # producible (can this be made?), then tracking flags (will I
    # need to specify a batch / serial when transacting?).
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


def _item_metrics_section(item: dict[str, Any]) -> None:
    """Render Tier 2 — decision metrics as text rows (not Metric components).

    Items typically have ≤3 numeric facts (variant count, lead time, MOQ),
    so the Metric layout would be visually heavy for a sparse row. Plain
    text rows still give the agent the facts without competing visually
    with the more important variants table below.
    """
    variants = item.get("variants") or []
    Text(content=f"Variants: {len(variants)}")
    if item.get("lead_time") is not None:
        Text(content=f"Lead Time: {item['lead_time']} days")
    if item.get("minimum_order_quantity") is not None:
        Text(content=f"Min Order Qty: {item['minimum_order_quantity']}")


def _item_supplier_line(item: dict[str, Any]) -> None:
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
    """
    supplier = item.get("supplier")
    nested_name = supplier.get("name") if isinstance(supplier, dict) else None
    nested_id = supplier.get("id") if isinstance(supplier, dict) else None

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
    fallback_sid = item.get("default_supplier_id")
    if fallback_sid:
        supplier_url = katana_web_url("supplier", fallback_sid)
        if supplier_url:
            with Row(gap=1):
                Text(content="Default Supplier:")
                Link(
                    content=f"#{fallback_sid}",
                    href=supplier_url,
                    target="_blank",
                )
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
        paginated=True,
        pageSize=20,
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


def _item_reference_section(item: dict[str, Any]) -> None:
    """Render Tier 3 reference data: UoM, category, purchase UoM,
    default supplier (Linked), configs, additional info, and the
    nested variants table.
    """
    if item.get("uom"):
        Text(content=f"UoM: {item['uom']}")
    if item.get("category_name"):
        Text(content=f"Category: {item['category_name']}")
    _variant_purchase_uom_line(item)
    _item_supplier_line(item)
    _item_configs_section(item)
    additional_info = item.get("additional_info")
    if additional_info:
        Text(content=f"Notes: {additional_info}")
    _item_variants_table(item)


def _item_footer_section(item: dict[str, Any]) -> None:
    """Render Tier 4 action buttons keyed off item type.

    All buttons emit ``SendMessage`` invocations of other tools —
    correct use of the agent-prompt rail per the module docstring
    convention (composes context the agent fills in, vs. a deterministic
    URL which would be a Link). The title's external Link already covers
    "open in Katana", so no footer button for that.
    """
    item_id = item.get("id")
    item_type = item.get("type") or "item"
    if item_id is None:
        return

    if item_type == "material":
        Button(
            label="Create Purchase Order",
            variant="outline",
            on_click=SendMessage(f"Draft a purchase order for material_id {item_id}"),
        )
        Button(
            label="List MOs Using This",
            variant="outline",
            on_click=SendMessage(
                f"List manufacturing orders that use material_id {item_id}"
            ),
        )
    elif item_type == "product" and item.get("is_producible"):
        Button(
            label="Create Manufacturing Order",
            variant="outline",
            on_click=SendMessage(
                f"Draft a manufacturing order for product_id {item_id}"
            ),
        )

    Button(
        label="Modify Item",
        variant="outline",
        on_click=SendMessage(
            f"I want to modify {item_type} {item_id} — what should I change?"
        ),
    )


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
    - **Tier 4 — Actions**: sub-type-specific SendMessage buttons:
      ``Create Purchase Order`` + ``List MOs Using This`` (materials),
      ``Create Manufacturing Order`` (producible products),
      ``Modify Item`` (all). No "View in Katana" footer button —
      the title link replaces it.

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
            _item_metrics_section(item)
            Separator()
            _item_reference_section(item)

        with CardFooter(), Row(gap=2):
            _item_footer_section(item)
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
        DataTable(
            columns=[
                DataTableColumn(key="location_name", header="Location"),
                # ``location_name`` is allowed to be ``None`` when the
                # location-cache lookup misses; the ID column stays as
                # an always-present fallback so rows are never
                # unidentifiable. Same shape the pre-#549 card had.
                DataTableColumn(key="location_id", header="ID", align="right"),
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
    Button(
        label="Create PO",
        variant="outline",
        on_click=SendMessage(f"Draft a purchase order for {identity}"),
    )
    Button(
        label="View Variant Details",
        variant="outline",
        on_click=SendMessage(f"Get variant details for {identity}"),
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

        DataTable(
            columns=[
                DataTableColumn(key="sku", header="SKU", sortable=True),
                # Variant ID is the row's other primary identifier. A
                # not-found stub from a variant-ID lookup has empty SKU
                # and empty product_name — without this column the row
                # has no visible identity at all and the user can't tell
                # which input was missing. SKU-bearing rows also get to
                # show their variant_id so downstream tools (which key
                # on variant_id) can copy it directly off the table.
                DataTableColumn(
                    key="variant_id", header="Variant ID", sortable=True, align="right"
                ),
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
            ],
            rows="{{ items }}",
            search=True,
            paginated=True,
            pageSize=25,
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
                    DataTableColumn(key="location_id", header="ID", align="right"),
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
            paginated=True,
        )

        with Row(gap=2):
            Button(
                label="Create Restock Orders",
                variant="default",
                on_click=SendMessage(
                    "Create purchase orders to restock all low-stock items"
                ),
            )
            Button(
                label="Check Inventory",
                variant="default",
                on_click=SendMessage(
                    "Check inventory details for these low-stock items"
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
                Badge(label=f"Location {location_id}", variant="outline")
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
            # First resolved SKU drives both follow-up actions; falls back
            # to variant_id when the variant has no SKU (per the documented
            # null-SKU invariant).
            first_handle: str | int = ""
            if items:
                first_handle = items[0].get("sku") or items[0].get("variant_id") or ""
            Button(
                label="Check Current Inventory",
                variant="outline",
                on_click=SendMessage(
                    f"Check current inventory for {first_handle}"
                    if first_handle
                    else "Check current inventory"
                ),
            )
            Button(
                label="View Movements",
                variant="outline",
                on_click=SendMessage(
                    f"Show inventory movements for SKU {first_handle}"
                    if first_handle
                    else "Show recent inventory movements"
                ),
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
    DataTableColumn(key="new_value", header="New Value"),
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


def _format_money(amount: float | int | None, currency: str | None) -> str:
    """Format a Metric ``Total`` value using ISO 4217 currency-aware rules.

    Delegates to :func:`babel.numbers.format_currency` so the rendered string
    picks up the right symbol, decimal-digit count, and grouping for the
    currency (``$1,500.00`` for USD, ``€1,500.00`` for EUR, ``¥1,500`` for
    JPY with no decimals). Integer ``amount`` is passed through unchanged
    — Babel handles ``int`` and ``float`` identically.

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
    """
    out: dict[str, FieldChangeView] = {}
    for action in actions:
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

    Wire shape allows None, str, int, float, bool, list, dict; the entity
    view renders each as text. Strings, numbers, and booleans render
    directly; lists/dicts fall back to ``repr`` (rare — the diff producer
    avoids nested types). None renders as ``(unset)`` so a transition
    from blank to populated reads naturally as ``(unset) → Net-30``.
    """
    if value is None:
        return "(unset)"
    if isinstance(value, bool):
        return "yes" if value else "no"
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


# Initial state slots written by the direct-apply rail's Confirm/Cancel
# action chains. Builders that opt into the rail seed these to ``False`` /
# ``None`` so the iframe's If/Elif blocks have something to bind to before
# the first click. ``SetState`` mutations from
# ``_build_apply_action_direct`` / ``_build_cancel_action`` flip them.
_DIRECT_APPLY_STATE_INIT: dict[str, Any] = {
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
        state.update(_DIRECT_APPLY_STATE_INIT)
        apply_action = _build_apply_action_direct(confirm_tool, confirm_request)
        cancel_action = _build_cancel_action("the stock adjustment")

    location_id = response.get("location_id")
    adj_id = response.get("id")
    reason = response.get("reason")

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content="Stock Adjustment")
            if adj_id is not None:
                Badge(label=f"#{adj_id}", variant="outline")
            if location_id is not None:
                Badge(label=f"Location {location_id}", variant="outline")
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
                    direct_apply=True,
                )
            elif response.get("katana_url"):
                Button(
                    label="View in Katana",
                    variant="outline",
                    on_click=SendMessage(
                        f"Open {response['katana_url']} in the Katana web UI"
                    ),
                )
    return app


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
    diff_rows: list[dict[str, str]] = []
    for field, label in (
        ("stock_adjustment_number", "Number"),
        ("stock_adjustment_date", "Date"),
        ("location_id", "Location ID"),
        ("reason", "Reason"),
        ("additional_info", "Additional Info"),
    ):
        value = response.get(field)
        if value is not None:
            diff_rows.append({"field": label, "new_value": str(value)})

    state: dict[str, Any] = {"diff_rows": diff_rows}
    apply_action: list[Action] | None = None
    cancel_action: list[Action] | None = None
    if is_preview:
        state.update(_DIRECT_APPLY_STATE_INIT)
        apply_action = _build_apply_action_direct(confirm_tool, confirm_request)
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
                    direct_apply=True,
                )
            elif response.get("katana_url"):
                Button(
                    label="View in Katana",
                    variant="outline",
                    on_click=SendMessage(
                        f"Open {response['katana_url']} in the Katana web UI"
                    ),
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
        state = dict(_DIRECT_APPLY_STATE_INIT)
        apply_action = _build_apply_action_direct(confirm_tool, confirm_request)
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
                Metric(
                    label="Location",
                    value=str(response.get("location_id") or "—"),
                )
                Metric(
                    label="Rows",
                    value=str(response.get("row_count", 0)),
                )

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
                    direct_apply=True,
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
    next_action_buttons: tuple[tuple[str, str], ...] = (),
    applied_verb: str = "created",
) -> None:
    """Tier 4: CardFooter for a preview/apply card.

    ``applied_verb`` controls the muted body line in applied state — create
    cards default to ``"created"`` ("Purchase Order created."); modify cards
    should pass ``"applied"`` ("Purchase Order Modify applied.") so the user-
    visible copy matches the actual operation.

    The applied-state View-in-Katana link and the per-entity next-action
    SendMessage buttons bind to ``{{ result.<field> }}`` templates so they
    work in both entry paths:

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
                direct_apply=True,
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
                for label, send_text in next_action_buttons:
                    Button(
                        label=label,
                        variant="outline",
                        on_click=SendMessage(send_text),
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
                direct_apply=True,
            )


ItemAction = Literal["Created", "Updated", "Deleted"]


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
    :func:`_build_apply_action_direct` populates it via
    ``SetState("result", RESULT)`` before flipping ``applied=True``.
    """
    applied = not response.get("is_preview", True)
    state: dict[str, Any] = {
        "applied": applied,
        "pending": False,
        "cancelled": False,
        "error": None,
    }
    if applied:
        state["result"] = response
    return state


def _render_party_line(
    label: str,
    *,
    name: str | None,
    entity_id: int | None,
    entity_kind: EntityKind | None = None,
) -> None:
    """Render a 'Supplier:' / 'Customer:' / 'Location:' line.

    When ``entity_kind`` resolves to a Katana web URL and a ``name`` is
    present, renders ``<label>: <Link name>`` so users can click through
    to the source-of-truth entity (mirrors the variant card's parent and
    default-supplier link pattern; matches this module's "Link Katana
    entities wherever possible" convention). Falls back to plain text
    otherwise. Skips entirely when ``entity_id`` is None.
    """
    if entity_id is None:
        return
    url = katana_web_url(entity_kind, entity_id) if entity_kind else None
    if name and url:
        with Row(gap=1):
            Text(content=f"{label}:")
            Link(content=name, href=url, target="_blank")
    elif name:
        Text(content=f"{label}: {name} (ID: {entity_id})")
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
    - The Total Metric uses the post-change ``total_cost`` from the
      response payload — line-item adds/removes already propagated into
      the response's recomputed total by the dispatcher.

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

    apply_action = _build_apply_action_direct(confirm_tool, confirm_request)
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
                (
                    "Receive Items",
                    "Receive items for purchase order {{ result.id }}",
                ),
                (
                    "Verify Document",
                    "Verify a supplier document against PO {{ result.id }}",
                ),
            ),
        )
    return app


def _summarize_apply_outcome(
    actions: list[dict[str, Any]],
) -> tuple[str, str]:
    """Bucket a modify response's action outcomes for the header Badge.

    Returns ``(state_label, badge_variant)``. Variants align with the
    create-card Tier 1 vocabulary (``default`` / ``secondary`` /
    ``destructive`` / ``outline``).

    - **Empty actions**: ``APPLIED`` / default. A modify/delete plan
      can legitimately produce zero actions (no-op patch, or all
      requested changes turned out to be unchanged). The card has
      nothing to "fail" — render success chrome, not destructive.
    - **All succeeded** (any ``verified`` value): ``APPLIED`` / default.
      Note: per the agreed design, verification mismatch is surfaced
      at the card-level header alone; per-field decoration ignores
      ``verified`` because most users don't differentiate.
    - **All failed**: ``FAILED`` / destructive.
    - **Mixed**: ``PARTIAL FAILURE`` / destructive.
    """
    if not actions:
        return "APPLIED", "default"
    succeeded = sum(1 for a in actions if a.get("succeeded") is True)
    failed = sum(1 for a in actions if a.get("succeeded") is False)
    if failed == 0 and succeeded > 0:
        return "APPLIED", "default"
    if succeeded == 0 and failed > 0:
        return "FAILED", "destructive"
    return "PARTIAL FAILURE", "destructive"


def _init_modify_card_state(response: dict[str, Any]) -> dict[str, Any]:
    """Seed iframe state for a modify card.

    Mirrors :func:`_init_create_card_state` but adds nothing extra — the
    modify card uses the same applied/pending/cancelled/error booleans
    and the same ``result`` slot on the standalone-applied path so the
    direct-apply on_success chain (``SetState("result", RESULT)``)
    populates the post-apply data uniformly.
    """
    return _init_create_card_state(response)


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
    actions = response.get("actions") or []
    is_preview = bool(response.get("is_preview", True))
    entity_id = response.get("entity_id")
    # ``prior_state`` arrives in the wire shape from ``serialize_for_prior_state``
    # (``RegularPurchaseOrder.to_dict()`` etc.) — ``order_no``, ``total``,
    # ``additional_info``, nested ``supplier``. Normalize to the response
    # shape the entity-view renderer reads so unchanged-field rows
    # surface real values in the rendered card.
    prior_state = _normalize_po_prior_state(response.get("prior_state"))
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
    entity = {**prior_state, **{k: v for k, v in response.items() if v is not None}}
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
    changes_by_field = _index_changes_by_field(actions)

    apply_action = _build_apply_action_direct(confirm_tool, confirm_request)
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

    with (
        PrefabApp(state=_init_modify_card_state(response), css_class="p-4") as app,
        Card(),
    ):
        # Delete: applied-state copy reads "Deleted" / "deleted"; modify
        # and correct read "Applied" / "applied". The verb_label drives
        # the title-suffix mapping so e.g. ``"Purchase Order Modify"``
        # title in preview becomes ``"Purchase Order Applied"`` in the
        # rendered applied state — not the misleading "Created" the
        # shared helpers default to.
        if verb_label == "Delete":
            applied_title_suffix = "Deleted"
            applied_state_label = "DELETED"
            applied_verb = "deleted"
        else:
            applied_title_suffix = "Applied"
            applied_state_label = "APPLIED"
            applied_verb = "applied"
        applied_state_variant = "default"

        # On the standalone-applied path (is_preview=False), let the
        # actual outcome drive both the state label AND the badge
        # variant — so a fully-failed apply reads "FAILED" with the
        # destructive (red) variant, not "APPLIED" with the success
        # (green) variant. Partial failures also surface in the
        # destructive variant. The title suffix and footer verb track
        # the outcome too — a failed delete reads "Purchase Order
        # Failed" / "failed.", NOT "Purchase Order Deleted" / "deleted."
        # which would contradict the FAILED badge.
        if not is_preview:
            outcome_label, outcome_variant = _summarize_apply_outcome(actions)
            if outcome_label != "APPLIED":
                applied_state_label = outcome_label
                applied_state_variant = outcome_variant
                if outcome_label == "FAILED":
                    applied_title_suffix = "Failed"
                    applied_verb = "failed"
                else:  # PARTIAL FAILURE
                    applied_title_suffix = "Partially Applied"
                    applied_verb = "partially applied"

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
      ``location_name``), warnings.
    - Tier 4: Confirm/Cancel (preview) or View in Katana + Fulfill Order
      (applied).
    """
    order_number = response.get("order_number") or "N/A"
    status = response.get("status")
    total = response.get("total")
    currency = response.get("currency")
    item_count = response.get("item_count")
    delivery_date = response.get("delivery_date")

    apply_action = _build_apply_action_direct(confirm_tool, confirm_request)
    cancel_action = _build_cancel_action("that sales order")

    with (
        PrefabApp(state=_init_create_card_state(response), css_class="p-4") as app,
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
                name=None,  # SalesOrderResponse has no location_name
                entity_id=response.get("location_id"),
            )
            block_warnings = _render_warnings_block(response.get("warnings"))
        _render_preview_footer(
            title_prefix="Sales Order",
            block_warnings=block_warnings,
            confirm_label="Confirm & Create Sales Order",
            apply_action=apply_action,
            cancel_action=cancel_action,
            next_action_buttons=(
                ("Fulfill Order", "Fulfill sales order {{ result.id }}"),
            ),
        )
    return app


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
    - Tier 2: Planned Qty, Deadline.
    - Tier 3: variant (sku + id), location ID, created date, notes
      (additional_info), warnings.
    - Tier 4: Confirm/Cancel (preview) or View in Katana + Complete Order
      (applied).
    """
    order_number = response.get("order_no") or "N/A"
    status = response.get("status")
    variant_id = response.get("variant_id")
    sku = response.get("sku")
    planned_quantity = response.get("planned_quantity")
    location_id = response.get("location_id")
    order_created_date = response.get("order_created_date")
    production_deadline_date = response.get("production_deadline_date")
    additional_info = response.get("additional_info")

    apply_action = _build_apply_action_direct(confirm_tool, confirm_request)
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
            if planned_quantity is not None or production_deadline_date:
                with Row(gap=4):
                    if planned_quantity is not None:
                        Metric(label="Planned Qty", value=str(planned_quantity))
                    if production_deadline_date:
                        Metric(
                            label="Deadline",
                            value=_iso_date_only(production_deadline_date),
                        )
            if variant_id is not None or sku:
                if sku and variant_id is not None:
                    Text(content=f"Variant: {sku} (ID: {variant_id})")
                elif sku:
                    Text(content=f"Variant: {sku}")
                else:
                    Text(content=f"Variant ID: {variant_id}")
            if location_id is not None:
                Text(content=f"Location ID: {location_id}")
            if order_created_date:
                Text(content=f"Created: {_iso_date_only(order_created_date)}")
            if additional_info:
                Text(content=f"Notes: {additional_info}")
            block_warnings = _render_warnings_block(response.get("warnings"))
        _render_preview_footer(
            title_prefix="Manufacturing Order",
            block_warnings=block_warnings,
            confirm_label="Confirm & Create Manufacturing Order",
            apply_action=apply_action,
            cancel_action=cancel_action,
            next_action_buttons=(
                (
                    "Complete Order",
                    "Complete manufacturing order {{ result.id }}",
                ),
            ),
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


def _render_inventory_updates(
    response: dict[str, Any], *, label: str = "Inventory Changes:"
) -> None:
    """Render inventory update list if present."""
    if response.get("inventory_updates"):
        Muted(content=label)
        for update in response["inventory_updates"]:
            Text(content=f"  {update}")


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

    Three metrics:
    - **Rows** — count of rows being fulfilled (always present, never zero
      on a real response — the MO branch synthesizes a single-row entry).
    - **Total Qty** — sum of quantities across rows, rendered via ``:g``.
    - **Total Value** — sum of ``row_total`` across rows, formatted via
      babel. Omitted when no row carries a price (MO branch — MOs track
      cost, not price; the cost ledger lives on a separate surface).

    Skipped entirely when the response carries no enrichment
    (back-compat with older payloads that pre-dated #553).
    """
    rows_count = response.get("rows_count")
    if rows_count is None:
        return
    total_qty = response.get("total_quantity")
    total_value = response.get("total_value")
    currency = response.get("currency")
    with Row(gap=4):
        Metric(label="Rows", value=str(rows_count))
        if isinstance(total_qty, int | float):
            Metric(label="Total Qty", value=f"{total_qty:g}")
        if total_value is not None:
            Metric(label="Total Value", value=_format_money(total_value, currency))


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
) -> PrefabApp:
    """Build a fulfillment preview card.

    The "Confirm Fulfillment" button re-invokes ``fulfill_order`` with
    ``preview=False`` and the original ``order_id`` / ``order_type``
    inlined from the response. No LLM round-trip.

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
    raw_order_type = response["order_type"]
    # Direct lookup, not .get() — FulfillOrderResponse declares both fields
    # required; a missing key signals a malformed response dict and we
    # want to fail at preview-build time, not at click time.
    confirm_request = FulfillOrderRequest(
        order_id=response["order_id"],
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

    state = {
        "response": response,
        "fulfilled_rows": fulfilled_rows_display,
        "pending": False,
        "cancelled": False,
    }

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"Fulfill {order_type_display} Order")
            Badge(label=order_number, variant="outline")
            Badge(label=status, variant="secondary")

        with CardContent(), Column(gap=2):
            _render_fulfill_metrics(response)
            _render_inventory_updates(response)
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
            if response.get("inventory_updates"):
                Separator()
            _render_inventory_updates(response, label="Inventory Updates:")
            _render_fulfill_per_row_table(
                fulfilled_rows_display,
                order_type=raw_order_type,
                is_preview=False,
            )

        with CardFooter(), Row(gap=2):
            # Tier 4 actions (#553): two follow-ups. View in Katana wins
            # the primary slot when a deep-link is available (operator's
            # most common next move on a successful fulfill is to verify
            # in the web UI); inventory check stays the secondary action.
            if katana_url:
                Button(
                    label="View in Katana",
                    variant="default",
                    on_click=SendMessage(f"Open {katana_url} in the Katana web UI"),
                )
            Button(
                label="Check Inventory",
                variant="outline",
                on_click=SendMessage("Check current inventory levels"),
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
    - **Tier 2 — Decision metrics**: three Metric widgets — Matched
      count, Discrepant count (variant ``destructive`` when >0), and
      Totals reconciled (``$matched_total of $po_total``) using
      :func:`_format_money` with the PO's currency.
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
    perfect_count = 0
    non_perfect_count = 0
    matched_total = 0.0
    for m in matches:
        if m.get("status") == "perfect":
            perfect_count += 1
            matched_total += (m.get("quantity") or 0) * (m.get("unit_price") or 0)
        else:
            non_perfect_count += 1
    discrepant_count = len(discrepancies) + non_perfect_count
    matched_total_formatted = _format_money(matched_total, currency)
    po_total_formatted = _format_money(po_total, currency)

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
                    on_click=SendMessage(
                        f"Receive items for purchase order {order_id}"
                    ),
                )
            else:
                Button(
                    label="Receive Anyway",
                    variant="outline",
                    on_click=SendMessage(
                        f"Receive items for purchase order {order_id} "
                        "despite discrepancies"
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


def _humanize_snake_case(raw: str) -> str:
    """Convert a snake_case identifier to a Title Case display label."""
    return raw.replace("_", " ").title()


def _verb_label(tool_name: str | None) -> str:
    """Pick the human-readable verb for the modification card title.

    Used to render ``"Modify Product"`` / ``"Delete Product"`` /
    ``"Correct Purchase Order"`` titles correctly across the modification
    rail. ``None`` (or any unrecognized prefix) falls back to "Modify".
    """
    if not tool_name:
        return "Modify"
    return _VERB_DISPLAY.get(tool_name.split("_", 1)[0], "Modify")


# Single column set used by both preview and result modification cards.
# One row per planned action — server-derived ``status_label`` and
# ``summary`` fields land directly here so the apply path's
# ``SetState("plan_actions", RESULT.actions)`` swap preserves shape.
_ACTION_COLUMNS: list[DataTableColumn] = [
    DataTableColumn(key="index", header="#", width="3rem"),
    DataTableColumn(key="operation_label", header="Operation"),
    DataTableColumn(key="target_label", header="Target"),
    DataTableColumn(key="summary", header="Changes"),
    DataTableColumn(key="status_label", header="Status"),
]

_PLAN_ACTIONS_KEY = "plan_actions"
# DataTable.rows requires the mustache template form (``{{ key }}``) for
# state-bound rows — the JS renderer interprets bare strings as the rows
# array itself and crashes with ``t.some is not a function``. Discovered
# via headless apps_dev render tests after #634; the Python pydantic
# field type accepts bare strings, but the wire format only resolves
# mustache references.
_PLAN_ACTIONS_REF = f"{{{{ {_PLAN_ACTIONS_KEY} }}}}"


def _derive_status_label(action: dict[str, Any]) -> str:
    """Compute a status label from raw ``succeeded`` / ``verified`` fields.

    Used as a fallback for action dicts that don't already carry the
    server-derived ``status_label`` (legacy responses, older clients,
    test fixtures). Mirrors
    :func:`katana_mcp.tools._modification._derive_status_label`.
    """
    succeeded = action.get("succeeded")
    if succeeded is None:
        return "PLANNED"
    if succeeded is True:
        verified = action.get("verified")
        if verified is False:
            return "APPLIED (verification mismatch)"
        if verified is True:
            return "APPLIED (verified)"
        return "APPLIED"
    return "FAILED"


def _derive_summary(action: dict[str, Any]) -> str:
    """Fallback summary derivation when the action lacks a server-supplied one."""
    op = str(action.get("operation") or "").lower()
    changes = action.get("changes") or []
    if op.startswith("delete"):
        return "deleted"
    if op.startswith("add") or op.startswith("create"):
        return f"{len(changes)} field(s) set"
    n_changed = sum(
        1 for c in changes if isinstance(c, dict) and not c.get("is_unchanged")
    )
    if n_changed == 0 and changes:
        return f"{len(changes)} field(s) — no change"
    return f"{n_changed} field(s) changed"


def _action_to_row(idx: int, action: dict[str, Any]) -> dict[str, Any]:
    """Project one ActionResult dict into a DataTable row.

    Returns a dict that carries display-only derived fields (``index``,
    ``operation_label``, ``target_label``) on top of the underlying
    ActionResult fields. Pre-populating the same shape both at preview-
    build time and on the apply RESULT means the on_success
    ``SetState("plan_actions", RESULT.actions)`` swap doesn't need any
    transformation — the server's ``status_label``/``summary`` already
    travel on every ActionResult.

    Falls back to local derivation when ``status_label``/``summary`` are
    absent (legacy single-action shape, older response generators, tests).
    """
    target = action.get("target_id")
    return {
        "index": action.get("index") or idx,
        "operation_label": action.get("operation_label")
        or (_humanize_snake_case(str(action.get("operation") or "")) or "Action"),
        "target_label": action.get("target_label")
        or (f"#{target}" if target is not None else "—"),
        "summary": action.get("summary") or _derive_summary(action),
        "status_label": action.get("status_label") or _derive_status_label(action),
        # Pass through the underlying fields so RESULT.actions replacement
        # preserves shape (the server's ActionResults carry these too).
        "operation": action.get("operation"),
        "target_id": target,
        "succeeded": action.get("succeeded"),
        "verified": action.get("verified"),
        "error": action.get("error"),
    }


def _legacy_action(response: dict[str, Any]) -> dict[str, Any] | None:
    """Synthesize a single ActionResult-shaped dict from the legacy shape.

    The legacy single-action response carries top-level ``operation`` +
    ``changes`` (instead of an ``actions`` list). Wrap it as one synthetic
    action so both card builders flow through the same row builder.
    """
    legacy_changes = response.get("changes") or []
    legacy_op = response.get("operation") or ""
    if not legacy_op and not legacy_changes:
        return None
    is_preview = bool(response.get("is_preview"))
    n = len(legacy_changes)
    return {
        "operation": legacy_op,
        "target_id": response.get("entity_id"),
        "changes": legacy_changes,
        "succeeded": None if is_preview else True,
        "verified": None,
        "error": None,
        "status_label": "PLANNED" if is_preview else "APPLIED",
        "summary": f"{n} field(s) changed" if n else "—",
    }


def _actions_to_rows(actions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map ActionResult dicts to DataTable rows for ``state.plan_actions``."""
    return [_action_to_row(idx, action) for idx, action in enumerate(actions, start=1)]


def _count_outcomes(actions: list[dict[str, Any]]) -> tuple[int, int]:
    """Tally ``(succeeded, failed)`` across an action list."""
    s = sum(1 for a in actions if a.get("succeeded") is True)
    f = sum(1 for a in actions if a.get("succeeded") is False)
    return s, f


def build_modification_preview_ui(
    response: dict[str, Any],
    *,
    confirm_request: BaseModel,
    confirm_tool: str,
) -> PrefabApp:
    """Preview card for a :class:`ModificationResponse` with the direct-apply rail.

    Used by every tool that returns a ``ModificationResponse`` from
    ``_modification.py`` — ``modify_*``, ``delete_*``, ``correct_*``.

    The card renders **one DataTable** bound to ``state.plan_actions``
    (one row per planned action: # / Operation / Target / Changes / Status).
    Confirm fires ``tools/call`` directly; the on_success chain pushes
    ``RESULT.actions`` into ``state.plan_actions`` so each row's status
    cell ticks PLANNED → APPLIED/FAILED in place without re-rendering
    the iframe (ADR-0016 direct-apply rail). The iframe also pushes the
    structured result to the agent via ``ui/update-model-context``.
    """
    actions = response.get("actions") or []
    if not actions:
        legacy = _legacy_action(response)
        if legacy is not None:
            actions = [legacy]

    apply_action = _build_apply_action_direct(confirm_tool, confirm_request)
    # NOTE: A live-tick design (rows ticking PLANNED -> APPLIED in place via
    # ``SetState("plan_actions", RESULT.actions)``) was attempted in #634 but
    # turned out to be broken: ``$result`` in the on_success Rx context
    # resolves to the apply tool's ``structured_content`` (a PrefabApp wire
    # envelope from ``make_tool_result``), not to the raw
    # ``ModificationResponse``. ``$result.actions`` therefore doesn't
    # resolve and the SetState was a no-op in production. Caught by Copilot
    # review; verified by the browser harness when its stub was switched to
    # match production shape. Tracked as a follow-up — until then the
    # apply path morphs the card via the existing ``applied=True`` flag.
    entity_type_raw = str(response.get("entity_type") or "entity")
    entity_type_label = _humanize_snake_case(entity_type_raw)
    verb_label = _verb_label(confirm_tool)
    cancel_action = _build_cancel_action(
        f"the {entity_type_raw.replace('_', ' ')} {verb_label.lower()}"
    )

    block_warnings, regular_warnings = _split_warnings(response.get("warnings"))
    n_actions = len(actions)

    state: dict[str, Any] = {
        "pending": False,
        "cancelled": False,
        "applied": False,
        "error": None,
        _PLAN_ACTIONS_KEY: _actions_to_rows(actions),
    }

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            title_suffix = f" — {n_actions} action(s)" if n_actions > 0 else ""
            CardTitle(content=f"{verb_label} {entity_type_label}{title_suffix}")
            entity_id = response.get("entity_id")
            if entity_id is not None:
                Badge(label=f"#{entity_id}", variant="outline")
            Badge(label="PREVIEW", variant="secondary")

        with CardContent(), Column(gap=3):
            if response.get("message"):
                Text(content=response["message"])

            if n_actions > 0:
                DataTable(columns=_ACTION_COLUMNS, rows=_PLAN_ACTIONS_REF)

            if block_warnings or regular_warnings:
                Separator()
                for warning in block_warnings:
                    Badge(label=warning, variant="destructive")
                for warning in regular_warnings:
                    Badge(label=warning, variant="secondary")

            with If("error"):
                Separator()
                with Alert(variant="destructive", icon="circle-alert"):
                    AlertTitle(content="Apply failed")
                    AlertDescription(content="{{ error }}")

        with CardFooter():
            if block_warnings:
                Muted(
                    content="Cannot proceed — see warnings above. No changes have been made."
                )
            else:
                with If("applied"):
                    Muted(
                        content="Changes applied — see status column for per-action outcome."
                    )
                with Elif("error"):
                    Muted(content="Apply failed — see error above.")
                with Elif("cancelled"):
                    Muted(content="Cancelled. No changes were made.")
                with Else():
                    Muted(content="This is a preview. No changes have been made.")

            confirm_label = (
                f"Confirm {n_actions} action(s)" if n_actions > 1 else "Confirm Changes"
            )
            _render_apply_button_row(
                confirm_label=confirm_label,
                apply_action=apply_action,
                cancel_action=cancel_action,
                disabled=bool(block_warnings),
                direct_apply=True,
            )
    return app


def build_modification_result_ui(
    response: dict[str, Any], *, tool_name: str | None = None
) -> PrefabApp:
    """Result card for an *applied* :class:`ModificationResponse`.

    Mirrors :func:`build_modification_preview_ui` but without Confirm/Cancel
    — every action carries its terminal status (APPLIED / APPLIED (verified) /
    APPLIED (verification mismatch) / FAILED) and the card surfaces the
    aggregate outcome plus a "View in Katana" button when a ``katana_url``
    is present (deletes successfully applied null out the URL upstream).

    ``tool_name`` is the registered MCP tool name (e.g. ``"delete_item"``) —
    used to derive the title's verb so a successful delete reads "Product
    Delete" rather than the misleading "Product Modification". Optional
    for backwards compatibility with the legacy single-action shape, which
    falls back to the response's top-level ``operation`` field.
    """
    entity_type_label = _humanize_snake_case(
        str(response.get("entity_type") or "entity")
    )
    actions = response.get("actions") or []
    legacy_op = _humanize_snake_case(str(response.get("operation") or ""))
    if not actions:
        legacy = _legacy_action(response)
        if legacy is not None:
            actions = [legacy]

    success_count, failed_count = _count_outcomes(actions)

    overall_status: str
    overall_variant: Literal["default", "secondary", "outline", "destructive"]
    if failed_count > 0 and success_count > 0:
        overall_status, overall_variant = "PARTIAL FAILURE", "destructive"
    elif failed_count > 0:
        overall_status, overall_variant = "FAILED", "destructive"
    else:
        overall_status, overall_variant = "APPLIED", "default"

    state: dict[str, Any] = {_PLAN_ACTIONS_KEY: _actions_to_rows(actions)}

    # Title verb: prefer the tool-derived verb (works for delete/correct
    # tools); fall back to the legacy single-action ``operation`` field;
    # finally to a neutral "Modification".
    if tool_name:
        title_op = _verb_label(tool_name)
    else:
        title_op = legacy_op or "Modification"

    with PrefabApp(state=state, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"{entity_type_label} {title_op}")
            entity_id = response.get("entity_id")
            if entity_id is not None:
                Badge(label=f"#{entity_id}", variant="outline")
            Badge(label=overall_status, variant=overall_variant)

        with CardContent(), Column(gap=3):
            if response.get("message"):
                Text(content=response["message"])

            if actions:
                Muted(
                    content=(
                        f"{success_count} succeeded, {failed_count} failed "
                        f"of {len(actions)}"
                    )
                )
                DataTable(columns=_ACTION_COLUMNS, rows=_PLAN_ACTIONS_REF)

        if response.get("katana_url"):
            with CardFooter(), Row(gap=2):
                Button(
                    label="View in Katana",
                    variant="outline",
                    on_click=SendMessage(
                        f"Open {response['katana_url']} in the Katana web UI"
                    ),
                )
    return app


# ============================================================================
# Item Created/Updated/Deleted UIs
# ============================================================================


def build_item_mutation_ui(
    item: dict[str, Any],
    action: ItemAction,
) -> PrefabApp:
    """Build a card for item created/updated/deleted responses."""
    with PrefabApp(state={"item": item}, css_class="p-4") as app, Card():
        with CardHeader(), Row(gap=2):
            CardTitle(content=f"Item {action}")
            if item.get("type"):
                Badge(label=str(item["type"]), variant="secondary")

        with CardContent(), Column(gap=2):
            Text(content=f"ID: {item.get('id', 'N/A')}")
            Text(content=f"Name: {item.get('name', 'N/A')}")
            if item.get("sku"):
                Text(content=f"SKU: {item['sku']}")
            _variant_purchase_uom_line(item)
            if item.get("message"):
                Text(content=item["message"])

        with CardFooter(), Row(gap=2):
            if item.get("sku"):
                Button(
                    label="View Details",
                    variant="outline",
                    on_click=SendMessage(f"Get variant details for SKU {item['sku']}"),
                )
            if item.get("sku"):
                Button(
                    label="Check Inventory",
                    variant="outline",
                    on_click=SendMessage(f"Check inventory for SKU {item['sku']}"),
                )
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

    received_date = item.get("received_date")
    row_total = item.get("row_total")
    return {
        "display_name": item.get("display_name") or "",
        "sku": item.get("sku") or "",
        "quantity": _qty_display(),
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

    state: dict[str, Any] = {
        "response": response,
        "received_items": received_items_display,
        "pending": False,
        "cancelled": False,
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
            if response.get("supplier_id"):
                name = response.get("supplier_name")
                Text(
                    content=f"Supplier: {name} (ID: {response['supplier_id']})"
                    if name
                    else f"Supplier ID: {response['supplier_id']}"
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
                    on_click=SendMessage(
                        "Check current inventory levels after receipt"
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

    state: dict[str, Any] = {
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
        "pending": False,
        "cancelled": False,
    }
    apply_action = _build_apply_action(confirm_tool, confirm_request)
    cancel_action = _build_cancel_action(
        f"the batch recipe update ({total} planned operation(s))"
    )

    columns = [
        DataTableColumn(key="group", header="Group", sortable=True),
        DataTableColumn(key="mo_id", header="MO", sortable=True),
        DataTableColumn(key="action", header="Action"),
        DataTableColumn(key="row_id", header="Row ID"),
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
            paginated=True,
            pageSize=25,
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
            with Row(gap=2):
                Button(
                    label="Review failed ops",
                    variant="outline",
                    on_click=SendMessage(
                        "List the failed sub-operations from the last batch update "
                        "and suggest recovery steps"
                    ),
                )
        else:
            with Row(gap=2):
                Button(
                    label="Verify recipes",
                    variant="outline",
                    on_click=SendMessage(
                        "Verify the updated manufacturing order recipes"
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
                    on_click=SendMessage(f"Open {katana_url} in the Katana web UI"),
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
