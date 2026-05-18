#!/usr/bin/env python3
"""Generate Pydantic v2 models from the OpenAPI specification.

This script:
1. Runs datamodel-codegen to generate Pydantic models (config in pyproject.toml)
2. Parses the generated file using Python AST
3. Groups classes by domain into separate files
4. Generates cross-file imports and __init__.py
5. Generates _auto_registry.py for attrs↔pydantic mappings
6. Runs ruff format/fix on the generated code

Usage:
    uv run python scripts/generate_pydantic_models.py
"""

from __future__ import annotations

import ast
import io
import re
import shutil
import subprocess
import tempfile
import tokenize
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


class GenerationError(Exception):
    """Raised when code generation fails."""

    def __init__(self, message: str, exit_code: int = 1) -> None:
        super().__init__(message)
        self.exit_code = exit_code


# Domain groupings that preserve discriminator relationships
# Key: group name, Value: list of class name patterns (exact match or prefix match with *)
DOMAIN_GROUPS: dict[str, list[str]] = {
    "base": [
        "BaseEntity",
        "UpdatableEntity",
        "DeletableEntity",
        "ArchivableEntity",
        "ArchivableDeletableEntity",
    ],
    "errors": [
        "ErrorResponse",
        "CodedErrorResponse",
        "DetailedErrorResponse",
        "BaseValidationError",
        "ValidationErrorDetail",
        # Ajv-style validation error subtypes (one per Ajv keyword)
        "AdditionalPropertiesValidationError",
        "ConstValidationError",
        "DependenciesValidationError",
        "EnumValidationError",
        "ExclusiveMaximumValidationError",
        "ExclusiveMinimumValidationError",
        "FormatValidationError",
        "MaxItemsValidationError",
        "MaxLengthValidationError",
        "MaximumValidationError",
        "MinItemsValidationError",
        "MinLengthValidationError",
        "MinimumValidationError",
        "MultipleOfValidationError",
        "OneOfValidationError",
        "PatternValidationError",
        "RequiredValidationError",
        "TypeValidationError",
        "UniqueItemsValidationError",
        "GenericValidationError",
        # Anonymous ``info`` shape classes and ``Code*`` discriminator enums
        # are emitted by the codegen as ``Info``/``Info1``/... and
        # ``Code``/``Code1``/... — match them with prefix wildcards so adding
        # a 20th Ajv keyword down the road doesn't require updating this
        # list. Safe: ``CodedErrorResponse`` (the only non-numbered ``Code*``
        # name) resolves via the exact-match pass above.
        "Info*",
        "Code*",
    ],
    "inventory": [
        "InventoryItem",
        "Product",
        "ProductListResponse",
        "Material",
        "MaterialListResponse",
        "Variant",
        "VariantListResponse",
        "VariantResponse",  # Has discriminated union Product | Material
        "ServiceVariant",
        "ItemConfig",
        "MaterialConfig",
        "Inventory",
        "InventoryListResponse",
        "InventoryMovement",
        "InventoryMovementListResponse",
        "InventoryReorderPoint*",
        "InventorySafetyStock*",
        "Service",
        "ServiceListResponse",
        "CreateProduct*",
        "CreateMaterial*",
        "CreateVariant*",
        "CreateService*",
        "CreateInventoryReorderPointRequest",
        "UpdateProduct*",
        "UpdateMaterial*",
        "UpdateVariant*",
        "UpdateService*",
    ],
    "stock": [
        "Batch*",
        "Stock*",
        "Stocktake*",
        "StorageBin*",
        "NegativeStock*",
        "SerialNumber*",
        "ResourceType1",  # Enum for CreateSerialNumbersRequest - must be co-located
        "CreateSerial*",
        "DeleteSerial*",  # DeleteSerialNumbersRequest references SerialNumberResourceType
        "CreateStock*",
        "CreateStocktake*",
        "UpdateStock*",
        "UpdateStocktake*",
    ],
    "purchase_orders": [
        "PurchaseOrder*",
        "OutsourcedPurchaseOrder*",
        "RegularPurchaseOrder*",
        "CreatePurchaseOrder*",
        "CreateOutsourcedPurchaseOrder*",
        "UpdatePurchaseOrder*",
        "UpdateOutsourcedPurchaseOrder*",
    ],
    "sales_orders": [
        "SalesOrder*",
        "SalesReturn*",
        "ReturnableItem",
        "UnassignedBatchTransaction",
        "UnassignedBatchTransactionListResponse",
        "CreateSalesOrder*",
        "CreateSalesReturn*",
        "UpdateSalesOrder*",
        "UpdateSalesReturn*",
        "Address1",  # Extends SalesOrderAddress - must be co-located to avoid circular imports
    ],
    "manufacturing": [
        "ManufacturingOrder*",
        "Recipe*",
        "BomRow*",
        "MakeToOrder*",
        "CreateManufacturing*",
        "CreateRecipe*",
        "CreateBom*",
        "BatchCreateBom*",
        "BatchCreateBomRowsRequest",  # Uses CreateBomRowRequest from manufacturing
        "UpdateManufacturing*",
        "UpdateBom*",
        "UpdateRecipeRowRequest",
        "UnlinkManufacturing*",
    ],
    "contacts": [
        "Customer*",
        "Supplier*",
        "PriceList*",
        "CreateCustomer*",
        "CreateSupplier*",
        "CreatePriceList*",
        "UpdateCustomer*",
        "UpdateSupplier*",
        "UpdatePriceList*",
    ],
    "webhooks": [
        "Webhook*",
        "CreateWebhook*",
        "UpdateWebhook*",
    ],
    # common catches everything else
}


@dataclass(frozen=True)
class CacheExtraField:
    """A cache-only field hoisted onto a cache class.

    Used when a discriminated-union root (``PurchaseOrderBase``) is cached as
    one SQL table but the listing tool needs to filter by a column that
    lives on a subclass (``OutsourcedPurchaseOrder.tracking_location_id``).
    The converter copies the value out of the subclass instance.

    ``render()`` emits the field declaration as a Python source line. The
    caller pastes it into the cache class body via ``inject_extra_cache_fields``;
    SQLModel infers the column type from the annotation (``Optional`` types
    stay nullable). When ``description`` is set the renderer uses
    ``Annotated[..., Field(description=...)]`` so the field is self-
    documenting in the generated source.
    """

    name: str
    python_type: str
    default: str = "None"
    description: str | None = None

    def render(self) -> str:
        if self.description is None:
            return f"    {self.name}: {self.python_type} = {self.default}"
        return (
            f"    {self.name}: Annotated[\n"
            f"        {self.python_type},\n"
            f"        Field(description={self.description!r}),\n"
            f"    ] = {self.default}"
        )


@dataclass(frozen=True)
class CacheTableSpec:
    """Per-class cache-table configuration.

    All entry-keyed cache settings live here so a reader doesn't need to
    consult four parallel dicts to know what one class produces.
    ``CACHE_RELATIONSHIPS`` (list of parent→child links) stays separate
    because it has different cardinality.

    - ``name_override``: post-rename base name (no ``Cached`` prefix) used
      to derive both the cache class name and the SQLAlchemy
      ``__tablename__`` when the API class name reads awkwardly. Example:
      ``PurchaseOrderBase`` sets ``name_override="PurchaseOrder"``,
      yielding cache class ``CachedPurchaseOrder`` (via ``_cached_name``)
      and ``__tablename__`` ``purchase_order`` (via ``_snake_case``).
    - ``extra_fields``: cache-only fields hoisted from API subclasses
      (e.g., outsourced-PO's ``tracking_location_id``).
    - ``json_columns``: fields whose values stay JSON in the cache (lists
      of polymorphic / non-cached nested models, single nested objects
      SQLAlchemy can't auto-map).
    - ``index_columns``: fields that get ``index=True`` on the SQLAlchemy
      column. Used for high-cardinality lookup columns where the legacy
      schema defined a plain index — e.g., ``Variant.sku`` (legacy
      ``idx_entity_sku ON entity_index(sku COLLATE NOCASE)``). Add
      ``unique=True`` support here when a future cache class needs
      DB-level uniqueness.
    - ``flatten_parent``: when set, the cache class flattens an intermediate
      non-base, non-cached parent class (e.g., ``Material(InventoryItem)`` →
      ``CachedMaterial(ArchivableEntity)`` with ``InventoryItem``'s fields
      inlined). Required for SQLModel ``table=True`` because the intermediate
      parent's nested-list/nested-object fields can't be inferred as columns.
    """

    name_override: str | None = None
    extra_fields: tuple[CacheExtraField, ...] = ()
    json_columns: tuple[str, ...] = ()
    index_columns: tuple[str, ...] = ()
    flatten_parent: str | None = None


