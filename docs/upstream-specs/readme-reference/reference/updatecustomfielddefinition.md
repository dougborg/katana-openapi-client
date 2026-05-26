# Update a custom field definition

> 🚧 **Beta — feature-flagged.** Contact support@katanamrp.com to enable.

Updates the `label`, `description`, or `options` of a custom field definition. Other properties (`field_type`, `entity_type`, `source`) are immutable.

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
    "/custom_field_definitions/{id}": {
      "patch": {
        "summary": "Update a custom field definition",
        "tags": [
          "Custom Field Definition"
        ],
        "description": "> 🚧 **Beta — feature-flagged.** Contact support@katanamrp.com to enable.\n\nUpdates the `label`, `description`, or `options` of a custom field definition. Other properties (`field_type`, `entity_type`, `source`) are immutable.",
        "operationId": "updateCustomFieldDefinition",
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "Custom field definition id (UUID).",
            "schema": {
              "type": "string",
              "format": "uuid"
            },
            "in": "path"
          }
        ],
        "requestBody": {
          "description": "Custom field definition fields to update",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "description": "Only `label`, `description`, and `options` may be updated. `field_type`, `entity_type`, and `source` are immutable.",
                "properties": {
                  "label": {
                    "type": "string",
                    "maxLength": 255
                  },
                  "description": {
                    "type": "string",
                    "nullable": true
                  },
                  "options": {
                    "type": "object",
                    "nullable": true,
                    "additionalProperties": false,
                    "description": "Only meaningful when the field is a `singleSelect`. Send the **full** `choices` array — every existing choice must be included and identified by its server-assigned `id`. Omit a choice and it is removed from history (use `deleted: true` instead to soft-delete it and keep historical values resolvable). New choices in the array are created without an `id`.",
                    "properties": {
                      "choices": {
                        "type": "array",
                        "items": {
                          "type": "object",
                          "additionalProperties": false,
                          "properties": {
                            "id": {
                              "type": "integer",
                              "description": "Server-assigned. Required to identify an existing choice. Omit on a brand-new choice — the server assigns one."
                            },
                            "label": {
                              "type": "string",
                              "description": "Human-readable label for the choice."
                            },
                            "deleted": {
                              "type": "boolean",
                              "description": "Set to `true` to soft-delete an existing choice. Soft-deleted choices remain in the array so historical values stay resolvable."
                            }
                          },
                          "required": [
                            "label"
                          ]
                        }
                      }
                    }
                  }
                }
              },
              "examples": {
                "renameLabel": {
                  "summary": "Rename the field",
                  "value": {
                    "label": "Sales channel"
                  }
                },
                "addAndSoftDeleteChoices": {
                  "summary": "Add a new choice and soft-delete an existing one",
                  "value": {
                    "options": {
                      "choices": [
                        {
                          "id": 1,
                          "label": "Online"
                        },
                        {
                          "id": 2,
                          "label": "Retail",
                          "deleted": true
                        },
                        {
                          "id": 3,
                          "label": "Wholesale"
                        },
                        {
                          "label": "B2B"
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
            "description": "Custom field definition updated",
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
                  "label": "Sales channel",
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
                        "label": "Retail",
                        "deleted": true
                      },
                      {
                        "id": 3,
                        "label": "Wholesale"
                      },
                      {
                        "id": 4,
                        "label": "B2B"
                      }
                    ]
                  },
                  "created_at": "2026-05-14T10:00:00.000Z",
                  "updated_at": "2026-05-14T10:15:00.000Z",
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
          "404": {
            "description": "Make sure data is correct",
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
                  "statusCode": 404,
                  "name": "NotFoundError",
                  "message": "Not found"
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