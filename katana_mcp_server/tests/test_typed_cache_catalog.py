"""Tests for the catalog tier of the typed cache (#472 Phase B).

Coverage targets the acceptance criteria from the Phase B plan:

- Each ``Cached*`` catalog entity round-trips through sync.
- Variant cache-only fields (``parent_archived_at``, ``display_name``,
  ``parent_name``, ``supplier_item_codes_text``) populate correctly
  from the extended ``product_or_material`` payload.
- ``CatalogQueries`` adapter:
  - ``get_by_id`` defaults filter archived/deleted; explicit flags
    surface them.
  - ``get_by_sku`` uses NOCASE collation.
  - ``smart_search`` handles SKU-shaped queries (``00.4021.018.003``),
    UPC queries on ``registered_barcode``, multi-token queries
    (``"kitchen knife"``), and falls through to fuzzy on FTS5 syntax
    errors.
- ``_validate_dependency_graph`` raises on cycles and unknown
  references.
- Cross-EntitySpec FK ordering: parents sync before children on cold
  start.
"""

from __future__ import annotations

import contextlib
from datetime import UTC, datetime
from typing import Any, cast
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from katana_mcp.typed_cache import (
    EntitySpec,
    ensure_customers_synced,
    ensure_factory_synced,
    ensure_locations_synced,
    ensure_materials_synced,
    ensure_products_synced,
    ensure_services_synced,
    ensure_suppliers_synced,
    ensure_tax_rates_synced,
    ensure_variants_synced,
)
from katana_mcp.typed_cache.sync import _validate_dependency_graph

from katana_public_api_client.models import (
    Customer as AttrsCustomer,
    Factory as AttrsFactory,
    LocationType0 as AttrsLocation,
    Material as AttrsMaterial,
    Product as AttrsProduct,
    Service as AttrsService,
    Supplier as AttrsSupplier,
    TaxRate as AttrsTaxRate,
    VariantResponse as AttrsVariantResponse,
)
from katana_public_api_client.models_pydantic._generated import (
    CachedCustomer,
    CachedFactory,
    CachedLocation,
    CachedMaterial,
    CachedProduct,
    CachedService,
    CachedSupplier,
    CachedTaxRate,
    CachedVariant,
    InventoryItemType,
)


def _list_response(data: list) -> MagicMock:
    """Stub a 200 list response with a ``data=[...]`` parsed body."""
    parsed = MagicMock()
    parsed.data = data
    response = MagicMock()
    response.status_code = 200
    response.parsed = parsed
    return response


def _single_response(item: object) -> MagicMock:
    """Stub a 200 single-record response (e.g., ``GET /factory``).

    Single-record endpoints return the entity directly via
    ``response.parsed``, not nested under ``data``. Mirrors what
    ``unwrap()`` consumes.
    """
    response = MagicMock()
    response.status_code = 200
    response.parsed = item
    return response


@contextlib.contextmanager
def _stub_endpoint(target: str, return_value: MagicMock):
    """Patch one ``katana_mcp.typed_cache.sync.<target>.asyncio_detailed`` call."""
    with patch(
        f"katana_mcp.typed_cache.sync.{target}.asyncio_detailed",
        new=AsyncMock(return_value=return_value),
    ):
        yield


class TestEntitySpecValidation:
    """Dependency-graph validation runs at engine.open()."""

    def test_unknown_dependency_raises(self):
        """A spec referencing an unknown ``entity_key`` is a config bug."""
        # ``MagicMock`` doesn't statically conform to ``_FromAttrs`` — these
        # specs never actually invoke ``from_attrs`` because the validator
        # raises before sync runs, so the mock is fine at runtime.
        spec = EntitySpec(
            entity_key="orphan",
            api_fn=MagicMock(),
            cache_cls=CachedProduct,
            pydantic_cls=cast(Any, MagicMock()),
            depends_on=("nonexistent",),
        )
        with pytest.raises(ValueError, match="depends_on='nonexistent'"):
            _validate_dependency_graph([spec])

    def test_dependency_cycle_raises(self):
        """Cyclic dependencies are caught at validation time."""
        a = EntitySpec(
            entity_key="a",
            api_fn=MagicMock(),
            cache_cls=CachedProduct,
            pydantic_cls=cast(Any, MagicMock()),
            depends_on=("b",),
        )
        b = EntitySpec(
            entity_key="b",
            api_fn=MagicMock(),
            cache_cls=CachedMaterial,
            pydantic_cls=cast(Any, MagicMock()),
            depends_on=("a",),
        )
        with pytest.raises(ValueError, match="cycle"):
            _validate_dependency_graph([a, b])


