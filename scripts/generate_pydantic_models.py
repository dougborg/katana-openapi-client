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
import re
import shutil
import subprocess
import tempfile
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
        "EnumValidationError",
        "MinValidationError",
        "MaxValidationError",
        "InvalidTypeValidationError",
        "TooSmallValidationError",
        "TooBigValidationError",
        "RequiredValidationError",
        "PatternValidationError",
        "UnrecognizedKeysValidationError",
        "GenericValidationError",
        # Also include Code enums that are part of error types
        "Code",
        "Code1",
        "Code2",
        "Code3",
        "Code4",
        "Code5",
        "Code6",
        "Code7",
        "Code8",
        "Code9",
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


# Cache-table configuration for #342 — select generated pydantic classes opt
# into SQLAlchemy table semantics (`table=True`) so they double as cache row
# schemas. Expanded incrementally per-entity as list tools get cache-backed;
# PR 2 covers SalesOrder + SalesOrderRow as the pattern-proving pair.
CACHE_TABLES: set[str] = {
    "SalesOrder",
    "SalesOrderRow",
    "StockAdjustment",
    "StockAdjustmentRow",
    "ManufacturingOrder",
    "PurchaseOrderBase",
    "PurchaseOrderRow",
}


# Cache class name overrides — when the API class name reads awkwardly as a
# cache class, remap. Example: ``PurchaseOrderBase`` is the API discriminated
# union root (sibling of RegularPurchaseOrder + OutsourcedPurchaseOrder); the
# cache class shadows it as ``CachedPurchaseOrder`` (and ``__tablename__`` is
# ``purchase_order``, not ``purchase_order_base``).
CACHE_TABLE_RENAMES: dict[str, str] = {
    "PurchaseOrderBase": "PurchaseOrder",
}


# Cache-only fields hoisted from API subclasses into the cache base. Used when
# a discriminated-union root (PurchaseOrderBase) is cached as one SQL table
# but the listing tool needs to filter by a column that lives on a subclass
# (OutsourcedPurchaseOrder.tracking_location_id). The converter copies these
# fields out of the subclass instance when the entity_type matches.
CACHE_EXTRA_FIELDS: dict[str, list[str]] = {
    "PurchaseOrderBase": [
        "    tracking_location_id: int | None = None",
    ],
}


@dataclass(frozen=True)
class CacheTableRelationship:
    """1:N parent→child relationship declaration between two cache tables."""

    parent: str
    parent_field: str
    child: str
    child_back_ref: str
    child_fk_field: str

    @property
    def parent_table(self) -> str:
        # Honor ``CACHE_TABLE_RENAMES`` so FK ``foreign_key="<table>.id"``
        # references match the renamed tablename (e.g.,
        # ``PurchaseOrderBase`` → ``purchase_order``, not
        # ``purchase_order_base``).
        renamed = CACHE_TABLE_RENAMES.get(self.parent, self.parent)
        return _snake_case(renamed)


def _snake_case(name: str) -> str:
    """CamelCase → snake_case — used for default SQLAlchemy tablenames."""
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _cached_name(name: str) -> str:
    """API class name → cache-row class name (``SalesOrder`` → ``CachedSalesOrder``).

    Cache rows live as ``Cached<Name>`` siblings of the API pydantic models
    so the API surface stays pure (no ``table=True``, no FK pollution) while
    the cache schema can carry SQLAlchemy machinery, FK back-pointers, and
    relationships. ``CACHE_TABLE_RENAMES`` lets a class shadow under a
    different name (``PurchaseOrderBase`` → ``CachedPurchaseOrder``).
    """
    return f"Cached{CACHE_TABLE_RENAMES.get(name, name)}"


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
]


# Fields on cache tables that contain lists of non-cached nested models (e.g.,
# polymorphic attributes, batch transactions, serial numbers). These are stored
# as JSON rather than exploded into child tables — they're low-signal for the
# cache's query workload and not worth the schema churn.
CACHE_JSON_COLUMNS: dict[str, list[str]] = {
    "SalesOrder": ["shipping_fee", "addresses"],
    "SalesOrderRow": ["attributes", "batch_transactions", "serial_numbers"],
    "StockAdjustmentRow": ["batch_transactions"],
    "ManufacturingOrder": ["batch_transactions", "serial_numbers"],
    # PurchaseOrderBase.supplier is a single nested ``Supplier`` object that
    # SQLAlchemy can't auto-map; cache it as JSON so the row stays denormalized.
    "PurchaseOrderBase": ["supplier"],
    # ``landed_cost: str | float | None`` is a non-optional inner union
    # that SQLAlchemy can't auto-type — JSON-column it instead of dropping.
    "PurchaseOrderRow": ["batch_transactions", "landed_cost"],
}


