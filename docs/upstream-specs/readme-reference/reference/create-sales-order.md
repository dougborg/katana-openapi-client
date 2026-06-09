> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Create a sales order

Creates a new sales order object.

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
    "/sales_orders": {
      "post": {
        "summary": "Create a sales order",
        "tags": [
          "Sales order"
        ],
        "description": "Creates a new sales order object.",
        "operationId": "createSalesOrder",
        "requestBody": {
          "description": "new sales order details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "customer_id",
                  "sales_order_rows"
                ],
                "properties": {
                  "order_no": {
                    "type": "string"
                  },
                  "customer_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "sales_order_rows": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "quantity",
                        "variant_id"
                      ],
                      "properties": {
                        "quantity": {
                          "type": "number",
                          "maximum": 100000000000000000
                        },
                        "variant_id": {
                          "type": "integer",
                          "maximum": 2147483647
                        },
                        "tax_rate_id": {
                          "type": "integer",
                          "maximum": 2147483647
                        },
                        "location_id": {
                          "type": "integer",
                          "maximum": 2147483647
                        },
                        "attributes": {
                          "type": "array",
                          "items": {
                            "type": "object",
                            "additionalProperties": false,
                            "required": [
                              "key",
                              "value"
                            ],
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
                        "price_per_unit": {
                          "type": "number",
                          "maximum": 1000000000000000000
                        },
                        "total_discount": {
                          "type": "number",
                          "maximum": 1000000000000000000
                        }
                      }
                    }
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
                  },
                  "order_created_date": {
                    "type": "string"
                  },
                  "delivery_date": {
                    "type": "string"
                  },
                  "currency": {
                    "description": "E.g. USD, EUR. All currently active currency codes in ISO 4217 format.",
                    "type": "string"
                  },
                  "location_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "status": {
                    "type": "string",
                    "enum": [
                      "NOT_SHIPPED",
                      "PENDING"
                    ],
                    "description": "When the status is omitted, NOT_SHIPPED is used as default.\n        Use PENDING when you want to create sales order quotes."
                  },
                  "additional_info": {
                    "type": "string"
                  },
                  "customer_ref": {
                    "type": "string",
                    "maxLength": 255,
                    "nullable": true
                  },
                  "ecommerce_order_type": {
                    "type": "string"
                  },
                  "ecommerce_store_name": {
                    "type": "string"
                  },
                  "ecommerce_order_id": {
                    "type": "string"
                  },
                  "custom_fields": {
                    "type": "object",
                    "nullable": true,
                    "additionalProperties": true,
                    "description": "_Behind feature flag — contact support@katanamrp.com to enable._ Custom field values keyed by custom field definition ID (UUID). Each value matches the definition’s `field_type` — string for `shortText`/`url`, number for `number`, boolean for `boolean`, `YYYY-MM-DD` string for `date`, or the integer choice `id` for `singleSelect`."
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "New sales order created",
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
                  "picked_date": null,
                  "status": "NOT_SHIPPED",
                  "currency": "USD",
                  "conversion_rate": 2,
                  "total": 300,
                  "total_in_base_currency": 150,
                  "conversion_date": "2020-10-23T10:37:05.085Z",
                  "product_availability": "IN_STOCK",
                  "ingredient_availability": "PROCESSED",
                  "production_status": "DONE",
                  "invoicing_status": "invoiced",
                  "additional_info": "additional info",
                  "customer_ref": "my customer reference",
                  "ecommerce_order_type": "shopify",
                  "ecommerce_store_name": "katana.myshopify.com",
                  "ecommerce_order_id": "19433769",
                  "created_at": "2020-10-23T10:37:05.085Z",
                  "updated_at": "2020-10-23T10:37:05.085Z",
                  "deleted_at": null,
                  "sales_order_rows": [
                    {
                      "sales_order_id": 1,
                      "id": 1,
                      "quantity": 2,
                      "variant_id": 1,
                      "tax_rate_id": 1,
                      "location_id": 1,
                      "price_per_unit": 150,
                      "total": 300,
                      "total_in_base_currency": 150,
                      "conversion_rate": null,
                      "conversion_date": null,
                      "created_at": "2020-10-23T10:37:05.085Z",
                      "updated_at": "2020-10-23T10:37:05.085Z",
                      "attributes": [
                        {
                          "key": "key",
                          "value": "value"
                        }
                      ],
                      "batch_transactions": []
                    }
                  ],
                  "tracking_number": "12345678",
                  "tracking_number_url": "https://tracking-number-url",
                  "custom_fields": {
                    "37460d24-ea57-416d-888e-bea7c0505642": "PO-1234",
                    "6afe78d2-2b95-4d71-92f5-1bc2be852afe": 5
                  },
                  "billing_address_id": 1234,
                  "shipping_address_id": 1235,
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