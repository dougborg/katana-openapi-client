"""Shape-only probes for #734 and #736 — bypass the existence check.

The live API runs Ajv schema validation **before** any application-level
existence / FK lookups, so we can map request-body shape contracts by
sending deliberately-bogus IDs: the 422 details reveal whether the
server expected a single object vs an array, or a dict vs an array for
``custom_fields``. None of these POSTs reach the persistence layer —
the ledger stays empty.
"""

from __future__ import annotations

import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.spec_drift_verify import make_client, pp_response

FAKE_BIN_ID = 99999999
FAKE_VARIANT_ID = 99999999
FAKE_CUSTOMER_ID = 99999999


def _discover_sales_location(client: httpx.Client) -> int:
    """Look up the tenant's default sales location via ``GET /factory``."""
    factory = client.get("/factory").json()
    return factory.get("default_sales_location_id") or 0


def _verify_fake_ids_absent(client: httpx.Client) -> None:
    """Confirm the high-positive fake IDs don't resolve on this tenant.

    These probes rely on the FK lookup failing so the Ajv validator
    surfaces the shape error rather than persisting anything. If a real
    variant / bin happens to have ID 99999999, the probe would silently
    succeed and mutate state without recording to the ledger. Cheap
    pre-flight GET on each — abort if any resolves.
    """
    for path in (
        f"/variants/{FAKE_VARIANT_ID}",
        f"/bin_locations/{FAKE_BIN_ID}",
        f"/customers/{FAKE_CUSTOMER_ID}",
    ):
        r = client.get(path)
        if r.status_code != 404:
            print(
                f"✗ pre-flight: GET {path} → {r.status_code} (expected 404). "
                "A real entity exists at this ID; aborting to avoid a "
                "ledger-less mutation.",
                file=sys.stderr,
            )
            sys.exit(1)


def _assert_not_persisted(label: str, response: httpx.Response) -> None:
    """Ensure a shape probe didn't accidentally persist anything.

    The probes are *meant* to fail with 422; a 2xx means an FK happened
    to resolve and we just mutated tenant state without a ledger entry.
    Bail loudly so the operator can investigate.
    """
    if 200 <= response.status_code < 300:
        print(
            f"✗ {label}: unexpected 2xx — the FK lookup resolved and "
            f"the API persisted. Body: {response.text[:300]}",
            file=sys.stderr,
        )
        sys.exit(1)


def probe_variant_bin_locations_shape(client: httpx.Client, sales_loc: int) -> None:
    print("\n=== #736: /variant_bin_locations request body shape ===")

    print("\n--- A. single object body ---")
    r = client.post(
        "/variant_bin_locations",
        json={
            "variant_id": FAKE_VARIANT_ID,
            "bin_location_id": FAKE_BIN_ID,
            "location_id": sales_loc,
        },
    )
    _assert_not_persisted("variant_bin_locations single-object", r)
    print(pp_response(r))

    print("\n--- B. array body ---")
    r = client.post(
        "/variant_bin_locations",
        json=[
            {
                "variant_id": FAKE_VARIANT_ID,
                "bin_location_id": FAKE_BIN_ID,
                "location_id": sales_loc,
            }
        ],
    )
    _assert_not_persisted("variant_bin_locations array", r)
    print(pp_response(r))

    print("\n--- C. dict with 'variant_bin_locations' wrapper ---")
    r = client.post(
        "/variant_bin_locations",
        json={
            "variant_bin_locations": [
                {
                    "variant_id": FAKE_VARIANT_ID,
                    "bin_location_id": FAKE_BIN_ID,
                    "location_id": sales_loc,
                }
            ]
        },
    )
    _assert_not_persisted("variant_bin_locations wrapped", r)
    print(pp_response(r))


def probe_so_row_custom_fields_shapes(client: httpx.Client, sales_loc: int) -> None:
    """Try various ``custom_fields`` shapes on SO row create to infer
    what the live API expects on the wire.

    Uses a known-bad customer_id so the request fails fast at FK check
    if it gets past Ajv validation — leaving the 422 to tell us about
    shape.
    """
    print("\n=== #734: /sales_orders custom_fields request shape ===")

    def _send(body, label):
        print(f"\n--- {label} ---")
        r = client.post("/sales_orders", json=body)
        _assert_not_persisted(f"sales_orders shape probe — {label}", r)
        print(pp_response(r))

    common = {
        "customer_id": FAKE_CUSTOMER_ID,
        "location_id": sales_loc,
        "sales_order_rows": [
            {"variant_id": FAKE_VARIANT_ID, "quantity": 1, "price_per_unit": 1.0}
        ],
    }

    # A. dict-shape (what we confirmed works at validation level)
    _send(
        {
            **common,
            "order_no": "SDT-shape-A",
            "sales_order_rows": [
                {**common["sales_order_rows"][0], "custom_fields": {"k": "v"}}
            ],
        },
        "A. row.custom_fields as dict",
    )

    # B. array-of-objects shape (matches local READ schema)
    _send(
        {
            **common,
            "order_no": "SDT-shape-B",
            "sales_order_rows": [
                {
                    **common["sales_order_rows"][0],
                    "custom_fields": [{"field_name": "k", "field_value": "v"}],
                }
            ],
        },
        "B. row.custom_fields as structured array",
    )

    # C. SO-level custom_fields (not on row)
    _send(
        {**common, "order_no": "SDT-shape-C", "custom_fields": {"k": "v"}},
        "C. SO-level custom_fields dict",
    )

    # D. SO-level array
    _send(
        {
            **common,
            "order_no": "SDT-shape-D",
            "custom_fields": [{"field_name": "k", "field_value": "v"}],
        },
        "D. SO-level custom_fields array",
    )


def main() -> int:
    with make_client() as client:
        sales_loc = _discover_sales_location(client)
        if not sales_loc:
            print("✗ factory.default_sales_location_id missing; aborting")
            return 1
        _verify_fake_ids_absent(client)
        probe_variant_bin_locations_shape(client, sales_loc)
        probe_so_row_custom_fields_shapes(client, sales_loc)
    return 0


if __name__ == "__main__":
    sys.exit(main())
