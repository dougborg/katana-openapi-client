#!/usr/bin/env python3
"""
API Documentation Gap Analysis

This script provides detailed analysis and actionable recommendations
for bringing our OpenAPI specification into alignment with the comprehensive
documentation from developer.katanamrp.com.

It generates specific recommendations for:
1. Missing endpoints to implement
2. Missing HTTP methods to add
3. Missing parameters to include
4. Schema improvements needed
5. Documentation enhancements required
"""

import json
from pathlib import Path
from typing import Any

from validate_api_documentation import APIDocumentationValidator


class DocumentationGapAnalyzer:
    """Analyzes gaps between current spec and comprehensive documentation."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.validator = APIDocumentationValidator(repo_root)
        self.validation_results = self.validator.run_validation()

    def analyze_missing_endpoints(self) -> dict[str, Any]:
        """Analyze missing endpoints and categorize by priority."""
        missing_endpoints = self.validation_results["endpoints"]["missing_in_current"]

        # Categorize endpoints by type and priority
        categorized = {"critical": [], "important": [], "nice_to_have": []}

        # Critical endpoints (CRUD operations on main entities)
        critical_patterns = [
            r"/customers/{id}",
            r"/products/{id}",
            r"/sales_orders/{id}",
            r"/purchase_orders/{id}",
            r"/manufacturing_orders/{id}",
        ]

        # Important endpoints (common operations)
        important_patterns = [
            r"/stock_adjustments/{id}",
            r"/stock_transfers/{id}",
            r"/sales_order_rows/{id}",
            r"/purchase_order_rows/{id}",
            r"/price_lists/{id}",
            r"/services/{id}",
        ]

        for endpoint in missing_endpoints:
            if any(
                pattern.replace("{id}", "").rstrip("/") in endpoint
                for pattern in critical_patterns
            ):
                categorized["critical"].append(endpoint)
            elif any(
                pattern.replace("{id}", "").rstrip("/") in endpoint
                for pattern in important_patterns
            ):
                categorized["important"].append(endpoint)
            else:
                categorized["nice_to_have"].append(endpoint)

        return categorized

    def analyze_method_gaps(self) -> dict[str, Any]:
        """Analyze missing HTTP methods and their impact."""
        method_mismatches = self.validation_results["endpoints"]["method_mismatches"]

        analysis = {
            "crud_completeness_issues": [],
            "standard_operations_missing": [],
            "minor_gaps": [],
        }

        for mismatch in method_mismatches:
            path = mismatch["path"]
            missing_methods = mismatch["missing_in_current"]

            # CRUD completeness issues (entity endpoints missing key methods)
            if "/{id}" in path:
                crud_missing = [
                    m for m in missing_methods if m in {"get", "patch", "delete"}
                ]
                if crud_missing:
                    analysis["crud_completeness_issues"].append(
                        {
                            "path": path,
                            "missing_crud_methods": crud_missing,
                            "impact": "High - Core entity operations unavailable",
                        }
                    )

            # Collection endpoints missing POST
            elif path.endswith("s") and "post" in missing_methods:
                analysis["standard_operations_missing"].append(
                    {
                        "path": path,
                        "missing_methods": ["post"],
                        "impact": "Medium - Cannot create new resources",
                    }
                )

            # Other method gaps
            else:
                analysis["minor_gaps"].append(
                    {
                        "path": path,
                        "missing_methods": missing_methods,
                        "impact": "Low - Limited functionality",
                    }
                )

        return analysis

    def analyze_parameter_gaps(self) -> dict[str, Any]:
        """Analyze missing parameters and their importance."""
        parameter_mismatches = self.validation_results["endpoints"][
            "parameter_mismatches"
        ]

        # Group by parameter type
        parameter_analysis = {
            "pagination_missing": [],
            "filtering_missing": [],
            "other_missing": [],
        }

        for mismatch in parameter_mismatches:
            path = mismatch["path"]
            method = mismatch["method"]
            missing_params = mismatch["missing_in_current"]

            # Pagination parameters
            pagination_params = [p for p in missing_params if p in {"limit", "page"}]
            if pagination_params:
                parameter_analysis["pagination_missing"].append(
                    {
                        "endpoint": f"{method.upper()} {path}",
                        "missing_params": pagination_params,
                    }
                )

            # Filtering parameters
            filtering_params = [
                p
                for p in missing_params
                if p
                in {
                    "created_at_min",
                    "created_at_max",
                    "updated_at_min",
                    "updated_at_max",
                    "include_deleted",
                }
            ]
            if filtering_params:
                parameter_analysis["filtering_missing"].append(
                    {
                        "endpoint": f"{method.upper()} {path}",
                        "missing_params": filtering_params,
                    }
                )

            # Other parameters
            other_params = [
                p
                for p in missing_params
                if p
                not in {
                    "limit",
                    "page",
                    "created_at_min",
                    "created_at_max",
                    "updated_at_min",
                    "updated_at_max",
                    "include_deleted",
                }
            ]
            if other_params:
                parameter_analysis["other_missing"].append(
                    {
                        "endpoint": f"{method.upper()} {path}",
                        "missing_params": other_params[:5],  # Limit to avoid noise
                    }
                )

        return parameter_analysis

    def analyze_schema_gaps(self) -> dict[str, Any]:
        """Analyze schema definition gaps and issues."""
        schema_issues = self.validation_results["schemas"]["property_mismatches"]

        analysis = {
            "critical_schemas_without_descriptions": [],
            "properties_missing_descriptions": [],
            "potential_missing_schemas": [],
        }

        # Identify critical business entities
        critical_entities = {
            "Product",
            "Customer",
            "SalesOrder",
            "PurchaseOrder",
            "ManufacturingOrder",
            "Inventory",
            "Variant",
            "Material",
        }

        for schema_issue in schema_issues:
            schema_name = schema_issue["schema"]
            issues = schema_issue["issues"]

            if "missing_description" in issues and schema_name in critical_entities:
                analysis["critical_schemas_without_descriptions"].append(schema_name)

            property_issues = [
                issue
                for issue in issues
                if "property_" in issue and "missing_description" in issue
            ]
            if property_issues:
                analysis["properties_missing_descriptions"].append(
                    {
                        "schema": schema_name,
                        "properties_without_descriptions": [
                            issue.replace("property_", "").replace(
                                "_missing_description", ""
                            )
                            for issue in property_issues[:5]  # Limit to avoid noise
                        ],
                    }
                )

        return analysis

    def generate_implementation_recommendations(self) -> dict[str, Any]:
        """Generate specific implementation recommendations."""
        endpoint_analysis = self.analyze_missing_endpoints()
        method_analysis = self.analyze_method_gaps()
        parameter_analysis = self.analyze_parameter_gaps()
        schema_analysis = self.analyze_schema_gaps()

        recommendations = {
            "immediate_actions": [],
            "short_term_improvements": [],
            "long_term_enhancements": [],
            "implementation_priority": [],
        }

        # Immediate actions (critical gaps)
        if endpoint_analysis["critical"]:
            recommendations["immediate_actions"].append(
                {
                    "action": "Implement missing critical endpoints",
                    "details": endpoint_analysis["critical"][:5],
                    "effort": "High",
                    "impact": "High",
                }
            )

        if method_analysis["crud_completeness_issues"]:
            recommendations["immediate_actions"].append(
                {
                    "action": "Add missing CRUD methods to entity endpoints",
                    "details": [
                        issue["path"]
                        for issue in method_analysis["crud_completeness_issues"][:3]
                    ],
                    "effort": "Medium",
                    "impact": "High",
                }
            )

        if schema_analysis["critical_schemas_without_descriptions"]:
            recommendations["immediate_actions"].append(
                {
                    "action": "Add descriptions to critical business entity schemas",
                    "details": schema_analysis["critical_schemas_without_descriptions"],
                    "effort": "Low",
                    "impact": "Medium",
                }
            )

        # Short-term improvements
        if endpoint_analysis["important"]:
            recommendations["short_term_improvements"].append(
                {
                    "action": "Implement important missing endpoints",
                    "details": endpoint_analysis["important"][:5],
                    "effort": "Medium",
                    "impact": "Medium",
                }
            )

        if len(parameter_analysis["pagination_missing"]) > 10:
            recommendations["short_term_improvements"].append(
                {
                    "action": "Add pagination parameters to list endpoints",
                    "details": f"{len(parameter_analysis['pagination_missing'])} endpoints missing pagination",
                    "effort": "Low",
                    "impact": "Medium",
                }
            )

        if len(parameter_analysis["filtering_missing"]) > 15:
            recommendations["short_term_improvements"].append(
                {
                    "action": "Add common filtering parameters (date ranges, include_deleted)",
                    "details": f"{len(parameter_analysis['filtering_missing'])} endpoints missing filters",
                    "effort": "Low",
                    "impact": "Medium",
                }
            )

        # Long-term enhancements
        if endpoint_analysis["nice_to_have"]:
            recommendations["long_term_enhancements"].append(
                {
                    "action": "Implement additional endpoints for completeness",
                    "details": f"{len(endpoint_analysis['nice_to_have'])} additional endpoints",
                    "effort": "Medium",
                    "impact": "Low",
                }
            )

        # Priority implementation order
        recommendations["implementation_priority"] = [
            "1. Critical entity CRUD endpoints (/customers/{id}, etc.)",
            "2. Missing CRUD methods (PATCH, DELETE for entities)",
            "3. Schema descriptions for business entities",
            "4. Pagination parameters for list endpoints",
            "5. Common filtering parameters",
            "6. Important operational endpoints",
            "7. Additional endpoints for feature completeness",
        ]

        return recommendations

    def generate_technical_specifications(self) -> dict[str, Any]:
        """Generate technical specifications for implementing missing features."""
        missing_endpoints = self.analyze_missing_endpoints()
        method_analysis = self.analyze_method_gaps()

        specifications = {
            "missing_endpoint_specs": [],
            "missing_method_specs": [],
            "parameter_additions": [],
        }

        # Specifications for critical missing endpoints
        for endpoint in missing_endpoints["critical"][:3]:
            if "/customers/{id}" in endpoint:
                specifications["missing_endpoint_specs"].append(
                    {
                        "path": "/customers/{id}",
                        "methods": {
                            "get": {
                                "summary": "Retrieve a specific customer",
                                "parameters": [
                                    {
                                        "name": "id",
                                        "in": "path",
                                        "required": True,
                                        "schema": {"type": "integer"},
                                    }
                                ],
                                "responses": {
                                    "200": {
                                        "description": "Customer details",
                                        "schema": "$ref:Customer",
                                    }
                                },
                            },
                            "patch": {
                                "summary": "Update a customer",
                                "parameters": [
                                    {
                                        "name": "id",
                                        "in": "path",
                                        "required": True,
                                        "schema": {"type": "integer"},
                                    }
                                ],
                                "requestBody": {"schema": "$ref:CustomerUpdate"},
                                "responses": {
                                    "200": {
                                        "description": "Updated customer",
                                        "schema": "$ref:Customer",
                                    }
                                },
                            },
                            "delete": {
                                "summary": "Delete a customer",
                                "parameters": [
                                    {
                                        "name": "id",
                                        "in": "path",
                                        "required": True,
                                        "schema": {"type": "integer"},
                                    }
                                ],
                                "responses": {
                                    "204": {
                                        "description": "Customer deleted successfully"
                                    }
                                },
                            },
                        },
                    }
                )

        # Specifications for missing methods
        for issue in method_analysis["crud_completeness_issues"][:3]:
            path = issue["path"]
            missing_methods = issue["missing_crud_methods"]

            method_specs = {}
            for method in missing_methods:
                if method == "patch":
                    method_specs["patch"] = {
                        "summary": f"Update {path.split('/')[-2][:-1]}",
                        "requestBody": {"required": True},
                        "responses": {
                            "200": {"description": "Resource updated successfully"}
                        },
                    }
                elif method == "delete":
                    method_specs["delete"] = {
                        "summary": f"Delete {path.split('/')[-2][:-1]}",
                        "responses": {
                            "204": {"description": "Resource deleted successfully"}
                        },
                    }

            if method_specs:
                specifications["missing_method_specs"].append(
                    {"path": path, "methods": method_specs}
                )

        return specifications

    def print_comprehensive_analysis(self) -> None:
        """Print comprehensive analysis and recommendations."""
        print("\n" + "=" * 100)
        print("📊 COMPREHENSIVE API DOCUMENTATION GAP ANALYSIS")
        print("=" * 100)

        # Summary
        summary = self.validation_results["summary"]
        print("\n📋 OVERALL SUMMARY")
        print(f"Current endpoints: {summary['total_endpoints_current']}")
        print(f"Documented endpoints: {summary['total_endpoints_comprehensive']}")
        print(f"Missing endpoints: {summary['endpoints_missing_in_current']}")
        print(f"Method mismatches: {summary['endpoint_method_mismatches']}")
        print(f"Parameter mismatches: {summary['endpoint_parameter_mismatches']}")
        print(f"Schema issues: {summary['schema_issues']}")

        # Analysis
        endpoint_analysis = self.analyze_missing_endpoints()
        method_analysis = self.analyze_method_gaps()
        parameter_analysis = self.analyze_parameter_gaps()
        schema_analysis = self.analyze_schema_gaps()

        print("\n🚨 CRITICAL GAPS")
        print(f"Critical missing endpoints: {len(endpoint_analysis['critical'])}")
        if endpoint_analysis["critical"]:
            for endpoint in endpoint_analysis["critical"][:5]:
                print(f"  - {endpoint}")

        print(
            f"CRUD completeness issues: {len(method_analysis['crud_completeness_issues'])}"
        )
        if method_analysis["crud_completeness_issues"]:
            for issue in method_analysis["crud_completeness_issues"][:3]:
                print(f"  - {issue['path']}: missing {issue['missing_crud_methods']}")

        print("\n⚠️  IMPORTANT GAPS")
        print(f"Important missing endpoints: {len(endpoint_analysis['important'])}")
        print(
            f"Endpoints missing pagination: {len(parameter_analysis['pagination_missing'])}"
        )
        print(
            f"Endpoints missing filtering: {len(parameter_analysis['filtering_missing'])}"
        )

        print("\n📋 SCHEMA ISSUES")
        print(
            f"Critical schemas without descriptions: {len(schema_analysis['critical_schemas_without_descriptions'])}"
        )
        if schema_analysis["critical_schemas_without_descriptions"]:
            print(
                f"  - {', '.join(schema_analysis['critical_schemas_without_descriptions'])}"
            )

        # Recommendations
        recommendations = self.generate_implementation_recommendations()

        print("\n🎯 IMPLEMENTATION RECOMMENDATIONS")
        print("\n🔥 IMMEDIATE ACTIONS (High Impact):")
        for i, action in enumerate(recommendations["immediate_actions"], 1):
            print(f"  {i}. {action['action']}")
            print(f"     Effort: {action['effort']}, Impact: {action['impact']}")
            if isinstance(action["details"], list):
                for detail in action["details"][:3]:
                    print(f"     - {detail}")
            else:
                print(f"     - {action['details']}")

        print("\n📈 SHORT-TERM IMPROVEMENTS:")
        for i, action in enumerate(recommendations["short_term_improvements"], 1):
            print(f"  {i}. {action['action']}")
            print(f"     Effort: {action['effort']}, Impact: {action['impact']}")

        print("\n🔮 LONG-TERM ENHANCEMENTS:")
        for i, action in enumerate(recommendations["long_term_enhancements"], 1):
            print(f"  {i}. {action['action']}")
            print(f"     Effort: {action['effort']}, Impact: {action['impact']}")

        print("\n📝 IMPLEMENTATION PRIORITY ORDER:")
        for i, priority in enumerate(recommendations["implementation_priority"], 1):
            print(f"  {priority}")

        print("\n✅ Analysis complete!")


def main():
    """Main analysis function."""
    repo_root = Path(__file__).parent.parent
    analyzer = DocumentationGapAnalyzer(repo_root)

    try:
        analyzer.print_comprehensive_analysis()

        # Save detailed analysis
        recommendations = analyzer.generate_implementation_recommendations()
        technical_specs = analyzer.generate_technical_specifications()

        analysis_output = {
            "validation_results": analyzer.validation_results,
            "gap_analysis": {
                "missing_endpoints": analyzer.analyze_missing_endpoints(),
                "method_gaps": analyzer.analyze_method_gaps(),
                "parameter_gaps": analyzer.analyze_parameter_gaps(),
                "schema_gaps": analyzer.analyze_schema_gaps(),
            },
            "recommendations": recommendations,
            "technical_specifications": technical_specs,
        }

        output_file = repo_root / "documentation_gap_analysis.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(analysis_output, f, indent=2)

        print(f"\n💾 Complete analysis saved to: {output_file}")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
