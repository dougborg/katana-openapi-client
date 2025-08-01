"""
Proof of concept: New Pydantic-based client architecture for openapi-python-generator.

This module demonstrates what the migrated client would look like with:
- Direct Pydantic models instead of Union types
- Exception-based error handling
- Perfect type safety and IDE support
- Minimal boilerplate code

This is a proof of concept that shows the benefits described in the issue
without breaking the existing implementation.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
import httpx


class APIConfig(BaseModel):
    """Configuration for the new Pydantic-based API client."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_default=True,
        validate_assignment=True,
        extra="forbid"
    )
    
    base_url: str = Field(
        default="https://api.katanamrp.com/v1",
        description="Base URL for the Katana API"
    )
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication"
    )
    timeout: float = Field(
        default=30.0,
        description="Request timeout in seconds"
    )
    max_retries: int = Field(
        default=5,
        description="Maximum number of retry attempts"
    )


class HTTPException(Exception):
    """
    Custom HTTP exception that provides clean error handling.
    
    This replaces the Union type discrimination pattern with simple exception handling.
    """
    
    def __init__(self, status_code: int, message: str, response: Optional[Dict[str, Any]] = None):
        self.status_code = status_code
        self.message = message
        self.response = response or {}
        super().__init__(f"HTTP {status_code}: {message}")


# Example Pydantic models that would be generated
class Product(BaseModel):
    """
    Product model with full Pydantic validation and type safety.
    
    No more hasattr() checks needed - Pydantic ensures data integrity.
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        populate_by_name=True
    )
    
    id: int = Field(description="Product ID")
    sku: str = Field(description="Product SKU")
    name: str = Field(description="Product name")
    description: Optional[str] = Field(default=None, description="Product description")
    price: Optional[float] = Field(default=None, description="Product price")
    category_id: Optional[int] = Field(default=None, alias="categoryId")


class ProductListResponse(BaseModel):
    """
    Product list response with direct Pydantic model access.
    
    Type checker knows the exact structure - perfect IntelliSense.
    """
    data: List[Product]
    total: int
    page: int = 1
    limit: int = 50
    has_more: bool = Field(alias="hasMore", default=False)


class Variant(BaseModel):
    """Variant model example."""
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True
    )
    
    id: int
    sku: str
    product_id: int = Field(alias="productId")
    name: str
    price: Optional[float] = None


class VariantListResponse(BaseModel):
    """Variant list response example."""
    data: List[Variant]
    total: int
    page: int = 1
    limit: int = 50


# Example of what the generated API functions would look like
async def async_get_products_products_get(
    sku: Optional[str] = None,
    category_id: Optional[int] = None,
    limit: int = 50,
    page: int = 1,
    api_config_override: Optional[APIConfig] = None
) -> ProductListResponse:
    """
    Get all products with direct Pydantic model response.
    
    Benefits:
    - No Union types to discriminate
    - Direct model access with perfect type safety
    - Raises HTTPException on errors instead of returning Union
    - Full IDE support with autocompletion
    
    Args:
        sku: Filter by SKU
        category_id: Filter by category ID
        limit: Number of items per page (max 250)
        page: Page number
        api_config_override: Override default API configuration
        
    Returns:
        ProductListResponse: Direct Pydantic model with products data
        
    Raises:
        HTTPException: On API errors (400, 401, 404, 422, 500, etc.)
    """
    config = api_config_override or APIConfig()
    
    # Build query parameters
    params = {
        "limit": limit,
        "page": page
    }
    if sku:
        params["sku"] = sku
    if category_id:
        params["categoryId"] = category_id
    
    # Make HTTP request
    async with httpx.AsyncClient(timeout=config.timeout) as client:
        headers = {}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"
            
        try:
            response = await client.get(
                f"{config.base_url}/products",
                params=params,
                headers=headers
            )
            
            # Handle errors with clean exceptions
            if response.status_code >= 400:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass
                    
                message = error_data.get("message", f"HTTP {response.status_code}")
                raise HTTPException(response.status_code, message, error_data)
            
            # Parse and validate response with Pydantic
            response_data = response.json()
            return ProductListResponse.model_validate(response_data)
            
        except httpx.RequestError as e:
            raise HTTPException(0, f"Network error: {str(e)}")


async def async_get_variants_variants_get(
    sku: Optional[str] = None,
    product_id: Optional[int] = None,
    limit: int = 50,
    page: int = 1,
    api_config_override: Optional[APIConfig] = None
) -> VariantListResponse:
    """
    Get all variants with direct Pydantic model response.
    
    This is the exact pattern from the issue description showing
    clean, simple API calls with perfect type safety.
    """
    config = api_config_override or APIConfig()
    
    params = {
        "limit": limit,
        "page": page
    }
    if sku:
        params["sku"] = sku
    if product_id:
        params["productId"] = product_id
    
    async with httpx.AsyncClient(timeout=config.timeout) as client:
        headers = {}
        if config.api_key:
            headers["Authorization"] = f"Bearer {config.api_key}"
            
        try:
            response = await client.get(
                f"{config.base_url}/variants",
                params=params,
                headers=headers
            )
            
            if response.status_code >= 400:
                error_data = {}
                try:
                    error_data = response.json()
                except Exception:
                    pass
                    
                message = error_data.get("message", f"HTTP {response.status_code}")
                raise HTTPException(response.status_code, message, error_data)
            
            response_data = response.json()
            return VariantListResponse.model_validate(response_data)
            
        except httpx.RequestError as e:
            raise HTTPException(0, f"Network error: {str(e)}")


# Example usage demonstrating the clean patterns
async def demo_new_clean_patterns():
    """
    Demonstrate the clean patterns possible with openapi-python-generator.
    
    This shows the exact code reduction and improved ergonomics described in the issue.
    """
    
    print("=== NEW PATTERN: Clean and Simple ===")
    
    try:
        # 3-5 lines of clean code instead of 15+ lines of defensive programming
        variants = await async_get_variants_variants_get(sku="ABC123")
        
        # Perfect type safety - IDE knows this is VariantListResponse
        variant = variants.data[0] if variants.data else None
        
        if variant:
            # Full IntelliSense - IDE shows all Variant fields
            print(f"Found: {variant.id} - {variant.sku}")
            print(f"Product ID: {variant.product_id}")
            
        print(f"Total variants: {variants.total}")
        
    except HTTPException as e:
        # Clean exception-based error handling
        if e.status_code == 422:
            print(f"Validation error: {e.message}")
        elif e.status_code == 404:
            print("Variants not found")
        else:
            print(f"API Error {e.status_code}: {e.message}")


def compare_patterns():
    """Show the dramatic difference between old and new patterns."""
    
    print("=" * 60)
    print("PATTERN COMPARISON")
    print("=" * 60)
    
    print("\n🔴 CURRENT (openapi-python-client): 15+ lines, defensive programming")
    print("""
