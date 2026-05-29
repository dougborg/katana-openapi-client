"""Regression tests for the generate_pydantic_models.py post-processors.

The post-processors transform datamodel-codegen output into the final
``Cached*`` SQLModel classes. These tests pin the rewrite behavior so a
future codegen tooling change that subtly shifts the generated text
pattern doesn't silently disable the transform.

Loads ``scripts/generate_pydantic_models.py`` via ``importlib`` so the
test doesn't need ``sys.path`` manipulation.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

_SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "generate_pydantic_models.py"
)


def _load_module() -> ModuleType:
    import sys

    name = "generate_pydantic_under_test"
    spec = importlib.util.spec_from_file_location(name, _SCRIPT_PATH)
    if spec is None or spec.loader is None:
        msg = f"Could not load module from {_SCRIPT_PATH}"
        raise RuntimeError(msg)
    module = importlib.util.module_from_spec(spec)
    # Register in ``sys.modules`` so ``@dataclass`` (and any other
    # decorator that looks up ``sys.modules[cls.__module__]``) can find
    # the loader-attached classes during class-body execution.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen() -> ModuleType:
    return _load_module()


def _make_cls(gen: ModuleType, name: str, body: str) -> Any:
    """Build a ClassInfo with the given body wrapped in a class header."""
    source = f"class {name}(DeletableEntity, table=True):\n{body}"
    return gen.ClassInfo(
        name=name,
        source=source,
        bases=["DeletableEntity"],
        line_start=1,
        line_end=source.count("\n") + 1,
    )


# ─── wrap_cache_fields_in_mapped ────────────────────────────────────────


def test_wrap_simple_scalar(gen: ModuleType) -> None:
    """Bare scalar field → ``Annotated[Mapped[int], Field(...)]``."""
    # ``CACHE_TABLES`` is a dict keyed by un-prefixed entity name; pick
    # any real cache class so ``_cached_name`` resolves it for the pass.
    name = next(iter(gen.CACHE_TABLES))
    cached_name = gen._cached_name(name)
    cls = _make_cls(
        gen,
        cached_name,
        '    id: Annotated[int, SQLField(primary_key=True, description="x")]\n',
    )
    [out] = gen.wrap_cache_fields_in_mapped([cls])
    assert "Annotated[Mapped[int], SQLField(" in out.source


def test_wrap_union(gen: ModuleType) -> None:
    """Union (``T | None``) types are wrapped intact."""
    name = next(iter(gen.CACHE_TABLES))
    cached_name = gen._cached_name(name)
    cls = _make_cls(
        gen,
        cached_name,
        '    deleted_at: Annotated[datetime | None, Field(description="x")] = None\n',
    )
    [out] = gen.wrap_cache_fields_in_mapped([cls])
    assert "Mapped[datetime | None]" in out.source


def test_wrap_single_bracket_generic(gen: ModuleType) -> None:
    """Single-level generic (``list["X"]``) is wrapped correctly."""
    name = next(iter(gen.CACHE_TABLES))
    cached_name = gen._cached_name(name)
    cls = _make_cls(
        gen,
        cached_name,
        '    rows: Annotated[list["RowSchema"], Field(description="x")] = None\n',
    )
    [out] = gen.wrap_cache_fields_in_mapped([cls])
    assert 'Mapped[list["RowSchema"]]' in out.source


def test_wrap_two_level_generic(gen: ModuleType) -> None:
    """Two-level generic (``Optional[list["X"]]``) — the regex's documented depth limit."""
    name = next(iter(gen.CACHE_TABLES))
    cached_name = gen._cached_name(name)
    cls = _make_cls(
        gen,
        cached_name,
        '    items: Annotated[Optional[list["X"]], Field(description="x")] = None\n',
    )
    [out] = gen.wrap_cache_fields_in_mapped([cls])
    assert 'Mapped[Optional[list["X"]]]' in out.source


def test_wrap_relationship(gen: ModuleType) -> None:
    """Relationship fields get ``Mapped[]`` on the outer type."""
    name = next(iter(gen.CACHE_TABLES))
    cached_name = gen._cached_name(name)
    cls = _make_cls(
        gen,
        cached_name,
        '    rows: list["CachedRow"] = Relationship(back_populates="parent")\n',
    )
    [out] = gen.wrap_cache_fields_in_mapped([cls])
    assert 'Mapped[list["CachedRow"]] = Relationship(' in out.source


