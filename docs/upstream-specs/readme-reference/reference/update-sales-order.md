# Update a sales order

Updates the specified sales order by setting the values of the parameters passed.
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
    "/sales_orders/{id}": {
      "patch": {
        "summary": "Update a sales order",
        "tags": [
          "Sales order"
        ],
        "description": "Updates the specified sales order by setting the values of the parameters passed.\n  Any parameters not provided will be left unchanged. ",
        "operationId": "updateSalesOrder",
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "Sales order id",
            "schema": {
              "type": "integer"
            },
            "in": "path"
          }
        ],
        "requestBody": {
          "description": "sales order fields to be updated with new values",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "order_no": {
                    "type": "string",
                    "description": "Updatable only when sales order status is NOT_SHIPPED or PENDING.",
                    "minLength": 1
                  },
                  "customer_id": {
                    "type": "integer",
                    "description": "Updatable only when sales order status is NOT_SHIPPED or PENDING.",
                    "maximum": 2147483647
                  },
                  "order_created_date": {
                    "type": "string"
                  },
                  "delivery_date": {
                    "type": "string",
                    "description": "Updatable only when sales order status is NOT_SHIPPED or PENDING."
                  },
                  "picked_date": {
                    "type": "string",
                    "description": "Updatable only when sales order status is NOT_SHIPPED or PENDING."
                  },
                  "location_id": {
                    "type": "integer",
                    "description": "Updatable only when sales order status is NOT_SHIPPED or PENDING.",
                    "maximum": 2147483647
                  },
                  "status": {
                    "type": "string",
                    "description": "When the status is omitted, NOT_SHIPPED is used as default.\n        Use PENDING when you want to create sales order quotes.",
                    "enum": [
                      "NOT_SHIPPED",
                      "PENDING",
                      "PACKED",
                      "DELIVERED"
                    ]
                  },
                  "currency": {
                    "description": "E.g. USD, EUR. All currently active currency codes in ISO 4217 format.\n        Updatable only when sales order status is NOT_SHIPPED or PENDING.",
                    "type": "string"
                  },
                  "conversion_rate": {
                    "description": "Updatable only when sales order status is PACKED or DELIVERED, otherwise it will fail with 422.",
                    "type": "number"
                  },
                  "conversion_date": {
                    "description": "Updatable only when sales order status is PACKED or DELIVERED, otherwise it will fail with 422.",
                    "type": "string"
                  },
                  "additional_info": {
                    "type": "string",
                    "nullable": true
                  },
                  "customer_ref": {
                    "type": "string",
                    "maxLength": 255,
                    "nullable": true
                  },
                  "tracking_number": {
                    "type": "string",
                    "maxLength": 256,
                    "nullable": true
                  },
                  "tracking_number_url": {
                    "type": "string",
                    "maxLength": 2048,
                    "nullable": true
                  },
                  "custom_fields": {
                    "type": "object",
                    "nullable": true,
                    "additionalProperties": true,
                    "description": "_Behind feature flag — contact support@katanamrp.com to enable._ Custom field values keyed by custom field definition ID (UUID). Each value matches the definition’s `field_type` — string for `shortText`/`url`, number for `number`, boolean for `boolean`, `YYYY-MM-DD` string for `date`, or the integer choice `id` for `singleSelect`. Merged with existing values — omit a key to leave it unchanged. Set the whole field to `null` to clear every custom field value on this sales order."
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Sales order updated",
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
                  "customer_id": 1,
                  "order_no": "SO-3",
                  "source": "API",
                  "order_created_date": "2020-10-23T10:37:05.085Z",
                  "delivery_date": "2020-10-23T10:37:05.085Z",
                  "location_id": 1,
                  "status": "NOT_SHIPPED",
                  "currency": "USD",
                  "conversion_rate": 0.7,
                  "conversion_date": "2020-10-23T10:37:05.085Z",
                  "product_availability": "IN_STOCK",
                  "ingredient_availability": "PROCESSED",
                  "production_status": "DONE",
                  "invoicing_status": "invoiced",
                  "additional_info": "additional info",
                  "customer_ref": "my customer reference",
                  "picked_date": "2020-10-23T10:37:05.085Z",
                  "ecommerce_order_type": "shopify",
                  "ecommerce_store_name": "katana.myshopify.com",
                  "ecommerce_order_id": "19433769",
                  "tracking_number": "12345678",
                  "tracking_number_url": "https://tracking-number-url",
                  "custom_fields": {
                    "37460d24-ea57-416d-888e-bea7c0505642": "PO-1234",
                    "6afe78d2-2b95-4d71-92f5-1bc2be852afe": 5
                  },
                  "billing_address_id": 1234,
                  "shipping_address_id": 1235,
                  "linked_manufacturing_order_id": 1,
                  "addresses": [
                    {
                      "id": 1234,
                      "sales_order_id": 12345,
                      "entity_type": "billing",
                      "first_name": "Luke",
                      "last_name": "Skywalker",
                      "company": "Company",
                      "phone": "123456",
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
                      "id": 1235,
                      "sales_order_id": 12345,
                      "entity_type": "shipping",
                      "first_name": "Luke",
                      "last_name": "Skywalker",
                      "company": "Company",
                      "phone": "123456",
                      "line_1": "Line 1",
                      "line_2": "Line 2",
                      "city": "City",
                      "state": "State",
                      "zip": "Zip",
                      "country": "Country",
                      "updated_at": "2020-10-23T10:37:05.085Z",
                      "created_at": "2020-10-23T10:37:05.085Z"
                    }
                  ],
                  "created_at": "2020-10-23T10:37:05.085Z",
                  "updated_at": "2020-10-23T10:37:05.085Z",
                  "deleted_at": null
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