# Cache-table configuration for #342 — select generated pydantic classes opt
# into SQLAlchemy table semantics (``table=True``) so they double as cache
# row schemas. Each entry's spec carries any per-class overrides; an empty
# ``CacheTableSpec()`` means "default cache table, no overrides".
CACHE_TABLES: dict[str, CacheTableSpec] = {
    "SalesOrder": CacheTableSpec(
        # ``shipping_fee`` is a single nested object; ``addresses`` is a
        # list of nested ``SalesOrderAddress``. ``custom_fields`` is a
        # tenant-keyed dict (see #734). All three stay JSON because
        # they're low-signal for the cache's filter workload.
        json_columns=("shipping_fee", "addresses", "custom_fields"),
    ),
    "SalesOrderRow": CacheTableSpec(
        json_columns=(
            "attributes",
            "batch_transactions",
            "serial_numbers",
            "serial_number_transactions",
            "custom_fields",
        ),
    ),
    "StockAdjustment": CacheTableSpec(),
    "StockAdjustmentRow": CacheTableSpec(json_columns=("batch_transactions",)),
    "ManufacturingOrder": CacheTableSpec(
        json_columns=("batch_transactions", "serial_numbers"),
    ),
    "ManufacturingOrderRecipeRow": CacheTableSpec(
        json_columns=("batch_transactions",),
    ),
    "PurchaseOrderBase": CacheTableSpec(
        # API discriminated-union root (sibling of RegularPurchaseOrder +
        # OutsourcedPurchaseOrder); cache shadows as ``CachedPurchaseOrder``
        # (``__tablename__`` ``purchase_order``, not ``purchase_order_base``).
        name_override="PurchaseOrder",
        extra_fields=(
            CacheExtraField(
                name="tracking_location_id",
                python_type="int | None",
                description=(
                    "(cache-only) Hoisted from OutsourcedPurchaseOrder so the "
                    "single ``purchase_order`` cache table can filter by tracking "
                    "location without a UNION across regular/outsourced rows."
                ),
            ),
        ),
        # ``supplier`` is a single nested ``Supplier`` object; SQLAlchemy
        # can't auto-map it, JSON-column instead.
        json_columns=("supplier",),
    ),
    "PurchaseOrderRow": CacheTableSpec(
        # ``landed_cost: str | float | None`` is a non-optional inner union
        # SQLAlchemy can't auto-type — JSON-column it instead of dropping.
        json_columns=("batch_transactions", "landed_cost"),
    ),
    "StockTransfer": CacheTableSpec(),
    "StockTransferRow": CacheTableSpec(json_columns=("batch_transactions",)),
    # ── Catalog tier (#472 Phase A) ──────────────────────────────────────
    # 11 entity types previously cached in the legacy single-table
    # ``CatalogCache`` (entities + entity_index + FTS5). Each gets its own
    # ``Cached<Name>`` SQLModel sibling so they can join the typed-cache
    # engine in Phase B.
    "Variant": CacheTableSpec(
        # Variant has no ``archived_at`` of its own — Katana archives at the
        # parent (Product/Material) level. The legacy cache denormalized
        # ``parent_archived_at`` at sync time so the index could filter
        # archived variants out by default. Phase B's ``attrs_postprocess``
        # hook populates this column from ``attrs_obj.product_or_material``.
        # ``display_name``, ``parent_name``, and ``supplier_item_codes_text``
        # are also synthesized at sync time — they back the FTS5 columns
        # declared in ``CACHE_FTS_SPECS["Variant"]``.
        extra_fields=(
            CacheExtraField(
                name="parent_archived_at",
                python_type="datetime | None",
                description=(
                    "(cache-only) Lifted from parent product/material so search "
                    "can filter by parent archive state without a join."
                ),
            ),
            CacheExtraField(
                name="display_name",
                python_type="str | None",
                description=(
                    "(cache-only) Synthesized at sync time — parent name + "
                    "config attribute values, joined with ``/``. Backs FTS5 "
                    "search; falls back to SKU when parent name is empty."
                ),
            ),
            CacheExtraField(
                name="parent_name",
                python_type="str | None",
                description=(
                    "(cache-only) Lifted from parent product/material name. "
                    "Backs FTS5 search and surfaces in result rendering."
                ),
            ),
            CacheExtraField(
                name="supplier_item_codes_text",
                python_type="str | None",
                description=(
                    "(cache-only) Space-joined ``supplier_item_codes`` so the "
                    "FTS5 tokenizer can index multi-token supplier codes "
                    "without parsing JSON at query time."
                ),
            ),
        ),
        # ``custom_fields`` and ``config_attributes`` are lists of nested
        # objects SQLAlchemy can't auto-map. ``supplier_item_codes`` is a
        # ``list[str]`` — JSON-columned for the same reason; the FTS-friendly
        # joined form lives in ``supplier_item_codes_text`` (extra_field).
        json_columns=("custom_fields", "config_attributes", "supplier_item_codes"),
        # The legacy ``entity_index`` table had only a non-unique index
        # ``idx_entity_sku`` (with ``COLLATE NOCASE``) on sku — uniqueness
        # was on ``(entity_type, id)``, not on sku. Mirror that here:
        # ``sku`` is indexed but not unique. Phase B's CatalogQueries
        # adapter applies ``COLLATE NOCASE`` in the lookup query so
        # case-insensitive ``get_by_sku`` keeps the legacy semantics.
        index_columns=("sku",),
    ),
    "Product": CacheTableSpec(
        # Product extends ``InventoryItem`` (intermediate non-cached parent
        # with nested-list fields SQLModel can't auto-map). Flatten to
        # ``ArchivableEntity`` directly, inlining InventoryItem's columns
        # into the cache class body so JSON-column injection lands.
        flatten_parent="InventoryItem",
        # ``variants`` references CachedVariant after the duplicate-pass
        # rewrite (a list of nested cache rows); ``configs`` is a list of
        # ``ItemConfig`` (not in CACHE_TABLES); ``supplier`` is a single
        # nested ``Supplier`` (becomes ``CachedSupplier`` after rewrite,
        # but cross-entity FK wiring is deferred to Phase B). All three
        # stay JSON for Phase A.
        json_columns=("variants", "configs", "supplier"),
    ),
    "Material": CacheTableSpec(
        flatten_parent="InventoryItem",
        json_columns=("variants", "configs", "supplier"),
    ),
    "Service": CacheTableSpec(
        # ``variants: list[ServiceVariant]`` — ServiceVariant is not in
        # CACHE_TABLES, JSON-column it.
        json_columns=("variants",),
    ),
    "Customer": CacheTableSpec(
        # ``addresses: list[CustomerAddress]`` — CustomerAddress is not in
        # CACHE_TABLES, JSON-column it.
        json_columns=("addresses",),
    ),
    "Supplier": CacheTableSpec(
        json_columns=("addresses",),
    ),
    "Location": CacheTableSpec(
        # ``address: LocationAddress | None`` is a single nested object
        # SQLAlchemy can't auto-map, JSON it.
        json_columns=("address",),
    ),
    "TaxRate": CacheTableSpec(),
    "Operator": CacheTableSpec(),
    "Factory": CacheTableSpec(
        # ``legal_address: dict[str, Any] | None`` is an unstructured dict
        # SQLAlchemy can't auto-map, JSON it.
        json_columns=("legal_address",),
    ),
    "AdditionalCost": CacheTableSpec(),
}


# ── #472 Phase A — FTS5 column specs ─────────────────────────────────────
# Per-entity FTS5 search columns. Phase B builds ``<entity>_fts`` virtual
# tables from these specs and rewrites ``smart_search`` to MATCH against
# them. Entities omitted from this dict skip FTS — ``get_all`` + ``difflib``
# fuzzy fallback covers the lookup-only types (Location, TaxRate, Operator,
# Factory, AdditionalCost).
#
# Generator emits ``__fts_columns__: ClassVar[tuple[str, ...]]`` on each
# ``Cached*`` class with an entry here. Every column listed must exist on
# ``Cached<Name>.__table__.columns`` — a Phase B startup assertion will
# enforce this. Synthesized columns (``display_name``, ``parent_name``,
# ``supplier_item_codes_text`` on Variant) live in CACHE_TABLES.extra_fields
# so the schema and the FTS spec stay honest.
CACHE_FTS_SPECS: dict[str, tuple[str, ...]] = {
    "Variant": (
        "sku",
        "display_name",
        "parent_name",
        "supplier_item_codes_text",
        "internal_barcode",
        "registered_barcode",
    ),
    "Product": ("name", "category_name"),
    "Material": ("name", "category_name"),
    "Service": ("name",),
    # Supplier doesn't have a ``code`` field on the wire (the legacy index's
    # ``name2_key="code"`` resolved to ``None`` in dict lookups). Drop it
    # from FTS — searchable fields below are the real ones.
    "Customer": ("name", "email", "phone"),
    "Supplier": ("name", "email", "phone"),
}


@dataclass(frozen=True)
class CacheTableRelationship:
    """1:N parent→child relationship declaration between two cache tables.

    When the API model exposes the children as a nested list field on the
    parent (e.g., ``SalesOrder.sales_order_rows``), set ``parent_field`` to
    that field name and ``cache_only_parent_field`` to ``False`` — the
    generator rewrites the list field as a SQLModel ``Relationship``.

    When the API model does NOT expose the children on the wire (e.g.,
    ``ManufacturingOrder``: recipe rows are fetched via a separate
    endpoint), set ``cache_only_parent_field=True`` and ``parent_field``
    to the desired cache-only attribute name. The generator appends a
    fresh ``Relationship`` descriptor to the cached parent class — useful
    for orphan-cleanup and back-pointer traversal in cache queries.
    """

    parent: str
    parent_field: str
    child: str
    child_back_ref: str
    child_fk_field: str
    cache_only_parent_field: bool = False

    @property
    def parent_table(self) -> str:
        # Honor the cache spec's ``name_override`` so FK
        # ``foreign_key="<table>.id"`` matches the renamed tablename
        # (e.g., ``PurchaseOrderBase`` → ``purchase_order``, not
        # ``purchase_order_base``).
        return _snake_case(_resolve_cache_class(self.parent))


def _snake_case(name: str) -> str:
    """CamelCase → snake_case — used for default SQLAlchemy tablenames."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _rewrite_identifiers_outside_strings(
    source: str, replacements: dict[str, str]
) -> str:
    """Rename identifiers in Python source, skipping string literals.

    Used by both ``duplicate_cache_tables_as_cached_siblings`` and
    ``flatten_intermediate_inheritance`` to rewrite cross-cache type
    references (``Variant`` → ``CachedVariant``, etc.) without corrupting
    descriptions that happen to use the same identifier as an English
    word (e.g. ``"Customer's reference number"`` stays untouched).

    Walks the source via ``tokenize`` and substitutes inside ``NAME``
    tokens plus single-line forward-reference ``STRING`` tokens
    (``Mapped[Optional["Variant"]]`` — SQLAlchemy resolves these as type
    expressions). Triple-quoted docstrings stay untouched. ``untokenize``
    in 5-tuple form preserves the original formatting exactly.

    Falls back to a regex-based rewrite if tokenize fails on
    syntactically odd input — should not happen on valid generated code,
    but keeps the pipeline alive if datamodel-codegen ever emits an
    edge-case shape.
    """
    rewritten: list[tokenize.TokenInfo] = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            new_string = _rewrite_token_string(tok, replacements)
            if new_string is None:
                rewritten.append(tok)
            else:
                rewritten.append(tok._replace(string=new_string))
    except (tokenize.TokenError, IndentationError):
        result = source
        for key in sorted(replacements, key=len, reverse=True):
            result = re.sub(rf"\b{re.escape(key)}\b", replacements[key], result)
        return result
    return tokenize.untokenize(rewritten)


def _rewrite_token_string(
    tok: tokenize.TokenInfo, replacements: dict[str, str]
) -> str | None:
    """Return the rewritten token string, or None if the token is unchanged.

    Two cases get rewritten:

    - ``NAME`` tokens whose value is in ``replacements`` (identifier rename).
    - Single-quoted ``STRING`` tokens whose unquoted content is in
      ``replacements`` (forward-reference rename in
      ``Mapped[Optional["Variant"]]`` etc.). Triple-quoted strings
      (docstrings) and prefix-quoted strings (``r""``, ``b""``) are skipped.
    """
    if tok.type == tokenize.NAME and tok.string in replacements:
        return replacements[tok.string]
    if (
        tok.type == tokenize.STRING
        and tok.string
        and tok.string[0] in ('"', "'")
        and not tok.string.startswith(('"""', "'''"))
        and tok.string[1:-1] in replacements
    ):
        quote = tok.string[0]
        return f"{quote}{replacements[tok.string[1:-1]]}{quote}"
    return None


def _resolve_cache_class(name: str) -> str:
    """API class name → cache class name (post-rename, no ``Cached`` prefix).

    Returns the cache class's final name without the ``Cached`` prefix. Used
    by ``_cached_name`` and by ``CacheTableRelationship.parent_table`` so
    cache references resolve to the renamed table consistently.
    """
    spec = CACHE_TABLES.get(name)
    return spec.name_override if (spec and spec.name_override is not None) else name


def _cached_name(name: str) -> str:
    """API class name → cache-row class name (``SalesOrder`` → ``CachedSalesOrder``).

    Cache rows live as ``Cached<Name>`` siblings of the API pydantic models
    so the API surface stays pure (no ``table=True``, no FK pollution) while
    the cache schema can carry SQLAlchemy machinery, FK back-pointers, and
    relationships. ``CacheTableSpec.name_override`` lets a class shadow
    under a different name (``PurchaseOrderBase`` → ``CachedPurchaseOrder``).
    """
    return f"Cached{_resolve_cache_class(name)}"


CACHE_RELATIONSHIPS: list[CacheTableRelationship] = [
    CacheTableRelationship(
        parent="SalesOrder",
        parent_field="sales_order_rows",
        child="SalesOrderRow",
        child_back_ref="sales_order",
        child_fk_field="sales_order_id",
    ),
    CacheTableRelationship(
        parent="StockAdjustment",
        parent_field="stock_adjustment_rows",
        child="StockAdjustmentRow",
        child_back_ref="stock_adjustment",
        child_fk_field="stock_adjustment_id",
    ),
    CacheTableRelationship(
        parent="PurchaseOrderBase",
        parent_field="purchase_order_rows",
        child="PurchaseOrderRow",
        child_back_ref="purchase_order",
        child_fk_field="purchase_order_id",
    ),
    CacheTableRelationship(
        parent="StockTransfer",
        parent_field="stock_transfer_rows",
        child="StockTransferRow",
        child_back_ref="stock_transfer",
        child_fk_field="stock_transfer_id",
    ),
    # ManufacturingOrder does NOT expose recipe_rows on the wire — the
    # rows are fetched via a separate ``manufacturing_order_recipe``
    # endpoint. ``cache_only_parent_field=True`` tells the generator to
    # append a fresh ``Relationship`` descriptor to the cached parent
    # rather than rewriting an existing list field. On the child,
    # ``inject_foreign_keys`` rewrites the existing
    # ``manufacturing_order_id`` field (returned on the wire) into an
    # FK-aware ``SQLField(...)``, so orphan cleanup queries can traverse
    # parent→children correctly.
    CacheTableRelationship(
        parent="ManufacturingOrder",
        parent_field="recipe_rows",
        child="ManufacturingOrderRecipeRow",
        child_back_ref="manufacturing_order",
        child_fk_field="manufacturing_order_id",
        cache_only_parent_field=True,
    ),
]