def test_skips_non_cache_class(gen: ModuleType) -> None:
    """Non-cache classes are left untouched."""
    cls = gen.ClassInfo(
        name="NotACache",
        source=(
            "class NotACache(KatanaPydanticBase):\n"
            '    id: Annotated[int, Field(description="x")]\n'
        ),
        bases=["KatanaPydanticBase"],
        line_start=1,
        line_end=2,
    )
    [out] = gen.wrap_cache_fields_in_mapped([cls])
    assert "Mapped[" not in out.source
    assert out.source == cls.source


def test_includes_entity_base_classes(gen: ModuleType) -> None:
    """Shared entity bases (BaseEntity, DeletableEntity, etc.) get wrapping
    too — without this, inherited ``deleted_at`` / ``created_at`` would
    stay un-wrapped and call sites would still need ``col()``."""
    base_name = next(iter(gen.ENTITY_BASE_CLASSES))
    cls = gen.ClassInfo(
        name=base_name,
        source=(
            f"class {base_name}(KatanaPydanticBase):\n"
            '    deleted_at: Annotated[datetime | None, Field(description="x")] = None\n'
        ),
        bases=["KatanaPydanticBase"],
        line_start=1,
        line_end=2,
    )
    [out] = gen.wrap_cache_fields_in_mapped([cls])
    assert "Mapped[datetime | None]" in out.source


def test_raises_on_unwrappable_deep_nesting(gen: ModuleType) -> None:
    """Three-level nesting exceeds the regex depth → assertion fires.

    Pin the failure mode: the regex handles up to two levels of bracket
    nesting (``Optional[list[X]]`` works, ``dict[str, dict[int, list[X]]]``
    doesn't). Rather than silently emit unwrapped fields, the pass
    raises ``GenerationError`` so a future spec addition that introduces
    this shape is caught immediately.
    """
    name = next(iter(gen.CACHE_TABLES))
    cached_name = gen._cached_name(name)
    cls = _make_cls(
        gen,
        cached_name,
        # Three levels: dict -> list -> dict
        '    nested: Annotated[dict[str, list[dict[int, str]]], Field(description="x")]\n',
    )
    with pytest.raises(gen.GenerationError, match="missed an Annotated"):
        gen.wrap_cache_fields_in_mapped([cls])


# ─── inject_index_annotations ───────────────────────────────────────────


def test_inject_index_annotations_handles_index_columns(gen: ModuleType) -> None:
    """``index_columns`` → ``SQLField(index=True, description=...)``.

    Variant.sku is in ``index_columns`` (non-unique index, mirroring the
    legacy ``idx_entity_sku`` non-unique index).
    """
    cls = _make_cls(
        gen,
        "CachedVariant",
        '    sku: Annotated[str, Field(description="Stock keeping unit")]\n',
    )
    [out] = gen.inject_index_annotations([cls])
    assert "SQLField(index=True, description=" in out.source
    # ``unique=True`` should NOT be present — legacy didn't enforce SKU
    # uniqueness, only a plain (non-unique) index.
    assert "unique=True" not in out.source
    # description preserved
    assert '"Stock keeping unit"' in out.source


def test_inject_index_annotations_skips_classes_without_specs(
    gen: ModuleType,
) -> None:
    """Classes without ``index_columns`` are untouched."""
    # CachedSalesOrder has neither spec.
    cls = _make_cls(
        gen,
        "CachedSalesOrder",
        '    order_no: Annotated[str, Field(description="Order number")]\n',
    )
    [out] = gen.inject_index_annotations([cls])
    assert out.source == cls.source


# ─── inject_fts_columns ─────────────────────────────────────────────────


def test_inject_fts_columns_emits_classvar(gen: ModuleType) -> None:
    """Cached classes with FTS specs get ``__fts_columns__`` as ClassVar."""
    # CachedVariant has CACHE_FTS_SPECS entry.
    cls = gen.ClassInfo(
        name="CachedVariant",
        source=(
            "class CachedVariant(DeletableEntity, table=True):\n"
            '    __tablename__ = "variant"\n'
            "    model_config = ConfigDict(frozen=False)\n"
        ),
        bases=["DeletableEntity"],
        line_start=1,
        line_end=3,
    )
    [out] = gen.inject_fts_columns([cls])
    assert "__fts_columns__: ClassVar[tuple[str, ...]] = (" in out.source
    # Each declared column should appear as a string literal.
    for col in gen.CACHE_FTS_SPECS["Variant"]:
        assert f"'{col}'" in out.source or f'"{col}"' in out.source


