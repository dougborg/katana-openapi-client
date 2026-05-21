# ADR-0021: Unified Direct-Apply Rail for Preview→Apply Cards

## Status

Accepted

Date: 2026-05-21

Supersedes [ADR-0015](../../../docs/adr/0015-confirmation-pattern-for-write-tools.md)
(the `SendMessage` re-issue rail) for the apply-button rail. ADR-0015's
`destructiveHint` policy table remains in force.

## Context

ADR-0015 settled the preview→apply pattern with a two-step UI: a preview card with
Confirm/Cancel buttons whose `on_click` fired

- `SetState("pending", True)` +
  `SendMessage("Apply: call <tool>(<args>, preview=False)")` on Confirm — instructing
  the agent to re-issue the apply tool call,
- `SetState("cancelled", True)` + `SendMessage("Cancel: do not apply <description>.")`
  on Cancel — telling the agent the user opted out.

The reason for the agent round-trip — explained in ADR-0015 — was that the 2025-11-25
MCP Tools spec routed an iframe-initiated `tools/call` result back to the iframe, not to
the agent's model context. Without agent re-issue, successes and errors never reached
the agent: closing #545 and #559 required the agent to *be* the caller.

That constraint dissolved with the **MCP Apps spec, SEP-1865 (2026-01-26)**. The new
`ui/update-model-context` notification lets an iframe push structured content into the
agent's model context for the agent's next turn. The iframe can now fire the apply call
*and* deliver the structured response — both of the things ADR-0015 said were
impossible.

Once `ui/update-model-context` shipped, we ran a controlled rollout of the new rail (the
"direct-apply rail") on `create_purchase_order` and the `modify_*` / `delete_*` /
`correct_*` / stock-adjustment write tools. It worked, so we extended it to most tools —
but `fulfill_order`, `receive_purchase_order`, `create_stock_transfer`, and the
batch-recipe-update card stayed on the SendMessage rail (the ADR-0015 default), giving
us two visibly different rails:

- Direct-apply rail: Confirm fires
  `CallTool(... preview=False, on_success=[..., UpdateContext($result), ...])` → iframe
  morphs to the applied card in place; agent sees the result on its next turn via
  `ui/update-model-context`. No chat indirection.
- SendMessage rail: Confirm fires `SendMessage("Apply: call <tool>(...)")` → agent
  recognizes the prefix and re-issues; iframe is replaced by whatever the apply's
  response card looks like. Always at least one agent round-trip; verbose chat lines on
  large applies; ~400 tokens of dual-rail coaching in every preview tool's description.

PR #807 then migrated **drill-in / view-in-Katana / open-ended** follow-up buttons (the
*other* SendMessage uses across `prefab_ui.py`) to `CallTool` / `OpenLink` /
`UpdateContext`. After #807 the only SendMessage instances left in the apply-card
surface were `_build_apply_action` (Confirm) and `_build_cancel_action` (Cancel) — the
rail this ADR finishes migrating.

## Decision

**The Confirm and Cancel buttons on every preview card fire deterministic actions via
the same rail:**

- **Confirm button** fires:
  1. `SetState("pending", True)` — disables both buttons immediately (in-flight click
     guard against double-fire).
  1. `CallTool(<apply_tool>, arguments={<original args>, preview: False}, on_success=[…], on_error=[…])`
     — calls the apply tool from the iframe with `preview=False`.
     - `on_success` runs `SetState("result", $result)`, `SetState("applied", True)`, and
       `UpdateContext(content=$result)` — the third action pushes the structured result
       into the agent's model context for its next turn.
     - `on_error` runs `SetState("error", $error)`, a `ShowToast`, and
       `UpdateContext(content="Apply failed: $error")` — the agent sees the failure
       reason.
- **Cancel button** fires:
  1. `SetState("cancelled", True)` — flips the card to a "Cancelled" pill, locks both
     buttons.
  1. `UpdateContext(content="User cancelled the <description> preview.")` — the agent's
     context picks up the opt-out without a chat line.

`_build_apply_action` and `_build_apply_action_direct` collapse into a single
`_build_apply_action` function. `_render_apply_button_row` loses its `direct_apply` flag
— the state machine is the same for every tool (Preview → Pending →
Applied/Error/Cancelled). `register_preview_tool` and `with_preview_coaching` lose their
`direct=` flag and ship one coaching variant; the `PREVIEW_APPLY_DIRECT_COACHING`
constant goes away.

The `_build_apply_message` helper (which produced the
`Apply: call <tool>(<args>, preview=False)` chat-string format) is deleted — no longer
reachable.

