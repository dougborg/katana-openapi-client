> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# List all sales order rows

Returns a list of sales order rows you’ve previously created.
  The sales order rows are returned in a sorted order,
    with the most recent sales order rows appearing first.

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
    "/sales_order_rows": {
      "get": {
        "summary": "List all sales order rows",
        "tags": [
          "Sales order row"
        ],
        "description": "Returns a list of sales order rows you’ve previously created.\n  The sales order rows are returned in a sorted order,\n    with the most recent sales order rows appearing first.",
        "operationId": "getAllSalesOrderRows",
        "parameters": [
          {
            "name": "ids",
            "required": false,
            "description": "Filters sales order rows by an array of IDs",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer"
              }
            },
            "in": "query"
          },
          {
            "name": "sales_order_ids",
            "required": false,
            "description": "Filters sales order rows by an array of sales order ids",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer"
              }
            },
            "in": "query"
          },
          {
            "name": "variant_id",
            "required": false,
            "description": "Filters sales order rows by variant id.",
            "schema": {
              "type": "integer"
            },
            "in": "query"
          },
          {
            "name": "location_id",
            "required": false,
            "description": "Filters sales order rows by location",
            "schema": {
              "type": "integer"
            },
            "in": "query"
          },
          {
            "name": "tax_rate_id",
            "required": false,
            "description": "Filters sales order rows by tax rate id.",
            "schema": {
              "type": "integer"
            },
            "in": "query"
          },
          {
            "name": "linked_manufacturing_order_id",
            "required": false,
            "description": "Filters sales order rows manufacturing order id.",
            "schema": {
              "type": "integer"
            },
            "in": "query"
          },
          {
            "name": "product_availability",
            "required": false,
            "description": "Filters sales order rows by product availability",
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
            "name": "extend",
            "required": false,
            "description": "Array of objects that need to be added to the response",
            "schema": {
              "type": "array",
              "items": {
                "type": "string",
                "enum": [
                  "variant"
                ]
              }
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
            "description": "List all sales order rows",
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
                      "sales_order_id": 1,
                      "id": 1,
                      "quantity": 1,
                      "variant_id": 1,
                      "tax_rate_id": 1,
                      "location_id": 1,
                      "price_per_unit": 150,
                      "total_discount": "10.00",
                      "price_per_unit_in_base_currency": 300,
                      "conversion_rate": 2,
                      "conversion_date": "2020-10-23T10:37:05.085Z",
                      "product_availability": "EXPECTED",
                      "product_expected_date": "2020-10-23T10:37:05.085Z",
                      "created_at": "2020-10-23T10:37:05.085Z",
                      "updated_at": "2020-10-23T10:37:05.085Z",
                      "deleted_at": null,
                      "total": 150,
                      "total_in_base_currency": 300,
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
                      ],
                      "custom_fields": {
                        "37460d24-ea57-416d-888e-bea7c0505642": "note for picker"
                      },
                      "variant": {
                        "id": 1,
                        "sku": "EM",
                        "sales_price": 40,
                        "product_id": 1,
                        "purchase_price": 0,
                        "type": "product",
                        "created_at": "2020-10-23T10:37:05.085Z",
                        "updated_at": "2020-10-23T10:37:05.085Z",
                        "internal_barcode": "0316",
                        "registered_barcode": "0785223088",
                        "supplier_item_codes": [
                          "978-0785223085",
                          "0785223088"
                        ],
                        "config_attributes": [
                          {
                            "config_name": "Type",
                            "config_value": "Standard"
                          }
                        ]
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