@dataclass
class ClassInfo:
    """Information about a class definition."""

    name: str
    source: str
    bases: list[str]
    line_start: int
    line_end: int


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
    # 2. table=True + frozen=False model_config on the cached class header.
    # 3. Redeclare id with primary_key=True (depends on the model_config
    #    line placed by step 2).
    # 4. Swap AwareDatetime → datetime so SQLModel's type inference works.
    # 5. FK / relationship / JSON column annotations on field declarations.
    classes = duplicate_cache_tables_as_cached_siblings(classes)
    classes = inject_table_annotations(classes)
    classes = inject_primary_key_in_table_classes(classes)
    classes = swap_awaredatetime_for_datetime(classes)
    classes = inject_foreign_keys(classes)
    classes = inject_relationship_fields(classes)
    classes = inject_json_columns(classes)
    classes = inject_extra_cache_fields(classes)

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
    cached_targets = {n: _cached_name(n) for n in CACHE_TABLES}

    def _rewrite_internal_refs(source: str) -> str:
        new_source = source
        # Word-boundary swap so e.g. ``SalesOrder`` → ``CachedSalesOrder``
        # doesn't also touch ``SalesOrderRow`` (the longer name handled in
        # its own iteration). Iterate longest-first to avoid corrupting
        # nested references like ``SalesOrderRow`` → ``CachedSalesOrderRow``
        # when ``SalesOrder`` is rewritten first.
        for original in sorted(cached_targets, key=len, reverse=True):
            cached = cached_targets[original]
            new_source = re.sub(rf"\b{re.escape(original)}\b", cached, new_source)
        return new_source

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
        new_source = _rewrite_internal_refs(new_source)
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
        fixed.append(
            ClassInfo(
                name=cls.name,
                source=new_source,
                bases=cls.bases,
                line_start=cls.line_start,
                line_end=cls.line_end,
            )
        )
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
        fixed.append(
            ClassInfo(
                name=cls.name,
                source=new_source,
                bases=cls.bases,
                line_start=cls.line_start,
                line_end=cls.line_end,
            )
        )
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
        fixed.append(
            ClassInfo(
                name=cls.name,
                source=new_source,
                bases=cls.bases,
                line_start=cls.line_start,
                line_end=cls.line_end,
            )
        )
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
        if cls.name in by_parent:
            rel = by_parent[cls.name]
            cached_child = _cached_name(rel.child)
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
            fixed.append(
                ClassInfo(
                    name=cls.name,
                    source=new_source,
                    bases=cls.bases,
                    line_start=cls.line_start,
                    line_end=cls.line_end,
                )
            )
        else:
            fixed.append(cls)
    return fixed


# Base classes whose fields propagate into cache tables via inheritance.
# Their AwareDatetime annotations (created_at / updated_at / deleted_at /
# archived_at) must be swapped to plain ``datetime`` too — otherwise
# SQLModel's table-column inference on the inheriting cache class fails.
_CACHE_BASE_CLASSES = frozenset(
    {
        "BaseEntity",
        "UpdatableEntity",
        "DeletableEntity",
        "ArchivableEntity",
        "ArchivableDeletableEntity",
    }
)


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
    swap_targets = {_cached_name(n) for n in CACHE_TABLES} | _CACHE_BASE_CLASSES
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
        fixed.append(
            ClassInfo(
                name=cls.name,
                source=new_source,
                bases=cls.bases,
                line_start=cls.line_start,
                line_end=cls.line_end,
            )
        )
    return fixed


def inject_extra_cache_fields(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Append ``CACHE_EXTRA_FIELDS`` declarations to the cache class body.

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
        _cached_name(name): fields for name, fields in CACHE_EXTRA_FIELDS.items()
    }
    fixed = []
    for cls in classes:
        extra_lines = cached_extras.get(cls.name)
        if not extra_lines:
            fixed.append(cls)
            continue
        new_source = cls.source.rstrip() + "\n" + "\n".join(extra_lines) + "\n"
        fixed.append(
            ClassInfo(
                name=cls.name,
                source=new_source,
                bases=cls.bases,
                line_start=cls.line_start,
                line_end=cls.line_end,
            )
        )
    return fixed


def inject_json_columns(classes: list[ClassInfo]) -> list[ClassInfo]:
    """Annotate specified list fields with ``sa_column=Column(JSON)``.

    For fields listed in ``CACHE_JSON_COLUMNS`` — typically lists of
    polymorphic or non-cached nested models — this preserves the typed
    pydantic interface while telling SQLAlchemy to store them as JSON rather
    than attempting to normalize them into child tables. Operates on the
    ``Cached<Name>`` siblings: ``CACHE_JSON_COLUMNS`` keys are user-facing
    API names so the cached lookup converts via ``_cached_name``.
    """
    cached_json_columns = {
        _cached_name(name): fields for name, fields in CACHE_JSON_COLUMNS.items()
    }
    fixed = []
    for cls in classes:
        fields = cached_json_columns.get(cls.name)
        if not fields:
            fixed.append(cls)
            continue
        new_source = cls.source
        for field_name in fields:
            # Rewrite `Field(` → `SQLField(` AND inject sa_column=Column(JSON).
            # Same rationale as foreign_key injection — pydantic.Field
            # doesn't accept ``sa_column``; SQLField does.
            pattern = (
                rf"({re.escape(field_name)}:\s*Annotated\[\s*"
                rf"[^,]+,\s*)Field\(\s*(description=)"
            )
            replacement = r"\1SQLField(sa_column=Column(JSON), \2"
            new_source, n = re.subn(pattern, replacement, new_source, count=1)
            if n != 1:
                msg = (
                    f"Failed to inject JSON sa_column on "
                    f"{cls.name}.{field_name}. Field shape may have changed."
                )
                raise GenerationError(msg)
        fixed.append(
            ClassInfo(
                name=cls.name,
                source=new_source,
                bases=cls.bases,
                line_start=cls.line_start,
                line_end=cls.line_end,
            )
        )
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
    cached_json_class_names = {_cached_name(n) for n in CACHE_JSON_COLUMNS}
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
    if has_cache_tables:
        import_lines.append("from typing import Optional")
        import_lines.append("from sqlmodel import Field as SQLField, Relationship")
        if not any("ConfigDict" in line for line in import_lines):
            import_lines.append("from pydantic import ConfigDict")
        if has_json_columns:
            import_lines.append("from sqlalchemy import JSON, Column")

    # #342: any module whose classes had AwareDatetime swapped for plain
    # datetime needs the stdlib datetime import. Applies to both cache-table
    # modules and the base module (shared entity bases feed cache tables via
    # inheritance).
    needs_datetime_import = any(
        cls.name in (cached_class_names | _CACHE_BASE_CLASSES) for cls in classes
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
