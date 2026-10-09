---
updatedAt: 2026-05-14T13:38:42.000Z
agentTools:
  projectIndex: https://developer.katanamrp.com/llms.txt
---

# Create a custom field definition

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
        "description": "Creates a new custom field definition for a given entity type. A factory may have at most 50 definitions.",
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
                      "SalesOrderRow",
                      "ProductVariant",
                      "MaterialVariant",
                      "ServiceVariant",
                      "PurchaseOrder",
                      "PurchaseOrderRow",
                      "OutsourcedPurchaseOrder",
                      "OutsourcedPurchaseOrderRow",
                      "ProductionOperation",
                      "RecipeBom",
                      "Supplier",
                      "Customer"
                    ],
                    "description": "Entity the custom field applies to. Immutable after creation.\n- `SalesOrder` / `SalesOrderRow` — the field lives on a sales order, or on one of its rows.\n- `ProductVariant` / `MaterialVariant` / `ServiceVariant` — the field lives on an item. In Katana these are the Products, Materials, and Services an item can be. Values are held **per variant**, not on the product / material / service itself: a `ProductVariant` definition is set and read on each of a product’s variants, and a product with one variant simply has one place to set it.\n- `PurchaseOrder` / `PurchaseOrderRow` / `OutsourcedPurchaseOrder` / `OutsourcedPurchaseOrderRow` — the field lives on a purchase order, standard or outsourced, or on one of its rows.\n- `ProductionOperation` — the field lives on a production operation.\n- `RecipeBom` — the field lives on a BOM row. The same definitions are used on manufacturing order recipe rows and outsourced purchase order recipe rows.\n- `Supplier` — the field lives on a supplier.\n- `Customer` — the field lives on a customer.\n\nTwo groups each share a single pool of definitions, so a definition is accepted beyond the exact entity type it was created with:\n- The three variant entity types — a definition created with any one of them is accepted on any variant, whatever kind of item it belongs to.\n- Standard and outsourced purchase orders — `PurchaseOrder` and `OutsourcedPurchaseOrder` definitions are both accepted on any purchase order, and likewise `PurchaseOrderRow` / `OutsourcedPurchaseOrderRow` on any purchase order row.\n\nKatana’s own UI still scopes each definition to the item type or kind of order it was created for, so pick the `entity_type` that matches where you want the field to appear.\n\nThe variant entity types, the four purchase order entity types, `Customer`, and `ProductionOperation` are behind feature flags — contact support@katanamrp.com to enable. `ProductionOperation` additionally requires the Advanced Manufacturing or Manufacturing Management add-on."
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
                    "description": "Extra configuration for the definition. `choices` is only meaningful when `field_type` is `singleSelect`; `appearsOn` is only meaningful on a variant definition. Omit (or send `null`) when neither applies.",
                    "properties": {
                      "appearsOn": {
                        "type": "array",
                        "uniqueItems": true,
                        "description": "Transactional entities this definition additionally applies to, on top of its own `entity_type`. Listing a target makes this definition’s id a valid key in that entity’s `custom_fields` — nothing is copied, and the target’s `custom_fields` accepts its own definitions and linked-in ones alike.\n\nOnly variant definitions (`ProductVariant` / `MaterialVariant` / `ServiceVariant`) may target `SalesOrderRow`, `PurchaseOrderRow`, `OutsourcedPurchaseOrderRow`, and `ManufacturingOrder`; a `ProductionOperation` definition may target `ManufacturingOrder` only. Any other combination, a duplicate entry, or the definition’s own `entity_type` is rejected with a 422.\n\nSeparately from this, a row or manufacturing order created against a variant takes a **snapshot** of that variant’s current values for the fields that name it in `appearsOn`. The snapshot is editable on the record afterwards and is never re-synced, so later edits to the variant do not reach records that already exist. A value whose definition no longer applies to the entity — the target was dropped from `appearsOn`, or the definition was deleted — is retained but no longer returned on reads of that record.\n\nBehind a feature flag on the target side too — contact support@katanamrp.com to enable.",
                        "items": {
                          "type": "string",
                          "enum": [
                            "SalesOrderRow",
                            "PurchaseOrderRow",
                            "OutsourcedPurchaseOrderRow",
                            "ManufacturingOrder"
                          ]
                        }
                      },
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
                },
                "variantFieldOnSalesOrderRows": {
                  "summary": "Variant field that also applies to sales order rows",
                  "value": {
                    "label": "Country of origin",
                    "field_type": "shortText",
                    "entity_type": "ProductVariant",
                    "source": "your-integration",
                    "options": {
                      "appearsOn": [
                        "SalesOrderRow"
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