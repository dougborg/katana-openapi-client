> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Create a bin transfer row

Adds a row to an existing bin transfer, optionally with traceability in the same call. The row inherits `location_id`, `created_date`, and `departed_at` from the parent transfer. Rows cannot be added when the parent is in `DONE`.

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
    "/bin_transfer_rows": {
      "post": {
        "summary": "Create a bin transfer row",
        "tags": [
          "Bin transfer row"
        ],
        "description": "Adds a row to an existing bin transfer, optionally with traceability in the same call. The row inherits `location_id`, `created_date`, and `departed_at` from the parent transfer. Rows cannot be added when the parent is in `DONE`.",
        "operationId": "createBinTransferRow",
        "requestBody": {
          "description": "new bin transfer row",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "bin_transfer_id",
                  "variant_id",
                  "quantity"
                ],
                "properties": {
                  "bin_transfer_id": {
                    "type": "integer",
                    "maximum": 2147483647,
                    "description": "Parent bin transfer id. Must not be in `DONE` status."
                  },
                  "variant_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "quantity": {
                    "type": "string",
                    "maximum": 100000000000000000,
                    "description": "Quantity to move, as a positive decimal string."
                  },
                  "source_bin_location_id": {
                    "type": "integer",
                    "maximum": 2147483647,
                    "nullable": true
                  },
                  "target_bin_location_id": {
                    "type": "integer",
                    "maximum": 2147483647,
                    "nullable": true
                  },
                  "traceability": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "description": "One allocation entry. A row's `traceability` is an array; entries together cover the row's quantity.\n\n- **Non-tracked variant** — send `[]` (or omit `traceability`).\n- **Batch-tracked** — each entry sets `batch_id` and `quantity`. Use multiple entries to draw from multiple batches.\n- **Serial-tracked** — each entry sets `serial_number_id`. Use one entry per serial number.\n\nA variant is tracked one way, so per row you cannot mix batch and serial entries. Each entry sets at most one of `batch_id` / `serial_number_id`. Sum of entry `quantity` must not exceed the row `quantity`; any leftover surfaces on read as an entry with both ids null.",
                      "properties": {
                        "batch_id": {
                          "type": "integer",
                          "maximum": 2147483647,
                          "nullable": true,
                          "description": "Batch id. Mutually exclusive with `serial_number_id`."
                        },
                        "serial_number_id": {
                          "type": "integer",
                          "maximum": 2147483647,
                          "nullable": true,
                          "description": "Serial number id. Mutually exclusive with `batch_id`."
                        },
                        "quantity": {
                          "type": "string",
                          "maximum": 100000000000000000,
                          "description": "Decimal string. Required for batch entries; serial entries are implicit `'1'` (the server stores and returns `'1'` regardless of submitted value)."
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
            "description": "New bin transfer row created",
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
                  "id": 11,
                  "bin_transfer_id": 1,
                  "location_id": 1,
                  "variant_id": 42,
                  "quantity": "3",
                  "source_bin_location_id": 7,
                  "target_bin_location_id": 9,
                  "created_date": "2026-05-22T10:00:00.000Z",
                  "departed_at": null,
                  "arrived_at": null,
                  "traceability": [
                    {
                      "batch_id": 100,
                      "serial_number_id": null,
                      "quantity": "3"
                    }
                  ],
                  "created_at": "2026-05-22T10:00:00.000Z",
                  "updated_at": "2026-05-22T10:00:00.000Z",
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