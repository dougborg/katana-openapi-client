"""Build Katana web-app URLs for deep-linking from tool responses.

Tool responses include a ``katana_url`` field where applicable so agents
never compose URLs themselves and can't get path conventions wrong
(e.g., ``manufacturingorder`` vs ``manufacturingorders``).

The base URL comes from ``KATANA_WEB_BASE_URL`` (default
``https://factory.katanamrp.com``), parallel to ``KATANA_BASE_URL`` which
points at the API.

See issue #442 for the motivation and full URL pattern list.
"""

from __future__ import annotations

import os
import re
from typing import Literal
from urllib.parse import urlsplit

EntityKind = Literal[
    "sales_order",
    "manufacturing_order",
    "purchase_order",
    "product",
    "material",
    "customer",
    "supplier",
    "stock_transfer",
    "stock_adjustment",
]

DEFAULT_WEB_BASE_URL = "https://factory.katanamrp.com"

# Path templates per entity. Variants link to their parent product/material —
# Katana's web app does not have per-variant pages.
_PATHS: dict[EntityKind, str] = {
    "sales_order": "/salesorder/{id}",
    "manufacturing_order": "/manufacturingorder/{id}",
    "purchase_order": "/purchaseorder/{id}",
    "product": "/product/{id}",
    "material": "/material/{id}",
    "customer": "/contacts/customers/{id}",
    "supplier": "/contacts/suppliers/{id}",
    "stock_transfer": "/stocktransfer/{id}",
    "stock_adjustment": "/stockadjustment/{id}",
}


def _base_url() -> str:
    return os.getenv("KATANA_WEB_BASE_URL", DEFAULT_WEB_BASE_URL).rstrip("/")


def katana_web_url(kind: EntityKind, id: int | None) -> str | None:
    """Return the web-app URL for an entity, or ``None`` if id is missing.

    ``id is None`` short-circuits to ``None`` so preview-mode responses
    (no id assigned yet) can call this unconditionally.
    """
    if id is None:
        return None
    return f"{_base_url()}{_PATHS[kind].format(id=id)}"


# --- Ecommerce storefront deep-links -----------------------------------------
#
# Sales orders imported from a *native* Katana ecommerce integration carry
# ``ecommerce_order_type`` / ``ecommerce_store_name`` / ``ecommerce_order_id``.
# Katana's web UI renders an "Open in {platform}" link from them via its
# frontend ``EcomLink`` component. There is no API field for the link — Katana
# derives it — so we derive it the same way, to surface it on tool responses.
#
# Provenance: transcribed by hand from Katana's public (unauthenticated)
# module-federation frontend bundles — the ``sales-mf`` ``EcommerceIntegrationType``
# enum + the ``EcomLink`` component — captured 2026-06-03. Confirmed against a
# real captured API payload (``katana.myshopify.com`` / order ``19433769``) and a
# live test-tenant round-trip. See issue #913. ``poe audit-frontend-enums``
# re-checks these keys against the live bundle (soft-fail).
#
# Keys are the EXACT camelCase ``EcommerceIntegrationType`` values — matching is
# case-sensitive (the wire stores the literal verbatim and PATCH cannot change
# it). ``{store}`` = ``ecommerce_store_name``, ``{order_id}`` = ``ecommerce_order_id``.
# For Shopify/WooCommerce ``{store}`` is a full hostname (``acme.myshopify.com``);
# for BigCommerce it is a bare subdomain slug — we mirror the frontend's
# ``store-{store}`` interpolation verbatim. eBay (and every other marketplace) is
# intentionally absent: it lives in ``ThirdPartyIntegrationType``, never gets the
# ``ecommerce_*`` fields populated (it arrives via middleware that writes
# ``order_no``), and the frontend does not deep-link it.
_ECOMMERCE_TEMPLATES: dict[str, str] = {
    "shopify": "https://{store}/admin/orders/{order_id}",
    "wooCommerce": "https://{store}/wp-admin/post.php?post={order_id}&action=edit",
    "bigCommerce": "https://store-{store}.mybigcommerce.com/manage/orders/{order_id}",
}

