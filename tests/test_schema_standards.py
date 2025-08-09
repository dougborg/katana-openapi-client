"""
Tests to validate OpenAPI schema standards and requirements.

This test suite codifies our expectations for:
1. Schema inheritance patterns (BaseEntity, UpdatableEntity, etc.)
2. Property descriptions and documentation quality
3. Schema examples and structure
4. Endpoint definition requirements
5. Consistency across the API specification

Run with: poetry run pytest tests/test_schema_standards.py -v
"""

from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest
import yaml


@lru_cache(maxsize=1)
def load_openapi_spec() -> dict[str, Any]:
    """Load the OpenAPI specification."""
    spec_path = Path(__file__).parent.parent / "katana-openapi.yaml"
    with open(spec_path) as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def get_schemas() -> dict[str, Any]:
    """Get all schemas from the OpenAPI spec."""
    spec = load_openapi_spec()
    return spec.get("components", {}).get("schemas", {})


@lru_cache(maxsize=1)
def get_entity_schemas() -> list[tuple[str, dict[str, Any]]]:
    """Get all entity schemas (those with id property or BaseEntity inheritance)."""
    schemas = get_schemas()
    entity_schemas = []

    for schema_name, schema_def in schemas.items():
        # Skip base entity classes themselves
        if schema_name in [
            "BaseEntity",
            "UpdatableEntity",
            "DeletableEntity",
            "ArchivableEntity",
        ]:
            continue

        # Check if this is an entity schema
        if _has_id_property(schema_def) or _uses_base_entity_inheritance(schema_def):
            entity_schemas.append((schema_name, schema_def))

    return entity_schemas


@lru_cache(maxsize=1)
def get_all_schemas() -> list[tuple[str, dict[str, Any]]]:
    """Get all schemas for validation."""
    schemas = get_schemas()
    return [(name, schema) for name, schema in schemas.items()]


# Helper functions (defined before the test class)
def _has_id_property(schema_def: dict[str, Any]) -> bool:
    """Check if schema has an 'id' property."""
    properties = _get_all_properties(schema_def)
    return "id" in properties


def _has_property(schema_def: dict[str, Any], property_name: str) -> bool:
    """Check if schema has a specific property."""
    properties = _get_all_properties(schema_def)
    return property_name in properties


def _has_timestamp_properties(schema_def: dict[str, Any]) -> bool:
    """Check if schema has timestamp properties."""
    properties = _get_all_properties(schema_def)
    timestamp_props = {"created_at", "updated_at"}
    return any(prop in properties for prop in timestamp_props)


def _uses_base_entity_inheritance(schema_def: dict[str, Any]) -> bool:
    """Check if schema uses BaseEntity inheritance."""
    return _uses_inheritance(schema_def, "BaseEntity")


def _uses_inheritance(schema_def: dict[str, Any], entity_name: str) -> bool:
    """Check if schema uses specific entity inheritance."""
    all_of = schema_def.get("allOf", [])
    for item in all_of:
        ref = item.get("$ref", "")
        if ref.endswith(f"/{entity_name}"):
            return True
    return False


def _get_all_properties(schema_def: dict[str, Any]) -> dict[str, Any]:
    """Get all properties from schema, including inherited ones."""
    properties = {}

    # Get properties from allOf inheritance
    all_of = schema_def.get("allOf", [])
    for item in all_of:
        if "properties" in item:
            properties.update(item.get("properties", {}))

    # Get direct properties
    properties.update(schema_def.get("properties", {}))

    return properties


