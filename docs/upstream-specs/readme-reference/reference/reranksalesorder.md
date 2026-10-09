---
updatedAt: 2026-07-17T12:23:10.000Z
agentTools:
  projectIndex: https://developer.katanamrp.com/llms.txt
---

# Change a sales order's rank

Moves one or more sales orders to an exact place in the sales order list.

The sales orders in `order_ids` are placed as one consecutive block, in the order given, at the place set in `place`. The first id ends up highest in the list. All other sales orders keep their order relative to each other.

`before_id` places them directly above that sales order, and `after_id` directly below it. Sending the same request again changes nothing, so a request can be retried safely.

Only open sales orders can be reranked. A sales order moves together with its linked manufacturing orders.

To rerank more than 250 sales orders, send them in batches: the first batch with `place.position` set to `top`, each next batch with `place.after_id` set to the last id in the previous response's `order_ids`.

Sales order lists show the new order shortly after the request returns.

The request returns 422 when any of the sales orders, including the one in `before_id` or `after_id`, doesn't exist or is not open, or when `before_id` or `after_id` is one of `order_ids`.

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
    "/sales_order_rerank": {
      "post": {
        "summary": "Change a sales order's rank",
        "tags": [
          "Sales order"
        ],
        "description": "Moves one or more sales orders to an exact place in the sales order list.\n\nThe sales orders in `order_ids` are placed as one consecutive block, in the order given, at the place set in `place`. The first id ends up highest in the list. All other sales orders keep their order relative to each other.\n\n`before_id` places them directly above that sales order, and `after_id` directly below it. Sending the same request again changes nothing, so a request can be retried safely.\n\nOnly open sales orders can be reranked. A sales order moves together with its linked manufacturing orders.\n\nTo rerank more than 250 sales orders, send them in batches: the first batch with `place.position` set to `top`, each next batch with `place.after_id` set to the last id in the previous response's `order_ids`.\n\nSales order lists show the new order shortly after the request returns.\n\nThe request returns 422 when any of the sales orders, including the one in `before_id` or `after_id`, doesn't exist or is not open, or when `before_id` or `after_id` is one of `order_ids`.",
        "operationId": "reRankSalesOrder",
        "requestBody": {
          "required": true,
          "description": "The sales orders to move and where to put them",
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "order_ids",
                  "place"
                ],
                "properties": {
                  "order_ids": {
                    "description": "IDs of the sales orders to move, in the order they should appear, highest first. 1 to 250 unique IDs.",
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 250,
                    "uniqueItems": true,
                    "items": {
                      "type": "integer",
                      "minimum": 1,
                      "maximum": 2147483647
                    }
                  },
                  "place": {
                    "description": "Where to put the sales orders. Set exactly one of `position`, `before_id` or `after_id`.",
                    "type": "object",
                    "additionalProperties": false,
                    "minProperties": 1,
                    "maxProperties": 1,
                    "properties": {
                      "position": {
                        "type": "string",
                        "enum": [
                          "top",
                          "bottom"
                        ],
                        "description": "- `top` — above all other sales orders\n- `bottom` — below all other sales orders"
                      },
                      "before_id": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 2147483647,
                        "description": "ID of the sales order to place them directly above. It can't be one of `order_ids`."
                      },
                      "after_id": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 2147483647,
                        "description": "ID of the sales order to place them directly below. It can't be one of `order_ids`."
                      }
                    }
                  }
                }
              },
              "examples": {
                "top": {
                  "summary": "Move to the top",
                  "value": {
                    "order_ids": [
                      101,
                      102
                    ],
                    "place": {
                      "position": "top"
                    }
                  }
                },
                "before": {
                  "summary": "Move directly above another sales order",
                  "value": {
                    "order_ids": [
                      101,
                      102
                    ],
                    "place": {
                      "before_id": 55
                    }
                  }
                },
                "after": {
                  "summary": "Move directly below another sales order",
                  "value": {
                    "order_ids": [
                      101,
                      102
                    ],
                    "place": {
                      "after_id": 55
                    }
                  }
                },
                "bottom": {
                  "summary": "Move to the bottom",
                  "value": {
                    "order_ids": [
                      101,
                      102
                    ],
                    "place": {
                      "position": "bottom"
                    }
                  }
                }
              }
            }
          }
        },
        "responses": {
          "200": {
            "description": "Sales orders reranked",
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
                "schema": {
                  "type": "object",
                  "required": [
                    "order_ids"
                  ],
                  "properties": {
                    "order_ids": {
                      "description": "The moved sales orders in their resulting order.",
                      "type": "array",
                      "minItems": 1,
                      "uniqueItems": true,
                      "items": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 2147483647
                      }
                    }
                  }
                },
                "example": {
                  "order_ids": [
                    101,
                    102
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