> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Update a purchase order

Updates the specified purchase order by setting the values of the parameters passed.
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
    "/purchase_orders/{id}": {
      "patch": {
        "summary": "Update a purchase order",
        "tags": [
          "Purchase order"
        ],
        "description": "Updates the specified purchase order by setting the values of the parameters passed.\n    Any parameters not provided will be left unchanged.",
        "operationId": "updatePurchaseOrder",
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "Purchase order id",
            "schema": {
              "type": "integer"
            },
            "in": "path"
          }
        ],
        "requestBody": {
          "required": true,
          "description": "Purchase order fields to be updated with new values",
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "order_no": {
                    "type": "string",
                    "minLength": 3,
                    "description": "Updatable only when status is in DRAFT, NOT_RECEIVED and PARTIALLY_RECEIVED"
                  },
                  "supplier_id": {
                    "type": "integer",
                    "maximum": 2147483647,
                    "description": "Updatable only when status is in DRAFT and NOT_RECEIVED"
                  },
                  "currency": {
                    "type": "string",
                    "description": "Updatable only when status is in DRAFT and NOT_RECEIVED"
                  },
                  "tracking_location_id": {
                    "type": "string",
                    "maximum": 2147483647,
                    "description": "Updatable only when status is in DRAFT and NOT_RECEIVED and\n        entity_type is outsourced"
                  },
                  "status": {
                    "type": "string",
                    "enum": [
                      "DRAFT",
                      "NOT_RECEIVED",
                      "RECEIVED",
                      "PARTIALLY_RECEIVED"
                    ]
                  },
                  "expected_arrival_date": {
                    "type": "string",
                    "description": "Updatable only when status is in DRAFT, NOT_RECEIVED and PARTIALLY_RECEIVED. Update will override arrival_date on purchase order rows"
                  },
                  "order_created_date": {
                    "type": "string"
                  },
                  "location_id": {
                    "type": "integer",
                    "maximum": 2147483647,
                    "description": "Updatable only when status is in DRAFT and NOT_RECEIVED"
                  },
                  "additional_info": {
                    "type": "string"
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Purchase order updated",
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