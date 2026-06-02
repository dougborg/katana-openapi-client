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
    def spec(self, openapi_spec: dict[str, Any]) -> dict[str, Any]:
        """Re-export the session-scoped OpenAPI spec under this class's name.

        Delegates to ``conftest.openapi_spec`` so the YAML is parsed once
        per run, not once per class.
        """
        return openapi_spec

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

    def test_create_endpoint_success_status_codes(self, spec: dict[str, Any]):
        """Pin live-verified POST create endpoints to status 200.

        Katana's actual API returns ``200`` from create endpoints, not ``201``.
        The spec previously misdeclared five endpoints as ``201``, which caused
        the generated parser to return ``parsed=None`` for what was actually a
        successful response — leading to ``UnexpectedResponse`` errors in
        ``unwrap_as`` even though the mutation had landed server-side.

        All five have been verified live via ``make_test_client()``:

        - ``POST /sales_order_fulfillments`` → 200
        - ``POST /stock_transfers`` → 200
        - ``POST /sales_return_rows`` → 200
        - ``POST /inventory_reorder_points`` → 200
        - ``POST /outsourced_purchase_order_recipe_rows`` → 200
        """
        paths = spec.get("paths", {})
        live_verified_endpoints = [
            "/sales_order_fulfillments",
            "/stock_transfers",
            "/sales_return_rows",
            "/inventory_reorder_points",
            "/outsourced_purchase_order_recipe_rows",
        ]
        for endpoint in live_verified_endpoints:
            post_spec = paths.get(endpoint, {}).get("post", {})
            responses = post_spec.get("responses", {})
            assert "200" in responses, (
                f"POST {endpoint} must declare 200 as success "
                f"(live-verified — Katana returns 200, not 201). "
                f"Declared response codes: {sorted(responses.keys())}"
            )
            assert "201" not in responses, (
                f"POST {endpoint} must NOT declare 201 — Katana returns 200. "
                f"Mis-declaring this breaks the generated parser. "
                f"Declared response codes: {sorted(responses.keys())}"
            )


class TestCustomFieldsSurfaceAlignment:
    """Pin the custom-fields surface to Katana's live API (issue #805).

    These invariants were verified against the live official Katana catalog
    (``/custom_field_definitions``, ``/sales_orders/search``,
    ``/sales_order_rows/search``) on 2026-06-02. The live API supersedes the
    pre-GA partner PDF on three points captured here: only 6 field types (no
    ``multiSelect``), entity_type limited to ``SalesOrder`` / ``SalesOrderRow``,
    and a narrower search operator set.
    """

    @pytest.fixture(scope="class")
    def schemas(self, openapi_spec: dict[str, Any]) -> dict[str, Any]:
        return openapi_spec["components"]["schemas"]

    def test_entity_type_narrowed_to_live_values(self, schemas: dict[str, Any]):
        """Only sales orders and rows carry partner custom fields today."""
        assert schemas["CustomFieldEntityType"]["enum"] == [
            "SalesOrder",
            "SalesOrderRow",
        ], "entity_type must match the live allowlist; add a value only once live."

    def test_field_type_has_no_multiselect(self, schemas: dict[str, Any]):
        """The live API enumerates 6 types; multiSelect is not yet live."""
        enum = schemas["CustomFieldType"]["enum"]
        assert "multiSelect" not in enum, (
            "multiSelect is announced but the live API rejects it — do not add "
            "it to the enum until the live catalog accepts it."
        )
        assert set(enum) == {
            "shortText",
            "number",
            "singleSelect",
            "date",
            "boolean",
            "url",
        }

    def test_options_choice_shapes_split_create_vs_read(self, schemas: dict[str, Any]):
        """Create choices carry only ``label``; read/update add ``id`` + ``deleted``."""
        create_props = schemas["CustomFieldChoiceCreate"]["properties"]
        assert set(create_props) == {"label"}

        rw_props = schemas["CustomFieldChoice"]["properties"]
        assert {"id", "label", "deleted"} == set(rw_props)
        assert schemas["CustomFieldChoice"]["required"] == ["label"]

    def test_options_schemas_wire_to_correct_choice_type(self, schemas: dict[str, Any]):
        """Guard against swapping the create-side and read/update-side $refs.

        A swap (e.g. CustomFieldOptions pointing at CustomFieldChoiceCreate)
        would let a create payload omit ``id``/``deleted`` on update, or demand
        them on create — and every shape-only test above would still pass.
        """
        assert schemas["CustomFieldOptions"]["properties"]["choices"]["items"][
            "$ref"
        ].endswith("/CustomFieldChoice")
        assert schemas["CustomFieldOptionsCreate"]["properties"]["choices"]["items"][
            "$ref"
        ].endswith("/CustomFieldChoiceCreate")

        def _options_ref(schema_name: str) -> str:
            # options is `anyOf: [{$ref}, {type: null}]` — find the $ref branch.
            options = schemas[schema_name]["properties"]["options"]
            return next(b["$ref"] for b in options["anyOf"] if "$ref" in b)

        assert _options_ref("CreateCustomFieldDefinitionRequest").endswith(
            "/CustomFieldOptionsCreate"
        )
        assert _options_ref("UpdateCustomFieldDefinitionRequest").endswith(
            "/CustomFieldOptions"
        )
        assert _options_ref("CustomFieldDefinition").endswith("/CustomFieldOptions")

    def test_search_comparator_uses_live_operator_set(self, schemas: dict[str, Any]):
        """No nlike/nilike/regexp/eq/exists — match the live structured schema."""
        ops = set(schemas["SearchComparator"]["properties"])
        assert ops == {
            "neq",
            "gt",
            "gte",
            "lt",
            "lte",
            "inq",
            "nin",
            "between",
            "like",
            "ilike",
        }
        assert schemas["SearchComparator"]["additionalProperties"] is False

    def test_search_filter_request_retired(self, schemas: dict[str, Any]):
        """The generic envelope is replaced by per-endpoint request schemas."""
        assert "SearchFilterRequest" not in schemas
        for name in (
            "SalesOrderSearchRequest",
            "SalesOrderRowSearchRequest",
        ):
            assert name in schemas

    def test_search_endpoints_reference_typed_requests(
        self, openapi_spec: dict[str, Any]
    ):
        """Both search endpoints point at their per-endpoint request schema."""
        paths = openapi_spec["paths"]
        so = paths["/sales_orders/search"]["post"]["requestBody"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        row = paths["/sales_order_rows/search"]["post"]["requestBody"]["content"][
            "application/json"
        ]["schema"]["$ref"]
        assert so.endswith("/SalesOrderSearchRequest")
        assert row.endswith("/SalesOrderRowSearchRequest")

    def test_search_where_uses_snake_case_custom_fields_path(
        self, schemas: dict[str, Any]
    ):
        """Pin the live-verified snake_case ``custom_fields.<uuid>`` search path.

        Verified live (2026-06-02): the API accepts ``custom_fields.<uuid>`` in
        ``where`` and rejects camelCase ``customFields.<uuid>`` as an unknown
        field. The where schemas allow the dynamic UUID keys via
        ``additionalProperties: true`` and must NOT declare a ``customFields``
        property (which would reintroduce the pre-GA camelCase footgun).
        """
        for name in ("SalesOrderSearchWhere", "SalesOrderRowSearchWhere"):
            where = schemas[name]
            assert where["additionalProperties"] is True, (
                f"{name} must allow custom_fields.<uuid> dynamic keys"
            )
            assert "customFields" not in where.get("properties", {}), (
                f"{name} must not declare a camelCase customFields property"
            )
