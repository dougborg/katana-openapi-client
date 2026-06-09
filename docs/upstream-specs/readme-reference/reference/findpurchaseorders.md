> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# List all purchase orders

Returns a list of purchase orders you’ve previously created. The purchase orders are returned in sorted
    order, with the most recent purchase orders appearing first.

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
    "/purchase_orders": {
      "get": {
        "summary": "List all purchase orders",
        "tags": [
          "Purchase order"
        ],
        "description": "Returns a list of purchase orders you’ve previously created. The purchase orders are returned in sorted\n    order, with the most recent purchase orders appearing first.",
        "operationId": "findPurchaseOrders",
        "parameters": [
          {
            "name": "ids",
            "required": false,
            "description": "Filters purchase orders by an array of IDs",
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
            "description": "Filters purchase orders by an order number",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "entity_type",
            "required": false,
            "description": "Filters purchase orders by an entity type",
            "schema": {
              "type": "string",
              "enum": [
                "regular",
                "outsourced"
              ]
            },
            "in": "query"
          },
          {
            "name": "status",
            "required": false,
            "description": "Filters purchase orders by a status",
            "schema": {
              "enum": [
                "DRAFT",
                "NOT_RECEIVED",
                "PARTIALLY_RECEIVED",
                "RECEIVED"
              ]
            },
            "in": "query"
          },
          {
            "name": "billing_status",
            "required": false,
            "description": "Filters purchase orders by a billing status",
            "schema": {
              "enum": [
                "BILLED",
                "NOT_BILLED",
                "PARTIALLY_BILLED"
              ]
            },
            "in": "query"
          },
          {
            "name": "currency",
            "required": false,
            "description": "Filters purchase orders by a currency",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "location_id",
            "required": false,
            "description": "Filters purchase orders by a location",
            "schema": {
              "type": "number"
            },
            "in": "query"
          },
          {
            "name": "tracking_location_id",
            "required": false,
            "description": "Filters purchase orders by a tracking location",
            "schema": {
              "type": "number"
            },
            "in": "query"
          },
          {
            "name": "supplier_id",
            "required": false,
            "description": "Filters purchase orders by a supplier",
            "schema": {
              "type": "number"
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
                  "supplier"
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
            "description": "List all purchase orders",
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
                      "status": "NOT_RECEIVED",
                      "order_no": "PO-1",
                      "entity_type": "regular",
                      "default_group_id": 9,
                      "supplier_id": 1,
                      "currency": "USD",
                      "expected_arrival_date": "2021-10-13T15:31:48.490Z",
                      "order_created_date": "2021-10-13T15:31:48.490Z",
                      "additional_info": "Please unpack",
                      "location_id": 1,
                      "ingredient_availability": null,
                      "ingredient_expected_date": null,
                      "tracking_location_id": null,
                      "total": 1,
                      "total_in_base_currency": 1,
                      "created_at": "2021-10-13T15:31:48.490Z",
                      "updated_at": "2021-10-13T15:31:48.490Z",
                      "deleted_at": null,
                      "billing_status": "BILLED",
                      "last_document_status": "SENDING",
                      "purchase_order_rows": [
                        {
                          "id": 1,
                          "quantity": 1,
                          "variant_id": 1,
                          "tax_rate_id": 1,
                          "price_per_unit": 1.5,
                          "purchase_uom": "cm",
                          "created_at": "2021-10-13T15:31:48.490Z",
                          "updated_at": "2021-10-13T15:31:48.490Z",
                          "deleted_at": null,
                          "currency": "USD",
                          "conversion_rate": 1,
                          "total": 1,
                          "total_in_base_currency": 1,
                          "conversion_date": "2021-10-13T15:31:48.490Z",
                          "received_date": "2021-10-13T15:31:48.490Z",
                          "batch_transactions": [
                            {
                              "quantity": 1,
                              "batch_id": 1
                            },
                            {
                              "quantity": 1,
                              "batch_id": null
                            }
                          ],
                          "purchase_order_id": 1,
                          "purchase_uom_conversion_rate": 1.1,
                          "landed_cost": "45.0000000000",
                          "group_id": 11
                        }
                      ],
                      "supplier": {
                        "id": 1,
                        "name": "Luke Skywalker",
                        "email": "luke.skywalker@example.com",
                        "comment": "Luke Skywalker was a Tatooine farmboy who rose from humble beginnings to become one of the\n              greatest Jedi the galaxy has ever known.",
                        "currency": "UAH",
                        "created_at": "2020-10-23T10:37:05.085Z",
                        "updated_at": "2020-10-23T10:37:05.085Z",
                        "deleted_at": null
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