## Consequences

### Positive Consequences

- **Architectural symmetry.** The apply rail and the rest of `prefab_ui` (post-#807) now
  use the same primitives: `CallTool` for deterministic re-invocation, `UpdateContext`
  for context signals, `OpenLink` for navigation. The mental model is uniform.
- **One fewer round-trip per apply.** ADR-0015 explicitly noted "one extra LLM
  round-trip per apply, ~2–5s and a few hundred tokens" as the cost of the SendMessage
  rail. Removed.
- **No more dual-rail tax in tool descriptions.** Every preview-mode write tool's
  description was carrying ~400 tokens of dual-rail coaching (one branch for
  SendMessage, one for direct-apply). Single coaching variant now.
- **No `Apply: call <tool>(<args>...)` chat lines.** Verbose, parseable-but-ugly.
  Replaced by an `UpdateContext` notification that doesn't pollute the chat history.
- **Determinism.** The iframe builds the apply args at preview-build time and bakes
  `preview=False` into the `CallTool.arguments` dict. There is no agent transcription
  step to drop a field or re-format a value (#491 territory).
- **Same chosen Confirm/Cancel UX.** Button labels still say "Confirm X" / "Cancel"; the
  user-visible flow is identical. Only the underlying action mechanism changed.

### Negative Consequences

- **Cross-host coverage tied to MCP Apps support.** The direct-apply rail requires
  `ui/update-model-context` (SEP-1865, 2026-01-26). Hosts that render iframes but not
  MCP Apps would not deliver the apply result back to the agent. The set of hosts in
  that category appears to be empty in practice (Claude Desktop, Claude.ai, Cowork all
  support MCP Apps), but the surface is narrower than ADR-0015's "works on every host
  that renders Prefab cards" guarantee. The no-iframe fallback
  (host-doesn't-render-iframes path in the coaching) handles CLI clients the same way as
  before.
- **One agent-coaching block to maintain instead of two.** Removed, not just merged —
  `with_preview_coaching` and `register_preview_tool` shrunk.

### Neutral Consequences

- **`destructiveHint` policy unchanged.** ADR-0015's per-tool `destructiveHint` table
  (delete/modify True, create False, etc.) carries forward; this ADR doesn't touch
  annotation policy.
- **The `_render_apply_button_row` state machine is unchanged in behavior** — Pending →
  Applied → Cancelled transitions worked the same way on both rails, and the SendMessage
  rail's "no applied/error states" was a degenerate case of the same machine.

## Alternatives Considered

### Alternative 1: Keep both rails, document the split

- **Description.** Leave `_build_apply_action` (SendMessage) and
  `_build_apply_action_direct` (CallTool+UpdateContext) as separate functions, with
  `direct=True` opt-in per tool. The dual-rail tool descriptions stay.
- **Why rejected.** No remaining reason for the split. The SendMessage rail was a
  workaround for a now-resolved spec gap. PR #807 already collapsed the *other*
  SendMessage uses in `prefab_ui`; leaving the apply rail behind perpetuates
  inconsistency.

### Alternative 2: Restore `context.elicit()`

- **Description.** Replace iframe Confirm/Cancel with server-initiated elicitation
  dialogs.
- **Why rejected.** Same reason as ADR-0015's Alternative 1: most candidate hosts don't
  support elicitation; the spec restricts schema to flat primitives; it'd raise on
  unsupported hosts.

### Alternative 3: Drop the iframe rail entirely; chat-only "yes"

- **Description.** No buttons; preview ends the turn, user types "yes" to apply, agent
  re-issues.
- **Why rejected.** Same reason as ADR-0015's Alternative 3: works, but loses the
  one-click affordance. The unified direct-apply rail delivers the same fidelity *and*
  keeps the button.

## References

- ADR-0015 (superseded) — original SendMessage-rail rationale + the `destructiveHint`
  policy table that carries forward
- PR #807 — `SendMessage → CallTool/OpenLink/UpdateContext` migration for drill-in /
  view-in-Katana / open-ended buttons (13 CallTool, 5 OpenLink, 21 UpdateContext sites;
  precedent for this ADR)
- [MCP Apps spec, SEP-1865](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1865)
  — `ui/update-model-context` notification (2026-01-26)
- [MCP Tools spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- #316 — confirmation-pattern decision (the parent thread for ADR-0015)
- #491 — Confirm-button arguments dropped (closed by #493) — the template-binding
  fragility the direct rail also avoids by inlining args into `CallTool.arguments` at
  card-build time
