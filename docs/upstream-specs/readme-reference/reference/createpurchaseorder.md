> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Create a purchase order

Creates a new purchase order object.

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
    "/purchase_orders": {
      "post": {
        "summary": "Create a purchase order",
        "tags": [
          "Purchase order"
        ],
        "description": "Creates a new purchase order object.",
        "operationId": "createPurchaseOrder",
        "requestBody": {
          "description": "new purchase order details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "supplier_id",
                  "location_id",
                  "purchase_order_rows"
                ],
                "properties": {
                  "order_no": {
                    "type": "string"
                  },
                  "entity_type": {
                    "type": "string",
                    "enum": [
                      "regular",
                      "outsourced"
                    ]
                  },
                  "supplier_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "currency": {
                    "description": "E.g. USD, EUR. All currently active currency codes in ISO 4217 format.",
                    "type": "string"
                  },
                  "status": {
                    "type": "string",
                    "enum": [
                      "DRAFT",
                      "NOT_RECEIVED"
                    ]
                  },
                  "expected_arrival_date": {
                    "type": "string"
                  },
                  "order_created_date": {
                    "type": "string"
                  },
                  "location_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "tracking_location_id": {
                    "type": "integer",
                    "maximum": 2147483647,
                    "description": "Submittable only when entity_type is outsourced"
                  },
                  "additional_info": {
                    "type": "string"
                  },
                  "purchase_order_rows": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "quantity",
                        "variant_id",
                        "price_per_unit"
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
                        "price_per_unit": {
                          "type": "number",
                          "maximum": 100000000000000000,
                          "minimum": 0
                        },
                        "purchase_uom_conversion_rate": {
                          "type": "number",
                          "maximum": 100000000000000000,
                          "minimum": 0
                        },
                        "purchase_uom": {
                          "type": "string",
                          "maxLength": 7
                        },
                        "arrival_date": {
                          "type": "string"
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
            "description": "New purchase order",
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
                  "status": "NOT_RECEIVED",
                  "billing_status": "NOT_BILLED",
                  "last_document_status": "NOT_SENT",
                  "order_no": "PO-1",
                  "entity_type": "regular",
                  "default_group_id": 9,
                  "supplier_id": 1,
                  "currency": "USD",
                  "expected_arrival_date": "2021-10-13T15:31:48.490Z",
                  "order_created_date": "2021-10-13T15:31:48.490Z",
                  "additional_info": "Please unpack",
                  "location_id": 1,
                  "tracking_location_id": null,
                  "total": 1,
                  "total_in_base_currency": 1,
                  "created_at": "2021-02-03T13:13:07.110Z",
                  "updated_at": "2021-02-03T13:13:07.110Z",
                  "deleted_at": null,
                  "purchase_order_rows": [
                    {
                      "id": 1,
                      "quantity": 1,
                      "variant_id": 1,
                      "tax_rate_id": 1,
                      "price_per_unit": 1.5,
                      "purchase_uom_conversion_rate": 1.1,
                      "purchase_uom": "cm",
                      "created_at": "2021-02-03T13:13:07.121Z",
                      "updated_at": "2021-02-03T13:13:07.121Z",
                      "deleted_at": null,
                      "batch_transactions": [],
                      "currency": "USD",
                      "conversion_rate": null,
                      "conversion_date": null,
                      "received_date": "2021-02-03T13:13:07.000Z",
                      "purchase_order_id": 1,
                      "total": 1,
                      "total_in_base_currency": 1,
                      "landed_cost": "45.0000000000",
                      "group_id": 11
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