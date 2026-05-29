# Positive Helpers — When to Reach for Each

Project-canonical rendering helpers in `katana_mcp_server/src/katana_mcp/tools/prefab_ui.py`.
Cards that bypass these helpers and roll their own rendering are the source of every
anti-pattern in `prefab-anti-patterns.md`.

Pair each finding from a `/card-review` run with the matching helper here so the
remediation is concrete.

Line numbers are intentionally omitted — `prefab_ui.py` evolves and hard-coded
positions drift faster than this file is maintained. Use `grep -n "^def
_render_party_line" katana_mcp_server/src/katana_mcp/tools/prefab_ui.py` (or LSP
`goToDefinition`) to jump to the current location.

---

## `_render_party_line`

**Signature:**

```python
def _render_party_line(
    label: str,
    *,
    name: str | None,
    entity_id: int | None,
    entity_kind: EntityKind | None = None,
) -> None
```

**Use when:** a card refers to a Katana entity (customer / supplier / location / variant) and wants to surface its identity.

**Behavior:**

- `name` + `entity_kind` → renders `<label>: <Link name>` (Katana web URL).
- `name` only (no `entity_kind`, or `entity_kind` has no web URL) →
  `<label>: <name>`. The entity_id is dropped from the visible text —
  it's still on the response for programmatic consumers, but the card
  doesn't echo it next to its resolved name when there's no
  click-through to anchor (anti-pattern #2 — don't double-print a raw
  ID alongside its name).
- Neither name nor URL → `<label> ID: <entity_id>`. Last-resort
  fallback when impl-side name resolution couldn't fill `name`; the
  matching impl path should also append a cache-miss advisory to
  `warnings` so the operator sees *why* the name is missing.
- `entity_id is None` → renders nothing (skip).

**Reach for it instead of:**

```python
Text(content=f"Customer: {name} (ID: {customer_id})")
Text(content=f"Location ID: {location_id}")
```

**Call example** (`build_so_create_ui` — grep `_render_party_line\("Customer"`):

```python
_render_party_line(
    "Customer",
    name=response.get("customer_name"),
    entity_id=response.get("customer_id"),
    entity_kind="customer",
)
```

---

## `_render_party_diff_line`

**Signature:**

```python
def _render_party_diff_line(
    label: str,
    *,
    id_change: FieldChangeView,
    name_change: FieldChangeView | None,
    prior_name: str | None,
) -> None
```

**Use when:** a modify card's party (supplier / customer / location) is *changing* — renders `<before-name> (<before-id>) → <after-name> (<after-id>)` with the `✗` failure gutter.

**Reach for it instead of:** custom `f"{old} → {new}"` strings inside `Text(content=…)`.

---

## `_render_address_block`

**Signature:**

```python
def _render_address_block(label: str, address: dict[str, Any]) -> bool
```

**Use when:** any card displays a postal address (shipping, billing, supplier address). Returns `False` if every field except `entity_type` was empty (caller decides whether to skip the section).

**Behavior:**

- Reads `first_name`/`last_name`/`company`/`line_1`/`line_2`/`city`/`state`/`zip`/`country`/`phone`.
- Composes the recipient/company/street/locality/country lines, skipping blank components.
- Wire-format note: reads `address["zip"]` (the attrs `to_dict()` emits the wire name).

**Companion:** `_addresses_are_equivalent(a, b)` — call before rendering a Billing block to dedup against Shipping. The canonical implementation lives in `katana_mcp/tools/_addresses.py` (shared between impl + UI); `prefab_ui.py` re-exports the legacy private name.

**Reach for it instead of:** manually building a multi-line address string in `Text(content=…)`.

**Call example** (`_render_customer_entity_view` — grep for the function name):

```python
ship = next((a for a in addresses if a.get("entity_type") == "shipping"), None)
bill = next((a for a in addresses if a.get("entity_type") == "billing"), None)
if ship:
    _render_address_block("Shipping Address", ship)
if bill and not _addresses_are_equivalent(ship or {}, bill):
    _render_address_block("Billing Address", bill)
```

---

## `_render_field_diff_line`

**Use when:** modify card needs a scalar before/after line (status, notes, arrival date, etc.). Handles the `(prior unknown)` case and the 2-character `✗` gutter for failed fields.

**Reach for it instead of:**

```python
Text(content=f"Status: {old} → {new}")
```

Or a 3-column DataTable (`Field / Old / New`) when the field count is small — `_render_field_diff_line` is cleaner for scalar diffs.

---

## `_render_failed_changes_block`

