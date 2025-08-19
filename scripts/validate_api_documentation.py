#!/usr/bin/env python3
"""
API Documentation Validation Script

This script validates schemas and endpoint definitions against the comprehensive
documentation downloaded from developer.katanamrp.com.

It compares:
1. Current OpenAPI spec (docs/katana-openapi.yaml) against comprehensive docs OpenAPI spec
2. Individual endpoint documentation files
3. Schema definitions and consistency
4. Parameter specifications and examples
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import yaml


class APIDocumentationValidator:
    """Validates API documentation consistency."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.current_spec_path = repo_root / "docs" / "katana-openapi.yaml"
        self.comprehensive_spec_path = repo_root / "docs" / "katana-api-comprehensive" / "openapi-spec.json"
        self.comprehensive_docs_dir = repo_root / "docs" / "katana-api-comprehensive"
        
        self.current_spec = self._load_current_spec()
        self.comprehensive_spec = self._load_comprehensive_spec()
        self.validation_results = {
            "endpoints": {
                "missing_in_current": [],
                "missing_in_comprehensive": [],
                "method_mismatches": [],
                "parameter_mismatches": []
            },
            "schemas": {
                "missing_definitions": [],
                "property_mismatches": [],
                "type_mismatches": [],
                "description_mismatches": []
            },
            "documentation": {
                "missing_files": [],
                "content_mismatches": []
            },
            "summary": {}
        }

    def _load_current_spec(self) -> Dict[str, Any]:
        """Load the current OpenAPI specification."""
        with open(self.current_spec_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _load_comprehensive_spec(self) -> Dict[str, Any]:
        """Load the comprehensive OpenAPI specification."""
        with open(self.comprehensive_spec_path, encoding="utf-8") as f:
            return json.load(f)

    def validate_endpoints(self) -> None:
        """Validate endpoint definitions between specs."""
        current_paths = set(self.current_spec.get("paths", {}).keys())
        comp_paths = set(self.comprehensive_spec.get("paths", {}).keys())
        
        # Find missing endpoints
        self.validation_results["endpoints"]["missing_in_current"] = list(comp_paths - current_paths)
        self.validation_results["endpoints"]["missing_in_comprehensive"] = list(current_paths - comp_paths)
        
        # Validate common endpoints
        common_paths = current_paths & comp_paths
        for path in common_paths:
            self._validate_endpoint_methods(path)
            self._validate_endpoint_parameters(path)

    def _validate_endpoint_methods(self, path: str) -> None:
        """Validate HTTP methods for a specific endpoint."""
        current_methods = set(self.current_spec["paths"][path].keys())
        comp_methods = set(self.comprehensive_spec["paths"][path].keys())
        
        # Filter out non-method keys
        current_methods = {m for m in current_methods if m.lower() in 
                          {"get", "post", "put", "patch", "delete", "options", "head"}}
        comp_methods = {m for m in comp_methods if m.lower() in 
                       {"get", "post", "put", "patch", "delete", "options", "head"}}
        
        if current_methods != comp_methods:
            self.validation_results["endpoints"]["method_mismatches"].append({
                "path": path,
                "current_methods": list(current_methods),
                "comprehensive_methods": list(comp_methods),
                "missing_in_current": list(comp_methods - current_methods),
                "extra_in_current": list(current_methods - comp_methods)
            })

    def _validate_endpoint_parameters(self, path: str) -> None:
        """Validate parameters for a specific endpoint."""
        current_path = self.current_spec["paths"][path]
        comp_path = self.comprehensive_spec["paths"][path]
        
        for method in current_path:
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
                
            if method not in comp_path:
                continue
                
            current_params = current_path[method].get("parameters", [])
            comp_params = comp_path[method].get("parameters", [])
            
            # Extract parameter names for comparison
            current_param_names = {p.get("name") for p in current_params if "name" in p}
            comp_param_names = {p.get("name") for p in comp_params if "name" in p}
            
            if current_param_names != comp_param_names:
                self.validation_results["endpoints"]["parameter_mismatches"].append({
                    "path": path,
                    "method": method,
                    "current_params": list(current_param_names),
                    "comprehensive_params": list(comp_param_names),
                    "missing_in_current": list(comp_param_names - current_param_names),
                    "extra_in_current": list(current_param_names - comp_param_names)
                })

    def validate_schemas(self) -> None:
        """Validate schema definitions."""
        current_schemas = self.current_spec.get("components", {}).get("schemas", {})
        comp_schemas = self.comprehensive_spec.get("components", {}).get("schemas", {})
        
        # Note: Comprehensive spec has 0 schemas, so we'll validate against 
        # individual documentation files and look for schema references
        self._validate_schema_references_in_docs()
        self._validate_schema_completeness()

    def _validate_schema_references_in_docs(self) -> None:
        """Check for schema references in individual documentation files."""
        # Look for schema references in markdown files
        doc_files = list(self.comprehensive_docs_dir.glob("*.md"))
        referenced_schemas = set()
        
        for doc_file in doc_files:
            try:
                with open(doc_file, encoding="utf-8") as f:
                    content = f.read()
                    # Look for schema-like structures in the content
                    # This is a simplified approach - could be enhanced based on actual content format
                    schemas_in_content = re.findall(r'"[A-Z][A-Za-z]*"', content)
                    referenced_schemas.update(schema.strip('"') for schema in schemas_in_content)
            except Exception:
                continue
        
        current_schemas = set(self.current_spec.get("components", {}).get("schemas", {}).keys())
        
        # This is a basic check - in practice, we'd need more sophisticated parsing
        # of the documentation to extract actual schema requirements
        potential_missing = referenced_schemas - current_schemas
        if potential_missing:
            self.validation_results["schemas"]["missing_definitions"].extend(
                list(potential_missing)[:10]  # Limit to first 10 for practicality
            )

    def _validate_schema_completeness(self) -> None:
        """Validate that all schemas referenced in current spec are complete."""
        current_schemas = self.current_spec.get("components", {}).get("schemas", {})
        
        # Check for schemas that might be missing properties or descriptions
        incomplete_schemas = []
        for schema_name, schema_def in current_schemas.items():
            issues = []
            
            if "description" not in schema_def or not schema_def["description"].strip():
                issues.append("missing_description")
                
            if "properties" in schema_def:
                for prop_name, prop_def in schema_def["properties"].items():
                    if "description" not in prop_def:
                        issues.append(f"property_{prop_name}_missing_description")
                        
            if issues:
                incomplete_schemas.append({
                    "schema": schema_name,
                    "issues": issues
                })
        
        self.validation_results["schemas"]["property_mismatches"] = incomplete_schemas

    def validate_documentation_files(self) -> None:
        """Validate individual documentation files against current spec."""
        current_paths = self.current_spec.get("paths", {})
        
        # Map endpoint paths to expected documentation files
        expected_doc_files = self._generate_expected_doc_files(current_paths)
        actual_doc_files = {f.stem for f in self.comprehensive_docs_dir.glob("*.md")}
        
        missing_docs = []
        for expected_file in expected_doc_files:
            if expected_file not in actual_doc_files:
                missing_docs.append(expected_file)
                
        self.validation_results["documentation"]["missing_files"] = missing_docs

    def _generate_expected_doc_files(self, paths: Dict[str, Any]) -> Set[str]:
        """Generate expected documentation file names from API paths."""
        expected_files = set()
        
        for path, methods in paths.items():
            for method in methods:
                if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                    continue
                    
                # Convert path and method to expected filename format
                # This is based on patterns observed in the comprehensive docs
                operation_id = methods[method].get("operationId", "")
                if operation_id:
                    # Convert camelCase to lowercase
                    filename = re.sub(r'([A-Z])', r'_\1', operation_id).lower().lstrip('_')
                    expected_files.add(filename)
                    
        return expected_files

    def generate_summary(self) -> None:
        """Generate validation summary."""
        endpoints = self.validation_results["endpoints"]
        schemas = self.validation_results["schemas"]
        docs = self.validation_results["documentation"]
        
        self.validation_results["summary"] = {
            "total_endpoints_current": len(self.current_spec.get("paths", {})),
            "total_endpoints_comprehensive": len(self.comprehensive_spec.get("paths", {})),
            "total_schemas_current": len(self.current_spec.get("components", {}).get("schemas", {})),
            "total_schemas_comprehensive": len(self.comprehensive_spec.get("components", {}).get("schemas", {})),
            "endpoints_missing_in_current": len(endpoints["missing_in_current"]),
            "endpoints_missing_in_comprehensive": len(endpoints["missing_in_comprehensive"]),
            "endpoint_method_mismatches": len(endpoints["method_mismatches"]),
            "endpoint_parameter_mismatches": len(endpoints["parameter_mismatches"]),
            "schema_issues": len(schemas["missing_definitions"]) + len(schemas["property_mismatches"]),
            "missing_documentation_files": len(docs["missing_files"])
        }

    def run_validation(self) -> Dict[str, Any]:
        """Run complete validation and return results."""
        print("🔍 Validating API documentation...")
        
        print("  📍 Validating endpoints...")
        self.validate_endpoints()
        
        print("  📋 Validating schemas...")
        self.validate_schemas()
        
        print("  📄 Validating documentation files...")
        self.validate_documentation_files()
        
        print("  📊 Generating summary...")
        self.generate_summary()
        
        return self.validation_results

    def print_validation_report(self) -> None:
        """Print a detailed validation report."""
        results = self.validation_results
        summary = results["summary"]
        
        print("\n" + "="*80)
        print("📋 API DOCUMENTATION VALIDATION REPORT")
        print("="*80)
        
        # Summary
        print(f"\n📊 SUMMARY")
        print(f"Current spec endpoints: {summary['total_endpoints_current']}")
        print(f"Comprehensive docs endpoints: {summary['total_endpoints_comprehensive']}")
        print(f"Current spec schemas: {summary['total_schemas_current']}")
        print(f"Comprehensive docs schemas: {summary['total_schemas_comprehensive']}")
        
        # Endpoint issues
        print(f"\n🔍 ENDPOINT VALIDATION")
        print(f"Missing in current spec: {summary['endpoints_missing_in_current']}")
        print(f"Missing in comprehensive docs: {summary['endpoints_missing_in_comprehensive']}")
        print(f"Method mismatches: {summary['endpoint_method_mismatches']}")
        print(f"Parameter mismatches: {summary['endpoint_parameter_mismatches']}")
        
        # Show specific missing endpoints
        if results["endpoints"]["missing_in_current"]:
            print(f"\n🚨 ENDPOINTS MISSING IN CURRENT SPEC ({len(results['endpoints']['missing_in_current'])}):")
            for endpoint in sorted(results["endpoints"]["missing_in_current"])[:10]:
                print(f"  - {endpoint}")
            if len(results["endpoints"]["missing_in_current"]) > 10:
                print(f"  ... and {len(results['endpoints']['missing_in_current']) - 10} more")
        
        # Show method mismatches
        if results["endpoints"]["method_mismatches"]:
            print(f"\n⚠️  METHOD MISMATCHES ({len(results['endpoints']['method_mismatches'])}):")
            for mismatch in results["endpoints"]["method_mismatches"][:5]:
                print(f"  {mismatch['path']}:")
                if mismatch["missing_in_current"]:
                    print(f"    Missing methods: {', '.join(mismatch['missing_in_current'])}")
                if mismatch["extra_in_current"]:
                    print(f"    Extra methods: {', '.join(mismatch['extra_in_current'])}")
        
        # Schema issues
        print(f"\n📋 SCHEMA VALIDATION")
        print(f"Schema issues found: {summary['schema_issues']}")
        
        if results["schemas"]["property_mismatches"]:
            print(f"\n📝 SCHEMA PROPERTY ISSUES ({len(results['schemas']['property_mismatches'])}):")
            for schema in results["schemas"]["property_mismatches"][:10]:
                print(f"  {schema['schema']}: {', '.join(schema['issues'][:3])}")
        
        # Documentation files
        print(f"\n📄 DOCUMENTATION VALIDATION")
        print(f"Missing documentation files: {summary['missing_documentation_files']}")
        
        print(f"\n✅ Validation complete!")


def main():
    """Main validation function."""
    repo_root = Path(__file__).parent.parent
    validator = APIDocumentationValidator(repo_root)
    
    try:
        validator.run_validation()
        validator.print_validation_report()
        
        # Save detailed results to file
        output_file = repo_root / "validation_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(validator.validation_results, f, indent=2)
        
        print(f"\n💾 Detailed results saved to: {output_file}")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        raise


if __name__ == "__main__":
    main()