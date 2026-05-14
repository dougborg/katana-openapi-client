# List all sales orders

Returns a list of sales orders you’ve previously created.
  The sales orders are returned in a sorted order,
    with the most recent sales orders appearing first.

# OpenAPI definition

```json
{
  "openapi": "3.0.0",
  "info": {
    "title": "RESOURCES",
    "version": "1.0.0",
    "description": "public api"
  },
  "servers": [
    {
      "url": "https://api.katanamrp.com/v1"
    }
  ],
  "security": [
    {
      "bearerAuth": []
    }
  ],
  "components": {
    "securitySchemes": {
      "bearerAuth": {
        "type": "http",
        "scheme": "bearer"
      }
    }
  },
  "paths": {
    "/sales_orders": {
      "get": {
        "summary": "List all sales orders",
        "tags": [
          "Sales order"
        ],
        "description": "Returns a list of sales orders you’ve previously created.\n  The sales orders are returned in a sorted order,\n    with the most recent sales orders appearing first.",
        "operationId": "getAllSalesOrders",
        "parameters": [
          {
            "name": "ids",
            "required": false,
            "description": "Filters sales orders by an array of IDs",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer"
              }
            },
            "in": "query"
          },
          {
            "name": "order_no",
            "required": false,
            "description": "Filters sales orders by an order number",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "source",
            "required": false,
            "description": "Filters sales orders by a creation source",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "location_id",
            "required": false,
            "description": "Filters sales orders by location",
            "schema": {
              "type": "number"
            },
            "in": "query"
          },
          {
            "name": "customer_id",
            "required": false,
            "description": "Filters sales orders by customer",
            "schema": {
              "type": "number"
            },
            "in": "query"
          },
          {
            "name": "status",
            "required": false,
            "description": "Filters sales orders by a status",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "currency",
            "required": false,
            "description": "Filters sales orders by currency",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "invoicing_status",
            "required": false,
            "description": "Filters sales orders by an invoicing status",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "product_availability",
            "required": false,
            "description": "Filters sales orders by product availability",
            "schema": {
              "enum": [
                "IN_STOCK",
                "EXPECTED",
                "PICKED",
                "NOT_AVAILABLE",
                "NOT_APPLICABLE"
              ]
            },
            "in": "query"
          },
          {
            "name": "ingredient_availability",
            "required": false,
            "description": "Filters sales orders by ingredient availability",
            "schema": {
              "enum": [
                "PROCESSED",
                "IN_STOCK",
                "NOT_AVAILABLE",
                "EXPECTED",
                "NO_RECIPE",
                "NOT_APPLICABLE"
              ]
            },
            "in": "query"
          },
          {
            "name": "production_status",
            "required": false,
            "description": "Filters sales orders by production status",
            "schema": {
              "enum": [
                "NOT_STARTED",
                "NONE",
                "NOT_APPLICABLE",
                "IN_PROGRESS",
                "BLOCKED",
                "DONE"
              ]
            },
            "in": "query"
          },
          {
            "name": "ecommerce_order_type",
            "required": false,
            "description": "Filters sales orders by an e-commerce order type",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "ecommerce_store_name",
            "required": false,
            "description": "Filters sales orders by an e-commerce store name",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "ecommerce_order_id",
            "required": false,
            "description": "Filters sales orders by an e-commerce order id",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "include_deleted",
            "required": false,
            "description": "Soft-deleted data is excluded from result set by default. Set to true to include it.",
            "schema": {
              "type": "boolean"
            },
            "in": "query"
          },
          {
            "name": "limit",
            "required": false,
            "description": "Used for pagination (default is 50)",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "page",
            "required": false,
            "description": "Used for pagination (default is 1)",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "created_at_min",
            "required": false,
            "description": "Minimum value for created_at range. Must be compatible with ISO 8601 format",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "created_at_max",
            "required": false,
            "description": "Maximum value for created_at range. Must be compatible with ISO 8601 format",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "updated_at_min",
            "required": false,
            "description": "Minimum value for updated_at range. Must be compatible with ISO 8601 format",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "updated_at_max",
            "required": false,
            "description": "Maximum value for updated_at range. Must be compatible with ISO 8601 format",
            "schema": {
              "type": "string"
            },
            "in": "query"
          }
        ],
        "responses": {
          "200": {
            "description": "List all sales orders",
            "headers": {
              "X-Pagination": {
                "description": "Pagination metadata",
                "schema": {
                  "type": "object",
                  "properties": {
                    "total_records": {
                      "type": "number"
                    },
                    "total_pages": {
                      "type": "number"
                    },
                    "offset": {
                      "type": "number"
                    },
                    "page": {
                      "type": "number"
                    },
                    "first_page": {
                      "type": "boolean"
                    },
                    "last_page": {
                      "type": "boolean"
                    }
                  }
                }
              },
              "X-Ratelimit-Limit": {
                "description": "Number of requests available for this application.",
                "schema": {
                  "type": "number"
                }
              },
              "X-Ratelimit-Remaining": {
                "description": "Number of requests remaining in quota.",
                "schema": {
                  "type": "number"
                }
              },
              "X-Ratelimit-Reset": {
                "description": "The timestamp when the quota will reset.",
                "schema": {
                  "type": "number"
                }
              }
            },
            "content": {
              "application/json": {
                "example": {
                  "data": [
                    {
                      "id": 1,
                      "customer_id": 1,
                      "order_no": "SO-3",
                      "source": "api",
                      "order_created_date": "2020-10-23T10:37:05.085Z",
                      "delivery_date": "2020-10-23T10:37:05.085Z",
                      "picked_date": "2020-10-23T10:37:05.085Z",
                      "location_id": 1,
                      "status": "NOT_SHIPPED",
                      "currency": "USD",
                      "conversion_rate": 2,
                      "total": 150,
                      "total_in_base_currency": 75,
                      "conversion_date": "2020-10-23T10:37:05.085Z",
                      "product_availability": "IN_STOCK",
                      "product_expected_date": "2021-09-10T08:00:00.000Z",
                      "ingredient_availability": "PROCESSED",
                      "ingredient_expected_date": "2021-09-10T08:00:00.000Z",
                      "production_status": "DONE",
                      "invoicing_status": "invoiced",
                      "additional_info": "additional info",
                      "customer_ref": "my customer reference",
                      "ecommerce_order_type": "shopify",
                      "ecommerce_store_name": "katana.myshopify.com",
                      "ecommerce_order_id": "19433769",
                      "created_at": "2020-10-23T10:37:05.085Z",
                      "updated_at": "2020-10-23T10:37:05.085Z",
                      "sales_order_rows": [
                        {
                          "sales_order_id": 1,
                          "id": 1,
                          "quantity": 2,
                          "variant_id": 1,
                          "tax_rate_id": 1,
                          "location_id": 1,
                          "price_per_unit": 75,
                          "total_discount": "10.00",
                          "price_per_unit_in_base_currency": 37.5,
                          "total": 150,
                          "total_in_base_currency": 75,
                          "conversion_rate": 2,
                          "conversion_date": "2020-10-23T10:37:05.085Z",
                          "product_availability": "IN_STOCK",
                          "product_expected_date": "2021-09-10T08:00:00.000Z",
                          "created_at": "2020-10-23T10:37:05.085Z",
                          "updated_at": "2020-10-23T10:37:05.085Z",
                          "linked_manufacturing_order_id": 1,
                          "attributes": [
                            {
                              "key": "key",
                              "value": "value"
                            }
                          ],
                          "batch_transactions": [
                            {
                              "batch_id": 1,
                              "quantity": 10
                            }
                          ],
                          "serial_numbers": [
                            1
                          ]
                        }
                      ],
                      "tracking_number": "12345678",
                      "tracking_number_url": "https://tracking-number-url",
                      "custom_fields": {
                        "37460d24-ea57-416d-888e-bea7c0505642": "PO-1234",
                        "6afe78d2-2b95-4d71-92f5-1bc2be852afe": 5
                      },
                      "billing_address_id": 1234,
                      "shipping_address_id": 1235,
                      "addresses": [
                        {
                          "id": 1234,
                          "sales_order_id": 12345,
                          "entity_type": "billing",
                          "first_name": "Luke",
                          "last_name": "Skywalker",
                          "company": "Company",
                          "phone": "123456",
                          "line_1": "Line 1",
                          "line_2": "Line 2",
                          "city": "City",
                          "state": "State",
                          "zip": "Zip",
                          "country": "Country",
                          "updated_at": "2020-10-23T10:37:05.085Z",
                          "created_at": "2020-10-23T10:37:05.085Z"
                        },
                        {
                          "id": 1235,
                          "sales_order_id": 12345,
                          "entity_type": "shipping",
                          "first_name": "Luke",
                          "last_name": "Skywalker",
                          "company": "Company",
                          "phone": "123456",
                          "line_1": "Line 1",
                          "line_2": "Line 2",
                          "city": "City",
                          "state": "State",
                          "zip": "Zip",
                          "country": "Country",
                          "updated_at": "2020-10-23T10:37:05.085Z",
                          "created_at": "2020-10-23T10:37:05.085Z"
                        }
                      ],
                      "shipping_fee": {
                        "id": 1,
                        "sales_order_id": 1,
                        "description": "",
                        "amount": "1.0000000000",
                        "tax_rate_id": 16582
                      }
                    }
                  ]
                }
              }
            }
          },
          "401": {
            "description": "Make sure you've entered your API token correctly.",
            "headers": {
              "X-Ratelimit-Limit": {
                "description": "Number of requests available for this application.",
                "schema": {
                  "type": "number"
                }
              },
              "X-Ratelimit-Remaining": {
                "description": "Number of requests remaining in quota.",
                "schema": {
                  "type": "number"
                }
              },
              "X-Ratelimit-Reset": {
                "description": "The timestamp when the quota will reset.",
                "schema": {
                  "type": "number"
                }
              }
            },
            "content": {
              "application/json": {
                "example": {
                  "statusCode": 401,
                  "name": "UnauthorizedError",
                  "message": "Unauthorized"
                }
              }
            }
          },
          "429": {
            "description": "The rate limit has been reached. Please try again later.",
            "headers": {
              "X-Ratelimit-Limit": {
                "description": "Number of requests available for this application.",
                "schema": {
                  "type": "number"
                }
              },
              "X-Ratelimit-Remaining": {
                "description": "Number of requests remaining in quota.",
                "schema": {
                  "type": "number"
                }
              },
              "X-Ratelimit-Reset": {
                "description": "The timestamp when the quota will reset.",
                "schema": {
                  "type": "number"
                }
              }
            },
            "content": {
              "application/json": {
                "example": {
                  "statusCode": 429,
                  "name": "TooManyRequests",
                  "message": "Too Many Requests"
                }
              }
            }
          },
          "500": {
            "description": "The server encountered an error. If this persists, please contact support",
            "headers": {
              "X-Ratelimit-Limit": {
                "description": "Number of requests available for this application.",
                "schema": {
                  "type": "number"
                }
              },
              "X-Ratelimit-Remaining": {
                "description": "Number of requests remaining in quota.",
                "schema": {
                  "type": "number"
                }
              },
              "X-Ratelimit-Reset": {
                "description": "The timestamp when the quota will reset.",
                "schema": {
                  "type": "number"
                }
              }
            },
            "content": {
              "application/json": {
                "example": {
                  "statusCode": 500,
                  "name": "InternalServerError",
                  "message": "Internal Server Error"
                }
              }
            }
          }
        }
      }
    }
  },
  "x-explorer-enabled": false,
  "x-samples-enabled": true,
  "x-samples-languages": [
    "curl",
    "node",
    "go",
    "ruby",
    "python",
    "php"
  ],
  "x-headers": [
    {
      "key": "Authorization",
      "value": "Bearer <Your api key>"
    }
  ]
}
```