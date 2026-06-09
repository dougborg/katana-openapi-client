> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Retrieve a manufacturing order production

Retrieves the details of an existing manufacturing order production based on ID.

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
    "/manufacturing_order_productions/{id}": {
      "get": {
        "summary": "Retrieve a manufacturing order production",
        "tags": [
          "Manufacturing order production"
        ],
        "description": "Retrieves the details of an existing manufacturing order production based on ID.",
        "operationId": "getManufacturingOrderProduction",
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "Manufacturing order production id",
            "schema": {
              "type": "integer"
            },
            "in": "path"
          }
        ],
        "responses": {
          "200": {
            "description": "Manufacturing order production",
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