def test_inject_fts_columns_skips_classes_without_spec(gen: ModuleType) -> None:
    """Cached classes without ``CACHE_FTS_SPECS`` entry are untouched."""
    # CachedTaxRate has no FTS spec (lookup-only).
    cls = gen.ClassInfo(
        name="CachedTaxRate",
        source=(
            "class CachedTaxRate(UpdatableEntity, table=True):\n"
            '    __tablename__ = "tax_rate"\n'
            "    model_config = ConfigDict(frozen=False)\n"
        ),
        bases=["UpdatableEntity"],
        line_start=1,
        line_end=3,
    )
    [out] = gen.inject_fts_columns([cls])
    assert "__fts_columns__" not in out.source
    assert out.source == cls.source


def test_inject_fts_columns_raises_when_tablename_missing(gen: ModuleType) -> None:
    """Insert depends on ``__tablename__`` — missing it is a generator bug."""
    cls = gen.ClassInfo(
        name="CachedVariant",
        source="class CachedVariant(DeletableEntity, table=True):\n    pass\n",
        bases=["DeletableEntity"],
        line_start=1,
        line_end=2,
    )
    with pytest.raises(gen.GenerationError, match="__tablename__"):
        gen.inject_fts_columns([cls])


# ─── flatten_intermediate_inheritance ───────────────────────────────────


def test_flatten_strips_overriding_child_fields(gen: ModuleType) -> None:
    """When child redeclares a parent field, parent's wins (for SQLModel)."""
    parent_cls = gen.ClassInfo(
        name="InventoryItem",
        source=(
            "class InventoryItem(ArchivableEntity):\n"
            '    name: Annotated[str, Field(description="Item name")]\n'
            "    type: Annotated[InventoryItemType, "
            'Field(description="Discriminator")]\n'
        ),
        bases=["ArchivableEntity"],
        line_start=1,
        line_end=3,
    )
    # Cache-class shape after the duplicate pass: still inherits from
    # InventoryItem, redeclares ``type`` with Literal narrowing.
    child_cls = gen.ClassInfo(
        name="CachedMaterial",
        source=(
            "class CachedMaterial(InventoryItem):\n"
            '    type: Annotated[Literal["material"], '
            'Field(description="Discriminator narrow")]\n'
            "    serial_tracked: Annotated[bool | None, "
            'Field(description="Serial tracked")] = None\n'
        ),
        bases=["InventoryItem"],
        line_start=1,
        line_end=4,
    )
    [out_parent, out_child] = gen.flatten_intermediate_inheritance(
        [parent_cls, child_cls]
    )
    # Parent is unchanged (not a CACHE_TABLES entry with flatten_parent).
    assert out_parent.source == parent_cls.source
    # Child's bases flipped to the parent's base.
    assert "class CachedMaterial(ArchivableEntity):" in out_child.source
    # Child's ``type: Literal[...]`` removed; parent's enum-typed
    # ``type`` is inlined.
    assert "InventoryItemType" in out_child.source
    assert 'Literal["material"]' not in out_child.source
    # Child-only field preserved.
    assert "serial_tracked" in out_child.source
    # Parent's field also preserved.
    assert "Item name" in out_child.source


def test_flatten_skips_non_flattening_classes(gen: ModuleType) -> None:
    """Cached classes without ``flatten_parent`` are untouched."""
    # CachedVariant inherits from UpdatableEntity, DeletableEntity directly
    # — no flatten_parent in its CacheTableSpec.
    cls = gen.ClassInfo(
        name="CachedVariant",
        source=(
            "class CachedVariant(UpdatableEntity, DeletableEntity):\n"
            '    sku: Annotated[str, Field(description="SKU")]\n'
        ),
        bases=["UpdatableEntity", "DeletableEntity"],
        line_start=1,
        line_end=2,
    )
    [out] = gen.flatten_intermediate_inheritance([cls])
    assert out.source == cls.source


# ─── End-to-end Cached* generator-output tests ──────────────────────────


def test_generated_cached_variant_indexed_sku() -> None:
    """``CachedVariant.sku`` is indexed (not unique).

    The legacy ``CatalogCache`` had a non-unique index on
    ``entity_index.sku COLLATE NOCASE``; uniqueness was on
    ``(entity_type, id)``. Phase A mirrors that: SKU is indexed for
    fast lookup but not unique. Phase B's adapter applies COLLATE NOCASE
    in the lookup query for case-insensitive ``get_by_sku``.
    """
    import importlib

    from sqlmodel import SQLModel

    importlib.import_module(
        "katana_public_api_client.models_pydantic._generated.inventory"
    )
    sku_col = SQLModel.metadata.tables["variant"].columns["sku"]
    assert sku_col.index is True
    # Not unique — see docstring; flipping this to True is a follow-up
    # tightening, paired with a NOCASE collation hint.
    assert sku_col.unique is None or sku_col.unique is False


