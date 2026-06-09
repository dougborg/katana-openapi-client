> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Create price list rows

Add variants to a price list.

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
    "/price_list_rows": {
      "post": {
        "summary": "Create price list rows",
        "tags": [
          "Price list rows"
        ],
        "description": "Add variants to a price list.",
        "operationId": "createPriceListRow",
        "requestBody": {
          "description": "new price list rows details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "price_list_id",
                  "price_list_rows"
                ],
                "properties": {
                  "price_list_id": {
                    "type": "number",
                    "description": "ID of the price list where the rows will be added",
                    "example": 2
                  },
                  "price_list_rows": {
                    "type": "array",
                    "description": "List of price list rows to be added",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "variant_id",
                        "adjustment_method",
                        "amount"
                      ],
                      "properties": {
                        "variant_id": {
                          "type": "number",
                          "description": "ID of the variant"
                        },
                        "adjustment_method": {
                          "type": "number",
                          "description": "Adjustment method for the price list row",
                          "enum": [
                            "fixed",
                            "percentage",
                            "markup"
                          ]
                        },
                        "amount": {
                          "type": "number",
                          "description": "Amount to be applied as discount or replaced price"
                        }
                      }
                    }
                  }
                },
                "example": {
                  "price_list_id": 2,
                  "price_list_rows": [
                    {
                      "variant_id": 223,
                      "adjustment_method": "fixed",
                      "amount": 5
                    },
                    {
                      "variant_id": 224,
                      "adjustment_method": "percentage",
                      "amount": 50
                    }
                  ]
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "New price list row created",
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
                "example": [
                  {
                    "id": 6,
                    "price_list_id": 2,
                    "variant_id": 223,
                    "adjustment_method": "fixed",
                    "amount": 5,
                    "created_at": "2024-06-25T08:53:38.864Z",
                    "updated_at": "2024-06-25T08:53:38.864Z"
                  },
                  {
                    "id": 7,
                    "price_list_id": 2,
                    "variant_id": 224,
                    "adjustment_method": "percentage",
                    "amount": 50,
                    "created_at": "2024-06-25T08:53:38.864Z",
                    "updated_at": "2024-06-25T08:53:38.864Z"
                  },
                  {
                    "id": 8,
                    "price_list_id": 2,
                    "variant_id": 225,
                    "adjustment_method": "markup",
                    "amount": 10,
                    "created_at": "2024-06-25T08:53:38.864Z",
                    "updated_at": "2024-06-25T08:53:38.864Z"
                  }
                ]
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