class TestCatalogSync:
    """Cold-start sync round-trip for each catalog entity."""

    @pytest.mark.asyncio
    async def test_product_round_trips(self, typed_cache_engine):
        attrs = AttrsProduct.from_dict(
            {
                "id": 101,
                "name": "Kitchen Knife",
                "type": "product",
                "category_name": "Cutlery",
            }
        )
        with _stub_endpoint("get_all_products", _list_response([attrs])):
            await ensure_products_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            cached = await session.get(CachedProduct, 101)
        assert cached is not None
        assert cached.name == "Kitchen Knife"
        assert cached.category_name == "Cutlery"

    @pytest.mark.asyncio
    async def test_material_round_trips(self, typed_cache_engine):
        attrs = AttrsMaterial.from_dict(
            {"id": 5001, "name": "Stainless Steel", "type": "material"}
        )
        with _stub_endpoint("get_all_materials", _list_response([attrs])):
            await ensure_materials_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            cached = await session.get(CachedMaterial, 5001)
        assert cached is not None
        assert cached.name == "Stainless Steel"

    @pytest.mark.asyncio
    async def test_service_round_trips(self, typed_cache_engine):
        attrs = AttrsService.from_dict({"id": 7001, "name": "Sharpening"})
        with _stub_endpoint("get_all_services", _list_response([attrs])):
            await ensure_services_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            cached = await session.get(CachedService, 7001)
        assert cached is not None
        assert cached.name == "Sharpening"

    @pytest.mark.asyncio
    async def test_customer_round_trips(self, typed_cache_engine):
        attrs = AttrsCustomer.from_dict(
            {"id": 9001, "name": "Jane Doe", "email": "jane.doe@example.com"}
        )
        with _stub_endpoint("get_all_customers", _list_response([attrs])):
            await ensure_customers_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            cached = await session.get(CachedCustomer, 9001)
        assert cached is not None
        assert cached.name == "Jane Doe"
        assert cached.email == "jane.doe@example.com"

    @pytest.mark.asyncio
    async def test_supplier_round_trips(self, typed_cache_engine):
        attrs = AttrsSupplier.from_dict({"id": 8001, "name": "Acme Steel Co"})
        with _stub_endpoint("get_all_suppliers", _list_response([attrs])):
            await ensure_suppliers_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            cached = await session.get(CachedSupplier, 8001)
        assert cached is not None
        assert cached.name == "Acme Steel Co"

    @pytest.mark.asyncio
    async def test_location_round_trips(self, typed_cache_engine):
        attrs = AttrsLocation.from_dict({"id": 1, "name": "Main Warehouse"})
        with _stub_endpoint("get_all_locations", _list_response([attrs])):
            await ensure_locations_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            cached = await session.get(CachedLocation, 1)
        assert cached is not None
        assert cached.name == "Main Warehouse"

    @pytest.mark.asyncio
    async def test_tax_rate_round_trips(self, typed_cache_engine):
        attrs = AttrsTaxRate.from_dict(
            {"id": 1, "name": "VAT 20%", "rate": 20.0, "is_default_sales": True}
        )
        with _stub_endpoint("get_all_tax_rates", _list_response([attrs])):
            await ensure_tax_rates_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            cached = await session.get(CachedTaxRate, 1)
        assert cached is not None
        assert cached.rate == 20.0

    @pytest.mark.asyncio
    async def test_factory_round_trips(self, typed_cache_engine):
        """Factory uses ``single_record=True`` — pins the bare-object fetch path."""
        attrs = AttrsFactory.from_dict(
            {
                "id": 1,
                "name": "Acme Mfg",
                "display_name": "Acme Mfg Co",
                "base_currency_code": "USD",
            }
        )
        with _stub_endpoint("get_factory", _single_response(attrs)):
            await ensure_factory_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            cached = await session.get(CachedFactory, 1)
        assert cached is not None
        assert cached.name == "Acme Mfg"
        assert cached.base_currency_code == "USD"


