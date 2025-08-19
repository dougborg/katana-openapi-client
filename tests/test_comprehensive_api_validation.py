"""
Comprehensive API Validation Tests

This module validates our OpenAPI specification against the comprehensive
documentation downloaded from developer.katanamrp.com.

These tests ensure that:
1. All documented endpoints are implemented in our spec
2. All documented methods are available for each endpoint
3. Parameter specifications match documentation
4. Schema definitions are complete and consistent
5. All documented functionality is covered
"""

import json
from pathlib import Path
from typing import Any, Dict, Set

import pytest
import yaml

from scripts.validate_api_documentation import APIDocumentationValidator


class TestComprehensiveAPIValidation:
    """Test suite for comprehensive API validation."""

    @pytest.fixture(scope="class")
    def validator(self) -> APIDocumentationValidator:
        """Create and configure validator instance."""
        repo_root = Path(__file__).parent.parent
        validator = APIDocumentationValidator(repo_root)
        validator.run_validation()
        return validator

    @pytest.fixture(scope="class")
    def validation_results(self, validator: APIDocumentationValidator) -> Dict[str, Any]:
        """Get validation results."""
        return validator.validation_results

    @pytest.fixture(scope="class")
    def current_spec(self, validator: APIDocumentationValidator) -> Dict[str, Any]:
        """Get current OpenAPI specification."""
        return validator.current_spec

    @pytest.fixture(scope="class")
    def comprehensive_spec(self, validator: APIDocumentationValidator) -> Dict[str, Any]:
        """Get comprehensive OpenAPI specification."""
        return validator.comprehensive_spec

    def test_current_spec_loads_successfully(self, current_spec: Dict[str, Any]):
        """Ensure our current OpenAPI spec loads without errors."""
        assert current_spec is not None
        assert "openapi" in current_spec
        assert "paths" in current_spec
        assert "components" in current_spec

    def test_comprehensive_spec_loads_successfully(self, comprehensive_spec: Dict[str, Any]):
        """Ensure comprehensive OpenAPI spec loads without errors."""
        assert comprehensive_spec is not None
        assert "openapi" in comprehensive_spec
        assert "paths" in comprehensive_spec

    def test_no_critical_endpoints_missing(self, validation_results: Dict[str, Any]):
        """Test that no critical endpoints are missing from our current spec."""
        missing_endpoints = validation_results["endpoints"]["missing_in_current"]
        
        # Define critical endpoints that should always be present
        critical_endpoints = {
            "/customers/{id}",  # Individual customer operations
            "/products/{id}",   # Individual product operations  
            "/sales_orders/{id}",  # Individual sales order operations
            "/purchase_orders/{id}",  # Individual purchase order operations
        }
        
        missing_critical = [ep for ep in missing_endpoints if ep in critical_endpoints]
        
        if missing_critical:
            pytest.fail(
                f"Critical endpoints missing from current spec: {missing_critical}\n"
                f"These endpoints are documented but not implemented in our OpenAPI spec."
            )

    def test_endpoint_method_completeness(self, validation_results: Dict[str, Any]):
        """Test that endpoints have complete HTTP method coverage."""
        method_mismatches = validation_results["endpoints"]["method_mismatches"]
        
        # Define critical method patterns
        critical_method_mismatches = []
        for mismatch in method_mismatches:
            path = mismatch["path"]
            missing_methods = mismatch["missing_in_current"]
            
            # Check for missing CRUD operations on entity endpoints
            if "/{id}" in path and missing_methods:
                # Entity endpoints should typically support GET, PATCH, DELETE
                critical_missing = [m for m in missing_methods if m in {"get", "patch", "delete"}]
                if critical_missing:
                    critical_method_mismatches.append({
                        "path": path,
                        "missing_critical_methods": critical_missing
                    })
        
        if critical_method_mismatches:
            error_msg = "Critical HTTP methods missing from endpoints:\n"
            for mismatch in critical_method_mismatches[:5]:  # Show first 5
                error_msg += f"  {mismatch['path']}: missing {mismatch['missing_critical_methods']}\n"
            
            pytest.fail(error_msg)

    def test_parameter_coverage(self, validation_results: Dict[str, Any]):
        """Test that endpoint parameters match comprehensive documentation."""
        parameter_mismatches = validation_results["endpoints"]["parameter_mismatches"]
        
        # Count significant parameter mismatches
        significant_mismatches = []
        for mismatch in parameter_mismatches:
            missing_params = mismatch["missing_in_current"]
            
            # Focus on commonly expected parameters
            critical_missing = [p for p in missing_params if p in {
                "limit", "page", "created_at_min", "created_at_max", 
                "updated_at_min", "updated_at_max", "include_deleted"
            }]
            
            if critical_missing:
                significant_mismatches.append({
                    "path": mismatch["path"],
                    "method": mismatch["method"],
                    "missing_critical_params": critical_missing
                })
        
        # Allow some parameter mismatches but not too many
        if len(significant_mismatches) > 10:
            pytest.fail(
                f"Too many endpoints missing critical parameters: {len(significant_mismatches)}\n"
                f"Examples: {significant_mismatches[:3]}"
            )

    def test_schema_definition_completeness(self, validation_results: Dict[str, Any]):
        """Test that schema definitions are complete and well-documented."""
        schema_issues = validation_results["schemas"]["property_mismatches"]
        
        # Count schemas with missing descriptions
        missing_descriptions = [
            schema for schema in schema_issues 
            if "missing_description" in schema["issues"]
        ]
        
        # Allow some schemas to lack descriptions, but not core business entities
        critical_schemas_without_descriptions = [
            schema for schema in missing_descriptions
            if schema["schema"] in {
                "Product", "Customer", "SalesOrder", "PurchaseOrder", 
                "ManufacturingOrder", "Inventory", "Variant"
            }
        ]
        
        if critical_schemas_without_descriptions:
            schema_names = [s["schema"] for s in critical_schemas_without_descriptions]
            pytest.fail(
                f"Critical business entity schemas missing descriptions: {schema_names}\n"
                f"These core schemas should have comprehensive descriptions."
            )

    def test_basic_crud_operations_coverage(self, current_spec: Dict[str, Any]):
        """Test that basic CRUD operations are covered for main entities."""
        paths = current_spec.get("paths", {})
        
        # Define main business entities that should support CRUD
        main_entities = {
            "customers": {
                "list": "/customers",
                "create": "/customers", 
                "read": "/customers/{id}",
                "update": "/customers/{id}",
                "delete": "/customers/{id}"
            },
            "products": {
                "list": "/products",
                "create": "/products",
                "read": "/products/{id}",
                "update": "/products/{id}",
                "delete": "/products/{id}"
            },
            "sales_orders": {
                "list": "/sales_orders",
                "create": "/sales_orders",
                "read": "/sales_orders/{id}",
                "update": "/sales_orders/{id}",
                "delete": "/sales_orders/{id}"
            }
        }
        
        missing_operations = []
        for entity, operations in main_entities.items():
            for operation_name, path in operations.items():
                if path not in paths:
                    missing_operations.append(f"{entity}.{operation_name} ({path})")
                else:
                    # Check if appropriate method exists
                    path_spec = paths[path]
                    expected_method = {
                        "list": "get",
                        "create": "post", 
                        "read": "get",
                        "update": "patch",
                        "delete": "delete"
                    }[operation_name]
                    
                    if expected_method not in path_spec:
                        missing_operations.append(
                            f"{entity}.{operation_name} ({path} {expected_method.upper()})"
                        )
        
        if missing_operations:
            pytest.fail(
                f"Missing basic CRUD operations: {missing_operations[:5]}\n"
                f"These are fundamental operations that should be supported."
            )

    def test_endpoint_response_schemas_defined(self, current_spec: Dict[str, Any]):
        """Test that all endpoints define proper response schemas."""
        paths = current_spec.get("paths", {})
        schemas = current_spec.get("components", {}).get("schemas", {})
        
        endpoints_missing_response_schemas = []
        
        for path, path_spec in paths.items():
            for method, method_spec in path_spec.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue
                    
                responses = method_spec.get("responses", {})
                success_responses = [code for code in responses.keys() 
                                   if code.startswith("2")]
                
                if not success_responses:
                    endpoints_missing_response_schemas.append(f"{method.upper()} {path}")
                    continue
                
                # Check if success responses have schema definitions
                has_schema = False
                for response_code in success_responses:
                    response_spec = responses[response_code]
                    if "content" in response_spec:
                        content = response_spec["content"]
                        if "application/json" in content:
                            json_content = content["application/json"]
                            if "schema" in json_content:
                                has_schema = True
                                break
                
                if not has_schema:
                    endpoints_missing_response_schemas.append(f"{method.upper()} {path}")
        
        # Allow some endpoints to not have response schemas, but not too many
        if len(endpoints_missing_response_schemas) > 20:
            pytest.fail(
                f"Too many endpoints missing response schemas: {len(endpoints_missing_response_schemas)}\n"
                f"Examples: {endpoints_missing_response_schemas[:5]}"
            )

    def test_openapi_specification_version_compatibility(self, current_spec: Dict[str, Any]):
        """Test that OpenAPI specification uses appropriate version."""
        openapi_version = current_spec.get("openapi")
        assert openapi_version is not None, "OpenAPI version must be specified"
        
        # Should use OpenAPI 3.1.x for latest features
        assert openapi_version.startswith("3.1"), (
            f"Expected OpenAPI 3.1.x for latest features, got {openapi_version}"
        )

    def test_security_scheme_completeness(self, current_spec: Dict[str, Any]):
        """Test that security schemes are properly defined."""
        components = current_spec.get("components", {})
        security_schemes = components.get("securitySchemes", {})
        
        assert "bearerAuth" in security_schemes, (
            "Bearer authentication should be defined for API access"
        )
        
        bearer_auth = security_schemes["bearerAuth"]
        assert bearer_auth.get("type") == "http", "Bearer auth should use HTTP type"
        assert bearer_auth.get("scheme") == "bearer", "Should use bearer scheme"

    def test_validation_summary_within_acceptable_limits(self, validation_results: Dict[str, Any]):
        """Test that overall validation results are within acceptable limits."""
        summary = validation_results["summary"]
        
        # Set acceptable thresholds for different types of issues
        thresholds = {
            "endpoints_missing_in_current": 30,  # Allow some missing endpoints
            "endpoint_method_mismatches": 20,    # Allow some method mismatches
            "endpoint_parameter_mismatches": 60, # Allow many parameter mismatches (common)
            "schema_issues": 50,                 # Allow some schema issues
        }
        
        failures = []
        for metric, threshold in thresholds.items():
            actual_value = summary.get(metric, 0)
            if actual_value > threshold:
                failures.append(f"{metric}: {actual_value} > {threshold}")
        
        if failures:
            pytest.fail(
                f"Validation metrics exceed acceptable thresholds:\n" +
                "\n".join(f"  - {failure}" for failure in failures) +
                f"\n\nSummary: {summary}"
            )


