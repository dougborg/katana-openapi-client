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
        "UpdatePurchaseOrder*",
    ],
    "sales_orders": [
        "SalesOrder*",
        "SalesReturn*",
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


def classify_class(class_name: str) -> str:
    """Determine which domain group a class belongs to.

    Exact matches are checked first (across all groups) before prefix matches.
    This ensures that explicit class names take priority over wildcard patterns.
    """
    # First pass: check for exact matches across all groups
    for group_name, patterns in DOMAIN_GROUPS.items():
        for pattern in patterns:
            if not pattern.endswith("*") and class_name == pattern:
                return group_name

    # Second pass: check for prefix matches
    for group_name, patterns in DOMAIN_GROUPS.items():
        for pattern in patterns:
            # Prefix match: pattern ends with * and class_name starts with pattern prefix
            if pattern.endswith("*") and class_name.startswith(pattern[:-1]):
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

    # Add standard imports from the original file
    for imp in imports:
        # Skip base class import - we'll add our own
        if imp.is_from_import and imp.module and "KatanaPydanticBase" in imp.names:
            continue
        # Skip RootModel if present
        if imp.is_from_import and "RootModel" in imp.names:
            imp.names = [n for n in imp.names if n != "RootModel"]
            if not imp.names:
                continue
        import_lines.append(imp.source)

    # Ensure we have the base class import
    import_lines.insert(
        0,
        "from katana_public_api_client.models_pydantic._base import KatanaPydanticBase",
    )

    # Find cross-module dependencies
    classes_in_module = {cls.name for cls in classes}
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

    header = f'''"""Auto-generated Pydantic models - {module_name} domain.

DO NOT EDIT - This file is generated by scripts/generate_pydantic_models.py

To regenerate, run:
    uv run poe generate-pydantic
"""

from __future__ import annotations

'''

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
