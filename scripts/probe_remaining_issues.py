"""Live-API probes for issues #734, #736, #738, #739.

Each probe is intentionally narrow — answer the smallest set of yes/no
questions the issue requires, record any persisted artifacts to the
spec-drift ledger, and bail early if a precondition is missing.

Order:

- #739 — POST /sales_order_fulfillments without ``sales_order_fulfillment_rows``
- #734 — POST /sales_order_rows with ``custom_fields`` dict, GET back to inspect read shape
- #736 — POST /variant_bin_locations single object vs array; POST /services with variant.sku omitted
- #738 — POST /stock_transfers + PATCH through status enum values

The probes share a single httpx client and reuse fixtures (location,
variant) discovered up-front from the live tenant to minimize blast
radius.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.spec_drift_verify import (
    discover_sdt_fixture,
    label,
    make_client,
    pp_response,
    record_artifact,
    tagged,
)


def _ensure_sdt_customer(client: httpx.Client) -> int:
    """Find or create an SDT-tagged customer for use as a probe target.

    The probe pattern previously was "grab the first customer the API
    returns" — exactly the WEB20604 incident's root cause (the first
    customer was a real Shopify record). Use ``discover_sdt_fixture``
    to filter for SDT-prefixed names; create a fresh SDT customer when
    none exist. The fresh customer hits the ledger and gets cleaned up
    on the next ``spec_drift_verify.py cleanup`` run.
    """
    found = discover_sdt_fixture(client, "/customers", "name")
    if found is not None:
        return int(found["id"])
    payload = {
        "name": label("probe-customer"),
        "company": label("probe-customer"),
    }
    resp = client.post("/customers", json=payload)
    if not resp.is_success:
        print(f"  ✗  could not create SDT customer: {pp_response(resp, 200)}")
        sys.exit(1)
    created = resp.json()
    record_artifact(
        endpoint="/customers",
        entity_id=created["id"],
        issue="probe-fixture",
        sku_or_name=payload["name"],
    )
    return int(created["id"])


def discover_fixtures(client: httpx.Client) -> dict[str, Any]:
    """Pre-fetch a location, customer, and sellable variant.

    Resolves the sales-enabled location via ``GET /factory`` (its
    ``default_sales_location_id`` is authoritative). Other locations
    on the tenant may have ``purchase_allowed: false`` and the live
    API rejects SO creates against them ("Location has selling
    disabled"). Bails (``sys.exit(1)``) when ``default_sales_location_id``
    is missing or no sellable variant is available; ``_ensure_sdt_customer``
    bails on its own if neither lookup nor creation succeeds.

    The customer is filtered for the SDT- prefix so probes never target
    a real customer record (root cause of the 2026-05-19 WEB20604
    near-miss — see issue #781). When no SDT-tagged customer exists, a
    fresh one is created and recorded to the ledger. Variants are still
    picked by "first sellable" because they're read-only fixtures (not
    the target of any mutation in this probe).
    """
    print("\n=== Discovering shared fixtures ===")
    factory = client.get("/factory").json()
    locations = client.get("/locations?limit=10").json().get("data", [])
    variants = client.get("/variants?limit=20").json().get("data", [])
    sellable = [v for v in variants if v.get("sales_price") is not None][:1]

    sales_location_id = factory.get("default_sales_location_id")
    # Pick any non-sales location for stock_transfer destination
    other = next(
        (loc["id"] for loc in locations if loc["id"] != sales_location_id),
        None,
    )

    if not sales_location_id:
        print("  ✗  factory.default_sales_location_id missing; aborting")
        sys.exit(1)
    if not sellable:
        print("  ✗  no sellable variant available; aborting")
        sys.exit(1)

    customer_id = _ensure_sdt_customer(client)

    fx = {
        "location_id": sales_location_id,
        "second_location_id": other,
        "customer_id": customer_id,
        "variant_id": sellable[0]["id"],
    }
    print(f"  fixtures: {fx}")
    return fx


# ----------------------------------------------------------------------
# #739 — sales_order_fulfillments without rows
# ----------------------------------------------------------------------


def probe_739_empty_fulfillment_rows(client: httpx.Client, fx: dict[str, Any]) -> None:
    """Send a fulfillment create without ``sales_order_fulfillment_rows``.

    Local spec marks the field required. README upstream OAS does not.
    """
    print("\n=== #739: POST /sales_order_fulfillments without rows ===")

    # SO with embedded row (sales_order_rows is required on create)
    so_resp = client.post(
        "/sales_orders",
        json={
            "order_no": tagged("SO-739"),
            "customer_id": fx["customer_id"],
            "location_id": fx["location_id"],
            "additional_info": label("for #739 verify"),
            "sales_order_rows": [
                {
                    "variant_id": fx["variant_id"],
                    "quantity": 1,
                    "price_per_unit": 1.0,
                }
            ],
        },
    )
    if not so_resp.is_success:
        print(f"  ✗  could not create SO: {pp_response(so_resp, 200)}")
        return
    so_id = so_resp.json()["id"]
    record_artifact(
        endpoint="/sales_orders",
        entity_id=so_id,
        issue="#739",
        order_no=tagged("SO-739"),
    )

    # Now try the fulfillment without the rows array
    fulfill = client.post(
        "/sales_order_fulfillments",
        json={
            "sales_order_id": so_id,
            "status": "PACKED",
        },
    )
    print(pp_response(fulfill, 400))
    if fulfill.is_success:
        record_artifact(
            endpoint="/sales_order_fulfillments",
            entity_id=fulfill.json()["id"],
            issue="#739",
            parent_so=so_id,
        )
        print("  ✓  Server ACCEPTED — rows field is optional on the wire")
    else:
        print(
            f"  ✗  Server REJECTED — rows field is required (status={fulfill.status_code})"
        )


# ----------------------------------------------------------------------
# #734 — custom_fields shape on SO row
# ----------------------------------------------------------------------


def probe_734_custom_fields(client: httpx.Client, fx: dict[str, Any]) -> None:
    print("\n=== #734: POST /sales_order_rows with custom_fields dict ===")

    # Create SO with embedded row that has custom_fields (dict shape)
    so = client.post(
        "/sales_orders",
        json={
            "order_no": tagged("SO-734"),
            "customer_id": fx["customer_id"],
            "location_id": fx["location_id"],
            "additional_info": label("for #734 verify"),
            "sales_order_rows": [
                {
                    "variant_id": fx["variant_id"],
                    "quantity": 1,
                    "price_per_unit": 1.0,
                    "custom_fields": {"sdt_test_key": "sdt_test_value"},
                }
            ],
        },
    )
    print("--- dict-shape custom_fields POST ---")
    print(pp_response(so, 600))
    if so.is_success:
        so_data = so.json()
        so_id = so_data["id"]
        record_artifact(
            endpoint="/sales_orders",
            entity_id=so_id,
            issue="#734",
            order_no=tagged("SO-734"),
        )
        # GET back the SO to inspect read shape
        got = client.get(f"/sales_orders/{so_id}")
        rows = got.json().get("sales_order_rows", [])
        if rows:
            cf = rows[0].get("custom_fields")
            print(f"\n  → custom_fields read shape: type={type(cf).__name__}")
            print(f"  → value: {cf!r}")


# ----------------------------------------------------------------------
# #736 — variant_bin_locations array shape
# ----------------------------------------------------------------------


def probe_736_bin_locations(client: httpx.Client, fx: dict[str, Any]) -> None:
    print("\n=== #736: POST /variant_bin_locations (single vs array) ===")
    print(
        "  → shape-only probe lives in scripts/probe_shape_only.py — "
        "uses bogus FKs so the Ajv validator fires before persistence.\n"
        "  → skipping here to avoid mutating a real variant's default-bin link."
    )


# ----------------------------------------------------------------------
# #736 — CreateServiceVariant.sku required
# ----------------------------------------------------------------------


def probe_736_service_sku(client: httpx.Client) -> None:
    print("\n=== #736: POST /services with variant.sku omitted ===")
    r = client.post(
        "/services",
        json={
            "name": label("verify-service-no-sku"),
            "variants": [
                {
                    "sales_price": 10.0,
                    # sku intentionally omitted
                }
            ],
        },
    )
    print(pp_response(r, 400))
    if r.is_success:
        sid = r.json()["id"]
        record_artifact(
            endpoint="/services",
            entity_id=sid,
            issue="#736",
            sku_or_name=label("verify-service-no-sku"),
        )
        print("  → server accepted variant.sku=null → spec should mark sku optional")
    else:
        print("  → server rejected → spec correctly requires sku")


# ----------------------------------------------------------------------
# #738 — stock transfer status round-trip
# ----------------------------------------------------------------------


def probe_738_stock_transfer_status(client: httpx.Client, fx: dict[str, Any]) -> None:
    print("\n=== #738: stock_transfer status round-trip ===")
    if not fx.get("second_location_id"):
        print("  ✗  need 2 locations; only 1 found — skipping")
        return

    # Try creating with status='draft' first
    for create_status in ("draft", "received", "inTransit", "created"):
        body = {
            "stock_transfer_number": tagged(f"ST-{create_status}"),
            "source_location_id": fx["location_id"],
            "target_location_id": fx["second_location_id"],
            "stock_transfer_date": "2026-05-15T00:00:00.000Z",
            "status": create_status,
            "stock_transfer_rows": [
                {"variant_id": fx["variant_id"], "quantity": "1.0"}
            ],
        }
        r = client.post("/stock_transfers", json=body)
        if r.is_success:
            data = r.json()
            record_artifact(
                endpoint="/stock_transfers",
                entity_id=data["id"],
                issue="#738",
                sku_or_name=tagged(f"ST-{create_status}"),
                requested_status=create_status,
                resolved_status=data.get("status"),
            )
            print(
                f"  ✓  create with status={create_status!r} accepted → "
                f"server resolved to {data.get('status')!r}"
            )
        else:
            print(f"  ✗  create with status={create_status!r} rejected:")
            print(f"     {pp_response(r, 400)}")


def main() -> int:
    with make_client() as client:
        fx = discover_fixtures(client)
        probe_739_empty_fulfillment_rows(client, fx)
        probe_734_custom_fields(client, fx)
        probe_736_bin_locations(client, fx)
        probe_736_service_sku(client)
        probe_738_stock_transfer_status(client, fx)
    print(
        "\nDone. Run `uv run python scripts/spec_drift_verify.py list` to inspect "
        "ledger, then `... cleanup` to delete artifacts."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
