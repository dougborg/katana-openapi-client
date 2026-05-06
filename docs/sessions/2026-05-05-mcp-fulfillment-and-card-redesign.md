# Session 2026-05-05 — MCP fulfillment + variant card redesign + PM groom

First applied session-retro doc, written manually (the `/session-retro` skill is
proposed in [harness-kit#30](https://github.com/dougborg/harness-kit/issues/30) and
tracked for adoption here as #561). Captures the cause-and-effect chain of a
high-density working session so patterns accumulate instead of scattering across one-off
bug reports.

## Goal

Two parallel objectives:

1. Ship the first card-redesign delivery (#538 — `get_variant_details`) as a working
   template for the rest of the umbrella (#537).
1. Test the MCP-backed shop-floor agent on a real Shopify→Katana sales-order fulfillment
   flow (SO #WEB20387, Carbon Rocker v2 / variant 33331882).

## What happened (chronological)

### Morning: PR #535 review feedback

Addressed Copilot review on PR #535 (`check_inventory` per-location DataTable):

- Single-item Prefab card path didn't render `by_location` — added DataTable + "N
  locations" badge when `len(by_location) > 1`
- N+1 cache lookups — switched from `services.cache.get_by_id()` per row to bulk
  `services.cache.get_many_by_ids(EntityType.LOCATION, unique_loc_ids)`
- DataTable column type — switched from raw `dict` to `DataTableColumn(...)` to match
  the existing search-results pattern

### Midday: variant card redesign (#542)

Implemented the four-tier framework (identity → metrics → reference → actions) on
`get_variant_details`:

- 4 new fields on `VariantDetailsResponse` (`uom`, `default_supplier_id`,
  `default_supplier_name`, `is_batch_tracked`) populated from the parent
  product/material — variants don't carry these on the attrs model directly
- `_enrich_variants_with_parent` helper does at most 3 bulk cache queries (products,
  materials, suppliers) regardless of variant count
- Card rewritten with extracted section helpers to stay under ruff complexity
- 5 behavior tests + 1 regression test for the per-type parent-map fix

PR opened, CI green, Copilot caught a real bug: merging `products` and `materials` into
a single `parent_by_id` keyed only by numeric ID would mis-attach parents on collision
(cache rows are keyed by `(entity_type, id)`). Fixed via per-type maps; this lesson is
now in CLAUDE.md "Known Pitfalls."

### Afternoon: live fulfillment session — bugs cascade

User ran a real fulfillment for SO #WEB20387 against the dev MCP server. The session
produced a chain of issues, each compounding the next:

1. **`search_items` iframe stuck on "Waiting for content…"** — happens both during AND
   after execution on 0-result paths. Updated #470 with new symptom data; root cause
   likely envelope delivery on the empty-state branch.

1. **Stale items cache, no MCP recovery path** — `search_items` returned 0 for an SKU
   the user knew existed. Agent tried `rebuild_cache`, found it only covers
   transactional entities (PO/SO/MO/ST/SA), gave up and went to the browser. Updated
   #472 to flag this as a recovery-path requirement on the WS-0 cache unification
   milestone.

1. **Preview→apply UX produces duplicate confirmation paths** — `fulfill_order` preview
   rendered correctly with a "Confirm Fulfillment" button, but the agent ALSO wrote
   "Please confirm the fulfillment:" with a bullet list. Two paths, ambiguous which one
   the user takes. Filed as #544.

1. **Confirm-button apply errors are opaque** — user clicked Confirm, apply failed with
   a 422, toast said only "Fulfillment for #WEB20387 failed" with no reason. The actual
   `UnprocessableEntityError: sum of serial number quantity (current: 0) must match fulfillment row quantity (expected: 1)`
   was visible only via tooltip on a small warning icon. Filed as #545.

1. **`fulfill_order` can't ship serial-tracked variants** — Rocker v2 is serial-tracked;
   tool has no `serial_numbers` parameter; agent diagnosed correctly and bailed to the
   browser. Filed as #547 with a 2-phase fix proposal (preview-time block warning +
   per-row override).

### Evening: backlog groom

Used `general-purpose` agent (briefed as a PM — there's no dedicated project-manager
agent yet) to survey 66 open issues. Output: a 5-PR P1 hotfix train (#527 → #544+#545 →
#547 → #499+#517), a stale-issue list, and a gap list. The PM brief itself was ad-hoc;
codifying it as a `/groom` skill is filed as
[harness-kit#26](https://github.com/dougborg/harness-kit/issues/26).

Filed 14 backlog gap issues (#548–#561):

- 10 sub-issues for the remaining card builders in #537 (#548–#557)
- 1 audit issue for `additional_info` echo helper generalization (#558)
- 1 bug for "agent re-runs preview after Confirm-button apply succeeded" (#559)
- 1 docs sync for help-resource drift after the new `correct_*` tools (#560)
- 1 process issue for the session-retro pattern (#561 — meta)

### Late evening: harness retro

Ran `/harness retro` and surfaced 5 findings to file in upstream `dougborg/harness-kit`:

1. `/groom` skill + `project-manager` agent —
   [harness-kit#26](https://github.com/dougborg/harness-kit/issues/26)
1. `discover-verification-cmd.sh` doesn't know about uv+poe — already fixed in v0.5.0
   (PR #19) — closed as duplicate
1. `poll-review.sh` classifies overall-only reviews as `comments` —
   [harness-kit#28](https://github.com/dougborg/harness-kit/issues/28)
1. `/commit` should auto-stage uv.lock to avoid pre-commit auto-stash race —
   [harness-kit#29](https://github.com/dougborg/harness-kit/issues/29)
1. `/session-retro` skill —
   [harness-kit#30](https://github.com/dougborg/harness-kit/issues/30)

## What worked

- **Four-tier card framework held up under stress test.** No contortions on the variant
  card; Header → Metrics → Reference → Actions mapped cleanly. The remaining 10 card
  sub-issues can use it verbatim.
- **`/simplify` triple-agent review** caught the unused supplier-rendering 3-arm
  conditional and the redundant comment narration. Ran in parallel, finished in ~30s,
  cost ~3k tokens.
- **Copilot caught a real bug none of my agent reviewers found.** The parent-map
  ID-collision was subtle — required understanding cache key uniqueness semantics.
  Treating Copilot as a peer reviewer (open the PR, wait for the review) costs nothing
  and pays off.
- **`/open-pr` → CI poll → review poll → `/review-pr` cascade.** End-to-end flow ran
  without manual intervention except for the `npm test` glitch (the discover script
  doesn't know about uv+poe — fixed upstream in v0.5.0).
- **PM groom output structure** — top-line state / umbrellas / next 5–10 PRs / stale /
  gaps. Opinionated, scanned in ~30s, surfaced both a clear plan and meaningful gaps.

## What didn't work

- **Agent fell back to the browser twice in one session** — once for stale items cache
  (#472), once for serial-tracked fulfillment (#547). Both are real product gaps that
  defeat the MCP-as-shop-floor-surface vision. These are the most important class of bug
  to surface from live sessions.
- **Preview→apply pattern produces visibly confused UX in the wild** — #544 + #545 +
  #558 are all symptoms of the same architectural issue. The mechanical bugs (#491,
  #495) are fixed but the conversational UX still feels broken.
- **`discover-verification-cmd.sh` returned wrong command** for this stack — fixed
  upstream in harness-kit v0.5.0 but not yet pulled into this project (still on v0.4.0).
  Plugin install + `/harness update` is the resolution.
- **Manually filing 14 issues + 5 upstream issues** — should have been one
  `/harness-issue` invocation per upstream issue (skill exists in v0.5.0).

## Lessons / patterns

- **Cache rows are keyed by `(entity_type, id)`** — never merge cross-entity maps by
  numeric ID alone. Now in CLAUDE.md "Known Pitfalls."
- **The four-tier card framework is the template.** Subsequent cards should follow the
  variant card's structure: extract section helpers from the start to stay under ruff
  complexity (`C901` ≤ 15 branches).
- **Live sessions produce ~10x the bug density of synthetic testing.** A single
  fulfillment flow surfaced 5 issues — bugs the test suite couldn't have found because
  the agent's reasoning is the thing being tested.
- **Bugs compound — file the chain, not just the symptom.** The fulfillment failure was
  three independent bugs (#544, #545, #547) layered on top of each other. Filing each in
  isolation loses the cause-and-effect; the cross-references between them are
  load-bearing context.
- **Plugin-shaped tooling beats one-off prompts.** The PM groom and the upstream
  issue-filing both worked but were ad-hoc; codifying them as skills (`/groom` and
  `/harness-issue` respectively) makes the patterns recur reliably.

## Issues filed (consolidated)

**Project-local (`dougborg/katana-openapi-client`):**

- Fulfillment chain: #544, #545, #547
- Updates: #470 (new symptom), #472 (recovery-path requirement)
- Card sub-issues: #548–#557 (10 cards — #557 is `batch_recipe_update_ui`, re-fired
  after the first parallel batch hit a missing label and cascade-cancelled)
- Audits: #558 (additional_info), #560 (help-resource drift)
- Process: #559 (agent re-runs preview), #561 (session-retro adoption)
- This PR: CLAUDE.md "cache IDs not globally unique" pitfall +
  `.claude/harness-upstream` config + this doc

**Upstream (`dougborg/harness-kit`):**

- New skills/agents: #26 (`/groom` + `project-manager`), #30 (`/session-retro`)
- Bugs: #28 (`poll-review.sh` classification), #29 (`/commit` uv.lock auto-stash race)
- Closed as duplicate: #27 (already fixed in v0.5.0)

## Next session priorities

Per the PM groom (full text in conversation transcript):

1. **#527** — fix `update_sales_order` empty-200 schema (every PATCH currently raises).
   Breaks `correct_sales_order`.
1. **#544 + #545 bundled** — the duplicate-confirmation + opaque-error bugs.
1. **#547** — `fulfill_order` serial_numbers parameter.
1. **#499 + #517 bundled** — surface 422 details on opaque create errors.
1. **Install harness-kit plugin** + `/harness update` — pulls v0.4.0 → v0.5.1 baseline,
   unlocks `/harness-issue` and `/standup`, fixes the discover-cmd glitch.
