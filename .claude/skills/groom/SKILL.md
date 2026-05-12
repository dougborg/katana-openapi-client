---
name: groom
description: >-
  Groom the Rolling Backlog (project #5) by reading current state and proposing
  diffs — not re-deriving the queue from scratch. Surfaces drift between issue
  state and project status, missing classification, and stale priorities. Asks
  per-category confirmation before mutating the board.
argument-hint: "[--dry-run]"
allowed-tools:
  - Bash(gh project *)
  - Bash(gh issue *)
  - Bash(python3 *)
---

# /groom — Backlog hygiene against the Rolling Backlog

## PURPOSE

Mutate the [Rolling Backlog](https://github.com/users/dougborg/projects/5)
(project #5) based on observed drift, not re-classify the world. A clean
groom run says "X items drifted, Y need triage, Z went stale — confirm each
category" and then applies the corresponding `gh project item-edit` /
`gh issue close` mutations. **Default behavior is read-only**: it always
prints what it would do and asks for per-category confirmation before any
mutation happens.

This is the long-term version of #568's §4: the board IS the priority
queue, and grooming evolves it forward. Do **not** re-derive priorities
from `gh issue list` — that produces a one-off transcript snapshot that
goes stale immediately. The board is durable; mutate it in place.

## CRITICAL

- **Default to read-only** — print proposals first, never auto-apply.
- **Per-category confirmation** — use `AskUserQuestion` to confirm each
  category of changes independently (the user may want to apply the
  triage queue but skip the stale-P3 closures).
- **Never close an issue without confirming** — closures are destructive
  and require an explicit per-issue acknowledgement, not blanket approval
  for the category.
- **Surface, don't decide** — the heuristics flag *candidates*, not
  certainties. A 90-day-stale P3 might still be relevant; let the user
  judge.
- **Don't grow the heuristics arbitrarily** — keep the rule set tight.
  Each new heuristic must have a concrete observed drift it solves; soft
  signals belong in a richer `/triage` skill (#684), not here.

## ASSUMES

- You have GitHub CLI (`gh`) installed and authenticated.
- Project #5 exists, owned by `@me`, with the field schema documented in
  `CLAUDE.md` "Project Backlog" (Priority / Effort / Workstream /
  Umbrella).
- Python 3.12+ on PATH (the analyzer uses stdlib only).

## STANDARD PATH

### Phase 1 — Analyze the board

Run the analyzer (writing to a file so the proposals can be re-read
during the apply phase without re-fetching the board):

```bash
python3 .claude/skills/groom/analyze.py > /tmp/groom-proposals.json
python3 -m json.tool /tmp/groom-proposals.json
```

Both `>` (shell redirect) and `python3 -m json.tool` are inside this
skill's `allowed-tools` list — `tee`, `cat`, and `jq` are intentionally
not, to keep the skill portable to hosts with stricter tool gates.
If you also need to capture and view the output in one shot (e.g., to
stream into the conversation while persisting it), pipe through a
Python tee:

```bash
python3 .claude/skills/groom/analyze.py \
  | python3 -c "import sys, pathlib; d = sys.stdin.read(); sys.stdout.write(d); pathlib.Path('/tmp/groom-proposals.json').write_text(d)"
```

(Note the **pipe** in `... analyze.py | python3 -c ...` — without it
the `python3 -c` block waits forever on stdin.)

It fetches `gh project item-list 5 --owner @me --format json` and the
state of every linked issue (one `gh issue view` per issue — serial,
not batched; typical wall-time is ~30s on a 200-item board). The output
JSON groups items into five categories:

| Category | What it flags |
| --- | --- |
| `needs_triage` | Project item has no Priority or no Workstream. |
| `drift_done_open` | Status=Done but linked issue is still OPEN. |
| `drift_closed_not_done` | Linked issue is CLOSED but Status≠Done. |
| `stale_p3` | P3-someday whose project-item `updatedAt` > 90 days ago. |
| `idle_p0_p1` | P0/P1 in Todo/In Progress, `updatedAt` > 21 days, no open PR. |

Each category prints a list of `{number, title, status, priority,
workstream, ago_days}` records. If a category is empty, skip it — no
confirmation prompt needed.

### Phase 2 — Present the diff

Format a compact summary for the user. Don't print the raw JSON; render
it as a table per category. Example:

```
Groom proposals (analyzed 128 items):

needs_triage (3):
  #719 [Todo, P(unset)/W(unset)]  feat(mcp): expose ...
  #720 [Todo, P(unset)/W(unset)]  bug(client): ...
  #721 [Todo, P(unset)/W(unset)]  docs: ...

drift_done_open (2):
  #659 [Done, P0/Spec-drift, 5d ago]  Bug umbrella for 0.66 — partially fixed
  #560 [Done, P1/Process, 7d ago]    docs(mcp): help resource sync

drift_closed_not_done (0): clean

stale_p3 (5):
  #53  [Todo, P3/Process, 180d ago]  MCP-22: usage examples for Claude Code
  ...

idle_p0_p1 (0): clean
```

When a category is empty, the corresponding section reads "clean". A
**fully-green** groom run (all categories clean) prints "Board is clean
— no proposals." and exits.

**Handling `fetch_errors`** — if the analyzer output includes a
`fetch_errors` array, some issues couldn't be read at the gh layer
(auth, rate-limit, network glitch — _not_ "this number is a PR not an
issue", which is filtered upstream). The drift heuristics that depend
on issue state (`drift_done_open`, `drift_closed_not_done`,
`idle_p0_p1`) are **under-counted** for those numbers. Surface the
list to the user before presenting proposals: "Couldn't fetch state
for N issues; drift counts may be low. Re-run after the transient
clears, or address with the partial data." Don't auto-retry — the
caller may have intentionally constrained the gh rate.

### Phase 3 — Confirm per category

For each non-empty category, ask the user separately via
`AskUserQuestion`. Don't bundle: someone might want to apply the
`needs_triage` queue but not the `stale_p3` closures.

Question template:

> "Apply the **{category}** proposals?"
>
> - **Apply all** — apply the mutation for every item in this category.
> - **Apply selected** — let the user list specific issue numbers to
>   apply (the rest are skipped this run).
> - **Skip** — leave this category alone.

For **destructive** categories (anything that closes an issue —
currently just `stale_p3` if the user wants to close-not-downgrade),
add a per-item second confirmation before each close. **Never bulk-close
without one prompt per issue.** Non-destructive mutations (status moves,
adding Priority/Workstream) can go through the category-level apply.

### Phase 4 — Apply mutations

For each accepted change:

**`needs_triage`** → delegate to `/triage` (#684) for interactive
classification. Until #684 exists, present the items and ask the user
for Priority + Workstream per item, then:

```bash
# Look up the project-item ID for the issue.
# (Python-stdlib lookup instead of jq so the example stays inside
# this skill's allowed-tools list.)
item_id="$(
  gh project item-list 5 --owner @me --format json \
    | python3 -c "
import json, sys
n = int(sys.argv[1])
items = json.load(sys.stdin).get('items', [])
for it in items:
    if (it.get('content') or {}).get('number') == n:
        print(it['id'])
        break
" "$issue_number"
)"

# Set Priority.
gh project item-edit --id "$item_id" \
  --field-id "$PRIORITY_FIELD_ID" \
  --project-id "PVT_kwHOABM-ps4BW02d" \
  --single-select-option-id "$priority_option_id"

# Set Workstream.
gh project item-edit --id "$item_id" \
  --field-id "$WORKSTREAM_FIELD_ID" \
  --project-id "PVT_kwHOABM-ps4BW02d" \
  --single-select-option-id "$workstream_option_id"
```

Field and option IDs are stable; look them up once via
`gh project field-list 5 --owner @me --format json` and cache for the
run. (Same Python-stdlib pattern for parsing the field-list JSON.)

**`drift_done_open`** → ask the user per-item: close the issue (because
the PR landed and we forgot the closing keyword) or move the item back
to "In Progress" / "Todo" (because the Done was applied prematurely).
Apply accordingly via `gh issue close <n>` or
`gh project item-edit ... --field-id <Status> --single-select-option-id
<In Progress|Todo>`.

**`drift_closed_not_done`** → straightforward: move the item to Done.

```bash
gh project item-edit --id "$item_id" \
  --field-id "$STATUS_FIELD_ID" \
  --project-id "PVT_kwHOABM-ps4BW02d" \
  --single-select-option-id "$DONE_OPTION_ID"
```

**`stale_p3`** → per-item: close the issue (most common — P3 stale = no
forcing function), downgrade to "archive" (no such status today, so this
collapses to close), or keep (mark via a brief comment "kept on
{date}").

**`idle_p0_p1`** → per-item: downgrade Priority (most common — the work
isn't actually P1 if it's been sitting 3 weeks with no PR), or move
Status to "Todo" if it was wedged in "In Progress".

### Phase 5 — Summary

After all confirmed mutations have applied, print a summary:

- Items touched per category (counts + numbers)
- Field IDs of mutations applied
- Any items that errored on the apply path (and why)

If the user wants a record for the session retro, suggest saving the
proposal JSON (`/tmp/groom-proposals.json`) alongside the summary.

## EDGE CASES

- **The board is clean (all categories empty)** — Print
  "Board is clean — no proposals." and exit. This is the win state; a
  daily/weekly `/groom` finding nothing means the integration is
  working.

- **Many proposals (>30 across categories)** — Don't paginate
  interactively; render the full list, then ask the user to opt in
  per-category. If a single category has >20 items, suggest the user
  apply "selected" with a narrower issue-number list rather than "all".

- **`gh project item-edit` rate-limited** — pause and retry; the project
  endpoints aren't rate-limited as aggressively as the issue endpoints,
  but bulk runs may still hit secondary limits. Fall back to sequential
  applies with `sleep 1` between items if a 403 surfaces.

- **The skill is run in a worktree** — pre-commit hooks may be missing.
  The skill itself doesn't commit; it mutates GitHub state. Worktree
  context doesn't affect correctness.

## CONFIGURATION

The analyzer's thresholds live as module-level constants in
`.claude/skills/groom/analyze.py`:

- `STALE_P3_DAYS = 90` — Trip threshold for `stale_p3`.
- `IDLE_P0_P1_DAYS = 21` — Trip threshold for `idle_p0_p1`.

Tune by editing the file. New heuristics get added as new categories in
`classify_items()` and surfaced in the SKILL.md table above.

## RELATED

- `/open-pr` — surfaces linked-issue board status when opening a PR.
- `/triage` (#684, planned) — interactive Priority/Workstream prompts
  for un-classified items. Until that exists, `/groom` walks the
  `needs_triage` category inline.
- CLAUDE.md "Project Backlog" — the field schema, Priority bucket
  definitions, and Workstream definitions that `/groom` reasons about.
- #568 — parent umbrella for board-integration work.
- #683 — issue tracking this skill's full delivery (you are here).
