> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Update a sales order fulfillment

Updates the specified sales order fulfillment by setting the values of the parameters passed.
  Any parameters not provided will be left unchanged.

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
    "/sales_order_fulfillments/{id}": {
      "patch": {
        "summary": "Update a sales order fulfillment",
        "tags": [
          "Sales order fulfillment"
        ],
        "description": "Updates the specified sales order fulfillment by setting the values of the parameters passed.\n  Any parameters not provided will be left unchanged.",
        "operationId": "updateSalesOrderFulfillment",
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "Sales order fulfillment id",
            "schema": {
              "type": "integer"
            },
            "in": "path"
          }
        ],
        "requestBody": {
          "description": "sales order fulfillment fields to be updated with new values",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "picked_date": {
                    "type": "string"
                  },
                  "status": {
                    "type": "string",
                    "enum": [
                      "DELIVERED",
                      "PACKED"
                    ]
                  },
                  "conversion_rate": {
                    "type": "number",
                    "maximum": 1000000000000,
                    "nullable": true
                  },
                  "packer_id": {
                    "type": "number",
                    "description": "id of the operator who packed this sales order.\n      It is only shown if the factory has Warehouse Management add-on and Pick & Pack feature has been enabled in the settings."
                  },
                  "conversion_date": {
                    "type": "string",
                    "nullable": true
                  },
                  "tracking_number": {
                    "type": "string",
                    "maxLength": 256,
                    "nullable": true
                  },
                  "tracking_url": {
                    "type": "string",
                    "maxLength": 2048,
                    "nullable": true
                  },
                  "tracking_carrier": {
                    "type": "string",
                    "maxLength": 256,
                    "nullable": true
                  },
                  "tracking_method": {
                    "type": "string",
                    "maxLength": 2048,
                    "nullable": true
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Sales order fulfillment updated",
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
                  "sales_order_id": 1,
                  "picked_date": "2020-10-23T10:37:05.085Z",
                  "status": "DELIVERED",
                  "conversion_rate": 2,
                  "conversion_date": "2020-10-23T10:37:05.085Z",
                  "tracking_number": "12345678",
                  "tracking_url": "https://tracking-number-url",
                  "tracking_carrier": "UPS",
                  "tracking_method": "ground",
                  "packer_id": 1,
                  "sales_order_fulfillment_rows": [
                    {
                      "sales_order_row_id": 1,
                      "quantity": 2,
                      "batch_transactions": [
                        {
                          "batch_id": 1,
                          "quantity": 2
                        }
                      ]
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