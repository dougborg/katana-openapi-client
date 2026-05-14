# Create a sales order fulfillment

Creates a new fulfillment for an existing sales order.

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
    "/sales_order_fulfillments": {
      "post": {
        "summary": "Create a sales order fulfillment",
        "tags": [
          "Sales order fulfillment"
        ],
        "description": "Creates a new fulfillment for an existing sales order.",
        "operationId": "createSalesOrderFulfillment",
        "requestBody": {
          "description": "new sales order fulfillment details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "sales_order_id",
                  "status"
                ],
                "properties": {
                  "sales_order_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
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
                    "maximum": 1000000000000
                  },
                  "conversion_date": {
                    "type": "string"
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
                    "type": "string"
                  },
                  "tracking_method": {
                    "type": "string"
                  },
                  "sales_order_fulfillment_rows": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "sales_order_row_id",
                        "quantity"
                      ],
                      "properties": {
                        "sales_order_row_id": {
                          "type": "integer",
                          "maximum": 2147483647
                        },
                        "quantity": {
                          "type": "number",
                          "maximum": 100000000000000000
                        },
                        "batch_transactions": {
                          "type": "array",
                          "minItems": 1,
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
                                "description": "ID of the batch. Use `null` to record unbatched (untraced) stock."
                              },
                              "quantity": {
                                "type": "number",
                                "maximum": 100000000000000000
                              }
                            }
                          }
                        },
                        "serial_numbers": {
                          "type": "array",
                          "items": {
                            "type": "number"
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
            "description": "New sales order fulfillment created",
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
                  "sales_order_fulfillment_rows": [
                    {
                      "id": 70550671,
                      "sales_order_row_id": 1,
                      "quantity": 2,
                      "batch_transactions": [
                        {
                          "batch_id": 1,
                          "quantity": 2
                        }
                      ],
                      "serial_numbers": [
                        1
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