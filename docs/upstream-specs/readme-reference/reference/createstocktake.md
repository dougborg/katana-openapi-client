# Create a stocktake

Create a new stocktake object.

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
    "/stocktakes": {
      "post": {
        "summary": "Create a stocktake",
        "tags": [
          "Stocktake"
        ],
        "description": "Create a new stocktake object.",
        "operationId": "createStocktake",
        "requestBody": {
          "description": "New stocktake details. Location id should exist and belong to the factory.\n      All batch trackable variants should have batch ids. Variant with batch id should be unique.",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "stocktake_number",
                  "location_id"
                ],
                "properties": {
                  "stocktake_number": {
                    "type": "string",
                    "minLength": 1
                  },
                  "location_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "reason": {
                    "type": "string",
                    "maxLength": 540,
                    "nullable": true
                  },
                  "additional_info": {
                    "type": "string",
                    "nullable": true
                  },
                  "created_date": {
                    "type": "string",
                    "minLength": 1
                  },
                  "set_remaining_items_as_counted": {
                    "type": "boolean",
                    "default": false
                  },
                  "stocktake_rows": {
                    "type": "array",
                    "maxItems": 250,
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "variant_id"
                      ],
                      "properties": {
                        "variant_id": {
                          "type": "integer",
                          "maximum": 2147483647
                        },
                        "batch_id": {
                          "type": "integer",
                          "maximum": 2147483647,
                          "nullable": true
                        },
                        "notes": {
                          "type": "string",
                          "nullable": true,
                          "maxLength": 540
                        },
                        "counted_quantity": {
                          "type": "number",
                          "minimum": 0,
                          "nullable": true
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
            "description": "New stocktake created",
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
                  "id": 15,
                  "stocktake_number": "STK-15",
                  "location_id": 1705,
                  "status": "NOT_STARTED",
                  "reason": "reason",
                  "additional_info": "",
                  "stocktake_created_date": "2021-12-20T07:50:45.856Z",
                  "started_date": "2021-12-20T07:50:58.567Z",
                  "completed_date": "2021-12-20T07:51:25.677Z",
                  "status_update_in_progress": false,
                  "set_remaining_items_as_counted": true,
                  "stock_adjustment_id": null,
                  "created_at": "2021-12-20T07:50:45.856Z",
                  "updated_at": "2021-12-20T07:51:56.359Z",
                  "deleted_at": null,
                  "stocktake_rows": [
                    {
                      "id": 90,
                      "variant_id": 21002,
                      "batch_id": null,
                      "stocktake_id": 2,
                      "notes": "test 2",
                      "in_stock_quantity": null,
                      "counted_quantity": 21,
                      "discrepancy_quantity": null,
                      "created_at": "2022-01-13T14:30:18.174Z",
                      "updated_at": "2022-01-13T14:30:18.174Z",
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