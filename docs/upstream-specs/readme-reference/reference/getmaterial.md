> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Retrieve a material

Retrieves the details of an existing material based on ID.

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
      "get": {
        "summary": "Retrieve a material",
        "tags": [
          "Material"
        ],
        "description": "Retrieves the details of an existing material based on ID.",
        "operationId": "getMaterial",
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
            "name": "extend",
            "required": false,
            "description": "Array of objects that need to be added to the response",
            "schema": {
              "type": "array",
              "items": {
                "type": "string",
                "enum": [
                  "supplier"
                ]
              }
            },
            "in": "query"
          }
        ],
        "responses": {
          "200": {
            "description": "Details of an existing material",
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
                      "product_id": null,
                      "material_id": 1,
                      "sku": "KC",
                      "sales_price": null,
                      "purchase_price": 45,
                      "config_attributes": [
                        {
                          "config_name": "Type",
                          "config_value": "Standard"
                        }
                      ],
                      "type": "material",
                      "deleted_at": null,
                      "internal_barcode": "internalcode",
                      "registered_barcode": "registeredcode",
                      "supplier_item_codes": [
                        "code"
                      ],
                      "lead_time": 1,
                      "minimum_order_quantity": 3,
                      "custom_fields": [
                        {
                          "field_name": "Power level",
                          "field_value": "Strong"
                        }
                      ],
                      "updated_at": "2020-10-23T10:37:05.085Z",
                      "created_at": "2020-10-23T10:37:05.085Z"
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
                  "updated_at": "2020-10-23T10:37:05.085Z",
                  "supplier": {
                    "id": 1,
                    "name": "Luke Skywalker",
                    "email": "luke.skywalker@example.com",
                    "comment": "Luke Skywalker was a Tatooine farmboy who rose from humble beginnings to become one of the\n              greatest Jedi the galaxy has ever known.",
                    "currency": "UAH",
                    "created_at": "2020-10-23T10:37:05.085Z",
                    "updated_at": "2020-10-23T10:37:05.085Z",
                    "deleted_at": null
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