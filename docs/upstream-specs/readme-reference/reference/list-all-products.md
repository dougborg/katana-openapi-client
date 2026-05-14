# List all products

Returns a list of products you’ve previously created. The products are returned in sorted order,
    with the most recent products appearing first.

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
    "/products": {
      "get": {
        "summary": "List all products",
        "tags": [
          "Product"
        ],
        "description": "Returns a list of products you’ve previously created. The products are returned in sorted order,\n    with the most recent products appearing first.",
        "operationId": "getAllProducts",
        "parameters": [
          {
            "name": "ids",
            "required": false,
            "description": "Filters products by an array of IDs",
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
            "description": "Filters products by a name",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "uom",
            "required": false,
            "description": "Filters products by a uom",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "is_sellable",
            "required": false,
            "description": "Filters products by a is_sellable",
            "schema": {
              "type": "boolean"
            },
            "in": "query"
          },
          {
            "name": "is_producible",
            "required": false,
            "description": "Filters products by an is_producible",
            "schema": {
              "type": "boolean"
            },
            "in": "query"
          },
          {
            "name": "is_purchasable",
            "required": false,
            "description": "Filters products by an is_purchasable",
            "schema": {
              "type": "boolean"
            },
            "in": "query"
          },
          {
            "name": "is_auto_assembly",
            "required": false,
            "description": "Filters products by an is_auto_assembly",
            "schema": {
              "type": "boolean"
            },
            "in": "query"
          },
          {
            "name": "default_supplier_id",
            "required": false,
            "description": "Filters products by a default_supplier_id",
            "schema": {
              "type": "integer"
            },
            "in": "query"
          },
          {
            "name": "batch_tracked",
            "required": false,
            "description": "Filters products by a batch_tracked",
            "schema": {
              "type": "boolean"
            },
            "in": "query"
          },
          {
            "name": "serial_tracked",
            "required": false,
            "description": "Filters products by a serial_tracked",
            "schema": {
              "type": "boolean"
            },
            "in": "query"
          },
          {
            "name": "operations_in_sequence",
            "required": false,
            "description": "Filters products by a operations_in_sequence",
            "schema": {
              "type": "boolean"
            },
            "in": "query"
          },
          {
            "name": "purchase_uom",
            "required": false,
            "description": "Filters products by a purchase_uom",
            "schema": {
              "type": "string"
            },
            "in": "query"
          },
          {
            "name": "purchase_uom_conversion_rate",
            "required": false,
            "description": "Filters products by a purchase_uom_conversion_rate",
            "schema": {
              "type": "number"
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
                  "supplier"
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
            "description": "List all products",
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
                      "name": "Standard-hilt lightsaber",
                      "uom": "pcs",
                      "category_name": "lightsaber",
                      "is_producible": true,
                      "default_supplier_id": 1,
                      "is_sellable": true,
                      "is_purchasable": true,
                      "is_auto_assembly": true,
                      "type": "product",
                      "purchase_uom": "pcs",
                      "purchase_uom_conversion_rate": 1,
                      "batch_tracked": true,
                      "operations_in_sequence": false,
                      "serial_tracked": false,
                      "archived_at": "2020-10-20T10:37:05.085Z",
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