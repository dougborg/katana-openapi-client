"""Cache synchronization helpers for Katana entity types.

Bridges the CatalogCache with the Katana API — handles fetching entities
from the API (with incremental sync via updated_at_min) and storing them
in the cache.

Usage in tools::

    services = get_services(context)
    await ensure_variants_synced(services)
    results = await services.cache.smart_search("variant", query, limit=20)
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from katana_mcp.cache import (
    CUSTOMER_INDEX,
    LOCATION_INDEX,
    MATERIAL_INDEX,
    OPERATOR_INDEX,
    PRODUCT_INDEX,
    SERVICE_INDEX,
    SUPPLIER_INDEX,
    TAX_RATE_INDEX,
    VARIANT_INDEX,
    IndexFields,
)
from katana_public_api_client.api.customer import get_all_customers
from katana_public_api_client.api.location import get_all_locations
from katana_public_api_client.api.material import get_all_materials
from katana_public_api_client.api.operator import get_all_operators
from katana_public_api_client.api.product import get_all_products
from katana_public_api_client.api.services import get_all_services
from katana_public_api_client.api.supplier import get_all_suppliers
from katana_public_api_client.api.tax_rate import get_all_tax_rates
from katana_public_api_client.api.variant import get_all_variants
from katana_public_api_client.models.get_all_variants_extend_item import (
    GetAllVariantsExtendItem,
)
from katana_public_api_client.utils import unwrap_data

if TYPE_CHECKING:
    from katana_mcp.services.dependencies import Services

logger = logging.getLogger(__name__)

# Minimum interval (seconds) between sync attempts for entities without updated_at_min
_NO_INCREMENTAL_DEBOUNCE = 300  # 5 minutes


def _timestamp_to_iso(ts: float) -> str:
    """Convert a unix timestamp to ISO 8601 string for API filtering."""
    return datetime.fromtimestamp(ts, tz=UTC).isoformat()


def _attrs_to_dicts(attrs_list: list[Any]) -> list[dict[str, Any]]:
    """Convert a list of attrs model instances to plain dicts."""
    result = []
    for obj in attrs_list:
        if hasattr(obj, "to_dict"):
            result.append(obj.to_dict())
        elif hasattr(obj, "__dict__"):
            result.append(vars(obj))
        else:
            result.append(obj)
    return result


def _variant_to_cache_dict(attrs_obj: Any) -> dict[str, Any]:
    """Convert a variant attrs model to a cache-friendly dict with display fields."""
    d = attrs_obj.to_dict() if hasattr(attrs_obj, "to_dict") else vars(attrs_obj)

    # Extract product_or_material info for indexing
    pom = d.get("product_or_material")
    parent_name = ""
    variant_type = ""
    if isinstance(pom, dict):
        parent_name = pom.get("name", "")
        variant_type = pom.get("type", "")
    elif pom and hasattr(pom, "name"):
        parent_name = getattr(pom, "name", "")
        variant_type = getattr(pom, "type_", "")

    d["parent_name"] = parent_name
    d["type"] = variant_type

    # Build display name for FTS indexing
    sku = d.get("sku", "")
    display_parts = [parent_name] if parent_name else [sku]
    config_attrs = d.get("config_attributes", [])
    if isinstance(config_attrs, list):
        for attr in config_attrs:
            if isinstance(attr, dict) and (val := attr.get("config_value")):
                display_parts.append(val)
    d["display_name"] = " / ".join(display_parts)

    return d


async def ensure_variants_synced(services: Services) -> None:
    """Ensure the variant cache is fresh, syncing from API if needed."""
    await _ensure_synced(
        services=services,
        entity_type="variant",
        index_fields=VARIANT_INDEX,
        fetch_fn=_fetch_variants,
        supports_incremental=True,
    )


async def ensure_products_synced(services: Services) -> None:
    """Ensure the product cache is fresh."""
    await _ensure_synced(
        services=services,
        entity_type="product",
        index_fields=PRODUCT_INDEX,
        fetch_fn=_fetch_products,
        supports_incremental=True,
    )


async def ensure_materials_synced(services: Services) -> None:
    """Ensure the material cache is fresh."""
    await _ensure_synced(
        services=services,
        entity_type="material",
        index_fields=MATERIAL_INDEX,
        fetch_fn=_fetch_materials,
        supports_incremental=True,
    )


async def ensure_services_synced(services: Services) -> None:
    """Ensure the service cache is fresh."""
    await _ensure_synced(
        services=services,
        entity_type="service",
        index_fields=SERVICE_INDEX,
        fetch_fn=_fetch_services,
        supports_incremental=True,
    )


async def ensure_suppliers_synced(services: Services) -> None:
    """Ensure the supplier cache is fresh."""
    await _ensure_synced(
        services=services,
        entity_type="supplier",
        index_fields=SUPPLIER_INDEX,
        fetch_fn=_fetch_suppliers,
        supports_incremental=True,
    )


async def ensure_customers_synced(services: Services) -> None:
    """Ensure the customer cache is fresh."""
    await _ensure_synced(
        services=services,
        entity_type="customer",
        index_fields=CUSTOMER_INDEX,
        fetch_fn=_fetch_customers,
        supports_incremental=True,
    )


async def ensure_locations_synced(services: Services) -> None:
    """Ensure the location cache is fresh."""
    await _ensure_synced(
        services=services,
        entity_type="location",
        index_fields=LOCATION_INDEX,
        fetch_fn=_fetch_locations,
        supports_incremental=False,
    )


async def ensure_tax_rates_synced(services: Services) -> None:
    """Ensure the tax rate cache is fresh."""
    await _ensure_synced(
        services=services,
        entity_type="tax_rate",
        index_fields=TAX_RATE_INDEX,
        fetch_fn=_fetch_tax_rates,
        supports_incremental=True,
    )


async def ensure_operators_synced(services: Services) -> None:
    """Ensure the operator cache is fresh."""
    await _ensure_synced(
        services=services,
        entity_type="operator",
        index_fields=OPERATOR_INDEX,
        fetch_fn=_fetch_operators,
        supports_incremental=False,
    )


# ── Internal sync logic ──────────────────────────────────────────────


async def _ensure_synced(
    services: Services,
    entity_type: str,
    index_fields: IndexFields,
    fetch_fn: Any,
    supports_incremental: bool,
) -> None:
    """Generic sync: check last_synced → incremental or full fetch → store."""
    import time

    cache = services.cache
    last_synced = await cache.get_last_synced(entity_type)

    if last_synced is not None and not supports_incremental:
        # For non-incremental entities, debounce full fetches
        age = time.time() - last_synced
        if age < _NO_INCREMENTAL_DEBOUNCE:
            return

    # Fetch from API (incremental if possible)
    updated_at_min = (
        _timestamp_to_iso(last_synced) if last_synced and supports_incremental else None
    )
    entities = await fetch_fn(services.client, updated_at_min=updated_at_min)

    if entities or last_synced is None:
        await cache.sync(entity_type, entities, index_fields)
        logger.info(
            "cache_sync_complete",
            entity_type=entity_type,
            fetched=len(entities),
            incremental=updated_at_min is not None,
        )


# ── API fetch functions ──────────────────────────────────────────────


async def _fetch_variants(client: Any, updated_at_min: str | None = None) -> list[dict]:
    kwargs: dict[str, Any] = {
        "client": client,
        "extend": [GetAllVariantsExtendItem.PRODUCT_OR_MATERIAL],
    }
    if updated_at_min:
        kwargs["updated_at_min"] = updated_at_min

    response = await get_all_variants.asyncio_detailed(**kwargs)
    attrs_list = unwrap_data(response)
    return [_variant_to_cache_dict(v) for v in attrs_list]


async def _fetch_products(client: Any, updated_at_min: str | None = None) -> list[dict]:
    kwargs: dict[str, Any] = {"client": client}
    if updated_at_min:
        kwargs["updated_at_min"] = updated_at_min

    response = await get_all_products.asyncio_detailed(**kwargs)
    return _attrs_to_dicts(unwrap_data(response))


async def _fetch_materials(
    client: Any, updated_at_min: str | None = None
) -> list[dict]:
    kwargs: dict[str, Any] = {"client": client}
    if updated_at_min:
        kwargs["updated_at_min"] = updated_at_min

    response = await get_all_materials.asyncio_detailed(**kwargs)
    return _attrs_to_dicts(unwrap_data(response))


async def _fetch_services(client: Any, updated_at_min: str | None = None) -> list[dict]:
    kwargs: dict[str, Any] = {"client": client}
    if updated_at_min:
        kwargs["updated_at_min"] = updated_at_min

    response = await get_all_services.asyncio_detailed(**kwargs)
    return _attrs_to_dicts(unwrap_data(response))


async def _fetch_suppliers(
    client: Any, updated_at_min: str | None = None
) -> list[dict]:
    kwargs: dict[str, Any] = {"client": client}
    if updated_at_min:
        kwargs["updated_at_min"] = updated_at_min

    response = await get_all_suppliers.asyncio_detailed(**kwargs)
    return _attrs_to_dicts(unwrap_data(response))


async def _fetch_customers(
    client: Any, updated_at_min: str | None = None
) -> list[dict]:
    kwargs: dict[str, Any] = {"client": client}
    if updated_at_min:
        kwargs["updated_at_min"] = updated_at_min

    response = await get_all_customers.asyncio_detailed(**kwargs)
    return _attrs_to_dicts(unwrap_data(response))


async def _fetch_locations(
    client: Any, updated_at_min: str | None = None
) -> list[dict]:
    # Locations don't support updated_at_min
    response = await get_all_locations.asyncio_detailed(client=client)
    return _attrs_to_dicts(unwrap_data(response))


async def _fetch_tax_rates(
    client: Any, updated_at_min: str | None = None
) -> list[dict]:
    kwargs: dict[str, Any] = {"client": client}
    if updated_at_min:
        kwargs["updated_at_min"] = updated_at_min

    response = await get_all_tax_rates.asyncio_detailed(**kwargs)
    return _attrs_to_dicts(unwrap_data(response))


async def _fetch_operators(
    client: Any, updated_at_min: str | None = None
) -> list[dict]:
    # Operators don't support updated_at_min
    response = await get_all_operators.asyncio_detailed(client=client)
    return _attrs_to_dicts(unwrap_data(response))
