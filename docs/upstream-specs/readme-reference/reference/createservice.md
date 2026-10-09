---
updatedAt: 2026-05-29T09:20:09.000Z
agentTools:
  projectIndex: https://developer.katanamrp.com/llms.txt
---

# Create a service

Creates a service object.

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
      "post": {
        "summary": "Create a service",
        "tags": [
          "Service"
        ],
        "description": "Creates a service object.",
        "operationId": "createService",
        "parameters": [
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
        "requestBody": {
          "description": "new service details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "name",
                  "variants"
                ],
                "properties": {
                  "name": {
                    "type": "string"
                  },
                  "uom": {
                    "type": "string",
                    "maxLength": 7
                  },
                  "category_name": {
                    "type": "string"
                  },
                  "additional_info": {
                    "type": "string"
                  },
                  "is_sellable": {
                    "type": "boolean"
                  },
                  "custom_field_collection_id": {
                    "type": "integer",
                    "maximum": 2147483647,
                    "nullable": true,
                    "description": "Custom fields collection the item draws its legacy `{field_name, field_value}` custom fields from. Belongs to the legacy representation only — sending it together with object-form `custom_fields` is rejected with a 422. See the `X-Custom-Fields-Format` header."
                  },
                  "variants": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 1,
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "sku": {
                          "type": "string"
                        },
                        "sales_price": {
                          "type": "number",
                          "maximum": 100000000000,
                          "minimum": 0,
                          "nullable": true
                        },
                        "default_cost": {
                          "type": "number",
                          "maximum": 100000000000,
                          "minimum": 0,
                          "nullable": true
                        },
                        "custom_fields": {
                          "description": "Custom field values on the variant. Served in one of two representations depending on the account — the legacy `{field_name, field_value}` array, or an object keyed by custom field definition id. See the `X-Custom-Fields-Format` header for how the representation is chosen, and note that a single request must not mix the two.",
                          "oneOf": [
                            {
                              "type": "object",
                              "description": "Object representation. Custom field values keyed by custom field definition id (UUID) of a definition whose `entity_type` is `ProductVariant`, `MaterialVariant`, or `ServiceVariant`. Each value matches the definition’s `field_type` — string for `shortText` / `url`, number for `number`, boolean for `boolean`, `YYYY-MM-DD` string for `date`, or the integer choice `id` for `singleSelect`. Send `null` to clear a single value. Keys that are not a UUID, and UUIDs with no matching definition, are rejected with a 422.",
                              "additionalProperties": {
                                "nullable": true,
                                "anyOf": [
                                  {
                                    "type": "string"
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ]
                              }
                            },
                            {
                              "type": "array",
                              "maxItems": 3,
                              "description": "Legacy representation. Up to three name/value pairs, drawn from the custom fields collection assigned to the item. Superseded by the object representation.",
                              "items": {
                                "type": "object",
                                "additionalProperties": false,
                                "required": [
                                  "field_name",
                                  "field_value"
                                ],
                                "properties": {
                                  "field_name": {
                                    "maxLength": 40,
                                    "type": "string"
                                  },
                                  "field_value": {
                                    "maxLength": 100,
                                    "type": "string"
                                  }
                                }
                              }
                            }
                          ]
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
            "description": "New service created",
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
                "examples": {
                  "legacyCustomFields": {
                    "summary": "Legacy custom fields representation",
                    "value": {
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
                  },
                  "objectCustomFields": {
                    "summary": "Object custom fields representation",
                    "value": {
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