"""Tests for the SQLite catalog cache with FTS5 search."""

import time

import pytest
import pytest_asyncio
from katana_mcp.cache import (
    PRODUCT_INDEX,
    VARIANT_INDEX,
    CatalogCache,
)


@pytest_asyncio.fixture
async def cache(tmp_path):
    """Create a temporary cache for testing."""
    db_path = tmp_path / "test_cache.db"
    c = CatalogCache(db_path=db_path)
    await c.open()
    yield c
    await c.close()


def _variant(
    id: int,
    sku: str,
    display_name: str = "",
    parent_name: str = "",
) -> dict:
    return {
        "id": id,
        "sku": sku,
        "display_name": display_name,
        "parent_name": parent_name,
        "updated_at": time.time(),
    }


def _product(id: int, name: str, category_name: str = "") -> dict:
    return {
        "id": id,
        "name": name,
        "category_name": category_name,
        "updated_at": time.time(),
    }


class TestCacheLifecycle:
    """Tests for opening, closing, and schema management."""

    @pytest.mark.asyncio
    async def test_open_creates_db_file(self, tmp_path):
        db_path = tmp_path / "subdir" / "cache.db"
        cache = CatalogCache(db_path=db_path)
        await cache.open()
        assert db_path.exists()
        await cache.close()

    @pytest.mark.asyncio
    async def test_close_and_reopen_preserves_data(self, tmp_path):
        db_path = tmp_path / "cache.db"

        # Write data
        cache = CatalogCache(db_path=db_path)
        await cache.open()
        await cache.sync("variant", [_variant(1, "SKU-001", "Widget")], VARIANT_INDEX)
        await cache.close()

        # Reopen and verify
        cache2 = CatalogCache(db_path=db_path)
        await cache2.open()
        result = await cache2.get_by_id("variant", 1)
        assert result is not None
        assert result["sku"] == "SKU-001"
        await cache2.close()

    @pytest.mark.asyncio
    async def test_runtime_error_when_not_open(self):
        cache = CatalogCache()
        with pytest.raises(RuntimeError, match="not open"):
            await cache.get_by_id("variant", 1)


class TestSync:
    """Tests for syncing entities into the cache."""

    @pytest.mark.asyncio
    async def test_sync_stores_entities(self, cache):
        variants = [
            _variant(1, "FOX-FORK-160", "Fox 36 Factory", "Fox Fork"),
            _variant(2, "SHIM-XT-M8100", "Shimano XT", "Shimano Derailleur"),
        ]
        await cache.sync("variant", variants, VARIANT_INDEX)

        result = await cache.get_by_id("variant", 1)
        assert result is not None
        assert result["sku"] == "FOX-FORK-160"

        result2 = await cache.get_by_id("variant", 2)
        assert result2 is not None
        assert result2["sku"] == "SHIM-XT-M8100"

    @pytest.mark.asyncio
    async def test_sync_upserts_on_conflict(self, cache):
        await cache.sync("variant", [_variant(1, "OLD-SKU", "Old Name")], VARIANT_INDEX)
        await cache.sync("variant", [_variant(1, "NEW-SKU", "New Name")], VARIANT_INDEX)

        result = await cache.get_by_id("variant", 1)
        assert result["sku"] == "NEW-SKU"

    @pytest.mark.asyncio
    async def test_sync_updates_metadata(self, cache):
        await cache.sync("variant", [_variant(1, "SKU-001")], VARIANT_INDEX)

        last_synced = await cache.get_last_synced("variant")
        assert last_synced is not None
        assert time.time() - last_synced < 5  # Within 5 seconds

    @pytest.mark.asyncio
    async def test_sync_empty_list_updates_last_synced(self, cache):
        """Empty sync still advances last_synced so we don't re-check immediately."""
        await cache.sync("variant", [], VARIANT_INDEX)
        assert await cache.get_last_synced("variant") is not None

    @pytest.mark.asyncio
    async def test_sync_without_index_fields(self, cache):
        """Entities can be stored without FTS indexing."""
        await cache.sync("factory", [{"id": 1, "name": "Main Factory"}])

        result = await cache.get_by_id("factory", 1)
        assert result is not None
        assert result["name"] == "Main Factory"


