> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Update a sales order row

Updates the specified sales order row by setting the values of the parameters passed.
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
    "/sales_order_rows/{id}": {
      "patch": {
        "summary": "Update a sales order row",
        "tags": [
          "Sales order row"
        ],
        "description": "Updates the specified sales order row by setting the values of the parameters passed.\n  Any parameters not provided will be left unchanged.",
        "operationId": "updateSalesOrderRow",
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "Sales order row id",
            "schema": {
              "type": "integer"
            },
            "in": "path"
          }
        ],
        "requestBody": {
          "required": true,
          "description": "sales order row fields to be updated with new values",
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "quantity": {
                    "type": "number",
                    "maximum": 100000000000000000,
                    "description": "Updatable only when sales order row status is NOT_SHIPPED or PENDING."
                  },
                  "variant_id": {
                    "type": "integer",
                    "description": "Updatable only when sales order row status is NOT_SHIPPED or PENDING."
                  },
                  "tax_rate_id": {
                    "type": "integer",
                    "description": "Updatable only when sales order row status is NOT_SHIPPED or PENDING."
                  },
                  "location_id": {
                    "type": "integer",
                    "description": "Updatable only when sales order row status is NOT_SHIPPED or PENDING and sales order row is not linked to a manufacturing order (linked_manufacturing_order_id is null)."
                  },
                  "price_per_unit": {
                    "type": "number",
                    "maximum": 1000000000000000000,
                    "description": "Updatable only when sales order row status is NOT_SHIPPED or PENDING."
                  },
                  "total_discount": {
                    "type": "number",
                    "maximum": 1000000000000000000,
                    "description": "Updatable only when sales order row status is NOT_SHIPPED or PENDING."
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
                          "type": "integer"
                        }
                      }
                    }
                  },
                  "serial_number_transactions": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "quantity": {
                          "maximum": 1,
                          "minimum": 0,
                          "type": "number"
                        },
                        "serial_number_id": {
                          "type": "integer"
                        }
                      }
                    }
                  },
                  "attributes": {
                    "type": "array",
                    "description": "When updating attributes, all keys and values must be provided.\n      Existing ones are replaced with new attributes.",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "key": {
                          "type": "string"
                        },
                        "value": {
                          "type": "string"
                        }
                      }
                    }
                  },
                  "custom_fields": {
                    "type": "object",
                    "nullable": true,
                    "additionalProperties": true,
                    "description": "_Behind feature flag — contact support@katanamrp.com to enable._ Custom field values keyed by custom field definition ID (UUID). Each value matches the definition’s `field_type` — string for `shortText`/`url`, number for `number`, boolean for `boolean`, `YYYY-MM-DD` string for `date`, or the integer choice `id` for `singleSelect`. Merged with existing values — omit a key to leave it unchanged. Set the whole field to `null` to clear every custom field value on this row."
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Sales order row updated",
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
                  "sales_order_id": 1,
                  "id": 1,
                  "quantity": 2,
                  "variant_id": 1,
                  "tax_rate_id": 1,
                  "location_id": 1,
                  "price_per_unit": 150,
                  "total_discount": "10.00",
                  "created_at": "2020-10-23T10:37:05.085Z",
                  "updated_at": "2020-10-23T10:37:05.085Z",
                  "deleted_at": null,
                  "linked_manufacturing_order_id": 1,
                  "attributes": [
                    {
                      "key": "key",
                      "value": "value"
                    }
                  ],
                  "batch_transactions": [
                    {
                      "batch_id": 1,
                      "quantity": 10
                    }
                  ],
                  "serial_numbers": [
                    1
                  ],
                  "custom_fields": {
                    "37460d24-ea57-416d-888e-bea7c0505642": "note for picker"
                  }
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