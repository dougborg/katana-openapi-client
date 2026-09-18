---
updatedAt: 2026-07-31T03:25:47.000Z
---

Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

# Search variants with advanced filters

> 🚧 **Beta — subject to change.** This endpoint is publicly available, but its request/response shape may evolve before General Availability as we incorporate early feedback.

Searches variants using a structured filter body with nested logical operators (`and`, `or`) and per-field comparators. Use this when the flat query parameters on `GET /variants` aren’t expressive enough.

Only the fields listed in the request schema may appear in `filter` and `order`; unknown fields return 422. Custom field values are addressable via `custom_fields.<uuid>` nested paths.

The response differs from `GET /variants`: the item reference is a single `item_id` with an `item_type` discriminator (rather than separate `product_id`/`material_id`), and the optional enriched item is returned under `item`. Use the `include` array to opt into `item` enrichment and to widen the result set to `archived` and/or `deleted` variants (both are excluded by default).

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
    "/variants/search": {
      "post": {
        "summary": "Search variants with advanced filters",
        "tags": [
          "Variant"
        ],
        "description": "> 🚧 **Beta — subject to change.** This endpoint is publicly available, but its request/response shape may evolve before General Availability as we incorporate early feedback.\n\nSearches variants using a structured filter body with nested logical operators (`and`, `or`) and per-field comparators. Use this when the flat query parameters on `GET /variants` aren’t expressive enough.\n\nOnly the fields listed in the request schema may appear in `filter` and `order`; unknown fields return 422. Custom field values are addressable via `custom_fields.<uuid>` nested paths.\n\nThe response differs from `GET /variants`: the item reference is a single `item_id` with an `item_type` discriminator (rather than separate `product_id`/`material_id`), and the optional enriched item is returned under `item`. Use the `include` array to opt into `item` enrichment and to widen the result set to `archived` and/or `deleted` variants (both are excluded by default).",
        "operationId": "searchVariants",
        "requestBody": {
          "description": "Structured filter body. See the schema for the field allowlist, the operator allowlist, and value caps.",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "properties": {
                  "filter": {
                    "type": "object",
                    "description": "Filter clause. Only the fields listed below may appear here — unknown fields are rejected with 422. Custom field values can also be addressed via `custom_fields.<uuid>` nested keys, where `<uuid>` is the custom field definition id.",
                    "properties": {
                      "and": {
                        "type": "array",
                        "description": "Logical AND — every nested clause must match. Maximum nesting depth: 2.",
                        "items": {
                          "type": "object"
                        }
                      },
                      "or": {
                        "type": "array",
                        "description": "Logical OR — at least one nested clause must match. Maximum nesting depth: 2.",
                        "items": {
                          "type": "object"
                        }
                      },
                      "id": {
                        "anyOf": [
                          {
                            "anyOf": [
                              {
                                "type": "string",
                                "maxLength": 256
                              },
                              {
                                "type": "number"
                              },
                              {
                                "type": "boolean"
                              }
                            ],
                            "nullable": true
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "neq": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Not equal"
                              },
                              "gt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than"
                              },
                              "gte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than or equal"
                              },
                              "lt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than"
                              },
                              "lte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than or equal"
                              },
                              "inq": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is in this list (max 100 entries)."
                              },
                              "nin": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is not in this list (max 100 entries)."
                              },
                              "between": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Inclusive range `[low, high]`."
                              },
                              "like": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-sensitive. Use `%` for any sequence and `_` for any single character."
                              },
                              "ilike": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-insensitive. Use `%` for any sequence and `_` for any single character."
                              }
                            }
                          }
                        ],
                        "description": "Variant id."
                      },
                      "sku": {
                        "anyOf": [
                          {
                            "anyOf": [
                              {
                                "type": "string",
                                "maxLength": 256
                              },
                              {
                                "type": "number"
                              },
                              {
                                "type": "boolean"
                              }
                            ],
                            "nullable": true
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "neq": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Not equal"
                              },
                              "gt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than"
                              },
                              "gte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than or equal"
                              },
                              "lt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than"
                              },
                              "lte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than or equal"
                              },
                              "inq": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is in this list (max 100 entries)."
                              },
                              "nin": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is not in this list (max 100 entries)."
                              },
                              "between": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Inclusive range `[low, high]`."
                              },
                              "like": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-sensitive. Use `%` for any sequence and `_` for any single character."
                              },
                              "ilike": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-insensitive. Use `%` for any sequence and `_` for any single character."
                              }
                            }
                          }
                        ],
                        "description": "Stock keeping unit."
                      },
                      "item_id": {
                        "anyOf": [
                          {
                            "anyOf": [
                              {
                                "type": "string",
                                "maxLength": 256
                              },
                              {
                                "type": "number"
                              },
                              {
                                "type": "boolean"
                              }
                            ],
                            "nullable": true
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "neq": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Not equal"
                              },
                              "gt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than"
                              },
                              "gte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than or equal"
                              },
                              "lt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than"
                              },
                              "lte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than or equal"
                              },
                              "inq": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is in this list (max 100 entries)."
                              },
                              "nin": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is not in this list (max 100 entries)."
                              },
                              "between": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Inclusive range `[low, high]`."
                              },
                              "like": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-sensitive. Use `%` for any sequence and `_` for any single character."
                              },
                              "ilike": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-insensitive. Use `%` for any sequence and `_` for any single character."
                              }
                            }
                          }
                        ],
                        "description": "Id of the product, material, or service this variant belongs to."
                      },
                      "item_type": {
                        "anyOf": [
                          {
                            "type": "string",
                            "enum": [
                              "product",
                              "material",
                              "service"
                            ],
                            "nullable": true
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "neq": {
                                "type": "string",
                                "enum": [
                                  "product",
                                  "material",
                                  "service"
                                ],
                                "nullable": true,
                                "description": "Not equal"
                              },
                              "inq": {
                                "type": "array",
                                "items": {
                                  "type": "string",
                                  "enum": [
                                    "product",
                                    "material",
                                    "service"
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is in this list (max 100 entries)."
                              },
                              "nin": {
                                "type": "array",
                                "items": {
                                  "type": "string",
                                  "enum": [
                                    "product",
                                    "material",
                                    "service"
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is not in this list (max 100 entries)."
                              }
                            }
                          }
                        ],
                        "description": "Kind of item the variant belongs to."
                      },
                      "sales_price": {
                        "anyOf": [
                          {
                            "anyOf": [
                              {
                                "type": "string",
                                "maxLength": 256
                              },
                              {
                                "type": "number"
                              },
                              {
                                "type": "boolean"
                              }
                            ],
                            "nullable": true
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "neq": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Not equal"
                              },
                              "gt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than"
                              },
                              "gte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than or equal"
                              },
                              "lt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than"
                              },
                              "lte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than or equal"
                              },
                              "inq": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is in this list (max 100 entries)."
                              },
                              "nin": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is not in this list (max 100 entries)."
                              },
                              "between": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Inclusive range `[low, high]`."
                              },
                              "like": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-sensitive. Use `%` for any sequence and `_` for any single character."
                              },
                              "ilike": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-insensitive. Use `%` for any sequence and `_` for any single character."
                              }
                            }
                          }
                        ],
                        "description": "Sales price."
                      },
                      "purchase_price": {
                        "anyOf": [
                          {
                            "anyOf": [
                              {
                                "type": "string",
                                "maxLength": 256
                              },
                              {
                                "type": "number"
                              },
                              {
                                "type": "boolean"
                              }
                            ],
                            "nullable": true
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "neq": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Not equal"
                              },
                              "gt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than"
                              },
                              "gte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than or equal"
                              },
                              "lt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than"
                              },
                              "lte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than or equal"
                              },
                              "inq": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is in this list (max 100 entries)."
                              },
                              "nin": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is not in this list (max 100 entries)."
                              },
                              "between": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Inclusive range `[low, high]`."
                              },
                              "like": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-sensitive. Use `%` for any sequence and `_` for any single character."
                              },
                              "ilike": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-insensitive. Use `%` for any sequence and `_` for any single character."
                              }
                            }
                          }
                        ],
                        "description": "Purchase price."
                      },
                      "minimum_order_quantity": {
                        "anyOf": [
                          {
                            "anyOf": [
                              {
                                "type": "string",
                                "maxLength": 256
                              },
                              {
                                "type": "number"
                              },
                              {
                                "type": "boolean"
                              }
                            ],
                            "nullable": true
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "neq": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Not equal"
                              },
                              "gt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than"
                              },
                              "gte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than or equal"
                              },
                              "lt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than"
                              },
                              "lte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than or equal"
                              },
                              "inq": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is in this list (max 100 entries)."
                              },
                              "nin": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is not in this list (max 100 entries)."
                              },
                              "between": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Inclusive range `[low, high]`."
                              },
                              "like": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-sensitive. Use `%` for any sequence and `_` for any single character."
                              },
                              "ilike": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-insensitive. Use `%` for any sequence and `_` for any single character."
                              }
                            }
                          }
                        ],
                        "description": "Minimum order quantity."
                      },
                      "lead_time": {
                        "anyOf": [
                          {
                            "anyOf": [
                              {
                                "type": "string",
                                "maxLength": 256
                              },
                              {
                                "type": "number"
                              },
                              {
                                "type": "boolean"
                              }
                            ],
                            "nullable": true
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "neq": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Not equal"
                              },
                              "gt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than"
                              },
                              "gte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than or equal"
                              },
                              "lt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than"
                              },
                              "lte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than or equal"
                              },
                              "inq": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is in this list (max 100 entries)."
                              },
                              "nin": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is not in this list (max 100 entries)."
                              },
                              "between": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Inclusive range `[low, high]`."
                              },
                              "like": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-sensitive. Use `%` for any sequence and `_` for any single character."
                              },
                              "ilike": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-insensitive. Use `%` for any sequence and `_` for any single character."
                              }
                            }
                          }
                        ],
                        "description": "Lead time in days."
                      },
                      "internal_barcode": {
                        "anyOf": [
                          {
                            "anyOf": [
                              {
                                "type": "string",
                                "maxLength": 256
                              },
                              {
                                "type": "number"
                              },
                              {
                                "type": "boolean"
                              }
                            ],
                            "nullable": true
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "neq": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Not equal"
                              },
                              "gt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than"
                              },
                              "gte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than or equal"
                              },
                              "lt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than"
                              },
                              "lte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than or equal"
                              },
                              "inq": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is in this list (max 100 entries)."
                              },
                              "nin": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is not in this list (max 100 entries)."
                              },
                              "between": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Inclusive range `[low, high]`."
                              },
                              "like": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-sensitive. Use `%` for any sequence and `_` for any single character."
                              },
                              "ilike": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-insensitive. Use `%` for any sequence and `_` for any single character."
                              }
                            }
                          }
                        ],
                        "description": "Internal barcode."
                      },
                      "registered_barcode": {
                        "anyOf": [
                          {
                            "anyOf": [
                              {
                                "type": "string",
                                "maxLength": 256
                              },
                              {
                                "type": "number"
                              },
                              {
                                "type": "boolean"
                              }
                            ],
                            "nullable": true
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "neq": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Not equal"
                              },
                              "gt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than"
                              },
                              "gte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than or equal"
                              },
                              "lt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than"
                              },
                              "lte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than or equal"
                              },
                              "inq": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is in this list (max 100 entries)."
                              },
                              "nin": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is not in this list (max 100 entries)."
                              },
                              "between": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Inclusive range `[low, high]`."
                              },
                              "like": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-sensitive. Use `%` for any sequence and `_` for any single character."
                              },
                              "ilike": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-insensitive. Use `%` for any sequence and `_` for any single character."
                              }
                            }
                          }
                        ],
                        "description": "Registered (GTIN/EAN/UPC) barcode."
                      },
                      "supplier_item_codes": {
                        "anyOf": [
                          {
                            "anyOf": [
                              {
                                "type": "string",
                                "maxLength": 256
                              },
                              {
                                "type": "number"
                              },
                              {
                                "type": "boolean"
                              }
                            ],
                            "nullable": true
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "neq": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Not equal"
                              },
                              "inq": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is in this list (max 100 entries)."
                              },
                              "nin": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is not in this list (max 100 entries)."
                              },
                              "like": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-sensitive. Use `%` for any sequence and `_` for any single character."
                              },
                              "ilike": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-insensitive. Use `%` for any sequence and `_` for any single character."
                              }
                            }
                          }
                        ],
                        "description": "Supplier item code."
                      },
                      "abc_classification": {
                        "anyOf": [
                          {
                            "type": "string",
                            "enum": [
                              "A",
                              "B",
                              "C"
                            ],
                            "nullable": true
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "neq": {
                                "type": "string",
                                "enum": [
                                  "A",
                                  "B",
                                  "C"
                                ],
                                "nullable": true,
                                "description": "Not equal"
                              },
                              "gt": {
                                "type": "string",
                                "enum": [
                                  "A",
                                  "B",
                                  "C"
                                ],
                                "nullable": true,
                                "description": "Greater than"
                              },
                              "gte": {
                                "type": "string",
                                "enum": [
                                  "A",
                                  "B",
                                  "C"
                                ],
                                "nullable": true,
                                "description": "Greater than or equal"
                              },
                              "lt": {
                                "type": "string",
                                "enum": [
                                  "A",
                                  "B",
                                  "C"
                                ],
                                "nullable": true,
                                "description": "Less than"
                              },
                              "lte": {
                                "type": "string",
                                "enum": [
                                  "A",
                                  "B",
                                  "C"
                                ],
                                "nullable": true,
                                "description": "Less than or equal"
                              },
                              "inq": {
                                "type": "array",
                                "items": {
                                  "type": "string",
                                  "enum": [
                                    "A",
                                    "B",
                                    "C"
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is in this list (max 100 entries)."
                              },
                              "nin": {
                                "type": "array",
                                "items": {
                                  "type": "string",
                                  "enum": [
                                    "A",
                                    "B",
                                    "C"
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is not in this list (max 100 entries)."
                              },
                              "between": {
                                "type": "array",
                                "items": {
                                  "type": "string",
                                  "enum": [
                                    "A",
                                    "B",
                                    "C"
                                  ],
                                  "nullable": true
                                },
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Inclusive range `[low, high]`."
                              },
                              "like": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-sensitive. Use `%` for any sequence and `_` for any single character."
                              },
                              "ilike": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-insensitive. Use `%` for any sequence and `_` for any single character."
                              }
                            }
                          }
                        ],
                        "description": "ABC inventory classification."
                      },
                      "created_at": {
                        "anyOf": [
                          {
                            "anyOf": [
                              {
                                "type": "string",
                                "maxLength": 256
                              },
                              {
                                "type": "number"
                              },
                              {
                                "type": "boolean"
                              }
                            ],
                            "nullable": true
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "neq": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Not equal"
                              },
                              "gt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than"
                              },
                              "gte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than or equal"
                              },
                              "lt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than"
                              },
                              "lte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than or equal"
                              },
                              "inq": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is in this list (max 100 entries)."
                              },
                              "nin": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is not in this list (max 100 entries)."
                              },
                              "between": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Inclusive range `[low, high]`."
                              },
                              "like": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-sensitive. Use `%` for any sequence and `_` for any single character."
                              },
                              "ilike": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-insensitive. Use `%` for any sequence and `_` for any single character."
                              }
                            }
                          }
                        ],
                        "description": "ISO 8601 timestamp the variant was created."
                      },
                      "updated_at": {
                        "anyOf": [
                          {
                            "anyOf": [
                              {
                                "type": "string",
                                "maxLength": 256
                              },
                              {
                                "type": "number"
                              },
                              {
                                "type": "boolean"
                              }
                            ],
                            "nullable": true
                          },
                          {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "neq": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Not equal"
                              },
                              "gt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than"
                              },
                              "gte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Greater than or equal"
                              },
                              "lt": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than"
                              },
                              "lte": {
                                "anyOf": [
                                  {
                                    "type": "string",
                                    "maxLength": 256
                                  },
                                  {
                                    "type": "number"
                                  },
                                  {
                                    "type": "boolean"
                                  }
                                ],
                                "nullable": true,
                                "description": "Less than or equal"
                              },
                              "inq": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is in this list (max 100 entries)."
                              },
                              "nin": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "maxItems": 100,
                                "description": "Value is not in this list (max 100 entries)."
                              },
                              "between": {
                                "type": "array",
                                "items": {
                                  "anyOf": [
                                    {
                                      "type": "string",
                                      "maxLength": 256
                                    },
                                    {
                                      "type": "number"
                                    },
                                    {
                                      "type": "boolean"
                                    }
                                  ],
                                  "nullable": true
                                },
                                "minItems": 2,
                                "maxItems": 2,
                                "description": "Inclusive range `[low, high]`."
                              },
                              "like": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-sensitive. Use `%` for any sequence and `_` for any single character."
                              },
                              "ilike": {
                                "type": "string",
                                "maxLength": 256,
                                "description": "Pattern match, case-insensitive. Use `%` for any sequence and `_` for any single character."
                              }
                            }
                          }
                        ],
                        "description": "ISO 8601 timestamp the variant was last updated."
                      }
                    }
                  },
                  "order": {
                    "description": "Sort directive(s). Each entry is `<field> ASC|DESC` (direction defaults to ASC). Only filterable fields may be used here. `custom_fields.<uuid>` nested paths are orderable.",
                    "oneOf": [
                      {
                        "type": "string"
                      },
                      {
                        "type": "array",
                        "items": {
                          "type": "string"
                        }
                      }
                    ]
                  },
                  "limit": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 200,
                    "default": 50,
                    "description": "Page size. Defaults to 50 when omitted. Maximum 200."
                  },
                  "page": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 1,
                    "description": "1-based page number. Defaults to 1 when omitted. Pagination follows the same convention as every other paginated endpoint in the public API."
                  },
                  "include": {
                    "type": "array",
                    "description": "Related data to include and result-set widening. `item` enriches each variant with its parent item under `item`. `archived` and `deleted` include otherwise-excluded variants in the results.",
                    "items": {
                      "type": "string",
                      "enum": [
                        "item",
                        "archived",
                        "deleted"
                      ]
                    }
                  }
                }
              },
              "example": {
                "filter": {
                  "and": [
                    {
                      "item_type": {
                        "inq": [
                          "product",
                          "material"
                        ]
                      }
                    },
                    {
                      "created_at": {
                        "gte": "2026-01-01T00:00:00.000Z"
                      }
                    },
                    {
                      "custom_fields.0c8f1d6e-3c2a-4f5b-9d77-12ab34cd56ef": 2
                    }
                  ]
                },
                "include": [
                  "item"
                ],
                "order": [
                  "created_at DESC",
                  "id DESC"
                ],
                "limit": 50,
                "page": 1
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Paginated list of variants matching the filter.",
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
                      "item_id": 1,
                      "item_type": "product",
                      "minimum_order_quantity": 3,
                      "lead_time": 1,
                      "purchase_price": 0,
                      "created_at": "2020-10-23T10:37:05.085Z",
                      "updated_at": "2020-10-23T10:37:05.085Z",
                      "deleted_at": null,
                      "config_attributes": [
                        {
                          "config_name": "Type",
                          "config_value": "Standard"
                        }
                      ],
                      "custom_fields": {
                        "a1b2c3d4-1111-2222-3333-444455556666": "value"
                      },
                      "supplier_item_codes": [
                        "978-0785223085",
                        "0785223088"
                      ],
                      "internal_barcode": "0316",
                      "registered_barcode": "0785223088",
                      "abc_classification": "A",
                      "item": {
                        "id": 1,
                        "name": "Standard-hilt lightsaber",
                        "uom": "pcs",
                        "category_name": "lightsaber",
                        "type": "product",
                        "purchase_uom": "pcs",
                        "purchase_uom_conversion_rate": 1,
                        "batch_tracked": false,
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