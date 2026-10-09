---
updatedAt: 2026-05-29T09:20:09.000Z
agentTools:
  projectIndex: https://developer.katanamrp.com/llms.txt
---

# Create a purchase order row

Creates a new purchase order row object.

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
    "/purchase_order_rows": {
      "post": {
        "summary": "Create a purchase order row",
        "tags": [
          "Purchase order row"
        ],
        "description": "Creates a new purchase order row object.",
        "operationId": "createPurchaseOrderRow",
        "requestBody": {
          "description": "new purchase order row details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "purchase_order_id",
                  "price_per_unit",
                  "quantity",
                  "variant_id"
                ],
                "properties": {
                  "purchase_order_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "quantity": {
                    "type": "number",
                    "maximum": 100000000000000000
                  },
                  "variant_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "tax_rate_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "group_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "price_per_unit": {
                    "type": "number",
                    "maximum": 100000000000000000,
                    "minimum": 0
                  },
                  "purchase_uom_conversion_rate": {
                    "type": "number",
                    "maximum": 100000000000000000,
                    "minimum": 0
                  },
                  "purchase_uom": {
                    "type": "string",
                    "maxLength": 7
                  },
                  "arrival_date": {
                    "type": "string"
                  },
                  "location_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "custom_fields": {
                    "type": "object",
                    "nullable": true,
                    "additionalProperties": true,
                    "description": "_Behind feature flag — contact support@katanamrp.com to enable._ Custom field values keyed by custom field definition ID (UUID) of a definition with `entity_type` `PurchaseOrderRow` or `OutsourcedPurchaseOrderRow`. Each value matches the definition’s `field_type` — string for `shortText`/`url`, number for `number`, boolean for `boolean`, `YYYY-MM-DD` string for `date`, or the integer choice `id` for `singleSelect`. Unknown definition IDs are rejected with a 422."
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "New purchase order row",
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
                  "id": 1,
                  "quantity": 1,
                  "variant_id": 1,
                  "tax_rate_id": 1,
                  "price_per_unit": 1.5,
                  "purchase_uom_conversion_rate": 1.1,
                  "purchase_uom": "cm",
                  "created_at": "2021-02-03T13:13:07.121Z",
                  "updated_at": "2021-02-03T13:13:07.121Z",
                  "deleted_at": null,
                  "batch_transactions": [],
                  "currency": "USD",
                  "conversion_rate": null,
                  "conversion_date": null,
                  "received_date": "2021-02-03T13:13:07.000Z",
                  "arrival_date": "2021-02-02T13:13:07.000Z",
                  "purchase_order_id": 268123,
                  "total": 1,
                  "total_in_base_currency": 1,
                  "landed_cost": 45.5,
                  "group_id": 11,
                  "location_id": 1,
                  "custom_fields": {
                    "9d1c4b52-7f38-4e0a-9a6d-3f2b8c1e4a70": "inspect on arrival"
                  }
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
          "422": {
            "description": "Check the details property for a specific error message.",
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
                  "statusCode": 422,
                  "name": "UnprocessableEntityError",
                  "message": "The request body is invalid. See error object `details` property for more info.",
                  "code": "VALIDATION_FAILED",
                  "details": [
                    {
                      "path": ".name",
                      "code": "maxLength",
                      "message": "should NOT be longer than 10 characters",
                      "info": {
                        "limit": 10
                      }
                    }
                  ]
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