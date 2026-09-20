"""Persistent, tenant-scoped cleanup for live test artifacts.

Ledger rows use the spec-drift ledger format. Each fixture owns a separate
file, so concurrent test processes cannot overwrite one another's records.
Recovery always authenticates through ``make_test_client``.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import tempfile
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from .katana_client import KatanaClient
from .testing import make_test_client


def ledger_directory() -> Path:
    """Return the persistent directory shared by tests and the recovery CLI."""
    return Path(
        os.environ.get("KATANA_TEST_LEDGER_DIR")
        or Path(tempfile.gettempdir()) / "katana-test-ledgers"
    )


def _valid_artifact(endpoint: Any, entity_id: Any) -> bool:
    return (
        isinstance(endpoint, str)
        and re.fullmatch(r"/[a-z_]+", endpoint) is not None
        and type(entity_id) in (int, str)
        and re.fullmatch(r"[A-Za-z0-9-]+", str(entity_id)) is not None
    )


async def _factory_id(client: KatanaClient) -> int:
    response = await client.get_async_httpx_client().get("/factory")
    response.raise_for_status()
    factory_id = response.json().get("factory_id")
    if type(factory_id) is not int or factory_id <= 0:
        raise RuntimeError("Cannot establish test tenant factory_id; refusing writes")
    return factory_id


class LiveTestArtifacts:
    """Records created resources and deletes them in reverse creation order.

    Record only resources this test created. Children deleted with a tracked
    parent need no separate entry. Ledger files contain IDs and tenant
    fingerprints, never credentials or response payloads.
    """

    def __init__(self, *, client: KatanaClient, factory_id: int, path: Path) -> None:
        self.client = client
        self.factory_id = factory_id
        self.path = path
        self.base_url = str(client.get_async_httpx_client().base_url).rstrip("/")
        self.rows: list[dict[str, Any]] = []

    def tag(self, name: str) -> str:
        """Give a resource a discoverable, run-unique SDT identity."""
        return f"SDT-{datetime.now(UTC):%Y-%m-%d}-{self.path.stem[-8:]}-{name}"

    def _save(self) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            "".join(json.dumps(row) + "\n" for row in self.rows), encoding="utf-8"
        )
        temporary.replace(self.path)

    def record(self, *, endpoint: str, entity_id: int | str, issue: str) -> None:
        """Register immediately after creation, before any other assertion.

        Add to memory before writing so fixture teardown still attempts
        cleanup if the filesystem write fails.
        """
        if not _valid_artifact(endpoint, entity_id):
            raise ValueError("Expected a collection path and a resource ID")
        self.rows.append(
            {
                "endpoint": endpoint,
                "entity_id": entity_id,
                "issue": issue,
                "method": "POST",
                "created_at": datetime.now(UTC).isoformat(),
                "base_url": self.base_url,
                "factory_id": self.factory_id,
                "deleted_at": None,
                "delete_error": None,
            }
        )
        self._save()

    async def cleanup(self) -> None:
        """Delete tracked resources; retain failures for recovery and fail loudly."""
        pending = [row for row in self.rows if not row.get("deleted_at")]
        if not pending:
            return
        current_factory = await _factory_id(self.client)
        current_base = str(self.client.get_async_httpx_client().base_url).rstrip("/")
        # Check the entire ledger before the first deletion. A mismatched or
        # missing fingerprint must never authorize cleanup on another tenant.
        for row in pending:
            if (
                row.get("factory_id") != current_factory
                or row.get("base_url") != current_base
                or not _valid_artifact(row.get("endpoint"), row.get("entity_id"))
            ):
                raise RuntimeError(
                    f"Unverifiable or foreign artifact ledger: {self.path}"
                )
        failures: list[Exception] = []
        for row in reversed(pending):
            try:
                response = await self.client.get_async_httpx_client().delete(
                    f"{row['endpoint']}/{row['entity_id']}"
                )
                if response.status_code != 404:
                    response.raise_for_status()
                row["deleted_at"] = datetime.now(UTC).isoformat()
                row["delete_error"] = None
            except Exception as exc:
                row["delete_error"] = str(exc)
                failures.append(exc)
            try:
                self._save()
            except OSError as exc:
                failures.append(exc)
        if failures:
            raise ExceptionGroup(
                f"Artifact cleanup failed; recover {self.path}", failures
            )


@asynccontextmanager
async def live_test_artifacts(
    *, client: KatanaClient, directory: Path | None = None
) -> AsyncIterator[LiveTestArtifacts]:
    """Create a ledger before writes and clean its resources on every exit."""
    factory_id = await _factory_id(client)
    directory = directory or ledger_directory()
    directory.mkdir(parents=True, exist_ok=True)
    artifacts = LiveTestArtifacts(
        client=client,
        factory_id=factory_id,
        path=directory / f"{factory_id}-{uuid4().hex}.jsonl",
    )
    artifacts._save()
    try:
        yield artifacts
    finally:
        await artifacts.cleanup()


async def recover_artifacts(*, directory: Path) -> None:
    """Retry pending ledgers using only test-tenant credentials."""
    async with make_test_client() as client:
        factory_id = await _factory_id(client)
        failures: list[Exception] = []
        for path in sorted(directory.glob("*.jsonl")):
            try:
                artifacts = LiveTestArtifacts(
                    client=client, factory_id=factory_id, path=path
                )
                artifacts.rows = [
                    json.loads(line) for line in path.read_text().splitlines() if line
                ]
                await artifacts.cleanup()
            except Exception as exc:
                failures.append(exc)
        if failures:
            raise ExceptionGroup("Test artifact recovery failed", failures)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger-dir", type=Path, default=ledger_directory())
    args = parser.parse_args()
    asyncio.run(recover_artifacts(directory=args.ledger_dir))
