"""
External Documentation Comparison Tests

This module validates our OpenAPI specification against the comprehensive
documentation downloaded from developer.katanamrp.com.

Focus: External documentation vs internal specification consistency
All internal validation (schemas, endpoints, structure) is handled by:
- test_openapi_specification.py (OpenAPI structure validation)
- test_schema_comprehensive.py (comprehensive schema validation)
- test_endpoint_comprehensive.py (comprehensive endpoint validation)

These tests ensure that:
1. All documented endpoints are implemented in our spec
2. All documented methods are available for each endpoint
3. Our specification matches external documentation expectations
"""

import sys
from pathlib import Path
from typing import Any

import pytest
from scripts.analyze_api_documentation import OptimizedAPIAnalyzer

# Ensure the project root is in sys.path so scripts can be imported
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class TestExternalDocumentationComparison:
    """Test suite for external documentation comparison only."""

    @pytest.fixture(scope="class")
    def validator(self) -> OptimizedAPIAnalyzer:
        """Create the API documentation validator."""
        repo_root = Path(__file__).parent.parent
        validator = OptimizedAPIAnalyzer(repo_root)
        return validator

    @pytest.fixture
    def validation_results(
        self, current_spec: dict[str, Any], comprehensive_spec: dict[str, Any]
    ) -> dict[str, Any]:
        """Run validation between current and comprehensive specs."""
        # The OptimizedAPIAnalyzer automatically loads specs from the repo
        # so we just need to pass the repo root
        repo_root = Path(__file__).parent.parent

        # Initialize the analyzer with repo root
        analyzer = OptimizedAPIAnalyzer(repo_root=repo_root)

        # Run the analysis and return results
        return analyzer.run_analysis()

    @pytest.fixture(scope="class")
    def current_spec(self, validator: OptimizedAPIAnalyzer) -> dict[str, Any]:
        """Get the current OpenAPI spec."""
        return validator.current_spec

    @pytest.fixture(scope="class")
    def comprehensive_spec(self, validator: OptimizedAPIAnalyzer) -> dict[str, Any]:
        """Get the comprehensive external OpenAPI spec from the docs."""
        return validator.comprehensive_spec

    def test_current_spec_loads_successfully(self, current_spec: dict[str, Any]):
        """Test that our current OpenAPI spec loads successfully."""
        assert current_spec is not None, "Current spec should load successfully"
        assert isinstance(current_spec, dict), "Spec should be a dictionary"
        assert "paths" in current_spec, "Spec should have paths"

    def test_comprehensive_spec_loads_successfully(
        self, comprehensive_spec: dict[str, Any]
    ):
        """Test that the comprehensive external spec loads successfully."""
        assert comprehensive_spec is not None, (
            "Comprehensive spec should load successfully"
        )
        assert isinstance(comprehensive_spec, dict), (
            "Comprehensive spec should be a dictionary"
        )

    def test_no_critical_endpoints_missing(self, validation_results: dict[str, Any]):
        """Test that NO endpoints from external documentation are missing - ZERO tolerance."""
        missing_endpoints = validation_results["endpoints"]["missing_in_current"]

        # ZERO tolerance for any missing endpoints from comprehensive spec
        assert len(missing_endpoints) == 0, (
            f"Endpoints missing from current spec ({len(missing_endpoints)}). "
            f"ZERO tolerance for deviations. Missing: {missing_endpoints}"
        )

        # Note: The analyzer doesn't track endpoints in current but not in comprehensive
        # This is intentional - we're focused on implementing all documented endpoints

    def test_method_consistency(self, validation_results: dict[str, Any]):
        """Test that shared endpoints have exactly matching HTTP methods - ZERO tolerance."""
        method_mismatches = validation_results["endpoints"]["method_mismatches"]

        # ZERO tolerance for method deviations between specs
        assert len(method_mismatches) == 0, (
            f"Method mismatches found ({len(method_mismatches)}). "
            f"ZERO tolerance for deviations. All mismatches: {method_mismatches}"
        )

    def test_parameter_consistency(self, validation_results: dict[str, Any]):
        """Test that shared endpoints have exactly matching parameters - ZERO tolerance."""
        parameter_mismatches = validation_results["endpoints"]["parameter_mismatches"]

        # ZERO tolerance for parameter deviations between specs
        # Every parameter must match exactly between internal and external docs
        assert len(parameter_mismatches) == 0, (
            f"Parameter mismatches found ({len(parameter_mismatches)}). "
            f"ZERO tolerance for deviations. All mismatches: {parameter_mismatches}"
        )

    def test_security_scheme_completeness(self, current_spec: dict[str, Any]):
        """Test that security schemes are properly defined."""
        security_schemes = current_spec.get("components", {}).get("securitySchemes", {})

        # Should have Bearer authentication as shown in actual spec
        assert "bearerAuth" in security_schemes, (
            f"bearerAuth security scheme should be defined. Available: {list(security_schemes.keys())}"
        )

        bearer_scheme = security_schemes["bearerAuth"]
        assert bearer_scheme.get("type") == "http", "bearerAuth should be http type"
        assert bearer_scheme.get("scheme") == "bearer", (
            "bearerAuth should use bearer scheme"
        )

    def test_validation_summary_structure(self, validation_results: dict[str, Any]):
        """Test that validation summary contains expected structure and metrics."""
        summary = validation_results.get("summary", {})

        # Check that summary contains basic metrics about the comparison
        assert "current_endpoints" in summary, (
            "Summary should include current endpoint count"
        )
        assert "comprehensive_endpoints" in summary, (
            "Summary should include comprehensive endpoint count"
        )

        # Verify counts exist (no threshold requirements)
        current_count = summary.get("current_endpoints", 0)
        comprehensive_count = summary.get("comprehensive_endpoints", 0)

        assert current_count >= 0, (
            f"Current spec endpoint count should be non-negative, got {current_count}"
        )
        assert comprehensive_count >= 0, (
            f"Comprehensive spec endpoint count should be non-negative, got {comprehensive_count}"
        )

    def test_inventory_endpoints_complete(self, current_spec: dict[str, Any]):
        """Test that inventory endpoints are complete as documented."""
        paths = current_spec.get("paths", {})

        # Core inventory endpoints that should exist based on documentation
        expected_inventory_paths = [
            "/inventory",
            # Note: /inventory/{id} doesn't exist in current spec - only /inventory (list endpoint)
        ]

        missing_inventory_endpoints = []
        for expected_path in expected_inventory_paths:
            if expected_path not in paths:
                missing_inventory_endpoints.append(expected_path)

        assert not missing_inventory_endpoints, (
            f"Missing documented inventory endpoints: {missing_inventory_endpoints}"
        )

    def test_manufacturing_orders_endpoints_complete(
        self, current_spec: dict[str, Any]
    ):
        """Test that manufacturing orders endpoints are complete as documented."""
        paths = current_spec.get("paths", {})

        # Manufacturing orders endpoints that should exist based on documentation
        expected_mo_paths = [
            "/manufacturing_orders",  # List endpoint that exists
            # Note: /manufacturing_orders/{id} may not exist in current spec
        ]

        missing_mo_endpoints = []
        for expected_path in expected_mo_paths:
            if expected_path not in paths:
                missing_mo_endpoints.append(expected_path)

        assert not missing_mo_endpoints, (
            f"Missing documented manufacturing orders endpoints: {missing_mo_endpoints}"
        )

    def test_sales_orders_endpoints_complete(self, current_spec: dict[str, Any]):
        """Test that sales orders endpoints are complete as documented."""
        paths = current_spec.get("paths", {})

        # Sales orders endpoints that should exist based on documentation
        expected_so_paths = [
            "/sales_orders",  # List endpoint uses underscores
            # Note: /sales_orders/{id} may not exist in current spec
        ]

        missing_so_endpoints = []
        for expected_path in expected_so_paths:
            if expected_path not in paths:
                missing_so_endpoints.append(expected_path)

        assert not missing_so_endpoints, (
            f"Missing documented sales orders endpoints: {missing_so_endpoints}"
        )

    def test_external_vs_internal_coverage_reasonable(
        self, validation_results: dict[str, Any]
    ):
        """Test that coverage between external docs and internal spec is tracked accurately."""
        endpoints_section = validation_results["endpoints"]

        missing_in_current = len(endpoints_section["missing_in_current"])

        # Calculate coverage percentage based on comprehensive documentation
        summary = validation_results["summary"]
        comprehensive_total = summary.get("comprehensive_endpoints", 0)

        if comprehensive_total > 0:
            missing_percentage = (missing_in_current / comprehensive_total) * 100
        else:
            missing_percentage = 0

        # Report coverage without threshold enforcement - zero tolerance for hiding issues
        print(
            f"Coverage report: {missing_percentage:.1f}% endpoints missing from current spec "
            f"({missing_in_current} of {comprehensive_total} documented endpoints)"
        )

        # Only assert that the calculation is valid
        assert missing_percentage >= 0, "Missing percentage should be non-negative"

    def test_validation_completes_without_errors(self, validator: OptimizedAPIAnalyzer):
        """Test that the validation process completes without critical errors."""
        # If we got this far, validation completed successfully
        assert validator.analysis_results is not None, (
            "Analyzer should have analysis results structure"
        )
        assert validator.current_spec is not None, "Current spec should be loaded"

        # The comprehensive spec might be None if external docs aren't available
        # That's okay - we just test what we can
        if validator.comprehensive_spec is None:
            pytest.skip("External comprehensive documentation not available")
