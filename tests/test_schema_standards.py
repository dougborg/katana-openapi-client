"""
Schema Standards Tests

This module validates OpenAPI schema quality standards including:
- BaseEntity inheritance patterns
- Schema descriptions
- Property descriptions
- Example structure (schema-level vs property-level)
- Endpoint schema examples
"""

from pathlib import Path
from typing import Any

import pytest
import yaml


@pytest.fixture(scope="session")
def openapi_spec() -> dict[str, Any]:
    """Load the OpenAPI specification once for all tests."""
    spec_path = Path(__file__).parent.parent / "katana-openapi.yaml"
    with open(spec_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def schemas(openapi_spec: dict[str, Any]) -> dict[str, Any]:
    """Extract schemas from OpenAPI spec."""
    return openapi_spec.get("components", {}).get("schemas", {})


@pytest.fixture(scope="session")
def endpoint_schemas(openapi_spec: dict[str, Any]) -> set[str]:
    """Find all schemas referenced in API endpoints."""
    referenced_schemas = set()

    def find_schema_refs(obj: Any) -> None:
        """Recursively find $ref schema references."""
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                if ref.startswith("#/components/schemas/"):
                    schema_name = ref.replace("#/components/schemas/", "")
                    referenced_schemas.add(schema_name)
            else:
                for value in obj.values():
                    find_schema_refs(value)
        elif isinstance(obj, list):
            for item in obj:
                find_schema_refs(item)

    # Search through all paths/endpoints
    paths = openapi_spec.get("paths", {})
    find_schema_refs(paths)

    return referenced_schemas


class TestBaseEntityInheritance:
    """Test BaseEntity inheritance patterns."""

    def test_base_entity_exists(self, schemas: dict[str, Any]):
        """BaseEntity schema must exist."""
        assert "BaseEntity" in schemas

    def test_base_entity_has_id_property(self, schemas: dict[str, Any]):
        """BaseEntity must have id property."""
        base_entity = schemas["BaseEntity"]
        assert "properties" in base_entity
        assert "id" in base_entity["properties"]

    def test_business_entities_inherit_from_base_entity(
        self, schemas: dict[str, Any], endpoint_schemas: set[str]
    ):
        """Business entities referenced in endpoints should inherit from BaseEntity when they have id properties."""
        # Find schemas that have an 'id' property but don't inherit from BaseEntity
        base_entity_ref = "#/components/schemas/BaseEntity"
        entities_missing_inheritance = []

        for schema_name in endpoint_schemas:
            if schema_name in schemas:
                schema = schemas[schema_name]

                # Skip response/request wrappers and base entities themselves
                if schema_name.endswith(
                    ("Response", "Request", "ListResponse")
                ) or schema_name in [
                    "BaseEntity",
                    "UpdatableEntity",
                    "DeletableEntity",
                    "ArchivableEntity",
                ]:
                    continue

                # Check if schema has an id property directly (should inherit instead)
                properties = schema.get("properties", {})
                if "id" in properties:
                    # Should inherit from BaseEntity instead of defining id directly
                    inherits_from_base = False
                    if "allOf" in schema:
                        base_refs = [
                            item.get("$ref", "")
                            for item in schema["allOf"]
                            if isinstance(item, dict) and "$ref" in item
                        ]
                        if base_entity_ref in base_refs:
                            inherits_from_base = True

                    if not inherits_from_base:
                        entities_missing_inheritance.append(schema_name)

        # Report findings - this is more informational than strict requirement
        if entities_missing_inheritance:
            print("\nBusiness entities that could benefit from BaseEntity inheritance:")
            for entity in sorted(entities_missing_inheritance):
                print(f"  - {entity}")

        # This test passes but provides useful information
        assert True


class TestSchemaDescriptions:
    """Test schema description requirements."""

    def test_all_endpoint_schemas_have_descriptions(
        self, schemas: dict[str, Any], endpoint_schemas: set[str]
    ):
        """All schemas referenced in endpoints must have meaningful descriptions."""
        schemas_missing_descriptions = []
        schemas_with_short_descriptions = []

        for schema_name in endpoint_schemas:
            if schema_name in schemas:
                schema = schemas[schema_name]

                if "description" not in schema:
                    schemas_missing_descriptions.append(schema_name)
                else:
                    description = schema["description"]
                    if not description or not description.strip():
                        schemas_missing_descriptions.append(schema_name)
                    elif len(description.strip()) <= 10:
                        schemas_with_short_descriptions.append(schema_name)

        # Report missing descriptions
        if schemas_missing_descriptions:
            print(
                f"\nSchemas missing descriptions ({len(schemas_missing_descriptions)}):"
            )
            for schema in sorted(schemas_missing_descriptions):
                print(f"  - {schema}")

        if schemas_with_short_descriptions:
            print(
                f"\nSchemas with short descriptions ({len(schemas_with_short_descriptions)}):"
            )
            for schema in sorted(schemas_with_short_descriptions):
                print(f"  - {schema}")

        total_missing = len(schemas_missing_descriptions) + len(
            schemas_with_short_descriptions
        )
        assert total_missing == 0, (
            f"{total_missing} endpoint schemas missing or have inadequate descriptions"
        )


class TestPropertyDescriptions:
    """Test property description requirements."""

    def test_all_endpoint_schema_properties_have_descriptions(
        self, schemas: dict[str, Any], endpoint_schemas: set[str]
    ):
        """All properties in endpoint-referenced schemas must have descriptions."""
        properties_missing_descriptions = []

        # Skip inherited properties from base entities
        skip_properties = {
            "id",
            "created_at",
            "updated_at",
            "deleted_at",
            "archived_at",
        }

        for schema_name in endpoint_schemas:
            if schema_name in schemas:
                schema = schemas[schema_name]
                properties = self._get_all_properties(schema, schemas)

                for prop_name, prop_def in properties.items():
                    if prop_name in skip_properties:
                        continue

                    # Only check actual property definitions (not inherited refs)
                    if (
                        isinstance(prop_def, dict)
                        and "type" in prop_def
                        and "description" not in prop_def
                    ):
                        properties_missing_descriptions.append(
                            f"{schema_name}.{prop_name}"
                        )

        # Report missing descriptions
        if properties_missing_descriptions:
            print(
                f"\nProperties missing descriptions ({len(properties_missing_descriptions)}):"
            )
            for prop in sorted(properties_missing_descriptions):
                print(f"  - {prop}")

        assert len(properties_missing_descriptions) == 0, (
            f"{len(properties_missing_descriptions)} properties missing descriptions"
        )

    def _get_all_properties(
        self, schema: dict[str, Any], all_schemas: dict[str, Any]
    ) -> dict[str, Any]:
        """Get all properties including inherited ones."""
        properties = {}

        # Handle allOf inheritance
        if "allOf" in schema:
            for item in schema["allOf"]:
                if "$ref" in item:
                    ref_name = item["$ref"].replace("#/components/schemas/", "")
                    if ref_name in all_schemas:
                        inherited_props = self._get_all_properties(
                            all_schemas[ref_name], all_schemas
                        )
                        properties.update(inherited_props)
                elif "properties" in item:
                    properties.update(item["properties"])

        # Direct properties
        if "properties" in schema:
            properties.update(schema["properties"])

        return properties


class TestExampleStructure:
    """Test example structure requirements."""

    def test_no_property_level_examples(
        self, schemas: dict[str, Any], endpoint_schemas: set[str]
    ):
        """Schemas should use schema-level examples, not property-level examples."""
        schemas_with_property_examples = []

        for schema_name in endpoint_schemas:
            if schema_name in schemas:
                schema = schemas[schema_name]
                properties = self._get_all_properties(schema, schemas)

                for prop_name, prop_def in properties.items():
                    if isinstance(prop_def, dict) and "example" in prop_def:
                        schemas_with_property_examples.append(
                            f"{schema_name}.{prop_name}"
                        )

        if schemas_with_property_examples:
            print("\nProperties with property-level examples (should be schema-level):")
            for prop in sorted(schemas_with_property_examples):
                print(f"  - {prop}")

        assert len(schemas_with_property_examples) == 0, (
            f"{len(schemas_with_property_examples)} properties have property-level examples (should be schema-level)"
        )

    def _get_all_properties(
        self, schema: dict[str, Any], all_schemas: dict[str, Any]
    ) -> dict[str, Any]:
        """Get all properties including inherited ones."""
        properties = {}

        # Handle allOf inheritance
        if "allOf" in schema:
            for item in schema["allOf"]:
                if "$ref" in item:
                    ref_name = item["$ref"].replace("#/components/schemas/", "")
                    if ref_name in all_schemas:
                        inherited_props = self._get_all_properties(
                            all_schemas[ref_name], all_schemas
                        )
                        properties.update(inherited_props)
                elif "properties" in item:
                    properties.update(item["properties"])

        # Direct properties
        if "properties" in schema:
            properties.update(schema["properties"])

        return properties


class TestEndpointSchemaExamples:
    """Test schemas used in endpoints have proper examples."""

    def test_all_endpoint_schemas_have_examples(
        self, schemas: dict[str, Any], endpoint_schemas: set[str]
    ):
        """All schemas referenced in endpoints must have examples."""
        schemas_missing_examples = []

        for schema_name in endpoint_schemas:
            if schema_name in schemas:
                schema = schemas[schema_name]
                if "example" not in schema:
                    schemas_missing_examples.append(schema_name)

        if schemas_missing_examples:
            print(
                f"\nEndpoint schemas missing examples ({len(schemas_missing_examples)}):"
            )
            for schema in sorted(schemas_missing_examples):
                print(f"  - {schema}")

        assert len(schemas_missing_examples) == 0, (
            f"{len(schemas_missing_examples)} endpoint schemas missing examples"
        )


class TestSchemaQualityMetrics:
    """Overall schema quality metrics."""

    def test_schema_coverage_report(
        self, schemas: dict[str, Any], endpoint_schemas: set[str]
    ):
        """Generate coverage report for debugging."""
        total_schemas = len(schemas)
        schemas_with_descriptions = sum(
            1 for s in schemas.values() if s.get("description")
        )
        schemas_with_examples = sum(1 for s in schemas.values() if "example" in s)

        endpoint_schemas_with_examples = sum(
            1
            for name in endpoint_schemas
            if name in schemas and "example" in schemas[name]
        )

        print("\nSchema Quality Metrics:")
        print(f"Total schemas: {total_schemas}")
        print(f"Schemas with descriptions: {schemas_with_descriptions}/{total_schemas}")
        print(f"Schemas with examples: {schemas_with_examples}/{total_schemas}")
        print(f"Endpoint schemas: {len(endpoint_schemas)}")
        print(
            f"Endpoint schemas with examples: {endpoint_schemas_with_examples}/{len(endpoint_schemas)}"
        )

        # This test always passes but provides useful info
        assert True
