"""Spec-derived reads and shared core writes through generated Python endpoints."""

from __future__ import annotations

import importlib
import inspect
import json
from typing import Any, get_type_hints

import pytest
from scripts.live_contracts import catalog, detail_fixtures, scenarios, validate_sample

from katana_public_api_client import KatanaClient
from katana_public_api_client.testing_artifacts import LiveTestArtifacts

pytestmark = [pytest.mark.integration, pytest.mark.live, pytest.mark.asyncio]
OPERATIONS = catalog()


def operation(path: str, method: str) -> dict[str, Any]:
    return next(o for o in OPERATIONS if o["path"] == path and o["method"] == method)


async def call(
    client: KatanaClient,
    path: str,
    method: str = "get",
    *,
    entity_id: Any = None,
    body: dict[str, Any] | None = None,
    query: dict[str, Any] | None = None,
    artifacts: LiveTestArtifacts | None = None,
) -> Any:
    op = operation(path, method)
    endpoint = importlib.import_module(op["python"])
    function = endpoint.asyncio_detailed
    kwargs: dict[str, Any] = {"client": client}
    if entity_id is not None:
        kwargs["id"] = entity_id
    parameters = inspect.signature(function).parameters
    for key, value in (query or {}).items():
        if key in parameters:
            kwargs[key] = value
    for key in ("page", "limit"):
        if key in parameters:
            kwargs.setdefault(key, 1)
    if body is not None:
        kwargs["body"] = get_type_hints(function)["body"].from_dict(body)

    # Record a successful POST before the generated parser or validator can
    # fail: malformed successful responses must not orphan a created resource.
    async def record_created(response: Any) -> None:
        if artifacts is not None and method == "post" and response.is_success:
            await response.aread()
            created = response.json()
            rows = created if isinstance(created, list) else [created]
            artifacts.record_many(
                endpoint=path,
                entity_ids=[
                    row.get("id") if isinstance(row, dict) else None for row in rows
                ],
                issue="#1157",
            )

    hooks = client.get_async_httpx_client().event_hooks["response"]
    hooks.append(record_created)
    try:
        response = await function(**kwargs)
    finally:
        hooks.remove(record_created)
    assert 200 <= response.status_code < 300, (
        f"{method.upper()} {path}: HTTP {response.status_code}"
    )
    wire = json.loads(response.content) if response.content else None
    validate_sample(path, method, int(response.status_code), wire)
    if wire is not None:
        assert response.parsed is not None, (
            f"{op['sdk']}: generated parser returned None"
        )
    return wire


def entries(body: Any) -> list[dict[str, Any]]:
    return body if isinstance(body, list) else body.get("data", [])


OWNED_DETAILS = {
    read["path"] for case in detail_fixtures()["cases"] for read in case["reads"]
}
READS = [
    o for o in OPERATIONS if o["method"] == "get" and o["path"] not in OWNED_DETAILS
]


@pytest.mark.parametrize(
    "case", detail_fixtures()["cases"], ids=lambda case: case["name"]
)
async def test_owned_detail_reads(
    live_client: KatanaClient, live_artifacts: LiveTestArtifacts, case: dict[str, Any]
) -> None:
    resources = detail_fixtures()["resources"]
    values: dict[str, Any] = {}

    async def resolve(value: Any, tag: str) -> Any:
        if isinstance(value, dict):
            return {key: await resolve(item, tag) for key, item in value.items()}
        if isinstance(value, list):
            return [await resolve(item, tag) for item in value]
        if not isinstance(value, str) or not value.startswith("$"):
            return value
        if value == "$tag":
            return tag
        name, *keys = value[1:].split(".")
        if name not in values:
            definition = resources[name]
            own_tag = live_artifacts.tag(
                definition.get("tag", f"PY-{case['name']}-{name}")
            )
            for dependency in definition.get("after", []):
                await resolve(f"${dependency}", own_tag)
            body = await resolve(definition.get("body"), own_tag)
            result = await call(
                live_client,
                definition["path"],
                definition.get("method", "post"),
                body=body,
                artifacts=live_artifacts,
            )
            for check in definition.get("verify", []):
                checked_id = result
                for key in check["id"].split("."):
                    checked_id = (
                        checked_id[int(key)]
                        if isinstance(checked_id, list)
                        else checked_id[key]
                    )
                await call(live_client, check["path"], entity_id=checked_id)
            for key in (
                definition.get("select", "").split(".")
                if definition.get("select")
                else []
            ):
                result = result[int(key)] if isinstance(result, list) else result[key]
            values[name] = result
        result = values[name]
        for key in keys:
            result = result[int(key)] if isinstance(result, list) else result[key]
        return result

    for read in case["reads"]:
        entity_id = await resolve(read["id"], "")
        await call(live_client, read["path"], entity_id=entity_id)


