---
updatedAt: 2026-05-29T09:20:09.000Z
agentTools:
  projectIndex: https://developer.katanamrp.com/llms.txt
---

# Update a customer

Updates the specified customer by setting the values of the parameters passed.
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
    "/customers/{id}": {
      "patch": {
        "summary": "Update a customer",
        "tags": [
          "Customer"
        ],
        "description": "Updates the specified customer by setting the values of the parameters passed.\n    Any parameters not provided will be left unchanged.",
        "operationId": "updateCustomer",
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "Customer id",
            "schema": {
              "type": "integer"
            },
            "in": "path"
          }
        ],
        "requestBody": {
          "description": "Customer details",
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
                  "default_shipping_id": {
                    "type": "integer"
                  },
                  "custom_fields": {
                    "type": "object",
                    "nullable": true,
                    "additionalProperties": true,
                    "description": "_Behind feature flag — contact support@katanamrp.com to enable._ Custom field values keyed by custom field definition ID (UUID) of a definition with `entity_type` `Customer`. Each value matches the definition’s `field_type` — string for `shortText`/`url`, number for `number`, boolean for `boolean`, `YYYY-MM-DD` string for `date`, or the integer choice `id` for `singleSelect`. Merged with existing values — omit a key to leave it unchanged. Set the whole field to `null` to clear every custom field value on this customer. Unknown definition IDs are rejected with a 422."
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Customer updated",
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
                  "custom_fields": {
                    "37460d24-ea57-416d-888e-bea7c0505642": "VIP",
                    "6afe78d2-2b95-4d71-92f5-1bc2be852afe": 5
                  },
                  "created_at": "2020-10-23T10:37:05.085Z",
                  "updated_at": "2020-10-23T10:37:05.085Z",
                  "deleted_at": null,
                  "default_billing_id": 1,
                  "default_shipping_id": 2
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