"""Tests for the Katana web-app URL helper."""

from __future__ import annotations

import pytest
from katana_mcp.web_urls import DEFAULT_WEB_BASE_URL, EntityKind, katana_web_url


@pytest.mark.parametrize(
    ("kind", "id", "expected_path"),
    [
        ("sales_order", 12345, "/salesorder/12345"),
        ("manufacturing_order", 67890, "/manufacturingorder/67890"),
        ("purchase_order", 1, "/purchaseorder/1"),
        # Katana's web app uses singular nouns for entity routes; products
        # and materials each have their own route (verified live, #454).
        ("product", 42, "/product/42"),
        ("material", 99, "/material/99"),
        ("customer", 7, "/contacts/customers/7"),
        ("stock_transfer", 555, "/stocktransfer/555"),
        ("stock_adjustment", 222, "/stockadjustment/222"),
    ],
)
def test_known_entity_kinds_build_expected_url(
    kind: EntityKind, id: int, expected_path: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("KATANA_WEB_BASE_URL", raising=False)
    assert katana_web_url(kind, id) == f"{DEFAULT_WEB_BASE_URL}{expected_path}"


def test_none_id_returns_none() -> None:
    """Preview-mode responses (no id yet) get None — callers can pass through."""
    assert katana_web_url("sales_order", None) is None


def test_env_override_is_honored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("KATANA_WEB_BASE_URL", "https://eu.katanamrp.com")
    assert katana_web_url("sales_order", 1) == "https://eu.katanamrp.com/salesorder/1"


def test_trailing_slash_on_base_is_stripped(monkeypatch: pytest.MonkeyPatch) -> None:
    """A trailing slash on the configured base must not double up."""
    monkeypatch.setenv("KATANA_WEB_BASE_URL", "https://factory.katanamrp.com/")
    url = katana_web_url("manufacturing_order", 9)
    assert url == "https://factory.katanamrp.com/manufacturingorder/9"
    assert "//manufacturingorder" not in url


def test_default_constant_matches_documented_value() -> None:
    """The default must match the value documented in CLAUDE.md and #442."""
    assert DEFAULT_WEB_BASE_URL == "https://factory.katanamrp.com"
