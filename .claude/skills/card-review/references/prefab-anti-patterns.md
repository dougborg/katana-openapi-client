# Prefab UI Anti-Patterns

Catalog of patterns that violate the user-centric-content rule. Each entry shows
the bad shape (with a real `prefab_ui.py` excerpt from current or recently-fixed
code), the symptom the operator sees, and the fix.

The numbering matches the table in `SKILL.md` "Scan against the seven anti-patterns".

---

## 1. Redundant text dump next to a table/widget

**Symptom.** The card lists every row twice — once as a Muted text block, once as a `DataTable` — so the operator scrolls past 9 lines of "Row 108854645: ship 1 of …" to reach the table that says the same thing.

**Detection grep:**

```text
grep -n "for .* in response\[" katana_mcp_server/src/katana_mcp/tools/prefab_ui.py
grep -n "Muted(content=" katana_mcp_server/src/katana_mcp/tools/prefab_ui.py | head
```

Cross-check: any `Muted` followed within ~5 lines by `DataTable` over the same response key is suspect.

**Historical bad example** (the fulfill card before phase 2):

```python
def _render_inventory_updates(response, *, label="Inventory Changes:"):
    if response.get("inventory_updates"):
        Muted(content=label)
        for update in response["inventory_updates"]:
            Text(content=f"  {update}")
```

The strings in `inventory_updates` are server-generated `"Row {row_id}: ship {qty} of {label}"` lines that also become rows in the `_render_fulfill_per_row_table` DataTable below.

**Fix.** Pick one rendering. The DataTable carries structured columns (Item / SKU / Qty / Serials / Batch / Line Total) — keep it. Delete the text block. Single-line context (e.g., a `picked_date`) promotes to a Metric, not a re-rendered text line.

---

## 2. Internal IDs surfaced in user-facing text

**Symptom.** Card body shows `Variant ID: 12345`, `Supplier: Acme (ID: 67)`, `Row 108854645: …`. The number means nothing to the operator and crowds out the name.

**Detection grep:**

```text
grep -nE "f\"\w+ ID:" katana_mcp_server/src/katana_mcp/tools/prefab_ui.py
grep -nE "f\"#\{" katana_mcp_server/src/katana_mcp/tools/prefab_ui.py
grep -nE "Text\(content=f\".*_id" katana_mcp_server/src/katana_mcp/tools/prefab_ui.py
```

**Bad shapes:**

```python
Text(content=f"Variant ID: {variant_id}")
Text(content=f"Supplier: {name} (ID: {supplier_id})")
Text(content=f"Location ID: {location_id}")
```

**Fix.** `_render_party_line("Supplier", name=..., entity_id=..., entity_kind="supplier")`. The helper:

- Renders the name as a `Link` to the Katana web UI when `entity_kind` resolves.
- Falls back to plain `"<Label>: <name>"` (no ID parenthetical) when no `entity_kind` is supplied. The structured response still carries the ID for programmatic consumers; the card text doesn't echo it next to its resolved name when there's no click-through to anchor.
- Falls back to `"<Label> ID: <id>"` only when name is missing — and that's a *signal*, not the target shape: resolve the name impl-side via `resolve_entity_name(catalog, Cached*, id, entity_label="…")`.

If a Variant ID appears in body text, the SKU should usually replace it entirely. SKUs are the human-facing identifier; variant IDs are wire-shape.

---

## 3. Missing party / address reference info on an order card

**Symptom.** An SO / PO / MO confirmation card has no customer / supplier / location name, no shipping address. The operator can confirm the action but can't verify *who* it ships to or *where* it draws from.

**Detection:**

```text
# List the order-related card builders.
rg -nE "^def build_(so|po|mo|fulfill|receipt)_.*_ui" katana_mcp_server/src/katana_mcp/tools/prefab_ui.py

# For any card found above, check that its body uses the party-line /
# address-block helpers. Run after reading the function with the LSP
# (``goToDefinition``) or a Read on the spanning line range.
rg -nE "_render_party_line|_render_address_block" katana_mcp_server/src/katana_mcp/tools/prefab_ui.py
```

A card-builder name from the first command whose function body (located
via LSP / Read) doesn't appear in the second command's hits is a finding.

**Fix.** Tier 3 reference block, before the Tier 3 per-row table:

