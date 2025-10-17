"""Examples of using utility functions to unwrap and handle API responses.

This module demonstrates the various utility functions available for working
with Katana API responses in a clean, pythonic way.
"""

import asyncio

from katana_public_api_client import (
    APIError,
    AuthenticationError,
    KatanaClient,
    RateLimitError,
    ValidationError,
    get_error_message,
    handle_response,
    is_error,
    is_success,
    unwrap,
    unwrap_data,
)
from katana_public_api_client.api.product import get_all_products, get_product
from katana_public_api_client.api.webhook import get_all_webhooks


async def example_unwrap_basic():
    """Basic example: unwrap a response to get parsed data."""
    async with KatanaClient() as client:
        response = await get_all_products.asyncio_detailed(client=client, limit=10)

        # unwrap_data extracts the list and raises exceptions on errors
        products = unwrap_data(response)
        print(f"Got {len(products)} products")


async def example_unwrap_data():
    """Extract data directly from list responses."""
    async with KatanaClient() as client:
        response = await get_all_webhooks.asyncio_detailed(client=client)

        # unwrap_data extracts the .data field directly
        webhooks = unwrap_data(response)
        for webhook in webhooks:
            print(f"Webhook: {webhook.id} - {webhook.url}")


async def example_error_handling():
    """Demonstrate error handling with unwrap."""
    async with KatanaClient() as client:
        try:
            # This will raise AuthenticationError if API key is invalid
            response = await get_all_products.asyncio_detailed(client=client)
            products = unwrap_data(response)
            print(f"Success! Got {len(products)} products")

        except AuthenticationError as e:
            print(f"Authentication failed: {e}")
            print(f"Status code: {e.status_code}")

        except ValidationError as e:
            print(f"Validation error: {e}")
            print(f"Validation details: {e.validation_errors}")

        except RateLimitError as e:
            print(f"Rate limited: {e}")
            # Could implement backoff and retry here

        except APIError as e:
            print(f"API error: {e}")
            print(f"Status: {e.status_code}")


async def example_graceful_error_handling():
    """Handle errors gracefully without exceptions."""
    async with KatanaClient() as client:
        response = await get_all_products.asyncio_detailed(client=client)

        # Use raise_on_error=False to get None instead of raising
        products = unwrap_data(response, raise_on_error=False)

        if products is None:
            print("Request failed, but didn't raise exception")
            error_msg = get_error_message(response)
            print(f"Error: {error_msg}")
        else:
            print(f"Success! Got {len(products)} products")


async def example_checking_status():
    """Check response status before processing."""
    async with KatanaClient() as client:
        response = await get_all_products.asyncio_detailed(client=client)

        if is_success(response):
            products = unwrap_data(response)
            print(f"✓ Successfully retrieved {len(products)} products")

        elif is_error(response):
            error_msg = get_error_message(response)
            print(f"✗ Error: {error_msg}")


async def example_with_default_value():
    """Use default values when data is not available."""
    async with KatanaClient() as client:
        response = await get_all_products.asyncio_detailed(client=client)

        # Provide a default value to return on error or empty data
        products = unwrap_data(
            response,
            raise_on_error=False,
            default=[],  # Return empty list on error
        )

        print(f"Products: {len(products)} (might be 0 on error)")


async def example_custom_handlers():
    """Use custom success and error handlers."""
    async with KatanaClient() as client:
        response = await get_all_products.asyncio_detailed(client=client)

        def on_success(product_list):
            """Handle successful response."""
            print(f"✓ Retrieved {len(product_list.data)} products")
            return [p for p in product_list.data if p.is_sellable]

        def on_error(error: APIError):
            """Handle error response."""
            print(f"✗ Request failed: {error}")
            return []  # Return empty list on error

        # handle_response calls the appropriate callback
        sellable_products = handle_response(
            response, on_success=on_success, on_error=on_error
        )

        print(f"Found {len(sellable_products)} sellable products")


async def example_batch_processing():
    """Process multiple items with error handling."""
    async with KatanaClient() as client:
        product_ids = [1, 2, 3, 999999, 4, 5]  # 999999 might not exist

        results = []
        errors = []

        for product_id in product_ids:
            try:
                response = await get_product.asyncio_detailed(
                    client=client, id=product_id
                )
                product = unwrap(response)
                results.append(product)
            except APIError as e:
                print(f"Failed to get product {product_id}: {e}")
                errors.append((product_id, e))

        print(f"Successfully retrieved {len(results)} products")
        print(f"Failed to retrieve {len(errors)} products")


async def example_nested_error_format():
    """Handle nested error response format."""
    async with KatanaClient() as client:
        response = await get_all_products.asyncio_detailed(client=client, limit=-1)

        # The utils automatically extract error from nested format
        # like: {"error": {"statusCode": 400, "message": "Invalid limit"}}
        try:
            # Use unwrap_data to get the list directly
            products = unwrap_data(response)
            print(f"Got {len(products)} products")
        except ValidationError as e:
            print(f"Validation failed: {e}")
            # Error message is automatically extracted from nested format


async def main():
    """Run all examples."""
    print("=" * 60)
    print("Katana API Client - Utility Functions Examples")
    print("=" * 60)

    examples = [
        ("Basic unwrap", example_unwrap_basic),
        ("Unwrap data directly", example_unwrap_data),
        ("Error handling", example_error_handling),
        ("Graceful error handling", example_graceful_error_handling),
        ("Status checking", example_checking_status),
        ("Default values", example_with_default_value),
        ("Custom handlers", example_custom_handlers),
        ("Batch processing", example_batch_processing),
        ("Nested error format", example_nested_error_format),
    ]

    for name, example_func in examples:
        print(f"\n{name}:")
        print("-" * 60)
        try:
            await example_func()
        except Exception as e:
            print(f"Example failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
