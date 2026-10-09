---
updatedAt: 2026-05-29T09:20:09.000Z
agentTools:
  projectIndex: https://developer.katanamrp.com/llms.txt
---

# Retrieve a variant

Retrieves the details of an existing variant based on ID.

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
    "/variants/{id}": {
      "get": {
        "summary": "Retrieve a variant",
        "tags": [
          "Variant"
        ],
        "description": "Retrieves the details of an existing variant based on ID.",
        "operationId": "getVariant",
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "Variant id",
            "schema": {
              "type": "integer"
            },
            "in": "path"
          },
          {
            "name": "extend",
            "required": false,
            "description": "Array of objects that need to be added to the response",
            "schema": {
              "type": "array",
              "items": {
                "type": "string",
                "enum": [
                  "product_or_material"
                ]
              }
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
            "description": "Details of an existing variant",
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
                      "sku": "EM",
                      "sales_price": 40,
                      "product_id": 1,
                      "material_id": null,
                      "purchase_price": 0,
                      "type": "product",
                      "created_at": "2020-10-23T10:37:05.085Z",
                      "updated_at": "2020-10-23T10:37:05.085Z",
                      "deleted_at": null,
                      "internal_barcode": "0316",
                      "registered_barcode": "0785223088",
                      "supplier_item_codes": [
                        "978-0785223085",
                        "0785223088"
                      ],
                      "config_attributes": [
                        {
                          "config_name": "Type",
                          "config_value": "Standard"
                        }
                      ],
                      "product_or_material": {
                        "id": 1,
                        "name": "Standard-hilt lightsaber",
                        "uom": "pcs",
                        "category_name": "lightsaber",
                        "is_producible": true,
                        "default_supplier_id": 1,
                        "is_purchasable": true,
                        "type": "product",
                        "purchase_uom": "pcs",
                        "purchase_uom_conversion_rate": 1,
                        "batch_tracked": false,
                        "variants": [
                          {
                            "id": 1,
                            "sku": "EM",
                            "sales_price": 40,
                            "product_id": 1,
                            "purchase_price": 0,
                            "type": "product",
                            "created_at": "2020-10-23T10:37:05.085Z",
                            "updated_at": "2020-10-23T10:37:05.085Z",
                            "lead_time": 1,
                            "minimum_order_quantity": 3,
                            "config_attributes": [
                              {
                                "config_name": "Type",
                                "config_value": "Standard"
                              }
                            ],
                            "internal_barcode": "internalcode",
                            "registered_barcode": "registeredcode",
                            "supplier_item_codes": [
                              "code"
                            ],
                            "custom_fields": [
                              {
                                "field_name": "Power level",
                                "field_value": "Strong"
                              }
                            ]
                          }
                        ],
                        "configs": [
                          {
                            "id": 1,
                            "name": "Type",
                            "values": [
                              "Standard",
                              "Double-bladed"
                            ],
                            "product_id": 1
                          }
                        ],
                        "additional_info": "additional info",
                        "created_at": "2020-10-23T10:37:05.085Z",
                        "updated_at": "2020-10-23T10:37:05.085Z"
                      }
                    }
                  },
                  "objectCustomFields": {
                    "summary": "Object custom fields representation",
                    "value": {
                      "id": 1,
                      "sku": "EM",
                      "sales_price": 40,
                      "product_id": 1,
                      "material_id": null,
                      "purchase_price": 0,
                      "type": "product",
                      "created_at": "2020-10-23T10:37:05.085Z",
                      "updated_at": "2020-10-23T10:37:05.085Z",
                      "deleted_at": null,
                      "internal_barcode": "0316",
                      "registered_barcode": "0785223088",
                      "supplier_item_codes": [
                        "978-0785223085",
                        "0785223088"
                      ],
                      "config_attributes": [
                        {
                          "config_name": "Type",
                          "config_value": "Standard"
                        }
                      ],
                      "custom_fields": {
                        "a1b2c3d4-1111-2222-3333-444455556666": "Strong",
                        "0c8f1d6e-3c2a-4f5b-9d77-12ab34cd56ef": 2
                      }
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