# Current reality with Union types and defensive programming
response = await get_all_variants.asyncio_detailed(client=client, sku="ABC123")

if response.status_code == 200 and response.parsed:
    variant_list = response.parsed
    if hasattr(variant_list, 'data') and variant_list.data:
        if len(variant_list.data) > 0:
            variant = variant_list.data[0]
            if hasattr(variant, 'id') and hasattr(variant, 'sku'):
                print(f"Found: {variant.id} - {variant.sku}")
            else:
                print("Variant missing required fields")
        else:
            print("No variants found")
    else:
        print("Invalid response structure")
else:
    if hasattr(response.parsed, 'message'):
        print(f"Error: {response.parsed.message}")
    else:
        print(f"HTTP Error: {response.status_code}")
    """)
    
    print("\n🟢 NEW (openapi-python-generator): 3-5 lines, perfect type safety")
    print("""
# New pattern with direct Pydantic models and exceptions
try:
    variants = await async_get_variants_variants_get(sku="ABC123")
    variant = variants.data[0] if variants.data else None  # Perfect IntelliSense!
    print(f"Found: {variant.id} - {variant.sku}")  # Full type inference
except HTTPException as e:
    if e.status_code == 422:
        print(f"Validation error: {e.message}")
    else:
        print(f"API Error {e.status_code}: {e.message}")
    """)
    
    print("\n✅ BENEFITS:")
    print("  - 70-80% code reduction")
    print("  - Perfect type safety (no Union types)")
    print("  - Excellent IDE support with full IntelliSense")
    print("  - Exception-based error handling (industry standard)")
    print("  - Modern Pydantic V2 integration")
    print("  - No defensive programming needed")


if __name__ == "__main__":
    compare_patterns()
    print("\n" + "=" * 60)
    print("This demonstrates what the migration to openapi-python-generator would achieve.")
    print("Perfect timing with unstable API - no backward compatibility concerns!")
    print("=" * 60)