class TestVariantPostprocess:
    """Variant cache-only fields populate from the extended payload."""

    @pytest.mark.asyncio
    async def test_parent_archived_at_lifted(self, typed_cache_engine):
        """When the parent product is archived, the variant cache row reflects it."""
        # Sync the parent product first so the registry has a slot for
        # the variant's ``product_or_material`` reference. The test
        # actually exercises the postprocess hook, not the FK.
        archived_dt = datetime(2025, 1, 15, tzinfo=UTC)
        product_attrs = AttrsProduct.from_dict(
            {
                "id": 101,
                "name": "Kitchen Knife",
                "type": "product",
                "archived_at": archived_dt.isoformat(),
            }
        )
        with _stub_endpoint("get_all_products", _list_response([product_attrs])):
            await ensure_products_synced(MagicMock(), typed_cache_engine)

        # Now sync a variant whose extended payload exposes the archived parent.
        variant_attrs = AttrsVariantResponse.from_dict(
            {
                "id": 3001,
                "sku": "KNF-PRO-8PC",
                "product_id": 101,
                "type": "product",
                "config_attributes": [
                    {"config_name": "Piece Count", "config_value": "8-piece"}
                ],
                "supplier_item_codes": ["SUPP-KNF-001"],
                "product_or_material": {
                    "id": 101,
                    "name": "Kitchen Knife",
                    "type": "product",
                    "archived_at": archived_dt.isoformat(),
                },
            }
        )
        # Stub product/material as empty for the variant sync's
        # ensure_*_synced fan-out (the helper re-syncs parents).
        empty = _list_response([])
        with (
            _stub_endpoint("get_all_products", empty),
            _stub_endpoint("get_all_materials", empty),
            _stub_endpoint("get_all_variants", _list_response([variant_attrs])),
        ):
            await ensure_variants_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            cached = await session.get(CachedVariant, 3001)
        assert cached is not None
        assert cached.parent_archived_at is not None
        assert cached.parent_name == "Kitchen Knife"
        assert cached.display_name == "Kitchen Knife / 8-piece"
        assert cached.supplier_item_codes_text == "SUPP-KNF-001"

    @pytest.mark.asyncio
    async def test_display_name_falls_back_to_sku(self, typed_cache_engine):
        """Defensive fallback when parent name is empty — mirrors legacy semantics."""
        variant_attrs = AttrsVariantResponse.from_dict(
            {
                "id": 3002,
                "sku": "FALLBACK-SKU",
                "type": "product",
            }
        )
        empty = _list_response([])
        with (
            _stub_endpoint("get_all_products", empty),
            _stub_endpoint("get_all_materials", empty),
            _stub_endpoint("get_all_variants", _list_response([variant_attrs])),
        ):
            await ensure_variants_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            cached = await session.get(CachedVariant, 3002)
        assert cached is not None
        # No parent name → SKU fallback (mirrors legacy
        # ``_variant_to_cache_dict``).
        assert cached.display_name == "FALLBACK-SKU"
        assert cached.parent_archived_at is None


