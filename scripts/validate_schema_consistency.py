#!/usr/bin/env python3
"""
Validate schema consistency between our OpenAPI 3.1 spec and the downloaded OpenAPI 3.0 spec.
Compares schema definitions, examples, and identifies potential inconsistencies.
"""

import json
import sys
import warnings
from datetime import datetime
from pathlib import Path
from typing import Any

import jsonschema
import yaml

# Suppress the RefResolver deprecation warning until we can properly migrate to referencing library
# TODO: Migrate to the modern 'referencing' library approach in a future update
warnings.filterwarnings(
    "ignore", message=".*RefResolver.*deprecated.*", category=DeprecationWarning
)


def load_yaml_spec(file_path: Path) -> dict[str, Any]:
    """Load our OpenAPI 3.1 YAML specification."""
    with open(file_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_json_spec(file_path: Path) -> dict[str, Any]:
    """Load the downloaded OpenAPI 3.0 JSON specification."""
    with open(file_path, encoding="utf-8") as f:
        return json.load(f)


def extract_examples_by_endpoint(
    spec: dict[str, Any],
) -> dict[str, list[dict[str, Any]]]:
    """Extract examples from OpenAPI spec grouped by endpoint path and method."""
    examples: dict[str, list[dict[str, Any]]] = {}

    paths = spec.get("paths", {})
    for path, methods in paths.items():
        for method, operation in methods.items():
            if not isinstance(operation, dict):
                continue

            endpoint_key = f"{method.upper()} {path}"

            responses = operation.get("responses", {})
            for status, response in responses.items():
                if not isinstance(response, dict):
                    continue

                content = response.get("content", {})
                for media_type, media_content in content.items():
                    if "examples" in media_content:
                        examples_data = media_content["examples"]
                        for example_name, example_data in examples_data.items():
                            if "value" in example_data:
                                if endpoint_key not in examples:
                                    examples[endpoint_key] = []
                                examples[endpoint_key].append(
                                    {
                                        "path": path,
                                        "method": method.upper(),
                                        "status": status,
                                        "media_type": media_type,
                                        "example_name": example_name,
                                        "data": example_data["value"],
                                    }
                                )

                    # Also check for single example
                    if "example" in media_content:
                        if endpoint_key not in examples:
                            examples[endpoint_key] = []
                        examples[endpoint_key].append(
                            {
                                "path": path,
                                "method": method.upper(),
                                "status": status,
                                "media_type": media_type,
                                "example_name": "default",
                                "data": media_content["example"],
                            }
                        )

    return examples


def extract_examples_from_spec(spec: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Legacy function - kept for compatibility but deprecated."""
    # Use the new endpoint-based extraction instead
    return extract_examples_by_endpoint(spec)


def get_response_schema_for_endpoint(
    spec: dict[str, Any], path: str, method: str, status: str = "200"
) -> dict[str, Any] | None:
    """Extract the response schema for a specific endpoint from our OpenAPI spec."""
    paths = spec.get("paths", {})
    if path not in paths:
        return None

    methods = paths[path]
    if method.lower() not in methods:
        return None

    operation = methods[method.lower()]
    responses = operation.get("responses", {})
    if status not in responses:
        return None

    response = responses[status]
    content = response.get("content", {})

    # Try application/json first, then any content type
    for content_type in ["application/json", *content.keys()]:
        if content_type in content:
            schema = content[content_type].get("schema")
            if schema:
                return schema

    return None


def resolve_schema_ref(spec: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
    """Resolve $ref in schema to get the actual schema definition."""
    if "$ref" in schema:
        ref_path = schema["$ref"]
        if ref_path.startswith("#/"):
            # Remove '#/' and split by '/'
            path_parts = ref_path[2:].split("/")
            result = spec
            for part in path_parts:
                result = result.get(part, {})
            return result
    return schema


def compare_schema_properties(
    our_schema: dict[str, Any], downloaded_schema: dict[str, Any], schema_name: str
) -> list[str]:
    issues = []

    # Handle allOf schemas
    our_props = {}
    if "allOf" in our_schema:
        for item in our_schema["allOf"]:
            if "properties" in item:
                our_props.update(item["properties"])
    elif "properties" in our_schema:
        our_props = our_schema["properties"]

    downloaded_props = {}
    if "allOf" in downloaded_schema:
        for item in downloaded_schema["allOf"]:
            if "properties" in item:
                downloaded_props.update(item["properties"])
    elif "properties" in downloaded_schema:
        downloaded_props = downloaded_schema["properties"]

    # Check for missing properties in our schema
    our_prop_names = set(our_props.keys())
    downloaded_prop_names = set(downloaded_props.keys())

    missing_in_ours = downloaded_prop_names - our_prop_names
    extra_in_ours = our_prop_names - downloaded_prop_names

    if missing_in_ours:
        issues.append(
            f"❌ {schema_name}: Missing properties in our schema: {sorted(missing_in_ours)}"
        )

    if extra_in_ours:
        issues.append(
            f"Info: {schema_name}: Extra properties in our schema: {sorted(extra_in_ours)}"
        )

    # Check property types for common properties
    common_props = our_prop_names & downloaded_prop_names
    for prop_name in common_props:
        our_prop = our_props[prop_name]
        downloaded_prop = downloaded_props[prop_name]

        # Compare types
        our_type = our_prop.get("type")
        downloaded_type = downloaded_prop.get("type")

        if our_type != downloaded_type:
            # Handle nullable types
            our_nullable = isinstance(our_type, list) and "null" in our_type
            downloaded_nullable = downloaded_prop.get("nullable", False)

            if not (our_nullable and downloaded_nullable):
                issues.append(
                    f"⚠️  {schema_name}.{prop_name}: Type mismatch - ours: {our_type}, downloaded: {downloaded_type}"
                )

        # Compare enums
        our_enum = our_prop.get("enum")
        downloaded_enum = downloaded_prop.get("enum")

        if our_enum and downloaded_enum:
            our_enum_set = set(our_enum)
            downloaded_enum_set = set(downloaded_enum)

            if our_enum_set != downloaded_enum_set:
                missing = downloaded_enum_set - our_enum_set
                extra = our_enum_set - downloaded_enum_set
                if missing:
                    issues.append(
                        f"❌ {schema_name}.{prop_name}: Missing enum values: {sorted(missing)}"
                    )
                if extra:
                    issues.append(
                        f"Info: {schema_name}.{prop_name}: Extra enum values: {sorted(extra)}"
                    )

    return issues


def validate_basic_properties(
    example_data: dict[str, Any], schema: dict[str, Any]
) -> list[str]:
    """Basic property validation when jsonschema is not available."""
    errors = []

    # Check required properties
    required_props = schema.get("required", [])
    for prop in required_props:
        if prop not in example_data:
            errors.append(f"Missing required property: {prop}")

    # Check property types
    properties = schema.get("properties", {})
    for prop_name, prop_value in example_data.items():
        if prop_name in properties:
            prop_schema = properties[prop_name]
            expected_type = prop_schema.get("type")

            if expected_type:
                actual_type = type(prop_value).__name__
                type_mapping = {
                    "str": "string",
                    "int": "integer",
                    "float": "number",
                    "bool": "boolean",
                    "list": "array",
                    "dict": "object",
                }

                if type_mapping.get(actual_type) != expected_type:
                    errors.append(
                        f"Property '{prop_name}' has type {actual_type}, expected {expected_type}"
                    )

    return errors


def is_error_response(item: dict[str, Any]) -> bool:
    """Check if an item is an error response that shouldn't be validated against business schemas."""
    if not isinstance(item, dict):
        return False

    # Common error response patterns
    error_indicators = ["statusCode", "name", "message", "error", "code"]
    has_error_fields = any(field in item for field in error_indicators)

    # Additional check: if it has statusCode with a non-2xx value
    if "statusCode" in item:
        status_code = item.get("statusCode")
        if isinstance(status_code, int) and (status_code < 200 or status_code >= 300):
            return True

    return has_error_fields


def extract_individual_items_from_response(
    response_data: dict[str, Any], resource_type: str
) -> list[dict[str, Any]]:
    """Extract individual items from response wrappers like {"data": [...]}."""
    individual_items = []

    # Handle common response patterns
    if isinstance(response_data, dict):
        # Pattern 1: {"data": [...]} - array of items
        if "data" in response_data and isinstance(response_data["data"], list):
            individual_items.extend(response_data["data"])

        # Pattern 2: Single item response
        elif "data" in response_data and isinstance(response_data["data"], dict):
            individual_items.append(response_data["data"])

        # Pattern 3: Direct object (not wrapped)
        elif resource_type.lower() in str(response_data).lower():
            individual_items.append(response_data)

    # Pattern 4: Direct array
    elif isinstance(response_data, list):
        individual_items.extend(response_data)

    return individual_items


def find_matching_schemas(
    our_schemas: dict[str, Any], downloaded_schemas: dict[str, Any]
) -> dict[str, str]:
    """Find matching schemas between our spec and downloaded spec."""
    matches = {}

    # Direct name matches
    for our_name in our_schemas:
        if our_name in downloaded_schemas:
            matches[our_name] = our_name

    # Handle potential name variations
    name_mappings = {
        "SalesOrder": "SalesOrder",
        "PurchaseOrder": "PurchaseOrder",
        "ManufacturingOrder": "ManufacturingOrder",
        "Product": "Product",
        "Material": "Material",
        "Customer": "Customer",
        "Supplier": "Supplier",
        "Variant": "Variant",
        "Location": "Location",
        "TaxRate": "TaxRate",
        "Webhook": "Webhook",
        "Inventory": "Inventory",
        "BomRow": "BomRow",
    }

    for our_name, downloaded_name in name_mappings.items():
        if our_name in our_schemas and downloaded_name in downloaded_schemas:
            matches[our_name] = downloaded_name

    return matches


def main():
    """Main validation function."""
    print("🔍 Katana OpenAPI Schema Consistency Validation")
    print(f"📅 Run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Load specifications
    our_spec_path = Path("docs/katana-openapi.yaml")
    downloaded_spec_path = Path("docs/katana-api-comprehensive/openapi-spec.json")

    if not our_spec_path.exists():
        print(f"❌ Our OpenAPI spec not found: {our_spec_path}")
        return 1

    if not downloaded_spec_path.exists():
        print(f"❌ Downloaded OpenAPI spec not found: {downloaded_spec_path}")
        return 1

    print(f"📖 Loading our OpenAPI 3.1 spec: {our_spec_path}")
    our_spec = load_yaml_spec(our_spec_path)

    print(f"📖 Loading downloaded OpenAPI 3.0 spec: {downloaded_spec_path}")
    downloaded_spec = load_json_spec(downloaded_spec_path)

    our_schemas = our_spec.get("components", {}).get("schemas", {})
    downloaded_schemas = downloaded_spec.get("components", {}).get("schemas", {})

    print(f"📊 Our schemas: {len(our_schemas)}")
    print(f"📊 Downloaded schemas: {len(downloaded_schemas)}")
    print()

    # Extract examples from downloaded spec grouped by endpoint
    print("🔍 Extracting examples from downloaded spec by endpoint...")
    downloaded_examples = extract_examples_by_endpoint(downloaded_spec)
    print(f"📋 Found examples for {len(downloaded_examples)} endpoints")

    # Print endpoints found for debugging
    print("📋 Endpoints with examples:")
    for endpoint, examples in downloaded_examples.items():
        print(f"   {endpoint}: {len(examples)} examples")
    print()

    # Skip schema comparison since downloaded spec has no schemas
    # Focus only on endpoint-to-endpoint validation
    all_issues = []

    # Validate examples against corresponding endpoint schemas in our spec
    print("🧪 Validating examples against corresponding endpoint schemas...")
    for endpoint, examples in downloaded_examples.items():
        method, path = endpoint.split(" ", 1)

        # Find the corresponding schema in our spec for this endpoint
        our_schema = get_response_schema_for_endpoint(our_spec, path, method, "200")

        if our_schema:
            # Resolve any $ref in the schema
            resolved_schema = resolve_schema_ref(our_spec, our_schema)

            schema_issues = validate_examples_against_schema(
                examples, resolved_schema, f"{endpoint}", our_spec
            )
            all_issues.extend(schema_issues)

            if not schema_issues:
                print(f"✅ {endpoint}: All examples validated successfully")
        else:
            # Handle DELETE endpoints which typically don't have response schemas
            if method == "DELETE":
                print(f"✅ {endpoint}: DELETE endpoint - no response schema expected")
            else:
                # Note missing endpoint schemas for non-DELETE methods
                all_issues.append(
                    f"INFO  {endpoint}: No response schema found in our spec"
                )
                all_issues.append("")

    print()
    print("📋 VALIDATION SUMMARY")
    print("=" * 60)

    if not all_issues:
        print("🎉 No inconsistencies found! All schemas and examples are aligned.")
        return 0

    print(f"⚠️  Found {len(all_issues)} potential issues:")
    print()

    if all_issues:
        print("🚨 ALL VALIDATION ISSUES:")
        for issue in all_issues:
            print(f"  {issue}")
        print()

    # Also group by type for summary
    errors = [issue for issue in all_issues if issue.startswith("❌")]
    warnings = [issue for issue in all_issues if issue.startswith("⚠️")]
    info = [issue for issue in all_issues if issue.startswith("INFO")]

    print("📈 SUMMARY:")
    print(f"   Total issues: {len(all_issues)}")
    print(f"   Errors: {len(errors)}")
    print(f"   Warnings: {len(warnings)}")
    print(f"   Info: {len(info)}")
    print()

    return 1 if errors else 0


def get_appropriate_schema_for_example(
    example: dict[str, Any], resource_type: str
) -> str:
    """Map an example to the most appropriate schema based on its source path and data structure."""
    path = example.get("path", "")
    example.get("data", {})

    # Handle special cases based on endpoint paths
    if "/inventory_reorder_points" in path:
        return "InventoryReorderPoint"  # This would need its own schema
    elif "/inventory_safety_stock_levels" in path:
        return "InventorySafetyStockLevel"  # This would need its own schema
    elif "/inventory" in path:
        return "Inventory"

    # Standard resource type mapping
    schema_mapping = {
        "Sales orders": "SalesOrder",
        "Purchase orders": "PurchaseOrder",
        "Manufacturing orders": "ManufacturingOrder",
        "Products": "Product",
        "Materials": "Material",
        "Customers": "Customer",
        "Suppliers": "Supplier",
        "Variants": "Variant",
        "Locations": "Location",
        "Tax rates": "TaxRate",
        "Webhooks": "Webhook",
        "Inventory": "Inventory",
        "BOM rows": "BomRow",
    }

    return schema_mapping.get(resource_type, resource_type)


def validate_examples_against_schema(
    examples: list[dict[str, Any]],
    schema: dict[str, Any],
    schema_name: str,
    full_spec: dict[str, Any],
) -> list[str]:
    """Validate a list of examples against a schema using RefResolver."""
    issues = []

    # Create a validator with RefResolver for $ref resolution (deprecated but working)
    try:
        validator = jsonschema.Draft7Validator(
            schema, resolver=jsonschema.RefResolver.from_schema(full_spec)
        )
    except jsonschema.SchemaError as e:
        issues.append(f"❌ Invalid schema '{schema_name}': {e}")
        return issues

    valid_examples = 0
    for i, example in enumerate(examples):
        data = example.get("data", {})
        path = example.get("path", "unknown")

        # Skip error responses
        if is_error_response(data):
            continue

        # Validate the data against the schema
        try:
            validator.validate(data)
            valid_examples += 1
        except jsonschema.ValidationError as e:
            issues.append(f"❌ {schema_name} example {i + 1} validation failed:")
            issues.append(f"   Path: {path}")
            issues.append(f"   Error: {e.message}")
            issues.append(
                f"   Schema path: {' -> '.join(str(p) for p in e.absolute_path)}"
            )
            issues.append(f"   Failed value: {e.instance}")
            issues.append("")

    if valid_examples > 0:
        print(
            f"✅ {schema_name}: {valid_examples}/{len(examples)} examples validated successfully"
        )

    return issues


if __name__ == "__main__":
    sys.exit(main())
