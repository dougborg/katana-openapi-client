> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# List all sales order addresses

Returns a list of sales order addresses you’ve previously created.
   The sales order addresses are returned in sorted order, with the most recent sales order addresses appearing first.

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
    "/sales_order_addresses": {
      "get": {
        "summary": "List all sales order addresses",
        "tags": [
          "Sales order address"
        ],
        "description": "Returns a list of sales order addresses you’ve previously created.\n   The sales order addresses are returned in sorted order, with the most recent sales order addresses appearing first.",
        "operationId": "getSalesOrderAddresses",
        "parameters": [
          {
            "name": "ids",
            "required": false,
            "description": "Filters sales order addresses by an array of IDs",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer"
              }
            },
            "in": "query"
          },
          {
            "name": "sales_order_ids",
            "required": false,
            "description": "Filters sales order addresses by an array of sales order IDs",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer"
              }
            },
            "in": "query"
          },
          {
            "name": "entity_type",
            "required": false,
            "description": "Filters sales order addresses by a entity_type",
            "schema": {
              "enum": [
                "billing",
                "shipping"
              ]
            },
            "in": "query"
          },
          {
            "name": "first_name",
            "required": false,
            "description": "Filters sales order addresses by a first_name",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "last_name",
            "required": false,
            "description": "Filters sales order addresses by a last_name",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "company",
            "required": false,
            "description": "Filters sales order addresses by an company",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "line_1",
            "required": false,
            "description": "Filters sales order addresses by a line_1",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "line_2",
            "required": false,
            "description": "Filters sales order addresses by a line_2",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "city",
            "required": false,
            "description": "Filters sales order addresses by a city",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "state",
            "required": false,
            "description": "Filters sales order addresses by a state",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "zip",
            "required": false,
            "description": "Filters sales order addresses by a zip",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "country",
            "required": false,
            "description": "Filters sales order addresses by a country",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "phone",
            "required": false,
            "description": "Filters sales order addresses by a phone",
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
            "description": "List all sales order addresses",
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
                      "id": 2,
                      "sales_order_id": 12345,
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
                      "created_at": "2020-10-23T10:37:05.085Z",
                      "deleted_at": null
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