"""
Example demonstrating OpenTracing integration with the Katana OpenAPI client.

This example shows how to use OpenTracing with the Katana client to automatically
trace all API requests.
"""

import asyncio
import logging
from katana_public_api_client import KatanaClient

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_jaeger_tracer():
    """Set up a Jaeger tracer for distributed tracing."""
    try:
        from jaeger_client import Config

        config = Config(
            config={
                "sampler": {
                    "type": "const",
                    "param": 1,
                },
                "logging": True,
                "reporter_batch_size": 1,
            },
            service_name="katana-client-example",
            validate=True,
        )

        tracer = config.initialize_tracer()
        logger.info("Jaeger tracer initialized successfully")
        return tracer
    except ImportError:
        logger.warning(
            "Jaeger client not available. Install with: pip install 'katana-openapi-client[tracing]'"
        )
        return None


async def example_without_tracing():
    """Example of using the client without OpenTracing."""
    logger.info("=== Example without OpenTracing ===")

    # Create client without tracer (normal usage)
    async with KatanaClient(
        api_key="test-api-key", base_url="https://api.example.com/v1"
    ) as client:
        logger.info("Client created without tracing")

        # Simulate making an API call
        # In a real scenario, you would call actual API methods like:
        # from katana_public_api_client.generated.api.product import get_all_products
        # response = await get_all_products.asyncio_detailed(client=client)

        logger.info("API calls would work normally without any tracing overhead")


async def example_with_tracing():
    """Example of using the client with OpenTracing."""
    logger.info("=== Example with OpenTracing ===")

    # Set up a tracer
    tracer = setup_jaeger_tracer()

    if tracer is None:
        logger.warning("Skipping tracing example - tracer not available")
        return

    # Create client with tracer
    async with KatanaClient(
        tracer=tracer, api_key="test-api-key", base_url="https://api.example.com/v1"
    ) as client:
        logger.info("Client created with OpenTracing enabled")

        # All API calls will now be automatically traced
        # The tracer will create spans for each HTTP request
        # with tags like:
        # - component: "katana-openapi-client"
        # - http.method: "GET"
        # - http.url: "https://api.example.com/v1/products"
        # - http.status_code: 200
        # - span.kind: "client"

        # In a real scenario, you would call API methods like:
        # from katana_public_api_client.generated.api.product import get_all_products
        # response = await get_all_products.asyncio_detailed(client=client)

        logger.info("API calls would be automatically traced with detailed spans")


async def example_with_custom_spans():
    """Example of using the client with custom spans."""
    logger.info("=== Example with custom spans ===")

    tracer = setup_jaeger_tracer()

    if tracer is None:
        logger.warning("Skipping custom spans example - tracer not available")
        return

    # Create a parent span for the entire operation
    with tracer.start_span("business_operation") as parent_span:
        parent_span.set_tag("business.operation", "fetch_product_data")

        # Create client with tracer
        async with KatanaClient(
            tracer=tracer, api_key="test-api-key", base_url="https://api.example.com/v1"
        ) as client:
            # The client will automatically create child spans
            # for each API request under the parent span
            logger.info("Client API calls will be traced as child spans")

            # In a real scenario:
            # response = await get_all_products.asyncio_detailed(client=client)
            # The above call would create a span like:
            # - operation_name: "katana_client.GET"
            # - parent: "business_operation"
            # - tags: http.method=GET, http.url=..., etc.


async def example_error_tracing():
    """Example of error tracing."""
    logger.info("=== Example with error tracing ===")

    tracer = setup_jaeger_tracer()

    if tracer is None:
        logger.warning("Skipping error tracing example - tracer not available")
        return

    async with KatanaClient(
        tracer=tracer, api_key="test-api-key", base_url="https://api.example.com/v1"
    ) as client:
        # If an API call fails, the span will be tagged with error information:
        # - error: true
        # - logs containing the error message

        logger.info("Errors in API calls will be automatically traced")

        # For HTTP errors (4xx, 5xx), the span will include:
        # - http.status_code: 500
        # - error: true

        # For network errors, the span will include:
        # - error: true
        # - logs: {"error": "Connection failed"}


async def main():
    """Run all examples."""
    try:
        await example_without_tracing()
        await example_with_tracing()
        await example_with_custom_spans()
        await example_error_tracing()

        logger.info("All examples completed successfully!")

    except Exception as e:
        logger.error(f"Error running examples: {e}")


if __name__ == "__main__":
    asyncio.run(main())
