> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# List bin inventory levels

Per-bin inventory levels at the chosen granularity. `granularity=VARIANT` (default) returns one row per
(location, variant, bin); `BATCH` and `SERIAL_NUMBER` break rows down further by the matching
traceability axis. Each row carries three decimal-string quantities: `quantity_in_stock`,
`quantity_committed`, `quantity_expected`.

A null `bin_location_id`, `batch_id`, or `serial_number_id` denotes stock whose traceability on that
axis has not been set (unassigned bin, unbatched stock, untraced serial). Pass `?<param>=null` to
target those rows.

Rows are removed once all three quantities reach zero; absence implies zero across the board. This
prevents the dataset from accumulating stale entries for every combination ever touched —
`(location, variant, bin)`, `(location, variant, bin, batch)`, or
`(location, variant, bin, serial_number)` depending on granularity — and keeps pagination focused on
positions with non-zero stock, commitments, or expected receipts.

Bin inventory levels are computed asynchronously and are eventually consistent — recent stock
movements may not be reflected immediately.

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
    "/bin_inventory": {
      "get": {
        "summary": "List bin inventory levels",
        "tags": [
          "Bin inventory"
        ],
        "description": "Per-bin inventory levels at the chosen granularity. `granularity=VARIANT` (default) returns one row per\n(location, variant, bin); `BATCH` and `SERIAL_NUMBER` break rows down further by the matching\ntraceability axis. Each row carries three decimal-string quantities: `quantity_in_stock`,\n`quantity_committed`, `quantity_expected`.\n\nA null `bin_location_id`, `batch_id`, or `serial_number_id` denotes stock whose traceability on that\naxis has not been set (unassigned bin, unbatched stock, untraced serial). Pass `?<param>=null` to\ntarget those rows.\n\nRows are removed once all three quantities reach zero; absence implies zero across the board. This\nprevents the dataset from accumulating stale entries for every combination ever touched —\n`(location, variant, bin)`, `(location, variant, bin, batch)`, or\n`(location, variant, bin, serial_number)` depending on granularity — and keeps pagination focused on\npositions with non-zero stock, commitments, or expected receipts.\n\nBin inventory levels are computed asynchronously and are eventually consistent — recent stock\nmovements may not be reflected immediately.",
        "operationId": "getBinInventory",
        "parameters": [
          {
            "name": "granularity",
            "required": false,
            "description": "Row granularity. Defaults to `VARIANT`.",
            "schema": {
              "type": "string",
              "enum": [
                "VARIANT",
                "BATCH",
                "SERIAL_NUMBER"
              ],
              "default": "VARIANT"
            },
            "in": "query"
          },
          {
            "name": "location_id",
            "required": false,
            "description": "Filter by location id.",
            "schema": {
              "type": "integer"
            },
            "in": "query"
          },
          {
            "name": "variant_id",
            "required": false,
            "description": "Filter by variant id.",
            "schema": {
              "type": "integer"
            },
            "in": "query"
          },
          {
            "name": "bin_location_id",
            "required": false,
            "description": "Filter by bin location id. Pass `null` to target unassigned-bin rows.",
            "schema": {
              "type": "string",
              "pattern": "^(\\d+|null)$"
            },
            "in": "query"
          },
          {
            "name": "batch_id",
            "required": false,
            "description": "Filter by batch id. Only valid when `granularity=BATCH`. Pass `null` to target unbatched rows.",
            "schema": {
              "type": "string",
              "pattern": "^(\\d+|null)$"
            },
            "in": "query"
          },
          {
            "name": "serial_number_id",
            "required": false,
            "description": "Filter by serial number id. Only valid when `granularity=SERIAL_NUMBER`. Pass `null` to target untraced rows.",
            "schema": {
              "type": "string",
              "pattern": "^(\\d+|null)$"
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
          }
        ],
        "responses": {
          "200": {
            "description": "List of bin inventory levels",
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
                "examples": {
                  "variant": {
                    "summary": "granularity=VARIANT (default)",
                    "value": {
                      "data": [
                        {
                          "location_id": 1,
                          "variant_id": 50,
                          "bin_location_id": 9,
                          "quantity_in_stock": "10.00000",
                          "quantity_committed": "3.00000",
                          "quantity_expected": "5.00000"
                        },
                        {
                          "location_id": 1,
                          "variant_id": 51,
                          "bin_location_id": null,
                          "quantity_in_stock": "2.00000",
                          "quantity_committed": "0.00000",
                          "quantity_expected": "0.00000"
                        }
                      ]
                    }
                  },
                  "batch": {
                    "summary": "granularity=BATCH",
                    "value": {
                      "data": [
                        {
                          "location_id": 1,
                          "variant_id": 50,
                          "batch_id": 300,
                          "bin_location_id": 9,
                          "quantity_in_stock": "10.00000",
                          "quantity_committed": "3.00000",
                          "quantity_expected": "5.00000"
                        }
                      ]
                    }
                  },
                  "serial_number": {
                    "summary": "granularity=SERIAL_NUMBER",
                    "value": {
                      "data": [
                        {
                          "location_id": 1,
                          "variant_id": 50,
                          "serial_number_id": 400,
                          "bin_location_id": 9,
                          "quantity_in_stock": "1.00000",
                          "quantity_committed": "0.00000",
                          "quantity_expected": "0.00000"
                        }
                      ]
                    }
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