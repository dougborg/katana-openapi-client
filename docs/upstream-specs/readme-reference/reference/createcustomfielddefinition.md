> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Create a custom field definition

> 🚧 **Beta — feature-flagged.** Contact support@katanamrp.com to enable.

Creates a new custom field definition for a given entity type. A factory may have at most 50 definitions.

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
    "/custom_field_definitions": {
      "post": {
        "summary": "Create a custom field definition",
        "tags": [
          "Custom Field Definition"
        ],
        "description": "> 🚧 **Beta — feature-flagged.** Contact support@katanamrp.com to enable.\n\nCreates a new custom field definition for a given entity type. A factory may have at most 50 definitions.",
        "operationId": "createCustomFieldDefinition",
        "requestBody": {
          "description": "New custom field definition details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "label",
                  "field_type",
                  "entity_type",
                  "source"
                ],
                "properties": {
                  "label": {
                    "type": "string",
                    "maxLength": 255,
                    "description": "Human-readable label of the custom field."
                  },
                  "field_type": {
                    "type": "string",
                    "enum": [
                      "shortText",
                      "number",
                      "singleSelect",
                      "date",
                      "boolean",
                      "url"
                    ],
                    "description": "Type of value the field stores. Immutable after creation.\n- `shortText` — string\n- `number` — number\n- `singleSelect` — integer choice id (requires `options.choices`)\n- `date` — `YYYY-MM-DD` string\n- `boolean` — true / false\n- `url` — string"
                  },
                  "entity_type": {
                    "type": "string",
                    "enum": [
                      "SalesOrder",
                      "SalesOrderRow"
                    ],
                    "description": "Entity the custom field applies to. Immutable after creation."
                  },
                  "source": {
                    "type": "string",
                    "maxLength": 255,
                    "description": "Caller-provided identifier of the integration that owns the field — for example your application slug. Used to namespace and audit field definitions."
                  },
                  "description": {
                    "type": "string",
                    "nullable": true,
                    "description": "Optional free-text description shown alongside the field in Katana."
                  },
                  "options": {
                    "type": "object",
                    "nullable": true,
                    "additionalProperties": false,
                    "description": "Only meaningful when `field_type` is `singleSelect`. Omit (or send `null`) for other types.",
                    "properties": {
                      "choices": {
                        "type": "array",
                        "description": "Allowed choices. On create, send each choice with just a `label`; the server assigns each one an integer `id` and returns the resolved array in the response. Use that `id` when setting a value on a sales order.",
                        "items": {
                          "type": "object",
                          "additionalProperties": false,
                          "required": [
                            "label"
                          ],
                          "properties": {
                            "label": {
                              "type": "string",
                              "description": "Human-readable label for the choice."
                            }
                          }
                        }
                      }
                    }
                  }
                }
              },
              "examples": {
                "shortText": {
                  "summary": "Plain short-text field",
                  "value": {
                    "label": "PO reference",
                    "field_type": "shortText",
                    "entity_type": "SalesOrder",
                    "source": "your-integration"
                  }
                },
                "singleSelect": {
                  "summary": "Single-select with choices",
                  "value": {
                    "label": "Channel",
                    "field_type": "singleSelect",
                    "entity_type": "SalesOrder",
                    "source": "your-integration",
                    "options": {
                      "choices": [
                        {
                          "label": "Online"
                        },
                        {
                          "label": "Retail"
                        },
                        {
                          "label": "Wholesale"
                        }
                      ]
                    }
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Custom field definition created",
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
                  "id": "0c8f1d6e-3c2a-4f5b-9d77-12ab34cd56ef",
                  "label": "Channel",
                  "description": null,
                  "field_type": "singleSelect",
                  "entity_type": "SalesOrder",
                  "source": "your-integration",
                  "options": {
                    "choices": [
                      {
                        "id": 1,
                        "label": "Online"
                      },
                      {
                        "id": 2,
                        "label": "Retail"
                      },
                      {
                        "id": 3,
                        "label": "Wholesale"
                      }
                    ]
                  },
                  "created_at": "2026-05-14T10:00:00.000Z",
                  "updated_at": "2026-05-14T10:00:00.000Z",
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