```python
_render_party_line(
    "Customer",  # or "Supplier", "Location"
    name=response.get("customer_name"),
    entity_id=response.get("customer_id"),
    entity_kind="customer",
)
if shipping_address:
    _render_address_block("Shipping Address", shipping_address)
if billing_address:  # only when not equivalent to shipping
    _render_address_block("Billing Address", billing_address)
```

Impl side adds the response fields (`customer_name`, `shipping_address: dict[str, Any] | None`, etc.) and resolves names via the typed cache.

---

## 4. Abstract verbs over content

**Symptom.** Columns labeled `Operation`, `Target`, `Changes`, `# of actions`. The user has to mentally translate "3 field(s) changed" back to "what changed?".

**Detection:**

```text
grep -nE "\"Operation\"|\"Target\"|n_actions|f\"\{verb_label\}\"" katana_mcp_server/src/katana_mcp/tools/prefab_ui.py
```

**Historical bad example** (modification preview card):

```python
_ACTION_COLUMNS = [
    DataTableColumn(key="num", header="#"),
    DataTableColumn(key="operation", header="Operation"),
    DataTableColumn(key="target", header="Target"),
    DataTableColumn(key="changes", header="Changes"),
    DataTableColumn(key="status", header="Status"),
]

# elsewhere:
target_label = f"#{target}"  # raw entity_id
summary = f"{n_changes} field(s) changed"  # count, not content
```

**Fix.** Promote to a per-entity renderer (`_render_po_entity_view`-style) when the entity type is known. For unknown types, the column set becomes `Field / Before / After / Status` keyed off the entity's `prior_state` vs `changes`. Render each entity as its own sub-card body — never a row in a table-of-actions.

Title drops `"N action(s)"` — single-action shows `"<entity_type> <entity_no>"`; multi-action shows `"<N> <entity_type>s"`.

---

## 5. Wire shape leaking to UI

**Symptom.** Snake_case headers in DataTables (`recipe_row_id`, `inventory_movements_id`), raw enum values (`AddressEntityType.SHIPPING` instead of `Shipping`), `model_dump()` output rendered as a JSON-ish dump.

**Detection:**

```text
grep -nE "header=\"\w+_\w+\"" katana_mcp_server/src/katana_mcp/tools/prefab_ui.py
grep -nE "\.value\b" katana_mcp_server/src/katana_mcp/tools/prefab_ui.py | grep -v "warnings\|metric"
```

**Bad shapes:**

```python
DataTableColumn(key="recipe_row_id", header="Row ID")  # wire identifier, no user value
DataTableColumn(key="mo_id", header="MO")              # raw integer; user wants order_no
Text(content=f"Type: {address.entity_type.value}")     # enum dump
```

**Fix.** Resolve wire IDs to user-facing labels impl-side. For columns that exist purely as drill-down anchors (e.g. "click to see the underlying MO"), prefer a per-row Katana URL on a name column over a separate ID column.

---

## 6. Buried decision context

**Symptom.** The thing the operator confirms (per-row table, address block, before/after diff) sits below 3+ warnings, metrics, or status badges. The operator's eye lands on the noise before the signal.

**Detection.** Read the card's `CardContent` block top-to-bottom. The intended order is:

1. **Tier 1 — Identity:** `_render_preview_header` (title + entity badge + status badge).
2. **Tier 2 — Decision metrics:** `Metric` row (Total / Item count / Picked date).
3. **Tier 3 — Reference data:** party lines + address blocks + per-row DataTable / per-field diff.
4. **Tier 4 — Actions:** `_render_preview_footer` with Confirm/Cancel + secondary buttons.

Warnings rail (`BLOCK:`-prefixed) goes *under* Tier 3, immediately above Tier 4. Non-blocking informational warnings go inside Tier 3 next to what they describe — never inside Tier 1.

**Fix.** Reorder. If a card has a `Separator` before the DataTable, the table is buried — move the table up so it's the first body element the eye sees after the Tier 2 metrics.

---

## 7. Helper-fallback masking

**Symptom.** A card calls `_render_party_line(name=None, entity_id=<id>, …)` (or any party helper without a resolved name). The helper *appears* in the diff, the audit grep for "raw ID in Text" misses it, but the rendered output is still `"<Label> ID: <id>"` per the helper's documented fallback. The card looks clean at the call site but the operator still sees a bare numeric ID.

