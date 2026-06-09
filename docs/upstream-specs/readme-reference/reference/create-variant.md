> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Create a variant

Creates a new variant object. Note that you can create variants for both products and materials.
    In order for Katana to know which one you are creating,
    you have to specify either product_id or material_id, not both.

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
      "post": {
        "summary": "Create a variant",
        "tags": [
          "Variant"
        ],
        "description": "Creates a new variant object. Note that you can create variants for both products and materials.\n    In order for Katana to know which one you are creating,\n    you have to specify either product_id or material_id, not both.",
        "operationId": "createVariant",
        "requestBody": {
          "description": "new variant details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
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
                  "purchase_price": {
                    "type": "number",
                    "maximum": 100000000000,
                    "minimum": 0,
                    "nullable": true
                  },
                  "product_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "supplier_item_codes": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                      "type": "string",
                      "minLength": 1
                    }
                  },
                  "internal_barcode": {
                    "type": "string",
                    "minLength": 3,
                    "maxLength": 40
                  },
                  "registered_barcode": {
                    "type": "string",
                    "maxLength": 120
                  },
                  "material_id": {
                    "type": "integer",
                    "maximum": 2147483647
                  },
                  "lead_time": {
                    "type": "integer",
                    "maximum": 999,
                    "nullable": true
                  },
                  "minimum_order_quantity": {
                    "type": "number",
                    "maximum": 999999999,
                    "minimum": 0,
                    "nullable": true
                  },
                  "config_attributes": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "config_name",
                        "config_value"
                      ],
                      "properties": {
                        "config_name": {
                          "type": "string"
                        },
                        "config_value": {
                          "type": "string"
                        }
                      }
                    }
                  },
                  "custom_fields": {
                    "type": "array",
                    "maxItems": 3,
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
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "New variant created",
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
                  "sku": "EM",
                  "sales_price": 40,
                  "product_id": 1,
                  "material_id": null,
                  "purchase_price": 0,
                  "type": "product",
                  "internal_barcode": "0315",
                  "registered_barcode": "0785223088",
                  "supplier_item_codes": [
                    "978-0785223085",
                    "0785223088"
                  ],
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
                  "custom_fields": [
                    {
                      "field_name": "Power level",
                      "field_value": "Strong"
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