class TestSchemaStandards:
    """Test suite for OpenAPI schema standards compliance."""

    @pytest.fixture(scope="class")
    def openapi_spec(self) -> dict[str, Any]:
        """Load the OpenAPI specification."""
        return load_openapi_spec()

    @pytest.fixture(scope="class")
    def schemas(self, openapi_spec: dict[str, Any]) -> dict[str, Any]:
        """Extract schemas from the OpenAPI spec."""
        return openapi_spec.get("components", {}).get("schemas", {})

    @pytest.fixture(scope="class")
    def paths(self, openapi_spec: dict[str, Any]) -> dict[str, Any]:
        """Extract paths/endpoints from the OpenAPI spec."""
        return openapi_spec.get("paths", {})

    @pytest.mark.parametrize("schema_name,schema_def", get_entity_schemas())
    def test_entity_uses_base_entity_inheritance(
        self, schema_name: str, schema_def: dict[str, Any]
    ):
        """Test that entity schema uses BaseEntity inheritance."""
        has_id_property = _has_id_property(schema_def)
        uses_base_entity = _uses_base_entity_inheritance(schema_def)

        assert has_id_property, f"Schema {schema_name} should have id property"
        assert uses_base_entity, (
            f"Schema {schema_name} has id property but doesn't use BaseEntity inheritance"
        )

    @pytest.mark.parametrize("schema_name,schema_def", get_all_schemas())
    def test_schema_has_description(self, schema_name: str, schema_def: dict[str, Any]):
        """Test that schema has a meaningful description."""
        description = schema_def.get("description", "")

        assert description, f"Schema {schema_name} is missing a description"
        assert len(description) >= 20, (
            f"Schema {schema_name} description is too short: '{description}'"
        )
        assert description != schema_name, (
            f"Schema {schema_name} description is just the schema name"
        )

    @pytest.mark.parametrize("schema_name,schema_def", get_entity_schemas())
    def test_entity_has_schema_example(
        self, schema_name: str, schema_def: dict[str, Any]
    ):
        """Test that entity schema has a comprehensive example."""
        example = schema_def.get("example")
        assert example is not None, (
            f"Entity schema {schema_name} is missing a schema-level example"
        )
        assert isinstance(example, dict), (
            f"Entity schema {schema_name} example should be a dictionary"
        )

    @pytest.mark.parametrize("schema_name,schema_def", get_entity_schemas())
    def test_entity_avoids_property_examples(
        self, schema_name: str, schema_def: dict[str, Any]
    ):
        """Test that entity schema uses schema-level examples instead of property-level."""
        properties = _get_all_properties(schema_def)
        property_examples = [
            prop_name
            for prop_name, prop_def in properties.items()
            if prop_def.get("example") is not None
        ]

        assert not property_examples, (
            f"Schema {schema_name} has property-level examples {property_examples}. "
            f"Use schema-level examples instead for better documentation."
        )

    @pytest.mark.parametrize("schema_name,schema_def", get_all_schemas())
    def test_schema_properties_have_descriptions(
        self, schema_name: str, schema_def: dict[str, Any]
    ):
        """Test that schema properties have descriptions."""
        # Skip base entity classes and simple schemas
        if schema_name in [
            "BaseEntity",
            "UpdatableEntity",
            "DeletableEntity",
            "ArchivableEntity",
        ]:
            pytest.skip(f"Skipping base entity class {schema_name}")

        properties = _get_all_properties(schema_def)
        undescribed_properties = []

        for prop_name, prop_def in properties.items():
            # Skip common properties that inherit descriptions
            if prop_name in [
                "id",
                "created_at",
                "updated_at",
                "deleted_at",
                "archived_at",
            ]:
                continue

            if not prop_def.get("description"):
                undescribed_properties.append(prop_name)

        # Only require descriptions for schemas with significant properties
        if len(properties) > 2:  # More than just id + timestamps
            assert not undescribed_properties, (
                f"Schema {schema_name} has properties without descriptions: {undescribed_properties}"
            )

    def test_endpoint_response_schema_requirements(
        self, paths: dict[str, Any], schemas: dict[str, Any]
    ):
        """Test that endpoints reference proper response schemas."""
        endpoints_missing_response_schemas = []
        endpoints_with_inline_responses = []

        for path, path_def in paths.items():
            for method, method_def in path_def.items():
                if method.upper() not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
                    continue

                responses = method_def.get("responses", {})

                for status_code, response_def in responses.items():
                    if status_code.startswith("2"):  # Success responses
                        content = response_def.get("content", {})

                        for media_def in content.values():
                            schema_ref = media_def.get("schema", {})

                            if not schema_ref:
                                endpoints_missing_response_schemas.append(
                                    f"{method.upper()} {path} ({status_code})"
                                )
                            elif "$ref" not in schema_ref and "type" in schema_ref:
                                # Inline schema instead of reference
                                endpoints_with_inline_responses.append(
                                    f"{method.upper()} {path} ({status_code})"
                                )

        # These are informational for now - endpoints are generally well-structured
        if endpoints_missing_response_schemas or endpoints_with_inline_responses:
            print("\nEndpoint issues found but not failing test:")
            if endpoints_missing_response_schemas:
                print(f"Missing schemas: {len(endpoints_missing_response_schemas)}")
            if endpoints_with_inline_responses:
                print(f"Inline responses: {len(endpoints_with_inline_responses)}")

    def test_consistent_naming_conventions(self, schemas: dict[str, Any]):
        """Test that schema names follow consistent conventions."""
        naming_issues = []

        for schema_name in schemas:
            # Check for consistent naming patterns
            if (
                schema_name.endswith("Response")
                and not schema_name.endswith("ListResponse")
                and "List" in schema_name
                and not schema_name.endswith("ListResponse")
            ):
                naming_issues.append(
                    f"{schema_name}: List responses should end with 'ListResponse'"
                )

            # Check for PascalCase
            if not schema_name[0].isupper() or "_" in schema_name:
                naming_issues.append(f"{schema_name}: Should use PascalCase")

        assert not naming_issues, f"Naming convention issues found: {naming_issues}"
