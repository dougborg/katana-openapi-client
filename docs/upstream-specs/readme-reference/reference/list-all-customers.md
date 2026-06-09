> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# List all customers

Returns a list of customers you’ve previously created. The customers are returned in sorted order,
    with the most recent customers appearing first.

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
      "get": {
        "summary": "List all customers",
        "tags": [
          "Customer"
        ],
        "description": "Returns a list of customers you’ve previously created. The customers are returned in sorted order,\n    with the most recent customers appearing first.",
        "operationId": "getAllCustomers",
        "parameters": [
          {
            "name": "name",
            "required": false,
            "description": "Filters customers by name",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "first_name",
            "required": false,
            "description": "Filters customers by first name",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "last_name",
            "required": false,
            "description": "Filters customers by last name",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "company",
            "required": false,
            "description": "Filters customers by company",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "ids",
            "required": false,
            "description": "Filters customers by an array of IDs",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer"
              }
            },
            "in": "query"
          },
          {
            "name": "email",
            "required": false,
            "description": "Filters customers by an email",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "phone",
            "required": false,
            "description": "Filters customers by a phone number",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "currency",
            "required": false,
            "description": "Filters customers by currency",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "reference_id",
            "required": false,
            "description": "Filters customers by a reference ID",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "category",
            "required": false,
            "description": "Filters customers by a category",
            "schema": {
              "type": "string"
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
            "description": "List of customers",
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
                      "id": 12345,
                      "name": "Luke Skywalker",
                      "first_name": "Luke",
                      "last_name": "Skywalker",
                      "company": "Company",
                      "email": "luke.skywalker@example.com",
                      "comment": "Luke Skywalker was a Tatooine farmboy who rose from humble beginnings to become one of the\n              greatest Jedi the galaxy has ever known.",
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