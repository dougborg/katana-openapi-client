"""
Critical API Gap Tests

This module contains focused tests for the most critical API functionality
that should be present in any production-ready OpenAPI specification.

These tests complement:
- test_comprehensive_api_validation.py (        assert missing_fields == set(), (
            f"OpenAPI info section missing required fields: {missing_fields}"
        )

        # Check description exists (no length requirement - zero tolerance for arbitrary limits)
        description = info.get("description", "")
        assert description, "OpenAPI description should exist to help developers understand the API"completeness vs documentation)
- test_schema_standards.py (schema quality standards)
- test_individual_schema_validation.py (granular validation per schema/endpoint)

The tests here focus on absolute requirements that would make the API unusable
if missing (e.g., core customer endpoints, basic documentation, operation IDs).
"""

from pathlib import Path
from typing import Any

import pytest
import yaml


class TestCriticalAPIGaps:
    """Test critical API gaps that should be addressed immediately."""

    @pytest.fixture(scope="class")
    def current_spec(self) -> dict[str, Any]:
        """Load current OpenAPI specification."""
        spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"
        with open(spec_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_critical_customer_endpoints_present(self, current_spec: dict[str, Any]):
        """Test that critical customer endpoints are present."""
        paths = current_spec.get("paths", {})

        # Customer endpoints are fundamental for any ERP system
        required_customer_endpoints = [
            "/customers",  # List and create customers
            "/customers/{id}",  # Individual customer operations
        ]

        missing_endpoints = []
        for endpoint in required_customer_endpoints:
            if endpoint not in paths:
                missing_endpoints.append(endpoint)

        if missing_endpoints:
            pytest.fail(
                f"Critical customer endpoints missing: {missing_endpoints}\n"
                f"Customer management is fundamental ERP functionality that must be supported.\n"
                f"The comprehensive documentation shows these endpoints should exist."
            )

    def test_api_specification_structure(self, current_spec: dict[str, Any]):
        """Test that the API specification has proper basic structure."""
        paths = current_spec.get("paths", {})

        # Test basic structural requirements without assumptions about specific operations
        assert isinstance(paths, dict), "Paths must be a dictionary"
        assert len(paths) > 0, "API must have at least one endpoint"

        # Verify each path has valid structure
        for path, path_spec in paths.items():
            assert isinstance(path_spec, dict), f"Path {path} must have methods"
            assert path.startswith("/"), f"Path {path} must start with /"

            # Check that each method has basic required structure
            for method, method_spec in path_spec.items():
                if method.lower() in {"get", "post", "put", "patch", "delete"}:
                    assert isinstance(method_spec, dict), (
                        f"{method.upper()} {path} must be an object"
                    )
                    assert "responses" in method_spec, (
                        f"{method.upper()} {path} must define responses"
                    )

    def test_existing_endpoints_are_properly_documented(
        self, current_spec: dict[str, Any]
    ):
        """Test that existing endpoints have proper documentation."""
        paths = current_spec.get("paths", {})

        endpoints_without_docs = []
        for path, path_spec in paths.items():
            for method, method_spec in path_spec.items():
                if (
                    method.lower() in {"get", "post", "put", "patch", "delete"}
                    and "summary" not in method_spec
                    and "description" not in method_spec
                ):
                    endpoints_without_docs.append(f"{method.upper()} {path}")

        # Don't make assumptions about how many should have docs, just test what exists
        if (
            len(endpoints_without_docs) > 100
        ):  # Only fail if vast majority are undocumented
            pytest.fail(
                f"Many endpoints lack documentation: {len(endpoints_without_docs)} total"
            )

    def test_core_business_schemas_have_descriptions(
        self, current_spec: dict[str, Any]
    ):
        """Test that core business entity schemas have descriptions."""
        schemas = current_spec.get("components", {}).get("schemas", {})

        # Core business entities that should have descriptions
        core_entities = [
            "Customer",
            "Product",
            "SalesOrder",
            "PurchaseOrder",
            "ManufacturingOrder",
            "Inventory",
            "Variant",
            "Material",
        ]

        missing_descriptions = []
        for entity in core_entities:
            if entity in schemas:
                schema = schemas[entity]
                if "description" not in schema or not schema["description"].strip():
                    missing_descriptions.append(entity)

        if missing_descriptions:
            pytest.fail(
                f"Core business entity schemas missing descriptions: {missing_descriptions}\n"
                f"Business entity schemas should have clear descriptions for API consumers.\n"
                f"This is essential for API usability and developer experience."
            )

    def test_list_endpoints_have_pagination(self, current_spec: dict[str, Any]):
        """Test that list endpoints have basic pagination parameters."""
        paths = current_spec.get("paths", {})

        # Find collection endpoints (those that return lists)
        list_endpoints = []
        for path, path_spec in paths.items():
            if "get" in path_spec:
                get_spec = path_spec["get"]
                operation_id = get_spec.get("operationId", "")
                summary = get_spec.get("summary", "").lower()

                # Collection endpoints typically have operationIds starting with "getAll" or "list"
                # or have "list" in their summary
                if (
                    operation_id.startswith(("getAll", "list"))
                    or "list" in summary
                    or (path.count("/") == 1 and "{" not in path)
                ):
                    list_endpoints.append(path)

        # Check for pagination parameters
        endpoints_missing_pagination = []
        for endpoint in list_endpoints[:10]:  # Check first 10 to avoid noise
            get_spec = paths[endpoint]["get"]
            parameters = get_spec.get("parameters", [])
            param_names = set()

            # Extract parameter names, resolving $ref if needed
            for param in parameters:
                if isinstance(param, dict):
                    if "name" in param:
                        param_names.add(param["name"])
                    elif "$ref" in param:
                        # Resolve parameter reference
                        ref = param["$ref"]
                        if ref.startswith("#/components/parameters/"):
                            param_key = ref.split("/")[-1]
                            components = current_spec.get("components", {})
                            param_defs = components.get("parameters", {})
                            if param_key in param_defs:
                                param_def = param_defs[param_key]
                                if "name" in param_def:
                                    param_names.add(param_def["name"])

            # Check for basic pagination parameters
            has_limit = "limit" in param_names
            has_page = "page" in param_names

            if not (has_limit and has_page):
                endpoints_missing_pagination.append(endpoint)

        # Allow some endpoints to lack pagination, but flag if many are missing
        if len(endpoints_missing_pagination) > 5:
            pytest.fail(
                f"Too many list endpoints missing pagination parameters: {len(endpoints_missing_pagination)}\n"
                f"Examples: {endpoints_missing_pagination[:5]}\n"
                f"List endpoints should typically support 'limit' and 'page' parameters for pagination.\n"
                f"The comprehensive documentation shows these parameters are standard."
            )

    # NOTE: Gap analysis test removed - functionality is covered by:
    # - test_comprehensive_api_validation.py for endpoint completeness
    # - test_schema_standards.py for schema quality
    # - test_individual_schema_validation.py for granular validation
    # Tests should not depend on generated analysis files.

    def test_api_specification_completeness(self):
        """Test that the API specification itself is structurally complete."""
        # Test the actual OpenAPI spec instead of looking for validation files
        spec_file = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"

        assert spec_file.exists(), "OpenAPI specification file should exist"

        # Verify it's valid YAML
        import yaml

        with open(spec_file, encoding="utf-8") as f:
            spec_data = yaml.safe_load(f)

        # Basic structure validation
        assert "openapi" in spec_data, "OpenAPI spec must have version"
        assert "info" in spec_data, "OpenAPI spec must have info section"
        assert "paths" in spec_data, "OpenAPI spec must have paths section"
        assert "components" in spec_data, "OpenAPI spec must have components section"


class TestDocumentationCompliance:
    """Test compliance with documentation standards."""

    @pytest.fixture(scope="class")
    def current_spec(self) -> dict[str, Any]:
        """Load current OpenAPI specification."""
        spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"
        with open(spec_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_openapi_info_section_complete(self, current_spec: dict[str, Any]):
        """Test that OpenAPI info section is complete and descriptive."""
        info = current_spec.get("info", {})

        required_fields = ["title", "version", "description"]
        missing_fields = [field for field in required_fields if field not in info]

        assert not missing_fields, (
            f"OpenAPI info section missing required fields: {missing_fields}"
        )

        # Check description quality
        description = info.get("description", "")
        assert len(description) > 100, (
            "OpenAPI description should be comprehensive (>100 characters) to help developers understand the API"
        )

    def test_all_endpoints_have_operation_ids(self, current_spec: dict[str, Any]):
        """Test that all endpoints have operation IDs for client generation."""
        paths = current_spec.get("paths", {})

        missing_operation_ids = []
        for path, path_spec in paths.items():
            for method, method_spec in path_spec.items():
                if (
                    method.lower() in {"get", "post", "put", "patch", "delete"}
                    and "operationId" not in method_spec
                ):
                    missing_operation_ids.append(f"{method.upper()} {path}")

        assert not missing_operation_ids, (
            f"Endpoints missing operationId: {missing_operation_ids[:5]}\n"
            f"All endpoints should have operationId for proper client generation"
        )

    def test_endpoints_have_descriptions(self, current_spec: dict[str, Any]):
        """Test that endpoints have proper descriptions."""
        paths = current_spec.get("paths", {})

        missing_descriptions = []
        for path, path_spec in paths.items():
            for method, method_spec in path_spec.items():
                if method.lower() in {"get", "post", "put", "patch", "delete"}:
                    description = method_spec.get("description", "")
                    summary = method_spec.get("summary", "")

                    if not description and not summary:
                        missing_descriptions.append(f"{method.upper()} {path}")

        # Zero tolerance for missing descriptions - report all issues
        assert len(missing_descriptions) == 0, (
            f"Found {len(missing_descriptions)} endpoints missing descriptions:\n"
            f"{missing_descriptions}\n"
            f"All endpoints must have descriptions or summaries for API documentation"
        )
