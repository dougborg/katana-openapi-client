"""External documentation comparison tests.

Validates ``docs/katana-openapi.yaml`` against the live upstream OpenAPI
spec at ``docs/upstream-specs/live-gateway.yaml`` (refreshed by
``poe refresh-upstream-spec``). All comparison logic comes from
``scripts/audit_spec_drift.audit()``; this module just runs the audit
and asserts on the structured findings.

Internal spec quality (schema validity, structure, etc.) is covered by:

- ``test_openapi_specification.py`` — OpenAPI document structure
- ``test_schema_comprehensive.py`` — schema-level checks
- ``test_endpoint_comprehensive.py`` — endpoint-level checks
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

# Ensure the project root is on sys.path so ``scripts`` is importable.
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit_spec_drift import AuditReport, audit  # noqa: E402

LOCAL_SPEC_PATH = PROJECT_ROOT / "docs" / "katana-openapi.yaml"
LIVE_SPEC_PATH = PROJECT_ROOT / "docs" / "upstream-specs" / "live-gateway.yaml"


@pytest.fixture(scope="module")
def local_spec(openapi_spec: dict[str, Any]) -> dict[str, Any]:
    """Re-export the session-scoped OpenAPI spec under this module's name."""
    return openapi_spec


@pytest.fixture(scope="module")
def live_spec() -> dict[str, Any]:
    if not LIVE_SPEC_PATH.exists():
        pytest.skip(
            f"{LIVE_SPEC_PATH.relative_to(PROJECT_ROOT)} not present — "
            "run `uv run poe refresh-upstream-spec` first"
        )
    return yaml.safe_load(LIVE_SPEC_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def drift_report(local_spec: dict[str, Any], live_spec: dict[str, Any]) -> AuditReport:
    return audit(local_spec, live_spec)


# ---------------------------------------------------------------------------
# Spec-loading sanity
# ---------------------------------------------------------------------------


def test_local_spec_loads(local_spec: dict[str, Any]) -> None:
    assert isinstance(local_spec, dict)
    assert "paths" in local_spec


def test_live_spec_loads(live_spec: dict[str, Any]) -> None:
    assert isinstance(live_spec, dict)
    assert "paths" in live_spec


# ---------------------------------------------------------------------------
# Endpoint coverage (live vs local)
# ---------------------------------------------------------------------------


def test_no_endpoints_missing_from_local(drift_report: AuditReport) -> None:
    """Every (path, method) in the live gateway spec should exist locally."""
    missing = drift_report.paths_only_in_live
    assert not missing, (
        f"{len(missing)} endpoints in live but not local spec. "
        "Refresh the upstream spec, then add them locally. Missing: "
        f"{[f'{m.upper()} {p}' for p, m in missing]}"
    )


def test_no_invented_endpoints(drift_report: AuditReport) -> None:
    """Every (path, method) in the local spec should exist in the live gateway.

    The live gateway is the canonical source; anything we expose locally
    that the gateway doesn't is either an alias / legacy endpoint kept
    for backwards compatibility or a real spec bug. The audit doc tracks
    documented exceptions; raise the bar if new ones appear.
    """
    only_local = drift_report.paths_only_in_local
    documented_locals = {
        # Live spec uses an inline (no $ref) request schema for these;
        # ``audit_spec_drift`` skips inline-schema endpoints during DTO
        # mapping but still flags them in the path-coverage diff.
        ("/inventory_reorder_points", "post"),
        ("/inventory_safety_stock_levels", "post"),
        ("/purchase_order_receive", "post"),
        ("/unlink_variant_bin_locations", "post"),
        ("/variant_bin_locations", "post"),
    }
    surprise = [(p, m) for p, m in only_local if (p, m) not in documented_locals]
    assert not surprise, (
        f"{len(surprise)} unexpected endpoints in local spec. "
        "Either the live spec dropped them or our spec invented them. "
        f"Surprise: {[f'{m.upper()} {p}' for p, m in surprise]}"
    )


# ---------------------------------------------------------------------------
# Static spec-quality checks (no live spec needed)
# ---------------------------------------------------------------------------


def test_security_scheme_completeness(local_spec: dict[str, Any]) -> None:
    """Bearer auth must be defined."""
    schemes = local_spec.get("components", {}).get("securitySchemes", {})
    assert "bearerAuth" in schemes, f"bearerAuth missing. Got: {list(schemes.keys())}"
    bearer = schemes["bearerAuth"]
    assert bearer.get("type") == "http"
    assert bearer.get("scheme") == "bearer"


@pytest.mark.parametrize(
    "expected_path",
    [
        "/inventory",
        "/manufacturing_orders",
        "/sales_orders",
    ],
)
def test_core_endpoints_exposed(local_spec: dict[str, Any], expected_path: str) -> None:
    """Core CRUD list endpoints must be present in the local spec."""
    assert expected_path in local_spec.get("paths", {}), (
        f"Core endpoint {expected_path!r} missing from local spec"
    )
