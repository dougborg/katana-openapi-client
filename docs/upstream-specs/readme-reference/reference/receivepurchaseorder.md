---
updatedAt: 2026-05-29T09:20:09.000Z
agentTools:
  projectIndex: https://developer.katanamrp.com/llms.txt
---

# Receive a purchase order

If you receive the items on the purchase order, you can mark the purchase order as received.
    This will update the existing purchase order rows quantities to the quantities left unreceived and
    create a new rows with the received quantities and dates. If you want to mark all rows as received and
    the order doesn’t contain batch tracked items, you can use PATCH /purchase_orders/id endpoint.
    Reverting the receive must also be done through that endpoint.

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
    "/purchase_order_receive": {
      "post": {
        "summary": "Receive a purchase order",
        "tags": [
          "Purchase order"
        ],
        "description": "If you receive the items on the purchase order, you can mark the purchase order as received.\n    This will update the existing purchase order rows quantities to the quantities left unreceived and\n    create a new rows with the received quantities and dates. If you want to mark all rows as received and\n    the order doesn’t contain batch tracked items, you can use PATCH /purchase_orders/id endpoint.\n    Reverting the receive must also be done through that endpoint.",
        "operationId": "receivePurchaseOrder",
        "requestBody": {
          "description": "receive purchase order rows details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "anyOf": [
                  {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "quantity",
                        "purchase_order_row_id"
                      ],
                      "properties": {
                        "purchase_order_row_id": {
                          "type": "integer",
                          "maximum": 2147483647
                        },
                        "quantity": {
                          "type": "number",
                          "maximum": 100000000000000000
                        },
                        "received_date": {
                          "type": "string"
                        },
                        "batch_transactions": {
                          "type": "array",
                          "deprecated": true,
                          "description": "Batch breakdown of the received quantity, in the purchase unit of the row. **Deprecated** — prefer `traceability`, which follows the same quantity rules. Cannot be combined with `traceability` on the same row.",
                          "items": {
                            "type": "object",
                            "additionalProperties": false,
                            "properties": {
                              "quantity": {
                                "maximum": 100000000000000000,
                                "type": "number"
                              },
                              "batch_id": {
                                "type": "integer",
                                "nullable": true,
                                "description": "ID of the batch to receive stock for. Use `null` to record unbatched (untraced) stock."
                              }
                            }
                          }
                        },
                        "traceability": {
                          "type": "array",
                          "description": "Batch, serial number and bin location breakdown of the received quantity, in the purchase unit of the row. Preferred over `batch_transactions`; cannot be combined with it on the same row. When neither is sent, the received quantity takes the traceability pre-assigned to the row and any quantity it leaves uncovered is received untraced. The inventory settings of the account may reject a receipt that is not fully traced (422).",
                          "items": {
                            "type": "object",
                            "additionalProperties": false,
                            "description": "One allocation entry for the received quantity. Entries replace the traceability pre-assigned to the row for this receipt.\n\n- **Non-tracked variant** — omit `traceability`, or send entries with only `bin_location_id` and `quantity` to receive into bins.\n- **Batch-tracked** — each entry sets `batch_id` and `quantity`. Use multiple entries to receive into multiple batches.\n- **Serial-tracked** — each entry sets `serial_number_id` and no `quantity`, one entry per serial number. A serial number is one unit in the stock unit of the variant, so a row with a `purchase_uom_conversion_rate` takes the row's received `quantity` × `purchase_uom_conversion_rate` serial numbers. Create serial numbers first with `POST /serial_numbers`.\n\nQuantities are in the purchase unit of the row, like the row's `quantity`, and together may not exceed it. Depending on the account's traceability settings, any quantity the entries leave uncovered is received untraced or the receipt is rejected with a 422. Each entry sets at most one of `batch_id` / `serial_number_id`.",
                            "properties": {
                              "batch_id": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 2147483647,
                                "nullable": true,
                                "description": "Batch id. Mutually exclusive with `serial_number_id`."
                              },
                              "serial_number_id": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 2147483647,
                                "nullable": true,
                                "description": "Serial number id. Mutually exclusive with `batch_id`."
                              },
                              "bin_location_id": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 2147483647,
                                "nullable": true,
                                "description": "Bin location id at the receiving location that the stock arrives in. Optional."
                              },
                              "quantity": {
                                "type": "string",
                                "description": "Positive decimal string in the purchase unit of the row. Required for batch and bin-only entries; omit it for serial entries."
                              }
                            }
                          }
                        },
                        "location_id": {
                          "type": "integer",
                          "maximum": 2147483647
                        }
                      }
                    },
                    "title": "Multiple rows",
                    "minItems": 1
                  },
                  {
                    "type": "object",
                    "additionalProperties": false,
                    "required": [
                      "quantity",
                      "purchase_order_row_id"
                    ],
                    "properties": {
                      "purchase_order_row_id": {
                        "type": "integer",
                        "maximum": 2147483647
                      },
                      "quantity": {
                        "type": "number",
                        "maximum": 100000000000000000
                      },
                      "received_date": {
                        "type": "string"
                      },
                      "batch_transactions": {
                        "type": "array",
                        "deprecated": true,
                        "description": "Batch breakdown of the received quantity, in the purchase unit of the row. **Deprecated** — prefer `traceability`, which follows the same quantity rules. Cannot be combined with `traceability` on the same row.",
                        "items": {
                          "type": "object",
                          "additionalProperties": false,
                          "properties": {
                            "quantity": {
                              "maximum": 100000000000000000,
                              "type": "number"
                            },
                            "batch_id": {
                              "type": "integer",
                              "nullable": true,
                              "description": "ID of the batch to receive stock for. Use `null` to record unbatched (untraced) stock."
                            }
                          }
                        }
                      },
                      "traceability": {
                        "type": "array",
                        "description": "Batch, serial number and bin location breakdown of the received quantity, in the purchase unit of the row. Preferred over `batch_transactions`; cannot be combined with it on the same row. When neither is sent, the received quantity takes the traceability pre-assigned to the row and any quantity it leaves uncovered is received untraced. The inventory settings of the account may reject a receipt that is not fully traced (422).",
                        "items": {
                          "type": "object",
                          "additionalProperties": false,
                          "description": "One allocation entry for the received quantity. Entries replace the traceability pre-assigned to the row for this receipt.\n\n- **Non-tracked variant** — omit `traceability`, or send entries with only `bin_location_id` and `quantity` to receive into bins.\n- **Batch-tracked** — each entry sets `batch_id` and `quantity`. Use multiple entries to receive into multiple batches.\n- **Serial-tracked** — each entry sets `serial_number_id` and no `quantity`, one entry per serial number. A serial number is one unit in the stock unit of the variant, so a row with a `purchase_uom_conversion_rate` takes the row's received `quantity` × `purchase_uom_conversion_rate` serial numbers. Create serial numbers first with `POST /serial_numbers`.\n\nQuantities are in the purchase unit of the row, like the row's `quantity`, and together may not exceed it. Depending on the account's traceability settings, any quantity the entries leave uncovered is received untraced or the receipt is rejected with a 422. Each entry sets at most one of `batch_id` / `serial_number_id`.",
                          "properties": {
                            "batch_id": {
                              "type": "integer",
                              "minimum": 0,
                              "maximum": 2147483647,
                              "nullable": true,
                              "description": "Batch id. Mutually exclusive with `serial_number_id`."
                            },
                            "serial_number_id": {
                              "type": "integer",
                              "minimum": 0,
                              "maximum": 2147483647,
                              "nullable": true,
                              "description": "Serial number id. Mutually exclusive with `batch_id`."
                            },
                            "bin_location_id": {
                              "type": "integer",
                              "minimum": 0,
                              "maximum": 2147483647,
                              "nullable": true,
                              "description": "Bin location id at the receiving location that the stock arrives in. Optional."
                            },
                            "quantity": {
                              "type": "string",
                              "description": "Positive decimal string in the purchase unit of the row. Required for batch and bin-only entries; omit it for serial entries."
                            }
                          }
                        }
                      },
                      "location_id": {
                        "type": "integer",
                        "maximum": 2147483647
                      }
                    },
                    "title": "Single row"
                  }
                ]
              }
            }
          }
        },
        "responses": {
          "204": {
            "description": "Receive purchase order rows",
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