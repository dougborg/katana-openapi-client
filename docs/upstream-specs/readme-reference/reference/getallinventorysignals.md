---
updatedAt: 2026-09-17T10:56:56.000Z
agentTools:
  projectIndex: https://developer.katanamrp.com/llms.txt
---

# List inventory replenishment signals

Returns a list of inventory replenishment signals, one per variant. Signals are account-wide,
    summed across all locations. Only variants with demand in the chosen demand window have a row, so a
    variant_id filter can return fewer rows than ids requested. A missing row means no demand in that window, not
    a missing variant. Use /inventory for a full listing.

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
        "description": "Returns a list of inventory replenishment signals, one per variant. Signals are account-wide,\n    summed across all locations. Only variants with demand in the chosen demand window have a row, so a\n    variant_id filter can return fewer rows than ids requested. A missing row means no demand in that window, not\n    a missing variant. Use /inventory for a full listing.",
        "operationId": "getAllInventorySignals",
        "parameters": [
          {
            "name": "demand_window",
            "required": false,
            "description": "The demand window in days to return signals for. Defaults to\n        30. Any other value is a 400.",
            "schema": {
              "type": "integer",
              "enum": [
                7,
                30,
                60,
                90
              ],
              "default": 30
            },
            "in": "query"
          },
          {
            "name": "variant_id",
            "required": false,
            "description": "Filters signals by valid variant ids. A variant with no demand in the chosen demand window has\n        no row, so the response can be shorter than the list you asked for.",
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
                            "description": "ID of the product or material variant the signal describes. Signals are account-wide: one row\n        per variant, summed across all locations."
                          },
                          "demand_window": {
                            "type": "integer",
                            "enum": [
                              7,
                              30,
                              60,
                              90
                            ],
                            "description": "The number of days avg_daily_demand is calculated over: 7, 30, 60 or 90. Matches the\n        demand_window query parameter, which defaults to 30."
                          },
                          "avg_daily_demand": {
                            "type": "string",
                            "description": "Quantity consumed over the last demand_window days divided by demand_window. Demand counts\n        sales, manufacturing ingredient consumption, and outsourced purchase order recipe rows. If the variant's\n        first stock movement is less than demand_window days old, the divisor is the days since that movement\n        instead. Recalculated nightly at 07:00 UTC, so it can be up to 24 hours old. The average is flat: no\n        seasonality and no trend."
                          },
                          "reorder_point": {
                            "type": "string",
                            "nullable": true,
                            "description": "The calculated stock level under which the shortfall lands inside the lead time\n        (= avg_daily_demand * lead_time_used + safety_stock). Null while the variant's demand has not yet been\n        calculated. This is not the reorder_point on the inventory object, which is the user-set safety stock."
                          },
                          "days_of_stock_left": {
                            "type": "integer",
                            "nullable": true,
                            "description": "Whole days until stock runs out at the current demand rate (= floor(in_stock /\n        avg_daily_demand)). Uses in_stock alone: it ignores committed stock and incoming supply, so it can disagree\n        with stock_risk. Null while the variant's demand has not yet been calculated."
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
                            "description": "How urgent replenishment is, as an integer from 0 to 3. Worked out from in_stock less\n        committed, plus incoming supply that lands in time, over a horizon of lead_time_used + 7 days.\n        0 = low: stock stays at or above safety stock through the horizon.\n        1 = high: stock falls below safety stock inside the horizon, but after the lead time.\n        2 = critical: stock falls below safety stock inside the lead time, so an order placed now arrives late.\n        3 = stockout: in_stock is 0 or less.\n        Stockout is checked first and the first match wins. Values are in ascending severity, so a value of 1 or\n        more means the variant needs attention. Null while the variant's demand has not yet been calculated."
                          },
                          "in_stock": {
                            "type": "string",
                            "description": "Quantity on hand, summed across all locations."
                          },
                          "committed": {
                            "type": "string",
                            "description": "Quantity already claimed by open sales and manufacturing orders, so it cannot cover the demand\n        ahead. stock_risk and safety_stock_breach_at are worked out from in_stock less committed.\n        days_of_stock_left is not."
                          },
                          "safety_stock_breach_at": {
                            "type": "string",
                            "format": "date-time",
                            "nullable": true,
                            "description": "The projected date on which in_stock less committed, counting incoming supply, falls below\n        safety stock. Set on high (1) and critical (2) rows only. Null everywhere else."
                          },
                          "expected_before_safety_stock_breach": {
                            "type": "string",
                            "nullable": true,
                            "description": "The incoming quantity that stock_risk counted. Open orders are taken in expected-date order. An\n        order counts only if it lands on or before the projected breach day, and each counted order pushes that day\n        further out. An overdue order counts as landing today. 0 means nothing incoming lands in time. Null where\n        incoming supply could not change the risk. Neither value means nothing is incoming."
                          },
                          "safety_stock": {
                            "type": "string",
                            "description": "The safety stock level set for the variant."
                          },
                          "lead_time_used": {
                            "type": "integer",
                            "description": "Lead time in days used in the calculations. The variant lead time. Where that is not set, the\n        factory default purchase lead time, then the factory default manufacturing lead time, then 14 days."
                          },
                          "lead_time_source": {
                            "type": "string",
                            "enum": [
                              "sku",
                              "system_po",
                              "system_mo",
                              "fallback"
                            ],
                            "description": "Which source supplied lead_time_used: sku (variant lead time), system_po (factory default\n        purchase lead time), system_mo (factory default manufacturing lead time) or fallback (14 days)."
                          },
                          "demand_calculated_at": {
                            "type": "string",
                            "format": "date-time",
                            "description": "When avg_daily_demand was last calculated. It dates the average, not the row. Every other field\n        updates within seconds of a change to in_stock, safety_stock or incoming supply. A lead time change is not\n        applied within seconds."
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
                      "demand_window": 30,
                      "avg_daily_demand": "3.50000000000000000000",
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