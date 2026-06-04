"""Seeded money/decimal wire-type sweep for #735 — the write-side pass.

The read-only ``probe_money_fields.py`` left a residual set of ``number``-typed
fields it could not confirm because no record carrying a non-null value exists
on the test tenant. This script *creates* one SDT-tagged record per residual
field, GETs it back, prints the raw wire type, then deletes everything it made.

Mutating — POST/DELETE against the **test tenant only** (``KATANA_TEST_API_KEY``,
never the prod key). Every created entity is SDT-tagged and appended to a
cleanup file (``/tmp/seed_money_cleanup.jsonl``) the instant it's created, so a
crash mid-run still leaves a deletable trail. Cleanup runs in reverse at the
end of a normal run; re-run with ``cleanup`` to drain the file by hand::

    export KATANA_TEST_API_KEY=$(grep '^KATANA_TEST_API_KEY=' .env | cut -d= -f2-)
    uv run python scripts/seed_money_fields.py            # seed, sample, clean up
    uv run python scripts/seed_money_fields.py cleanup     # drain leftover artifacts

A sampled value of type ``str`` is drift (spec says ``number``); int/float is
fine. Dependency-chained entities (price-list row, stock transfer, outsourced
recipe row) skip gracefully if a prerequisite can't be met on the tenant.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

BASE_URL = os.environ.get("KATANA_TEST_BASE_URL", "https://api.katanamrp.com/v1")
SDT_PREFIX = "SDT-735-seed"
CLEANUP_FILE = Path("/tmp/seed_money_cleanup.jsonl")

# Reusable tenant fixtures discovered read-only (locations/suppliers/variants).
LOCATION_A = 184870  # Main Location
LOCATION_B = 184871  # 2nd Location
SUPPLIER_EUR = 1606755  # Paint Supplier [DEMO] (currency EUR)
VARIANT = 40793076  # an existing variant to reference in rows

# field -> observed wire type, filled as we sample
RESULTS: dict[str, dict[str, Any]] = {}


def _key() -> str:
    k = os.environ.get("KATANA_TEST_API_KEY")
    if not k:
        print(
            "KATANA_TEST_API_KEY not set — export from repo-root .env.", file=sys.stderr
        )
        sys.exit(2)
    return k


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


def _record(delete_path: str) -> None:
    """Append a deletable artifact to the cleanup file immediately."""
    with CLEANUP_FILE.open("a") as fh:
        fh.write(json.dumps({"delete_path": delete_path}) + "\n")


def _sample(field: str, value: Any) -> None:
    t = _typename(value)
    drift = "  <-- STRING DRIFT" if t == "str" else ""
    RESULTS[field] = {"type": t, "sample": value}
    print(f"   {field:48} {t:8} sample={value!r}{drift}")


def _tag(suffix: str) -> str:
    return f"[{SDT_PREFIX}] {suffix}"


def seed_customer(c: httpx.Client) -> None:
    print("\n## Customer.discount_rate")
    r = c.post("/customers", json={"name": _tag("discount probe"), "discount_rate": 5})
    if not r.is_success:
        print(f"   skip — POST /customers {r.status_code}: {r.text[:160]}")
        return
    cid = r.json()["id"]
    _record(f"/customers/{cid}")
    got = c.get(f"/customers/{cid}").json()
    _sample("Customer.discount_rate", got.get("discount_rate"))


def seed_material(c: httpx.Client) -> None:
    print("\n## Material.purchase_uom_conversion_rate + Variant.minimum_order_quantity")
    payload = {
        "name": _tag("uom+moq probe"),
        "uom": "pcs",
        "purchase_uom": "box",
        "purchase_uom_conversion_rate": 12,
        "variants": [
            {
                "sku": f"{SDT_PREFIX}-mat",
                "purchase_price": 5,
                "minimum_order_quantity": 7,
            }
        ],
    }
    r = c.post("/materials", json=payload)
    if not r.is_success:
        print(f"   skip — POST /materials {r.status_code}: {r.text[:160]}")
        return
    mat = r.json()
    mid = mat["id"]
    _record(f"/materials/{mid}")
    got = c.get(f"/materials/{mid}").json()
    _sample(
        "Material.purchase_uom_conversion_rate", got.get("purchase_uom_conversion_rate")
    )
    variants = got.get("variants") or []
    if variants:
        _sample(
            "Variant.minimum_order_quantity", variants[0].get("minimum_order_quantity")
        )


def seed_purchase_order(c: httpx.Client) -> None:
    print("\n## PurchaseOrderRow.conversion_rate + purchase_uom_conversion_rate")
    payload = {
        "supplier_id": SUPPLIER_EUR,
        "location_id": LOCATION_A,
        "order_no": f"{SDT_PREFIX}-po",
        "purchase_order_rows": [
            {
                "variant_id": VARIANT,
                "quantity": 4,
                "price_per_unit": 3.5,
                "purchase_uom": "box",
                "purchase_uom_conversion_rate": 12,
            }
        ],
    }
    r = c.post("/purchase_orders", json=payload)
    if not r.is_success:
        print(f"   skip — POST /purchase_orders {r.status_code}: {r.text[:200]}")
        return
    po = r.json()
    pid = po["id"]
    _record(f"/purchase_orders/{pid}")
    got = c.get(f"/purchase_orders/{pid}").json()
    print(f"   (PO currency={got.get('currency')!r})")
    rows = got.get("purchase_order_rows") or []
    if rows:
        _sample("PurchaseOrderRow.conversion_rate", rows[0].get("conversion_rate"))
        _sample(
            "PurchaseOrderRow.purchase_uom_conversion_rate",
            rows[0].get("purchase_uom_conversion_rate"),
        )


def seed_price_list(c: httpx.Client) -> None:
    print("\n## PriceListRow.amount")
    r = c.post("/price_lists", json={"name": _tag("amount probe")})
    if not r.is_success:
        print(f"   skip — POST /price_lists {r.status_code}: {r.text[:160]}")
        return
    plid = r.json()["id"]
    _record(f"/price_lists/{plid}")
    rr = c.post(
        "/price_list_rows",
        json={
            "price_list_id": plid,
            "price_list_rows": [{"variant_id": VARIANT, "amount": 9.99}],
        },
    )
    if not rr.is_success:
        print(f"   skip — POST /price_list_rows {rr.status_code}: {rr.text[:200]}")
        return
    body = rr.json()
    created = body.get("data", body)
    rows = created if isinstance(created, list) else [created]
    if rows and isinstance(rows[0], dict):
        rid = rows[0].get("id")
        if rid:
            _record(f"/price_list_rows/{rid}")
        _sample("PriceListRow.amount", rows[0].get("amount"))


def seed_stock_adjustment(c: httpx.Client) -> None:
    print("\n## StockAdjustmentRow.quantity")
    payload = {
        "location_id": LOCATION_A,
        "stock_adjustment_number": f"{SDT_PREFIX}-sa",
        "stock_adjustment_rows": [
            {"variant_id": VARIANT, "quantity": 3, "cost_per_unit": 4.5}
        ],
    }
    r = c.post("/stock_adjustments", json=payload)
    if not r.is_success:
        print(f"   skip — POST /stock_adjustments {r.status_code}: {r.text[:200]}")
        return
    sid = r.json()["id"]
    _record(f"/stock_adjustments/{sid}")
    got = c.get(f"/stock_adjustments/{sid}").json()
    rows = got.get("stock_adjustment_rows") or []
    if rows:
        _sample("StockAdjustmentRow.quantity", rows[0].get("quantity"))
        _sample("StockAdjustmentRow.cost_per_unit", rows[0].get("cost_per_unit"))


def seed_stock_transfer(c: httpx.Client) -> None:
    print("\n## StockTransferRow.quantity")
    payload = {
        "source_location_id": LOCATION_A,
        "target_location_id": LOCATION_B,
        "stock_transfer_number": f"{SDT_PREFIX}-st",
        "stock_transfer_rows": [{"variant_id": VARIANT, "quantity": 2}],
    }
    r = c.post("/stock_transfers", json=payload)
    if not r.is_success:
        print(f"   skip — POST /stock_transfers {r.status_code}: {r.text[:200]}")
        return
    tid = r.json()["id"]
    _record(f"/stock_transfers/{tid}")
    got = c.get(f"/stock_transfers/{tid}").json()
    rows = got.get("stock_transfer_rows") or []
    if rows:
        _sample("StockTransferRow.quantity", rows[0].get("quantity"))
        _sample("StockTransferRow.cost_per_unit", rows[0].get("cost_per_unit"))


def cleanup(c: httpx.Client) -> None:
    if not CLEANUP_FILE.exists():
        print("No cleanup file — nothing to delete.")
        return
    paths = [
        json.loads(line)["delete_path"]
        for line in CLEANUP_FILE.read_text().splitlines()
        if line.strip()
    ]
    ok = fail = 0
    for p in reversed(paths):  # children before parents
        r = c.delete(p)
        if r.status_code in (200, 204, 404):
            ok += 1
        else:
            fail += 1
            print(f"   DELETE {p} -> {r.status_code} {r.text[:120]}")
    print(f"\nCleanup: {ok} deleted/absent, {fail} failed.")
    if fail == 0:
        CLEANUP_FILE.unlink()


def main() -> int:
    headers = {"Authorization": f"Bearer {_key()}"}
    with httpx.Client(base_url=BASE_URL, headers=headers, timeout=60.0) as c:
        if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
            cleanup(c)
            return 0
        print("================ SEEDED MONEY-FIELD WIRE TYPES ================")
        for fn in (
            seed_customer,
            seed_material,
            seed_purchase_order,
            seed_price_list,
            seed_stock_adjustment,
            seed_stock_transfer,
        ):
            try:
                fn(c)
            except Exception as exc:  # keep going; cleanup still runs
                print(f"   ERROR in {fn.__name__}: {exc}")
        print("\n---------------- cleanup ----------------")
        cleanup(c)
    Path("/tmp/seed_money_results.json").write_text(
        json.dumps(RESULTS, indent=2, default=str)
    )
    print("\nWrote /tmp/seed_money_results.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
