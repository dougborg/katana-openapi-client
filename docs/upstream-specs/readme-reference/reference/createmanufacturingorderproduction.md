---
updatedAt: 2026-05-29T09:20:09.000Z
---

Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

# Create a manufacturing order production

Creates a manufacturing order production (partial completion). The `ingredients` and `operations`
  arrays each behave independently:

  - **Entries provided**: records exactly that consumption.
  - **Empty array (`[]`)**: records no consumption.
  - **Array omitted**: consumption is auto-created from the manufacturing order plan.

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
        "description": "Creates a manufacturing order production (partial completion). The `ingredients` and `operations`\n  arrays each behave independently:\n\n  - **Entries provided**: records exactly that consumption.\n  - **Empty array (`[]`)**: records no consumption.\n  - **Array omitted**: consumption is auto-created from the manufacturing order plan.",
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
                          "deprecated": true,
                          "description": "Deprecated in favor of `traceability`.",
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
                        }
                      }
                    }
                  },
                  "serial_numbers": {
                    "type": "array",
                    "deprecated": true,
                    "description": "Deprecated in favor of `traceability`.",
                    "items": {
                      "type": "number"
                    }
                  },
                  "traceability": {
                    "type": "array",
                    "description": "Produced traceability for the output, moved here from the manufacturing order.",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "description": "One allocation entry for the produced output. `traceability` is an array because the two tracking modes need different cardinality — a variant is tracked one way, so an output is either all-batch or all-serial, never mixed:\n\n- **Non-tracked variant** — send `[]` (or omit `traceability`).\n- **Batch-tracked** — the entire produced quantity goes to a **single batch**, so send exactly **one** entry with its `batch_id`. Only one batch is ever honored per output; extra batch entries are not applied. `quantity` is not used here — the batch takes the whole output and is never split across batches.\n- **Serial-tracked** — each produced unit is its own serial number, so send **one entry per serial number** (`serial_number_id`). This is the case the array shape exists for. The number of entries may not exceed the produced quantity (422 otherwise).",
                      "properties": {
                        "batch_id": {
                          "type": "integer",
                          "minimum": 0,
                          "maximum": 2147483647,
                          "nullable": true,
                          "description": "Batch id. Mutually exclusive with `serial_number_id`. At most one batch per output — the whole produced quantity is assigned to it."
                        },
                        "serial_number_id": {
                          "type": "integer",
                          "minimum": 0,
                          "maximum": 2147483647,
                          "nullable": true,
                          "description": "Serial number id. Mutually exclusive with `batch_id`. One entry per produced unit."
                        },
                        "quantity": {
                          "type": "string",
                          "description": "Ignored for produced output: a batch entry takes the entire produced quantity and each serial entry is one unit. Accepted for shape compatibility but has no effect."
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
                      "transaction_id": null,
                      "serial_number": "SN1",
                      "resource_type": "Production",
                      "resource_id": 21300,
                      "transaction_date": "2023-02-10T10:06:14.435Z",
                      "quantity_change": 1
                    }
                  ],
                  "traceability": [
                    {
                      "batch_id": 1,
                      "serial_number_id": null,
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