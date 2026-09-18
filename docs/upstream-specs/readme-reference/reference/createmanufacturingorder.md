---
updatedAt: 2026-05-29T09:20:09.000Z
---

Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

# Create a manufacturing order

Creates a new manufacturing order. Manufacturing order recipe and
  operation rows are created automatically based on the product recipe and operations.

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
    "/manufacturing_orders": {
      "post": {
        "summary": "Create a manufacturing order",
        "tags": [
          "Manufacturing order"
        ],
        "description": "Creates a new manufacturing order. Manufacturing order recipe and\n  operation rows are created automatically based on the product recipe and operations.",
        "operationId": "createManufacturingOrder",
        "requestBody": {
          "description": "new manufacturing order details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "variant_id",
                  "location_id",
                  "planned_quantity"
                ],
                "properties": {
                  "status": {
                    "enum": [
                      "NOT_STARTED"
                    ],
                    "type": "string"
                  },
                  "order_no": {
                    "type": "string"
                  },
                  "variant_id": {
                    "type": "number"
                  },
                  "location_id": {
                    "type": "number"
                  },
                  "planned_quantity": {
                    "type": "number"
                  },
                  "actual_quantity": {
                    "type": "number"
                  },
                  "order_created_date": {
                    "type": "string"
                  },
                  "production_deadline_date": {
                    "type": "string",
                    "description": "Use only if automatic production deadline calculation for the factory location is switched OFF."
                  },
                  "additional_info": {
                    "type": "string"
                  },
                  "batch_transactions": {
                    "type": "array",
                    "deprecated": true,
                    "description": "Deprecated in favor of `traceability`.",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
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
                    "description": "Pre-assigned traceability for the order output. Produced traceability is moved to the production.",
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
            "description": "New manufacturing order",
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
                  "id": 21400,
                  "status": "NOT_STARTED",
                  "order_no": "SO-2 / 1",
                  "variant_id": 1418016,
                  "planned_quantity": 1,
                  "actual_quantity": null,
                  "batch_transactions": [],
                  "location_id": 2327,
                  "order_created_date": "2021-09-01T07:49:29.000Z",
                  "done_date": null,
                  "production_deadline_date": "2021-10-18T08:00:00.000Z",
                  "additional_info": "",
                  "is_linked_to_sales_order": true,
                  "ingredient_availability": "IN_STOCK",
                  "total_cost": 0,
                  "total_actual_time": 0,
                  "total_planned_time": 18000,
                  "sales_order_id": 1,
                  "sales_order_row_id": 1,
                  "sales_order_delivery_deadline": "2021-09-01T07:49:29.813Z",
                  "material_cost": 10,
                  "created_at": "2021-09-01T07:49:29.813Z",
                  "updated_at": "2021-10-15T14:05:47.625Z",
                  "subassemblies_cost": 10,
                  "operations_cost": 10,
                  "deleted_at": null,
                  "serial_numbers": [
                    {
                      "id": 1,
                      "transaction_id": null,
                      "serial_number": "SN1",
                      "resource_type": "ManufacturingOrder",
                      "resource_id": 21400,
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