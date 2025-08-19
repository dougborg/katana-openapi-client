"""
Test API quality analysis and design recommendations.

This module validates the strategic aspects of API design that the analyze_api_documentation.py
script identifies, converting its recommendations into automated tests for continuous validation.
"""

from pathlib import Path
from typing import Any

import pytest
import yaml


class TestAPIQualityAnalysis:
    """Test API quality metrics and design recommendations."""

    @pytest.fixture(scope="class")
    def api_spec(self) -> dict[str, Any]:
        """Load the OpenAPI specification."""
        spec_path = Path(__file__).parent.parent / "docs" / "katana-openapi.yaml"
        with open(spec_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_no_orphaned_component_parameters(self, api_spec: dict[str, Any]) -> None:
        """
        Test that all component parameters are actually used in endpoints.

        Orphaned components add maintenance burden and confuse API consumers.
        Currently informational - logs orphaned components as warnings.
        """
        # Get all component parameters
        component_params = api_spec.get("components", {}).get("parameters", {})

        if not component_params:
            pytest.skip("No component parameters defined")

        # Find all parameter references in endpoints
        used_params: set[str] = set()

        for _path, path_def in api_spec.get("paths", {}).items():
            for method, method_def in path_def.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue

                parameters = method_def.get("parameters", [])
                for param in parameters:
                    if "$ref" in param:
                        # Extract component name from $ref
                        ref_path = param["$ref"]
                        if ref_path.startswith("#/components/parameters/"):
                            param_name = ref_path.split("/")[-1]
                            used_params.add(param_name)

        # Check for orphaned components
        defined_params = set(component_params.keys())
        orphaned_params = defined_params - used_params

        if orphaned_params:
            orphaned_list = sorted(orphaned_params)
            pytest.fail(
                f"Found {len(orphaned_params)} orphaned component parameters: {orphaned_list}. "
                f"These parameters are defined in components but never referenced in endpoints. "
                f"Consider removing them or adding them to relevant endpoints."
            )

    def test_parameter_consistency_across_endpoints(
        self, api_spec: dict[str, Any]
    ) -> None:
        """
        Test that parameters with the same name have consistent definitions across endpoints.

        Inconsistent parameter definitions confuse API consumers and indicate design issues.
        """
        # Collect all inline parameters (non-$ref) grouped by name
        parameters_by_name: dict[str, list[dict[str, Any]]] = {}

        for path, path_def in api_spec.get("paths", {}).items():
            for method, method_def in path_def.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue

                parameters = method_def.get("parameters", [])
                for param in parameters:
                    # Skip $ref parameters (they're already consistent by definition)
                    if "$ref" in param:
                        continue

                    param_name = param.get("name")
                    if not param_name:
                        continue

                    if param_name not in parameters_by_name:
                        parameters_by_name[param_name] = []

                    # Add context for better error messages
                    param_with_context = {
                        **param,
                        "_context": {"path": path, "method": method},
                    }
                    parameters_by_name[param_name].append(param_with_context)

        # Check consistency for parameters that appear multiple times
        inconsistencies = []

        for param_name, param_list in parameters_by_name.items():
            if len(param_list) <= 1:
                continue  # Can't be inconsistent if it only appears once

            # Use first parameter as reference
            reference = param_list[0]
            ref_context = reference["_context"]

            for param in param_list[1:]:
                context = param["_context"]

                # Compare key fields (excluding context)
                ref_clean = {k: v for k, v in reference.items() if k != "_context"}
                param_clean = {k: v for k, v in param.items() if k != "_context"}

                if ref_clean != param_clean:
                    inconsistencies.append(
                        {
                            "parameter": param_name,
                            "reference": f"{ref_context['method'].upper()} {ref_context['path']}",
                            "conflicting": f"{context['method'].upper()} {context['path']}",
                            "reference_def": ref_clean,
                            "conflicting_def": param_clean,
                        }
                    )

        if inconsistencies:
            error_details = []
            for inc in inconsistencies[:5]:  # Show first 5 to avoid overwhelming output
                error_details.append(
                    f"Parameter '{inc['parameter']}' differs between "
                    f"{inc['reference']} and {inc['conflicting']}"
                )

            pytest.fail(
                f"Found {len(inconsistencies)} parameter inconsistencies:\n"
                + "\n".join(f"  • {detail}" for detail in error_details)
                + (
                    f"\n  ... and {len(inconsistencies) - 5} more"
                    if len(inconsistencies) > 5
                    else ""
                )
            )

    def test_extractable_parameters_identified(self, api_spec: dict[str, Any]) -> None:
        """
        Test identification of parameters that could be extracted to reusable components.

        This doesn't fail the test but provides visibility into API design optimization opportunities.
        """
        # Collect all inline parameters grouped by signature
        parameter_signatures: dict[str, list[dict[str, Any]]] = {}

        for path, path_def in api_spec.get("paths", {}).items():
            for method, method_def in path_def.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue

                parameters = method_def.get("parameters", [])
                for param in parameters:
                    # Skip $ref parameters (already extracted)
                    if "$ref" in param:
                        continue

                    # Create signature based on key characteristics
                    signature = self._create_parameter_signature(param)
                    if not signature:
                        continue

                    if signature not in parameter_signatures:
                        parameter_signatures[signature] = []

                    parameter_signatures[signature].append(
                        {"path": path, "method": method, "param": param}
                    )

        # Find parameters that appear 3+ times (good extraction candidates)
        extractable = []
        for signature, usages in parameter_signatures.items():
            if len(usages) >= 3:
                # Check if all usages are consistent
                reference_param = usages[0]["param"]
                is_consistent = all(
                    self._params_equivalent(reference_param, usage["param"])
                    for usage in usages[1:]
                )

                if is_consistent:
                    extractable.append(
                        {
                            "name": reference_param.get("name"),
                            "signature": signature,
                            "usage_count": len(usages),
                            "endpoints": [
                                f"{u['method'].upper()} {u['path']}" for u in usages
                            ],
                        }
                    )

        # This should fail if we have extractable parameters - they represent poor API design
        if extractable:
            extraction_details = []
            for param in extractable:
                endpoints_str = ", ".join(param["endpoints"][:3])
                if len(param["endpoints"]) > 3:
                    endpoints_str += f" (and {len(param['endpoints']) - 3} more)"
                extraction_details.append(
                    f"'{param['name']}' used {param['usage_count']} times: {endpoints_str}"
                )

            pytest.fail(
                f"Found {len(extractable)} parameters that could be extracted to components:\n"
                + "\n".join(f"  • {detail}" for detail in extraction_details)
                + "\nConsider extracting these to reusable component parameters."
            )

    def test_api_design_metrics(self, api_spec: dict[str, Any]) -> None:
        """
        Test overall API design quality metrics.

        Zero tolerance - fails on any quality issues.
        """
        # Count different types of parameters
        total_endpoints = len(list(api_spec.get("paths", {}).keys()))

        component_params = len(api_spec.get("components", {}).get("parameters", {}))

        # Count inline parameters
        inline_param_count = 0
        total_params = 0

        for _path, path_def in api_spec.get("paths", {}).items():
            for method, method_def in path_def.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue

                parameters = method_def.get("parameters", [])
                for param in parameters:
                    total_params += 1
                    if "$ref" not in param:
                        inline_param_count += 1

        # Calculate reuse rate
        (component_params / total_params * 100) if total_params > 0 else 0

        # Count orphaned components (similar to other test but simplified)
        used_params = set()
        for _path, path_def in api_spec.get("paths", {}).items():
            for method, method_def in path_def.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue

                parameters = method_def.get("parameters", [])
                for param in parameters:
                    if "$ref" in param:
                        ref_path = param["$ref"]
                        if ref_path.startswith("#/components/parameters/"):
                            param_name = ref_path.split("/")[-1]
                            used_params.add(param_name)

        component_params_set = set(
            api_spec.get("components", {}).get("parameters", {}).keys()
        )
        orphaned_count = len(component_params_set - used_params)

        # Count extractable parameters (simplified version)
        parameter_signatures: dict[str, int] = {}
        for _path, path_def in api_spec.get("paths", {}).items():
            for method, method_def in path_def.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue

                parameters = method_def.get("parameters", [])
                for param in parameters:
                    if "$ref" not in param:
                        signature = self._create_parameter_signature(param)
                        if signature:
                            parameter_signatures[signature] = (
                                parameter_signatures.get(signature, 0) + 1
                            )

        extractable_count = len(
            [sig for sig, count in parameter_signatures.items() if count >= 3]
        )

        # Zero tolerance - fail on ANY quality issues
        if orphaned_count > 0:
            pytest.fail(
                f"Found {orphaned_count} orphaned component parameters (zero tolerance)"
            )

        if extractable_count > 0:
            pytest.fail(
                f"Found {extractable_count} extractable parameters that should be moved to components (zero tolerance)"
            )

        # Assert minimum API quality standards
        assert total_endpoints > 0, "No endpoints found in API specification"
        assert total_params > 0, "No parameters found in API specification"

    def _create_parameter_signature(self, param: dict[str, Any]) -> str:
        """Create a signature for parameter comparison."""
        name = param.get("name", "")
        in_location = param.get("in", "")
        schema = param.get("schema", {})
        param_type = schema.get("type", "unknown")
        required = param.get("required", False)

        if not name or not in_location:
            return ""

        return f"{name}|{in_location}|{param_type}|{required}"

    def _params_equivalent(
        self, param1: dict[str, Any], param2: dict[str, Any]
    ) -> bool:
        """Check if two parameters are equivalent for extraction purposes."""
        # Remove context fields and compare
        clean1 = {k: v for k, v in param1.items() if not k.startswith("_")}
        clean2 = {k: v for k, v in param2.items() if not k.startswith("_")}
        return clean1 == clean2

    def _calculate_api_metrics(self, api_spec: dict[str, Any]) -> dict[str, Any]:
        """Calculate comprehensive API design metrics."""
        # Count endpoints
        total_endpoints = 0
        total_parameters = 0
        inline_parameters = 0

        for _path, path_def in api_spec.get("paths", {}).items():
            for method, method_def in path_def.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue

                total_endpoints += 1
                parameters = method_def.get("parameters", [])
                total_parameters += len(parameters)

                # Count inline vs component parameters
                for param in parameters:
                    if "$ref" not in param:
                        inline_parameters += 1

        # Count component parameters
        component_params = api_spec.get("components", {}).get("parameters", {})
        component_parameters = len(component_params)

        # Calculate orphaned components (defined but not used)
        used_components = set()
        for _path, path_def in api_spec.get("paths", {}).items():
            for method, method_def in path_def.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue

                parameters = method_def.get("parameters", [])
                for param in parameters:
                    if "$ref" in param:
                        ref_path = param["$ref"]
                        if ref_path.startswith("#/components/parameters/"):
                            param_name = ref_path.split("/")[-1]
                            used_components.add(param_name)

        orphaned_components = len(set(component_params.keys()) - used_components)

        # Calculate extractable parameters (inline params used 3+ times)
        parameter_usage: dict[str, int] = {}
        for _path, path_def in api_spec.get("paths", {}).items():
            for method, method_def in path_def.items():
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue

                parameters = method_def.get("parameters", [])
                for param in parameters:
                    if "$ref" in param:
                        continue

                    signature = self._create_parameter_signature(param)
                    if signature:
                        parameter_usage[signature] = (
                            parameter_usage.get(signature, 0) + 1
                        )

        extractable_parameters = sum(
            1 for count in parameter_usage.values() if count >= 3
        )

        # Calculate reuse rate
        reused_parameters = len(used_components) + extractable_parameters
        parameter_reuse_rate = reused_parameters / max(total_parameters, 1)

        return {
            "total_endpoints": total_endpoints,
            "total_parameters": total_parameters,
            "component_parameters": component_parameters,
            "inline_parameters": inline_parameters,
            "orphaned_components": orphaned_components,
            "extractable_parameters": extractable_parameters,
            "parameter_reuse_rate": parameter_reuse_rate,
        }
