"""
Critical API Gap Tests

This module contains focused tests for the most critical gaps identified
between our current OpenAPI specification and the comprehensive documentation.

These tests fail when critical issues are present, providing clear guidance
on what needs to be implemented to achieve documentation compliance.
"""

import json
from pathlib import Path
from typing import Any, Dict

import pytest
import yaml


class TestCriticalAPIGaps:
    """Test critical API gaps that should be addressed immediately."""

    @pytest.fixture(scope="class")
    def current_spec(self) -> Dict[str, Any]:
        """Load current OpenAPI specification."""
        spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"
        with open(spec_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    @pytest.fixture(scope="class")
    def gap_analysis(self) -> Dict[str, Any]:
        """Load gap analysis results."""
        analysis_path = Path(__file__).parent.parent / "documentation_gap_analysis.json"
        if analysis_path.exists():
            with open(analysis_path, encoding="utf-8") as f:
                return json.load(f)
        return {}

    def test_critical_customer_endpoints_present(self, current_spec: Dict[str, Any]):
        """Test that critical customer endpoints are present."""
        paths = current_spec.get("paths", {})
        
        # Customer endpoints are fundamental for any ERP system
        required_customer_endpoints = [
            "/customers",      # List and create customers
            "/customers/{id}"  # Individual customer operations
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

    def test_customer_crud_operations_complete(self, current_spec: Dict[str, Any]):
        """Test that customer CRUD operations are complete."""
        paths = current_spec.get("paths", {})
        
        # Customer collection endpoint
        if "/customers" in paths:
            customers_path = paths["/customers"]
            assert "get" in customers_path, "Must be able to list customers"
            assert "post" in customers_path, "Must be able to create customers"
        
        # Individual customer endpoint  
        if "/customers/{id}" in paths:
            customer_path = paths["/customers/{id}"]
            missing_methods = []
            
            if "get" not in customer_path:
                missing_methods.append("GET (retrieve customer)")
            if "patch" not in customer_path:
                missing_methods.append("PATCH (update customer)")
            if "delete" not in customer_path:
                missing_methods.append("DELETE (delete customer)")
            
            if missing_methods:
                pytest.fail(
                    f"Customer endpoint /customers/{{id}} missing methods: {missing_methods}\n"
                    f"Complete CRUD operations are required for customer management."
                )

    def test_sales_returns_crud_complete(self, current_spec: Dict[str, Any]):
        """Test that sales returns support complete CRUD operations."""
        paths = current_spec.get("paths", {})
        
        if "/sales_returns/{id}" in paths:
            sales_return_path = paths["/sales_returns/{id}"]
            missing_methods = []
            
            if "patch" not in sales_return_path:
                missing_methods.append("PATCH (update sales return)")
            if "delete" not in sales_return_path:
                missing_methods.append("DELETE (delete sales return)")
            
            if missing_methods:
                pytest.fail(
                    f"Sales return endpoint missing critical methods: {missing_methods}\n"
                    f"The comprehensive documentation shows these methods should be available.\n"
                    f"Sales return management requires update and delete capabilities."
                )

    def test_core_business_schemas_have_descriptions(self, current_spec: Dict[str, Any]):
        """Test that core business entity schemas have descriptions."""
        schemas = current_spec.get("components", {}).get("schemas", {})
        
        # Core business entities that should have descriptions
        core_entities = [
            "Customer", "Product", "SalesOrder", "PurchaseOrder", 
            "ManufacturingOrder", "Inventory", "Variant", "Material"
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

    def test_list_endpoints_have_pagination(self, current_spec: Dict[str, Any]):
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
                if (operation_id.startswith(("getAll", "list")) or 
                    "list" in summary or 
                    path.count("/") == 1 and not "{" in path):
                    list_endpoints.append(path)
        
        # Check for pagination parameters
        endpoints_missing_pagination = []
        for endpoint in list_endpoints[:10]:  # Check first 10 to avoid noise
            get_spec = paths[endpoint]["get"]
            parameters = get_spec.get("parameters", [])
            param_names = {p.get("name") for p in parameters if "name" in p}
            
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

    def test_gap_analysis_shows_acceptable_coverage(self, gap_analysis: Dict[str, Any]):
        """Test that gap analysis shows acceptable API coverage."""
        if not gap_analysis:
            pytest.skip("Gap analysis not available")
        
        validation_results = gap_analysis.get("validation_results", {})
        summary = validation_results.get("summary", {})
        
        # Check critical metrics
        critical_issues = []
        
        endpoints_missing = summary.get("endpoints_missing_in_current", 0)
        if endpoints_missing > 30:
            critical_issues.append(f"Too many missing endpoints: {endpoints_missing}")
        
        method_mismatches = summary.get("endpoint_method_mismatches", 0)
        if method_mismatches > 20:
            critical_issues.append(f"Too many method mismatches: {method_mismatches}")
        
        # Get specific critical gaps
        gap_analysis_data = gap_analysis.get("gap_analysis", {})
        missing_endpoints = gap_analysis_data.get("missing_endpoints", {})
        critical_missing = missing_endpoints.get("critical", [])
        
        if len(critical_missing) > 5:
            critical_issues.append(f"Too many critical endpoints missing: {len(critical_missing)}")
        
        method_gaps = gap_analysis_data.get("method_gaps", {})
        crud_issues = method_gaps.get("crud_completeness_issues", [])
        
        if len(crud_issues) > 3:
            critical_issues.append(f"Too many CRUD completeness issues: {len(crud_issues)}")
        
        if critical_issues:
            pytest.fail(
                f"API coverage has critical issues:\n" +
                "\n".join(f"  - {issue}" for issue in critical_issues) +
                f"\n\nDetailed analysis available in documentation_gap_analysis.json"
            )

    def test_documentation_validation_files_exist(self):
        """Test that validation and analysis files are properly generated."""
        repo_root = Path(__file__).parent.parent
        
        validation_file = repo_root / "validation_results.json"
        analysis_file = repo_root / "documentation_gap_analysis.json"
        
        assert validation_file.exists(), (
            "validation_results.json should be generated by validation script"
        )
        
        assert analysis_file.exists(), (
            "documentation_gap_analysis.json should be generated by gap analysis script"
        )
        
        # Verify files contain valid JSON
        with open(validation_file, encoding="utf-8") as f:
            validation_data = json.load(f)
        
        with open(analysis_file, encoding="utf-8") as f:
            analysis_data = json.load(f)
        
        assert "endpoints" in validation_data, "Validation results should contain endpoint analysis"
        assert "schemas" in validation_data, "Validation results should contain schema analysis"
        assert "summary" in validation_data, "Validation results should contain summary"
        
        assert "gap_analysis" in analysis_data, "Analysis should contain gap analysis"
        assert "recommendations" in analysis_data, "Analysis should contain recommendations"


class TestDocumentationCompliance:
    """Test compliance with documentation standards."""

    @pytest.fixture(scope="class")
    def current_spec(self) -> Dict[str, Any]:
        """Load current OpenAPI specification."""
        spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"
        with open(spec_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_openapi_info_section_complete(self, current_spec: Dict[str, Any]):
        """Test that OpenAPI info section is complete and descriptive."""
        info = current_spec.get("info", {})
        
        required_fields = ["title", "version", "description"]
        missing_fields = [field for field in required_fields if field not in info]
        
        assert not missing_fields, f"OpenAPI info section missing required fields: {missing_fields}"
        
        # Check description quality
        description = info.get("description", "")
        assert len(description) > 100, (
            "OpenAPI description should be comprehensive (>100 characters) to help developers understand the API"
        )

    def test_all_endpoints_have_operation_ids(self, current_spec: Dict[str, Any]):
        """Test that all endpoints have operation IDs for client generation."""
        paths = current_spec.get("paths", {})
        
        missing_operation_ids = []
        for path, path_spec in paths.items():
            for method, method_spec in path_spec.items():
                if method.lower() in {"get", "post", "put", "patch", "delete"}:
                    if "operationId" not in method_spec:
                        missing_operation_ids.append(f"{method.upper()} {path}")
        
        assert not missing_operation_ids, (
            f"Endpoints missing operationId: {missing_operation_ids[:5]}\n"
            f"All endpoints should have operationId for proper client generation"
        )

    def test_endpoints_have_descriptions(self, current_spec: Dict[str, Any]):
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
        
        # Allow some endpoints to lack descriptions, but not too many
        assert len(missing_descriptions) < 10, (
            f"Too many endpoints missing descriptions: {len(missing_descriptions)}\n"
            f"Examples: {missing_descriptions[:5]}\n"
            f"Endpoints should have descriptions or summaries for API documentation"
        )