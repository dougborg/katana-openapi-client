"""The shared harness must exercise generated endpoints and detect wire drift."""

import importlib
import importlib.util
from pathlib import Path

import httpx
import pytest
from scripts.live_contracts import catalog, scenarios, spec, validate_sample

from katana_public_api_client import KatanaClient
from katana_public_api_client.testing_artifacts import live_test_artifacts


def test_every_get_operation_has_a_generated_python_entrypoint():
    reads = [o for o in catalog() if o["method"] == "get"]
    assert {o["path"] for o in reads} == {
        p for p, operations in spec()["paths"].items() if "get" in operations
    }
    for op in reads:
        assert callable(importlib.import_module(op["python"]).asyncio_detailed)


def test_both_clients_share_all_eight_core_write_scenarios():
    assert {s["entity"] for s in scenarios()} == {
        "products",
        "materials",
        "purchase_orders",
        "sales_orders",
        "manufacturing_orders",
        "customers",
        "suppliers",
        "stock_adjustments",
    }
    operations = {(o["path"], o["method"]) for o in catalog()}
    for scenario in scenarios():
        path = f"/{scenario['entity']}"
        assert (path, "post") in operations
        assert (f"{path}/{{id}}", "patch") in operations
        assert (f"{path}/{{id}}", "delete") in operations


def test_validator_fails_on_wire_drift_without_printing_tenant_values():
    validate_sample("/locations", "get", 200, {"data": []})
    secret_value = "tenant-value-that-must-not-appear"
    with pytest.raises(AssertionError, match="schema violations") as raised:
        validate_sample("/locations", "get", 200, {"data": [{"id": secret_value}]})
    assert secret_value not in str(raised.value)
    with pytest.raises(AssertionError, match="undocumented HTTP"):
        validate_sample("/locations", "get", 202, {"data": []})


def test_validator_checks_delete_contract_and_empty_body():
    validate_sample("/suppliers/{id}", "delete", 204, None)
    with pytest.raises(AssertionError, match="expected an empty response"):
        validate_sample("/suppliers/{id}", "delete", 204, {"data": []})


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["parser", "validator"])
async def test_create_is_recorded_before_parser_or_validator_failure(
    tmp_path, monkeypatch, failure
):
    module_spec = importlib.util.spec_from_file_location(
        "shared_sdk_contracts_live",
        Path(__file__).parent / "integration/test_shared_sdk_contracts_live.py",
    )
    assert module_spec is not None and module_spec.loader is not None
    live = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(live)

    deleted = []

    def handler(request):
        if request.method == "DELETE":
            deleted.append(request.url.path)
            return httpx.Response(204)
        body = (
            {"id": 1, "name": "SDT-CUSTOMER"}
            if request.method == "POST"
            else {"factory_id": 123}
        )
        return httpx.Response(200, json=body)

    def fail(*args, **kwargs):
        raise RuntimeError("contract failed")

    if failure == "parser":
        endpoint = importlib.import_module(
            live.operation("/customers", "post")["python"]
        )
        monkeypatch.setattr(endpoint, "_parse_response", fail)
    else:
        monkeypatch.setattr(live, "validate_sample", fail)
    async with KatanaClient(
        api_key="test-key",
        base_url="https://katana.test/v1",
        transport=httpx.MockTransport(handler),
        max_retries=0,
    ) as client:
        artifacts = None
        with pytest.raises(RuntimeError, match="contract failed"):
            async with live_test_artifacts(
                client=client, directory=tmp_path
            ) as artifacts:
                await live.call(
                    client,
                    "/customers",
                    "post",
                    body={"name": "SDT-CUSTOMER"},
                    artifacts=artifacts,
                )
        assert artifacts is not None
        assert all(row["deleted_at"] for row in artifacts.rows)
    assert deleted == ["/v1/customers/1"]
