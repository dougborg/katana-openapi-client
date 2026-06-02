---
name: card-review
description: >-
  Audit Prefab UI card builders (`build_*_ui` in `katana_mcp_server/src/katana_mcp/tools/prefab_ui.py`)
  for user-centric content: real names over IDs, no redundant text dumps,
  named helpers over ad-hoc rendering. Reports findings; does not modify code.
  Use when reviewing card UX or after touching `prefab_ui.py`.
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash(grep *)
  - Bash(rg *)
---

# /card-review — Prefab UI Card UX Audit

## PURPOSE

Surface user-centric-content problems in MCP card builders before the operator
sees them. Cards live in `katana_mcp_server/src/katana_mcp/tools/prefab_ui.py`
as `build_<entity>_ui(response) -> PrefabApp` functions and render inside Claude
Code as the iframe payload of a `ToolResult`.

## CRITICAL

- **Read-only review** — propose fixes, don't apply them. Cite `file:line` for every finding.
- **Anchor on the user's actual decision** — every card answers "what am I confirming?" The audit asks whether the rendered content lets the operator answer that without consulting the raw tool blob or the Katana web UI.
- **Cross-check with `feedback-user-centric-card-content` memory** — that rule is the foundational principle this skill enforces; new anti-patterns we find belong added to `references/prefab-anti-patterns.md`.

## ASSUMES

- Target is one card (`/card-review build_fulfill_preview_ui`) or all (`/card-review --all`).
- Findings are reported as `[HIGH|MEDIUM|LOW|NONE] <card_name>` with file:line.
- The repo already has the right pattern set (`_render_party_line`, `_render_address_block`, `_render_field_diff_line`, `_render_failed_changes_block`, `_render_preview_header`/`_render_preview_footer`). The bar is "does this card use them, or bypass them?"

## STANDARD PATH

### 1. Identify the card(s) to audit

```bash
grep -n "^def build_.*_ui" katana_mcp_server/src/katana_mcp/tools/prefab_ui.py
```

Pick by name or audit all. Each `build_*_ui` consumes a response dict (see the impl
side in `katana_mcp_server/src/katana_mcp/tools/foundation/*.py`).

### 2. Scan against the eight anti-patterns

Run each grep pattern against the card's function body. Detail + remediation is in
[references/prefab-anti-patterns.md](references/prefab-anti-patterns.md).

| # | Anti-pattern | Grep target |
|---|---|---|
| 1 | Redundant text dump next to a table/widget | `for .* in response\[.*"`, `Muted\(content=` followed by `DataTable` |
| 2 | Internal IDs surfaced in user-facing text | `f"\w+ ID: \{`, `f"#\{`, `_id}` inside `Text(content=…)` |
| 3 | Missing party / address reference info on an order card | absence of `_render_party_line\|_render_address_block` in any SO/PO/MO body |
| 4 | Abstract verbs over content (`Operation`, `Target`, `n action(s)`) | `"Operation"`, `"Target"`, `n_actions`, `f"\{verb_label\}"` |
| 5 | Wire shape leaking to UI (snake_case headers, raw enum values, `model_dump()` dumps) | `header="\w*_\w+"`, `\.value\b` inside `Text(content=` |
| 6 | Buried decision context (table below 3+ warnings/metrics) | inspect layout order: identity → metrics → reference → decision-driver → footer |
| 7 | Helper-fallback masking (`name=None` passed to a party-line helper) | `_render_party_line\(.*name=None`, or a `_render_party_line` call whose source dict has no `*_name` field |
| 8 | Thin post-action DTO / single-row table (create card shows only name+SKU+message; one-row DataTable) | `build_\w+_(create\|success)_ui` body with no `_render_\w+_entity_view`; thin `Create\w+Response` vs exhaustive `get_<entity>` response |

### 3. Cross-reference positive helpers

Each anti-pattern finding pairs with a specific gold-standard helper. See
[references/positive-helpers.md](references/positive-helpers.md) for the inventory
and "use when" guide. If the card already uses the right helper but mis-passes args
(e.g., `entity_id` without `name`), flag the call site, not the helper itself.

### 4. Report

```text
## Card Review: <card_name>

### Severity
HIGH | MEDIUM | LOW | NONE

### Findings
- [Anti-pattern #N] `prefab_ui.py:NNNN-NNNN` — <one-line quote of the offending code>
  Fix: <which helper + how to call it>
- ...

### Positive (when severity NONE)
- Uses `_render_party_line` for Customer (`prefab_ui.py:NNNN`)
- ...
```

For `--all`, group cards by severity band (HIGH first), one block per card. Keep
the total report scannable — under ~50 lines per band.

## EDGE CASES

- **Card already uses a helper but the helper itself emits an ID** — flag the helper, not the card. `_render_party_line` falls back to `f"<Label> ID: {entity_id}"` when name is None; the impl side should resolve the name (typed cache: `resolve_entity_name(catalog, Cached*, id, entity_label="…")` — pattern at `katana_mcp_server/src/katana_mcp/tools/foundation/sales_orders.py:568`).
- **Success card vs preview card divergence** — the post-action card often inherits the preview's reference block. Audit both branches; the `is_preview` switch is not an excuse to drop user-facing content.
- **MO branch on shared card** — manufacturing orders legitimately lack a customer + shipping address. The audit should skip the missing-reference-info check when `order_type == "manufacturing"` and the card has a per-branch guard.
- **No generic modification fallback** — every modify/delete entity now has a dedicated per-entity card (`build_<entity>_modify_ui`); the old generic `ActionResult`-table cards were deleted in #721 Phase 6. `to_tool_result` dispatches on `entity_type` and *raises* for an unregistered type. A new modification entity needs its own `build_<entity>_modify_ui` + a dispatch branch (model: `build_po_modify_ui`) — there is no generic card to fall back to.
- **One entity-view helper across create / modify / detail** — an entity with multiple card surfaces should share a single `_render_<entity>_entity_view` (Tier 2+3), like `_render_po_entity_view` / `_render_item_entity_view`. A create card that re-renders the metric/reference block inline (instead of delegating) is anti-pattern #8 — flag it. The helper carries a `changes=None` diff-overlay seam for the modify card and a `collapse_single_variant` flag so the create card renders a single child inline rather than a one-row table.
- **Create cards enrich from the result, not a second fetch** — when a create card looks thin, the fix is to widen the response DTO and map it from the `.create()` result (which is already fully populated), resolving the party *name* from the typed cache. Don't flag a create card as needing a `get_<entity>` round-trip.

## RELATED

- `frontend-design-review` skill (upstream `microsoft/skills@frontend-design-review`, vendored at `.claude/skills/frontend-design-review/`) — provides the three-pillar framework (Frictionless / Quality Craft / Trustworthy). This skill rebinds the pillars to Prefab UI semantics.
- `code-modernizer` agent — actively rewrites the patterns this skill flags.
- `/review` skill — broader code review; use after `/card-review` for non-UX issues.
- `feedback-user-centric-card-content` memory — the foundational principle this skill enforces.