@dataclass
class ClassInfo:
    """Information about a class definition."""

    name: str
    source: str
    bases: list[str]
    line_start: int
    line_end: int

    def with_source(self, new_source: str) -> ClassInfo:
        """Return a copy with a rewritten ``source`` (other fields preserved).

        Used by the cache-table inject passes — each pass mutates the
        generated source string in-place; using this helper avoids the
        repetitive ``ClassInfo(name=cls.name, source=new_source, ...)``
        reconstruction with four passthrough fields.
        """
        return ClassInfo(
            name=self.name,
            source=new_source,
            bases=self.bases,
            line_start=self.line_start,
            line_end=self.line_end,
        )


@dataclass
class TypeAliasInfo:
    """Information about a type alias assignment (e.g., ConfigAttribute2 = ConfigAttribute)."""

    name: str
    source: str
    target: str  # The class name it's aliasing


@dataclass
class ImportInfo:
    """Information about an import statement."""

    source: str
    names: list[str]
    is_from_import: bool
    module: str | None = None


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    """Run a command and return the result.

    Args:
        cmd: Command and arguments to run.
        cwd: Working directory for the command.
        check: If True, raise GenerationError on non-zero exit code.

    Returns:
        The completed process result.

    Raises:
        GenerationError: If check is True and command exits with non-zero code.
    """
    import sys

    print(f"  Running: {' '.join(cmd)}")
    if cwd:
        print(f"    Working directory: {cwd}")

    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    if check and result.returncode != 0:
        msg = f"Command failed with exit code {result.returncode}: {' '.join(cmd)}"
        raise GenerationError(msg, exit_code=result.returncode)

    return result


def generate_single_file(output_path: Path) -> None:
    """Generate Pydantic models to a single file using datamodel-codegen.

    The tool reads configuration from pyproject.toml.

    Args:
        output_path: Path where the generated file will be written.

    Raises:
        GenerationError: If generation fails or output file is not created.
    """
    print("Generating Pydantic models from OpenAPI spec...")

    cmd = [
        "datamodel-codegen",
        "--output",
        str(output_path),
    ]

    result = run_command(cmd, check=False)

    if result.returncode != 0:
        msg = f"datamodel-codegen failed with exit code {result.returncode}"
        raise GenerationError(msg, exit_code=result.returncode)

    if not output_path.exists():
        msg = f"Generated file not found at {output_path}"
        raise GenerationError(msg)

    lines = len(output_path.read_text().splitlines())
    print(f"  Generated {lines} lines")


