"""Read-only list/detail custom-field contract probe for #782.

Run ``uv run python scripts/probe_custom_field_reads.py`` with test credentials.
At most eight GET requests: one first-page list and one detail per populated
entity. Reports shapes and schema errors only; no record IDs or values. Empty
lists leave detail behavior unverified. Does not assume list/detail parity.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import yaml
from jsonschema import Draft202012Validator

from katana_public_api_client.testing import make_test_client

SPEC_PATH = Path(__file__).resolve().parents[1] / "docs" / "katana-openapi.yaml"
ENTITIES = (
    ("products", "Product", "Product"),
    ("materials", "Material", "Material"),
    ("services", "Service", "Service"),
    ("variants", "Variant", "VariantResponse"),
)


def schema_parts(schema: dict[str, Any], schemas: dict[str, Any]) -> Iterator[dict]:
    """Follow local inheritance to inspect effective field requiredness."""
    if "$ref" in schema:
        yield from schema_parts(schemas[schema["$ref"].rsplit("/", 1)[-1]], schemas)
    yield schema
    for child in schema.get("allOf", []):
        yield from schema_parts(child, schemas)


def field_contract(*, schemas: dict[str, Any], name: str) -> dict[str, Any]:
    parts = list(schema_parts(schemas[name], schemas))
    fields = [
        part["properties"]["custom_fields"]
        for part in parts
        if "custom_fields" in part.get("properties", {})
    ]
    return {
        "declared": bool(fields),
        "required": any("custom_fields" in part.get("required", []) for part in parts),
        "schema": {"allOf": fields} if fields else {},
    }


def field_shape(record: dict[str, Any]) -> str:
    if "custom_fields" not in record:
        return "absent"
    value = record["custom_fields"]
    if value is None:
        return "null"
    if isinstance(value, list):
        return "empty_array" if not value else "array"
    if isinstance(value, dict):
        return "empty_object" if not value else "object"
    return type(value).__name__


def summarize(*, records: list[dict[str, Any]], contract: dict[str, Any]) -> dict:
    """Validate the field projection, leaving unrelated response fields alone."""
    errors: Counter[str] = Counter()
    validator = Draft202012Validator(contract["schema"])
    for record in records:
        if "custom_fields" not in record:
            if contract["required"]:
                errors["custom_fields: required"] += 1
            continue
        for error in validator.iter_errors(record["custom_fields"]):
            # Error.message can quote tenant values. Emit only the keyword and
            # property/index path, which is enough to locate contract drift.
            path = "/".join(str(part) for part in error.absolute_path)
            errors[f"custom_fields/{path}: {error.validator}"] += 1
    return {
        "records": len(records),
        "shapes": dict(Counter(field_shape(record) for record in records)),
        "violations": dict(errors),
    }


async def probe(*, http: httpx.AsyncClient, schemas: dict, limit: int = 50) -> dict:
    report = {}
    for endpoint, list_schema, detail_schema in ENTITIES:
        contract = field_contract(schemas=schemas, name=list_schema)
        response = await http.get(
            f"/{endpoint}",
            params={"limit": limit, "page": 1},
            extensions={"auto_pagination": False},
        )
        entry: dict[str, Any] = {
            "declared": contract["declared"],
            "required": contract["required"],
            "list_status": response.status_code,
        }
        report[endpoint] = entry
        if response.status_code != 200:
            entry["detail"] = "not probed: list request failed"
            continue
        records = response.json()["data"]
        entry["list"] = summarize(records=records, contract=contract)
        if not records:
            entry["detail"] = "not probed: empty first page"
            continue
        detail = await http.get(
            f"/{endpoint}/{records[0]['id']}", extensions={"auto_pagination": False}
        )
        entry["detail_status"] = detail.status_code
        if detail.status_code == 200:
            entry["detail"] = summarize(
                records=[detail.json()],
                contract=field_contract(schemas=schemas, name=detail_schema),
            )
    return report


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, choices=range(1, 51), default=50)
    args = parser.parse_args()
    schemas = yaml.safe_load(SPEC_PATH.read_text())["components"]["schemas"]
    async with make_test_client() as client:
        report = await probe(
            http=client.get_async_httpx_client(), schemas=schemas, limit=args.limit
        )
    print(json.dumps(report, indent=2))
    failed = any(
        entry["list_status"] != 200
        or entry.get("detail_status", 200) != 200
        or any(
            isinstance(entry.get(stage), dict) and entry[stage]["violations"]
            for stage in ("list", "detail")
        )
        for entry in report.values()
    )
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
