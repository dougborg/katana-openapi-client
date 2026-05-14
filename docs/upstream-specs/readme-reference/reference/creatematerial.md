# Create a material

Creates a material object.

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
    "/materials": {
      "post": {
        "summary": "Create a material",
        "tags": [
          "Material"
        ],
        "description": "Creates a material object.",
        "operationId": "createMaterial",
        "requestBody": {
          "description": "new material details",
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
                  "purchase_uom": {
                    "type": "string",
                    "maxLength": 7
                  },
                  "purchase_uom_conversion_rate": {
                    "type": "number",
                    "maximum": 1000000000000
                  },
                  "configs": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "name",
                        "values"
                      ],
                      "properties": {
                        "name": {
                          "type": "string"
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
                    "nullable": true
                  },
                  "variants": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "sku": {
                          "type": "string"
                        },
                        "purchase_price": {
                          "type": "number",
                          "maximum": 100000000000,
                          "minimum": 0,
                          "nullable": true
                        },
                        "internal_barcode": {
                          "type": "string",
                          "minLength": 3,
                          "maxLength": 40
                        },
                        "registered_barcode": {
                          "type": "string",
                          "maxLength": 40,
                          "minLength": 3
                        },
                        "supplier_item_codes": {
                          "type": "array",
                          "items": {
                            "type": "string",
                            "minLength": 1,
                            "maxLength": 40
                          }
                        },
                        "lead_time": {
                          "type": "number",
                          "maximum": 999,
                          "minimum": 0,
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
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "New material created",
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