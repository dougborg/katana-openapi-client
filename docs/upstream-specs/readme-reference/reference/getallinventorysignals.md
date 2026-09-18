---
updatedAt: 2026-09-17T10:56:56.000Z
---

Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

# List inventory replenishment signals

Returns a list of inventory replenishment signals, one per variant. Signals are account-wide,
    summed across all locations. Only variants with demand in the last 30 days
    have a row, so a variant_id filter can return fewer rows than ids requested. A missing row means no recent
    demand, not a missing variant. Use /inventory for a full listing.

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
    "/inventory_signals": {
      "get": {
        "summary": "List inventory replenishment signals",
        "tags": [
          "Inventory signals"
        ],
        "description": "Returns a list of inventory replenishment signals, one per variant. Signals are account-wide,\n    summed across all locations. Only variants with demand in the last 30 days\n    have a row, so a variant_id filter can return fewer rows than ids requested. A missing row means no recent\n    demand, not a missing variant. Use /inventory for a full listing.",
        "operationId": "getAllInventorySignals",
        "parameters": [
          {
            "name": "variant_id",
            "required": false,
            "description": "Filters signals by valid variant ids. A variant with no demand in the\n        30-day window has no row, so the response can be shorter than the\n        list you asked for.",
            "schema": {
              "type": "array",
              "items": {
                "type": "integer"
              }
            },
            "in": "query"
          },
          {
            "name": "stock_risk",
            "required": false,
            "description": "Filters signals by risk level: 0 low, 1 high, 2 critical, 3 stockout. Any other value is a 400.",
            "schema": {
              "type": "integer",
              "enum": [
                0,
                1,
                2,
                3
              ]
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
          }
        ],
        "responses": {
          "200": {
            "description": "List all inventory replenishment signals",
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
                "schema": {
                  "type": "object",
                  "properties": {
                    "data": {
                      "type": "array",
                      "items": {
                        "type": "object",
                        "properties": {
                          "variant_id": {
                            "type": "integer",
                            "description": "The variant the signal describes. One row per variant, summed across all locations."
                          },
                          "avg_daily_demand_30d": {
                            "type": "string",
                            "description": "Quantity consumed over the last 30 days divided by\n        30. Recalculated nightly at 07:00 UTC."
                          },
                          "reorder_point": {
                            "type": "string",
                            "nullable": true,
                            "description": "Calculated as avg_daily_demand_30d * lead_time_used + safety_stock. Not the reorder_point on\n        /inventory. Null while demand has not yet been calculated."
                          },
                          "days_of_stock_left": {
                            "type": "integer",
                            "nullable": true,
                            "description": "floor(in_stock / avg_daily_demand_30d). Ignores committed stock and incoming supply. Null while\n        demand has not yet been calculated."
                          },
                          "stock_risk": {
                            "type": "integer",
                            "nullable": true,
                            "enum": [
                              0,
                              1,
                              2,
                              3
                            ],
                            "description": "0 low, 1 high, 2 critical, 3 stockout. Null while demand has not yet been calculated."
                          },
                          "in_stock": {
                            "type": "string",
                            "description": "Quantity on hand, summed across all locations."
                          },
                          "committed": {
                            "type": "string",
                            "description": "Quantity claimed by open sales and manufacturing orders."
                          },
                          "safety_stock_breach_at": {
                            "type": "string",
                            "format": "date-time",
                            "nullable": true,
                            "description": "Projected date stock falls below safety stock. Set on high and critical rows only."
                          },
                          "expected_before_safety_stock_breach": {
                            "type": "string",
                            "nullable": true,
                            "description": "Incoming quantity that stock_risk counted as landing in time."
                          },
                          "safety_stock": {
                            "type": "string",
                            "description": "The safety stock level set for the variant."
                          },
                          "lead_time_used": {
                            "type": "integer",
                            "description": "Lead time in days used in the calculations."
                          },
                          "lead_time_source": {
                            "type": "string",
                            "enum": [
                              "sku",
                              "system_po",
                              "system_mo",
                              "fallback"
                            ],
                            "description": "Which source supplied lead_time_used."
                          },
                          "demand_calculated_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "When avg_daily_demand_30d was last calculated."
                          }
                        }
                      }
                    }
                  }
                },
                "example": {
                  "data": [
                    {
                      "variant_id": 1,
                      "avg_daily_demand_30d": "3.50000000000000000000",
                      "reorder_point": "49.00000000000000000000",
                      "days_of_stock_left": 12,
                      "stock_risk": 1,
                      "in_stock": "42.00000000000000000000",
                      "committed": "0.00000000000000000000",
                      "safety_stock_breach_at": "2026-08-24T00:00:00.000Z",
                      "expected_before_safety_stock_breach": "30.00000000000000000000",
                      "safety_stock": "0.00000000000000000000",
                      "lead_time_used": 14,
                      "lead_time_source": "sku",
                      "demand_calculated_at": "2026-08-12T07:00:00.000Z"
                    }
                  ]
                }
              }
            }
          },
          "400": {
            "description": "Make sure request body is not malformed, and query parameters are correct",
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
                  "statusCode": 400,
                  "name": "BadRequestError",
                  "message": "Required parameter is missing!",
                  "code": "MISSING_REQUIRED_PARAMETER"
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