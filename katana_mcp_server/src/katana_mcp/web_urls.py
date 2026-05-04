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
from typing import Literal

EntityKind = Literal[
    "sales_order",
    "manufacturing_order",
    "purchase_order",
    "product",
    "material",
    "customer",
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
