"""
OpenAPI Specification Structure and Syntax Validation

This module validates the basic OpenAPI document structure, syntax, and metadata.
Focuses on document-level validation without testing individual schemas or endpoints.

Consolidates:
- test_openapi_validation.py (basic structure validation)
- Structural parts of test_openapi_comprehensive.py
- Basic structural requirements from test_critical_api_gaps.py
"""

from pathlib import Path
from typing import Any

import pytest
import yaml


class TestOpenAPISpecification:
    """Test OpenAPI specification document structure and syntax."""

    @pytest.fixture(scope="class")
    def spec(self) -> dict[str, Any]:
        """Load OpenAPI specification."""
        spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"
        with open(spec_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_openapi_version_compliance(self, spec: dict[str, Any]):
        """Test OpenAPI version is supported."""
        assert "openapi" in spec, "OpenAPI specification must have version"
        version = spec["openapi"]
        assert version.startswith("3."), f"OpenAPI version {version} should be 3.x"

    def test_required_sections_present(self, spec: dict[str, Any]):
        """Test that all required OpenAPI sections are present."""
        required_sections = ["openapi", "info", "paths", "components"]

        for section in required_sections:
            assert section in spec, (
                f"OpenAPI specification missing required section: {section}"
            )

    def test_info_section_completeness(self, spec: dict[str, Any]):
        """Test that info section has all required fields."""
        info = spec.get("info", {})

        required_fields = ["title", "version", "description"]
        missing_fields = [field for field in required_fields if field not in info]

        assert not missing_fields, (
            f"Info section missing required fields: {missing_fields}"
        )

        # Check description exists (no length requirement - zero tolerance for arbitrary limits)
        description = info.get("description", "")
        assert description, (
            "OpenAPI description should exist to help developers understand the API"
        )

    def test_paths_structure_validity(self, spec: dict[str, Any]):
        """Test that paths section has valid structure."""
        paths = spec.get("paths", {})

        assert isinstance(paths, dict), "Paths must be a dictionary"
        assert len(paths) > 0, "API must have at least one endpoint"

        # Verify each path has valid structure
        for path, path_spec in paths.items():
            assert isinstance(path_spec, dict), f"Path {path} must have methods"
            assert path.startswith("/"), f"Path {path} must start with /"

            # Check that each HTTP method has proper structure
            for method, method_spec in path_spec.items():
                if method.lower() in {
                    "get",
                    "post",
                    "put",
                    "patch",
                    "delete",
                    "head",
                    "options",
                }:
                    assert isinstance(method_spec, dict), (
                        f"{method.upper()} {path} must be an object"
                    )
                    assert "responses" in method_spec, (
                        f"{method.upper()} {path} must define responses"
                    )

    def test_components_structure_validity(self, spec: dict[str, Any]):
        """Test that components section has valid structure."""
        components = spec.get("components", {})

        assert isinstance(components, dict), "Components must be a dictionary"

        # Check schemas structure if present
        if "schemas" in components:
            schemas = components["schemas"]
            assert isinstance(schemas, dict), "Components.schemas must be a dictionary"
            assert len(schemas) > 0, "Components.schemas should not be empty if defined"

        # Check parameters structure if present
        if "parameters" in components:
            parameters = components["parameters"]
            assert isinstance(parameters, dict), (
                "Components.parameters must be a dictionary"
            )

    def test_operation_ids_unique(self, spec: dict[str, Any]):
        """Test that all operation IDs are unique across the API."""
        paths = spec.get("paths", {})
        operation_ids = []

        for _path, path_spec in paths.items():
            for method, method_spec in path_spec.items():
                if (
                    method.lower()
                    in {
                        "get",
                        "post",
                        "put",
                        "patch",
                        "delete",
                        "head",
                        "options",
                    }
                    and "operationId" in method_spec
                ):
                    operation_ids.append(method_spec["operationId"])

        # Check for duplicates
        duplicates = [
            op_id for op_id in set(operation_ids) if operation_ids.count(op_id) > 1
        ]
        assert not duplicates, f"Duplicate operation IDs found: {duplicates}"

    def test_security_schemes_defined(self, spec: dict[str, Any]):
        """Test that security schemes are properly defined if used."""
        components = spec.get("components", {})

        # If security is used anywhere, schemes should be defined
        paths = spec.get("paths", {})
        uses_security = False

        for _path, path_spec in paths.items():
            for method, method_spec in path_spec.items():
                if method.lower() in {
                    "get",
                    "post",
                    "put",
                    "patch",
                    "delete",
                    "head",
                    "options",
                } and ("security" in method_spec or "security" in spec):
                    uses_security = True
                    break
            if uses_security:
                break

        if uses_security:
            assert "securitySchemes" in components, (
                "Security is used but no securitySchemes defined in components"
            )

    def test_yaml_syntax_validity(self):
        """Test that the OpenAPI spec file has valid YAML syntax."""
        spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"

        assert spec_path.exists(), "OpenAPI specification file should exist"

        # This will raise an exception if YAML is invalid
        with open(spec_path, encoding="utf-8") as f:
            yaml.safe_load(f)

    def test_parameter_definition_consistency(self, spec: dict[str, Any]):
        """Test that parameters are only defined at operation level for consistency."""
        paths = spec.get("paths", {})

        path_level_param_violations = []

        for path, path_spec in paths.items():
            # Check if this path has path-level parameters
            if "parameters" in path_spec:
                path_level_param_violations.append(path)

        assert len(path_level_param_violations) == 0, (
            f"Found {len(path_level_param_violations)} paths with path-level parameters. "
            f"For consistency, all parameters should be defined at operation level using $ref. "
            f"Violating paths: {path_level_param_violations}"
        )
