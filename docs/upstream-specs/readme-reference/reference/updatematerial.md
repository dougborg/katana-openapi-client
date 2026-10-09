---
updatedAt: 2026-05-29T09:20:09.000Z
agentTools:
  projectIndex: https://developer.katanamrp.com/llms.txt
---

# Update a material

Updates the specified material by setting the values of the parameters passed.
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
    "/materials/{id}": {
      "patch": {
        "summary": "Update a material",
        "tags": [
          "Material"
        ],
        "description": "Updates the specified material by setting the values of the parameters passed.\n    Any parameters not provided will be left unchanged.",
        "operationId": "updateMaterial",
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "Material id",
            "schema": {
              "type": "integer"
            },
            "in": "path"
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
        "requestBody": {
          "description": "Material details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
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
                  "default_supplier_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "additional_info": {
                    "type": "string"
                  },
                  "batch_tracked": {
                    "type": "boolean"
                  },
                  "is_sellable": {
                    "type": "boolean"
                  },
                  "is_archived": {
                    "type": "boolean"
                  },
                  "purchase_uom": {
                    "type": "string",
                    "maxLength": 7,
                    "description": "If used, then purchase_uom_conversion_rate must have a value as well."
                  },
                  "purchase_uom_conversion_rate": {
                    "type": "number",
                    "description": "If used, then purchase_uom must have a value as well.",
                    "maximum": 1000000000000
                  },
                  "configs": {
                    "type": "array",
                    "minItems": 1,
                    "description": "When updating configs, all configs and values must be provided. Existing ones are matched,\n        new ones are created, and configs not provided in the update are deleted.",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "name",
                        "values"
                      ],
                      "properties": {
                        "id": {
                          "type": "integer",
                          "description": "If config ID is used to map the config, then name is ignored."
                        },
                        "name": {
                          "type": "string",
                          "description": "If config name is used to map the config, then we match to the existing config by name.\n              If a match is not found, a new one is created."
                        },
                        "values": {
                          "type": "array",
                          "items": {
                            "type": "string"
                          }
                        }
                      }
                    }
                  },
                  "custom_field_collection_id": {
                    "type": "integer",
                    "maximum": 2147483647,
                    "nullable": true,
                    "description": "Custom fields collection the item draws its legacy `{field_name, field_value}` custom fields from. Belongs to the legacy representation only — sending it together with object-form `custom_fields` is rejected with a 422. See the `X-Custom-Fields-Format` header."
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Material updated",
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
                      "name": "Kyber Crystal",
                      "uom": "pcs",
                      "category_name": "Lightsaber components",
                      "default_supplier_id": 1,
                      "type": "material",
                      "purchase_uom": "pcs",
                      "purchase_uom_conversion_rate": 1,
                      "batch_tracked": false,
                      "is_sellable": false,
                      "archived_at": "2020-10-20T10:37:05.085Z",
                      "variants": [
                        {
                          "id": 1,
                          "sku": "KC",
                          "sales_price": null,
                          "product_id": 1,
                          "purchase_price": 45,
                          "type": "material",
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
                      "custom_field_collection_id": 1,
                      "created_at": "2020-10-23T10:37:05.085Z",
                      "updated_at": "2020-10-23T10:37:05.085Z"
                    }
                  },
                  "objectCustomFields": {
                    "summary": "Object custom fields representation",
                    "value": {
                      "id": 1,
                      "name": "Kyber Crystal",
                      "uom": "pcs",
                      "category_name": "Lightsaber components",
                      "default_supplier_id": 1,
                      "type": "material",
                      "purchase_uom": "pcs",
                      "purchase_uom_conversion_rate": 1,
                      "batch_tracked": false,
                      "is_sellable": false,
                      "archived_at": "2020-10-20T10:37:05.085Z",
                      "variants": [
                        {
                          "id": 1,
                          "sku": "KC",
                          "sales_price": null,
                          "product_id": 1,
                          "purchase_price": 45,
                          "type": "material",
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
                          "custom_fields": {
                            "a1b2c3d4-1111-2222-3333-444455556666": "Strong"
                          }
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