class TestCatalogQueriesGetters:
    """Direct lookup methods on the CatalogQueries adapter."""

    @pytest.mark.asyncio
    async def test_get_by_id_filters_archived_by_default(self, typed_cache_engine):
        """A row with ``archived_at`` set is hidden unless ``include_archived=True``."""
        archived_dt = datetime(2025, 1, 15, tzinfo=UTC)
        async with typed_cache_engine.session() as session:
            session.add(
                CachedProduct(
                    id=42,
                    name="Archived Product",
                    type=InventoryItemType.product,
                    archived_at=archived_dt,
                )
            )
            await session.commit()

        # Default: archived rows hidden.
        result = await typed_cache_engine.catalog.get_by_id(CachedProduct, 42)
        assert result is None

        # Opt-in: archived rows surfaced.
        result = await typed_cache_engine.catalog.get_by_id(
            CachedProduct, 42, include_archived=True
        )
        assert result is not None
        assert result.id == 42

    @pytest.mark.asyncio
    async def test_get_by_id_filters_deleted_by_default(self, typed_cache_engine):
        """A row with ``deleted_at`` set is hidden unless ``include_deleted=True``."""
        deleted_dt = datetime(2025, 2, 1, tzinfo=UTC)
        async with typed_cache_engine.session() as session:
            session.add(
                CachedCustomer(id=99, name="Deleted Customer", deleted_at=deleted_dt)
            )
            await session.commit()

        result = await typed_cache_engine.catalog.get_by_id(CachedCustomer, 99)
        assert result is None

        result = await typed_cache_engine.catalog.get_by_id(
            CachedCustomer, 99, include_deleted=True
        )
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_by_sku_is_case_insensitive(self, typed_cache_engine):
        """NOCASE collation lets callers pass any-case SKUs."""
        async with typed_cache_engine.session() as session:
            session.add(CachedVariant(id=1, sku="KNF-PRO-8PC"))
            await session.commit()

        result_upper = await typed_cache_engine.catalog.get_by_sku("KNF-PRO-8PC")
        result_lower = await typed_cache_engine.catalog.get_by_sku("knf-pro-8pc")
        result_mixed = await typed_cache_engine.catalog.get_by_sku("Knf-Pro-8Pc")
        assert result_upper is not None
        assert result_lower is not None
        assert result_mixed is not None
        assert result_upper.id == result_lower.id == result_mixed.id == 1

    @pytest.mark.asyncio
    async def test_get_many_by_ids_dedupes_and_returns_dict(self, typed_cache_engine):
        """Duplicates collapse; the result is keyed by id for hits only."""
        async with typed_cache_engine.session() as session:
            session.add(CachedProduct(id=1, name="P1", type=InventoryItemType.product))
            session.add(CachedProduct(id=2, name="P2", type=InventoryItemType.product))
            await session.commit()

        result = await typed_cache_engine.catalog.get_many_by_ids(
            CachedProduct, [1, 2, 1, 999]
        )
        assert set(result.keys()) == {1, 2}
        assert result[1].name == "P1"

    @pytest.mark.asyncio
    async def test_get_all_filters_archived(self, typed_cache_engine):
        """``get_all`` honors the same archive filter as the lookup methods."""
        archived_dt = datetime(2025, 1, 15, tzinfo=UTC)
        async with typed_cache_engine.session() as session:
            session.add(
                CachedProduct(
                    id=1, name="Active Product", type=InventoryItemType.product
                )
            )
            session.add(
                CachedProduct(
                    id=2,
                    name="Archived Product",
                    type=InventoryItemType.product,
                    archived_at=archived_dt,
                )
            )
            await session.commit()

        active = await typed_cache_engine.catalog.get_all(CachedProduct)
        all_rows = await typed_cache_engine.catalog.get_all(
            CachedProduct, include_archived=True
        )
        assert {p.id for p in active} == {1}
        assert {p.id for p in all_rows} == {1, 2}


