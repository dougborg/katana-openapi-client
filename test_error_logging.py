#!/usr/bin/env python3
"""
Quick test script to demonstrate enhanced error logging for 422 validation errors.
"""

import asyncio
import json
import logging
import sys
from unittest.mock import MagicMock

import httpx

from katana_public_api_client.katana_client import ResilientAsyncTransport


async def test_422_error_logging():
    """Test that our enhanced error logging works for 422 validation errors."""

    # Set up logging to see our error messages - output to console
    logger = logging.getLogger("katana_public_api_client.katana_client")
    logger.setLevel(logging.ERROR)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create a mock 422 response with validation errors
    mock_response_data = {
        "statusCode": 422,
        "name": "UnprocessableEntityError",
        "message": "Sales order validation failed",
        "code": "VALIDATION_ERROR",
        "details": [
            {
                "path": "products.0.availability",
                "code": "invalid_choice",
                "message": "Value must be one of: in_stock, out_of_stock, on_order, discontinued",
                "info": {
                    "provided_value": None,
                    "allowed_values": [
                        "in_stock",
                        "out_of_stock",
                        "on_order",
                        "discontinued",
                    ],
                },
            },
            {
                "path": "customer_id",
                "code": "required",
                "message": "This field is required",
            },
        ],
    }

    # Create mock request and response
    mock_request = httpx.Request("POST", "https://api.katanamrp.com/v1/sales-orders")
    mock_response = MagicMock()
    mock_response.status_code = 422
    mock_response.json.return_value = mock_response_data
    mock_response.text = json.dumps(mock_response_data)

    # Create transport and test error logging
    transport = ResilientAsyncTransport(logger=logger)

    print("=== Testing Enhanced Error Logging ===")
    print("\nTriggering 422 validation error logging:")
    print("-" * 50)

    # This should log our enhanced 422 error details
    await transport._log_client_error(mock_response, mock_request)

    print("-" * 50)
    print("\nAlso testing general 400 error:")
    print("-" * 50)

    # Test a general 400 error
    mock_400_data = {
        "statusCode": 400,
        "name": "BadRequestError",
        "message": "Invalid request parameters",
        "code": "BAD_REQUEST",
        "details": {"invalid_param": "page must be a positive integer"},
    }

    mock_response.status_code = 400
    mock_response.json.return_value = mock_400_data

    await transport._log_client_error(mock_response, mock_request)

    print("-" * 50)
    print("\n✅ Error logging test complete!")


if __name__ == "__main__":
    asyncio.run(test_422_error_logging())