def test_generated_cached_variant_fts_columns() -> None:
    """``CachedVariant.__fts_columns__`` matches CACHE_FTS_SPECS."""
    from katana_public_api_client.models_pydantic._generated import CachedVariant

    assert CachedVariant.__fts_columns__ == (
        "sku",
        "display_name",
        "parent_name",
        "supplier_item_codes_text",
        "internal_barcode",
        "registered_barcode",
    )


def test_generated_cached_variant_extra_fields() -> None:
    """Cache-only synthesized columns (extra_fields) land on the table."""
    import importlib

    from sqlmodel import SQLModel

    importlib.import_module(
        "katana_public_api_client.models_pydantic._generated.inventory"
    )
    column_names = {c.name for c in SQLModel.metadata.tables["variant"].columns}
    assert "parent_archived_at" in column_names
    assert "display_name" in column_names
    assert "parent_name" in column_names
    assert "supplier_item_codes_text" in column_names


def test_generated_catalog_cache_classes_resolve() -> None:
    """All 11 catalog ``Cached*`` classes are importable from the package."""
    from sqlmodel import SQLModel

    from katana_public_api_client.models_pydantic._generated import (
        CachedAdditionalCost,
        CachedCustomer,
        CachedFactory,
        CachedLocation,
        CachedMaterial,
        CachedOperator,
        CachedProduct,
        CachedService,
        CachedSupplier,
        CachedTaxRate,
        CachedVariant,
    )

    # Each class registers a table on SQLModel.metadata at import time —
    # verify the expected tablenames are all present.
    expected_tables = {
        CachedAdditionalCost.__tablename__,
        CachedCustomer.__tablename__,
        CachedFactory.__tablename__,
        CachedLocation.__tablename__,
        CachedMaterial.__tablename__,
        CachedOperator.__tablename__,
        CachedProduct.__tablename__,
        CachedService.__tablename__,
        CachedSupplier.__tablename__,
        CachedTaxRate.__tablename__,
        CachedVariant.__tablename__,
    }
    metadata_tables = set(SQLModel.metadata.tables)
    missing = expected_tables - metadata_tables
    assert not missing, f"Tables not registered with SQLModel.metadata: {missing}"


def test_generated_cached_location_tablename() -> None:
    """``Location`` API class shadowed as ``CachedLocation`` /
    ``__tablename__`` ``location``."""
    from katana_public_api_client.models_pydantic._generated import CachedLocation

    # SQLModel's metaclass exposes ``__tablename__`` as ``declared_attr[str]``
    # at class-level access; pyright sees ``==`` on that as
    # ``ColumnElement[bool]``. Read via ``str()`` to compare the actual
    # tablename string.
    assert str(CachedLocation.__tablename__) == "location"


def test_generated_cached_material_flattens_inventory_item() -> None:
    """``CachedMaterial`` inlines InventoryItem fields and skips the
    intermediate inheritance — ``variants``/``configs``/``supplier`` land
    as JSON columns on the table itself."""
    import importlib

    from sqlmodel import SQLModel

    importlib.import_module(
        "katana_public_api_client.models_pydantic._generated.inventory"
    )
    column_names = {c.name for c in SQLModel.metadata.tables["material"].columns}
    # Inlined from InventoryItem
    assert "name" in column_names
    assert "uom" in column_names
    assert "category_name" in column_names
    assert "variants" in column_names
    assert "configs" in column_names
    assert "supplier" in column_names
    # Material's own
    assert "serial_tracked" in column_names
    assert "deleted_at" in column_names
    # ArchivableEntity's
    assert "archived_at" in column_names


# ─── _rewrite_identifiers_outside_strings ────────────────────────────────