class TestCatalogQueriesSearch:
    """Smart_search + fuzzy fallback semantics."""

    @pytest.mark.asyncio
    async def test_smart_search_sku_shaped_query(self, typed_cache_engine):
        """SKU-shaped query (``00.4021.018.003``) tokenizes via ``\\W+``.

        The legacy ``CatalogCache.smart_search`` used ``query.split()``
        which kept the ``.`` separators, producing one super-token that
        FTS5 stripped to nothing — a real user repro from #471.
        """
        async with typed_cache_engine.session() as session:
            session.add(
                CachedVariant(
                    id=1,
                    sku="ZSF-V2",
                    supplier_item_codes_text="00 4021 018 003",
                    display_name="ZSF V2 / Black",
                )
            )
            await session.commit()

        results = await typed_cache_engine.catalog.smart_search(
            CachedVariant, "00.4021.018.003"
        )
        assert len(results) == 1
        assert results[0].id == 1

    @pytest.mark.asyncio
    async def test_smart_search_multi_token(self, typed_cache_engine):
        """Multi-token queries still match across columns."""
        async with typed_cache_engine.session() as session:
            session.add(
                CachedVariant(
                    id=2,
                    sku="KNF-PRO-8PC",
                    display_name="Kitchen Knife / 8-piece",
                    parent_name="Kitchen Knife",
                )
            )
            await session.commit()

        results = await typed_cache_engine.catalog.smart_search(
            CachedVariant, "kitchen knife"
        )
        assert len(results) == 1
        assert results[0].id == 2

    @pytest.mark.asyncio
    async def test_smart_search_upc_query(self, typed_cache_engine):
        """UPC search hits ``registered_barcode`` — covers #471/#473 acceptance."""
        async with typed_cache_engine.session() as session:
            session.add(
                CachedVariant(
                    id=3,
                    sku="BARCODE-VARIANT",
                    registered_barcode="710845916762",
                )
            )
            await session.commit()

        results = await typed_cache_engine.catalog.smart_search(
            CachedVariant, "710845916762"
        )
        assert len(results) == 1
        assert results[0].id == 3

    @pytest.mark.asyncio
    async def test_smart_search_falls_through_on_syntax_error(self, typed_cache_engine):
        """FTS5 ``OperationalError`` falls through to fuzzy.

        The tokenizer strips punctuation (``re.split(\\W+, ...)``), so
        user-supplied punctuation like ``stainles(`` can't actually
        trigger an FTS5 syntax error in production — the malformed
        token never reaches the FTS5 grammar. To exercise the
        fall-through branch directly, patch the FTS-execution path to
        raise the same ``OperationalError`` SQLite would have raised
        for a syntactically invalid match expression. Fuzzy fallback
        should still rescue the row by approximate match on
        ``display_name`` / ``parent_name``.

        Legacy cache silently returned an empty list — a real bug
        since the user got *zero* results for a query that fuzzy
        could have rescued.
        """
        from sqlalchemy.exc import OperationalError

        async with typed_cache_engine.session() as session:
            session.add(
                CachedVariant(
                    id=4,
                    sku="STAINLES-V1",
                    display_name="Stainless Steel V1",
                    parent_name="Stainless Steel",
                )
            )
            await session.commit()

        # Stub ``exec_driver_sql`` to raise the FTS5 syntax error
        # SQLite would emit for an invalid match expression. Wrap the
        # original so non-FTS calls (the fuzzy path's own SELECTs) keep
        # working — only the first call (the FTS5 query in
        # ``smart_search``) raises.
        from sqlalchemy.ext.asyncio import AsyncConnection

        original = AsyncConnection.exec_driver_sql
        call_count = {"n": 0}

        async def _raise_first(self, statement, parameters=None, *a, **kw):
            call_count["n"] += 1
            if call_count["n"] == 1 and "MATCH" in statement:
                msg = 'fts5: syntax error near "("'
                raise OperationalError(statement, parameters, Exception(msg))
            return await original(self, statement, parameters, *a, **kw)

        with patch.object(AsyncConnection, "exec_driver_sql", _raise_first):
            results = await typed_cache_engine.catalog.smart_search(
                CachedVariant, "stainles"
            )
        # Fuzzy fallback should rescue the row by approximate match.
        assert any(r.id == 4 for r in results)
        # Belt-and-suspenders: confirm the patched path actually fired.
        assert call_count["n"] >= 1

    @pytest.mark.asyncio
    async def test_smart_search_propagates_non_syntax_operational_error(
        self, typed_cache_engine
    ):
        """Operational errors (locked DB, missing table) propagate — no silent fuzzy.

        The fall-through is narrowed to FTS5 syntax errors only. A
        generic ``OperationalError`` (e.g. ``database is locked``,
        ``no such table: variant_fts``) signals a real problem; masking
        it behind a fuzzy fallback would leave the operator without
        any signal that the FTS sidecar broke.
        """
        from sqlalchemy.exc import OperationalError
        from sqlalchemy.ext.asyncio import AsyncConnection

        async with typed_cache_engine.session() as session:
            session.add(
                CachedVariant(
                    id=99,
                    sku="OPERATIONAL-ERR",
                    display_name="Should Not Surface",
                )
            )
            await session.commit()

        original = AsyncConnection.exec_driver_sql

        async def _raise_locked(self, statement, parameters=None, *a, **kw):
            if "MATCH" in statement:
                msg = "database is locked"
                raise OperationalError(statement, parameters, Exception(msg))
            return await original(self, statement, parameters, *a, **kw)

        with (
            patch.object(AsyncConnection, "exec_driver_sql", _raise_locked),
            pytest.raises(OperationalError),
        ):
            await typed_cache_engine.catalog.smart_search(CachedVariant, "operational")

    @pytest.mark.asyncio
    async def test_smart_search_empty_query_returns_empty(self, typed_cache_engine):
        results = await typed_cache_engine.catalog.smart_search(CachedVariant, "")
        assert results == []
        results = await typed_cache_engine.catalog.smart_search(CachedVariant, "   ")
        assert results == []

    @pytest.mark.asyncio
    async def test_smart_search_archived_filter(self, typed_cache_engine):
        """Archived-parent variants hide by default; surface with explicit flag."""
        archived_dt = datetime(2025, 1, 15, tzinfo=UTC)
        async with typed_cache_engine.session() as session:
            session.add(
                CachedVariant(
                    id=5,
                    sku="ARCHIVED-V1",
                    display_name="Archived Knife",
                    parent_name="Archived Knife",
                    parent_archived_at=archived_dt,
                )
            )
            await session.commit()

        # Default: archived parent hidden.
        default_results = await typed_cache_engine.catalog.smart_search(
            CachedVariant, "archived"
        )
        assert default_results == []

        # Opt-in: surface archived rows.
        opted_in = await typed_cache_engine.catalog.smart_search(
            CachedVariant, "archived", include_archived=True
        )
        assert any(r.id == 5 for r in opted_in)


