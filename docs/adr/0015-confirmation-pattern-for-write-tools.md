# ADR-0015: Confirmation Pattern for Write Tools (preview→apply, agent re-issued)

## Status

Accepted

Date: 2026-05-06

Closes the action items from issue #316; supersedes the iframe-direct-apply shape that
#491, #495, #545, #559 were filed against.

## Context

Every Katana MCP write tool (`create_*`, `modify_*`, `delete_*`, `fulfill_order`,
`receive_purchase_order`, `correct_*`, `update_stock_adjustment`) is destructive in some
sense. Two confirmation shapes exist in MCP today:

1. **`destructiveHint` annotation** — advisory metadata on the tool. Hosts *should*
   prompt before invoking, but per
   [the python-sdk source](https://github.com/modelcontextprotocol/python-sdk/blob/main/src/mcp/types/_types.py)
   and the
   [Tool Annotations as Risk Vocabulary blog post](https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/),
   it is *"hints, not guarantees"*. "Always allow" toggles silently disable it.
1. **`elicitation/create`** ("`context.elicit()` / `ctx.elicit()`") — a server-initiated
   input-gathering primitive. Per the
   [2025-06-18 Elicitation spec](https://modelcontextprotocol.io/specification/2025-06-18/client/elicitation):
   schema is restricted to flat objects with primitive properties, *"Servers MUST NOT
   use elicitation to request sensitive information"*, and host support is sparse —
   Claude Desktop, Claude.ai, ChatGPT, Cline, Continue, and Zed do **not** support it
   (per the [MCP clients support matrix](https://modelcontextprotocol.io/clients), May
   2026 snapshot).

Issue #316 settled the architectural question: **keep `preview→apply`, do not restore
`context.elicit()`.** Anthropic's reference filesystem server
([modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers/blob/main/src/filesystem/index.ts))
ships exactly this pattern — `destructiveHint: true` paired with a `dryRun: boolean`
parameter — so we converged on the de facto standard.

That decision left the **conversational UX** unfinished. Three follow-up bugs
accumulated:

- **#491** (closed by #493) — The Confirm button on the preview card fired a
  `tools/call` from the iframe with templated arguments that the host silently dropped.
  Eight production manufacturing orders were created with empty `additional_info`. Fix:
  bake values into the action payload.
- **#495** (closed) — Even with arguments inlined, the click fired invisibly. No toast,
  no chat-history line. Fix: attach `ShowToast` + `SendMessage` handlers to every
  Confirm button.
- **#544** — Agent renders the preview card *and* asks for confirmation in chat. Two
  confirmation rails; user doesn't know which is canonical.
- **#545** — When the apply call fails, the toast and `SendMessage` both swallow the
  actual error reason — they're built from static f-strings.
- **#559** — When the apply succeeds, the `SendMessage` hint is too vague for the agent
  to recognize as a completion signal. Agent re-narrates the preview on its next turn.

Investigating #545 / #559 surfaced a deeper architectural fact:

> By MCP spec, an iframe-initiated `tools/call` returns its result to the iframe, not to
> the agent's context. The agent never sees the structured apply response.

This applies equally to the 2025-11-25 Tools spec, the 2025-06-18 Elicitation spec,
FastMCP, and the still-open SEP-1487 (`trustedHint`) proposal. There is no MCP primitive
— present or imminent — that lets an iframe-initiated call deliver its result back to
the agent. The iframe→agent boundary is one-way.

That means the iframe-direct apply path was **the wrong rail**. The agent was always
going to be blind to apply outcomes; #545 and #559 were not solvable as long as the
iframe owned the apply.

## Decision

The Confirm button **does not call the apply tool directly.** Instead:

- **Confirm button** fires:

  1. `SetState("pending", True)` — flips the preview card to a "Pending…" pill +
     grayed-out buttons.
  1. `SendMessage("Apply: call <tool>(<args>, preview=False)")` — a chat message
     containing the explicit re-invocation instruction with all args inlined (same
     inlining as #493, no template fragility).

- **Cancel button** fires:

  1. `SetState("cancelled", True)` — flips the card to a "Cancelled" pill.
  1. `SendMessage("Cancel: do not apply <description>.")` — explicit cancellation chat
     message.

- **Tool descriptions** for every preview-mode write tool include coaching:

  - When `preview=True` returns, end the turn — do not re-narrate the card or ask for
    chat-side confirmation.
  - When the agent receives an `Apply: call <tool>(...)` message, re-issue the tool call
    exactly as written.
  - When the agent receives a `Cancel: do not apply ...` message, acknowledge briefly
    without re-issuing.

The button thus becomes UX shorthand for the user typing "yes, apply it" — preserving
the one-click affordance while routing the apply through the agent's tool-calling loop,
where the agent sees the full structured response.

The `destructiveHint` annotation is settled by uniform policy:

| Tool family                                | `destructiveHint` |
| ------------------------------------------ | ----------------- |
| `delete_*`                                 | `True`            |
| `modify_*` (overwrites)                    | `True`            |
| `create_*` (additive)                      | `False`           |
| `fulfill_order`, `receive_purchase_order`  | `True`            |
| `correct_*`                                | `True`            |
| `update_stock_adjustment`                  | `True`            |
| `rebuild_cache` (wipes local cache tables) | `True`            |

## Consequences

### Positive Consequences

- **The agent sees the full structured apply response.** Successes and errors arrive as
  ordinary tool results in the agent's context. Closes #545 (real error reasons surface)
  and #559 (agent recognizes the apply as complete because it made the call itself).
- **One canonical confirmation rail.** Tool-description coaching tells the agent to stop
  narrating after a preview, so the card is the only confirmation surface. Closes #544.
- **No template-binding fragility.** All args are inlined into the `SendMessage` text at
  preview-build time. The host never has to substitute anything.
- **Works on every host.** `SendMessage` and `SetState` are universally supported across
  hosts that render Prefab cards. Unlike `elicitation/create`, no host is left out.
- **Auditable history.** Each step (preview, Apply/Cancel SendMessage, apply tool call,
  apply result) is a permanent chat line.

### Negative Consequences

- **One extra LLM round-trip per apply.** ~2–5s and a few hundred tokens vs. the
  previous iframe-direct fire. Acceptable cost for fidelity.
- **Verbose `SendMessage` lines.** A `create_purchase_order` preview with 20 line items
  produces a long `Apply: call create_purchase_order(...)` line. Acceptable; revisit if
  it becomes unwieldy.
- **Two cards in chat per apply.** The preview (now showing "Pending…") plus the result
  card. Slightly more vertical real estate; the visual progression matches user
  expectations.
- **Agent reliability assumption.** The agent must reliably parse
  `Apply: call <tool>(<args>)` and re-issue. Validated for Sonnet 4 / Opus 4 class
  models; mitigated by uniform format and tool-description coaching.

### Neutral Consequences

- **`build_apply_success_ui` / `build_apply_error_ui`** are added as generic
  apply-result builders. Existing per-entity success cards (`build_order_created_ui`,
  `build_fulfill_success_ui`, `build_item_mutation_ui`) keep their custom affordances
  and are not replaced. The generics are available for tools that don't have a dedicated
  card.

## Alternatives Considered

### Alternative 1: Restore `context.elicit()`

- **Description.** Server pauses the apply tool call mid-execution and asks the host to
  render a confirmation dialog.
- **Why rejected.** Per #316: most candidate hosts (Claude Desktop, Claude.ai, ChatGPT,
  Cline, Continue, Zed) don't support elicitation; the spec explicitly forbids using it
  for sensitive data; and the schema is restricted to flat primitives. Calls would
  *raise* on unsupported hosts.

### Alternative 2: Card-morphing with no agent signal

- **Description.** Confirm fires `CallTool` directly (today's behavior), the iframe's
  `on_success` flips the card to a result view via `SetState`, no `SendMessage` is sent.
  Agent has no signal at all.
- **Why rejected.** Loses the one capability that motivated the rail change: the agent
  seeing the structured apply response. #559 stays broken (agent re-narrates the preview
  because it doesn't know the apply ran), and #545 stays broken (the agent never sees
  the error).

### Alternative 3: Drop the iframe button entirely; chat-only "yes"

- **Description.** After a preview, the agent's turn ends; the user types "yes" /
  "apply"; the agent re-issues with `preview=False`.
- **Why rejected.** Functionally equivalent to the chosen path from the agent's
  perspective, but loses the one-click button affordance. The hybrid retains the button
  while delivering the same fidelity.

### Alternative 4: Server-side preview-id stash + short SendMessage

- **Description.** Server stores apply args under a short ID; the `SendMessage` only
  carries the ID; the agent looks it up via a separate tool call before re-issuing.
- **Why rejected.** Adds server state, extra round-trips, and a bespoke retrieval tool.
  The verbose-SendMessage cost of inlining args is acceptable in practice.

## References

- #316 — confirmation-pattern decision (the parent thread)
- #491 — Confirm-button arguments dropped (closed by #493)
- #495 — Confirm-button click in-chat feedback (closed)
- #544 — duplicate confirmation paths (closed by this ADR's PR)
- #545 — opaque apply errors (closed by this ADR's PR)
- #559 — agent re-runs preview after Confirm-button apply (closed by this ADR's PR)
- [MCP Tools spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [MCP Elicitation spec 2025-06-18](https://modelcontextprotocol.io/specification/2025-06-18/client/elicitation)
- [MCP clients support matrix](https://modelcontextprotocol.io/clients)
- [Tool Annotations as Risk Vocabulary](https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/)
- [Reference filesystem server (`dryRun` pattern)](https://github.com/modelcontextprotocol/servers/blob/main/src/filesystem/index.ts)
- [SEP-1487 `trustedHint` proposal](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1487)
- ADR-0014 (superseded; harness-kit migration) — for ADR-naming convention
