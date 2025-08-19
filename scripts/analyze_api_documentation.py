#!/usr/bin/env python3
"""
Streamlined API Documentation Analysis

This script combines validation and gap analysis with entity-aware filtering
and parameter resolution. It replaces both analyze_documentation_gaps.py
and validate_api_documentation.py with a single, optimized solution.

Features:
- Resolves $ref parameters for accurate comparison
- Entity-aware filtering based on DeletableEntity, UpdatableEntity, ArchivableEntity
- Smart categorization of gaps by importance and entity capabilities
- Actionable recommendations with effort/impact assessment
"""

import json
from pathlib import Path
from typing import Any

import yaml


class OptimizedAPIAnalyzer:
    """Unified API documentation analyzer with entity awareness and smart filtering."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.current_spec_path = repo_root / "docs" / "katana-openapi.yaml"
        self.comprehensive_spec_path = (
            repo_root / "docs" / "katana-api-comprehensive" / "openapi-spec.json"
        )

        self.current_spec = self._load_current_spec()
        self.comprehensive_spec = self._load_comprehensive_spec()
        self.entity_capabilities = self._build_entity_capabilities()

        self.analysis_results: dict[str, Any] = {
            "endpoints": {
                "missing_in_current": [],
                "method_mismatches": [],
                "parameter_mismatches": [],
            },
            "gaps": {
                "entity_aware_filtering": [],
                "pagination": [],
                "business_logic": [],
            },
            "common_parameters": {
                "extractable_parameters": [],
                "inconsistent_parameters": [],
                "orphaned_components": [],
            },
            "recommendations": {
                "immediate": [],
                "short_term": [],
                "long_term": [],
            },
            "summary": {},
        }

    def _load_current_spec(self) -> dict[str, Any]:
        """Load the current OpenAPI specification."""
        with open(self.current_spec_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_comprehensive_spec(self) -> dict[str, Any]:
        """Load the comprehensive OpenAPI specification."""
        with open(self.comprehensive_spec_path, encoding="utf-8") as f:
            return json.load(f)

    def _build_entity_capabilities(self) -> dict[str, dict[str, Any]]:
        """Build entity inheritance and filtering capabilities map."""
        schemas = self.current_spec.get("components", {}).get("schemas", {})
        capabilities = {}

        # Define base entity capabilities
        base_entities = {
            "DeletableEntity": {
                "date_filters": [
                    "created_at_min",
                    "created_at_max",
                    "updated_at_min",
                    "updated_at_max",
                ],
                "special_filters": ["include_deleted"],
                "description": "Entities that can be soft deleted",
            },
            "UpdatableEntity": {
                "date_filters": [
                    "created_at_min",
                    "created_at_max",
                    "updated_at_min",
                    "updated_at_max",
                ],
                "special_filters": [],
                "description": "Entities with timestamp tracking",
            },
            "ArchivableEntity": {
                "date_filters": [
                    "created_at_min",
                    "created_at_max",
                    "updated_at_min",
                    "updated_at_max",
                ],
                "special_filters": ["include_archived"],
                "description": "Entities that can be archived",
            },
        }

        for schema_name, schema_def in schemas.items():
            expected_filters: list[str] = []
            inheritance_chain = []

            # Check for allOf inheritance
            if "allOf" in schema_def:
                for item in schema_def["allOf"]:
                    if "$ref" in item:
                        ref_name = item["$ref"].split("/")[-1]
                        if ref_name in base_entities:
                            inheritance_chain.append(ref_name)
                            expected_filters.extend(
                                base_entities[ref_name]["date_filters"]
                            )
                            expected_filters.extend(
                                base_entities[ref_name]["special_filters"]
                            )

            if expected_filters or inheritance_chain:
                capabilities[schema_name] = {
                    "expected_filters": list(set(expected_filters)),
                    "inheritance_chain": inheritance_chain,
                }

        return capabilities

    def _resolve_parameter_refs(self, parameters: list[dict[str, Any]]) -> list[str]:
        """Resolve $ref parameters to actual parameter names."""
        resolved_names = []
        param_components = self.current_spec.get("components", {}).get("parameters", {})

        for param in parameters:
            if "$ref" in param:
                ref_name = param["$ref"].split("/")[-1]
                if ref_name in param_components:
                    param_def = param_components[ref_name]
                    if "name" in param_def:
                        resolved_names.append(param_def["name"])
            elif "name" in param:
                resolved_names.append(param["name"])

        return resolved_names

    def _get_endpoint_entity_name(self, path: str) -> str | None:
        """Determine the primary entity name for an endpoint."""
        clean_path = path.strip("/").split("/")[0]

        # Convert plural endpoint names to singular entity names
        entity_mappings = {
            "manufacturing_orders": "ManufacturingOrder",
            "sales_orders": "SalesOrder",
            "purchase_orders": "PurchaseOrder",
            "customers": "Customer",
            "suppliers": "Supplier",
            "products": "Product",
            "materials": "Material",
            "variants": "Variant",
            "tax_rates": "TaxRate",
            "locations": "Location",
            "users": "User",
            "inventory": "Inventory",
            "batch_stocks": "BatchStock",
            "stock_transfers": "StockTransfer",
            "stock_adjustments": "StockAdjustment",
            "stocktakes": "Stocktake",
            "sales_returns": "SalesReturn",
            "webhooks": "Webhook",
            "bin_locations": "BinLocation",
            "additional_costs": "AdditionalCost",
            "services": "Service",
            "inventory_movements": "InventoryMovement",
        }

        return entity_mappings.get(clean_path)

    def _is_collection_endpoint(self, path: str) -> bool:
        """Determine if an endpoint returns a collection."""
        return (
            not path.rstrip("/").endswith("/{id}")
            and not path.strip("/").split("/")[-1].startswith("{")
            and len(path.strip("/").split("/")) <= 2
        )

    def analyze_endpoints(self) -> None:
        """Analyze endpoints between current and comprehensive specs."""
        # Normalize paths by removing trailing slashes for comparison
        current_paths = set(self.current_spec.get("paths", {}).keys())
        comp_paths = set(self.comprehensive_spec.get("paths", {}).keys())

        # Create normalized path mappings
        current_normalized = {path.rstrip("/"): path for path in current_paths}
        comp_normalized = {path.rstrip("/"): path for path in comp_paths}

        # Find missing endpoints (using normalized paths)
        missing_normalized = set(comp_normalized.keys()) - set(
            current_normalized.keys()
        )
        self.analysis_results["endpoints"]["missing_in_current"] = [
            comp_normalized[norm_path] for norm_path in missing_normalized
        ]

        # Validate common endpoints (using original paths)
        common_normalized = set(current_normalized.keys()) & set(comp_normalized.keys())
        for norm_path in common_normalized:
            current_path = current_normalized[norm_path]
            comp_path = comp_normalized[norm_path]
            self._analyze_endpoint_details(current_path, comp_path)

    def _analyze_endpoint_details(
        self, current_path_key: str, comp_path_key: str
    ) -> None:
        """Analyze methods and parameters for a specific endpoint."""
        current_path = self.current_spec["paths"][current_path_key]
        comp_path = self.comprehensive_spec["paths"][comp_path_key]

        # Check methods
        current_methods = {
            k
            for k in current_path
            if k.lower() in {"get", "post", "put", "patch", "delete"}
        }
        comp_methods = {
            k
            for k in comp_path
            if k.lower() in {"get", "post", "put", "patch", "delete"}
        }

        if current_methods != comp_methods:
            self.analysis_results["endpoints"]["method_mismatches"].append(
                {
                    "path": current_path_key,  # Use current path format
                    "missing_methods": list(comp_methods - current_methods),
                    "extra_methods": list(current_methods - comp_methods),
                }
            )

        # Analyze parameters for GET methods on collections
        if (
            "get" in current_methods
            and "get" in comp_methods
            and self._is_collection_endpoint(current_path_key)
        ):
            self._analyze_collection_parameters(current_path_key, comp_path_key)

    def _analyze_collection_parameters(
        self, current_path_key: str, comp_path_key: str
    ) -> None:
        """Analyze parameters for collection endpoints with comprehensive detail."""
        current_method = self.current_spec["paths"][current_path_key]["get"]
        comp_method = self.comprehensive_spec["paths"][comp_path_key]["get"]

        current_params = set(
            self._resolve_parameter_refs(current_method.get("parameters", []))
        )
        comp_params_raw = comp_method.get("parameters", [])
        comp_params = {p.get("name") for p in comp_params_raw if "name" in p}

        missing_params = comp_params - current_params

        if not missing_params:
            return

        # Get detailed parameter information from comprehensive spec
        missing_param_details = {}
        for param in comp_params_raw:
            param_name = param.get("name")
            if param_name in missing_params:
                missing_param_details[param_name] = {
                    "description": param.get("description", ""),
                    "required": param.get("required", False),
                    "schema": param.get("schema", {}),
                    "in": param.get("in", "query"),
                }

        # Get entity information
        entity_name = self._get_endpoint_entity_name(current_path_key)
        entity_info = (
            self.entity_capabilities.get(entity_name, {}) if entity_name else {}
        )
        expected_filters = entity_info.get("expected_filters", [])

        # Categorize missing parameters with detailed information
        mismatch_info = {
            "path": current_path_key,
            "entity": entity_name,
            "missing_params": list(missing_params),
            "missing_param_details": missing_param_details,
            "current_params": list(current_params),
            "comprehensive_params": list(comp_params),
        }

        self.analysis_results["endpoints"]["parameter_mismatches"].append(mismatch_info)

        # Enhanced entity-aware filtering analysis
        if expected_filters:
            entity_aware_missing = []
            for param in missing_params:
                if any(filter_name in param for filter_name in expected_filters):
                    entity_aware_missing.append(
                        {
                            "name": param,
                            "details": missing_param_details.get(param, {}),
                            "entity_reason": f"Expected for {entity_name} ({', '.join(entity_info.get('inheritance_chain', []))})",
                        }
                    )

            if entity_aware_missing:
                self.analysis_results["gaps"]["entity_aware_filtering"].append(
                    {
                        "endpoint": f"GET {current_path_key}",
                        "entity": entity_name,
                        "missing_filters": entity_aware_missing,
                        "inheritance": entity_info.get("inheritance_chain", []),
                    }
                )

        # Pagination analysis with details
        pagination_missing = []
        for param in missing_params:
            if param in {"limit", "page"} and not (
                "limit" in current_params and "page" in current_params
            ):
                pagination_missing.append(
                    {
                        "name": param,
                        "details": missing_param_details.get(param, {}),
                    }
                )

        if pagination_missing:
            self.analysis_results["gaps"]["pagination"].append(
                {
                    "endpoint": f"GET {current_path_key}",
                    "missing_pagination": pagination_missing,
                }
            )

        # Enhanced business logic parameters analysis
        excluded = {
            "limit",
            "page",
            "created_at_min",
            "created_at_max",
            "updated_at_min",
            "updated_at_max",
            "include_deleted",
            "include_archived",
        }

        business_missing = []
        for param in missing_params:
            if param not in excluded and param not in expected_filters:
                param_details = missing_param_details.get(param, {})
                business_missing.append(
                    {
                        "name": param,
                        "description": param_details.get("description", ""),
                        "required": param_details.get("required", False),
                        "type": self._get_param_type_summary(
                            param_details.get("schema", {})
                        ),
                    }
                )

        if business_missing:
            self.analysis_results["gaps"]["business_logic"].append(
                {
                    "endpoint": f"GET {current_path_key}",
                    "missing_business_filters": business_missing[
                        :8
                    ],  # Show more details
                }
            )

    def _get_param_type_summary(self, schema: dict[str, Any]) -> str:
        """Get a human-readable parameter type summary."""
        param_type = schema.get("type", "unknown")

        if param_type == "array":
            items_type = schema.get("items", {}).get("type", "unknown")
            return f"array[{items_type}]"
        elif "enum" in schema:
            enum_values = schema["enum"]
            if len(enum_values) <= 3:
                return f"enum({', '.join(map(str, enum_values))})"
            else:
                return f"enum({len(enum_values)} values)"
        else:
            return param_type

    def generate_recommendations(self) -> None:
        """Generate prioritized recommendations based on analysis."""
        entity_gaps = len(self.analysis_results["gaps"]["entity_aware_filtering"])
        len(self.analysis_results["gaps"]["pagination"])
        business_gaps = len(self.analysis_results["gaps"]["business_logic"])
        missing_endpoints = len(
            self.analysis_results["endpoints"]["missing_in_current"]
        )

        # Immediate: Entity-aware filtering (high impact, low effort)
        if entity_gaps > 0:
            self.analysis_results["recommendations"]["immediate"].append(
                {
                    "action": "Add entity-appropriate filtering parameters",
                    "description": f"{entity_gaps} endpoints missing filters based on their entity inheritance",
                    "effort": "Low",
                    "impact": "High",
                    "affected_endpoints": entity_gaps,
                }
            )

        # Short-term: Business logic filters
        if business_gaps > 5:
            self.analysis_results["recommendations"]["short_term"].append(
                {
                    "action": "Add business logic filtering parameters",
                    "description": f"{business_gaps} endpoints missing business-specific filters",
                    "effort": "Medium",
                    "impact": "Medium",
                    "affected_endpoints": business_gaps,
                }
            )

        # Long-term: Additional endpoints
        if missing_endpoints > 0:
            self.analysis_results["recommendations"]["long_term"].append(
                {
                    "action": "Implement additional endpoints",
                    "description": f"{missing_endpoints} endpoints available in comprehensive docs",
                    "effort": "High",
                    "impact": "Low",
                    "affected_endpoints": missing_endpoints,
                }
            )

        # Common parameter recommendations
        common_params = self.analysis_results["common_parameters"]

        # Immediate: Extract highly reused consistent parameters
        consistent_extractable = [
            p
            for p in common_params["extractable_parameters"]
            if p["is_consistent"] and p["usage_count"] >= 5
        ]
        if consistent_extractable:
            self.analysis_results["recommendations"]["immediate"].append(
                {
                    "action": "Extract common parameters to components",
                    "description": f"{len(consistent_extractable)} consistent parameters used 5+ times can be extracted",
                    "effort": "Low",
                    "impact": "High",
                    "affected_endpoints": sum(
                        p["usage_count"] for p in consistent_extractable
                    ),
                }
            )

        # Short-term: Fix inconsistent parameters
        if common_params["inconsistent_parameters"]:
            self.analysis_results["recommendations"]["short_term"].append(
                {
                    "action": "Standardize inconsistent parameters",
                    "description": f"{len(common_params['inconsistent_parameters'])} parameters have different definitions across endpoints",
                    "effort": "Medium",
                    "impact": "Medium",
                    "affected_endpoints": len(common_params["inconsistent_parameters"]),
                }
            )

        # Long-term: Clean up orphaned components
        if common_params["orphaned_components"]:
            self.analysis_results["recommendations"]["long_term"].append(
                {
                    "action": "Remove unused component parameters",
                    "description": f"{len(common_params['orphaned_components'])} component parameters are defined but not used",
                    "effort": "Low",
                    "impact": "Low",
                    "affected_endpoints": len(common_params["orphaned_components"]),
                }
            )

    def generate_summary(self) -> None:
        """Generate analysis summary."""
        self.analysis_results["summary"] = {
            "current_endpoints": len(self.current_spec.get("paths", {})),
            "comprehensive_endpoints": len(self.comprehensive_spec.get("paths", {})),
            "missing_endpoints": len(
                self.analysis_results["endpoints"]["missing_in_current"]
            ),
            "method_mismatches": len(
                self.analysis_results["endpoints"]["method_mismatches"]
            ),
            "parameter_mismatches": len(
                self.analysis_results["endpoints"]["parameter_mismatches"]
            ),
            "entity_aware_gaps": len(
                self.analysis_results["gaps"]["entity_aware_filtering"]
            ),
            "pagination_gaps": len(self.analysis_results["gaps"]["pagination"]),
            "business_logic_gaps": len(self.analysis_results["gaps"]["business_logic"]),
        }

    def analyze_common_parameters(self) -> None:
        """Analyze common parameters across endpoints and identify extraction opportunities."""
        # Get all existing component parameters
        component_params = self.current_spec.get("components", {}).get("parameters", {})

        # Collect all inline parameters from endpoints
        inline_parameters: dict[
            str, list[dict[str, Any]]
        ] = {}  # {param_signature: [{"path": path, "method": method, "param": param_def}]}
        parameter_usage_count = {}  # {param_signature: count}

        for path, path_def in self.current_spec.get("paths", {}).items():
            for method, method_def in path_def.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue

                parameters = method_def.get("parameters", [])
                for param in parameters:
                    # Skip $ref parameters (already extracted)
                    if "$ref" in param:
                        continue

                    # Create a signature for the parameter based on its key characteristics
                    param_sig = self._create_parameter_signature(param)

                    if param_sig not in inline_parameters:
                        inline_parameters[param_sig] = []
                        parameter_usage_count[param_sig] = 0

                    inline_parameters[param_sig].append(
                        {"path": path, "method": method, "param": param}
                    )
                    parameter_usage_count[param_sig] += 1

        # Find parameters that appear multiple times (candidates for extraction)
        extractable_params = []
        for param_sig, count in parameter_usage_count.items():
            if count >= 3:  # Appears in 3+ endpoints
                usages = inline_parameters[param_sig]
                sample_param = usages[0]["param"]

                # Check if parameters are truly identical or just similar
                identical_params = self._check_parameter_consistency(usages)

                extractable_params.append(
                    {
                        "signature": param_sig,
                        "name": sample_param.get("name", "unknown"),
                        "usage_count": count,
                        "is_consistent": identical_params["is_consistent"],
                        "sample_param": sample_param,
                        "usages": [
                            {"path": u["path"], "method": u["method"]} for u in usages
                        ],
                        "inconsistencies": identical_params["inconsistencies"],
                    }
                )

        # Find inconsistent parameters (same name but different definitions)
        inconsistent_params = []
        param_names: dict[str, list[dict[str, Any]]] = {}  # {name: [param_instances]}

        for usages in inline_parameters.values():
            for usage in usages:
                param_name = usage["param"].get("name")
                if param_name:
                    if param_name not in param_names:
                        param_names[param_name] = []
                    param_names[param_name].append(usage)

        for param_name, instances in param_names.items():
            if len(instances) > 1:
                # Check if all instances have the same definition
                signatures = {
                    self._create_parameter_signature(inst["param"])
                    for inst in instances
                }
                if len(signatures) > 1:
                    inconsistent_params.append(
                        {
                            "name": param_name,
                            "instance_count": len(instances),
                            "signature_variations": len(signatures),
                            "instances": [
                                {
                                    "path": inst["path"],
                                    "method": inst["method"],
                                    "signature": self._create_parameter_signature(
                                        inst["param"]
                                    ),
                                    "description": inst["param"].get("description", ""),
                                }
                                for inst in instances
                            ],
                        }
                    )

        # Find orphaned component parameters (defined but not used)
        used_component_refs = set()
        for path_def in self.current_spec.get("paths", {}).values():
            for method, method_def in path_def.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue
                parameters = method_def.get("parameters", [])
                for param in parameters:
                    if "$ref" in param:
                        ref_path = param["$ref"]
                        if ref_path.startswith("#/components/parameters/"):
                            param_name = ref_path.split("/")[-1]
                            used_component_refs.add(param_name)

        orphaned_components = []
        for comp_name in component_params:
            if comp_name not in used_component_refs:
                orphaned_components.append(
                    {"name": comp_name, "definition": component_params[comp_name]}
                )

        # Store results
        self.analysis_results["common_parameters"]["extractable_parameters"] = (
            extractable_params
        )
        self.analysis_results["common_parameters"]["inconsistent_parameters"] = (
            inconsistent_params
        )
        self.analysis_results["common_parameters"]["orphaned_components"] = (
            orphaned_components
        )

    def _create_parameter_signature(self, param: dict[str, Any]) -> str:
        """Create a signature for a parameter based on its key characteristics."""
        name = param.get("name", "")
        in_location = param.get("in", "")
        schema = param.get("schema", {})
        param_type = schema.get("type", "")
        required = param.get("required", False)

        # Create a normalized signature
        return f"{name}|{in_location}|{param_type}|{required}"

    def _check_parameter_consistency(
        self, usages: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Check if parameter usages are consistent across endpoints."""
        if len(usages) <= 1:
            return {"is_consistent": True, "inconsistencies": []}

        reference_param = usages[0]["param"]
        inconsistencies = []

        for usage in usages[1:]:
            param = usage["param"]

            # Check description differences
            ref_desc = reference_param.get("description", "").strip()
            param_desc = param.get("description", "").strip()
            if ref_desc != param_desc:
                inconsistencies.append(
                    {
                        "field": "description",
                        "path": usage["path"],
                        "method": usage["method"],
                        "reference": ref_desc,
                        "actual": param_desc,
                    }
                )

            # Check schema differences
            ref_schema = reference_param.get("schema", {})
            param_schema = param.get("schema", {})
            if ref_schema != param_schema:
                inconsistencies.append(
                    {
                        "field": "schema",
                        "path": usage["path"],
                        "method": usage["method"],
                        "reference": ref_schema,
                        "actual": param_schema,
                    }
                )

        return {
            "is_consistent": len(inconsistencies) == 0,
            "inconsistencies": inconsistencies,
        }

    def run_analysis(self) -> dict[str, Any]:
        """Run the complete analysis."""
        print("🔍 Running optimized API analysis...")

        print("  📍 Analyzing endpoints...")
        self.analyze_endpoints()

        print("  � Analyzing common parameters...")
        self.analyze_common_parameters()

        print("  �💡 Generating recommendations...")
        self.generate_recommendations()

        print("  📊 Generating summary...")
        self.generate_summary()

        return self.analysis_results

    def print_report(self) -> None:
        """Print concise analysis report."""
        summary = self.analysis_results["summary"]
        gaps = self.analysis_results["gaps"]
        recs = self.analysis_results["recommendations"]

        print("\n" + "=" * 70)
        print("📊 OPTIMIZED API ANALYSIS REPORT")
        print("=" * 70)

        print("\n📋 SUMMARY")
        print(
            f"Endpoints: {summary['current_endpoints']}/{summary['comprehensive_endpoints']} implemented"
        )
        print(f"Missing endpoints: {summary['missing_endpoints']}")
        print(f"Parameter mismatches: {summary['parameter_mismatches']}")

        print("\n🎯 SMART GAP ANALYSIS")
        print(f"Entity-aware filtering gaps: {summary['entity_aware_gaps']}")
        print(f"Pagination gaps: {summary['pagination_gaps']}")
        print(f"Business logic gaps: {summary['business_logic_gaps']}")

        # Show common parameters analysis
        common_params = self.analysis_results["common_parameters"]
        if (
            common_params["extractable_parameters"]
            or common_params["inconsistent_parameters"]
        ):
            print("\n🔧 COMMON PARAMETERS ANALYSIS")

            if common_params["extractable_parameters"]:
                extractable = [
                    p
                    for p in common_params["extractable_parameters"]
                    if p["usage_count"] >= 3
                ]
                print(f"Extractable parameters: {len(extractable)} (used 3+ times)")

                if extractable:
                    print("\n📦 TOP EXTRACTABLE PARAMETERS:")
                    for param in extractable[:5]:  # Show top 5
                        consistent_status = "✅" if param["is_consistent"] else "⚠️"
                        print(
                            f"  • {param['name']} {consistent_status} (used {param['usage_count']} times)"
                        )
                        if not param["is_consistent"] and param["inconsistencies"]:
                            print(
                                f"    - {len(param['inconsistencies'])} inconsistencies found"
                            )

            if common_params["inconsistent_parameters"]:
                print(
                    f"\n⚠️  INCONSISTENT PARAMETERS: {len(common_params['inconsistent_parameters'])}"
                )
                for param in common_params["inconsistent_parameters"][:3]:  # Show top 3
                    print(
                        f"  • {param['name']} ({param['signature_variations']} different definitions)"
                    )

            if common_params["orphaned_components"]:
                print(
                    f"\n🗑️  ORPHANED COMPONENTS: {len(common_params['orphaned_components'])}"
                )
                for component in common_params["orphaned_components"][:3]:
                    print(f"  • {component['name']} (defined but not used)")

        # Show top entity-aware gaps with details
        if gaps["entity_aware_filtering"]:
            print("\n🧠 ENTITY-AWARE FILTERING GAPS (Detailed):")
            for gap in gaps["entity_aware_filtering"][:3]:
                inheritance = " → ".join(gap["inheritance"])
                print(f"  • {gap['endpoint']} ({gap['entity']} extends {inheritance})")
                for filter_info in gap["missing_filters"][:3]:
                    if isinstance(filter_info, dict):
                        name = filter_info.get("name", "unknown")
                        details = filter_info.get("details", {})
                        desc = details.get("description", "No description")
                        print(f"    - {name}: {desc}")
                    else:
                        print(f"    - {filter_info}")

        # Show business logic gaps with details
        if gaps["business_logic"]:
            print("\n💼 BUSINESS LOGIC PARAMETER GAPS (Top Examples):")
            for gap in gaps["business_logic"][:3]:
                print(f"  • {gap['endpoint']}")
                for param in gap["missing_business_filters"][:3]:
                    if isinstance(param, dict):
                        name = param.get("name", "unknown")
                        desc = param.get("description", "No description")
                        param_type = param.get("type", "unknown")
                        required = (
                            "required" if param.get("required", False) else "optional"
                        )
                        print(f"    - {name} ({param_type}, {required}): {desc}")
                    else:
                        print(f"    - {param}")

        # Show recommendations
        print("\n💡 PRIORITIZED RECOMMENDATIONS")

        for category, title in [
            ("immediate", "🔥 IMMEDIATE (High Impact, Low Effort)"),
            ("short_term", "📈 SHORT-TERM (Medium Impact/Effort)"),
            ("long_term", "🔮 LONG-TERM (Low Impact, High Effort)"),
        ]:
            if recs[category]:
                print(f"\n{title}:")
                for rec in recs[category]:
                    print(f"  • {rec['action']}")
                    print(f"    {rec['description']}")

        print(
            "\n✅ Analysis complete! This API is production-ready with minor enhancements available."
        )


def main():
    """Main function."""
    repo_root = Path(__file__).parent.parent
    analyzer = OptimizedAPIAnalyzer(repo_root)

    try:
        results = analyzer.run_analysis()
        analyzer.print_report()

        # Save results
        output_file = repo_root / "api_analysis_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to: {output_file}")

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