def test_rewrite_skips_identifiers_inside_descriptions(gen: ModuleType) -> None:
    """Class names appearing as English words in descriptions stay intact.

    This guards the regression seen during #472 Phase A: the duplicate
    pass's word-boundary regex was rewriting ``"Customer's reference"``
    to ``"CachedCustomer's reference"`` because ``Customer`` was a new
    CACHE_TABLES entry. The tokenize-aware version skips string literals.
    """
    source = (
        "class Foo:\n"
        '    description: str = "Customer\'s reference number"\n'
        "    parent: Customer | None = None\n"
    )
    rewritten = gen._rewrite_identifiers_outside_strings(
        source, {"Customer": "CachedCustomer"}
    )
    # String literal preserved intact.
    assert '"Customer\'s reference number"' in rewritten
    # Type annotation rewritten.
    assert "parent: CachedCustomer | None" in rewritten


def test_rewrite_handles_forward_ref_strings(gen: ModuleType) -> None:
    """Forward-ref strings (``"Variant"``) inside ``Mapped[...]`` get rewritten."""
    source = 'class Foo:\n    rel: Mapped[Optional["Variant"]] = Relationship()\n'
    rewritten = gen._rewrite_identifiers_outside_strings(
        source, {"Variant": "CachedVariant"}
    )
    assert '"CachedVariant"' in rewritten


def test_rewrite_preserves_whitespace_and_layout(gen: ModuleType) -> None:
    """Whitespace, indentation, and trailing newlines round-trip exactly
    when no identifiers match (no-op rewrite)."""
    source = "class Foo:\n    x: int = 1\n    y: str = 'hello'\n"
    rewritten = gen._rewrite_identifiers_outside_strings(source, {"NotPresent": "X"})
    assert rewritten == source


# ─── restore_phantom_any_timestamps ─────────────────────────────────────


def test_restore_phantom_any_created_updated(gen: ModuleType) -> None:
    """Bare ``created_at: Any`` / ``updated_at: Any`` → required ``AwareDatetime``.

    datamodel-codegen 0.58.0 emits these phantom ``Any`` fields when a schema
    promotes an inherited timestamp to ``required`` via allOf (e.g.
    ``InventoryMovement``). The pass restores the concrete type.
    """
    cls = gen.ClassInfo(
        name="InventoryMovement",
        source=(
            "class InventoryMovement(UpdatableEntity):\n"
            "    rank: Annotated[int | None, Field(description='x')] = None\n"
            "    created_at: Any\n"
            "    updated_at: Any\n"
        ),
        bases=["UpdatableEntity"],
        line_start=1,
        line_end=4,
    )
    [out] = gen.restore_phantom_any_timestamps([cls])
    assert "created_at: Any" not in out.source
    assert "updated_at: Any" not in out.source
    assert (
        "    created_at: Annotated[\n"
        '        AwareDatetime, Field(description="Timestamp when the entity '
        'was first created")\n'
        "    ]"
    ) in out.source
    assert (
        "    updated_at: Annotated[\n"
        '        AwareDatetime, Field(description="Timestamp when the entity '
        'was last updated")\n'
        "    ]"
    ) in out.source


def test_restore_phantom_leaves_typed_timestamps_untouched(gen: ModuleType) -> None:
    """A correctly-typed ``created_at`` is not rewritten (only bare ``Any`` is)."""
    typed = (
        "class Foo(UpdatableEntity):\n"
        "    created_at: Annotated[\n"
        '        AwareDatetime | None, Field(description="x")\n'
        "    ] = None\n"
    )
    cls = gen.ClassInfo(
        name="Foo", source=typed, bases=["UpdatableEntity"], line_start=1, line_end=4
    )
    [out] = gen.restore_phantom_any_timestamps([cls])
    assert out.source == typed


def test_restore_phantom_ignores_unrelated_any_fields(gen: ModuleType) -> None:
    """A non-timestamp ``: Any`` field is left alone — only the mapped names match."""
    src = "class Foo:\n    metadata: Any\n    created_at: Any\n"
    cls = gen.ClassInfo(name="Foo", source=src, bases=[], line_start=1, line_end=3)
    [out] = gen.restore_phantom_any_timestamps([cls])
    assert "    metadata: Any" in out.source  # untouched
    assert "created_at: Any" not in out.source  # restored


def test_generated_inventory_movement_timestamps_typed() -> None:
    """End-to-end: the generated InventoryMovement keeps AwareDatetime timestamps."""
    from katana_public_api_client.models_pydantic._generated.inventory import (
        InventoryMovement,
    )

    for field_name in ("created_at", "updated_at"):
        annotation = InventoryMovement.model_fields[field_name].annotation
        assert annotation is not Any, (
            f"{field_name} regressed to Any — restore_phantom_any_timestamps "
            "should keep it AwareDatetime"
        )
