# List all sales order fulfillments

Returns a list of sales order fulfillments you’ve previously created.
  The sales order fulfillments are returned in a sorted order,
    with the most recent sales order fulfillments appearing first.

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
    "/sales_order_fulfillments": {
      "get": {
        "summary": "List all sales order fulfillments",
        "tags": [
          "Sales order fulfillment"
        ],
        "description": "Returns a list of sales order fulfillments you’ve previously created.\n  The sales order fulfillments are returned in a sorted order,\n    with the most recent sales order fulfillments appearing first.",
        "operationId": "getAllSalesOrderFulfillments",
        "parameters": [
          {
            "name": "sales_order_id",
            "required": false,
            "description": "Filters sales order fulfillments by a sales order id",
            "schema": {
              "type": "number"
            },
            "in": "query"
          },
          {
            "name": "picked_date_min",
            "required": false,
            "description": "Filters sales order fulfillments by a picked date min",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "tracking_number",
            "required": false,
            "description": "Filters sales order fulfillments by a tracking number",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "tracking_url",
            "required": false,
            "description": "Filters sales order fulfillments by a tracking url",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "tracking_carrier",
            "required": false,
            "description": "Filters sales order fulfillments by a tracking carrier",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "tracking_method",
            "required": false,
            "description": "Filters sales order fulfillments by a tracking method",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "status",
            "required": false,
            "description": "Filters sales order fulfillments by a status",
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
                      "sales_order_id": 1,
                      "picked_date": "2020-10-23T10:37:05.085Z",
                      "status": "DELIVERED",
                      "invoice_status": "NOT_INVOICED",
                      "conversion_rate": 2,
                      "conversion_date": "2020-10-23T10:37:05.085Z",
                      "tracking_number": "12345678",
                      "tracking_url": "https://tracking-number-url",
                      "tracking_carrier": "UPS",
                      "tracking_method": "ground",
                      "packer_id": 1,
                      "sales_order_fulfillment_rows": [
                        {
                          "id": 70550671,
                          "sales_order_row_id": 1,
                          "quantity": 2,
                          "batch_transactions": [
                            {
                              "batch_id": 1,
                              "quantity": 2
                            }
                          ],
                          "serial_numbers": [
                            1
                          ]
                        }
                      ]
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