# Create a manufacturing order production

Creates a new manufacturing order production (partial completion).

**Ingredient and Operation Consumption Behavior:**

The following behavior applies independently to the 'ingredients' and 'operations' arrays:

- **When an array is provided with data**: Records the specified consumption values.
- **When an array is provided but empty ([])**: Records production but no consumption for that array.
- **When an array is omitted**: Automatically creates consumption based on the manufacturing order plan.

This allows flexible reporting: explicit values, no consumption, or auto-calculated from plan.

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
    "/manufacturing_order_productions": {
      "post": {
        "summary": "Create a manufacturing order production",
        "tags": [
          "Manufacturing order production"
        ],
        "description": "Creates a new manufacturing order production (partial completion).\n\n**Ingredient and Operation Consumption Behavior:**\n\nThe following behavior applies independently to the 'ingredients' and 'operations' arrays:\n\n- **When an array is provided with data**: Records the specified consumption values.\n- **When an array is provided but empty ([])**: Records production but no consumption for that array.\n- **When an array is omitted**: Automatically creates consumption based on the manufacturing order plan.\n\nThis allows flexible reporting: explicit values, no consumption, or auto-calculated from plan.",
        "operationId": "createManufacturingOrderProduction",
        "requestBody": {
          "description": "new manufacturing order production details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "manufacturing_order_id",
                  "completed_quantity"
                ],
                "properties": {
                  "manufacturing_order_id": {
                    "type": "number"
                  },
                  "completed_quantity": {
                    "type": "number",
                    "maximum": 1000000000000000
                  },
                  "completed_date": {
                    "type": "string"
                  },
                  "is_final": {
                    "type": "boolean"
                  },
                  "ingredients": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "manufacturing_order_recipe_row_id",
                        "quantity"
                      ],
                      "properties": {
                        "manufacturing_order_recipe_row_id": {
                          "type": "number"
                        },
                        "quantity": {
                          "type": "number"
                        },
                        "batch_transactions": {
                          "type": "array",
                          "items": {
                            "type": "object",
                            "additionalProperties": false,
                            "required": [
                              "quantity",
                              "batch_id"
                            ],
                            "properties": {
                              "quantity": {
                                "maximum": 1000000000000000,
                                "type": "number"
                              },
                              "batch_id": {
                                "type": "integer"
                              }
                            }
                          }
                        }
                      }
                    }
                  },
                  "operations": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "manufacturing_order_operation_id",
                        "time"
                      ],
                      "properties": {
                        "manufacturing_order_operation_id": {
                          "type": "number"
                        },
                        "time": {
                          "type": "number"
                        },
                        "batch_transactions": {
                          "type": "array",
                          "items": {
                            "type": "object",
                            "additionalProperties": false,
                            "required": [
                              "quantity",
                              "batch_id"
                            ],
                            "properties": {
                              "quantity": {
                                "maximum": 1000000000000000,
                                "type": "number"
                              },
                              "batch_id": {
                                "type": "integer"
                              }
                            }
                          }
                        }
                      }
                    }
                  },
                  "serial_numbers": {
                    "type": "array",
                    "items": {
                      "type": "number",
                      "additionalProperties": false
                    }
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "New manufacturing order production",
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
                  "id": 21300,
                  "manufacturing_order_id": 21400,
                  "quantity": 2,
                  "production_date": "2023-02-10T10:06:13.047Z",
                  "created_at": "2023-02-10T10:06:14.425Z",
                  "updated_at": "2023-02-10T10:06:15.094Z",
                  "deleted_at": null,
                  "ingredients": [
                    {
                      "id": 252,
                      "location_id": 321,
                      "variant_id": 24764,
                      "manufacturing_order_id": 21400,
                      "manufacturing_order_recipe_row_id": 20300,
                      "production_id": 21300,
                      "quantity": 4,
                      "production_date": "2023-02-10T10:06:13.047Z",
                      "cost": 1,
                      "created_at": "2023-02-10T10:06:14.435Z",
                      "updated_at": "2023-02-10T10:06:15.070Z",
                      "deleted_at": null
                    }
                  ],
                  "operations": [
                    {
                      "id": 61,
                      "location_id": 321,
                      "manufacturing_order_id": 21300,
                      "manufacturing_order_operation_id": 20400,
                      "production_id": 21300,
                      "time": 18000,
                      "production_date": "2023-02-10T10:06:13.047Z",
                      "cost": 50,
                      "created_at": "2023-02-10T10:06:14.435Z",
                      "updated_at": "2023-02-10T10:06:14.435Z",
                      "deleted_at": null
                    }
                  ],
                  "serial_numbers": [
                    {
                      "id": 1,
                      "transaction_id": "eb4da756-0842-4495-9118-f8135f681234",
                      "serial_number": "SN1",
                      "resource_type": "Production",
                      "resource_id": 2,
                      "transaction_date": "2023-02-10T10:06:14.435Z"
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