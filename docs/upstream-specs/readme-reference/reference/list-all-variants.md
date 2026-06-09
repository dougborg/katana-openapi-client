> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# List all variants

Returns a list of variants you've previously created. The variants are returned in sorted order,
    with the most recent variants appearing first.

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
    "/variants": {
      "get": {
        "summary": "List all variants",
        "tags": [
          "Variant"
        ],
        "description": "Returns a list of variants you've previously created. The variants are returned in sorted order,\n    with the most recent variants appearing first.",
        "operationId": "getAllVariants",
        "parameters": [
          {
            "name": "ids",
            "required": false,
            "description": "Filters variants by an array of IDs",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer"
              }
            },
            "in": "query"
          },
          {
            "name": "product_id",
            "required": false,
            "description": "Filters variants by a product id",
            "schema": {
              "type": "integer"
            },
            "in": "query"
          },
          {
            "name": "material_id",
            "required": false,
            "description": "Filters variants by a material id",
            "schema": {
              "type": "integer"
            },
            "in": "query"
          },
          {
            "name": "sku",
            "required": false,
            "description": "Filters variants by skus",
            "schema": {
              "type": "array",
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "in": "query"
          },
          {
            "name": "sales_price",
            "required": false,
            "description": "Filters variants by a sales price",
            "schema": {
              "type": "number"
            },
            "in": "query"
          },
          {
            "name": "purchase_price",
            "required": false,
            "description": "Filters variants by a purchase price",
            "schema": {
              "type": "number"
            },
            "in": "query"
          },
          {
            "name": "internal_barcode",
            "required": false,
            "description": "Filters variants by an internal barcode",
            "schema": {
              "type": "string",
              "minLength": 3,
              "maxLength": 40
            },
            "in": "query"
          },
          {
            "name": "registered_barcode",
            "required": false,
            "description": "Filters variants by a registered barcode",
            "schema": {
              "type": "string",
              "maxLength": 120
            },
            "in": "query"
          },
          {
            "name": "supplier_item_codes",
            "required": false,
            "description": "Filters variants by supplier item codes. Returns the variants that match with any of the codes in the array.",
            "schema": {
              "type": "array",
              "items": {
                "type": "string",
                "minLength": 1
              }
            },
            "in": "query"
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
          }
        ],
        "responses": {
          "200": {
            "description": "List all product variants",
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
                "example": {
                  "data": [
                    {
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