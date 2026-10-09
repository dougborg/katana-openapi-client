"""Keep endpoint-scoped portal specs usable for whole-API drift audits."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from scripts import pull_upstream_specs
from scripts.pull_upstream_specs import collect_reference_specs


def test_collect_reference_specs_merges_operations_and_components(tmp_path):
    reference = tmp_path / "reference"
    reference.mkdir()
    for name, method in [("create", "post"), ("list", "get")]:
        spec = {
            "openapi": "3.0.0",
            "info": {"title": "Katana", "version": "1"},
            "paths": {"/custom_field_definitions": {method: {"operationId": name}}},
            "components": {"schemas": {name: {"type": "object"}}},
        }
        (reference / f"{name}.md").write_text(
            f"# {name}\n\n```json\n{json.dumps(spec)}\n```\n"
        )
    (reference / "guide.md").write_text('```json\n{"example": true}\n```\n')
    combined = collect_reference_specs(tmp_path)
    assert combined is not None
    assert set(combined["paths"]["/custom_field_definitions"]) == {"post", "get"}
    assert set(combined["components"]["schemas"]) == {"create", "list"}


def test_collect_reference_specs_without_openapi_returns_none(tmp_path):
    assert collect_reference_specs(tmp_path) is None


@pytest.mark.asyncio
@pytest.mark.parametrize("results", [[True, False], [True, True]])
async def test_reference_index_and_stale_pages_only_change_after_complete_crawl(
    tmp_path, monkeypatch, results
):
    monkeypatch.setattr(pull_upstream_specs, "REPO_ROOT", tmp_path)
    output = tmp_path / "reference"
    output.mkdir()
    (output / "llms.txt").write_text("old index")
    stale = output / "removed.md"
    stale.write_text("previously published page")
    index = (
        "## API Reference\n"
        "- [Create](https://developer.katanamrp.com/reference/create.md)\n"
        "- [List](https://developer.katanamrp.com/reference/list.md)\n"
    )
    monkeypatch.setattr(
        pull_upstream_specs, "_fetch_text", AsyncMock(return_value=index)
    )
    monkeypatch.setattr(
        pull_upstream_specs, "_fetch_markdown_page", AsyncMock(side_effect=results)
    )
    complete = await pull_upstream_specs.fetch_readme_reference_markdown(
        MagicMock(), output
    )
    assert complete == all(results)
    assert (output / "llms.txt").read_text() == (index if complete else "old index")
    assert stale.exists() != complete


@pytest.mark.asyncio
async def test_partial_crawl_cannot_replace_complete_portal_with_ssr_endpoint(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(pull_upstream_specs, "REPO_ROOT", tmp_path)
    output = tmp_path / "specs"
    output.mkdir()
    previous = output / "readme-portal.yaml"
    previous.write_text("previous complete portal snapshot")
    monkeypatch.setattr(
        pull_upstream_specs.aiohttp,
        "ClientSession",
        MagicMock(return_value=MagicMock()),
    )
    monkeypatch.setattr(
        pull_upstream_specs,
        "fetch_live_openapi_spec",
        AsyncMock(return_value={"openapi": "3.0.0", "paths": {}}),
    )
    monkeypatch.setattr(
        pull_upstream_specs,
        "fetch_readme_oas",
        AsyncMock(return_value={"openapi": "3.0.0", "paths": {"/one": {}}}),
    )
    monkeypatch.setattr(
        pull_upstream_specs,
        "fetch_readme_reference_markdown",
        AsyncMock(return_value=False),
    )
    assert await pull_upstream_specs.refresh(output) == 1
    assert previous.read_text() == "previous complete portal snapshot"
