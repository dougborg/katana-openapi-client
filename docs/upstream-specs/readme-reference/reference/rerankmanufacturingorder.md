---
updatedAt: 2026-07-17T07:44:14.000Z
agentTools:
  projectIndex: https://developer.katanamrp.com/llms.txt
---

# Change a manufacturing order's rank

Moves one or more manufacturing orders to an exact place in the production schedule.

The manufacturing orders in `order_ids` are placed as one consecutive block, in the order given, at the place set in `place`. The first id ends up highest in the schedule. All other manufacturing orders keep their order relative to each other.

`before_id` places them directly above that manufacturing order, and `after_id` directly below it. Sending the same request again changes nothing, so a request can be retried safely.

Only open manufacturing orders can be reranked.

Manufacturing orders linked to the same sales order always stay together. Listing one of them moves all of them, placed where the first of them is listed and keeping their order among themselves, and the response includes all of them, so it can list more than 250 ids. When `before_id` or `after_id` is a manufacturing order linked to a sales order, the orders are placed above or below all manufacturing orders of that sales order.

To rerank more than 250 manufacturing orders, send them in batches: the first batch with `place.position` set to `top`, each next batch with `place.after_id` set to the last id in the previous response's `order_ids`. Keep manufacturing orders linked to the same sales order in the same batch.

Manufacturing order lists show the new order shortly after the request returns.

The request returns 422 when any of the manufacturing orders, including the one in `before_id` or `after_id`, doesn't exist or is not open, or when `before_id` or `after_id` is one of `order_ids` or is linked to the same sales order as one of them.

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
    "/manufacturing_order_rerank": {
      "post": {
        "summary": "Change a manufacturing order's rank",
        "tags": [
          "Manufacturing order"
        ],
        "description": "Moves one or more manufacturing orders to an exact place in the production schedule.\n\nThe manufacturing orders in `order_ids` are placed as one consecutive block, in the order given, at the place set in `place`. The first id ends up highest in the schedule. All other manufacturing orders keep their order relative to each other.\n\n`before_id` places them directly above that manufacturing order, and `after_id` directly below it. Sending the same request again changes nothing, so a request can be retried safely.\n\nOnly open manufacturing orders can be reranked.\n\nManufacturing orders linked to the same sales order always stay together. Listing one of them moves all of them, placed where the first of them is listed and keeping their order among themselves, and the response includes all of them, so it can list more than 250 ids. When `before_id` or `after_id` is a manufacturing order linked to a sales order, the orders are placed above or below all manufacturing orders of that sales order.\n\nTo rerank more than 250 manufacturing orders, send them in batches: the first batch with `place.position` set to `top`, each next batch with `place.after_id` set to the last id in the previous response's `order_ids`. Keep manufacturing orders linked to the same sales order in the same batch.\n\nManufacturing order lists show the new order shortly after the request returns.\n\nThe request returns 422 when any of the manufacturing orders, including the one in `before_id` or `after_id`, doesn't exist or is not open, or when `before_id` or `after_id` is one of `order_ids` or is linked to the same sales order as one of them.",
        "operationId": "reRankManufacturingOrder",
        "requestBody": {
          "required": true,
          "description": "The manufacturing orders to move and where to put them",
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
                    "description": "IDs of the manufacturing orders to move, in the order they should appear, highest first. 1 to 250 unique IDs.",
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
                    "description": "Where to put the manufacturing orders. Set exactly one of `position`, `before_id` or `after_id`.",
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
                        "description": "- `top` — above all other manufacturing orders\n- `bottom` — below all other manufacturing orders"
                      },
                      "before_id": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 2147483647,
                        "description": "ID of the manufacturing order to place them directly above. When it is linked to a sales order, they go above all manufacturing orders of that sales order. It can't be one of `order_ids` or linked to the same sales order as one of them."
                      },
                      "after_id": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 2147483647,
                        "description": "ID of the manufacturing order to place them directly below. When it is linked to a sales order, they go below all manufacturing orders of that sales order. It can't be one of `order_ids` or linked to the same sales order as one of them."
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
                  "summary": "Move directly above another manufacturing order",
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
                  "summary": "Move directly below another manufacturing order",
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
            "description": "Manufacturing orders reranked",
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
                      "description": "The moved manufacturing orders in their resulting order, including manufacturing orders that moved with them because they are linked to the same sales order. It can list more than 250 ids.",
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