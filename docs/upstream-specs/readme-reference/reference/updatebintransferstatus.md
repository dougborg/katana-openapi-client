> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Transition a bin transfer status

Transitions a bin transfer status. Any status is reachable from any other; the transition stamps or
clears the corresponding movement dates on the transfer and every row.

| From         | To           | Effect                                                              |
|--------------|--------------|---------------------------------------------------------------------|
| `CREATED`    | `IN_TRANSIT` | Stamps `departed_at` = now.                                         |
| `CREATED`    | `DONE`       | Stamps `departed_at` = now and `arrived_at` = now.                  |
| `IN_TRANSIT` | `DONE`       | Stamps `arrived_at` = now.                                          |
| `IN_TRANSIT` | `CREATED`    | Clears `departed_at`.                                               |
| `DONE`       | `IN_TRANSIT` | Clears `arrived_at`.                                                |
| `DONE`       | `CREATED`    | Clears both `departed_at` and `arrived_at`.                         |

Submitting the current status is a no-op (200 with the unchanged transfer). Stamped or cleared
timestamps must fall outside any inventory lock date window, otherwise 422.

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
    "/bin_transfers/{id}/status": {
      "patch": {
        "summary": "Transition a bin transfer status",
        "tags": [
          "Bin transfer"
        ],
        "description": "Transitions a bin transfer status. Any status is reachable from any other; the transition stamps or\nclears the corresponding movement dates on the transfer and every row.\n\n| From         | To           | Effect                                                              |\n|--------------|--------------|---------------------------------------------------------------------|\n| `CREATED`    | `IN_TRANSIT` | Stamps `departed_at` = now.                                         |\n| `CREATED`    | `DONE`       | Stamps `departed_at` = now and `arrived_at` = now.                  |\n| `IN_TRANSIT` | `DONE`       | Stamps `arrived_at` = now.                                          |\n| `IN_TRANSIT` | `CREATED`    | Clears `departed_at`.                                               |\n| `DONE`       | `IN_TRANSIT` | Clears `arrived_at`.                                                |\n| `DONE`       | `CREATED`    | Clears both `departed_at` and `arrived_at`.                         |\n\nSubmitting the current status is a no-op (200 with the unchanged transfer). Stamped or cleared\ntimestamps must fall outside any inventory lock date window, otherwise 422.",
        "operationId": "updateBinTransferStatus",
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "Bin transfer id",
            "schema": {
              "type": "integer"
            },
            "in": "path"
          }
        ],
        "requestBody": {
          "description": "target status",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "status"
                ],
                "properties": {
                  "status": {
                    "type": "string",
                    "enum": [
                      "CREATED",
                      "IN_TRANSIT",
                      "DONE"
                    ],
                    "description": "Target status."
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Bin transfer status updated",
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
                  "bin_transfer_number": "BT-1",
                  "location_id": 1,
                  "status": "IN_TRANSIT",
                  "created_date": "2026-05-22T10:00:00.000Z",
                  "departed_at": "2026-05-22T11:00:00.000Z",
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
          "404": {
            "description": "Make sure data is correct",
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
                  "statusCode": 404,
                  "name": "NotFoundError",
                  "message": "Not found"
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