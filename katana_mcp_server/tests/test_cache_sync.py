"""Tests for cache synchronization helpers.

Covers the critical incremental sync path where updated_at_min is passed
to the API, ensuring datetime objects (not strings) are used.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.cache_sync import (
    _ensure_synced,
    _timestamp_to_datetime,
    _variant_to_cache_dict,
    ensure_variants_synced,
)

# ============================================================================
# _timestamp_to_datetime
# ============================================================================


class TestTimestampToDatetime:
    """Verify the timestamp converter returns timezone-aware datetime objects."""

    def test_returns_datetime_not_string(self):
        result = _timestamp_to_datetime(1700000000.0)
        assert isinstance(result, datetime)
        assert not isinstance(result, str)

    def test_is_utc_aware(self):
        result = _timestamp_to_datetime(0.0)
        assert result.tzinfo is UTC

    def test_roundtrip_preserves_value(self):
        ts = time.time()
        result = _timestamp_to_datetime(ts)
        assert abs(result.timestamp() - ts) < 0.001


# ============================================================================
# _variant_to_cache_dict
# ============================================================================


class TestVariantToCacheDict:
    """Verify variant enrichment for cache storage."""

    def test_extracts_parent_name_from_dict(self):
        attrs_obj = MagicMock()
        attrs_obj.to_dict.return_value = {
            "id": 1,
            "sku": "SKU-001",
            "product_or_material": {"name": "Widget", "type": "product"},
            "config_attributes": [],
        }
        result = _variant_to_cache_dict(attrs_obj)
        assert result["parent_name"] == "Widget"
        assert result["type"] == "product"
        assert result["display_name"] == "Widget"

    def test_display_name_includes_config_attrs(self):
        attrs_obj = MagicMock()
        attrs_obj.to_dict.return_value = {
            "id": 2,
            "sku": "SKU-002",
            "product_or_material": {"name": "Widget", "type": "product"},
            "config_attributes": [
                {"config_name": "Color", "config_value": "Red"},
                {"config_name": "Size", "config_value": "Large"},
            ],
        }
        result = _variant_to_cache_dict(attrs_obj)
        assert result["display_name"] == "Widget / Red / Large"

    def test_falls_back_to_sku_without_parent(self):
        attrs_obj = MagicMock()
        attrs_obj.to_dict.return_value = {
            "id": 3,
            "sku": "SKU-003",
            "product_or_material": None,
            "config_attributes": [],
        }
        result = _variant_to_cache_dict(attrs_obj)
        assert result["display_name"] == "SKU-003"


# ============================================================================
# _ensure_synced — incremental sync path
# ============================================================================


class TestEnsureSynced:
    """Test the core sync logic, especially the incremental sync path."""

    @pytest.fixture
    def services(self):
        svc = MagicMock()
        svc.cache = AsyncMock()
        svc.client = MagicMock()
        return svc

    @pytest.mark.asyncio
    async def test_incremental_sync_passes_datetime_not_string(self, services):
        """The bug: updated_at_min was passed as str, but API expects datetime."""
        last_synced_ts = time.time() - 60
        services.cache.get_last_synced = AsyncMock(return_value=last_synced_ts)

        fetch_fn = AsyncMock(return_value=[])

        await _ensure_synced(
            services=services,
            entity_type="variant",
            index_fields=MagicMock(),
            fetch_fn=fetch_fn,
            supports_incremental=True,
        )

        fetch_fn.assert_awaited_once()
        call_kwargs = fetch_fn.call_args[1]
        assert isinstance(call_kwargs["updated_at_min"], datetime)
        assert call_kwargs["updated_at_min"].tzinfo is UTC

    @pytest.mark.asyncio
    async def test_full_sync_passes_none(self, services):
        """When there's no last_synced, updated_at_min should be None."""
        services.cache.get_last_synced = AsyncMock(return_value=None)

        fetch_fn = AsyncMock(return_value=[])

        await _ensure_synced(
            services=services,
            entity_type="variant",
            index_fields=MagicMock(),
            fetch_fn=fetch_fn,
            supports_incremental=True,
        )

        call_kwargs = fetch_fn.call_args[1]
        assert call_kwargs["updated_at_min"] is None

    @pytest.mark.asyncio
    async def test_non_incremental_debounce(self, services):
        """Non-incremental entities should skip sync within debounce window."""
        services.cache.get_last_synced = AsyncMock(return_value=time.time() - 10)

        fetch_fn = AsyncMock(return_value=[])

        await _ensure_synced(
            services=services,
            entity_type="location",
            index_fields=MagicMock(),
            fetch_fn=fetch_fn,
            supports_incremental=False,
        )

        fetch_fn.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_non_incremental_expired_debounce(self, services):
        """Non-incremental entities should sync after debounce expires."""
        services.cache.get_last_synced = AsyncMock(return_value=time.time() - 600)

        fetch_fn = AsyncMock(return_value=[])

        await _ensure_synced(
            services=services,
            entity_type="location",
            index_fields=MagicMock(),
            fetch_fn=fetch_fn,
            supports_incremental=False,
        )

        fetch_fn.assert_awaited_once()
        call_kwargs = fetch_fn.call_args[1]
        assert call_kwargs["updated_at_min"] is None

    @pytest.mark.asyncio
    async def test_sync_stores_results_in_cache(self, services):
        """Fetched entities should be passed to cache.sync()."""
        services.cache.get_last_synced = AsyncMock(return_value=None)

        entities = [{"id": 1, "sku": "A"}, {"id": 2, "sku": "B"}]
        fetch_fn = AsyncMock(return_value=entities)
        index_fields = MagicMock()

        await _ensure_synced(
            services=services,
            entity_type="variant",
            index_fields=index_fields,
            fetch_fn=fetch_fn,
            supports_incremental=True,
        )

        services.cache.sync.assert_awaited_once_with("variant", entities, index_fields)


# ============================================================================
# ensure_variants_synced — integration with decorator chain
# ============================================================================


class TestEnsureVariantsSynced:
    """Test that ensure_variants_synced wires up correctly."""

    @pytest.mark.asyncio
    async def test_calls_fetch_variants_with_datetime(self):
        """End-to-end: ensure_variants_synced passes datetime to the API."""
        last_synced_ts = time.time() - 60

        services = MagicMock()
        services.cache = AsyncMock()
        services.cache.get_last_synced = AsyncMock(return_value=last_synced_ts)
        services.client = MagicMock()

        with patch(
            "katana_mcp.cache_sync._fetch_variants", new_callable=AsyncMock
        ) as mock_fetch:
            mock_fetch.return_value = []
            await ensure_variants_synced(services)

            call_kwargs = mock_fetch.call_args[1]
            assert isinstance(call_kwargs["updated_at_min"], datetime)