class TestCrossEntitySpecOrdering:
    """Cross-EntitySpec FK ordering — Phase B's ``depends_on`` mechanism."""

    @pytest.mark.asyncio
    async def test_ensure_variants_synced_pulls_parents_first(self, typed_cache_engine):
        """Cold-start sync materializes Product/Material rows before Variant inserts.

        ``ensure_variants_synced`` syncs Product → Material → Variant in
        order. The variant's ``attrs_postprocess`` then reads the parent's
        ``archived_at`` from the extended payload and stores it on the
        cache row. End-state: parent rows in cache, variant in cache,
        ``parent_archived_at`` populated for any archived parent.
        """
        product_attrs = AttrsProduct.from_dict(
            {"id": 101, "name": "Knife", "type": "product"}
        )
        material_attrs = AttrsMaterial.from_dict(
            {"id": 5001, "name": "Steel", "type": "material"}
        )
        variant_for_product = AttrsVariantResponse.from_dict(
            {
                "id": 3001,
                "sku": "KNF-V1",
                "product_id": 101,
                "type": "product",
                "product_or_material": {
                    "id": 101,
                    "name": "Knife",
                    "type": "product",
                },
            }
        )
        variant_for_material = AttrsVariantResponse.from_dict(
            {
                "id": 3002,
                "sku": "STL-V1",
                "material_id": 5001,
                "type": "material",
                "product_or_material": {
                    "id": 5001,
                    "name": "Steel",
                    "type": "material",
                },
            }
        )

        with (
            _stub_endpoint("get_all_products", _list_response([product_attrs])),
            _stub_endpoint("get_all_materials", _list_response([material_attrs])),
            _stub_endpoint(
                "get_all_variants",
                _list_response([variant_for_product, variant_for_material]),
            ),
        ):
            await ensure_variants_synced(MagicMock(), typed_cache_engine)

        async with typed_cache_engine.session() as session:
            assert await session.get(CachedProduct, 101) is not None
            assert await session.get(CachedMaterial, 5001) is not None
            v_product = await session.get(CachedVariant, 3001)
            v_material = await session.get(CachedVariant, 3002)
        assert v_product is not None
        assert v_material is not None
        assert v_product.parent_name == "Knife"
        assert v_material.parent_name == "Steel"

    @pytest.mark.asyncio
    async def test_ensure_variants_synced_populates_fts_index(self, typed_cache_engine):
        """The bulk-upsert path keeps the FTS5 sidecar in sync.

        ``_sync_one_locked`` writes via ``sqlalchemy.dialects.sqlite.insert``
        (Core ``INSERT ... ON CONFLICT``), which bypasses SQLAlchemy
        ORM mapper events. The FTS5 sidecar relies on **SQLite triggers**
        (registered by ``_create_fts_tables_ddl`` on engine.open()) that
        fire for every write mode — ORM, Core, raw SQL — so the sync
        path keeps the inverted index in lock-step without an explicit
        reindex pass. Pre-#646 this surface was wired through ORM-only
        mapper-event listeners and ``smart_search`` would silently
        return empty until the next engine reopen rebuilt the index;
        this test pins the contract end-to-end: sync via the public
        ``ensure_variants_synced`` entrypoint, then assert
        ``smart_search`` against an FTS-only token (``KNF-V1-FTSTEST``)
        finds the synced rows.
        """
        product_attrs = AttrsProduct.from_dict(
            {"id": 201, "name": "Chef Knife", "type": "product"}
        )
        material_attrs = AttrsMaterial.from_dict(
            {"id": 6001, "name": "Stainless Steel", "type": "material"}
        )
        variant_for_product = AttrsVariantResponse.from_dict(
            {
                "id": 4001,
                "sku": "KNF-V1-FTSTEST",
                "product_id": 201,
                "type": "product",
                "product_or_material": {
                    "id": 201,
                    "name": "Chef Knife",
                    "type": "product",
                },
            }
        )
        variant_for_material = AttrsVariantResponse.from_dict(
            {
                "id": 4002,
                "sku": "STL-V1-FTSTEST",
                "material_id": 6001,
                "type": "material",
                "product_or_material": {
                    "id": 6001,
                    "name": "Stainless Steel",
                    "type": "material",
                },
            }
        )

        with (
            _stub_endpoint("get_all_products", _list_response([product_attrs])),
            _stub_endpoint("get_all_materials", _list_response([material_attrs])),
            _stub_endpoint(
                "get_all_variants",
                _list_response([variant_for_product, variant_for_material]),
            ),
        ):
            await ensure_variants_synced(MagicMock(), typed_cache_engine)

        # FTS-backed search should find the variant by SKU prefix even
        # though the row was written via Core upsert (where ORM mapper
        # events would not fire). The SQLite trigger trio fires for
        # Core writes, so this assertion catches a regression where
        # the trigger DDL stops being emitted on engine.open().
        variant_results = await typed_cache_engine.catalog.smart_search(
            CachedVariant, "KNF-V1-FTSTEST"
        )
        assert any(r.id == 4001 for r in variant_results), (
            "FTS5 sidecar not populated for variant inserted via "
            "_bulk_upsert — trigger trio likely dropped from "
            "_create_fts_tables_ddl"
        )

        # Parents (product, material) also ride the bulk-upsert path —
        # exercise their FTS sidecars too so a regression on either
        # surface is caught.
        product_results = await typed_cache_engine.catalog.smart_search(
            CachedProduct, "Chef Knife"
        )
        assert any(r.id == 201 for r in product_results)
        material_results = await typed_cache_engine.catalog.smart_search(
            CachedMaterial, "Stainless"
        )
        assert any(r.id == 6001 for r in material_results)


