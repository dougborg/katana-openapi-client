---
updatedAt: 2026-05-29T09:20:09.000Z
---

Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

# Create a stock adjustment

Creates a stock adjustment object.

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
    "/stock_adjustments": {
      "post": {
        "summary": "Create a stock adjustment",
        "tags": [
          "Stock adjustment"
        ],
        "description": "Creates a stock adjustment object.",
        "operationId": "createStockAdjustment",
        "requestBody": {
          "description": "new stock adjustment details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "location_id",
                  "stock_adjustment_rows"
                ],
                "properties": {
                  "stock_adjustment_number": {
                    "type": "string",
                    "minLength": 1
                  },
                  "stock_adjustment_date": {
                    "type": "string",
                    "minLength": 1
                  },
                  "location_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "reason": {
                    "type": "string"
                  },
                  "additional_info": {
                    "type": "string",
                    "nullable": true
                  },
                  "stock_adjustment_rows": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "quantity",
                        "variant_id"
                      ],
                      "properties": {
                        "quantity": {
                          "type": "number",
                          "maximum": 100000000000000000
                        },
                        "variant_id": {
                          "type": "integer",
                          "maximum": 2147483647
                        },
                        "cost_per_unit": {
                          "type": "number",
                          "maximum": 1000000000000000000
                        },
                        "batch_transactions": {
                          "type": "array",
                          "minItems": 1,
                          "deprecated": true,
                          "description": "Batch-level breakdown of the stock adjustment row quantity. The sum of batch transaction quantities must equal the row quantity. **Deprecated** — will be phased out; prefer `traceability`. When both `traceability` and `batch_transactions` are sent, `traceability` wins.",
                          "items": {
                            "type": "object",
                            "additionalProperties": false,
                            "required": [
                              "batch_id",
                              "quantity"
                            ],
                            "properties": {
                              "batch_id": {
                                "type": "integer",
                                "nullable": true,
                                "maximum": 2147483647,
                                "description": "ID of the batch to adjust stock for. Use `null` to record unbatched (untraced) stock."
                              },
                              "quantity": {
                                "type": "number",
                                "maximum": 100000000000000000
                              }
                            }
                          }
                        },
                        "traceability": {
                          "type": "array",
                          "description": "Unified allocation breakdown of the row quantity (batch / serial / bin). Preferred over `batch_transactions`; when both are sent, `traceability` wins. Each entry requires an explicit `quantity` (the service does not default it).",
                          "items": {
                            "type": "object",
                            "additionalProperties": false,
                            "description": "One allocation entry. A row's `traceability` is an array; entries together cover the row's quantity.\n\n- **Non-tracked variant** — send `[]` (or omit `traceability`).\n- **Batch-tracked** — each entry sets `batch_id` and `quantity`. Use multiple entries to draw from multiple batches.\n- **Serial-tracked** — each entry sets `serial_number_id`. Use one entry per serial number.\n\nA variant is tracked one way, so per row you cannot mix batch and serial entries. Each entry sets at most one of `batch_id` / `serial_number_id`. `bin_location_id` is optional and pins the allocation to a bin location.",
                            "properties": {
                              "batch_id": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 2147483647,
                                "nullable": true,
                                "description": "Batch id. Mutually exclusive with `serial_number_id`."
                              },
                              "serial_number_id": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 2147483647,
                                "nullable": true,
                                "description": "Serial number id. Mutually exclusive with `batch_id`."
                              },
                              "bin_location_id": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 2147483647,
                                "nullable": true,
                                "description": "Bin location id the allocation is drawn from / moved to. Optional."
                              },
                              "quantity": {
                                "type": "string",
                                "description": "Decimal string. **Required** for stock adjustments: the service does not default it, so a missing `quantity` is rejected. Serial entries are implicit `'1'` but the value must still be sent."
                              }
                            },
                            "required": [
                              "quantity"
                            ]
                          }
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
            "description": "New stock adjustment created",
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
                  "stock_adjustment_number": "SA-1",
                  "stock_adjustment_date": "2021-10-06T11:47:13.846Z",
                  "location_id": 1,
                  "reason": "adjustment reason",
                  "additional_info": "adjustment additional info",
                  "stock_adjustment_rows": [
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
                          "batch_id": null,
                          "quantity": 50
                        }
                      ],
                      "traceability": [
                        {
                          "batch_id": 1,
                          "serial_number_id": null,
                          "bin_location_id": 7,
                          "quantity": "50"
                        },
                        {
                          "batch_id": null,
                          "serial_number_id": null,
                          "bin_location_id": null,
                          "quantity": "50"
                        }
                      ]
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
                      "traceability": [
                        {
                          "batch_id": 3,
                          "serial_number_id": null,
                          "bin_location_id": null,
                          "quantity": "150"
                        }
                      ]
                    }
                  ],
                  "created_at": "2021-10-06T11:47:13.846Z",
                  "updated_at": "2021-10-06T11:47:13.846Z",
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