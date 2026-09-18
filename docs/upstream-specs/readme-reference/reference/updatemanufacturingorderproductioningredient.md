---
updatedAt: 2026-05-29T09:20:09.000Z
---

Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

# Update a manufacturing order production ingredient

Updates the traceability of the specified manufacturing order production ingredient.

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
    "/manufacturing_order_production_ingredients/{id}": {
      "patch": {
        "summary": "Update a manufacturing order production ingredient",
        "tags": [
          "Manufacturing order production ingredient"
        ],
        "description": "Updates the traceability of the specified manufacturing order production ingredient.",
        "operationId": "updateManufacturingOrderProductionIngredient",
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "manufacturing order production ingredient id",
            "schema": {
              "type": "integer"
            },
            "in": "path"
          }
        ],
        "requestBody": {
          "description": "manufacturing order production ingredient details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "batch_transactions": {
                    "type": "array",
                    "deprecated": true,
                    "description": "Deprecated in favor of `traceability`.",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "batch_id",
                        "quantity"
                      ],
                      "properties": {
                        "quantity": {
                          "type": "number"
                        },
                        "batch_id": {
                          "type": "integer"
                        }
                      }
                    }
                  },
                  "traceability": {
                    "type": "array",
                    "description": "Consumed traceability for the ingredient, moved here from the recipe row.",
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
        "responses": {
          "200": {
            "description": "Updated manufacturing order production ingredient",
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
                  "id": 252,
                  "location_id": 321,
                  "variant_id": 24001,
                  "manufacturing_order_id": 21400,
                  "manufacturing_order_recipe_row_id": 20300,
                  "production_id": 21300,
                  "quantity": 4,
                  "production_date": "2023-02-10T10:06:13.047Z",
                  "cost": 1,
                  "traceability": [
                    {
                      "batch_id": 1,
                      "bin_location_id": null,
                      "quantity": "2"
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