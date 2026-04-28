# ADR-0019: MCP tool description and batch-field conventions

## Status

Accepted

Date: 2026-04-27

## Context

Two recent epics — the `list_*` cache-back rollout (PR #391 and predecessors) and the
tool-description audit (PR #393, follow-on PR #397) — surfaced a recurring pattern:
agents calling our MCP tools fall back to N single-item invocations even when a batch
shape exists. Three things drove that fallback.

**Batch capability buried mid-docstring.** First-line summaries said what the tool
*returned* but not that it accepted a batch. Agents sized the input to the field they
saw on the first read pass and didn't scroll for a "Note: this also accepts a list"
buried five paragraphs later. PR #393 moved batch hints into the first sentence;
without a written rule the next tool will drift back.

**Parallel singular + plural fields.** Tools like the original `check_inventory`
exposed `sku` + `skus` + `variant_id` + `variant_ids` — four fields, mutually
exclusive, runtime-validated. Agents guessed the wrong combination, sent both, or
sent neither. PR #397 collapsed those four into a single
`skus_or_variant_ids: list[str | int]`. Same fork in the road for every future tool;
without a rule, contributors will reach for the four-field pattern again because
"singular + plural" looks more discoverable.

**`get_*` tools didn't advertise their `list_*` partner.** When an agent had multiple
IDs in hand and reached for `get_sales_order`, nothing in the docstring pointed them at
`list_sales_orders(ids=[...])` for a single round-trip. PR #397 added the cross-
reference; without a rule, future tool pairs won't get it.

**Help-resource drift.** `katana_mcp_server/src/katana_mcp/resources/help.py` mirrors
the tool docstrings as a top-level resource. The PR #397 review caught it
out-of-sync with the source-file docstrings — three workflow examples still used the
old `{"sku": "WIDGET"}` shape after the schema collapse. Without a written sync
expectation, this will recur on every tool change.

## Decision

We adopt four conventions for MCP tool description style. All four are enforced by
review (not lint) for now; if drift recurs, escalate to a `code-modernizer` rewrite
pass.

### 1. Batch-field naming

When a tool needs to accept either a single item or a batch:

**Heterogeneous batch (mixed types) — collapse to one list field.**

```python
class CheckInventoryRequest(BaseModel):
    skus_or_variant_ids: list[str | int] = Field(
        ...,
        min_length=1,
        description=(
            "SKUs (strings) or variant IDs (integers) to check — mix freely. "
            "Pass one for a detailed stock card; pass many for a summary table. "
            "Batching N items in a single call beats N separate invocations. "
            "Output order matches input order."
        ),
    )
```

The field is **required** (no `default_factory=list` — see PR #397 review) so the MCP
schema and Pydantic validation agree the field is required. The implementation
branches on `isinstance(item, str)` to dispatch.

**Homogeneous batch on a `list_*` tool — pass `ids=[...]`.**

```python
class ListSalesOrdersRequest(BaseModel):
    ids: list[int] | None = Field(
        default=None,
        description="Restrict to a specific set of sales order IDs",
    )
```

This is the cache-back pattern (PR #388 onward): every cache-backed `list_<entity>`
tool exposes an `ids` filter that runs as `WHERE id IN (...)` against the typed
cache. Agents holding a batch of IDs use the list tool instead of calling
`get_<entity>` N times. **Exception:** `list_stock_transfers` does not yet expose
`ids` (tracked as a follow-up — agents fall back to per-transfer
`stock_transfer_number` filters until it lands). When adding `ids` to a list tool,
update its docstring to the standard `ids=[1,2,3]` opening (see section 2).

**What we don't do: parallel singular + plural fields.** No `sku` + `skus`,
`variant_id` + `variant_ids`, `customer_id` + `customer_ids` on the request schema.
The four-field shape is mutually-exclusive at runtime, opaque at the MCP-schema layer,
and the source of the agent fallback that motivated PR #397. Always a single field —
either a list (always — `min_length=1` enforces non-empty when the field is required)
or a heterogeneous list with a discriminator type.

### 2. Docstring opening-sentence pattern

The first sentence of every tool docstring follows one of two shapes:

**`list_*` tools — single-line summary with batch hook.**

```
List <entities> with filters — pass `ids=[1,2,3]` to fetch a specific batch by ID (cache-backed[, indexed SQL]).
```

The em-dash (`—`, U+2014) separates the purpose clause from the batch hook. The
parenthetical notes the implementation (cache-backed, indexed SQL, etc.) when it
materially affects the call shape.

For `list_*` tools that don't yet expose `ids` (currently only
`list_stock_transfers`), the hook describes the value of getting multiple rows
back — keeping the same em-dash shape so the convention is recognizable:

```
List stock transfers with filters — returns multiple transfers for discovery or bulk review.
```

This is a **documented exception**, not a target. Adding `ids` to
`list_stock_transfers` (and migrating to the standard `ids=[1,2,3]` form) is
out-of-scope for this ADR — file a feature issue if/when the migration is
prioritised.

**`check_*` / `search_*` / single-item tools — short purpose line, then an
input-shape paragraph that includes the em-dash batch hint.**

```
Check current stock levels for one or more SKUs or variant IDs.

Pass a list of SKUs (strings) or variant IDs (integers) — or mix both — to
``skus_or_variant_ids``. A single item returns a rich stock card; multiple
items return a summary table. Batching N checks in one call is faster than
N separate invocations.
```

Two paragraphs: a short purpose line first (no em-dash on this line — it just
states what the tool does), then the input-shape paragraph that uses the em-dash
to introduce the batch hint and the field name. `get_*` tools follow the same
two-paragraph shape but their input-shape paragraph is the cross-reference
described in section 3.

### 3. `get_*` ↔ `list_*` cross-references

Every `get_<entity>` whose `list_<entity>` partner accepts `ids=[...]` includes this
cross-reference as the second paragraph of its docstring:

```
For multiple <entities> at once, use ``list_<entity>(ids=[...])`` —
it returns a summary table and supports all the same filters.
```

Use double-backticks (RST inline-literal form) for the call; em-dash
continuation. The cross-reference lives *after* the first-line summary and
*before* the parameters / returns sections.

When a `get_*` tool's per-call cost is non-trivial (e.g.,
`get_manufacturing_order_recipe` fetches inline rows that aren't cached), the cross-
reference also explains the cost trade-off: agents holding a batch of IDs should
prefer the list tool's summary path unless they specifically need the rich detail.

**Exception** — `get_manufacturing_order_recipe` cross-references
`get_manufacturing_order` (another `get_*` tool, not a `list_*`) because no
`list_*` partner exists for inline recipe rows. The cross-reference still lives
in the second paragraph; only the target tool differs from the standard form.

### 4. Help-resource sync expectation

`katana_mcp_server/src/katana_mcp/resources/help.py` is a hardcoded mirror of the tool
docstrings — it powers the `katana://help` resource that agents read during
onboarding. When a tool docstring or request schema changes:

- **Workflow examples** that reference the changed tool must be updated to use the
  new field names / signatures.
- **Parameter sections** that enumerate the tool's fields must be re-aligned.
- The change lands in the same PR as the tool change — never as a follow-up.

PR #397 review caught three stale `{"sku": "WIDGET"}` workflow examples after the
schema collapse landed in the source-file docstrings; treat that as the canonical
miss to avoid. The `pr-preparer` agent's project-specific PR-readiness check is
expected to flag help-resource drift; if a future drift slips past it, fold the
detection into the agent's brief.

## Consequences

### Positive

- Agents see batch capability in the first sentence, before deciding on N
  single-item calls.
- Heterogeneous batch fields stop generating four-way fork choices for contributors
  adding new tools.
- `get_*` ↔ `list_*` partner discovery is part of the tool itself, not the agent's
  prior knowledge.
- Help-resource drift is closed at PR review time, before it ships.

### Negative

- One more thing for new tools to comply with — easy to miss until a reviewer
  mentions it.
- Existing tools that don't yet match the conventions look like outliers; back-fill
  is gradual, not all-at-once.
- The "single field" rule means that adding a homogeneous batch shape to a tool that
  currently takes a single value is a breaking change to the request schema — see
  PR #397 for the precedent.

### Neutral

- The conventions are codified in this ADR, not in lint rules. Future contributors
  rely on review and on the `code-modernizer` agent's brief; if drift recurs, escalate
  to a `code-modernizer` rewrite pass.

## Examples in tree

The following tools follow all four conventions and serve as canonical references:

- `check_inventory` (`katana_mcp_server/.../foundation/inventory.py`) — heterogeneous
  collapse (`skus_or_variant_ids: list[str | int]`), order-preserving impl,
  required-field semantics.
- `list_sales_orders` (`.../foundation/sales_orders.py`) — first-line `ids=[...]`
  hook on a cache-backed list tool.
- `get_sales_order` (same file) — second-paragraph cross-reference to
  `list_sales_orders(ids=[...])`.
- `list_manufacturing_orders` / `get_manufacturing_order` — same pair pattern with
  the recipe-row caveat called out in `get_manufacturing_order_recipe`.

When adding a new tool, copy the shape from one of these and adjust.

## Alternatives considered

### Alternative 1: Lint rule (ruff custom check / generated docstring linter)

Catch first-sentence drift, parallel singular+plural fields, and missing cross-
references mechanically. **Rejected for now** — the conventions aren't yet stable
enough across the surface area of the tool set, and a lint rule that fires on every
new tool's first commit would generate more friction than value. Revisit if drift
recurs after this ADR lands; the bar for upgrading is "we reverted to the four-field
pattern in a real PR."

### Alternative 2: Tool-description templates / scaffolding

Add a `scripts/new_tool.py` that emits a docstring shell with the conventions baked
in. **Rejected** — the surface area of differences between tools is too high for one
scaffold to be useful (`list_*` vs. `check_*` vs. `get_*` vs. `create_*` /
`update_*` / `delete_*` all have different opening shapes). Revisit when the
write-tool conventions are also documented.

### Alternative 3: Generate help.py from the tool docstrings

Eliminate the manual sync requirement (section 4) by extracting the workflow examples
and parameter sections from the tool docstrings at build time. **Rejected for
now** — would require docstring sub-section markers (`:: Examples ::`,
`:: Workflows ::`) that don't exist today, and the `katana://help` resource needs
high-level workflow narrative that doesn't belong in any single tool's docstring.
Track separately if the manual-sync bug recurs.

## References

- PR #393 — surfaced batch shapes via first-line docstring updates (precursor)
- PR #397 — schema collapse for `check_inventory`; reviewer flagged the missing
  ADR; this ADR is the deferred Phase 1 work
- ADR-0017 — automated tool documentation (the layered docs strategy this ADR
  refines)
- ADR-0016 — tool interface pattern (the Annotated/Unpack/Pydantic shape these
  conventions live on top of)
- Issue #398 — this ADR's tracking issue
- `katana_mcp_server/src/katana_mcp/resources/help.py` — the help-resource mirror
- `.claude/agents/code-modernizer.md` — escalation path if drift recurs
- `.claude/agents/pr-preparer.md` — checks for help-resource drift at PR time