@pytest.mark.parametrize(
    "op",
    [
        pytest.param(
            o,
            id=o["path"],
            marks=pytest.mark.live_smoke
            if o["path"] in {"/locations", "/products", "/suppliers"}
            else (),
        )
        for o in READS
    ],
)
async def test_sdk_read_group(live_client: KatanaClient, op: dict[str, Any]) -> None:
    path = op["path"]
    entity_id = None
    query = {}
    if "{id}" in path:
        parent = path.split("/{id}")[0]
        rows = entries(await call(live_client, parent))
        if not rows:
            pytest.skip(f"No test-tenant fixture for {path}")
        entity_id = rows[0]["id"]
    if op["required_query"]:
        for key, collection in {
            "variant_id": "/variants",
            "location_id": "/locations",
        }.items():
            if key in op["required_query"]:
                rows = entries(await call(live_client, collection))
                assert rows, f"Test tenant needs {collection} for {path}"
                query[key] = rows[0]["id"]
    await call(live_client, path, entity_id=entity_id, query=query)


def substitute(value: Any, context: dict[str, Any]) -> Any:
    if isinstance(value, str):
        return context.get(value, value)
    if isinstance(value, dict):
        return {key: substitute(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [substitute(item, context) for item in value]
    return value


@pytest.mark.parametrize(
    "scenario",
    [
        pytest.param(
            s,
            id=s["entity"],
            marks=pytest.mark.live_smoke
            if s["entity"] in {"customers", "suppliers"}
            else (),
        )
        for s in scenarios()
    ],
)
async def test_core_sdk_round_trip(
    live_client: KatanaClient,
    live_artifacts: LiveTestArtifacts,
    scenario: dict[str, Any],
) -> None:
    entity = scenario["entity"]
    context: dict[str, Any] = {
        "$tag": live_artifacts.tag(f"PY-{entity}"),
        "$updated": live_artifacts.tag(f"PY-{entity}-UPDATED"),
    }
    template = json.dumps(scenario["create"])
    for key, dependency in {
        "$product": "products",
        "$material": "materials",
        "$customer": "customers",
        "$supplier": "suppliers",
    }.items():
        if key in template:
            definition = next(s for s in scenarios() if s["entity"] == dependency)
            child_context = {"$tag": live_artifacts.tag(f"PY-{entity}-{dependency}")}
            created = await call(
                live_client,
                f"/{dependency}",
                "post",
                body=substitute(definition["create"], child_context),
                artifacts=live_artifacts,
            )
            context[key] = (
                created["variants"][0]["id"]
                if dependency in {"products", "materials"}
                else created["id"]
            )
    if "$location" in template:
        locations = entries(await call(live_client, "/locations"))
        assert locations, "Test tenant needs a location"
        context["$location"] = locations[0]["id"]
    path = f"/{entity}"
    created = await call(
        live_client,
        path,
        "post",
        body=substitute(scenario["create"], context),
        artifacts=live_artifacts,
    )
    entity_id = created["id"]
    detail = f"{path}/{{id}}"
    if any(o["path"] == detail and o["method"] == "get" for o in OPERATIONS):
        read = await call(live_client, detail, entity_id=entity_id)
    else:
        rows = entries(
            await call(live_client, path, query={"ids": [entity_id], "limit": 100})
        )
        read = next(row for row in rows if row["id"] == entity_id)
    assert read[scenario["field"]] == context["$tag"]
    updated = await call(
        live_client,
        detail,
        "patch",
        entity_id=entity_id,
        body=substitute(scenario["update"], context),
    )
    assert updated[scenario["field"]] == context["$updated"]
    await call(live_client, detail, "delete", entity_id=entity_id)
    # Fixture cleanup treats this explicit DELETE's subsequent 404 as success.
