---
updatedAt: 2026-05-29T09:20:09.000Z
---

Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

# Update a manufacturing order recipe row

Updates the specified manufacturing order recipe row. Once the manufacturing order status is DONE,
  `variant_id`, `planned_quantity_per_unit`, and `total_actual_quantity` can no longer be changed.

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
    "/manufacturing_order_recipe_rows/{id}": {
      "patch": {
        "summary": "Update a manufacturing order recipe row",
        "tags": [
          "Manufacturing order recipe"
        ],
        "description": "Updates the specified manufacturing order recipe row. Once the manufacturing order status is DONE,\n  `variant_id`, `planned_quantity_per_unit`, and `total_actual_quantity` can no longer be changed.",
        "operationId": "updateManufacturingOrderRecipeRows",
        "requestBody": {
          "description": "manufacturing order recipe details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "variant_id": {
                    "type": "number"
                  },
                  "notes": {
                    "type": "string"
                  },
                  "planned_quantity_per_unit": {
                    "type": "number"
                  },
                  "total_actual_quantity": {
                    "type": "number"
                  },
                  "batch_transactions": {
                    "type": "array",
                    "deprecated": true,
                    "description": "Deprecated in favor of `traceability`.",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "batch_id": {
                          "type": "number"
                        },
                        "quantity": {
                          "type": "number"
                        }
                      }
                    }
                  },
                  "traceability": {
                    "type": "array",
                    "description": "Pre-assigned traceability for consumption. Consumed traceability is moved to the production ingredient.",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "description": "One allocation entry for a consumed ingredient. Entries together cover the recipe row / production ingredient quantity.\n\n- **Non-tracked variant** — send `[]` (or omit `traceability`).\n- **Batch-tracked** — each entry sets `batch_id` and `quantity`. `bin_location_id` optionally pins the bin the allocation is drawn from.",
                      "properties": {
                        "batch_id": {
                          "type": "integer",
                          "minimum": 0,
                          "maximum": 2147483647,
                          "nullable": true,
                          "description": "Batch id the ingredient allocation is drawn from."
                        },
                        "bin_location_id": {
                          "type": "integer",
                          "minimum": 0,
                          "maximum": 2147483647,
                          "nullable": true,
                          "description": "Bin location id the allocation is drawn from. Optional."
                        },
                        "quantity": {
                          "type": "string",
                          "description": "Decimal string quantity for this allocation entry."
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        },
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "manufacturing order recipe row id",
            "schema": {
              "type": "integer"
            },
            "in": "path"
          }
        ],
        "responses": {
          "200": {
            "description": "New manufacturin order operation row",
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
                  "manufacturing_order_id": 1,
                  "variant_id": 1,
                  "notes": "Pay close attention to this",
                  "planned_quantity_per_unit": 1.2,
                  "total_actual_quantity": 12,
                  "ingredient_availability": "IN_STOCK",
                  "ingredient_expected_date": "2021-03-18T12:33:39.957Z",
                  "batch_transactions": [
                    {
                      "batch_id": 11,
                      "quantity": 7.4
                    },
                    {
                      "batch_id": 12,
                      "quantity": 4.6
                    }
                  ],
                  "traceability": [
                    {
                      "batch_id": 1,
                      "bin_location_id": null,
                      "quantity": "2"
                    }
                  ],
                  "cost": 50.4,
                  "created_at": "2021-02-18T12:33:39.957Z",
                  "updated_at": "2021-02-18T12:33:39.957Z",
                  "deleted_at": null
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