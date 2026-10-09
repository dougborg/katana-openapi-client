---
updatedAt: 2026-05-29T09:20:09.000Z
agentTools:
  projectIndex: https://developer.katanamrp.com/llms.txt
---

# Retrieve an outsourced purchase order recipe row

Retrieves the details of an existing outsourced purchase order recipe row. `traceability` lists the batch, serial number and bin location allocations the ingredient is consumed from, in the stock unit of the ingredient variant, including the untraced remainder as an entry with both ids null.

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
    "/outsourced_purchase_order_recipe_rows/{id}": {
      "get": {
        "summary": "Retrieve an outsourced purchase order recipe row",
        "tags": [
          "Outsourced purchase order recipe row"
        ],
        "description": "Retrieves the details of an existing outsourced purchase order recipe row. `traceability` lists the batch, serial number and bin location allocations the ingredient is consumed from, in the stock unit of the ingredient variant, including the untraced remainder as an entry with both ids null.",
        "operationId": "getPurchaseOrderRecipeRow",
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "Outsourced purchase order recipe row id",
            "schema": {
              "type": "integer"
            },
            "in": "path"
          }
        ],
        "responses": {
          "200": {
            "description": "An outsourced purchase order recipe row",
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
                  "purchase_order_id": 1,
                  "purchase_order_row_id": 1,
                  "ingredient_variant_id": 1,
                  "notes": "",
                  "planned_quantity_per_unit": 1.5,
                  "ingredient_availability": "PROCESSED",
                  "ingredient_expected_date": null,
                  "batch_transactions": [
                    {
                      "batch_id": 1,
                      "quantity": 10
                    },
                    {
                      "batch_id": null,
                      "quantity": 5
                    }
                  ],
                  "traceability": [
                    {
                      "batch_id": 1,
                      "serial_number_id": null,
                      "bin_location_id": 3,
                      "quantity": "10"
                    },
                    {
                      "batch_id": null,
                      "serial_number_id": null,
                      "bin_location_id": null,
                      "quantity": "5"
                    }
                  ],
                  "cost": 0,
                  "created_at": "2020-10-23T10:37:05.085Z",
                  "updated_at": "2020-10-23T10:37:05.085Z",
                  "deleted_at": null,
                  "custom_fields": {
                    "2fa40b67-e0f1-46be-84b2-6441f2c976c3": "AISI 304",
                    "b6c0cbb5-6ba0-4f6e-a6f4-2b6c3f4a57ea": 12
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