---
updatedAt: 2026-05-29T09:20:09.000Z
---

Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

# Retrieve a manufacturing order operation row

Retrieves the details of an existing manufacturing order operation row.

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
    "/manufacturing_order_operation_rows/{id}": {
      "get": {
        "summary": "Retrieve a manufacturing order operation row",
        "tags": [
          "Manufacturing order operation"
        ],
        "description": "Retrieves the details of an existing manufacturing order operation row.",
        "operationId": "getManufacturingOrderOperationRow",
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "Manufacturing order operaton row id",
            "schema": {
              "type": "number"
            },
            "in": "path"
          }
        ],
        "responses": {
          "200": {
            "description": "Manufacturing order operation row",
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
                  "moOperationRowResponseExample": {
                    "id": 1,
                    "status": "IN_PROGRESS",
                    "type": "process",
                    "rank": 1,
                    "manufacturing_order_id": 1,
                    "operation_id": 1,
                    "operation_name": "Pack",
                    "resource_id": 1,
                    "resource_name": "Table",
                    "assigned_operators": [
                      {
                        "operator_id": 1,
                        "name": "Pack",
                        "deleted_at": null
                      }
                    ],
                    "completed_by_operators": [],
                    "active_operator_id": 1,
                    "planned_time_per_unit": 1,
                    "planned_time_parameter": 1,
                    "total_actual_time": 1,
                    "planned_cost_per_unit": 1,
                    "total_actual_cost": 1,
                    "cost_per_hour": 1,
                    "cost_parameter": 1,
                    "group_boundary": 1000,
                    "is_status_actionable": true,
                    "custom_fields": {
                      "37460d24-ea57-416d-888e-bea7c0505642": "CNC mill",
                      "6afe78d2-2b95-4d71-92f5-1bc2be852afe": 5
                    },
                    "completed_at": "2020-10-23T10:37:05.085Z",
                    "created_at": "2020-10-23T10:37:05.085Z",
                    "updated_at": "2020-10-23T10:37:05.085Z",
                    "deleted_at": null
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