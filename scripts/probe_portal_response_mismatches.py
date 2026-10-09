"""Verify portal response-example mismatches against the live test tenant.

Reports only shapes, JSON types, field presence, and schema keywords. Raw tenant
responses stay in memory. Mutations require --mutate, use SDT-owned parents and
the test-only persistent cleanup ledger, and never alter pre-existing resources.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from jsonschema import Draft202012Validator

from katana_public_api_client.testing import make_test_client
from katana_public_api_client.testing_artifacts import live_test_artifacts
from scripts.validate_response_examples import (
    _build_local_registry,
    _find_local_response_schema,
    _unwrap_labeled_example,
    load_yaml_spec,
)

ROOT = Path(__file__).resolve().parents[1]
ABSENT = object()


def typename(value: Any) -> str:
    if value is ABSENT:
        return "absent"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, str):
        return "string"
    if isinstance(value, (int, float)):
        return "number"
    return "array" if isinstance(value, list) else "object"


def values_at(body: Any, path: list[Any]) -> list[Any]:
    """Sample every array element at an example's indexed JSON path."""
    if not path:
        return [body]
    head, *tail = path
    if isinstance(head, int):
        if not isinstance(body, list):
            return [ABSENT]
        return [v for item in body for v in values_at(item, tail)]
    if not isinstance(body, dict) or head not in body:
        return [ABSENT]
    return values_at(body[head], tail)


def records(body: Any) -> list[dict[str, Any]]:
    data = body.get("data", body) if isinstance(body, dict) else body
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return [data] if isinstance(data, dict) else []


