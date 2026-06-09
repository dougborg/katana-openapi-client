> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Export webhook logs

Use the endpoint to export your webhook logs and troubleshoot any issues.
      Webhook logs are filtered by the provided parameters and exported into a CSV file.
      The response contains an URL to the CSV file.

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
    "/webhook_logs_export": {
      "post": {
        "summary": "Export webhook logs",
        "tags": [
          "Webhook logs"
        ],
        "description": "Use the endpoint to export your webhook logs and troubleshoot any issues.\n      Webhook logs are filtered by the provided parameters and exported into a CSV file.\n      The response contains an URL to the CSV file.",
        "operationId": "exportWebhookLogs",
        "requestBody": {
          "description": "webhook logs filters",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "webhook_id": {
                    "type": "integer"
                  },
                  "event": {
                    "type": "string",
                    "enum": [
                      "sales_order.created",
                      "sales_order.packed",
                      "sales_order.delivered",
                      "sales_order.updated",
                      "sales_order.deleted",
                      "sales_order.availability_updated",
                      "purchase_order.created",
                      "purchase_order.updated",
                      "purchase_order.deleted",
                      "purchase_order.partially_received",
                      "purchase_order.received",
                      "purchase_order_row.created",
                      "purchase_order_row.received",
                      "purchase_order_row.updated",
                      "purchase_order_row.deleted",
                      "outsourced_purchase_order.created",
                      "outsourced_purchase_order.updated",
                      "outsourced_purchase_order.deleted",
                      "outsourced_purchase_order.received",
                      "outsourced_purchase_order_row.created",
                      "outsourced_purchase_order_row.updated",
                      "outsourced_purchase_order_row.deleted",
                      "outsourced_purchase_order_row.received",
                      "outsourced_purchase_order_recipe_row.created",
                      "outsourced_purchase_order_recipe_row.updated",
                      "outsourced_purchase_order_recipe_row.deleted",
                      "manufacturing_order.created",
                      "manufacturing_order.updated",
                      "manufacturing_order.deleted",
                      "manufacturing_order.in_progress",
                      "manufacturing_order.blocked",
                      "manufacturing_order.done",
                      "manufacturing_order_recipe_row.created",
                      "manufacturing_order_recipe_row.updated",
                      "manufacturing_order_recipe_row.deleted",
                      "manufacturing_order_recipe_row.ingredients_in_stock",
                      "manufacturing_order_operation_row.created",
                      "manufacturing_order_operation_row.updated",
                      "manufacturing_order_operation_row.deleted",
                      "manufacturing_order_operation_row.in_progress",
                      "manufacturing_order_operation_row.paused",
                      "manufacturing_order_operation_row.blocked",
                      "manufacturing_order_operation_row.completed",
                      "current_inventory.product_updated",
                      "current_inventory.material_updated",
                      "current_inventory.product_out_of_stock",
                      "current_inventory.material_out_of_stock",
                      "product.created",
                      "product.updated",
                      "product.deleted",
                      "material.created",
                      "material.updated",
                      "material.deleted",
                      "variant.created",
                      "variant.updated",
                      "variant.deleted",
                      "product_recipe_row.created",
                      "product_recipe_row.deleted",
                      "product_recipe_row.updated"
                    ]
                  },
                  "status_code": {
                    "type": "integer"
                  },
                  "delivered": {
                    "type": "boolean"
                  },
                  "created_at_min": {
                    "type": "string"
                  },
                  "created_at_max": {
                    "type": "string"
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "New webhook created",
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
                  "url": "https://katana-storage.com/your-file"
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