def parse_generated_file(
    source_path: Path,
) -> tuple[list[ImportInfo], list[ClassInfo], list[TypeAliasInfo]]:
    """Parse the generated Python file using AST."""
    print("Parsing generated file with AST...")

    content = source_path.read_text(encoding="utf-8")
    lines = content.splitlines()
    tree = ast.parse(content)

    imports: list[ImportInfo] = []
    classes: list[ClassInfo] = []
    type_aliases: list[TypeAliasInfo] = []

    # Process only top-level nodes (imports, classes, and type aliases)
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(
                    ImportInfo(
                        source=ast.get_source_segment(content, node) or "",
                        names=[alias.name],
                        is_from_import=False,
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = [alias.name for alias in node.names]
            imports.append(
                ImportInfo(
                    source=ast.get_source_segment(content, node) or "",
                    names=names,
                    is_from_import=True,
                    module=module,
                )
            )
        elif isinstance(node, ast.ClassDef):
            # Get bases as strings
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute):
                    bases.append(ast.unparse(base))

            # Get source lines (including decorators)
            start_line = node.lineno - 1
            # Check for decorators
            if node.decorator_list:
                start_line = node.decorator_list[0].lineno - 1

            end_line = node.end_lineno or node.lineno

            # Get full class source
            class_source = "\n".join(lines[start_line:end_line])

            classes.append(
                ClassInfo(
                    name=node.name,
                    source=class_source,
                    bases=bases,
                    line_start=start_line,
                    line_end=end_line,
                )
            )
        elif (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and isinstance(node.value, ast.Name)
        ):
            # Type alias: Name = Name (e.g., ConfigAttribute2 = ConfigAttribute)
            alias_name = node.targets[0].id
            target_name = node.value.id
            source = ast.get_source_segment(content, node) or ""
            type_aliases.append(
                TypeAliasInfo(
                    name=alias_name,
                    source=source,
                    target=target_name,
                )
            )

    # Fix MRO issues: remove BaseEntity from classes that inherit from entity subtypes
    # DeletableEntity, UpdatableEntity, ArchivableEntity all inherit from BaseEntity
    classes = fix_mro_issues(classes)

    # Fix string enum defaults (e.g., = "DRAFT" -> = Status7.DRAFT)
    classes = fix_string_enum_defaults(classes)

    # Fix union_mode without discriminator
    classes = fix_union_mode_without_discriminator(classes)

    # Add extra="ignore" to BaseEntity for API response tolerance (#295)
    classes = add_base_entity_extra_ignore(classes)

    # #342 cache-table transforms — emit a ``Cached<Name>`` sibling for
    # each CACHE_TABLES entry. The original API class stays pure pydantic;
    # the cache class carries SQLModel ``table=True``, primary keys, FKs,
    # relationships, and JSON columns. Order matters:
    # 1. Duplicate each CACHE_TABLES API class as a ``Cached<Name>`` copy
    #    with internal references to other cached siblings rewritten.
    # 2. Flatten intermediate-parent inheritance (e.g., ``Material(InventoryItem)``
    #    → ``CachedMaterial(ArchivableEntity)`` with InventoryItem's fields
    #    inlined) so SQLModel's column inference sees every field on the
    #    cache class itself.
    # 3. table=True + frozen=False model_config on the cached class header.
    # 4. Redeclare id with primary_key=True (depends on the model_config
    #    line placed by step 3).
    # 5. Swap AwareDatetime → datetime so SQLModel's type inference works.
    # 6. FK / relationship / JSON column / index annotations on
    #    field declarations.
    # 7. ``__fts_columns__`` ClassVar declaration for entities with FTS5
    #    search columns (Phase B's <entity>_fts virtual tables read this).
    classes = duplicate_cache_tables_as_cached_siblings(classes)
    classes = flatten_intermediate_inheritance(classes)
    classes = inject_table_annotations(classes)
    classes = inject_primary_key_in_table_classes(classes)
    classes = swap_awaredatetime_for_datetime(classes)
    classes = inject_foreign_keys(classes)
    classes = inject_relationship_fields(classes)
    classes = inject_json_columns(classes)
    classes = inject_index_annotations(classes)
    classes = inject_extra_cache_fields(classes)
    classes = inject_fts_columns(classes)
    # ``Mapped[T]`` wrap runs LAST — earlier passes match
    # ``Annotated[T, Field(...)]`` literally, and would not find their
    # targets if the type was already wrapped.
    classes = wrap_cache_fields_in_mapped(classes)

    print(
        f"  Found {len(imports)} imports, {len(classes)} classes, "
        f"and {len(type_aliases)} type aliases"
    )
    return imports, classes, type_aliases


# Entity classes that already inherit from BaseEntity
ENTITY_SUBTYPES = {
    "UpdatableEntity",
    "DeletableEntity",
    "ArchivableEntity",
    "ArchivableDeletableEntity",
}


# Base classes whose fields propagate into cache tables via inheritance.
# Their AwareDatetime annotations (created_at / updated_at / deleted_at /
# archived_at) must be swapped to plain ``datetime`` too — otherwise
# SQLModel's table-column inference on the inheriting cache class fails.
ENTITY_BASE_CLASSES: frozenset[str] = frozenset(ENTITY_SUBTYPES | {"BaseEntity"})


def fix_mro_issues(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Fix Method Resolution Order issues by removing redundant base classes.

    When a class inherits from both BaseEntity and an entity subtype (like DeletableEntity),
    we need to remove BaseEntity because the subtype already inherits from it.
    """
    fixed_classes = []

    for cls in classes:
        # Check if class has both BaseEntity and an entity subtype
        has_base_entity = "BaseEntity" in cls.bases
        has_entity_subtype = any(base in ENTITY_SUBTYPES for base in cls.bases)

        if has_base_entity and has_entity_subtype:
            # Remove BaseEntity from the inheritance list in the source
            # Handles both orderings: (BaseEntity, DeletableEntity) and (DeletableEntity, BaseEntity)
            fixed_source = re.sub(
                r"class\s+(\w+)\s*\(\s*BaseEntity\s*,\s*",
                r"class \1(",
                cls.source,
            )
            fixed_source = re.sub(
                r",\s*BaseEntity\s*\)",
                ")",
                fixed_source,
            )
            new_bases = [b for b in cls.bases if b != "BaseEntity"]
            fixed_classes.append(
                ClassInfo(
                    name=cls.name,
                    source=fixed_source,
                    bases=new_bases,
                    line_start=cls.line_start,
                    line_end=cls.line_end,
                )
            )
        else:
            fixed_classes.append(cls)

    return fixed_classes


def fix_string_enum_defaults(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Fix string defaults that should be enum values.

    datamodel-codegen sometimes generates string defaults like `= "DRAFT"` or `= "csv"`
    when it should be `= Status7.draft` or `= Format.csv` (the enum value).

    Examples of what we're fixing:
        status: Annotated[
            Status7 | None, Field(description="...")
        ] = "DRAFT"

    Should become:
        status: Annotated[
            Status7 | None, Field(description="...")
        ] = Status7.draft
    """
    fixed_classes = []
    for cls in classes:
        # Use a different approach: find the enum type first, then replace nearby string defaults
        # Step 1: Find all lines with `EnumType | None` annotations
        lines = cls.source.split("\n")
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Look for enum type in annotation (e.g., "Status7 | None")
            enum_match = re.search(r"(\w+)\s*\|\s*None", line)
            if enum_match:
                enum_type = enum_match.group(1)
                # Check if it's a valid enum-like type (starts with uppercase)
                if enum_type[0].isupper():
                    # Check if there's also a default value on this same line
                    # Case 1: `EnumType | None, ...] = "VALUE"` (all on one line)
                    same_line_match = re.search(r'\]\s*=\s*"([A-Za-z_]+)"', line)
                    if same_line_match:
                        string_value = same_line_match.group(1)
                        member_name = string_value.lower()
                        new_line = re.sub(
                            r'\]\s*=\s*"' + re.escape(string_value) + r'"',
                            f"] = {enum_type}.{member_name}",
                            line,
                        )
                        fixed_lines.append(new_line)
                        i += 1
                        continue

                    # Case 2: `EnumType | None, ...] = (` on same line, value on next line
                    paren_match = re.search(r"\]\s*=\s*\(\s*$", line)
                    if paren_match and i + 1 < len(lines):
                        next_line = lines[i + 1]
                        value_match = re.search(r'^\s*"([A-Za-z_]+)"\s*$', next_line)
                        if value_match:
                            string_value = value_match.group(1)
                            member_name = string_value.lower()
                            # Replace the whole multiline construct
                            new_line = re.sub(
                                r"\]\s*=\s*\(\s*$",
                                f"] = {enum_type}.{member_name}",
                                line,
                            )
                            fixed_lines.append(new_line)
                            # Skip the next two lines (value and closing paren)
                            i += 3
                            continue

                    # Case 3: Look ahead for the closing ] and default value on next line
                    collected = [line]
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j]
                        collected.append(next_line)
                        # Check for default value assignment on this line
                        default_match = re.search(r'\]\s*=\s*"([A-Za-z_]+)"', next_line)
                        if default_match:
                            string_value = default_match.group(1)
                            member_name = string_value.lower()
                            # Replace the string with enum value
                            new_line = re.sub(
                                r'\]\s*=\s*"' + re.escape(string_value) + r'"',
                                f"] = {enum_type}.{member_name}",
                                next_line,
                            )
                            collected[-1] = new_line
                            fixed_lines.extend(collected)
                            i = j + 1
                            break
                        # Stop looking if we hit a new field definition
                        if re.match(r"\s*\w+:\s*Annotated", next_line):
                            # No default found, keep original
                            fixed_lines.extend(collected[:-1])
                            i = j
                            break
                        j += 1
                    else:
                        # Didn't find default, keep original
                        fixed_lines.extend(collected)
                        i = j
                    continue
            fixed_lines.append(line)
            i += 1

        fixed_source = "\n".join(fixed_lines)

        fixed_classes.append(
            ClassInfo(
                name=cls.name,
                source=fixed_source,
                bases=cls.bases,
                line_start=cls.line_start,
                line_end=cls.line_end,
            )
        )

    return fixed_classes


def fix_union_mode_without_discriminator(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Remove union_mode from Field() when there's no discriminator.

    Pydantic 2 only supports union_mode for discriminated unions. When datamodel-codegen
    generates union_mode="left_to_right" without a discriminator, it causes runtime errors:
        RuntimeError: Unable to apply constraint 'union_mode' to schema of type 'model'

    This function removes union_mode from Field() calls that don't have a discriminator.

    Examples:
        Field(description="...", union_mode="left_to_right")  -> Field(description="...")
        Field(union_mode="left_to_right")                     -> Field()
    """
    fixed_classes = []
    for cls in classes:
        source = cls.source

        # Pattern to match union_mode as an argument with comma before
        source = re.sub(
            r',\s*union_mode\s*=\s*"[^"]*"(?=[,\)])',
            "",
            source,
        )
        # Pattern to match union_mode as first argument
        source = re.sub(
            r'Field\(\s*union_mode\s*=\s*"[^"]*"\s*,\s*',
            "Field(",
            source,
        )
        # Pattern to match union_mode as only argument
        source = re.sub(
            r'Field\(\s*union_mode\s*=\s*"[^"]*"\s*\)',
            "Field()",
            source,
        )

        fixed_classes.append(
            ClassInfo(
                name=cls.name,
                source=source,
                bases=cls.bases,
                line_start=cls.line_start,
                line_end=cls.line_end,
            )
        )

    return fixed_classes


def add_base_entity_extra_ignore(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Add model_config with extra='ignore' to BaseEntity.

    Response models (which inherit from BaseEntity) should tolerate extra fields
    from the Katana API, while request models keep extra='forbid' from the base.
    See: https://github.com/dougborg/katana-openapi-client/issues/295
    """
    fixed_classes = []
    for cls in classes:
        if cls.name == "BaseEntity":
            # Inject model_config after the class definition line
            source = re.sub(
                r"(class BaseEntity\([^)]+\):)\n",
                r'\1\n    model_config = ConfigDict(extra="ignore")\n\n',
                cls.source,
            )
            if source == cls.source:
                msg = (
                    "Failed to inject model_config into BaseEntity. "
                    "The class header format may have changed."
                )
                raise GenerationError(msg)
            fixed_classes.append(
                ClassInfo(
                    name=cls.name,
                    source=source,
                    bases=cls.bases,
                    line_start=cls.line_start,
                    line_end=cls.line_end,
                )
            )
        else:
            fixed_classes.append(cls)
    return fixed_classes


# ── #342 cache-table AST transforms ────────────────────────────────────────


def duplicate_cache_tables_as_cached_siblings(
    classes: list[ClassInfo],
) -> list[ClassInfo]:
    """For each CACHE_TABLES entry, emit a ``Cached<Name>`` sibling class.

    The original API class stays pure pydantic — never gets ``table=True``,
    FKs, or relationships. The cached sibling is a copy of the source with:
    - The class identifier rewritten ``<Name>`` → ``Cached<Name>``.
    - References to other cached siblings rewritten (e.g.,
      ``list[SalesOrderRow]`` → ``list[CachedSalesOrderRow]``) so a
      relationship between two cache tables wires up to the cache copies,
      not the API ones.
    - Forward-reference strings inside ``Annotated`` / type hints rewritten
      the same way (covers cases where the type appears in a string-quoted
      forward ref).

    All subsequent inject passes target the ``Cached<Name>`` copies; the
    originals are left untouched. References from non-cache classes
    (``SalesOrderListResponse.data: list[SalesOrder]``) keep pointing at
    the API classes.
    """
    # Tokenize-aware identifier rewrite so cross-cache references
    # (``Variant`` → ``CachedVariant``) skip string literals — class names
    # that are also English words (``Customer``, ``Supplier``, ``Material``,
    # ``Product``) would otherwise corrupt descriptions like ``"Customer's
    # reference number"``. See ``_rewrite_identifiers_outside_strings``.
    cached_targets = {n: _cached_name(n) for n in CACHE_TABLES}

    cached_copies: list[ClassInfo] = []
    for cls in classes:
        if cls.name not in cached_targets:
            continue
        cached_name = cached_targets[cls.name]
        # Replace the class header identifier first (single hit), then
        # rewrite remaining cross-cache references in field annotations.
        # Bases are left intact — cache classes inherit from the same base
        # entity classes (DeletableEntity, etc.) as their API siblings.
        new_source = re.sub(
            rf"^class {re.escape(cls.name)}\b",
            f"class {cached_name}",
            cls.source,
            count=1,
            flags=re.MULTILINE,
        )
        new_source = _rewrite_identifiers_outside_strings(new_source, cached_targets)
        # Strip body-level statements that the cache passes will replace
        # with their SQL-aware equivalents. Standalone classes (extending
        # ``KatanaPydanticBase`` directly rather than an entity base) emit
        # their own ``model_config = ConfigDict(extra="forbid")`` plus an
        # optional ``id`` field — both must go before ``inject_table_annotations``
        # injects ``model_config = ConfigDict(frozen=False)`` and
        # ``inject_primary_key_in_table_classes`` injects the primary-key
        # ``id`` declaration. Match both single-line and multi-line forms.
        new_source = re.sub(
            r"    model_config = ConfigDict\([^)]*\)\n",
            "",
            new_source,
        )
        # Two shapes datamodel-codegen emits for ``id``:
        #   1. ``id: Annotated[int | None, Field(description=...)] = None``
        #      (multi-line tolerant — description may wrap)
        #   2. ``id: int | None = None`` (no description on the source field)
        # Either gets stripped so ``inject_primary_key_in_table_classes`` can
        # inject the canonical primary-keyed declaration without a duplicate.
        new_source = re.sub(
            r"    id:\s*Annotated\[\s*int(?:\s*\|\s*None)?\s*,"
            r"[^]]*\][^\n]*\n",
            "",
            new_source,
            count=1,
            flags=re.DOTALL,
        )
        new_source = re.sub(
            r"    id:\s*int(?:\s*\|\s*None)?(?:\s*=\s*None)?\n",
            "",
            new_source,
            count=1,
        )
        cached_copies.append(
            ClassInfo(
                name=cached_name,
                source=new_source,
                bases=list(cls.bases),
                line_start=cls.line_start,
                line_end=cls.line_end,
            )
        )
    return classes + cached_copies


def inject_primary_key_in_table_classes(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Redeclare ``id`` on each table class with ``primary_key=True``.

    ``primary_key`` is a SQLModel-specific ``Field`` kwarg, and base.py (where
    ``BaseEntity.id`` lives) continues using ``pydantic.Field``. Redeclaring
    ``id`` directly on each ``table=True`` class lets us use ``sqlmodel.Field``
    (scoped to cache-table modules) and keep the base class untouched. Some
    generated entity classes also declare their own ``id:`` field (with a
    tailored description) that overrides ``BaseEntity.id`` — we strip that
    declaration before injecting the primary-keyed form to avoid duplicates.
    """
    cache_class_names = {_cached_name(n) for n in CACHE_TABLES}
    fixed = []
    for cls in classes:
        if cls.name not in cache_class_names:
            fixed.append(cls)
            continue
        # Strip any existing in-body `id: Annotated[int, Field(...)]`
        # declaration. Multi-line tolerant (description may wrap).
        stripped = re.sub(
            r"    id:\s*Annotated\[int,\s*Field\([^)]*\)\][^\n]*\n",
            "",
            cls.source,
            count=1,
        )
        # Insert the canonical primary-keyed id right after model_config.
        # Uses SQLField (sqlmodel.Field alias) for the SQL-specific
        # ``primary_key`` kwarg; pydantic.Field doesn't accept it.
        id_line = (
            "    id: Annotated[int, SQLField(primary_key=True, "
            'description="Unique identifier")]\n'
        )
        new_source, n = re.subn(
            r"(model_config = ConfigDict\(frozen=False\)\n\n)",
            rf"\1{id_line}\n",
            stripped,
            count=1,
        )
        if n != 1:
            msg = (
                f"Failed to inject primary-key id on {cls.name}. "
                "model_config line may be missing or differently formatted."
            )
            raise GenerationError(msg)
        fixed.append(cls.with_source(new_source))
    return fixed


def inject_table_annotations(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Turn CACHE_TABLES entries into SQLModel tables.

    Three rewrites per class, emitted in order as the first body statements:
    1. Append ``, table=True`` to the class header bases list.
    2. Insert ``__tablename__`` set to the snake_case class name. Otherwise
       SQLAlchemy defaults to the raw lowercase class name (``salesorder``
       vs. ``sales_order``), which breaks FK references that use the
       readable snake_case form.
    3. Insert ``model_config = ConfigDict(frozen=False)``. SQLAlchemy's ORM
       mutates instances during session operations; the inherited
       ``frozen=True`` from ``KatanaPydanticBase`` would otherwise raise on
       every attribute write.
    """
    cache_class_names = {_cached_name(n) for n in CACHE_TABLES}
    fixed = []
    for cls in classes:
        if cls.name not in cache_class_names:
            fixed.append(cls)
            continue
        # ``__tablename__`` is the snake_case of the *original* (un-prefixed)
        # entity name so FK references like ``sales_order.id`` resolve
        # correctly — both API consumers and cache code think of the table
        # as "sales_order", not "cached_sales_order".
        tablename = _snake_case(cls.name.removeprefix("Cached"))
        # Single pass: append `, table=True` to the class bases and inject
        # __tablename__ + model_config as the first body statements.
        new_source, n = re.subn(
            rf"^(class {re.escape(cls.name)}\([^)]*)\):\n",
            (
                r"\1, table=True):" + "\n"
                rf'    __tablename__ = "{tablename}"' + "\n"
                r"    model_config = ConfigDict(frozen=False)" + "\n\n"
            ),
            cls.source,
            count=1,
            flags=re.MULTILINE,
        )
        if n != 1:
            msg = (
                f"Failed to inject table annotations (table=True, "
                f"__tablename__, model_config) into {cls.name}. "
                "The class-declaration shape may have changed."
            )
            raise GenerationError(msg)
        fixed.append(cls.with_source(new_source))
    return fixed


def inject_foreign_keys(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Add ``foreign_key="<parent_table>.id"`` to child cache-row FK columns.

    Two cases:
    1. The API model already carries the FK field (e.g.,
       ``SalesOrderRow.sales_order_id`` — Katana returns it). Rewrite the
       existing ``Field(...)`` call to ``SQLField(foreign_key=..., ...)``.
    2. The API model lacks the field because Katana doesn't return one
       (e.g., ``StockAdjustmentRow``: rows are nested under the parent on
       the wire, no back-pointer). Insert a fresh ``SQLField`` declaration
       — the FK is a cache-only column, populated by SQLAlchemy when the
       parent's relationship is set on ``session.merge``.

    Either way we operate exclusively on the ``Cached<Name>`` siblings;
    the API class never gets a SQL-specific kwarg or a synthetic FK field.
    """
    # Map cache-class → list of (fk_field, parent_tablename). Lookup uses
    # the cached name (``CachedSalesOrderRow``) since the API class
    # (``SalesOrderRow``) is excluded from cache transforms.
    by_child: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for rel in CACHE_RELATIONSHIPS:
        by_child[_cached_name(rel.child)].append((rel.child_fk_field, rel.parent_table))

    fixed = []
    for cls in classes:
        if cls.name not in by_child:
            fixed.append(cls)
            continue
        new_source = cls.source
        for fk_field, parent_table in by_child[cls.name]:
            # Rewrite `Field(` → `SQLField(` AND inject foreign_key kwarg.
            # pydantic.Field doesn't accept ``foreign_key``; the dual-import
            # scheme keeps pydantic.Field for normal validation fields and
            # uses sqlmodel.Field (aliased SQLField) for SQL-specific ones.
            pattern = (
                rf"({re.escape(fk_field)}:\s*Annotated\[\s*int\s*\|\s*None,"
                r"\s*)Field\(\s*(description=)"
            )
            replacement = rf'\1SQLField(foreign_key="{parent_table}.id", \2'
            new_source, n = re.subn(pattern, replacement, new_source, count=1)
            if n == 0:
                # Field doesn't exist in the API model — insert a fresh
                # cache-only declaration after the model_config block. This
                # is the StockAdjustmentRow / PurchaseOrderRow / StockTransferRow
                # case: Katana doesn't return the parent FK on row objects;
                # we synthesize the column so SQLAlchemy can wire the
                # parent→child relationship on insert.
                fk_line = (
                    f"    {fk_field}: Annotated[\n"
                    f"        int | None,\n"
                    f"        SQLField(\n"
                    f'            foreign_key="{parent_table}.id",\n'
                    f'            description="(cache-only) ID of the parent '
                    f'row, populated by SQLAlchemy on insert.",\n'
                    f"        ),\n"
                    f"    ] = None\n"
                )
                new_source, n = re.subn(
                    r"(model_config = ConfigDict\(frozen=False\)\n\n)",
                    rf"\1{fk_line}\n",
                    new_source,
                    count=1,
                )
                if n != 1:
                    msg = (
                        f"Failed to insert synthesized foreign_key "
                        f"{cls.name}.{fk_field}. Expected model_config "
                        "block on the cache class."
                    )
                    raise GenerationError(msg)
                continue
            if n != 1:
                msg = (
                    f"Failed to inject foreign_key on {cls.name}.{fk_field}. "
                    "Expected Annotated[int | None, Field(description=...)] shape."
                )
                raise GenerationError(msg)
        fixed.append(cls.with_source(new_source))
    return fixed


def inject_relationship_fields(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Rewrite parent list fields as ``Relationship()`` and add child back-refs.

    Operates on the ``Cached<Name>`` siblings only — both sides of the
    relationship reference cached classes so the SQLAlchemy graph doesn't
    cross over into the pure-pydantic API surface.

    For each declared parent→child relationship:
    - Parent (``Cached<Parent>``): the ``Annotated[list[Child] | None,
      Field(...)] = None`` field — note the inner type was rewritten to
      ``Cached<Child>`` by ``duplicate_cache_tables_as_cached_siblings``
      — becomes ``parent_field: list["Cached<Child>"] = Relationship(
      back_populates="child_back_ref")``.
    - Child (``Cached<Child>``): a new ``child_back_ref:
      Optional["Cached<Parent>"] = Relationship(back_populates="parent_field")``
      field is appended to the class body.
    """
    by_parent = {_cached_name(rel.parent): rel for rel in CACHE_RELATIONSHIPS}
    by_child = {_cached_name(rel.child): rel for rel in CACHE_RELATIONSHIPS}

    fixed = []
    for cls in classes:
        new_source = cls.source

        # Parent side: replace the list field with Relationship(). The inner
        # type was rewritten to ``Cached<Child>`` during duplication, so the
        # match pattern uses the cached child name.
        #
        # ``cache_only_parent_field=True`` means the API model never had a
        # nested children field — append a fresh Relationship descriptor at
        # the end of the class body instead of rewriting one in place.
        if cls.name in by_parent:
            rel = by_parent[cls.name]
            cached_child = _cached_name(rel.child)
            if rel.cache_only_parent_field:
                rel_line = (
                    f'    {rel.parent_field}: list["{cached_child}"] = '
                    f'Relationship(back_populates="{rel.child_back_ref}")\n'
                )
                new_source = new_source.rstrip() + "\n" + rel_line
            else:
                pattern = (
                    rf"{re.escape(rel.parent_field)}:\s*Annotated\[\s*"
                    rf"list\[{re.escape(cached_child)}\]\s*\|\s*None,\s*"
                    r"Field\([^)]*\),?\s*\]\s*=\s*None"
                )
                replacement = (
                    f'{rel.parent_field}: list["{cached_child}"] = '
                    f'Relationship(back_populates="{rel.child_back_ref}")'
                )
                new_source, n = re.subn(pattern, replacement, new_source, count=1)
                if n != 1:
                    msg = (
                        f"Failed to rewrite list relationship on "
                        f"{cls.name}.{rel.parent_field}. Expected shape "
                        f"`Annotated[list[{cached_child}] | None, Field(...)] = None`."
                    )
                    raise GenerationError(msg)

        # Child side: append back-reference field at end of class body.
        if cls.name in by_child:
            rel = by_child[cls.name]
            cached_parent = _cached_name(rel.parent)
            # SA's ``relationship()`` string-form resolution can't parse
            # ``"Cached<Parent> | None"``. Use ``Optional["Cached<Parent>"]``
            # so the outer Optional[] is evaluated at class-def time and only
            # the inner ``"Cached<Parent>"`` stays as a forward reference.
            backref_line = (
                f'    {rel.child_back_ref}: Optional["{cached_parent}"] = '
                f'Relationship(back_populates="{rel.parent_field}")\n'
            )
            new_source = new_source.rstrip() + "\n" + backref_line

        if new_source != cls.source:
            fixed.append(cls.with_source(new_source))
        else:
            fixed.append(cls)
    return fixed


def swap_awaredatetime_for_datetime(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Rewrite ``AwareDatetime`` as ``datetime`` in cache-table fields.

    SQLModel's automatic column-type inference has a hardcoded list of
    recognized Python types and does not know about pydantic's
    ``AwareDatetime`` (a pydantic-specific wrapper, not a ``datetime``
    subclass). Without this swap, defining a ``table=True`` class that
    inherits or declares an ``AwareDatetime`` field raises
    ``ValueError: AwareDatetime has no matching SQLAlchemy type`` at
    class-definition time.

    Applies to ``Cached<Name>`` siblings *and* to the shared entity base
    classes (BaseEntity, UpdatableEntity, DeletableEntity, etc.) — their
    datetime fields are inherited by cache tables, so they too must speak
    plain ``datetime``. The pure-pydantic API classes are unaffected, but
    swapping their inherited base ripples into them — that's accepted
    since timezone awareness is a Katana wire-protocol invariant; the
    extra pydantic validator was safety belt for data we already trust.
    """
    swap_targets = {_cached_name(n) for n in CACHE_TABLES} | ENTITY_BASE_CLASSES
    fixed = []
    for cls in classes:
        if cls.name not in swap_targets:
            fixed.append(cls)
            continue
        # Word-boundary swap: "AwareDatetime" → "datetime" in field
        # annotations only within the targeted classes.
        new_source = re.sub(r"\bAwareDatetime\b", "datetime", cls.source)
        if new_source == cls.source:
            fixed.append(cls)
            continue
        fixed.append(cls.with_source(new_source))
    return fixed


def inject_extra_cache_fields(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Append ``CacheTableSpec.extra_fields`` declarations to the cache class body.

    For discriminated-union roots (PurchaseOrderBase) cached as a single
    SQL table, this hoists subclass-only fields onto the cache class so
    queries can filter by them without a UNION across two tables. The
    converter copies the values from the API subclass instance.

    Inserts each declaration line at the end of the class body. Plain
    pydantic ``Field`` annotation is sufficient — SQLModel infers the
    column type from the annotation. ``Optional`` types stay nullable on
    the column.
    """
    cached_extras = {
        _cached_name(name): spec.extra_fields
        for name, spec in CACHE_TABLES.items()
        if spec.extra_fields
    }
    fixed = []
    for cls in classes:
        extras = cached_extras.get(cls.name)
        if not extras:
            fixed.append(cls)
            continue
        rendered = "\n".join(extra.render() for extra in extras)
        new_source = cls.source.rstrip() + "\n" + rendered + "\n"
        fixed.append(cls.with_source(new_source))
    return fixed


def wrap_cache_fields_in_mapped(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Wrap each cache class's field types in ``Mapped[...]``.

    Lets foundation-file query call sites use ``CachedX.field.in_(...)``
    without ``sqlmodel.col()`` wrappers — type checkers see ``Mapped[T]``
    (which exposes ``.in_/.is_/.desc/.ilike``), while the runtime
    ``Mapped`` shim makes ``Mapped[T]`` reduce to ``T`` so
    SQLModel + pydantic schema generation is unaffected.

    Operates on both ``Cached*`` siblings *and* the shared entity base
    classes (BaseEntity, UpdatableEntity, DeletableEntity, etc.) because
    ``Cached*`` inherits ``id`` / ``created_at`` / ``updated_at`` /
    ``deleted_at`` / ``archived_at`` from those bases. Wrapping only the
    Cached classes would leave the inherited fields as bare ``T`` from
    the type checker's point of view — and those are exactly the fields
    most query call sites filter on. The API classes that share the same
    bases are unaffected at runtime (Mapped → identity) and only see
    ``Mapped[T]`` typing on class-level attribute access, which no API
    consumer relies on (instance-level access stays as ``T`` per
    pydantic's normal field handling).

    Must run **after** all field-rewrite passes (``inject_primary_key``,
    ``inject_foreign_keys``, ``inject_json_columns``,
    ``inject_relationship_fields``, ``inject_extra_cache_fields``).
    Those passes match ``Annotated[T, Field(...)]`` literally; running
    this wrap before them would leave them unable to find their targets.
    """
    target_class_names = {_cached_name(n) for n in CACHE_TABLES} | ENTITY_BASE_CLASSES
    # Match 1: ``Annotated[<type>,`` — wraps the column-field type. Type
    # captures any chars that aren't ``,[]`` PLUS up to two levels of
    # balanced brackets, covering ``list["X"]``, ``dict[str, list[int]]``,
    # ``Optional[list["X"]]``. Multi-line tolerant; relationship fields
    # (no ``Annotated[`` shape) are naturally skipped. Three-level nesting
    # is not handled — see the post-substitution assertion below.
    inner_balanced = r"(?:[^\[\]]|\[[^\[\]]*\])*"
    annotated_pattern = re.compile(
        rf"(Annotated\[\s*)((?:[^,\[\]]|\[{inner_balanced}\])+?)(\s*,)"
    )
    # Match 2: relationship-field annotations of shape
    # ``    name: <type> = Relationship(...)`` — wraps the relationship
    # type so ``selectinload(Cached*.<rel>)`` type-checks without a
    # ``cast(QueryableAttribute, ...)``. SQLAlchemy 2.0 docs canonically
    # type relationships as ``Mapped[List[X]]`` / ``Mapped[Optional[X]]``,
    # so this brings the generated form into line.
    relationship_pattern = re.compile(
        rf"(^\s+\w+:\s+)((?:[^=\n\[\]]|\[{inner_balanced}\])+?)(\s*=\s*Relationship\()",
        re.MULTILINE,
    )
    # Match 3: bare ``    name: <type> = <default>`` and
    # ``    name: <type>`` declarations — datamodel-codegen emits these
    # for properties without a description (e.g., ``Variant.type:
    # VariantType | None = None``). Without wrapping, class-level access
    # ``CachedVariant.type.in_(...)`` doesn't type-check consistently
    # with the rest of the cached fields. Excludes the relationship case
    # already handled by Match 2 (``= Relationship(``) and dunder fields
    # (``__tablename__``, ``__fts_columns__``).
    bare_field_pattern = re.compile(
        rf"(^    (?!__)\w+:\s+)"
        rf"(?!Mapped\[|Annotated\[)"
        rf"((?:[^=\n\[\]]|\[{inner_balanced}\])+?)"
        rf"(\s*(?:=(?!\s*Relationship\()|$))",
        re.MULTILINE,
    )
    # Safety net: any ``Annotated[`` that survives substitution without
    # ``Mapped[`` immediately inside is a missed wrap (e.g., a field
    # whose type uses bracket nesting deeper than the regex handles).
    # Crash loud rather than emit silently-untyped class fields.
    # ``\s*+`` is the atomic (no-backtrack) variant; without it the
    # negative lookahead would let the engine reconsider shorter
    # whitespace runs and falsely match already-wrapped fields.
    unwrapped_annotated = re.compile(r"\bAnnotated\[\s*+(?!Mapped\[)")
    fixed = []
    for cls in classes:
        if cls.name not in target_class_names:
            fixed.append(cls)
            continue
        new_source = annotated_pattern.sub(r"\1Mapped[\2]\3", cls.source)
        new_source = relationship_pattern.sub(r"\1Mapped[\2]\3", new_source)
        new_source = bare_field_pattern.sub(r"\1Mapped[\2]\3", new_source)
        if unwrapped_annotated.search(new_source):
            sample = unwrapped_annotated.search(new_source)
            assert sample is not None  # for type-checkers
            line_no = new_source.count("\n", 0, sample.start()) + 1
            msg = (
                f"wrap_cache_fields_in_mapped: missed an Annotated[ "
                f"on {cls.name} (line {line_no} of class body). The "
                f"field's type likely has nesting deeper than the "
                f"two-level regex handles — extend ``inner_balanced`` "
                f"or refactor the field shape."
            )
            raise GenerationError(msg)
        fixed.append(cls.with_source(new_source))
    return fixed


# Class-body field declarations look like ``    name: <type>`` at exactly
# 4-space indent. Match the leading whitespace + identifier + colon so we
# don't catch nested ``Annotated[..., Field(...)]`` lines that also contain
# ``:``. Multi-line tolerant: matches the first line of a multi-line
# ``Annotated[...]`` declaration. ``\s*$|\s*[^A-Za-z_]`` after the colon
# rules out e.g. ``__tablename__:`` (no space prefix anyway, but defensive).
_FIELD_DECLARATION_HEAD = re.compile(
    r"^    ([A-Za-z_][A-Za-z0-9_]*)\s*:",
    re.MULTILINE,
)


def _extract_field_names(class_body: str) -> set[str]:
    """Return the set of top-level field names declared on a class body.

    Used by ``flatten_intermediate_inheritance`` to detect when a child
    class redeclares a parent's field — the cache class can only carry
    one column per name, and the parent's typed declaration usually wins
    (the child's override is often a discriminator narrowing like
    ``Literal["material"]`` that SQLModel can't map to a column).

    Skips dunder names (``__tablename__``) so the set really is field-only.
    """
    names: set[str] = set()
    for match in _FIELD_DECLARATION_HEAD.finditer(class_body):
        name = match.group(1)
        if name.startswith("__"):
            continue
        names.add(name)
    return names


def _strip_field_declaration(class_body: str, field_name: str) -> str:
    """Remove a top-level field declaration (header + continuation lines).

    Field declarations span one or more lines:
    - Single-line: ``    name: int = 0``
    - Multi-line (``Annotated[...]``):
      ::

          name: Annotated[
              int,
              Field(...),
          ] = None

    Strips from the first line whose 4-space indent + identifier matches
    ``field_name`` through the next blank line OR the next field
    declaration head. Preserves all other content.
    """
    lines = class_body.split("\n")
    out_lines: list[str] = []
    skipping = False
    for line in lines:
        head_match = _FIELD_DECLARATION_HEAD.match(line)
        if head_match and head_match.group(1) == field_name:
            skipping = True
            continue
        if skipping:
            # Stop skipping when we see the next field declaration head
            # OR a class-level statement at column 0 (rare but possible).
            if head_match and head_match.group(1) != field_name:
                skipping = False
                out_lines.append(line)
                continue
            # Also stop on lines that are clearly outside the class body
            # (top-level statements at column 0).
            if line and not line[0].isspace():
                skipping = False
                out_lines.append(line)
                continue
            # Otherwise still inside the multi-line continuation — skip.
            continue
        out_lines.append(line)
    return "\n".join(out_lines)


def flatten_intermediate_inheritance(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Inline an intermediate parent class's fields into the cache class body.

    Some catalog API classes inherit from a non-base, non-cached
    *intermediate* class — e.g., ``Material(InventoryItem)`` where
    ``InventoryItem`` declares nested-list fields (``variants``,
    ``configs``, ``supplier``) that SQLModel's column inference can't
    auto-map. Just leaving the cache class as ``CachedMaterial(InventoryItem)``
    and ``table=True`` raises ``ValueError: <class 'list'> has no
    matching SQLAlchemy type`` at class-definition time.

    The flatten pass:

    1. Reads ``CacheTableSpec.flatten_parent`` (e.g., ``"InventoryItem"``).
    2. Looks up the parent class's source.
    3. Extracts the parent body (everything after the class header and
       any ``model_config = ConfigDict(...)`` declaration).
    4. Inlines the parent body fields at the top of the cache class body
       (just below the cache class header).
    5. Rewrites the cache class's bases list, replacing the intermediate
       parent with the parent's own bases (e.g., ``InventoryItem`` →
       ``ArchivableEntity``).

    The injected fields then look just like body-declared ones to all
    downstream passes (``inject_json_columns``, etc.), so a
    ``json_columns=("variants", ...)`` entry on ``CacheTableSpec`` lands
    correctly.

    References to other cache classes inside the inlined fields go
    through ``_rewrite_identifiers_outside_strings`` (same as the
    duplicate pass) — e.g., ``InventoryItem.variants: list[Variant]``
    becomes ``list[CachedVariant]`` on the cache class.
    """
    cached_targets = {n: _cached_name(n) for n in CACHE_TABLES}
    flatten_specs = {
        _cached_name(name): spec.flatten_parent
        for name, spec in CACHE_TABLES.items()
        if spec.flatten_parent is not None
    }
    if not flatten_specs:
        return classes

    by_name = {cls.name: cls for cls in classes}

    fixed = []
    for cls in classes:
        parent_name = flatten_specs.get(cls.name)
        if parent_name is None:
            fixed.append(cls)
            continue
        parent_cls = by_name.get(parent_name)
        if parent_cls is None:
            msg = (
                f"flatten_intermediate_inheritance: cannot find parent class "
                f"{parent_name!r} for {cls.name}. Check spelling in "
                f"CacheTableSpec.flatten_parent."
            )
            raise GenerationError(msg)

        # Identify which fields the child class itself declares — we'll
        # need to de-dup. When the child overrides a parent field
        # (e.g., ``Material.type: Literal["material"]`` overrides
        # ``InventoryItem.type: InventoryItemType``), we keep the parent's
        # declaration on the cache class because SQLModel can't map
        # ``Literal[...]`` to a column type, while the parent's enum/scalar
        # type maps cleanly. Strip the child's overriding declaration from
        # ``cls.source`` after flattening.
        child_field_names = _extract_field_names(cls.source)

        # Extract the parent's body — everything after the class header.
        # Strip any ``model_config = ConfigDict(...)`` declaration (we keep
        # the cache class's own model_config from inject_table_annotations)
        # and any ``id`` field (the cache class redeclares it as a primary
        # key via inject_primary_key_in_table_classes).
        parent_lines = parent_cls.source.split("\n")
        parent_body_lines: list[str] = []
        in_model_config = False
        for line in parent_lines:
            stripped = line.lstrip()
            # Skip the class header line.
            if stripped.startswith("class "):
                continue
            # Skip model_config declarations (single-line and multi-line).
            if "model_config" in stripped and "ConfigDict" in stripped:
                if line.rstrip().endswith(")"):
                    continue
                in_model_config = True
                continue
            if in_model_config:
                if stripped.endswith(")"):
                    in_model_config = False
                continue
            parent_body_lines.append(line)

        # Drop any leading/trailing blank lines so the inlined block sits
        # cleanly above the cache class's own body.
        parent_body = "\n".join(parent_body_lines).strip("\n")
        # Rewrite cross-cache references (e.g., ``list[Variant]`` →
        # ``list[CachedVariant]``) so JSON-column injection on inlined
        # fields lands on the cache-aware types. Tokenize-aware so
        # descriptions that mention class names as English words don't get
        # corrupted — see ``_rewrite_identifiers_outside_strings``.
        parent_body = _rewrite_identifiers_outside_strings(parent_body, cached_targets)

        # Identify parent-declared field names so we can strip the child's
        # overriding declarations (kept the parent's instead). Without
        # this, ``Material.type: Literal["material"]`` survives alongside
        # the inlined ``InventoryItem.type: InventoryItemType`` and
        # SQLModel raises on the ambiguous duplicate (and on Literal[...]
        # which it can't map to a column type).
        parent_field_names = _extract_field_names(parent_body)
        overriding_fields = child_field_names & parent_field_names

        child_source = cls.source
        for field_name in overriding_fields:
            child_source = _strip_field_declaration(child_source, field_name)

        # Replace the parent name in the cache class header with the
        # parent's own bases. Preserves the ``Cached<Name>(<base>...):``
        # shape so inject_table_annotations can append ``, table=True``
        # and inject the body header lines.
        parent_bases_str = (
            ", ".join(parent_cls.bases) if parent_cls.bases else "BaseEntity"
        )
        new_source, n = re.subn(
            rf"^(class {re.escape(cls.name)}\()[^)]+(\):)",
            rf"\1{parent_bases_str}\2",
            child_source,
            count=1,
            flags=re.MULTILINE,
        )
        if n != 1:
            msg = (
                f"flatten_intermediate_inheritance: failed to rewrite class "
                f"header bases on {cls.name}. Expected single header line."
            )
            raise GenerationError(msg)

        # Insert the parent body right after the cache class header.
        # The cache class header was just rewritten; locate it again to
        # inject the inlined fields immediately below. ``parent_body``
        # contains string literals with ``\n`` escape sequences (literal
        # backslash-n character pairs); ``re.escape`` would leave those
        # alone, but ``re.sub``'s replacement-string parser would still
        # interpret them. Use ``re.sub``'s callable form so the body is
        # treated as raw text — the lambda returns the captured header
        # plus the body verbatim.
        body_with_trailing = parent_body + "\n"
        new_source, n = re.subn(
            rf"^(class {re.escape(cls.name)}\([^)]*\):\n)",
            lambda m, _body=body_with_trailing: m.group(1) + _body,
            new_source,
            count=1,
            flags=re.MULTILINE,
        )
        if n != 1:
            msg = (
                f"flatten_intermediate_inheritance: failed to inline parent "
                f"body on {cls.name}. Header may have an unexpected shape."
            )
            raise GenerationError(msg)

        # Cache class's own bases also flip — propagate to the ClassInfo
        # so downstream passes / classify_class see the new bases.
        fixed.append(
            ClassInfo(
                name=cls.name,
                source=new_source,
                bases=list(parent_cls.bases),
                line_start=cls.line_start,
                line_end=cls.line_end,
            )
        )
    return fixed


def inject_index_annotations(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Add ``index=True`` to fields per the cache spec.

    Reads ``CacheTableSpec.index_columns`` and rewrites the matching
    ``Field(...)`` declarations to ``SQLField(index=True, ...)`` preserving
    description. Mirrors the legacy ``CatalogCache``'s plain indexes (e.g.,
    ``idx_entity_sku ON entity_index(sku COLLATE NOCASE)``); the NOCASE
    collation is applied at query time by the Phase B adapter, not on the
    column itself.

    Two cases mirror ``inject_foreign_keys``:

    - Field already declares ``Field(...)``: rewrite to ``SQLField(...)``
      preserving description.
    - Field already declares ``SQLField(...)``: insert ``index=True`` as a
      leading kwarg (covers the case where ``inject_json_columns`` already
      rewrote the field — symmetric/safe).

    Operates on ``Cached<Name>`` siblings only.
    """
    column_specs: dict[str, tuple[str, ...]] = {
        _cached_name(name): spec.index_columns
        for name, spec in CACHE_TABLES.items()
        if spec.index_columns
    }

    fixed = []
    for cls in classes:
        fields = column_specs.get(cls.name)
        if not fields:
            fixed.append(cls)
            continue
        new_source = cls.source
        for field_name in fields:
            # Case 1: the field still uses ``Field(`` (no prior rewrite).
            pattern_pydantic = (
                rf"({re.escape(field_name)}:\s*Annotated\[\s*[^,]+,\s*)"
                r"Field\(\s*(description=)"
            )
            replacement_pydantic = r"\1SQLField(index=True, \2"
            new_source, n = re.subn(
                pattern_pydantic, replacement_pydantic, new_source, count=1
            )
            if n == 1:
                continue
            # Case 2: a prior pass already rewrote to ``SQLField(...)`` —
            # inject ``index=True`` as a leading kwarg (idempotent: skip
            # if already present so a re-run doesn't double-add).
            pattern_sqlfield = (
                rf"({re.escape(field_name)}:\s*Annotated\[\s*[^,]+,\s*)"
                r"SQLField\(\s*(?!index=)"
            )
            replacement_sqlfield = r"\1SQLField(index=True, "
            new_source, n = re.subn(
                pattern_sqlfield, replacement_sqlfield, new_source, count=1
            )
            if n != 1:
                msg = (
                    f"Failed to inject index annotations on "
                    f"{cls.name}.{field_name}. Field shape may have "
                    "changed, or the column name doesn't match a "
                    "declared field."
                )
                raise GenerationError(msg)
        fixed.append(cls.with_source(new_source))
    return fixed


def inject_fts_columns(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Emit ``__fts_columns__: ClassVar[tuple[str, ...]] = (...)``.

    For each ``Cached<Name>`` class with an entry in ``CACHE_FTS_SPECS``,
    declares a class-level constant naming the columns Phase B's
    ``<entity>_fts`` virtual table will index. The runtime invariant:
    every column listed must exist on ``Cached<Name>.__table__.columns``
    (Phase B will assert this at engine open).

    The declaration sits right below ``__tablename__`` so a reader can see
    the table identity and FTS contract together at the top of the class
    body. ``ClassVar`` ensures pydantic and SQLModel skip it during field
    enumeration — it's metadata, not a column.
    """
    cached_fts_specs = {
        _cached_name(name): cols for name, cols in CACHE_FTS_SPECS.items()
    }
    fixed = []
    for cls in classes:
        cols = cached_fts_specs.get(cls.name)
        if not cols:
            fixed.append(cls)
            continue
        cols_str = ", ".join(repr(c) for c in cols)
        fts_line = f"    __fts_columns__: ClassVar[tuple[str, ...]] = ({cols_str},)\n"
        # Insert right after ``__tablename__ = "..."``. inject_table_annotations
        # places that line; this pass runs after, so the line is present.
        new_source, n = re.subn(
            r'(__tablename__ = "[^"]+"\n)',
            rf"\1{fts_line}",
            cls.source,
            count=1,
        )
        if n != 1:
            msg = (
                f"inject_fts_columns: failed to find __tablename__ on "
                f"{cls.name}. inject_table_annotations may not have run "
                "yet, or the format has changed."
            )
            raise GenerationError(msg)
        fixed.append(cls.with_source(new_source))
    return fixed


def inject_json_columns(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Annotate specified list fields with ``sa_column=Column(JSON)``.

    For fields in ``CacheTableSpec.json_columns`` — typically lists of
    polymorphic or non-cached nested models — this preserves the typed
    pydantic interface while telling SQLAlchemy to store them as JSON rather
    than attempting to normalize them into child tables. Operates on the
    ``Cached<Name>`` siblings: spec keys are user-facing API names so the
    cached lookup converts via ``_cached_name``.

    Handles two field shapes:

    1. ``Annotated[T, Field(description=...)]`` — the common datamodel-codegen
       output. Rewrites ``Field(`` to ``SQLField(sa_column=Column(PydanticJSON), ``.
    2. ``name: T = Default`` (no ``Annotated``, no ``Field``) — emitted by
       datamodel-codegen for classes without a description on the property
       (e.g., ``Location.address: LocationAddress | None = None``). Wraps
       in ``Annotated[T, SQLField(sa_column=Column(PydanticJSON))]``.
    """
    cached_json_columns = {
        _cached_name(name): spec.json_columns
        for name, spec in CACHE_TABLES.items()
        if spec.json_columns
    }
    fixed = []
    for cls in classes:
        fields = cached_json_columns.get(cls.name)
        if not fields:
            fixed.append(cls)
            continue
        new_source = cls.source
        for field_name in fields:
            # Case 1: Annotated[T, Field(description=...)] — most common.
            # Rewrite `Field(` → `SQLField(` AND inject sa_column=Column(JSON).
            # pydantic.Field doesn't accept ``sa_column``; SQLField does.
            #
            # ``[^\[\]]|\[[^\[\]]*\]`` matches a non-bracket char OR a
            # single-level bracket pair, so ``dict[str, Any] | None`` (with
            # an inner comma) is captured fully. This is the same balanced
            # pattern ``wrap_cache_fields_in_mapped`` uses; the ``,\s*Field(``
            # delimiter terminates the type group at the right comma.
            pattern_field = (
                rf"({re.escape(field_name)}:\s*Annotated\[\s*"
                rf"(?:[^\[\]]|\[[^\[\]]*\])+?,\s*)Field\(\s*(description=)"
            )
            replacement_field = r"\1SQLField(sa_column=Column(PydanticJSON), \2"
            new_source, n = re.subn(
                pattern_field, replacement_field, new_source, count=1
            )
            if n == 1:
                continue
            # Case 2: bare ``name: T = Default`` (no Annotated, no Field) —
            # datamodel-codegen omits Annotated when the property has no
            # description. Wrap in ``Annotated[T, SQLField(sa_column=...)]``.
            # Multi-line tolerant since the type annotation may be a long
            # union split across lines (rare but possible).
            pattern_bare = (
                rf"^(\s+){re.escape(field_name)}:\s*([^=\n]+?)(\s*=\s*[^\n]+)$"
            )
            replacement_bare = (
                rf"\1{field_name}: Annotated["
                rf"\2, SQLField(sa_column=Column(PydanticJSON))]\3"
            )
            new_source, n = re.subn(
                pattern_bare,
                replacement_bare,
                new_source,
                count=1,
                flags=re.MULTILINE,
            )
            if n != 1:
                msg = (
                    f"Failed to inject JSON sa_column on "
                    f"{cls.name}.{field_name}. Field shape may have changed."
                )
                raise GenerationError(msg)
        fixed.append(cls.with_source(new_source))
    return fixed


def classify_class(class_name: str) -> str:
    """Determine which domain group a class belongs to.

    Exact matches are checked first (across all groups) before prefix matches.
    This ensures that explicit class names take priority over wildcard patterns.
    Cached siblings (``Cached<Name>``) classify under the same group as
    their underlying API class, so cache classes co-locate in the same
    module file as the model they shadow.
    """
    effective_name = class_name.removeprefix("Cached")

    # First pass: check for exact matches across all groups
    for group_name, patterns in DOMAIN_GROUPS.items():
        for pattern in patterns:
            if not pattern.endswith("*") and effective_name == pattern:
                return group_name

    # Second pass: check for prefix matches
    for group_name, patterns in DOMAIN_GROUPS.items():
        for pattern in patterns:
            # Prefix match: pattern ends with * and class_name starts with pattern prefix
            if pattern.endswith("*") and effective_name.startswith(pattern[:-1]):
                return group_name
    return "common"


def group_classes(
    classes: list[ClassInfo],
    type_aliases: list[TypeAliasInfo],
) -> tuple[dict[str, list[ClassInfo]], dict[str, list[TypeAliasInfo]]]:
    """Group classes and type aliases by domain."""
    print("Grouping classes by domain...")

    class_groups: dict[str, list[ClassInfo]] = defaultdict(list)
    alias_groups: dict[str, list[TypeAliasInfo]] = defaultdict(list)

    # Build class name to module mapping first
    class_to_module: dict[str, str] = {}
    for cls in classes:
        group = classify_class(cls.name)
        class_groups[group].append(cls)
        class_to_module[cls.name] = group

    # Place type aliases in the same module as their target class
    for alias in type_aliases:
        target_module = class_to_module.get(alias.target, "common")
        alias_groups[target_module].append(alias)

    for group, cls_list in sorted(class_groups.items()):
        alias_count = len(alias_groups.get(group, []))
        extra = f" + {alias_count} aliases" if alias_count else ""
        print(f"  {group}: {len(cls_list)} classes{extra}")

    return dict(class_groups), dict(alias_groups)


def build_class_to_module_map(
    class_groups: dict[str, list[ClassInfo]],
    alias_groups: dict[str, list[TypeAliasInfo]],
) -> dict[str, str]:
    """Build a mapping from class name (and alias name) to module name."""
    mapping = {}
    for module_name, classes in class_groups.items():
        for cls in classes:
            mapping[cls.name] = module_name
    for module_name, aliases in alias_groups.items():
        for alias in aliases:
            mapping[alias.name] = module_name
    return mapping


def generate_module_imports(
    imports: list[ImportInfo],
    classes: list[ClassInfo],
    class_to_module: dict[str, str],
    current_module: str,
) -> str:
    """Generate import statements for a module file."""
    import_lines: list[str] = []

    # #342: cache-table modules drop ``from __future__ import annotations``
    # (SQLAlchemy's relationship type resolution needs live type objects),
    # keep ``pydantic.Field`` (for original validation kwargs like ``pattern``
    # and ``examples`` which ``sqlmodel.Field`` rejects), and additionally
    # import ``sqlmodel.Field`` aliased as ``SQLField`` for SQL-specific
    # kwargs (``primary_key``, ``foreign_key``, ``sa_column``). All
    # generator-injected field declarations use ``SQLField``; original
    # datamodel-codegen output keeps ``Field`` from pydantic.
    classes_in_module = {cls.name for cls in classes}
    cached_class_names = {_cached_name(n) for n in CACHE_TABLES}
    has_cache_tables = bool(classes_in_module & cached_class_names)
    cached_json_class_names = {
        _cached_name(name) for name, spec in CACHE_TABLES.items() if spec.json_columns
    }
    has_json_columns = any(cls.name in cached_json_class_names for cls in classes)

    # Add standard imports from the original file
    for imp in imports:
        # Skip base class import - we'll add our own
        if imp.is_from_import and imp.module and "KatanaPydanticBase" in imp.names:
            continue
        # #342: drop `from __future__ import annotations` in cache-table modules.
        if (
            has_cache_tables
            and imp.is_from_import
            and imp.module == "__future__"
            and "annotations" in imp.names
        ):
            continue
        import_lines.append(imp.source)

    # Ensure we have the base class import
    import_lines.insert(
        0,
        "from katana_public_api_client.models_pydantic._base import KatanaPydanticBase",
    )

    # Add ConfigDict import for base module (needed for BaseEntity extra="ignore", #295)
    if current_module == "base" and not any(
        "ConfigDict" in line for line in import_lines
    ):
        import_lines.append("from pydantic import ConfigDict")

    # #342: cache-table modules get sqlmodel's Field (aliased as SQLField to
    # avoid collision with pydantic's Field), Relationship, and Optional for
    # child back-reference annotations (``Optional["Parent"]`` form required
    # so SQLAlchemy's string-form relationship resolution can parse the
    # forward ref).
    cached_fts_class_names = {_cached_name(n) for n in CACHE_FTS_SPECS}
    has_fts_columns = any(cls.name in cached_fts_class_names for cls in classes)
    if has_cache_tables:
        # ``ClassVar`` joins ``Optional`` on the same ``from typing import ...``
        # line when both are needed (FTS-bearing modules), keeping imports
        # tidy. ClassVar only matters for FTS columns; non-FTS modules skip it.
        typing_names = ["Optional"]
        if has_fts_columns:
            typing_names.append("ClassVar")
        typing_names.sort()
        import_lines.append(f"from typing import {', '.join(typing_names)}")
        import_lines.append("from sqlmodel import Field as SQLField, Relationship")
        if not any("ConfigDict" in line for line in import_lines):
            import_lines.append("from pydantic import ConfigDict")
        if has_json_columns:
            import_lines.append("from sqlalchemy import Column")
            import_lines.append(
                "from katana_public_api_client.models_pydantic._pydantic_json import PydanticJSON"
            )

    # ``Mapped`` shim import: cache-table modules and the base module
    # both need it. ``wrap_cache_fields_in_mapped`` wraps fields on every
    # ``Cached*`` class *and* on the shared entity base classes
    # (BaseEntity, DeletableEntity, etc.), so ``base.py`` ships the
    # shim too even though it has no ``table=True`` classes itself.
    has_mapped_targets = any(
        cls.name in (cached_class_names | ENTITY_BASE_CLASSES) for cls in classes
    )
    if has_mapped_targets:
        import_lines.append(
            "from katana_public_api_client.models_pydantic._mapped_shim import Mapped"
        )

    # #342: any module whose classes had AwareDatetime swapped for plain
    # datetime needs the stdlib datetime import. Applies to both cache-table
    # modules and the base module (shared entity bases feed cache tables via
    # inheritance).
    needs_datetime_import = any(
        cls.name in (cached_class_names | ENTITY_BASE_CLASSES) for cls in classes
    )
    if needs_datetime_import:
        import_lines.append("from datetime import datetime")

    # Find cross-module dependencies (classes_in_module set already built above).
    needed_imports: dict[str, set[str]] = defaultdict(set)  # module -> class names

    for cls in classes:
        for base in cls.bases:
            if base in class_to_module and base not in classes_in_module:
                target_module = class_to_module[base]
                if target_module != current_module:
                    needed_imports[target_module].add(base)

        # Also check for type references in the class source
        # Look for patterns like ": ClassName" or "list[ClassName]" etc.
        for other_class, other_module in class_to_module.items():
            if other_class in classes_in_module:
                continue
            if other_module == current_module:
                continue
            # Check if the class is referenced
            if re.search(rf"\b{re.escape(other_class)}\b", cls.source):
                needed_imports[other_module].add(other_class)

    # Add cross-module imports
    for module, class_names in sorted(needed_imports.items()):
        sorted_names = sorted(class_names)
        if len(sorted_names) <= 3:
            names_str = ", ".join(sorted_names)
            import_lines.append(f"from .{module} import {names_str}")
        else:
            # Multi-line import
            names_str = ",\n    ".join(sorted_names)
            import_lines.append(f"from .{module} import (\n    {names_str},\n)")

    return "\n".join(import_lines)


def write_module_file(
    output_dir: Path,
    module_name: str,
    imports: list[ImportInfo],
    classes: list[ClassInfo],
    type_aliases: list[TypeAliasInfo],
    class_to_module: dict[str, str],
) -> None:
    """Write a single module file."""
    file_path = output_dir / f"{module_name}.py"

    # #342: modules with cache tables must NOT use `from __future__ import
    # annotations` — SQLAlchemy's relationship type resolution needs live
    # type objects at class-definition time.
    cached_class_names = {_cached_name(n) for n in CACHE_TABLES}
    has_cache_tables = any(cls.name in cached_class_names for cls in classes)
    future_annotations_line = (
        "" if has_cache_tables else "from __future__ import annotations\n\n"
    )

    header = f'''"""Auto-generated Pydantic models - {module_name} domain.

DO NOT EDIT - This file is generated by scripts/generate_pydantic_models.py

To regenerate, run:
    uv run poe generate-pydantic
"""

{future_annotations_line}'''

    # Generate imports
    import_section = generate_module_imports(
        imports, classes, class_to_module, module_name
    )

    # Generate class definitions
    class_section = "\n\n\n".join(cls.source for cls in classes)

    # Generate type alias section (if any)
    alias_section = ""
    if type_aliases:
        alias_lines = [alias.source for alias in type_aliases]
        alias_section = "\n\n# Type aliases\n" + "\n".join(alias_lines)

    content = header + import_section + "\n\n\n" + class_section + alias_section + "\n"
    file_path.write_text(content, encoding="utf-8")


def write_init_file(
    output_dir: Path,
    class_groups: dict[str, list[ClassInfo]],
    alias_groups: dict[str, list[TypeAliasInfo]],
) -> None:
    """Write the __init__.py file that re-exports all models and type aliases."""
    print("Writing __init__.py...")

    imports: list[str] = []
    all_exports: list[str] = []

    # Get all module names
    all_modules = sorted(set(class_groups.keys()) | set(alias_groups.keys()))

    for module_name in all_modules:
        classes = class_groups.get(module_name, [])
        aliases = alias_groups.get(module_name, [])

        all_names = sorted(
            [cls.name for cls in classes] + [alias.name for alias in aliases]
        )
        if not all_names:
            continue

        if len(all_names) <= 5:
            names_str = ", ".join(all_names)
            imports.append(f"from .{module_name} import {names_str}")
        else:
            names_str = ",\n    ".join(all_names)
            imports.append(f"from .{module_name} import (\n    {names_str},\n)")
        all_exports.extend(all_names)

    content = '''"""Auto-generated Pydantic models from OpenAPI specification.

DO NOT EDIT - This file is generated by scripts/generate_pydantic_models.py

The models in this package mirror the attrs models in katana_public_api_client/models/
but use Pydantic v2 for validation and serialization.

To regenerate these models, run:
    uv run poe generate-pydantic
"""

'''
    content += "\n".join(imports)
    content += "\n\n__all__ = [\n"
    for name in sorted(all_exports):
        content += f'    "{name}",\n'
    content += "]\n"

    init_path = output_dir / "__init__.py"
    init_path.write_text(content, encoding="utf-8")
    print(f"  Exported {len(all_exports)} models")


def generate_auto_registry(
    groups: dict[str, list[ClassInfo]],
    output_path: Path,
    attrs_models_dir: Path,
) -> None:
    """Generate the auto-registry module that maps attrs <-> pydantic classes."""
    print("Generating auto-registry...")

    # Find all attrs model classes
    attrs_classes: dict[str, str] = {}  # class_name -> module_path
    for py_file in attrs_models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue

        content = py_file.read_text(encoding="utf-8")
        # Look for @_attrs_define decorated classes
        class_pattern = r"@_attrs_define\s+class\s+(\w+)"
        for match in re.finditer(class_pattern, content):
            class_name = match.group(1)
            module_path = f"katana_public_api_client.models.{py_file.stem}"
            attrs_classes[class_name] = module_path

    # Build pydantic class mapping
    pydantic_classes: dict[str, str] = {}  # class_name -> module_name
    for module_name, classes in groups.items():
        for cls in classes:
            pydantic_classes[cls.name] = module_name

    # Build registry code
    imports: list[str] = []
    registrations: list[str] = []
    matched = 0

    for class_name in sorted(pydantic_classes.keys()):
        if class_name not in attrs_classes:
            continue

        pydantic_module = pydantic_classes[class_name]
        attrs_module = attrs_classes[class_name]

        imports.append(f"from {attrs_module} import {class_name} as Attrs{class_name}")
        imports.append(
            f"from ._generated.{pydantic_module} import {class_name} as Pydantic{class_name}"
        )
        registrations.append(f"    register(Attrs{class_name}, Pydantic{class_name})")
        matched += 1

    content = '''"""Auto-generated registry mapping attrs <-> Pydantic model classes.

DO NOT EDIT - This file is generated by scripts/generate_pydantic_models.py

To regenerate, run:
    uv run poe generate-pydantic
"""

from ._registry import register

# Import all model classes
'''
    content += "\n".join(imports)
    content += "\n\n\ndef register_all_models() -> None:\n"
    content += '    """Register all attrs <-> Pydantic model mappings."""\n'
    if registrations:
        content += "\n".join(registrations)
    else:
        content += "    pass  # No models to register yet"
    content += "\n"

    output_path.write_text(content, encoding="utf-8")
    print(
        f"  Generated auto-registry with {matched} mappings "
        f"(of {len(pydantic_classes)} pydantic models)"
    )


def format_code(workspace_path: Path) -> None:
    """Run ruff format and fix on the generated code."""
    print("Formatting generated code...")

    pydantic_dir = workspace_path / "katana_public_api_client" / "models_pydantic"

    # Run ruff fix first
    run_command(
        ["ruff", "check", "--fix", "--unsafe-fixes", str(pydantic_dir)],
        cwd=workspace_path,
        check=False,
    )

    # Then format
    run_command(
        ["ruff", "format", str(pydantic_dir)],
        cwd=workspace_path,
        check=False,
    )

    print("Formatting complete")


def main() -> None:
    """Main function."""
    workspace_path = Path.cwd()
    output_dir = (
        workspace_path / "katana_public_api_client" / "models_pydantic" / "_generated"
    )
    attrs_models_dir = workspace_path / "katana_public_api_client" / "models"
    auto_registry_path = (
        workspace_path
        / "katana_public_api_client"
        / "models_pydantic"
        / "_auto_registry.py"
    )

    print("=" * 60)
    print("Pydantic Model Generation")
    print("=" * 60)
    print(f"Workspace: {workspace_path}")
    print(f"Output directory: {output_dir}")
    print()

    # Clean output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Generate single file to temp location
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as tmp:
        temp_file = Path(tmp.name)

    try:
        generate_single_file(temp_file)

        # Step 2: Parse the generated file
        imports, classes, type_aliases = parse_generated_file(temp_file)

        # Step 3: Group classes and type aliases by domain
        class_groups, alias_groups = group_classes(classes, type_aliases)

        # Step 4: Build class-to-module mapping
        class_to_module = build_class_to_module_map(class_groups, alias_groups)

        # Step 5: Write grouped module files
        print("Writing module files...")
        for module_name, module_classes in class_groups.items():
            module_aliases = alias_groups.get(module_name, [])
            write_module_file(
                output_dir,
                module_name,
                imports,
                module_classes,
                module_aliases,
                class_to_module,
            )
            alias_count = len(module_aliases)
            extra = f" + {alias_count} aliases" if alias_count else ""
            print(f"  Wrote {module_name}.py ({len(module_classes)} classes{extra})")

        # Step 6: Write __init__.py
        write_init_file(output_dir, class_groups, alias_groups)

        # Step 7: Generate auto-registry
        generate_auto_registry(class_groups, auto_registry_path, attrs_models_dir)

    finally:
        # Clean up temp file
        temp_file.unlink(missing_ok=True)

    # Step 8: Format code
    format_code(workspace_path)

    # Count total classes and aliases
    total_classes = sum(len(classes) for classes in class_groups.values())
    total_aliases = sum(len(aliases) for aliases in alias_groups.values())

    print()
    print("=" * 60)
    print("Generation complete!")
    alias_text = f" + {total_aliases} aliases" if total_aliases else ""
    print(
        f"  Generated {total_classes} classes{alias_text} in {len(class_groups)} files"
    )
    print()
    print("Next steps:")
    print("  1. Run tests: uv run poe test")
    print("  2. Check linting: uv run poe lint")
    print()


if __name__ == "__main__":
    import sys

    try:
        main()
    except GenerationError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(e.exit_code)
