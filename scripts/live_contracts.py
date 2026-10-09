"""Shared live scenarios and wire validation for both generated SDKs (#1157).

The CLI never contacts a tenant. TypeScript sends samples over stdin, so tenant
payloads are neither committed nor included in CI artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from functools import cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from scripts.validate_response_examples import _build_local_registry, load_yaml_spec

ROOT = Path(__file__).resolve().parents[1]


@cache
def spec() -> dict[str, Any]:
    return load_yaml_spec(ROOT / "docs/katana-openapi.yaml")


def catalog() -> list[dict[str, Any]]:
    """Derive reads from the source spec; new endpoint groups join automatically."""
    result = []
    for path, operations in spec()["paths"].items():
        for method, operation in operations.items():
            if method not in {"get", "post", "patch", "delete"}:
                continue
            name = operation["operationId"]
            snake = re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
            modules = list(
                (ROOT / "katana_public_api_client/api").glob(f"*/{snake}.py")
            )
            if len(modules) != 1:
                raise ValueError(f"Expected one Python SDK module for {name}")
            parameters = operations.get("parameters", []) + operation.get(
                "parameters", []
            )
            parameters = [
                spec()["components"]["parameters"][p["$ref"].split("/")[-1]]
                if "$ref" in p
                else p
                for p in parameters
            ]
            result.append(
                {
                    "path": path,
                    "method": method,
                    "sdk": name,
                    "python": ".".join(
                        modules[0].relative_to(ROOT).with_suffix("").parts
                    ),
                    "query": [p["name"] for p in parameters if p.get("in") == "query"],
                    "required_query": [
                        p["name"]
                        for p in parameters
                        if p.get("in") == "query" and p.get("required")
                    ],
                }
            )
    return result


@cache
def scenarios() -> list[dict[str, Any]]:
    return json.loads(
        (ROOT / "tests/integration/fixtures/core_round_trips.json").read_text()
    )


def validate_sample(path: str, method: str, status: int, body: Any) -> None:
    """Validate without printing payloads or JSON Schema's instance repr."""
    operation = spec()["paths"][path][method]
    response = operation["responses"].get(str(status))
    if response is None:
        raise AssertionError(f"{method.upper()} {path}: undocumented HTTP {status}")
    schema = response.get("content", {}).get("application/json", {}).get("schema")
    if schema is None:
        if body is not None:
            raise AssertionError(f"{method.upper()} {path}: expected an empty response")
        return
    validator = Draft202012Validator(
        {
            "$ref": f"urn:openapi-spec#/paths/{path.replace('~', '~0').replace('/', '~1')}/{method}/responses/{status}/content/application~1json/schema"
        },
        registry=_build_local_registry(spec()),
    )
    errors = list(validator.iter_errors(body))
    if errors:
        locations = ["/".join(map(str, e.absolute_path)) or "<root>" for e in errors]
        raise AssertionError(
            f"{method.upper()} {path}: schema violations at {locations}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["catalog", "validate"])
    args = parser.parse_args()
    if args.command == "catalog":
        print(json.dumps({"operations": catalog(), "scenarios": scenarios()}))
    else:
        for sample in json.load(sys.stdin):
            validate_sample(**sample)
