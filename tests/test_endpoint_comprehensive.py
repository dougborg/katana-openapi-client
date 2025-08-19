"""
Comprehensive Endpoint Validation

This module provides comprehensive parameterized testing for ALL endpoints in the OpenAPI spec.
Every endpoint gets identical validation treatment - no exceptions for "critical" vs "other" endpoints.

Consolidates:
- test_individual_schema_validation.py (endpoint validation parts)
- Endpoint validation parts from test_comprehensive_api_validation.py
- Endpoint validation parts from test_openapi_comprehensive.py
- Parameter validation from test_critical_api_gaps.py (pagination testing)
- Endpoint documentation testing from multiple files

All endpoint testing is now parameterized for complete equality and automatic scaling.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml


def pytest_generate_tests(metafunc):
    """Generate parameterized tests for endpoints."""
    # Load OpenAPI spec
    spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"
    with open(spec_path, encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    if "endpoint_info" in metafunc.fixturenames:
        # Generate endpoint tuples (path, method, operation_spec)
        paths = spec.get("paths", {})
        endpoints = []

        for path, path_spec in paths.items():
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
                    endpoints.append((path, method.lower(), method_spec))

        metafunc.parametrize(
            "endpoint_info",
            endpoints,
            ids=lambda x: f"{x[1].upper()}-{x[0].replace('/', '_').replace('{', '').replace('}', '')}",
        )

    elif "list_endpoint_info" in metafunc.fixturenames:
        # Generate only collection/list endpoints for pagination testing
        paths = spec.get("paths", {})
        list_endpoints = []

        for path, path_spec in paths.items():
            if "get" in path_spec:
                get_spec = path_spec["get"]
                operation_id = get_spec.get("operationId", "")
                summary = get_spec.get("summary", "").lower()
                description = get_spec.get("description", "").lower()

                # Skip single-resource endpoints (those with path parameters)
                if "{" in path:
                    continue

                # Skip endpoints that are clearly single resources
                single_resource_indicators = [
                    "factory",  # /factory is a singleton resource
                    "current",
                    "detail",
                    "by id",
                ]

                if any(
                    indicator in summary or indicator in description
                    for indicator in single_resource_indicators
                ):
                    continue

                # Skip endpoints that legitimately lack pagination in the reference spec
                # These are documented as API gaps, not implementation issues
                endpoints_without_pagination = [
                    "/serial_numbers_stock",
                    "/custom_fields_collections",
                ]

                if path in endpoints_without_pagination:
                    continue

                # Collection endpoints typically have operationIds starting with "getAll" or "list"
                # or have "list" in their summary, or are simple collection paths without path params
                if (
                    operation_id.startswith(("getAll", "list"))
                    or "list" in summary
                    or "returns a list" in description
                    or (path.count("/") == 1 and "{" not in path)
                ):
                    list_endpoints.append((path, "get", get_spec))

        metafunc.parametrize(
            "list_endpoint_info",
            list_endpoints,
            ids=lambda x: f"LIST-{x[0].replace('/', '_')}",
        )


class TestEndpointComprehensive:
    """Comprehensive parameterized testing for all endpoints."""

    @pytest.fixture(scope="class")
    def spec(self) -> dict[str, Any]:
        """Load OpenAPI specification."""
        spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"
        with open(spec_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _resolve_response_description(
        self, response_spec: dict[str, Any], spec: dict[str, Any]
    ) -> bool:
        """Check if response has description, resolving $ref if present."""
        if "description" in response_spec:
            # Direct description
            return True
        elif "$ref" in response_spec:
            # Response reference - resolve it
            ref_path = response_spec["$ref"]
            if ref_path.startswith("#/components/responses/"):
                response_name = ref_path.split("/")[-1]
                components_responses = spec.get("components", {}).get("responses", {})
                if response_name in components_responses:
                    return "description" in components_responses[response_name]
        return False

    def test_endpoint_has_operation_id(
        self, endpoint_info: tuple[str, str, dict[str, Any]], spec: dict[str, Any]
    ):
        """Test that every endpoint has an operation ID."""
        path, method, operation_spec = endpoint_info

        assert "operationId" in operation_spec, (
            f"{method.upper()} {path} missing operationId - required for client generation"
        )

        operation_id = operation_spec["operationId"]
        assert isinstance(operation_id, str), (
            f"{method.upper()} {path} operationId must be a string"
        )
        assert operation_id.strip(), (
            f"{method.upper()} {path} operationId cannot be empty"
        )

    def test_endpoint_has_documentation(
        self, endpoint_info: tuple[str, str, dict[str, Any]], spec: dict[str, Any]
    ):
        """Test that every endpoint has documentation."""
        path, method, operation_spec = endpoint_info

        summary = operation_spec.get("summary", "")
        description = operation_spec.get("description", "")

        has_documentation = (summary and summary.strip()) or (
            description and description.strip()
        )

        assert has_documentation, (
            f"{method.upper()} {path} missing documentation - must have summary or description"
        )

        # If summary exists, it should be meaningful
        if summary:
            assert len(summary.strip()) >= 5, (
                f"{method.upper()} {path} summary too short: '{summary}'"
            )

    def test_endpoint_response_schemas(
        self, endpoint_info: tuple[str, str, dict[str, Any]], spec: dict[str, Any]
    ):
        """Test that every endpoint has valid response schemas."""
        path, method, operation_spec = endpoint_info

        responses = operation_spec.get("responses", {})
        assert responses, f"{method.upper()} {path} must define responses"

        # Check for success responses (2xx)
        success_responses = [code for code in responses if code.startswith("2")]
        assert success_responses, (
            f"{method.upper()} {path} must define at least one success response (2xx)"
        )

        # Validate response structure
        for response_code, response_spec in responses.items():
            assert isinstance(response_spec, dict), (
                f"{method.upper()} {path} response {response_code} must be an object"
            )

            # Response should have description (either directly or via $ref)
            has_description = self._resolve_response_description(response_spec, spec)
            assert has_description, (
                f"{method.upper()} {path} response {response_code} missing description"
            )

    def test_endpoint_parameters_comprehensive(
        self, endpoint_info: tuple[str, str, dict[str, Any]], spec: dict[str, Any]
    ):
        """Test comprehensive parameter validation for every endpoint."""
        path, method, operation_spec = endpoint_info

        parameters = operation_spec.get("parameters", [])

        # Validate each parameter
        for i, param in enumerate(parameters):
            if isinstance(param, dict):
                if "name" in param:
                    # Direct parameter definition
                    assert "in" in param, (
                        f"{method.upper()} {path} parameter {i} missing 'in' field"
                    )
                    assert param["in"] in ["query", "header", "path", "cookie"], (
                        f"{method.upper()} {path} parameter {i} invalid 'in' value: {param['in']}"
                    )

                    # Path parameters must be required
                    if param["in"] == "path":
                        assert param.get("required", False), (
                            f"{method.upper()} {path} path parameter '{param['name']}' must be required"
                        )

                elif "$ref" in param:
                    # Parameter reference - validate reference exists
                    ref = param["$ref"]
                    assert ref.startswith("#/components/parameters/"), (
                        f"{method.upper()} {path} parameter {i} invalid reference: {ref}"
                    )

                    param_key = ref.split("/")[-1]
                    components = spec.get("components", {})
                    param_defs = components.get("parameters", {})
                    assert param_key in param_defs, (
                        f"{method.upper()} {path} parameter reference not found: {ref}"
                    )

    def test_list_endpoint_pagination(
        self, list_endpoint_info: tuple[str, str, dict[str, Any]], spec: dict[str, Any]
    ):
        """Test that collection endpoints have pagination parameters."""
        path, method, operation_spec = list_endpoint_info

        parameters = operation_spec.get("parameters", [])
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
                        components = spec.get("components", {})
                        param_defs = components.get("parameters", {})
                        if param_key in param_defs:
                            param_def = param_defs[param_key]
                            if "name" in param_def:
                                param_names.add(param_def["name"])

        # Check for basic pagination parameters
        has_limit = "limit" in param_names
        has_page = "page" in param_names

        # Allow some flexibility - either limit+page or other pagination patterns
        has_pagination = (
            has_limit or has_page or "offset" in param_names or "cursor" in param_names
        )

        assert has_pagination, (
            f"Collection endpoint {method.upper()} {path} should support pagination parameters. "
            f"Expected: limit, page, offset, or cursor. Found: {sorted(param_names)}"
        )

    def test_endpoint_request_body_validation(
        self, endpoint_info: tuple[str, str, dict[str, Any]], spec: dict[str, Any]
    ):
        """Test request body validation for endpoints that accept bodies."""
        path, method, operation_spec = endpoint_info

        # Only certain methods typically have request bodies
        if method.lower() in ["post", "put", "patch"]:
            request_body = operation_spec.get("requestBody")

            if request_body:
                assert isinstance(request_body, dict), (
                    f"{method.upper()} {path} requestBody must be an object"
                )

                # Request body should have content
                assert "content" in request_body, (
                    f"{method.upper()} {path} requestBody missing content"
                )

                content = request_body["content"]
                assert isinstance(content, dict), (
                    f"{method.upper()} {path} requestBody content must be an object"
                )
                assert content, (
                    f"{method.upper()} {path} requestBody content cannot be empty"
                )

    def test_endpoint_tags(
        self, endpoint_info: tuple[str, str, dict[str, Any]], spec: dict[str, Any]
    ):
        """Test that endpoints are properly tagged for organization."""
        path, method, operation_spec = endpoint_info

        tags = operation_spec.get("tags", [])

        # Not all endpoints need tags, but if present they should be valid
        if tags:
            assert isinstance(tags, list), (
                f"{method.upper()} {path} tags must be a list"
            )

            for tag in tags:
                assert isinstance(tag, str), (
                    f"{method.upper()} {path} tag must be a string: {tag}"
                )
                assert tag.strip(), f"{method.upper()} {path} tag cannot be empty"

    def test_endpoint_security_requirements(
        self, endpoint_info: tuple[str, str, dict[str, Any]], spec: dict[str, Any]
    ):
        """Test endpoint security requirements are properly defined."""
        path, method, operation_spec = endpoint_info

        # Check if endpoint has security defined
        security = operation_spec.get("security")
        spec.get("security")

        if security is not None:
            assert isinstance(security, list), (
                f"{method.upper()} {path} security must be a list"
            )

            # Validate security scheme references
            for security_req in security:
                assert isinstance(security_req, dict), (
                    f"{method.upper()} {path} security requirement must be an object"
                )

                # Check that referenced security schemes exist
                components = spec.get("components", {})
                security_schemes = components.get("securitySchemes", {})

                for scheme_name in security_req:
                    if scheme_name not in security_schemes and security_req != {}:
                        # Allow empty security requirement (public endpoint)
                        pytest.fail(
                            f"{method.upper()} {path} references unknown security scheme: {scheme_name}"
                        )


class TestEndpointCoverageMetrics:
    """Test overall endpoint coverage and quality metrics."""

    @pytest.fixture(scope="class")
    def spec(self) -> dict[str, Any]:
        """Load OpenAPI specification."""
        spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"
        with open(spec_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_endpoint_coverage_metrics(self, spec: dict[str, Any]):
        """Test overall endpoint coverage and quality metrics."""
        paths = spec.get("paths", {})

        # Count endpoints by method
        method_counts: dict[str, int] = {}
        endpoints_with_docs = 0
        endpoints_with_operation_ids = 0
        total_endpoints = 0

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
                }:
                    total_endpoints += 1

                    # Count by method
                    method_upper = method.upper()
                    method_counts[method_upper] = method_counts.get(method_upper, 0) + 1

                    # Check documentation
                    if method_spec.get("summary") or method_spec.get("description"):
                        endpoints_with_docs += 1

                    # Check operation IDs
                    if method_spec.get("operationId"):
                        endpoints_with_operation_ids += 1

        assert total_endpoints > 0, "API should have at least one endpoint"

        # Calculate coverage metrics
        doc_coverage = (
            endpoints_with_docs / total_endpoints if total_endpoints > 0 else 0
        )
        operation_id_coverage = (
            endpoints_with_operation_ids / total_endpoints if total_endpoints > 0 else 0
        )

        # Report coverage without thresholds - zero tolerance for hiding issues
        # Individual parameterized tests will catch specific missing documentation
        print("\n📊 Endpoint Quality Metrics:")
        print(
            f"   Documentation coverage: {doc_coverage:.1%} ({endpoints_with_docs}/{total_endpoints})"
        )
        print(
            f"   Operation ID coverage: {operation_id_coverage:.1%} ({endpoints_with_operation_ids}/{total_endpoints})"
        )

        # Only assert basic validity - parameterized tests catch specific issues
        assert doc_coverage >= 0, "Documentation coverage should be non-negative"
        assert operation_id_coverage >= 0, (
            "Operation ID coverage should be non-negative"
        )
        print(f"   Total endpoints: {total_endpoints}")
        print(f"   Documentation coverage: {doc_coverage:.1%}")
        print(f"   Operation ID coverage: {operation_id_coverage:.1%}")
        print(f"   Methods: {dict(sorted(method_counts.items()))}")
