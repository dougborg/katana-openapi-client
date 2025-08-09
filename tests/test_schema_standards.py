"""
Schema Standards Tests

This module validates OpenAPI schema quality standards including:
- BaseEntity inheritance patterns
- Schema descriptions
- Property descriptions 
- Example structure (schema-level vs property-level)
- Endpoint schema examples
"""

import pytest
import yaml
from pathlib import Path
from typing import Dict, Any, List, Set


@pytest.fixture(scope="session")
def openapi_spec() -> Dict[str, Any]:
    """Load the OpenAPI specification once for all tests."""
    spec_path = Path(__file__).parent.parent / "katana-openapi.yaml"
    with open(spec_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def schemas(openapi_spec: Dict[str, Any]) -> Dict[str, Any]:
    """Extract schemas from OpenAPI spec."""
    return openapi_spec.get("components", {}).get("schemas", {})


@pytest.fixture(scope="session")
def endpoint_schemas(openapi_spec: Dict[str, Any]) -> Set[str]:
    """Find all schemas referenced in API endpoints."""
    referenced_schemas = set()
    
    def find_schema_refs(obj: Any) -> None:
        """Recursively find $ref schema references."""
        if isinstance(obj, dict):
            if "$ref" in obj:
                ref = obj["$ref"]
                if ref.startswith("#/components/schemas/"):
                    schema_name = ref.replace("#/components/schemas/", "")
                    referenced_schemas.add(schema_name)
            else:
                for value in obj.values():
                    find_schema_refs(value)
        elif isinstance(obj, list):
            for item in obj:
                find_schema_refs(item)
    
    # Search through all paths/endpoints
    paths = openapi_spec.get("paths", {})
    find_schema_refs(paths)
    
    return referenced_schemas


class TestBaseEntityInheritance:
    """Test BaseEntity inheritance patterns."""
    
    def test_base_entity_exists(self, schemas: Dict[str, Any]):
        """BaseEntity schema must exist."""
        assert "BaseEntity" in schemas
        
    def test_base_entity_has_id_property(self, schemas: Dict[str, Any]):
        """BaseEntity must have id property."""
        base_entity = schemas["BaseEntity"]
        assert "properties" in base_entity
        assert "id" in base_entity["properties"]
        
    def test_entities_inherit_from_base_entity(self, schemas: Dict[str, Any]):
        """Key business entities should inherit from BaseEntity."""
        # Focus on the most important core entities
        entity_candidates = [
            "AdditionalCost", "Batch", "StorageBin", "Variant", "Location", 
            "Customer", "SalesOrder", "Material", "Product"
        ]
        
        for schema_name in entity_candidates:
            if schema_name in schemas:
                schema = schemas[schema_name]
                
                # Check if it uses allOf with BaseEntity reference
                if "allOf" in schema:
                    base_refs = [
                        item.get("$ref", "") 
                        for item in schema["allOf"] 
                        if isinstance(item, dict) and "$ref" in item
                    ]
                    base_entity_ref = "#/components/schemas/BaseEntity"
                    assert base_entity_ref in base_refs, f"{schema_name} should inherit from BaseEntity"


class TestSchemaDescriptions:
    """Test schema description requirements."""
    
    @pytest.mark.parametrize("schema_name", [
        "Batch", "StorageBin", "Location", "Customer", "SalesOrder",
        "CreateMaterialRequest", "UpdateMaterialRequest",
        "CreateProductRequest", "UpdateProductRequest", 
        "CreatePurchaseOrderRequest", "UpdatePurchaseOrderRequest"
    ])
    def test_schema_has_description(self, schemas: Dict[str, Any], schema_name: str):
        """Schema must have a meaningful description."""
        if schema_name not in schemas:
            pytest.skip(f"Schema {schema_name} not found")
            
        schema = schemas[schema_name]
        assert "description" in schema, f"Schema {schema_name} missing description"
        
        description = schema["description"]
        assert description and description.strip(), f"Schema {schema_name} has empty description"
        assert len(description.strip()) > 10, f"Schema {schema_name} description too short"


class TestPropertyDescriptions:
    """Test property description requirements."""
    
    @pytest.mark.parametrize("schema_name", [
        "CreateMaterialRequest", "UpdateMaterialRequest",
        "CreateProductRequest", "UpdateProductRequest",
        "CreatePurchaseOrderRequest", "PurchaseOrderRowRequest",
        "CreateSupplierRequest", "UpdateSupplierRequest",
        "CreateVariantRequest", "UpdateVariantRequest"
    ])
    def test_significant_properties_have_descriptions(self, schemas: Dict[str, Any], schema_name: str):
        """Significant properties must have descriptions."""
        if schema_name not in schemas:
            pytest.skip(f"Schema {schema_name} not found")
            
        schema = schemas[schema_name]
        
        # Skip inherited properties from BaseEntity/UpdatableEntity/etc
        skip_properties = {"id", "created_at", "updated_at", "deleted_at", "archived_at"}
        
        # Focus on key business properties that must have descriptions
        key_properties = {
            "name", "sku", "order_no", "quantity", "price_per_unit", 
            "email", "phone", "currency", "sales_price", "purchase_price"
        }
        
        properties = self._get_all_properties(schema, schemas)
        
        for prop_name, prop_def in properties.items():
            if prop_name in skip_properties:
                continue
                
            # Only check key business properties
            if prop_name in key_properties and isinstance(prop_def, dict) and "type" in prop_def:
                assert "description" in prop_def, f"Key property {prop_name} in {schema_name} missing description"
                
    def _get_all_properties(self, schema: Dict[str, Any], all_schemas: Dict[str, Any]) -> Dict[str, Any]:
        """Get all properties including inherited ones."""
        properties = {}
        
        # Handle allOf inheritance
        if "allOf" in schema:
            for item in schema["allOf"]:
                if "$ref" in item:
                    ref_name = item["$ref"].replace("#/components/schemas/", "")
                    if ref_name in all_schemas:
                        inherited_props = self._get_all_properties(all_schemas[ref_name], all_schemas)
                        properties.update(inherited_props)
                elif "properties" in item:
                    properties.update(item["properties"])
                    
        # Direct properties
        if "properties" in schema:
            properties.update(schema["properties"])
            
        return properties


class TestExampleStructure:
    """Test example structure requirements."""
    
    @pytest.mark.parametrize("schema_name", [
        "Batch", "BatchStock", "StorageBin", "InventoryMovement",
        "Location", "Inventory", "SerialNumber", "NegativeStock",
        "VariantDefaultStorageBinLink", "ServiceInputAttributes",
        "StockAdjustment", "StockTransfer", "Factory", "Stocktake", "StocktakeRow"
    ])
    def test_no_property_level_examples(self, schemas: Dict[str, Any], schema_name: str):
        """Schemas should use schema-level examples, not property-level examples."""
        if schema_name not in schemas:
            pytest.skip(f"Schema {schema_name} not found")
            
        schema = schemas[schema_name]
        
        # Check that properties don't have examples
        properties = self._get_all_properties(schema, schemas)
        
        for prop_name, prop_def in properties.items():
            if isinstance(prop_def, dict):
                assert "example" not in prop_def, f"Property {prop_name} in {schema_name} has property-level example (should be schema-level)"
                
    def test_schema_level_examples_exist(self, schemas: Dict[str, Any]):
        """Key schemas should have schema-level examples instead of property-level examples."""
        # Focus on schemas that specifically need examples based on business importance
        schemas_needing_examples = [
            "Batch", "InventoryMovement", "ServiceInputAttributes"
        ]
        
        for schema_name in schemas_needing_examples:
            if schema_name in schemas:
                schema = schemas[schema_name]
                assert "example" in schema, f"Schema {schema_name} should have schema-level example"
                
    def _get_all_properties(self, schema: Dict[str, Any], all_schemas: Dict[str, Any]) -> Dict[str, Any]:
        """Get all properties including inherited ones."""
        properties = {}
        
        # Handle allOf inheritance
        if "allOf" in schema:
            for item in schema["allOf"]:
                if "$ref" in item:
                    ref_name = item["$ref"].replace("#/components/schemas/", "")
                    if ref_name in all_schemas:
                        inherited_props = self._get_all_properties(all_schemas[ref_name], all_schemas)
                        properties.update(inherited_props)
                elif "properties" in item:
                    properties.update(item["properties"])
                    
        # Direct properties  
        if "properties" in schema:
            properties.update(schema["properties"])
            
        return properties


class TestEndpointSchemaExamples:
    """Test schemas used in endpoints have proper examples."""
    
    def test_endpoint_schemas_have_examples(self, schemas: Dict[str, Any], endpoint_schemas: Set[str]):
        """Most important endpoint schemas must have examples."""
        # Focus on core business entities that are frequently used in endpoints
        important_endpoint_schemas = [
            "Batch", "Variant"
        ]
        
        for schema_name in important_endpoint_schemas:
            if schema_name in schemas and schema_name in endpoint_schemas:
                schema = schemas[schema_name]
                assert "example" in schema, f"Endpoint schema {schema_name} should have example"


class TestSchemaQualityMetrics:
    """Overall schema quality metrics."""
    
    def test_schema_coverage_report(self, schemas: Dict[str, Any], endpoint_schemas: Set[str]):
        """Generate coverage report for debugging."""
        total_schemas = len(schemas)
        schemas_with_descriptions = sum(1 for s in schemas.values() if s.get("description"))
        schemas_with_examples = sum(1 for s in schemas.values() if "example" in s)
        
        endpoint_schemas_with_examples = sum(
            1 for name in endpoint_schemas 
            if name in schemas and "example" in schemas[name]
        )
        
        print(f"\nSchema Quality Metrics:")
        print(f"Total schemas: {total_schemas}")
        print(f"Schemas with descriptions: {schemas_with_descriptions}/{total_schemas}")
        print(f"Schemas with examples: {schemas_with_examples}/{total_schemas}")
        print(f"Endpoint schemas: {len(endpoint_schemas)}")
        print(f"Endpoint schemas with examples: {endpoint_schemas_with_examples}/{len(endpoint_schemas)}")
        
        # This test always passes but provides useful info
        assert True