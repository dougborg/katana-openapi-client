# Prefab UI — Rendering Pitfalls and Contracts

Prefab cards are emitted by MCP tools as JSON envelopes that the host (Claude Desktop,
Cowork, the browser-render harness) hydrates into a React tree inside an iframe. The
JSON wire is forgiving (it accepts most pydantic shapes); the JS renderer is not. The
rules below come from real production failures — cards that passed unit tests but
crashed in the host, or tools that promised a widget in their docstring and silently
emitted none.

When you change anything that emits a Prefab card, run `uv run poe test-browser` (needs
one-time `uv run playwright install chromium`) — the browser-render harness in
`katana_mcp_server/tests/browser/` is the only thing that exercises the real JS
renderer.

Related tests:

- `katana_mcp_server/tests/test_prefab_ui.py` — unit tests on the wire envelope.
- `katana_mcp_server/tests/browser/` — headless Chromium harness that proves cards
  actually mount.

______________________________________________________________________

## `DataTable.rows` requires mustache `{{ key }}`, never a bare string

The Python pydantic field type accepts `rows: str` either way, but the JS renderer
**crashes the entire iframe** with `t.some is not a function` if it sees a bare
state-key string — it treats the string as the rows array itself, calls `.some()` on a
string, and the React tree never mounts.

Always use the mustache form for state-bound rows:

```python
DataTable(rows="{{ items }}")
DataTable(rows="{{ stock.by_location }}")  # dotted paths supported
```

`_assert_state_bindings_resolve` in `tests/test_prefab_ui.py` enforces this on every
state-bound `DataTable`. The browser-render harness then proves the rendered card
actually mounts in headless Chromium — the prior unit-test contract (`to_json()` returns
a dict with `$prefab`) was insufficient because the wire envelope can be "valid but
unrenderable."

Discovered while investigating #629; bit every state-bound DataTable in the repo
(search, inventory, verification, batch_recipe, modification card).

______________________________________________________________________

## Browser-test tool stubs must mirror production wire shape via `make_tool_result`

When stubbing an MCP tool in `tests/browser/render_test_server.py`, return
`make_tool_result(response_pydantic, ui=ui_card)` — exactly like real tool code in
`src/katana_mcp/tools/foundation/`. A hand-built
`ToolResult(content="ok", structured_content=raw_dict)` silently passes browser tests
but misses production-shape bugs.

In particular, `$result` in the `on_success` Rx context resolves to the apply tool's
`structured_content` — a `PrefabApp` wire envelope keyed by `$prefab` / `view` / `state`
— **not** the raw `ModificationResponse` shape. A stub that returns a raw
`ModificationResponse` therefore exposes an `actions` field that doesn't exist in
production, so the rail's `Rx("$result.actions")` looks like it resolves correctly in
test but doesn't in real life.

Rule: **a stub that doesn't match production wire shape is worse than no stub.**
Discovered via Copilot review on #634; the broken live-tick that "passed" against the
bad stub is tracked for proper fix in #645.

______________________________________________________________________

## A tool's docstring promises must match the UI it actually emits

`register_preview_tool` auto-appends "Preview→apply: ... returns a Prefab card with
Confirm/Cancel buttons" to the tool's docstring. Hosts read that promise and look for a
widget. If the tool is registered with `register_preview_tool` but **without**
`meta=UI_META` (or it returns via `make_json_result` with no Prefab envelope), the
host's widget-fetch fails — Claude Desktop crashes its internal `read_widget_context`
with `tool_name=undefined` because no widget exists for the tool the host believed was
emitting one. The tool result still returns successfully, but the iframe renders
nothing.

The contract is bidirectional:

- Every `register_preview_tool` call **must** pair `meta=UI_META` with a real Prefab
  card (built via `make_tool_result(response, ui=...)`) — never the docstring without
  the card.
- Conversely, tools that emit no UI must use plain `mcp.tool(...)` and return a JSON
  `ToolResult` — prefer `make_json_result(response)` when the default dump works; build
  `ToolResult(...)` inline when the tool needs to thread request-driven kwargs through
  `model_dump_json` / `model_dump` (e.g., `get_manufacturing_order` composes an
  `exclude={...}` selector from `include_rows` / `include_operation_rows` /
  `include_productions` and adds `exclude_none=True` when `verbose=False`). Either way,
  **not** `register_preview_tool` — the docstring promise has to match reality.

Caught via a live Claude Desktop session against `create_stock_adjustment` (fixed in
#649); the same misregistration still applies to `create_stock_transfer` — tracked in
#639. (`fulfill_order` is correctly wired with `meta=UI_META`; its remaining work is the
direct-apply rail migration in #638, not this misregistration.)

______________________________________________________________________

## Help resource drift

`katana_mcp_server/.../resources/help.py` contains hardcoded tool documentation. When
adding or modifying tool parameters, also update the help resource content to stay in
sync. The `pr-preparer` agent flags this on PR readiness.
