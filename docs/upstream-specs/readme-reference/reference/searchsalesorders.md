# Search sales orders with advanced filters

> 🚧 **Beta — subject to change.** This endpoint is publicly available, but its request/response shape may evolve before General Availability as we incorporate early feedback.

Searches sales orders using a structured filter body with nested logical operators (`and`, `or`) and per-field comparators. Use this when the flat query parameters on `GET /sales_orders` aren’t expressive enough. The response payload matches `GET /sales_orders`.

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
    "/sales_orders/search": {
      "post": {
        "summary": "Search sales orders with advanced filters",
        "tags": [
          "Sales order"
        ],
        "description": "> 🚧 **Beta — subject to change.** This endpoint is publicly available, but its request/response shape may evolve before General Availability as we incorporate early feedback.\n\nSearches sales orders using a structured filter body with nested logical operators (`and`, `or`) and per-field comparators. Use this when the flat query parameters on `GET /sales_orders` aren’t expressive enough. The response payload matches `GET /sales_orders`.\n\nOnly the fields listed in the request schema may appear in `where` and `order`; unknown fields return 422. Custom field values are addressable via `custom_fields.<uuid>` nested paths.",
        "operationId": "searchSalesOrders",
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
                            "description": "Sales order id."
                          },
                          "order_no": {
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
                            "description": "Order number."
                          },
                          "customer_id": {
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
                            "description": "Customer id."
                          },
                          "customer_ref": {
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
                            "description": "Caller-supplied customer reference."
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
                            "description": "Location id the order ships from."
                          },
                          "status": {
                            "anyOf": [
                              {
                                "type": "string",
                                "enum": [
                                  "PENDING",
                                  "NOT_SHIPPED",
                                  "PACKED",
                                  "DELIVERED",
                                  "PARTIALLY_PACKED",
                                  "PARTIALLY_DELIVERED"
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
                                      "PENDING",
                                      "NOT_SHIPPED",
                                      "PACKED",
                                      "DELIVERED",
                                      "PARTIALLY_PACKED",
                                      "PARTIALLY_DELIVERED"
                                    ],
                                    "nullable": true,
                                    "description": "Not equal"
                                  },
                                  "gt": {
                                    "type": "string",
                                    "enum": [
                                      "PENDING",
                                      "NOT_SHIPPED",
                                      "PACKED",
                                      "DELIVERED",
                                      "PARTIALLY_PACKED",
                                      "PARTIALLY_DELIVERED"
                                    ],
                                    "nullable": true,
                                    "description": "Greater than"
                                  },
                                  "gte": {
                                    "type": "string",
                                    "enum": [
                                      "PENDING",
                                      "NOT_SHIPPED",
                                      "PACKED",
                                      "DELIVERED",
                                      "PARTIALLY_PACKED",
                                      "PARTIALLY_DELIVERED"
                                    ],
                                    "nullable": true,
                                    "description": "Greater than or equal"
                                  },
                                  "lt": {
                                    "type": "string",
                                    "enum": [
                                      "PENDING",
                                      "NOT_SHIPPED",
                                      "PACKED",
                                      "DELIVERED",
                                      "PARTIALLY_PACKED",
                                      "PARTIALLY_DELIVERED"
                                    ],
                                    "nullable": true,
                                    "description": "Less than"
                                  },
                                  "lte": {
                                    "type": "string",
                                    "enum": [
                                      "PENDING",
                                      "NOT_SHIPPED",
                                      "PACKED",
                                      "DELIVERED",
                                      "PARTIALLY_PACKED",
                                      "PARTIALLY_DELIVERED"
                                    ],
                                    "nullable": true,
                                    "description": "Less than or equal"
                                  },
                                  "inq": {
                                    "type": "array",
                                    "items": {
                                      "type": "string",
                                      "enum": [
                                        "PENDING",
                                        "NOT_SHIPPED",
                                        "PACKED",
                                        "DELIVERED",
                                        "PARTIALLY_PACKED",
                                        "PARTIALLY_DELIVERED"
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
                                        "PENDING",
                                        "NOT_SHIPPED",
                                        "PACKED",
                                        "DELIVERED",
                                        "PARTIALLY_PACKED",
                                        "PARTIALLY_DELIVERED"
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
                                        "PENDING",
                                        "NOT_SHIPPED",
                                        "PACKED",
                                        "DELIVERED",
                                        "PARTIALLY_PACKED",
                                        "PARTIALLY_DELIVERED"
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
                            "description": "Delivery status."
                          },
                          "invoicing_status": {
                            "anyOf": [
                              {
                                "type": "string",
                                "enum": [
                                  "invoiced",
                                  "partiallyInvoiced",
                                  "notInvoiced"
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
                                      "invoiced",
                                      "partiallyInvoiced",
                                      "notInvoiced"
                                    ],
                                    "nullable": true,
                                    "description": "Not equal"
                                  },
                                  "gt": {
                                    "type": "string",
                                    "enum": [
                                      "invoiced",
                                      "partiallyInvoiced",
                                      "notInvoiced"
                                    ],
                                    "nullable": true,
                                    "description": "Greater than"
                                  },
                                  "gte": {
                                    "type": "string",
                                    "enum": [
                                      "invoiced",
                                      "partiallyInvoiced",
                                      "notInvoiced"
                                    ],
                                    "nullable": true,
                                    "description": "Greater than or equal"
                                  },
                                  "lt": {
                                    "type": "string",
                                    "enum": [
                                      "invoiced",
                                      "partiallyInvoiced",
                                      "notInvoiced"
                                    ],
                                    "nullable": true,
                                    "description": "Less than"
                                  },
                                  "lte": {
                                    "type": "string",
                                    "enum": [
                                      "invoiced",
                                      "partiallyInvoiced",
                                      "notInvoiced"
                                    ],
                                    "nullable": true,
                                    "description": "Less than or equal"
                                  },
                                  "inq": {
                                    "type": "array",
                                    "items": {
                                      "type": "string",
                                      "enum": [
                                        "invoiced",
                                        "partiallyInvoiced",
                                        "notInvoiced"
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
                                        "invoiced",
                                        "partiallyInvoiced",
                                        "notInvoiced"
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
                                        "invoiced",
                                        "partiallyInvoiced",
                                        "notInvoiced"
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
                            "description": "Invoicing status."
                          },
                          "production_status": {
                            "anyOf": [
                              {
                                "type": "string",
                                "enum": [
                                  "NOT_STARTED",
                                  "NONE",
                                  "NOT_APPLICABLE",
                                  "IN_PROGRESS",
                                  "BLOCKED",
                                  "DONE"
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
                                      "NOT_STARTED",
                                      "NONE",
                                      "NOT_APPLICABLE",
                                      "IN_PROGRESS",
                                      "BLOCKED",
                                      "DONE"
                                    ],
                                    "nullable": true,
                                    "description": "Not equal"
                                  },
                                  "gt": {
                                    "type": "string",
                                    "enum": [
                                      "NOT_STARTED",
                                      "NONE",
                                      "NOT_APPLICABLE",
                                      "IN_PROGRESS",
                                      "BLOCKED",
                                      "DONE"
                                    ],
                                    "nullable": true,
                                    "description": "Greater than"
                                  },
                                  "gte": {
                                    "type": "string",
                                    "enum": [
                                      "NOT_STARTED",
                                      "NONE",
                                      "NOT_APPLICABLE",
                                      "IN_PROGRESS",
                                      "BLOCKED",
                                      "DONE"
                                    ],
                                    "nullable": true,
                                    "description": "Greater than or equal"
                                  },
                                  "lt": {
                                    "type": "string",
                                    "enum": [
                                      "NOT_STARTED",
                                      "NONE",
                                      "NOT_APPLICABLE",
                                      "IN_PROGRESS",
                                      "BLOCKED",
                                      "DONE"
                                    ],
                                    "nullable": true,
                                    "description": "Less than"
                                  },
                                  "lte": {
                                    "type": "string",
                                    "enum": [
                                      "NOT_STARTED",
                                      "NONE",
                                      "NOT_APPLICABLE",
                                      "IN_PROGRESS",
                                      "BLOCKED",
                                      "DONE"
                                    ],
                                    "nullable": true,
                                    "description": "Less than or equal"
                                  },
                                  "inq": {
                                    "type": "array",
                                    "items": {
                                      "type": "string",
                                      "enum": [
                                        "NOT_STARTED",
                                        "NONE",
                                        "NOT_APPLICABLE",
                                        "IN_PROGRESS",
                                        "BLOCKED",
                                        "DONE"
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
                                        "NOT_STARTED",
                                        "NONE",
                                        "NOT_APPLICABLE",
                                        "IN_PROGRESS",
                                        "BLOCKED",
                                        "DONE"
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
                                        "NOT_STARTED",
                                        "NONE",
                                        "NOT_APPLICABLE",
                                        "IN_PROGRESS",
                                        "BLOCKED",
                                        "DONE"
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
                            "description": "Production status of the order."
                          },
                          "source": {
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
                            "description": "Source the order was created from (e.g. `api`, `shopify`)."
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
                          "ingredient_availability": {
                            "anyOf": [
                              {
                                "type": "string",
                                "enum": [
                                  "PROCESSED",
                                  "IN_STOCK",
                                  "NOT_AVAILABLE",
                                  "EXPECTED",
                                  "NO_RECIPE",
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
                                      "PROCESSED",
                                      "IN_STOCK",
                                      "NOT_AVAILABLE",
                                      "EXPECTED",
                                      "NO_RECIPE",
                                      "NOT_APPLICABLE"
                                    ],
                                    "nullable": true,
                                    "description": "Not equal"
                                  },
                                  "gt": {
                                    "type": "string",
                                    "enum": [
                                      "PROCESSED",
                                      "IN_STOCK",
                                      "NOT_AVAILABLE",
                                      "EXPECTED",
                                      "NO_RECIPE",
                                      "NOT_APPLICABLE"
                                    ],
                                    "nullable": true,
                                    "description": "Greater than"
                                  },
                                  "gte": {
                                    "type": "string",
                                    "enum": [
                                      "PROCESSED",
                                      "IN_STOCK",
                                      "NOT_AVAILABLE",
                                      "EXPECTED",
                                      "NO_RECIPE",
                                      "NOT_APPLICABLE"
                                    ],
                                    "nullable": true,
                                    "description": "Greater than or equal"
                                  },
                                  "lt": {
                                    "type": "string",
                                    "enum": [
                                      "PROCESSED",
                                      "IN_STOCK",
                                      "NOT_AVAILABLE",
                                      "EXPECTED",
                                      "NO_RECIPE",
                                      "NOT_APPLICABLE"
                                    ],
                                    "nullable": true,
                                    "description": "Less than"
                                  },
                                  "lte": {
                                    "type": "string",
                                    "enum": [
                                      "PROCESSED",
                                      "IN_STOCK",
                                      "NOT_AVAILABLE",
                                      "EXPECTED",
                                      "NO_RECIPE",
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
                                        "PROCESSED",
                                        "IN_STOCK",
                                        "NOT_AVAILABLE",
                                        "EXPECTED",
                                        "NO_RECIPE",
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
                                        "PROCESSED",
                                        "IN_STOCK",
                                        "NOT_AVAILABLE",
                                        "EXPECTED",
                                        "NO_RECIPE",
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
                                        "PROCESSED",
                                        "IN_STOCK",
                                        "NOT_AVAILABLE",
                                        "EXPECTED",
                                        "NO_RECIPE",
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
                            "description": "Ingredient (material) availability rollup."
                          },
                          "ecommerce_order_type": {
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
                            "description": "Ecommerce platform identifier."
                          },
                          "ecommerce_store_name": {
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
                            "description": "Ecommerce store name."
                          },
                          "ecommerce_order_id": {
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
                            "description": "External order id from the ecommerce platform."
                          },
                          "tracking_number": {
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
                            "description": "Carrier tracking number."
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
                            "description": "ISO 8601 timestamp the order was created."
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
                            "description": "ISO 8601 timestamp the order was last updated."
                          },
                          "order_created_date": {
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
                            "description": "Business-meaningful order creation date (separate from `created_at`)."
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
                            "description": "Planned delivery date."
                          },
                          "picked_date": {
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
                            "description": "Date the order was picked / shipped."
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
                        "status": {
                          "inq": [
                            "NOT_SHIPPED",
                            "PACKED"
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
                  "order": [
                    "created_at DESC",
                    "id DESC"
                  ],
                  "limit": 50,
                  "page": 1
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Paginated list of sales orders matching the filter.",
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
                      "id": 12345,
                      "customer_id": 67890,
                      "order_no": "SO-1",
                      "source": "api",
                      "status": "NOT_SHIPPED",
                      "currency": "USD",
                      "total": "199.99",
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