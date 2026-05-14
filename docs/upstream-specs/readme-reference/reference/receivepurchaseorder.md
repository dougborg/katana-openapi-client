# Receive a purchase order

If you receive the items on the purchase order, you can mark the purchase order as received.
    This will update the existing purchase order rows quantities to the quantities left unreceived and
    create a new rows with the received quantities and dates. If you want to mark all rows as received and
    the order doesn’t contain batch tracked items, you can use PATCH /purchase_orders/id endpoint.
    Reverting the receive must also be done through that endpoint.

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
    "/purchase_order_receive": {
      "post": {
        "summary": "Receive a purchase order",
        "tags": [
          "Purchase order"
        ],
        "description": "If you receive the items on the purchase order, you can mark the purchase order as received.\n    This will update the existing purchase order rows quantities to the quantities left unreceived and\n    create a new rows with the received quantities and dates. If you want to mark all rows as received and\n    the order doesn’t contain batch tracked items, you can use PATCH /purchase_orders/id endpoint.\n    Reverting the receive must also be done through that endpoint.",
        "operationId": "receivePurchaseOrder",
        "requestBody": {
          "description": "receive purchase order rows details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "anyOf": [
                  {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "quantity",
                        "purchase_order_row_id"
                      ],
                      "properties": {
                        "purchase_order_row_id": {
                          "type": "integer",
                          "maximum": 2147483647
                        },
                        "quantity": {
                          "type": "number",
                          "maximum": 100000000000000000
                        },
                        "received_date": {
                          "type": "string"
                        },
                        "batch_transactions": {
                          "type": "array",
                          "items": {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "quantity": {
                                "maximum": 100000000000000000,
                                "type": "number"
                              },
                              "batch_id": {
                                "type": "integer",
                                "nullable": true,
                                "description": "ID of the batch to receive stock for. Use `null` to record unbatched (untraced) stock."
                              }
                            }
                          }
                        }
                      }
                    },
                    "title": "Multiple rows",
                    "minItems": 1
                  },
                  {
                    "type": "object",
                    "additionalProperties": false,
                    "required": [
                      "quantity",
                      "purchase_order_row_id"
                    ],
                    "properties": {
                      "purchase_order_row_id": {
                        "type": "integer",
                        "maximum": 2147483647
                      },
                      "quantity": {
                        "type": "number",
                        "maximum": 100000000000000000
                      },
                      "received_date": {
                        "type": "string"
                      },
                      "batch_transactions": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "additionalProperties": false,
                          "properties": {
                            "quantity": {
                              "maximum": 100000000000000000,
                              "type": "number"
                            },
                            "batch_id": {
                              "type": "integer",
                              "nullable": true,
                              "description": "ID of the batch to receive stock for. Use `null` to record unbatched (untraced) stock."
                            }
                          }
                        }
                      }
                    },
                    "title": "Single row"
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "204": {
            "description": "Receive purchase order rows",
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