class TestFTSSchemaValidation:
    """FTS column declarations stay in sync with the cache table schema."""

    @pytest.mark.asyncio
    async def test_engine_open_creates_per_entity_fts_tables(self, typed_cache_engine):
        """Phase B's per-entity FTS5 sidecar emits ``<entity>_fts`` tables.

        Lookup-only entities (Location, TaxRate, Operator, Factory,
        AdditionalCost) skip FTS — they're below the minimum-content
        threshold for FTS5 to add value.
        """
        from sqlalchemy import text

        async with typed_cache_engine.session() as session:
            conn = await session.connection()
            result = await conn.execute(
                text(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name LIKE '%_fts'"
                )
            )
            tables = {row[0] for row in result.fetchall()}

        # The 6 entities with ``__fts_columns__`` — variants, products,
        # materials, services, customers, suppliers — all get tables.
        expected = {
            "variant_fts",
            "product_fts",
            "material_fts",
            "service_fts",
            "customer_fts",
            "supplier_fts",
        }
        assert expected.issubset(tables)


class TestNoDoubleOpenInteraction:
    """Reopening an engine should be safe and FTS rows stay consistent."""

    @pytest.mark.asyncio
    async def test_fts_index_consistent_after_insert(self, typed_cache_engine):
        """ORM ``session.add`` populates the FTS sidecar via the ``ai`` trigger."""
        async with typed_cache_engine.session() as session:
            session.add(
                CachedVariant(
                    id=10,
                    sku="TRIGGER-TEST",
                    display_name="Trigger Test Item",
                )
            )
            await session.commit()

        # Round-trip: can we find it via the FTS-backed smart_search?
        results = await typed_cache_engine.catalog.smart_search(
            CachedVariant, "trigger"
        )
        assert any(r.id == 10 for r in results)


class TestNonFTSEntities:
    """smart_search degrades to fuzzy for entities without ``__fts_columns__``."""

    @pytest.mark.asyncio
    async def test_smart_search_on_taxrate_falls_back_to_fuzzy(
        self, typed_cache_engine
    ):
        """TaxRate has no FTS sidecar; smart_search returns fuzzy results."""
        async with typed_cache_engine.session() as session:
            session.add(CachedTaxRate(id=1, name="VAT 20%", rate=20.0))
            await session.commit()

        results = await typed_cache_engine.catalog.smart_search(CachedTaxRate, "VAT")
        assert any(r.id == 1 for r in results)