class Audit:
    def __init__(self) -> None:
        self.spec = load_yaml_spec(ROOT / "docs/katana-openapi.yaml")
        self.portal = load_yaml_spec(ROOT / "docs/upstream-specs/readme-portal.yaml")
        self.registry = _build_local_registry(self.spec)
        self.findings: list[dict[str, Any]] = []
        self.errors: list[Any] = []
        self.samples: dict[tuple[str, str], list[Any]] = defaultdict(list)
        self.requests: list[dict[str, Any]] = []
        self.lists: dict[str, list[dict[str, Any]]] = {}
        self.factory: dict[str, Any] = {}
        self.cleanup: str | None = None
        self.live_schema_errors: list[dict[str, Any]] = []
        for path, methods in self.portal["paths"].items():
            for method, operation in methods.items():
                if method not in {"get", "post", "patch", "delete"}:
                    continue
                for status, response in operation.get("responses", {}).items():
                    ref, _ = _find_local_response_schema(
                        self.spec, path, method, str(status)
                    )
                    if not ref:
                        continue
                    validator = Draft202012Validator(
                        {"$ref": ref}, registry=self.registry
                    )
                    for media in response.get("content", {}).values():
                        if "example" not in media:
                            continue
                        body = _unwrap_labeled_example(media["example"])
                        for error in validator.iter_errors(body):
                            field_path = list(error.absolute_path)
                            field = None
                            if error.validator == "required":
                                match = re.match(
                                    r"'([^']+)' is a required property", error.message
                                )
                                if match is None:
                                    raise ValueError(
                                        "Unrecognized required-property error"
                                    )
                                field = match.group(1)
                            elif error.validator == "additionalProperties":
                                field = (
                                    "traceability"
                                    if "traceability" in error.message
                                    else None
                                )
                            if field:
                                field_path.append(field)
                            self.findings.append(
                                {
                                    "finding": len(self.findings) + 1,
                                    "method": method.upper(),
                                    "endpoint": path,
                                    "status": int(status),
                                    "field_path": field_path,
                                    "schema_keyword": error.validator,
                                    "portal_type": typename(
                                        error.instance
                                        if not field
                                        else error.instance.get(field, ABSENT)
                                    ),
                                }
                            )
                            self.errors.append(error)

    async def request(
        self,
        http: httpx.AsyncClient,
        method: str,
        path: str,
        *,
        template: str | None = None,
        **kwargs: Any,
    ) -> Any | None:
        response = await http.request(
            method, path, extensions={"auto_pagination": False}, **kwargs
        )
        endpoint = template or path
        self.requests.append(
            {
                "method": method.upper(),
                "endpoint": endpoint,
                "status": response.status_code,
            }
        )
        print(f"{method.upper()} {endpoint}: {response.status_code}", flush=True)
        if not response.is_success or not response.content:
            if response.content:
                payload = response.json()
                details = payload.get("error", {}).get("details", [])
                self.requests[-1]["error_details"] = [
                    {k: d[k] for k in ("path", "code") if k in d} for d in details
                ]
            return None
        body = response.json()
        self.samples[(method.upper(), endpoint)].append(body)
        ref, _ = _find_local_response_schema(
            self.spec, endpoint, method.lower(), str(response.status_code)
        )
        if ref:
            validator = Draft202012Validator({"$ref": ref}, registry=self.registry)

            def record_error(error: Any) -> None:
                if error.context:
                    children = error.context
                    if error.validator == "oneOf" and isinstance(error.instance, dict):
                        kind = error.instance.get("entity_type")
                        if kind in ("regular", "outsourced"):
                            index = 0 if kind == "regular" else 1
                            children = [
                                e
                                for e in children
                                if next(iter(e.schema_path)) == index
                            ]
                    for child in children:
                        record_error(child)
                    return
                item = {
                    "method": method.upper(),
                    "endpoint": endpoint,
                    "field_path": [
                        "*" if isinstance(p, int) else p for p in error.absolute_path
                    ],
                    "schema_path": list(error.absolute_schema_path),
                    "keyword": error.validator,
                    "actual_type": typename(error.instance),
                }
                if error.validator == "enum" and isinstance(error.instance, str):
                    item["enum_value"] = error.instance
                self.live_schema_errors.append(item)

            for error in validator.iter_errors(body):
                record_error(error)
        return body

    async def readonly(self, http: httpx.AsyncClient) -> None:
        self.factory = await self.request(http, "get", "/factory") or {}
        if not isinstance(self.factory.get("factory_id"), int):
            raise RuntimeError("Could not verify test tenant factory_id")
        paths = sorted(
            {
                f["endpoint"].split("/{id}")[0]
                for f in self.findings
                if f["method"] == "GET"
            }
        )
        for path in paths:
            body = await self.request(
                http, "get", path, params={"limit": 50, "page": 1}
            )
            self.lists[path] = records(body) if body is not None else []
        details = sorted(
            {
                f["endpoint"]
                for f in self.findings
                if f["method"] == "GET" and "{id}" in f["endpoint"]
            }
        )
        for template in details:
            for row in self.lists.get(template.split("/{id}")[0], [])[:3]:
                if "id" in row:
                    await self.request(
                        http,
                        "get",
                        template.replace("{id}", str(row["id"])),
                        template=template,
                    )
        for path in ["/sales_orders/search", "/sales_order_rows/search"]:
            await self.request(http, "post", path, json={"limit": 50, "page": 1})

    async def mutate(self, client: Any) -> None:
        """Exercise responses on owned parents; ledger cleanup runs on every exit."""
        http = client.get_async_httpx_client()
        async with live_test_artifacts(client=client) as artifacts:
            self.cleanup = str(artifacts.path)

            async def create(
                path: str, payload: dict[str, Any], *, parent: bool = True
            ) -> Any:
                body = await self.request(http, "post", path, json=payload)
                if body is not None and parent:
                    artifacts.record(
                        endpoint=path,
                        entity_id=body["id"],
                        issue="portal-response-audit",
                    )
                return body

            async def detail(path: str, body: Any) -> None:
                if body is not None:
                    await self.request(
                        http, "get", f"{path}/{body['id']}", template=f"{path}/{{id}}"
                    )

            async def patch(path: str, body: Any, payload: dict[str, Any]) -> None:
                if body is not None:
                    await self.request(
                        http,
                        "patch",
                        f"{path}/{body['id']}",
                        template=f"{path}/{{id}}",
                        json=payload,
                    )

            locations = records(
                await self.request(http, "get", "/locations", params={"limit": 50})
            )
            location = locations[0]["id"]
            product = await create(
                "/products",
                {
                    "name": artifacts.tag("PORTAL-PRODUCT"),
                    "uom": "pcs",
                    "is_producible": True,
                    "is_purchasable": True,
                    "is_sellable": True,
                    "variants": [
                        {"sku": artifacts.tag("PORTAL-SKU-A")},
                        {"sku": artifacts.tag("PORTAL-SKU-B")},
                    ],
                },
            )
            if product is None:
                return
            variant, ingredient = [v["id"] for v in product["variants"]]
            supplier = await create(
                "/suppliers", {"name": artifacts.tag("PORTAL-SUPPLIER")}
            )
            customer = await create(
                "/customers", {"name": artifacts.tag("PORTAL-CUSTOMER")}
            )
            for path in ("/inventory_reorder_points", "/inventory_safety_stock_levels"):
                # Thresholds belong to the owned variant and disappear with its product.
                await create(
                    path,
                    {"variant_id": variant, "location_id": location, "value": 3.14},
                    parent=False,
                )
            adjustment = await create(
                "/stock_adjustments",
                {
                    "stock_adjustment_number": artifacts.tag("PORTAL-SA"),
                    "location_id": location,
                    "reason": artifacts.tag("PORTAL-AUDIT"),
                    "stock_adjustment_rows": [
                        {
                            "variant_id": ingredient,
                            "quantity": 5,
                            "cost_per_unit": 3.14,
                            "traceability": [
                                {
                                    "batch_id": None,
                                    "serial_number_id": None,
                                    "bin_location_id": None,
                                    "quantity": 5,
                                }
                            ],
                        }
                    ],
                },
            )
            await patch(
                "/stock_adjustments",
                adjustment,
                {"reason": artifacts.tag("PORTAL-AUDIT-PATCH")},
            )
            mo = await create(
                "/manufacturing_orders",
                {
                    "order_no": artifacts.tag("PORTAL-MO"),
                    "variant_id": variant,
                    "location_id": location,
                    "planned_quantity": 2,
                },
            )
            if mo:
                operation = await create(
                    "/manufacturing_order_operation_rows",
                    {
                        "manufacturing_order_id": mo["id"],
                        "status": "NOT_STARTED",
                        "operation_name": artifacts.tag("PORTAL-OP"),
                        "resource_name": artifacts.tag("PORTAL-RESOURCE"),
                        "type": "process",
                        "planned_time_parameter": 1.25,
                        "cost_parameter": 3.14,
                    },
                    parent=False,
                )
                await detail("/manufacturing_order_operation_rows", operation)
                await patch(
                    "/manufacturing_order_operation_rows",
                    operation,
                    {
                        "planned_time_parameter": 2.5,
                        "cost_parameter": 6.28,
                    },
                )
                recipe = await create(
                    "/manufacturing_order_recipe_rows",
                    {
                        "manufacturing_order_id": mo["id"],
                        "variant_id": ingredient,
                        "planned_quantity_per_unit": 1.25,
                        "total_actual_quantity": 1,
                    },
                    parent=False,
                )
                await detail("/manufacturing_order_recipe_rows", recipe)
                await patch(
                    "/manufacturing_order_recipe_rows",
                    recipe,
                    {"planned_quantity_per_unit": 2.5},
                )
                await patch(
                    "/manufacturing_order_operation_rows",
                    operation,
                    {"status": "COMPLETED"},
                )
            if supplier:
                for entity_type in ("regular", "outsourced"):
                    po = await create(
                        "/purchase_orders",
                        {
                            "order_no": artifacts.tag(f"PORTAL-PO-{entity_type}"),
                            "supplier_id": supplier["id"],
                            "location_id": location,
                            **(
                                {"tracking_location_id": location}
                                if entity_type == "outsourced"
                                else {}
                            ),
                            "entity_type": entity_type,
                            "status": "NOT_RECEIVED",
                            "purchase_order_rows": [
                                {
                                    "variant_id": variant,
                                    "quantity": 2,
                                    "price_per_unit": 3.14,
                                }
                            ],
                        },
                    )
                    await detail("/purchase_orders", po)
                    if po and entity_type == "outsourced":
                        row = await create(
                            "/outsourced_purchase_order_recipe_rows",
                            {
                                "purchase_order_row_id": po["purchase_order_rows"][0][
                                    "id"
                                ],
                                "ingredient_variant_id": ingredient,
                                "planned_quantity_per_unit": 1.25,
                            },
                            parent=False,
                        )
                        await detail("/outsourced_purchase_order_recipe_rows", row)
            if customer:
                so = await create(
                    "/sales_orders",
                    {
                        "order_no": artifacts.tag("PORTAL-SO"),
                        "customer_id": customer["id"],
                        "location_id": location,
                        "sales_order_rows": [
                            {
                                "variant_id": variant,
                                "quantity": 1,
                                "price_per_unit": 3.14,
                            }
                        ],
                    },
                )
                if so:
                    await detail("/sales_orders", so)
                    row = await create(
                        "/sales_order_rows",
                        {
                            "sales_order_id": so["id"],
                            "variant_id": ingredient,
                            "quantity": 1.25,
                            "price_per_unit": 3.14,
                            "location_id": location,
                        },
                        parent=False,
                    )
                    await detail("/sales_order_rows", row)
                    await patch("/sales_order_rows", row, {"price_per_unit": 6.28})
                    fee = await create(
                        "/sales_order_shipping_fee",
                        {
                            "sales_order_id": so["id"],
                            "amount": "3.14",
                            "description": artifacts.tag("PORTAL-FEE"),
                        },
                        parent=False,
                    )
                    await detail("/sales_order_shipping_fee", fee)
                    await patch("/sales_order_shipping_fee", fee, {"amount": "6.28"})
                    if adjustment:
                        fulfillment = await create(
                            "/sales_order_fulfillments",
                            {
                                "sales_order_id": so["id"],
                                "status": "PACKED",
                                "sales_order_fulfillment_rows": [
                                    {
                                        "sales_order_row_id": so["sales_order_rows"][0][
                                            "id"
                                        ],
                                        "quantity": 1,
                                        "traceability": [
                                            {
                                                "batch_id": None,
                                                "serial_number_id": None,
                                                "bin_location_id": None,
                                                "quantity": 1,
                                            }
                                        ],
                                    }
                                ],
                            },
                        )
                        await detail("/sales_order_fulfillments", fulfillment)
            await self.rare_cases(
                http,
                artifacts,
                create,
                detail,
                patch,
                customer,
                supplier,
                location,
                locations,
                variant,
            )
            # Refresh affected list responses while owned fixtures still exist.
            for path in self.lists:
                await self.request(http, "get", path, params={"limit": 50, "page": 1})
            for path in ("/sales_orders/search", "/sales_order_rows/search"):
                await self.request(http, "post", path, json={"limit": 50, "page": 1})

    async def rare_cases(
        self,
        http: Any,
        artifacts: Any,
        create: Any,
        detail: Any,
        patch: Any,
        customer: Any,
        supplier: Any,
        location: int,
        locations: Any,
        variant: int,
    ) -> None:
        # Own a batch-tracked product, but create no batch identities. Null
        # allocations track unallocated quantities on disposable order rows.
        product = await create(
            "/products",
            {
                "name": artifacts.tag("PORTAL-BATCH"),
                "uom": "pcs",
                "batch_tracked": True,
                "is_purchasable": True,
                "is_sellable": True,
                "variants": [{"sku": artifacts.tag("PORTAL-BATCH-SKU")}],
            },
        )
        if product:
            batch_variant = product["variants"][0]["id"]
            if supplier:
                po = await create(
                    "/purchase_orders",
                    {
                        "order_no": artifacts.tag("PORTAL-BATCH-OPO"),
                        "supplier_id": supplier["id"],
                        "location_id": location,
                        "tracking_location_id": location,
                        "entity_type": "outsourced",
                        "purchase_order_rows": [
                            {"variant_id": variant, "quantity": 1, "price_per_unit": 1}
                        ],
                    },
                )
                if po:
                    recipe = await create(
                        "/outsourced_purchase_order_recipe_rows",
                        {
                            "purchase_order_row_id": po["purchase_order_rows"][0]["id"],
                            "ingredient_variant_id": batch_variant,
                            "planned_quantity_per_unit": 1,
                            "batch_transactions": [{"batch_id": None, "quantity": 1}],
                        },
                        parent=False,
                    )
                    await detail("/outsourced_purchase_order_recipe_rows", recipe)
            if customer:
                so = await create(
                    "/sales_orders",
                    {
                        "order_no": artifacts.tag("PORTAL-BATCH-SO"),
                        "customer_id": customer["id"],
                        "location_id": location,
                        "sales_order_rows": [
                            {
                                "variant_id": batch_variant,
                                "quantity": 1,
                                "price_per_unit": 1,
                            }
                        ],
                    },
                )
                if so:
                    row = so["sales_order_rows"][0]
                    await patch(
                        "/sales_order_rows",
                        row,
                        {"batch_transactions": [{"batch_id": None, "quantity": 1}]},
                    )
                    await detail("/sales_order_rows", row)
                    await detail("/sales_orders", so)
                    fulfillment = await create(
                        "/sales_order_fulfillments",
                        {
                            "sales_order_id": so["id"],
                            "status": "PACKED",
                            "sales_order_fulfillment_rows": [
                                {
                                    "sales_order_row_id": row["id"],
                                    "quantity": 1,
                                    "traceability": [{"batch_id": None, "quantity": 1}],
                                }
                            ],
                        },
                    )
                    await detail("/sales_order_fulfillments", fulfillment)
            if len(locations) > 1:
                transfer = await create(
                    "/stock_transfers",
                    {
                        "stock_transfer_number": artifacts.tag("PORTAL-BATCH-ST"),
                        "source_location_id": location,
                        "target_location_id": locations[1]["id"],
                        "stock_transfer_rows": [
                            {
                                "variant_id": batch_variant,
                                "quantity": "1.0000000000",
                                "traceability": [{"batch_id": None, "quantity": 1}],
                            }
                        ],
                    },
                )
                if transfer:
                    await self.request(
                        http,
                        "patch",
                        f"/stock_transfers/{transfer['id']}/status",
                        template="/stock_transfers/{id}/status",
                        json={"status": "inTransit"},
                    )
                    await self.request(
                        http,
                        "get",
                        "/stock_transfers",
                        params={
                            "stock_transfer_number": transfer["stock_transfer_number"],
                            "limit": 50,
                        },
                    )

    def report(self) -> dict[str, Any]:
        output = []
        for finding, error in zip(self.findings, self.errors, strict=True):
            entry = dict(finding)
            bodies = self.samples[(entry["method"], entry["endpoint"])]
            observed = [
                v for body in bodies for v in values_at(body, entry["field_path"])
            ]
            entry["observed_types"] = dict(Counter(typename(v) for v in observed))
            present = [v for v in observed if v is not ABSENT]
            if not bodies or not observed:
                entry["verdict"] = "unverified_no_samples"
            elif error.validator == "required":
                entry["verdict"] = (
                    "local_schema_wrong"
                    if ABSENT in observed
                    else "portal_example_wrong"
                )
            elif error.validator == "additionalProperties":
                entry["verdict"] = (
                    "local_schema_wrong" if present else "unverified_field_not_observed"
                )
            elif error.validator in {"anyOf", "oneOf"}:
                # Check the disputed leaf, rather than blaming the example
                # for an unrelated violation in a different union branch.
                leaf = (
                    next(
                        (
                            e
                            for e in error.context
                            if list(e.absolute_path)[-1:] == ["landed_cost"]
                        ),
                        None,
                    )
                    if entry["endpoint"]
                    in {"/purchase_orders", "/purchase_orders/{id}"}
                    else None
                )
                if leaf is None:
                    entry["verdict"] = "unverified_unsupported_union"
                    entry["limitation"] = "Disputed union leaf requires manual review"
                    output.append(entry)
                    continue
                evidence_path = list(leaf.absolute_path)
                values = [
                    v
                    for body in bodies
                    for v in values_at(body, evidence_path)
                    if v is not ABSENT
                ]
                entry["evidence_field_path"] = evidence_path
                entry["observed_types"] = dict(Counter(typename(v) for v in values))
                validation = Draft202012Validator(leaf.schema)
                entry["verdict"] = (
                    "unverified_no_samples"
                    if not values
                    else "local_schema_wrong"
                    if any(not validation.is_valid(v) for v in values)
                    else "portal_example_wrong"
                )
            elif not present:
                entry["verdict"] = "unverified_no_nonnull_sample"
            else:
                validator = Draft202012Validator(
                    {**error.schema, "components": self.spec["components"]},
                    registry=self.registry,
                )
                invalid = [v for v in present if not validator.is_valid(v)]
                entry["verdict"] = (
                    "local_schema_wrong" if invalid else "portal_example_wrong"
                )
                if (
                    not invalid
                    and all(v is None for v in present)
                    and error.instance is not None
                ):
                    entry["verdict"] = "unverified_no_nonnull_sample"
                if (
                    invalid
                    and all(v is None for v in present)
                    and error.instance is not None
                ):
                    entry["limitation"] = (
                        "Observed invalid null; portal non-null type still unverified"
                    )
                if error.instance is None and not any(v is None for v in present):
                    entry["verdict"] = "unverified_null_case_not_observed"
                if error.validator == "enum" and error.instance not in present:
                    entry["verdict"] = "unverified_enum_case_not_observed"
            output.append(entry)
        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "factory_id": self.factory.get("factory_id"),
            "requests": self.requests,
            "findings": output,
            "summary": dict(Counter(f["verdict"] for f in output)),
            "cleanup_ledger": self.cleanup,
            "live_schema_errors": getattr(self, "live_schema_errors", []),
        }


async def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("/tmp/katana-response-audit.json")
    )
    parser.add_argument(
        "--mutate", action="store_true", help="Create and clean up tagged test records"
    )
    args = parser.parse_args()
    audit = Audit()
    try:
        async with make_test_client(max_retries=2, max_pages=2) as client:
            await audit.readonly(client.get_async_httpx_client())
            if args.mutate:
                await audit.mutate(client)
    finally:
        report = audit.report()
        if audit.cleanup:
            rows = [
                json.loads(line)
                for line in Path(audit.cleanup).read_text().splitlines()
            ]
            report["cleanup"] = {
                "created": len(rows),
                "deleted": sum(bool(row["deleted_at"]) for row in rows),
            }
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report["summary"], indent=2))


if __name__ == "__main__":
    asyncio.run(main())
