"""Read-only money/decimal wire-type sweep for #735.

Harvests the *raw* JSON type (str / int / float / null) of every
numeric-suspect field across the live test tenant, so we can tell which
fields Katana returns as fixed-precision **strings** despite our spec
modelling them as ``number``.

Read-only: GET only, no mutation. Goes through
:func:`katana_public_api_client.testing.make_test_client` — the sanctioned
entry point for live-tenant access — which reads ``KATANA_TEST_API_KEY``
(no silent fallback to the prod key) and centralizes the base URL. Raw-wire
GETs use the client's underlying ``get_async_httpx_client()`` so we observe
the unparsed JSON types the generated models would otherwise coerce away.

``make_test_client`` prefers ``os.environ`` over ``.env``, so in a worktree
export the key from the repo-root checkout first (the worktree ``.env`` has
no key)::

    # from the repo root checkout:
    export KATANA_TEST_API_KEY=$(grep '^KATANA_TEST_API_KEY=' .env | cut -d= -f2-)
    uv run python scripts/probe_money_fields.py

Output: per endpoint, every leaf field whose name looks like money/decimal,
with the set of wire types observed and a sample value. A field observed as
``str`` is drift (spec says ``number``); int/float-only is fine; null-only
stays unverifiable.

Scope caveats (this is a diagnostic, not an exhaustive auditor):

- Observations are keyed by ``(immediate-parent-key, field-name)``, so two
  nested objects that share both a parent key *and* a field name merge into
  one bucket. The failure mode is conservative — merging only ever *adds*
  observed types, so it can over-flag a field for manual review, never hide
  a real ``str`` drift.
"""

from __future__ import annotations

import asyncio
import json
import sys
from collections import defaultdict
from typing import Any

import httpx

from katana_public_api_client.testing import make_test_client

# field-name substrings that flag a money/decimal-suspect leaf
KW = (
    "cost",
    "price",
    "quantity",
    "time",
    "value",
    "rate",
    "amount",
    "total",
    "per_unit",
    "per_hour",
    "parameter",
    "discount",
    "conversion",
    "landed",
)

# Endpoints to sweep. Each entry: (path, params). The probe walks every
# record returned (plus nested rows), recording leaf field types. limit kept
# high to maximise the chance of catching a non-null sample.
ENDPOINTS: list[tuple[str, dict[str, Any]]] = [
    ("/sales_orders", {"limit": 100, "extend": "sales_order_rows"}),
    ("/sales_order_rows", {"limit": 250}),
    ("/purchase_orders", {"limit": 100}),
    ("/purchase_order_rows", {"limit": 250}),
    ("/manufacturing_orders", {"limit": 100}),
    ("/manufacturing_order_operation_rows", {"limit": 250}),
    ("/manufacturing_order_recipe_rows", {"limit": 250}),
    ("/manufacturing_order_productions", {"limit": 100}),
    ("/product_operation_rows", {"limit": 250}),
    ("/batch_stocks", {"limit": 250}),
    ("/stock_adjustments", {"limit": 100}),
    ("/stock_transfers", {"limit": 100}),
    ("/inventory_movements", {"limit": 250}),
    ("/variants", {"limit": 100}),
    ("/products", {"limit": 100}),
    ("/price_list_rows", {"limit": 250}),
    ("/tax_rates", {"limit": 100}),
    ("/customers", {"limit": 100}),
    ("/inventory", {"limit": 250}),
]


def _typename(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float"
    if isinstance(v, str):
        return "str"
    return type(v).__name__


def _walk(
    node: Any,
    parent: str,
    acc: dict[tuple[str, str], dict[str, Any]],
) -> None:
    """Record types for every money-suspect leaf, keyed by (parent, field)."""
    if isinstance(node, dict):
        for k, v in node.items():
            if isinstance(v, (dict, list)):
                _walk(v, k, acc)
            elif any(kw in k for kw in KW):
                slot = acc[(parent, k)]
                slot.setdefault("types", set()).add(_typename(v))
                # remember a representative non-null sample
                if v is not None and "sample" not in slot:
                    slot["sample"] = v
    elif isinstance(node, list):
        for item in node:
            _walk(item, parent, acc)


async def main() -> None:
    acc: dict[tuple[str, str], dict[str, Any]] = defaultdict(dict)
    async with make_test_client() as client:
        http = client.get_async_httpx_client()
        for path, params in ENDPOINTS:
            try:
                r = await http.get(path, params=params)
            except httpx.HTTPError as exc:
                print(f"  {path:42} ERROR {exc}", file=sys.stderr)
                continue
            if r.status_code != 200:
                print(f"  {path:42} HTTP {r.status_code}", file=sys.stderr)
                continue
            body = r.json()
            data = body.get("data", body) if isinstance(body, dict) else body
            n = len(data) if isinstance(data, list) else 1
            _walk(data, path.strip("/"), acc)
            print(f"  {path:42} ok ({n} records)", file=sys.stderr)

    # Report grouped by parent object key.
    by_parent: dict[str, list[tuple[str, dict[str, Any]]]] = defaultdict(list)
    for (parent, field), slot in acc.items():
        by_parent[parent].append((field, slot))

    out: dict[str, Any] = {}
    print("\n================ MONEY-FIELD WIRE TYPES ================\n")
    for parent in sorted(by_parent):
        print(f"## {parent}")
        for field, slot in sorted(by_parent[parent]):
            types = sorted(slot.get("types", set()))
            sample = slot.get("sample", "—")
            drift = "str" in types
            flag = "  <-- STRING DRIFT" if drift else ""
            print(f"   {field:34} {','.join(types):20} sample={sample!r}{flag}")
            out[f"{parent}.{field}"] = {"types": types, "sample": sample}
        print()

    with open("/tmp/money_fields_probe.json", "w") as fh:
        json.dump(out, fh, indent=2, default=str)
    print("Wrote /tmp/money_fields_probe.json")


if __name__ == "__main__":
    asyncio.run(main())