class TestFTS5Search:
    """Tests for FTS5 full-text search."""

    @pytest_asyncio.fixture(autouse=True)
    async def _populate(self, cache):
        variants = [
            _variant(1, "FOX-FORK-160", "Fox 36 Factory Fork", "Fox Suspension"),
            _variant(2, "FOX-SHOCK-200", "Fox Float X2 Shock", "Fox Suspension"),
            _variant(3, "SHIM-XT-M8100", "Shimano XT Derailleur", "Shimano Drivetrain"),
            _variant(4, "STEEL-SHEET-01", "Stainless Steel Sheet", "Raw Materials"),
        ]
        await cache.sync("variant", variants, VARIANT_INDEX)

    @pytest.mark.asyncio
    async def test_single_token_search(self, cache):
        results = await cache.search("variant", "fox")
        assert len(results) == 2
        skus = {r["sku"] for r in results}
        assert skus == {"FOX-FORK-160", "FOX-SHOCK-200"}

    @pytest.mark.asyncio
    async def test_multi_token_search_and_logic(self, cache):
        results = await cache.search("variant", "fox fork")
        assert len(results) == 1
        assert results[0]["sku"] == "FOX-FORK-160"

    @pytest.mark.asyncio
    async def test_prefix_matching(self, cache):
        results = await cache.search("variant", "shim")
        assert len(results) == 1
        assert results[0]["sku"] == "SHIM-XT-M8100"

    @pytest.mark.asyncio
    async def test_case_insensitive(self, cache):
        results = await cache.search("variant", "FOX")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_sku_search(self, cache):
        results = await cache.search("variant", "FOX-FORK")
        assert len(results) == 1
        assert results[0]["sku"] == "FOX-FORK-160"

    @pytest.mark.asyncio
    async def test_empty_query_returns_empty(self, cache):
        results = await cache.search("variant", "")
        assert results == []

    @pytest.mark.asyncio
    async def test_no_matches_returns_empty(self, cache):
        results = await cache.search("variant", "nonexistent")
        assert results == []

    @pytest.mark.asyncio
    async def test_respects_limit(self, cache):
        results = await cache.search("variant", "fox", limit=1)
        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_by_parent_name(self, cache):
        results = await cache.search("variant", "suspension")
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_search_scoped_to_entity_type(self, cache):
        """Products and variants don't mix in search results."""
        await cache.sync(
            "product",
            [_product(1, "Fox Fork Product", "Cycling")],
            PRODUCT_INDEX,
        )

        variant_results = await cache.search("variant", "fox")
        product_results = await cache.search("product", "fox")

        # Variants and products searched independently
        assert len(variant_results) == 2
        assert len(product_results) == 1


class TestArchivedFiltering:
    """Search must hide archived items by default and surface them on opt-in."""

    @pytest_asyncio.fixture(autouse=True)
    async def _populate(self, cache):
        # Mix of active and archived variants under the same parent name so
        # FTS5 returns multiple hits and we can verify the filter actually
        # narrows the set rather than coincidentally matching one.
        active = {
            "id": 1,
            "sku": "ACTIVE-001",
            "display_name": "Active Widget",
            "parent_name": "Widget Parent",
            "parent_archived_at": None,
            "updated_at": time.time(),
        }
        archived = {
            "id": 2,
            "sku": "ARCHIVED-001",
            "display_name": "Archived Widget",
            "parent_name": "Widget Parent",
            "parent_archived_at": "2024-01-01T00:00:00+00:00",
            "updated_at": time.time(),
        }
        await cache.sync("variant", [active, archived], VARIANT_INDEX)

    @pytest.mark.asyncio
    async def test_search_excludes_archived_by_default(self, cache):
        results = await cache.search("variant", "widget")
        assert {r["sku"] for r in results} == {"ACTIVE-001"}

    @pytest.mark.asyncio
    async def test_search_includes_archived_when_opted_in(self, cache):
        results = await cache.search("variant", "widget", include_archived=True)
        assert {r["sku"] for r in results} == {"ACTIVE-001", "ARCHIVED-001"}

    @pytest.mark.asyncio
    async def test_fuzzy_excludes_archived_by_default(self, cache):
        # "widgt" is a deletion typo — FTS5 prefix won't catch it, so this
        # exercises search_fuzzy specifically.
        results = await cache.search_fuzzy("variant", "widgt")
        assert {r["sku"] for r in results} == {"ACTIVE-001"}

    @pytest.mark.asyncio
    async def test_fuzzy_includes_archived_when_opted_in(self, cache):
        results = await cache.search_fuzzy("variant", "widgt", include_archived=True)
        assert {r["sku"] for r in results} == {"ACTIVE-001", "ARCHIVED-001"}


class TestFuzzySearch:
    """Tests for the difflib fuzzy fallback."""

    @pytest_asyncio.fixture(autouse=True)
    async def _populate(self, cache):
        variants = [
            _variant(1, "STEEL-001", "Stainless Steel Sheet", "Raw Materials"),
            _variant(2, "KNIFE-001", "Kitchen Knife", "Cutlery"),
        ]
        await cache.sync("variant", variants, VARIANT_INDEX)

    @pytest.mark.asyncio
    async def test_fts5_handles_prefix_typos(self, cache):
        # FTS5 prefix matching catches truncated words like "stainles" -> "stainless*"
        results = await cache.search("variant", "stainles")
        assert len(results) >= 1
        assert results[0]["sku"] == "STEEL-001"

    @pytest.mark.asyncio
    async def test_fuzzy_catches_misspelling(self, cache):
        # "knfe" is a transposition, not a prefix — FTS5 won't catch it
        assert await cache.search("variant", "knfe") == []
        fuzzy_results = await cache.search_fuzzy("variant", "knfe")

        # Fuzzy should find it even if FTS5 doesn't
        assert len(fuzzy_results) >= 1
        assert fuzzy_results[0]["sku"] == "KNIFE-001"


