> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# List all bin transfers

Returns a list of bin transfers you've previously created, sorted with the most recent first. Each
transfer is returned with its rows and the rows' traceability allocations.

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
    "/bin_transfers": {
      "get": {
        "summary": "List all bin transfers",
        "tags": [
          "Bin transfer"
        ],
        "description": "Returns a list of bin transfers you've previously created, sorted with the most recent first. Each\ntransfer is returned with its rows and the rows' traceability allocations.",
        "operationId": "findBinTransfers",
        "parameters": [
          {
            "name": "ids",
            "required": false,
            "description": "Filter bin transfers by an array of ids",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer"
              }
            },
            "in": "query"
          },
          {
            "name": "bin_transfer_number",
            "required": false,
            "description": "Filter by bin transfer number",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "location_id",
            "required": false,
            "description": "Filter by the location id the transfer happens within",
            "schema": {
              "type": "integer"
            },
            "in": "query"
          },
          {
            "name": "status",
            "required": false,
            "description": "Filter by status",
            "schema": {
              "type": "string",
              "enum": [
                "CREATED",
                "IN_TRANSIT",
                "DONE"
              ]
            },
            "in": "query"
          },
          {
            "name": "include_deleted",
            "required": false,
            "description": "Soft-deleted data is excluded from result set by default. Set to true to include it.",
            "schema": {
              "type": "boolean"
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
          },
          {
            "name": "created_at_min",
            "required": false,
            "description": "Minimum value for created_at range. Must be compatible with ISO 8601 format",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "created_at_max",
            "required": false,
            "description": "Maximum value for created_at range. Must be compatible with ISO 8601 format",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "updated_at_min",
            "required": false,
            "description": "Minimum value for updated_at range. Must be compatible with ISO 8601 format",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "updated_at_max",
            "required": false,
            "description": "Maximum value for updated_at range. Must be compatible with ISO 8601 format",
            "schema": {
              "type": "string"
            },
            "in": "query"
          }
        ],
        "responses": {
          "200": {
            "description": "List of bin transfers",
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
                "example": {
                  "data": [
                    {
                      "id": 1,
                      "bin_transfer_number": "BT-1",
                      "location_id": 1,
                      "status": "CREATED",
                      "created_date": "2026-05-22T10:00:00.000Z",
                      "departed_at": null,
                      "arrived_at": null,
                      "additional_info": "urgent transfer",
                      "bin_transfer_rows": [
                        {
                          "id": 11,
                          "bin_transfer_id": 1,
                          "location_id": 1,
                          "variant_id": 42,
                          "quantity": "3",
                          "source_bin_location_id": 7,
                          "target_bin_location_id": 9,
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
                        },
                        {
                          "id": 12,
                          "bin_transfer_id": 1,
                          "location_id": 1,
                          "variant_id": 43,
                          "quantity": "1",
                          "source_bin_location_id": 7,
                          "target_bin_location_id": 9,
                          "traceability": [
                            {
                              "batch_id": null,
                              "serial_number_id": 500,
                              "quantity": "1"
                            }
                          ],
                          "created_at": "2026-05-22T10:00:00.000Z",
                          "updated_at": "2026-05-22T10:00:00.000Z",
                          "deleted_at": null
                        }
                      ],
                      "created_at": "2026-05-22T10:00:00.000Z",
                      "updated_at": "2026-05-22T10:00:00.000Z",
                      "deleted_at": null
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