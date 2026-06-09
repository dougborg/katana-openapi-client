> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Create a customer

Creates a new customer object.

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
    "/customers": {
      "post": {
        "summary": "Create a customer",
        "tags": [
          "Customer"
        ],
        "description": "Creates a new customer object.",
        "operationId": "createCustomer",
        "requestBody": {
          "description": "new customer details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "name"
                ],
                "properties": {
                  "name": {
                    "type": "string"
                  },
                  "first_name": {
                    "type": "string"
                  },
                  "last_name": {
                    "type": "string"
                  },
                  "company": {
                    "type": "string"
                  },
                  "email": {
                    "type": "string"
                  },
                  "phone": {
                    "type": "string"
                  },
                  "currency": {
                    "type": "string",
                    "description": "The customer’s currency (ISO 4217)."
                  },
                  "reference_id": {
                    "type": "string",
                    "maxLength": 100
                  },
                  "category": {
                    "type": "string",
                    "maxLength": 100
                  },
                  "comment": {
                    "type": "string"
                  },
                  "discount_rate": {
                    "type": "number"
                  },
                  "addresses": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "entity_type"
                      ],
                      "properties": {
                        "entity_type": {
                          "type": "string",
                          "enum": [
                            "billing",
                            "shipping"
                          ]
                        },
                        "default": {
                          "type": "boolean"
                        },
                        "first_name": {
                          "type": "string",
                          "nullable": true
                        },
                        "last_name": {
                          "type": "string",
                          "nullable": true
                        },
                        "company": {
                          "type": "string",
                          "nullable": true
                        },
                        "phone": {
                          "type": "string",
                          "nullable": true
                        },
                        "line_1": {
                          "type": "string",
                          "nullable": true
                        },
                        "line_2": {
                          "type": "string",
                          "nullable": true
                        },
                        "city": {
                          "type": "string",
                          "nullable": true
                        },
                        "state": {
                          "type": "string",
                          "nullable": true
                        },
                        "zip": {
                          "type": "string",
                          "nullable": true
                        },
                        "country": {
                          "type": "string",
                          "nullable": true
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
            "description": "new customers created",
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
                  "id": 12345,
                  "name": "Luke Skywalker",
                  "first_name": "Luke",
                  "last_name": "Skywalker",
                  "company": "Company",
                  "email": "luke.skywalker@example.com",
                  "comment": "Luke Skywalker was a Tatooine farmboy who rose from humble beginnings to become one of the\n            greatest Jedi the galaxy has ever known.",
                  "discount_rate": 100,
                  "phone": "123456",
                  "currency": "USD",
                  "reference_id": "ref-12345",
                  "category": "category-12345",
                  "created_at": "2020-10-23T10:37:05.085Z",
                  "updated_at": "2020-10-23T10:37:05.085Z",
                  "deleted_at": null,
                  "default_billing_id": 1,
                  "default_shipping_id": 2,
                  "addresses": [
                    {
                      "id": 1,
                      "customer_id": 12345,
                      "entity_type": "billing",
                      "first_name": "Luke",
                      "last_name": "Skywalker",
                      "company": "Company",
                      "phone": "123456789",
                      "line_1": "Line 1",
                      "line_2": "Line 2",
                      "city": "City",
                      "state": "State",
                      "zip": "Zip",
                      "country": "Country",
                      "updated_at": "2020-10-23T10:37:05.085Z",
                      "created_at": "2020-10-23T10:37:05.085Z"
                    },
                    {
                      "id": 2,
                      "customer_id": 12345,
                      "entity_type": "shipping",
                      "first_name": "Luke",
                      "last_name": "Skywalker",
                      "company": "Company",
                      "phone": "123456789",
                      "line_1": "Line 1",
                      "line_2": "Line 2",
                      "city": "City",
                      "state": "State",
                      "zip": "Zip",
                      "country": "Country",
                      "updated_at": "2020-10-23T10:37:05.085Z",
                      "created_at": "2020-10-23T10:37:05.085Z"
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