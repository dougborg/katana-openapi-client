> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Assign serial numbers to a resource

Assigns the provided list of serial numbers to the specified resource.

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
    "/serial_numbers": {
      "post": {
        "summary": "Assign serial numbers to a resource",
        "tags": [
          "Serial number"
        ],
        "description": "Assigns the provided list of serial numbers to the specified resource.",
        "operationId": "createSerialNumbers",
        "requestBody": {
          "description": "new serial numbers",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "resource_type",
                  "resource_id",
                  "serial_numbers"
                ],
                "properties": {
                  "resource_type": {
                    "type": "string",
                    "enum": [
                      "ManufacturingOrder",
                      "Production",
                      "StockAdjustmentRow",
                      "StockTransferRow",
                      "PurchaseOrderRow",
                      "SalesOrderRow"
                    ]
                  },
                  "resource_id": {
                    "type": "integer"
                  },
                  "serial_numbers": {
                    "type": "array",
                    "items": {
                      "type": "string",
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
            "description": "Assigned serial numbers",
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
                  "failed": [
                    {
                      "reason": "NOT_IN_STOCK",
                      "serial_number": "SN2"
                    }
                  ],
                  "successful": [
                    {
                      "id": 1,
                      "transaction_id": "eb4da756-0842-4495-9118-f8135f681234",
                      "serial_number": "SN1",
                      "resource_type": "ManufacturingOrder",
                      "resource_id": 2,
                      "transaction_date": "2020-10-23T10:37:05.085Z",
                      "quantity_change": 1
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