**Use when:** modify card needs to surface per-field apply failures *without* destabilizing the unchanged-row layout. Renders a single Alert block at the bottom listing every failed field + its server error.

**Reach for it instead of:** inline error text after each failed field (jitter), or a generic "some changes failed" Alert with no diagnostics (unhelpful).

---

## `_render_preview_header` / `_render_preview_footer`

**Use when:** any preview/applied card that needs the standard four-tier layout (title prefix + entity badge + status badge in header; Confirm + Cancel + optional next-action buttons in footer).

**Reach for them instead of:** hand-rolled `CardHeader` + `CardTitle` + `Badge` triplet (drift risk — every card ends up with subtly different gap/variant choices).

**Call example** (`build_po_create_ui`):

```python
_render_preview_header(
    title_prefix="Purchase Order",
    entity="purchase_order",
    order_number=order_number,
    status=status,
)
# … body …
_render_preview_footer(
    title_prefix="Purchase Order",
    block_warnings=block_warnings,
    confirm_label="Confirm & Create Purchase Order",
    apply_action=apply_action,
    cancel_action=cancel_action,
)
```

---

## `_render_<entity>_entity_view` (the shared Tier 2+3 renderer)

**Examples:** `_render_po_entity_view`, `_render_item_entity_view`,
`_render_so_entity_view`, `_render_customer_entity_view`.

**Signature shape:**

```python
def _render_item_entity_view(
    item: dict[str, Any],
    *,
    changes: dict[str, FieldChangeView] | None = None,
    collapse_single_variant: bool = False,
) -> list[str]  # returns the block-warning list
```

**Use when:** an entity (PO / SO / item / customer) has both a *create* card and
a *modify* card — and often a *detail* read card too. Factor the Tier 2 metrics +
Tier 3 reference block into ONE `_render_<entity>_entity_view` that all of them call,
rather than re-rendering the same fields three times (and drifting). This is the
structural fix behind anti-pattern #4 ("promote to a per-entity renderer").

**Behavior contract:**

- Takes the entity dict; renders metrics + reference lines; returns the
  block-warning list (`_render_warnings_block(entity.get("warnings"))`) so the caller
  gates its Confirm button.
- `changes=None` → no diff overlay (create + detail cards). The modify card passes a
  `{wire_field: FieldChangeView}` map and the helper swaps changed lines for their
  before→after form. **Add the `changes=` seam when you build the create card** even
  if the modify card doesn't exist yet — it's far cheaper than retrofitting the
  signature later (#555 left the seam for #726).
- Must be called inside `with CardContent(), Column(gap=3):`.

**Single-row collapse:** `collapse_single_variant=True` (create card) renders a
single child's facts inline instead of a one-row DataTable — see anti-pattern #8. The
multi-child read card leaves it `False` to keep the table + per-row drill-down.

**Reach for it instead of:** copy-pasting the metric/reference block across
`build_<entity>_create_ui` and `build_<entity>_modify_ui`.

---

## Resolving names impl-side

Helpers above all assume the response already carries the user-facing `*_name` field.
The impl side resolves names via the typed cache:

**`resolve_entity_name`** — in `katana_mcp_server/src/katana_mcp/tools/tool_result_utils.py`

```python
async def resolve_entity_name(
    catalog: Any,
    cached_cls: Any,
    entity_id: int,
    *,
    entity_label: str,
) -> tuple[str | None, str | None]
```

Returns `(name, warning)`. If the cache miss / API fallback can't resolve a name, the warning string surfaces on the response so the operator sees a "couldn't resolve <Label> name" note instead of a silent empty field.

**Call sites to pattern-match** (grep `resolve_entity_name` in `foundation/`):

- `sales_orders.py` — customer + location name on SO create.
- `purchase_orders.py` — supplier name on PO create.
- `catalog.py` / `items.py` — default-supplier name on item create
  (`build_item_create_view`); the create result carries only the FK.
- `stock_transfers.py` — location names on stock transfer.
- `orders.py` — customer name on fulfill SO.
- `inventory.py` — location name on stock-adjustment create/update/delete.

Cache classes (`CachedCustomer`, `CachedSupplier`, `CachedLocation`, etc.) live in
`katana_public_api_client/models_pydantic/_generated/`.

---

## When to add a new helper

If a `/card-review` pass surfaces the same anti-pattern in 2+ cards and no helper
above fits, that's the signal to write a new helper. Naming follows the existing
pattern — `_render_<noun>_<shape>` for render helpers, `_<resolver-target>_section`
for impl-side composites. Add the new helper to this file when it lands.
