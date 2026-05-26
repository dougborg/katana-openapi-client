# Search sales order rows with advanced filters

> 🚧 **Beta — subject to change.** This endpoint is publicly available, but its request/response shape may evolve before General Availability as we incorporate early feedback.

Searches sales order rows using a structured filter body with nested logical operators (`and`, `or`) and per-field comparators. Use this when the flat query parameters on `GET /sales_order_rows` aren’t expressive enough. The response payload matches `GET /sales_order_rows`.

Only the fields listed in the request schema may appear in `where` and `order`; unknown fields return 422. Custom field values are addressable via `custom_fields.<uuid>` nested paths.

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
    "/sales_order_rows/search": {
      "post": {
        "summary": "Search sales order rows with advanced filters",
        "tags": [
          "Sales order row"
        ],
        "description": "> 🚧 **Beta — subject to change.** This endpoint is publicly available, but its request/response shape may evolve before General Availability as we incorporate early feedback.\n\nSearches sales order rows using a structured filter body with nested logical operators (`and`, `or`) and per-field comparators. Use this when the flat query parameters on `GET /sales_order_rows` aren’t expressive enough. The response payload matches `GET /sales_order_rows`.\n\nOnly the fields listed in the request schema may appear in `where` and `order`; unknown fields return 422. Custom field values are addressable via `custom_fields.<uuid>` nested paths.",
        "operationId": "searchSalesOrderRows",
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
                    "additionalProperties": false,
                    "properties": {
                      "where": {
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
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "Sales order row id."
                          },
                          "sales_order_id": {
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
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "Parent sales order id."
                          },
                          "variant_id": {
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
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "Variant id sold on this row."
                          },
                          "location_id": {
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
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "Location id this row ships from."
                          },
                          "tax_rate_id": {
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
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "Tax rate id applied to this row."
                          },
                          "quantity": {
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
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "Ordered quantity."
                          },
                          "price_per_unit": {
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
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "Unit price."
                          },
                          "total_discount": {
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
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "Total discount applied to this row."
                          },
                          "tax_rate": {
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
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "Tax rate percentage applied to this row."
                          },
                          "currency": {
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
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "ISO 4217 currency code."
                          },
                          "product_availability": {
                            "anyOf": [
                              {
                                "type": "string",
                                "enum": [
                                  "IN_STOCK",
                                  "EXPECTED",
                                  "PICKED",
                                  "NOT_AVAILABLE",
                                  "NOT_APPLICABLE"
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
                                      "IN_STOCK",
                                      "EXPECTED",
                                      "PICKED",
                                      "NOT_AVAILABLE",
                                      "NOT_APPLICABLE"
                                    ],
                                    "nullable": true,
                                    "description": "Not equal"
                                  },
                                  "gt": {
                                    "type": "string",
                                    "enum": [
                                      "IN_STOCK",
                                      "EXPECTED",
                                      "PICKED",
                                      "NOT_AVAILABLE",
                                      "NOT_APPLICABLE"
                                    ],
                                    "nullable": true,
                                    "description": "Greater than"
                                  },
                                  "gte": {
                                    "type": "string",
                                    "enum": [
                                      "IN_STOCK",
                                      "EXPECTED",
                                      "PICKED",
                                      "NOT_AVAILABLE",
                                      "NOT_APPLICABLE"
                                    ],
                                    "nullable": true,
                                    "description": "Greater than or equal"
                                  },
                                  "lt": {
                                    "type": "string",
                                    "enum": [
                                      "IN_STOCK",
                                      "EXPECTED",
                                      "PICKED",
                                      "NOT_AVAILABLE",
                                      "NOT_APPLICABLE"
                                    ],
                                    "nullable": true,
                                    "description": "Less than"
                                  },
                                  "lte": {
                                    "type": "string",
                                    "enum": [
                                      "IN_STOCK",
                                      "EXPECTED",
                                      "PICKED",
                                      "NOT_AVAILABLE",
                                      "NOT_APPLICABLE"
                                    ],
                                    "nullable": true,
                                    "description": "Less than or equal"
                                  },
                                  "inq": {
                                    "type": "array",
                                    "items": {
                                      "type": "string",
                                      "enum": [
                                        "IN_STOCK",
                                        "EXPECTED",
                                        "PICKED",
                                        "NOT_AVAILABLE",
                                        "NOT_APPLICABLE"
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
                                        "IN_STOCK",
                                        "EXPECTED",
                                        "PICKED",
                                        "NOT_AVAILABLE",
                                        "NOT_APPLICABLE"
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
                                        "IN_STOCK",
                                        "EXPECTED",
                                        "PICKED",
                                        "NOT_AVAILABLE",
                                        "NOT_APPLICABLE"
                                      ],
                                      "nullable": true
                                    },
                                    "minItems": 2,
                                    "maxItems": 2,
                                    "description": "Inclusive range `[low, high]`."
                                  },
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "Product availability rollup."
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
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "ISO 8601 timestamp the row was created."
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
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "ISO 8601 timestamp the row was last updated."
                          },
                          "delivery_date": {
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
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "Planned delivery date for this row."
                          },
                          "shipping_date": {
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
                                  "exists": {
                                    "type": "boolean",
                                    "description": "Match rows where this field is non-null (true) or null (false)."
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
                            "description": "Actual shipping date for this row."
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
                      }
                    }
                  }
                }
              },
              "example": {
                "filter": {
                  "where": {
                    "and": [
                      {
                        "sales_order_id": {
                          "inq": [
                            12345,
                            12346,
                            12347
                          ]
                        }
                      },
                      {
                        "quantity": {
                          "gt": 0
                        }
                      },
                      {
                        "product_availability": "IN_STOCK"
                      }
                    ]
                  },
                  "order": [
                    "delivery_date ASC",
                    "id ASC"
                  ],
                  "limit": 100,
                  "page": 1
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Paginated list of sales order rows matching the filter.",
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
                      "id": 98765,
                      "sales_order_id": 12345,
                      "variant_id": 6440195,
                      "quantity": "2",
                      "price_per_unit": "99.99",
                      "total": "199.98",
                      "tax_rate_id": null,
                      "created_at": "2026-05-14T08:00:00.000Z",
                      "updated_at": "2026-05-14T08:00:00.000Z"
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