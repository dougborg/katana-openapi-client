"""Exercise cleanup across assertion, network, storage, and tenant failures."""

import json
from pathlib import Path

import httpx
import pytest
import time_machine

from katana_public_api_client import KatanaClient
from katana_public_api_client.testing_artifacts import (
    LiveTestArtifacts,
    live_test_artifacts,
)

pytestmark = pytest.mark.asyncio


def _client(handler) -> KatanaClient:
    return KatanaClient(
        api_key="test-key",
        base_url="https://katana.test/v1",
        transport=httpx.MockTransport(handler),
        max_retries=0,
    )


async def test_assertion_failure_cleans_children_before_parents(tmp_path: Path) -> None:
    deleted = []
    artifacts: LiveTestArtifacts | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json={"factory_id": 123})
        deleted.append(request.url.path)
        return httpx.Response(204)

    with time_machine.travel("2026-09-20", tick=False):
        async with _client(handler) as client:
            with pytest.raises(AssertionError, match="test failed"):
                async with live_test_artifacts(
                    client=client, directory=tmp_path
                ) as artifacts:
                    assert artifacts.tag("SO").startswith("SDT-2026-09-20-")
                    artifacts.record(
                        endpoint="/sales_orders", entity_id=1, issue="#test"
                    )
                    artifacts.record(
                        endpoint="/sales_order_rows", entity_id=2, issue="#test"
                    )
                    persisted = [
                        json.loads(line)
                        for line in artifacts.path.read_text().splitlines()
                    ]
                    assert all(row["factory_id"] == 123 for row in persisted)
                    assert all(
                        row["base_url"] == "https://katana.test/v1" for row in persisted
                    )
                    raise AssertionError("test failed")

    assert deleted == ["/v1/sales_order_rows/2", "/v1/sales_orders/1"]
    assert artifacts is not None
    assert all(
        json.loads(line)["deleted_at"]
        for line in artifacts.path.read_text().splitlines()
    )


async def test_cleanup_continues_after_failure_and_retries_only_pending(
    tmp_path: Path,
) -> None:
    deleted = []
    fail = True
    artifacts: LiveTestArtifacts | None = None

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(200, json={"factory_id": 123})
        deleted.append(request.url.path)
        if fail and request.url.path.endswith("/2"):
            return httpx.Response(422, json={"error": "blocked"})
        return httpx.Response(404)

    async with _client(handler) as client:
        with pytest.raises(ExceptionGroup, match="Artifact cleanup failed"):
            async with live_test_artifacts(
                client=client, directory=tmp_path
            ) as artifacts:
                artifacts.record(endpoint="/sales_orders", entity_id=1, issue="#test")
                artifacts.record(endpoint="/sales_orders", entity_id=2, issue="#test")
        assert artifacts is not None
        assert artifacts.rows[0]["deleted_at"]
        assert artifacts.rows[1]["deleted_at"] is None
        assert artifacts.rows[1]["delete_error"]
        fail = False
        await artifacts.cleanup()
        await artifacts.cleanup()
    assert deleted == ["/v1/sales_orders/2", "/v1/sales_orders/1", "/v1/sales_orders/2"]
    assert artifacts.rows[1]["delete_error"] is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("factory_id", 456),
        ("factory_id", None),
        ("base_url", "https://other.test/v1"),
        ("base_url", None),
        ("endpoint", "/../sales_orders"),
        ("entity_id", "1/../2"),
        ("entity_id", None),
    ],
)
async def test_foreign_or_invalid_ledger_never_deletes(
    tmp_path: Path, field: str, value
) -> None:
    deleted = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            deleted.append(request.url.path)
        return httpx.Response(200, json={"factory_id": 123})

    async with _client(handler) as client:
        with pytest.raises(RuntimeError, match="Unverifiable or foreign"):
            async with live_test_artifacts(
                client=client, directory=tmp_path
            ) as artifacts:
                artifacts.record(endpoint="/sales_orders", entity_id=1, issue="#test")
                artifacts.rows[0][field] = value
    assert deleted == []


async def test_changed_tenant_refuses_cleanup(tmp_path: Path) -> None:
    factory_id = 123
    deleted = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            deleted.append(request.url.path)
        return httpx.Response(200, json={"factory_id": factory_id})

    async with _client(handler) as client:
        with pytest.raises(RuntimeError, match="Unverifiable or foreign"):
            async with live_test_artifacts(
                client=client, directory=tmp_path
            ) as artifacts:
                artifacts.record(endpoint="/sales_orders", entity_id=1, issue="#test")
                factory_id = 456
    assert deleted == []


async def test_failed_ledger_write_still_cleans_created_resource(
    tmp_path: Path, monkeypatch
) -> None:
    deleted = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            deleted.append(request.url.path)
            return httpx.Response(204)
        return httpx.Response(200, json={"factory_id": 123})

    def fail_save() -> None:
        raise OSError("disk full")

    async with _client(handler) as client:
        with pytest.raises(OSError, match="disk full"):
            async with live_test_artifacts(
                client=client, directory=tmp_path
            ) as artifacts:
                with monkeypatch.context() as patch:
                    patch.setattr(artifacts, "_save", fail_save)
                    artifacts.record(
                        endpoint="/sales_orders", entity_id=1, issue="#test"
                    )
    assert deleted == ["/v1/sales_orders/1"]


async def test_missing_factory_fails_before_test_can_write(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    async with _client(handler) as client:
        with pytest.raises(RuntimeError, match="Cannot establish"):
            async with live_test_artifacts(client=client, directory=tmp_path):
                pytest.fail("Must not yield without a factory fingerprint")
    assert not list(tmp_path.iterdir())


async def test_recovery_reads_pending_rows_and_continues_past_foreign_file(
    tmp_path: Path, monkeypatch
) -> None:
    from katana_public_api_client import testing_artifacts

    deleted = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "DELETE":
            deleted.append(request.url.path)
            return httpx.Response(204)
        return httpx.Response(200, json={"factory_id": 123})

    monkeypatch.setattr(testing_artifacts, "make_test_client", lambda: _client(handler))
    row = {
        "endpoint": "/sales_orders",
        "entity_id": 1,
        "base_url": "https://katana.test/v1",
        "factory_id": 456,
        "deleted_at": None,
    }
    (tmp_path / "a-foreign.jsonl").write_text(json.dumps(row) + "\n")
    row.update(factory_id=123, entity_id=2)
    own_path = tmp_path / "b-own.jsonl"
    own_path.write_text(json.dumps(row) + "\n")
    with pytest.raises(ExceptionGroup, match="Test artifact recovery failed"):
        await testing_artifacts.recover_artifacts(directory=tmp_path)
    assert deleted == ["/v1/sales_orders/2"]
    assert json.loads(own_path.read_text())["deleted_at"]