class TestDirectLookups:
    """Tests for ID and SKU lookups."""

    @pytest_asyncio.fixture(autouse=True)
    async def _populate(self, cache):
        await cache.sync(
            "variant",
            [_variant(1, "FOX-FORK-160", "Fox Fork", "Fox")],
            VARIANT_INDEX,
        )

    @pytest.mark.asyncio
    async def test_get_by_id(self, cache):
        result = await cache.get_by_id("variant", 1)
        assert result is not None
        assert result["sku"] == "FOX-FORK-160"

    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, cache):
        result = await cache.get_by_id("variant", 999)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_many_by_ids_returns_dict_keyed_by_id(self, cache):
        await cache.sync(
            "variant",
            [
                _variant(2, "SKU-002", "Item 2"),
                _variant(3, "SKU-003", "Item 3"),
            ],
            VARIANT_INDEX,
        )
        result = await cache.get_many_by_ids("variant", [1, 2, 3])
        assert set(result.keys()) == {1, 2, 3}
        assert result[1]["sku"] == "FOX-FORK-160"
        assert result[2]["sku"] == "SKU-002"
        assert result[3]["sku"] == "SKU-003"

    @pytest.mark.asyncio
    async def test_get_many_by_ids_omits_missing(self, cache):
        # Cache has only id=1 from the autouse fixture; 999 is absent.
        result = await cache.get_many_by_ids("variant", [1, 999])
        assert set(result.keys()) == {1}

    @pytest.mark.asyncio
    async def test_get_many_by_ids_empty_input_no_query(self, cache):
        # Empty input must short-circuit — calling with [] would otherwise
        # build an `IN ()` clause that's a SQLite syntax error.
        result = await cache.get_many_by_ids("variant", [])
        assert result == {}

    @pytest.mark.asyncio
    async def test_get_many_by_ids_dedups_input(self, cache):
        # Caller may pass duplicates (e.g., when one variant blocks several
        # MOs); dedup-then-query keeps the IN-clause minimal.
        result = await cache.get_many_by_ids("variant", [1, 1, 1])
        assert set(result.keys()) == {1}

    @pytest.mark.asyncio
    async def test_get_by_sku(self, cache):
        result = await cache.get_by_sku("FOX-FORK-160")
        assert result is not None
        assert result["id"] == 1

    @pytest.mark.asyncio
    async def test_get_by_sku_case_insensitive(self, cache):
        result = await cache.get_by_sku("fox-fork-160")
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_sku_not_found(self, cache):
        result = await cache.get_by_sku("NONEXISTENT")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_all(self, cache):
        await cache.sync(
            "variant",
            [_variant(2, "SKU-002", "Item 2")],
            VARIANT_INDEX,
        )
        all_items = await cache.get_all("variant")
        assert len(all_items) == 2


class TestInvalidation:
    """Tests for cache invalidation."""

    @pytest.mark.asyncio
    async def test_invalidate_single_entity(self, cache):
        await cache.sync(
            "variant",
            [_variant(1, "SKU-001"), _variant(2, "SKU-002")],
            VARIANT_INDEX,
        )

        await cache.invalidate("variant", entity_id=1)

        assert await cache.get_by_id("variant", 1) is None
        assert await cache.get_by_id("variant", 2) is not None

    @pytest.mark.asyncio
    async def test_invalidate_all_of_type(self, cache):
        await cache.sync(
            "variant",
            [_variant(1, "SKU-001"), _variant(2, "SKU-002")],
            VARIANT_INDEX,
        )

        await cache.invalidate("variant")

        assert await cache.get_by_id("variant", 1) is None
        assert await cache.get_by_id("variant", 2) is None
        assert await cache.get_last_synced("variant") is None

    @pytest.mark.asyncio
    async def test_mark_dirty_clears_sync_metadata(self, cache):
        await cache.sync("variant", [_variant(1, "SKU-001")], VARIANT_INDEX)
        assert await cache.get_last_synced("variant") is not None

        await cache.mark_dirty("variant")
        assert await cache.get_last_synced("variant") is None

        # Data still exists — just needs resync
        assert await cache.get_by_id("variant", 1) is not None

    @pytest.mark.asyncio
    async def test_clear_removes_everything(self, cache):
        await cache.sync("variant", [_variant(1, "SKU-001")], VARIANT_INDEX)
        await cache.sync("product", [_product(1, "Widget")], PRODUCT_INDEX)

        await cache.clear()

        assert await cache.get_by_id("variant", 1) is None
        assert await cache.get_by_id("product", 1) is None


class TestStats:
    """Tests for cache statistics."""

    @pytest.mark.asyncio
    async def test_stats_empty_cache(self, cache):
        stats = await cache.stats()
        assert stats["entities"] == {}

    @pytest.mark.asyncio
    async def test_stats_with_data(self, cache):
        await cache.sync("variant", [_variant(1, "SKU-001")], VARIANT_INDEX)

        stats = await cache.stats()
        assert "variant" in stats["entities"]
        assert stats["entities"]["variant"]["count"] == 1
        assert stats["entities"]["variant"]["age_seconds"] < 5
