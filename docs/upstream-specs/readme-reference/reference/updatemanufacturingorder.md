> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Update a manufacturing order

Updates the specified manufacturing order by setting the values of the parameters passed.
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
    "/manufacturing_orders/{id}": {
      "patch": {
        "summary": "Update a manufacturing order",
        "tags": [
          "Manufacturing order"
        ],
        "description": "Updates the specified manufacturing order by setting the values of the parameters passed.\n  Any parameters not provided will be left unchanged.",
        "operationId": "updateManufacturingOrder",
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "manufacturing order id",
            "schema": {
              "type": "integer"
            },
            "in": "path"
          }
        ],
        "requestBody": {
          "description": "manufacturing order details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "status": {
                    "type": "string",
                    "enum": [
                      "NOT_STARTED",
                      "BLOCKED",
                      "IN_PROGRESS",
                      "DONE"
                    ],
                    "description": "Not updatable when manufacturing order status is DONE and location is deleted\n      or manufacturing_allowed is false."
                  },
                  "order_no": {
                    "type": "string",
                    "description": "Not updatable when manufacturing order status is DONE."
                  },
                  "variant_id": {
                    "type": "number",
                    "description": "Not updatable when manufacturing order status is DONE."
                  },
                  "location_id": {
                    "type": "number",
                    "description": "Not updatable when manufacturing order status is DONE."
                  },
                  "planned_quantity": {
                    "type": "number",
                    "description": "Not updatable when manufacturing order status is DONE."
                  },
                  "actual_quantity": {
                    "type": "number",
                    "description": "Not updatable when manufacturing order status is DONE."
                  },
                  "order_created_date": {
                    "type": "string"
                  },
                  "production_deadline_date": {
                    "type": "string",
                    "description": "Use only if automatic production deadline calculation for the factory location is switched OFF.\n      Not updatable when manufacturing order status is DONE.\n Not updatable when manufacturing order status is DONE."
                  },
                  "additional_info": {
                    "type": "string"
                  },
                  "done_date": {
                    "type": "string"
                  },
                  "batch_transactions": {
                    "type": "array",
                    "description": "Not updatable when manufacturing order status is DONE.",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "quantity": {
                          "maximum": 1000000000000000,
                          "type": "number"
                        },
                        "batch_id": {
                          "type": "integer"
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
            "description": "New manufacturing order",
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
                  "id": 21400,
                  "status": "NOT_STARTED",
                  "order_no": "SO-2 / 1",
                  "variant_id": 1418016,
                  "planned_quantity": 1,
                  "actual_quantity": null,
                  "batch_transactions": [],
                  "location_id": 2327,
                  "order_created_date": "2021-09-01T07:49:29.000Z",
                  "done_date": null,
                  "production_deadline_date": "2021-10-18T08:00:00.000Z",
                  "additional_info": "",
                  "is_linked_to_sales_order": true,
                  "ingredient_availability": "IN_STOCK",
                  "total_cost": 0,
                  "total_actual_time": 0,
                  "total_planned_time": 18000,
                  "sales_order_id": 1,
                  "sales_order_row_id": 1,
                  "sales_order_delivery_deadline": "2021-09-01T07:49:29.813Z",
                  "material_cost": 10,
                  "created_at": "2021-09-01T07:49:29.813Z",
                  "updated_at": "2021-10-15T14:05:47.625Z",
                  "subassemblies_cost": 10,
                  "operations_cost": 10,
                  "deleted_at": null,
                  "serial_numbers": [
                    {
                      "id": 1,
                      "transaction_id": "eb4da756-0842-4495-9118-f8135f681234",
                      "serial_number": "SN1",
                      "resource_type": "Production",
                      "resource_id": 2,
                      "transaction_date": "2023-02-10T10:06:14.435Z"
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