**Detection grep:**

```text
grep -n "_render_party_line" katana_mcp_server/src/katana_mcp/tools/prefab_ui.py | grep -E "name=None|name=response\.get"
```

Also: any call where `response.get("<thing>_name")` is referenced but the response model has no `<thing>_name` field — the call always degrades to ID-only.

**Bad shape** (from `build_so_create_ui` before the LOW-band fix):

```python
_render_party_line(
    "Location",
    name=None,  # SalesOrderResponse has no location_name
    entity_id=response.get("location_id"),
)
```

The comment correctly documents *why* it's None — but the user still sees `"Location ID: 17"`. The fix is impl-side, not at the call.

**Fix.** Resolve the name on the impl side via the typed cache:

```python
location_name, name_warning = await resolve_entity_name(
    services.typed_cache.catalog,
    CachedLocation,
    location_id,
    entity_label="Location",
)
```

Then add `location_name` to the response model and pass it through. Pattern: grep `resolve_entity_name` in `katana_mcp_server/src/katana_mcp/tools/foundation/` for current call sites (sales_orders / purchase_orders / stock_transfers / orders / inventory).

When the cache miss + API fallback can't resolve a name, `resolve_entity_name` returns a non-None `warning` string — surface that on the response's `warnings` list so the operator sees "couldn't resolve Location name" instead of a silent ID-only line.

---

## 8. Thin post-action DTO (and the single-row table it spawns)

**Symptom.** A *create* / post-action card renders only id + name + a success
message because the tool's response model is thin — even though the Katana
`.create()` call returned a fully-populated entity. The operator just shipped a SKU
and the card can't tell them whether it's sellable, what the price is, who the
supplier is, or what to do next. The card looks "done" but answers nothing.

**Root cause.** The MCP response DTO (`CreateProductResponse`,
`CreateItemResponse`, …) was authored thin (id/name/sku/uom/message) while the API
result object (`Product` / `Material` attrs model) already carries `variants[]`,
`configs`, `is_sellable`, `is_producible`, `batch_tracked`, `serial_tracked`,
`category_name`, `additional_info`, and the supplier FK. The fix is to **widen the
DTO and map from the result you already have — not to add a second fetch** and not to
ship a bare card.

**Detection:**

```text
# A build_*_create / *_success card whose body is just Name + SKU + message,
# with no _render_<entity>_entity_view call:
rg -nE "^def build_\w+_(create|success)_ui" katana_mcp_server/src/katana_mcp/tools/prefab_ui.py
# Cross-check the response model — if it's id/name/sku/message only while a
# get_<entity> response is exhaustive, the create DTO is thin.
```

**Fix.** Add an `ItemCreateView`-style mixin of the four-tier fields to the create
response models; populate it in the impl from the `.create()` result via a
`build_<entity>_create_view(...)` helper that reuses the same converters as the read
path (`_variant_to_summary`, `_config_to_info`, `_supplier_to_info`). Resolve the
supplier/customer/location *name* from the typed cache (the result carries only the
FK) — see anti-pattern #7. Then render via the shared `_render_<entity>_entity_view`.

**Single-row table corollary.** A freshly-created item always has exactly *one*
variant. Rendering it as a searchable/paginated DataTable is needless chrome (a
table-of-one). Surface the single child's facts as inline reference lines instead
(SKU + prices), keyed off a `collapse_single_variant=True` flag on the shared entity
view. Reserve the DataTable + per-row drill-down for the genuine multi-child read
card. Generalizes the "pick one rendering" rule of anti-pattern #1 and the layout
economy of anti-pattern #6.

> **Drift note.** `configs` / `config_attributes` landed on **`modify_item`** (#581),
> *not* on the create response models — don't assume a create DTO surfaces configs
> just because the modify path does. Verify the model before relying on a field.

---

## Process notes

- New anti-patterns spotted during a `/card-review` run should land here, not in the SKILL.md. The skill loads `references/` lazily; the catalog can grow without bloating the skill's main file.
- Each bad-example excerpt above is a *historical* shape from this repo. When a card is rewritten, the excerpt stays — it's documentation of what the rewrite fixed, not a current bug.
- Examples should be quoted from real code. Synthetic / made-up bad examples drift faster than real ones.