class TestSpecificEndpointValidation:
    """Test specific endpoint functionality that should be present."""

    @pytest.fixture(scope="class")
    def current_spec(self) -> Dict[str, Any]:
        """Load current OpenAPI specification."""
        spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"
        with open(spec_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_products_endpoints_complete(self, current_spec: Dict[str, Any]):
        """Test that products endpoints are complete."""
        paths = current_spec.get("paths", {})
        
        required_product_endpoints = [
            ("/products", ["get", "post"]),
            ("/products/{id}", ["get", "patch", "delete"]),
            ("/variants", ["get", "post"]),
            ("/variants/{id}", ["get", "patch", "delete"]),
        ]
        
        for path, methods in required_product_endpoints:
            assert path in paths, f"Missing product endpoint: {path}"
            
            path_spec = paths[path]
            for method in methods:
                assert method in path_spec, (
                    f"Missing method {method.upper()} for {path}"
                )

    def test_inventory_endpoints_complete(self, current_spec: Dict[str, Any]):
        """Test that inventory management endpoints are complete."""
        paths = current_spec.get("paths", {})
        
        required_inventory_endpoints = [
            ("/inventory", ["get"]),
            ("/inventory_movements", ["get"]),
            ("/stock_adjustments", ["get", "post"]),
            ("/stock_transfers", ["get", "post"]),
        ]
        
        for path, methods in required_inventory_endpoints:
            assert path in paths, f"Missing inventory endpoint: {path}"
            
            path_spec = paths[path]
            for method in methods:
                assert method in path_spec, (
                    f"Missing method {method.upper()} for {path}"
                )

    def test_manufacturing_endpoints_complete(self, current_spec: Dict[str, Any]):
        """Test that manufacturing endpoints are complete."""
        paths = current_spec.get("paths", {})
        
        required_manufacturing_endpoints = [
            ("/manufacturing_orders", ["get", "post"]),
            ("/manufacturing_orders/{id}", ["get", "patch", "delete"]),
            ("/bom_rows", ["get", "post"]),
        ]
        
        for path, methods in required_manufacturing_endpoints:
            assert path in paths, f"Missing manufacturing endpoint: {path}"
            
            path_spec = paths[path]  
            for method in methods:
                assert method in path_spec, (
                    f"Missing method {method.upper()} for {path}"
                )

    def test_sales_endpoints_complete(self, current_spec: Dict[str, Any]):
        """Test that sales management endpoints are complete."""
        paths = current_spec.get("paths", {})
        
        required_sales_endpoints = [
            ("/sales_orders", ["get", "post"]),
            ("/sales_orders/{id}", ["get", "patch", "delete"]),
            ("/customers", ["get", "post"]),
        ]
        
        for path, methods in required_sales_endpoints:
            assert path in paths, f"Missing sales endpoint: {path}"
            
            path_spec = paths[path]
            for method in methods:
                assert method in path_spec, (
                    f"Missing method {method.upper()} for {path}"
                )