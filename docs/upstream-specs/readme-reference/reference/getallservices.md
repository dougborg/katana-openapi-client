---
updatedAt: 2026-05-29T09:20:09.000Z
agentTools:
  projectIndex: https://developer.katanamrp.com/llms.txt
---

# List all services

Returns a list of services you’ve previously created. The services are returned in sorted order, with the most recent services appearing first.

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
    "/services": {
      "get": {
        "summary": "List all services",
        "tags": [
          "Service"
        ],
        "description": "Returns a list of services you’ve previously created. The services are returned in sorted order, with the most recent services appearing first.",
        "operationId": "getAllServices",
        "parameters": [
          {
            "name": "ids",
            "required": false,
            "description": "Filters services by an array of IDs",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer"
              }
            },
            "in": "query"
          },
          {
            "name": "name",
            "required": false,
            "description": "Filters services by a name",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "uom",
            "required": false,
            "description": "Filters services by a uom",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "is_sellable",
            "required": false,
            "description": "Filters services by ability to sell",
            "schema": {
              "type": "boolean"
            },
            "in": "query"
          },
          {
            "name": "category_name",
            "required": false,
            "description": "Filters services by a category name",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "include_deleted",
            "required": false,
            "description": "Soft-deleted data is excluded from result set by default. Set to true to include it.",
            "schema": {
              "type": "boolean"
            },
            "in": "query"
          },
          {
            "name": "include_archived",
            "required": false,
            "description": "Archived data is excluded from result set by default. Set to true to include it.",
            "schema": {
              "type": "boolean"
            },
            "in": "query"
          },
          {
            "name": "limit",
            "required": false,
            "description": "Used for pagination (default is 50)",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "page",
            "required": false,
            "description": "Used for pagination (default is 1)",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "created_at_min",
            "required": false,
            "description": "Minimum value for created_at range. Must be compatible with ISO 8601 format",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "created_at_max",
            "required": false,
            "description": "Maximum value for created_at range. Must be compatible with ISO 8601 format",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "updated_at_min",
            "required": false,
            "description": "Minimum value for updated_at range. Must be compatible with ISO 8601 format",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "updated_at_max",
            "required": false,
            "description": "Maximum value for updated_at range. Must be compatible with ISO 8601 format",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "X-Custom-Fields-Format",
            "required": false,
            "in": "header",
            "description": "Selects the representation of `custom_fields` on items, for both the request body and the response.\n\n- `default` — object keyed by custom field definition id (UUID).\n- `legacy` — the `{field_name, field_value}` array tied to custom fields collections.\n\nMost accounts do not need this header: an account that has not moved to item custom fields always gets `legacy`, and an account that has moved and no longer uses collections always gets the object representation. The header matters only while both are available for the account, where `legacy` is the default and `default` opts into the object representation.\n\nRequesting a representation the account does not have returns 422, as does sending a `custom_fields` body whose shape does not match the representation in force, mixing both shapes in one request, or combining `custom_field_collection_id` with the object representation — that field belongs to the legacy representation and is left out of responses entirely under the object one. Responses vary on this header.",
            "schema": {
              "type": "string",
              "enum": [
                "default",
                "legacy"
              ]
            }
          }
        ],
        "responses": {
          "200": {
            "description": "List all services",
            "headers": {
              "X-Pagination": {
                "description": "Pagination metadata",
                "schema": {
                  "type": "object",
                  "properties": {
                    "total_records": {
                      "type": "number"
                    },
                    "total_pages": {
                      "type": "number"
                    },
                    "offset": {
                      "type": "number"
                    },
                    "page": {
                      "type": "number"
                    },
                    "first_page": {
                      "type": "boolean"
                    },
                    "last_page": {
                      "type": "boolean"
                    }
                  }
                }
              },
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
                "examples": {
                  "legacyCustomFields": {
                    "summary": "Legacy custom fields representation",
                    "value": {
                      "data": [
                        {
                          "id": 1,
                          "name": "Service name",
                          "uom": "pcs",
                          "category_name": "Service",
                          "type": "service",
                          "is_sellable": true,
                          "custom_field_collection_id": 1,
                          "additional_info": "additional info",
                          "created_at": "2020-10-23T10:37:05.085Z",
                          "updated_at": "2020-10-23T10:37:05.085Z",
                          "deleted_at": null,
                          "archived_at": "2020-10-20T10:37:05.085Z",
                          "variants": [
                            {
                              "id": 1,
                              "sku": "S-2486",
                              "sales_price": null,
                              "default_cost": null,
                              "service_id": 1,
                              "type": "service",
                              "created_at": "2020-10-23T10:37:05.085Z",
                              "updated_at": "2020-10-23T10:37:05.085Z",
                              "deleted_at": null,
                              "custom_fields": [
                                {
                                  "field_name": "Power level",
                                  "field_value": "Strong"
                                }
                              ]
                            }
                          ]
                        }
                      ]
                    }
                  },
                  "objectCustomFields": {
                    "summary": "Object custom fields representation",
                    "value": {
                      "data": [
                        {
                          "id": 1,
                          "name": "Service name",
                          "uom": "pcs",
                          "category_name": "Service",
                          "type": "service",
                          "is_sellable": true,
                          "additional_info": "additional info",
                          "created_at": "2020-10-23T10:37:05.085Z",
                          "updated_at": "2020-10-23T10:37:05.085Z",
                          "deleted_at": null,
                          "archived_at": "2020-10-20T10:37:05.085Z",
                          "variants": [
                            {
                              "id": 1,
                              "sku": "S-2486",
                              "sales_price": null,
                              "default_cost": null,
                              "service_id": 1,
                              "type": "service",
                              "created_at": "2020-10-23T10:37:05.085Z",
                              "updated_at": "2020-10-23T10:37:05.085Z",
                              "deleted_at": null,
                              "custom_fields": {
                                "a1b2c3d4-1111-2222-3333-444455556666": "Strong"
                              }
                            }
                          ]
                        }
                      ]
                    }
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