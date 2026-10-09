"""Spec-derived reads and shared core writes through generated Python endpoints."""

from __future__ import annotations

import importlib
import inspect
import json
from typing import Any, get_type_hints

import pytest
from scripts.live_contracts import catalog, scenarios, validate_sample

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
            artifacts.record(
                endpoint=path, entity_id=response.json()["id"], issue="#1157"
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


READS = [o for o in OPERATIONS if o["method"] == "get"]


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
