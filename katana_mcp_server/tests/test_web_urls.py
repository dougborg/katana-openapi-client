"""Tests for the Katana web-app URL helper."""

from __future__ import annotations

import pytest
from katana_mcp.web_urls import (
    DEFAULT_WEB_BASE_URL,
    RECOGNIZED_ECOMMERCE_TYPES,
    EntityKind,
    ecommerce_platform_label,
    ecommerce_storefront_url,
    katana_web_url,
)


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


# --- Ecommerce storefront deep-links -----------------------------------------


@pytest.mark.parametrize(
    ("order_type", "store", "order_id", "expected"),
    [
        # Verified against a real captured Katana payload (#913): a Shopify
        # order stores the myshopify host + numeric order id.
        (
            "shopify",
            "katana.myshopify.com",
            "19433769",
            "https://katana.myshopify.com/admin/orders/19433769",
        ),
        (
            "wooCommerce",
            "shop.acme.com",
            "501",
            "https://shop.acme.com/wp-admin/post.php?post=501&action=edit",
        ),
        # BigCommerce stores the bare slug; the frontend prefixes ``store-``.
        (
            "bigCommerce",
            "acme",
            "777",
            "https://store-acme.mybigcommerce.com/manage/orders/777",
        ),
    ],
)
def test_storefront_url_happy_paths(
    order_type: str, store: str, order_id: str, expected: str
) -> None:
    assert ecommerce_storefront_url(order_type, store, order_id) == expected


@pytest.mark.parametrize(
    ("order_type", "store", "order_id"),
    [
        # eBay/Etsy/etc. are not deep-linkable (ThirdPartyIntegrationType).
        ("ebay", "store", "1"),
        # Mis-cased platform must NOT coerce — the wire stores the literal and
        # the frontend matches camelCase exactly.
        ("woocommerce", "shop.acme.com", "1"),
        ("Shopify", "acme.myshopify.com", "1"),
        # Missing pieces — can't build a link.
        ("shopify", None, "1"),
        ("shopify", "acme.myshopify.com", None),
        ("shopify", "", "1"),
        ("shopify", "acme.myshopify.com", ""),
        (None, "acme.myshopify.com", "1"),
    ],
)
def test_storefront_url_returns_none(
    order_type: str | None, store: str | None, order_id: str | None
) -> None:
    assert ecommerce_storefront_url(order_type, store, order_id) is None


@pytest.mark.parametrize(
    ("store", "order_id"),
    [
        # store_name with userinfo / path / query / fragment / port / whitespace
        # could repoint the rendered link — reject, don't interpolate.
        ("evil.com/@phish", "1"),
        ("acme.myshopify.com@evil.com", "1"),
        ("acme.myshopify.com/admin", "1"),
        ("acme.myshopify.com?x=1", "1"),
        ("acme.myshopify.com#frag", "1"),
        ("acme.myshopify.com:8080", "1"),
        ("acme .myshopify.com", "1"),
        ("-acme.myshopify.com", "1"),
        ("acme..myshopify.com", "1"),
        # order_id that could inject extra path/query segments (e.g. an extra
        # &param into the WooCommerce query) must be refused too.
        ("acme.myshopify.com", "1/2"),
        ("acme.myshopify.com", "1&action=delete"),
        ("acme.myshopify.com", "1 2"),
        ("acme.myshopify.com", "1?x=2"),
        # Trailing newline must NOT slip through (Python's ``$`` is newline-
        # lenient; we use fullmatch precisely to close this).
        ("acme.myshopify.com\n", "1"),
        ("acme.myshopify.com", "1\n"),
        # IDN homograph: a Cyrillic U+0430 that *looks* like ASCII "a" must be
        # rejected — labels are ASCII-only.
        ("\u0430cme.myshopify.com", "1"),
        # Over-length input is bounded (253 host / 64 order-id caps).
        ("a" * 254, "1"),
        ("acme.myshopify.com", "1" * 65),
    ],
)
def test_storefront_url_rejects_unsafe_values(store: str, order_id: str) -> None:
    """Free-text ecommerce fields that don't look host/id-like build no link,
    so a crafted value can't produce a malformed or attacker-controlled URL."""
    assert ecommerce_storefront_url("shopify", store, order_id) is None


def test_storefront_url_allows_max_length_boundary() -> None:
    """A host/id exactly at the cap still builds a link — the bound is
    inclusive, so we don't reject legitimate long-but-valid values."""
    store = ("a" * 60 + ".") * 4 + "co"  # 245 chars, well-formed labels
    assert len(store) <= 253
    assert (
        ecommerce_storefront_url("shopify", store, "1" * 64)
        == f"https://{store}/admin/orders/{'1' * 64}"
    )


def test_platform_label() -> None:
    assert ecommerce_platform_label("shopify") == "Shopify"
    assert ecommerce_platform_label("wooCommerce") == "WooCommerce"
    assert ecommerce_platform_label("bigCommerce") == "BigCommerce"
    assert ecommerce_platform_label("ebay") is None
    assert ecommerce_platform_label(None) is None


def test_recognized_set_is_exactly_the_three_native_platforms() -> None:
    """Pins the deep-linkable set; ``audit-frontend-enums`` guards live drift."""
    assert {"shopify", "wooCommerce", "bigCommerce"} == RECOGNIZED_ECOMMERCE_TYPES


def test_every_recognized_platform_has_a_label() -> None:
    """Template and label maps must share an identical key set.

    The import-time invariant in ``web_urls`` enforces this so a new template
    can't ship without its "Open in {platform}" label; this test pins the
    contract independently (the drift audit only checks template keys against
    the live frontend and never inspects the labels).
    """
    assert all(
        ecommerce_platform_label(platform) is not None
        for platform in RECOGNIZED_ECOMMERCE_TYPES
    )
