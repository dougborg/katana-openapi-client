"""
Comprehensive Schema Validation

This module provides comprehensive parameterized testing for ALL schemas in the OpenAPI spec.
Every schema gets identical validation treatment - no exceptions for "core" vs "other" schemas.

Consolidates:
- test_schema_standards.py (schema quality standards)
- Schema validation parts from test_comprehensive_api_validation.py
- Schema validation parts from test_openapi_comprehensive.py
- Schema validation parts from test_individual_schema_validation.py

All schema testing is now parameterized for complete equality and automatic scaling.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml


def pytest_generate_tests(metafunc):
    """Generate parameterized tests for schemas."""
    # Load OpenAPI spec
    spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"
    with open(spec_path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    if "schema_name" in metafunc.fixturenames:
        schemas = spec.get("components", {}).get("schemas", {})
        schema_names = list(schemas.keys())
        metafunc.parametrize("schema_name", schema_names, ids=lambda x: f"schema-{x}")

    elif "referenced_schema_name" in metafunc.fixturenames:
        # Get schemas that are referenced in endpoints
        schemas = spec.get("components", {}).get("schemas", {})
        paths = spec.get("paths", {})
        referenced = set()

        def find_schema_refs(obj: Any, prefix: str = "#/components/schemas/"):
            """Recursively find schema references."""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if (
                        key == "$ref"
                        and isinstance(value, str)
                        and value.startswith(prefix)
                    ):
                        schema_name = value[len(prefix) :]
                        referenced.add(schema_name)
                    else:
                        find_schema_refs(value, prefix)
            elif isinstance(obj, list):
                for item in obj:
                    find_schema_refs(item, prefix)

        # Find references in paths and schemas
        find_schema_refs(paths)
        find_schema_refs(schemas)

        referenced_list = list(referenced)
        metafunc.parametrize(
            "referenced_schema_name", referenced_list, ids=lambda x: f"ref-schema-{x}"
        )


class TestSchemaComprehensive:
    """Comprehensive parameterized testing for all schemas."""

    @pytest.fixture(scope="class")
    def spec(self) -> dict[str, Any]:
        """Load OpenAPI specification."""
        spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"
        with open(spec_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_schema_has_description(self, schema_name: str, spec: dict[str, Any]):
        """Test that every schema has a description."""
        schemas = spec.get("components", {}).get("schemas", {})
        schema = schemas[schema_name]

        assert "description" in schema, f"Schema '{schema_name}' missing description"

        description = schema["description"]
        assert isinstance(description, str), (
            f"Schema '{schema_name}' description must be a string"
        )
        assert description.strip(), (
            f"Schema '{schema_name}' description cannot be empty"
        )
        assert len(description.strip()) >= 10, (
            f"Schema '{schema_name}' description too short: '{description}' "
            f"(minimum 10 characters for meaningful documentation)"
        )

    def test_schema_properties_have_descriptions(
        self, schema_name: str, spec: dict[str, Any]
    ):
        """Test that all properties in every schema have descriptions."""
        schemas = spec.get("components", {}).get("schemas", {})
        schema = schemas[schema_name]

        properties = schema.get("properties", {})
        if not properties:
            pytest.skip(f"Schema '{schema_name}' has no properties to validate")

        missing_descriptions = []

        for prop_name, prop_spec in properties.items():
            if isinstance(prop_spec, dict):
                if "description" not in prop_spec:
                    missing_descriptions.append(prop_name)
                elif not prop_spec["description"].strip():
                    missing_descriptions.append(f"{prop_name} (empty)")

        assert not missing_descriptions, (
            f"Schema '{schema_name}' has properties missing descriptions: {missing_descriptions}"
        )

    def test_schema_structure_standards(self, schema_name: str, spec: dict[str, Any]):
        """Test that every schema follows structure standards."""
        schemas = spec.get("components", {}).get("schemas", {})
        schema = schemas[schema_name]

        # Schema must be an object
        assert isinstance(schema, dict), f"Schema '{schema_name}' must be an object"

        # If it has properties, they should be properly defined
        if "properties" in schema:
            properties = schema["properties"]
            assert isinstance(properties, dict), (
                f"Schema '{schema_name}' properties must be an object"
            )

            for prop_name, prop_spec in properties.items():
                assert isinstance(prop_spec, dict), (
                    f"Property '{prop_name}' in schema '{schema_name}' must be an object"
                )

                # Property should have a type (directly or via $ref)
                has_type = (
                    "type" in prop_spec or "$ref" in prop_spec or "allOf" in prop_spec
                )
                assert has_type, (
                    f"Property '{prop_name}' in schema '{schema_name}' missing type definition"
                )

    def test_schema_base_entity_inheritance(
        self, schema_name: str, spec: dict[str, Any]
    ):
        """Test BaseEntity inheritance patterns where applicable."""
        schemas = spec.get("components", {}).get("schemas", {})
        schema = schemas[schema_name]

        # Check if this schema uses allOf (inheritance pattern)
        if "allOf" in schema:
            all_of = schema["allOf"]
            assert isinstance(all_of, list), (
                f"Schema '{schema_name}' allOf must be a list"
            )

            # Check for BaseEntity reference
            has_base_entity = False
            for item in all_of:
                if (
                    isinstance(item, dict)
                    and item.get("$ref") == "#/components/schemas/BaseEntity"
                ):
                    has_base_entity = True
                    break

            # If using inheritance, should typically inherit from BaseEntity
            # (Allow some exceptions for specific patterns)
            if not has_base_entity and schema_name not in [
                "BaseEntity",
                "ErrorResponse",
            ]:
                # This is informational - not all schemas need to inherit from BaseEntity
                pass

    def test_referenced_schema_quality(
        self, referenced_schema_name: str, spec: dict[str, Any]
    ):
        """Test extra quality requirements for schemas referenced in endpoints."""
        schemas = spec.get("components", {}).get("schemas", {})
        schema = schemas[referenced_schema_name]

        # Referenced schemas should have examples or be very well documented
        description = schema.get("description", "")
        has_example = "example" in schema

        if not has_example:
            # If no example, description should be comprehensive
            assert len(description) >= 20, (
                f"Referenced schema '{referenced_schema_name}' lacks example and has insufficient description "
                f"(minimum 20 characters): '{description}'"
            )

    def test_schema_naming_conventions(self, schema_name: str, spec: dict[str, Any]):
        """Test that schema names follow naming conventions."""
        # Schema names should be PascalCase
        assert schema_name[0].isupper(), (
            f"Schema name '{schema_name}' should start with uppercase"
        )

        # Should not contain underscores (prefer PascalCase)
        if "_" in schema_name:
            # Allow some exceptions for generated names
            allowed_patterns = ["_Response", "_Request", "_Error"]
            is_allowed = any(pattern in schema_name for pattern in allowed_patterns)
            if not is_allowed:
                pytest.fail(
                    f"Schema name '{schema_name}' contains underscores, prefer PascalCase"
                )

    def test_schema_type_consistency(self, schema_name: str, spec: dict[str, Any]):
        """Test that schema types are consistently defined."""
        schemas = spec.get("components", {}).get("schemas", {})
        schema = schemas[schema_name]

        # If schema has a type, it should be valid
        if "type" in schema:
            valid_types = [
                "object",
                "array",
                "string",
                "number",
                "integer",
                "boolean",
                "null",
            ]
            schema_type = schema["type"]
            assert schema_type in valid_types, (
                f"Schema '{schema_name}' has invalid type: '{schema_type}'"
            )

        # If schema has properties, it should typically be type: object
        if "properties" in schema and "type" in schema:
            assert schema["type"] == "object", (
                f"Schema '{schema_name}' has properties but type is not 'object'"
            )


class TestSchemaCoverageMetrics:
    """Test overall schema coverage and quality metrics."""

    @pytest.fixture(scope="class")
    def spec(self) -> dict[str, Any]:
        """Load OpenAPI specification."""
        spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"
        with open(spec_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_schema_coverage_metrics(self, spec: dict[str, Any]):
        """Test overall schema coverage and quality metrics."""
        schemas = spec.get("components", {}).get("schemas", {})
        paths = spec.get("paths", {})

        # Get referenced schemas
        referenced = set()

        def find_schema_refs(obj: Any, prefix: str = "#/components/schemas/"):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if (
                        key == "$ref"
                        and isinstance(value, str)
                        and value.startswith(prefix)
                    ):
                        schema_name = value[len(prefix) :]
                        referenced.add(schema_name)
                    else:
                        find_schema_refs(value, prefix)
            elif isinstance(obj, list):
                for item in obj:
                    find_schema_refs(item, prefix)

        find_schema_refs(paths)
        find_schema_refs(schemas)

        # Basic metrics
        all_schemas = list(schemas.keys())
        total_schemas = len(all_schemas)
        referenced_count = len(referenced)

        assert total_schemas > 0, "API should have at least one schema"

        # Calculate description coverage
        schemas_with_descriptions = 0
        for schema_name in all_schemas:
            schema = schemas[schema_name]
            if "description" in schema and schema["description"].strip():
                schemas_with_descriptions += 1

        description_coverage = (
            schemas_with_descriptions / total_schemas if total_schemas > 0 else 0
        )

        # Expect high coverage (allow some tolerance for generated/utility schemas)
        assert description_coverage >= 0.8, (
            f"Schema description coverage too low: {description_coverage:.1%} "
            f"({schemas_with_descriptions}/{total_schemas})"
        )

        # Log metrics for visibility
        print("\n📊 Schema Quality Metrics:")
        print(f"   Total schemas: {total_schemas}")
        print(f"   Referenced in endpoints: {referenced_count}")
        print(f"   Description coverage: {description_coverage:.1%}")
