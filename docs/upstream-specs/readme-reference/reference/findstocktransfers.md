> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# List all stock transfers

Returns a list of stock transfers you’ve previously created.
    The stock transfers are returned in sorted order, with the most recent
    stock transfers appearing first.

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
    "/stock_transfers": {
      "get": {
        "summary": "List all stock transfers",
        "tags": [
          "Stock transfer"
        ],
        "description": "Returns a list of stock transfers you’ve previously created.\n    The stock transfers are returned in sorted order, with the most recent\n    stock transfers appearing first.",
        "operationId": "findStockTransfers",
        "parameters": [
          {
            "name": "ids",
            "required": false,
            "description": "Filters stock transfers by an array of IDs",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer"
              }
            },
            "in": "query"
          },
          {
            "name": "stock_transfer_number",
            "required": false,
            "description": "Filters stock transfers by a stock transfer number",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "source_location_id",
            "required": false,
            "description": "Filters stock transfers by source location",
            "schema": {
              "type": "number"
            },
            "in": "query"
          },
          {
            "name": "target_location_id",
            "required": false,
            "description": "Filters stock transfers by target location",
            "schema": {
              "type": "number"
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
            "description": "List all stock transfers",
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
                      "stock_transfer_number": "ST-1",
                      "source_location_id": 1,
                      "target_location_id": 2,
                      "transfer_date": "2021-10-06T11:47:13.846Z",
                      "order_created_date": "2021-10-01T11:47:13.846Z",
                      "expected_arrival_date": "2021-10-20T11:47:13.846Z",
                      "additional_info": "transfer additional info",
                      "stock_transfer_rows": [
                        {
                          "id": 1,
                          "variant_id": 1,
                          "quantity": 100,
                          "cost_per_unit": 123.45,
                          "batch_transactions": [
                            {
                              "batch_id": 1,
                              "quantity": 50
                            },
                            {
                              "batch_id": 2,
                              "quantity": 50
                            }
                          ],
                          "deleted_at": null
                        },
                        {
                          "id": 2,
                          "variant_id": 2,
                          "quantity": 150,
                          "cost_per_unit": 234.56,
                          "batch_transactions": [
                            {
                              "batch_id": 3,
                              "quantity": 150
                            }
                          ],
                          "deleted_at": null
                        }
                      ],
                      "created_at": "2021-10-06T11:47:13.846Z",
                      "updated_at": "2021-10-06T11:47:13.846Z",
                      "deleted_at": null
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