# Human labels for the same keys, so a card button reads "Open in Shopify"
# rather than the camelCase literal. Kept adjacent to the templates so the
# drift audit can assert both maps share the same key set.
_ECOMMERCE_LABELS: dict[str, str] = {
    "shopify": "Shopify",
    "wooCommerce": "WooCommerce",
    "bigCommerce": "BigCommerce",
}

# The recognized deep-linkable ``ecommerce_order_type`` values, derived from the
# template map so there's one source of truth. Consumed by the create-time
# advisory guard (warn on unrecognized values) and the ``audit-frontend-enums``
# drift check (diff against the live frontend enum).
RECOGNIZED_ECOMMERCE_TYPES: frozenset[str] = frozenset(_ECOMMERCE_TEMPLATES)

# ``ecommerce_store_name`` / ``ecommerce_order_id`` are free-text, create-only
# wire fields that we interpolate straight into an ``https://`` link. Validate
# their shape before building a URL so a crafted value can't repoint the link
# (userinfo ``@``, path/query/fragment ``/ ? #``, or whitespace → somewhere
# unintended) or inject extra query params. ``store`` must look like a hostname
# or a bare subdomain slug (BigCommerce); ``order_id`` must be a bare token. On
# any mismatch we return ``None`` (no link) — better no link than a wrong one.
# ASCII-only labels also reject IDN homograph lookalikes (e.g. a Cyrillic
# U+0430 that mimics an ASCII "a").
# Matched with ``fullmatch`` (not ``match``) so a trailing newline can't slip
# through Python's newline-lenient ``$``; lengths are capped to bound pathological
# input (253 = max DNS hostname; order ids are short numeric strings in practice).
_HOST_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
_STORE_RE = re.compile(rf"{_HOST_LABEL}(?:\.{_HOST_LABEL})*")
_ORDER_ID_RE = re.compile(r"[A-Za-z0-9_-]+")
_MAX_STORE_LEN = 253
_MAX_ORDER_ID_LEN = 64


def ecommerce_storefront_url(
    order_type: str | None,
    store_name: str | None,
    order_id: str | None,
) -> str | None:
    """Build the storefront "Open in {platform}" URL, or ``None``.

    Exact-match ``order_type`` against the camelCase ``EcommerceIntegrationType``
    keys — **no** case normalization (a mis-cased ``"woocommerce"`` returns
    ``None`` by design; the wire stores the literal and coercing it would diverge
    from what Katana's own link matches). Returns ``None`` when the type is
    unrecognized, when ``store_name`` or ``order_id`` is missing/empty, or when
    either fails its host/id-shape guard (see ``_STORE_RE`` / ``_ORDER_ID_RE``) —
    so callers can invoke it unconditionally on any sales order and never surface
    a malformed or attacker-controlled link.
    """
    if not order_type or not store_name or not order_id:
        return None
    template = _ECOMMERCE_TEMPLATES.get(order_type)
    if template is None:
        return None
    if (
        len(store_name) > _MAX_STORE_LEN
        or len(order_id) > _MAX_ORDER_ID_LEN
        or not _STORE_RE.fullmatch(store_name)
        or not _ORDER_ID_RE.fullmatch(order_id)
    ):
        return None
    url = template.format(store=store_name, order_id=order_id)
    # Defense-in-depth: re-parse the assembled URL and refuse anything that isn't
    # a plain ``https`` link with no userinfo. The input guards above already
    # cover today's templates; this also catches a *future* template edit that
    # accidentally drops ``{store}`` into a userinfo/path position, which the
    # per-field checks alone wouldn't notice.
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.username or parsed.password:
        return None
    return url


def ecommerce_platform_label(order_type: str | None) -> str | None:
    """Return the human platform label (e.g. ``"Shopify"``) or ``None``.

    ``None`` for any type that isn't a recognized deep-linkable platform, so
    callers can gate a button/label on it the same way they gate the URL.
    """
    if not order_type:
        return None
    return _ECOMMERCE_LABELS.get(order_type)
