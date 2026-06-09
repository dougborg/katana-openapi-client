> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Update a manufacturing order operation row

Updates the specified manufacturing order operation row by setting the values of the parameters passed.
    Any parameters not provided will be left unchanged. Only completed_by_operators and total_actual_time can be
    updated when the manufacturing order status is DONE

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
    "/manufacturing_order_operation_rows/{id}": {
      "patch": {
        "summary": "Update a manufacturing order operation row",
        "tags": [
          "Manufacturing order operation"
        ],
        "description": "Updates the specified manufacturing order operation row by setting the values of the parameters passed.\n    Any parameters not provided will be left unchanged. Only completed_by_operators and total_actual_time can be\n    updated when the manufacturing order status is DONE",
        "operationId": "updateManufacturingOrderOperationRow",
        "requestBody": {
          "description": "manufacturing order details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "manufacturing_order_id",
                  "status"
                ],
                "properties": {
                  "operation_id": {
                    "type": "number",
                    "description": "If operation ID is used to map the operation, then operation_name is ignored."
                  },
                  "operation_name": {
                    "type": "string",
                    "description": "If operation name is used to map the operation then we match to the existing operations by name.\n        If a match is not found, a new one is created."
                  },
                  "type": {
                    "type": "string",
                    "enum": [
                      "process",
                      "setup",
                      "perUnit",
                      "fixed"
                    ],
                    "description": "Different operation types allows you to use different cost calculations depending on the type of product operation<br/>\n        Process: The process operation type is best for when products are individually built and time is the main driver of cost.<br/>\n        Setup: The setup operation type is best for setting up a machine for production where the production quantity doesn't affect cost.<br/>\n        Per unit: The per unit operation type is best when cost of time isn't a factor, but only the quantity of product made.<br/>\n        Fixed cost: The fixed cost operation type is useful for adding the expected extra costs that go into producing a product.\n      "
                  },
                  "resource_id": {
                    "type": "number",
                    "description": "If resource ID is used to map the resource, then resource_name is ignored."
                  },
                  "resource_name": {
                    "type": "string",
                    "description": "If resource name is used to map the resource then we match to the existing resources by name.\n        If a match is not found, a new one is created."
                  },
                  "planned_time_parameter": {
                    "type": "number",
                    "maximum": 10000000000000000,
                    "description": "The planned duration of an operation, in seconds, to either manufacture one unit of a product or\n        complete a manufacturing order (based on type)."
                  },
                  "planned_time_per_unit": {
                    "type": "number",
                    "maximum": 10000000000000000,
                    "deprecated": true,
                    "description": "(This field is deprecated in favor of planned_time_parameter)\n        The planned duration of an operation, in seconds, to either manufacture one unit of a product or\n         complete a manufacturing order (based on type)\n      "
                  },
                  "total_actual_time": {
                    "type": "number",
                    "maximum": 10000000000000000
                  },
                  "cost_parameter": {
                    "type": "number",
                    "description": "The expected cost of an operation, either total or per hour/unit of product (based on type).<br/>\n        Total cost of the operation on a manufacturing order is calculated as follows:<br/>\n        process: cost = cost_parameter x planned_time_parameter (in hours) x product quantity<br/>\n        setup: cost = cost_parameter x planned_time_parameter (in hours)<br/>\n        perUnit: cost = cost_parameter x product quantity<br/>\n        fixed: cost = cost_parameter\n      "
                  },
                  "cost_per_hour": {
                    "type": "number",
                    "deprecated": true,
                    "description": "(This field is deprecated in favor of cost_parameter)\n        The expected cost of an operation, either total or per hour/unit of product (based on type).<br/>\n        Total cost of the operation on a manufacturing order is calculated as follows:<br/>\n        process: cost = cost_parameter x planned_time_parameter (in hours) x product quantity<br/>\n        setup: cost = cost_parameter x planned_time_parameter (in hours)<br/>\n        perUnit: cost = cost_parameter x product quantity<br/>\n        fixed: cost = cost_parameter\n      "
                  },
                  "status": {
                    "type": "string",
                    "enum": [
                      "NOT_STARTED",
                      "BLOCKED",
                      "IN_PROGRESS",
                      "PAUSED",
                      "COMPLETED"
                    ]
                  },
                  "assigned_operators": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "operator_id": {
                          "type": "number",
                          "description": "If operator ID is used to map the operator, then name is ignored."
                        },
                        "name": {
                          "type": "string",
                          "description": "If operator name is used to map the operator then we match to the existing operators by name."
                        }
                      }
                    }
                  },
                  "completed_by_operators": {
                    "type": "array",
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "properties": {
                        "operator_id": {
                          "type": "number",
                          "description": "If operator ID is used to map the operator, then name is ignored."
                        },
                        "name": {
                          "type": "string",
                          "description": "If operator name is used to map the operator then we match to the existing operators by name."
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        },
        "parameters": [
          {
            "name": "id",
            "required": true,
            "description": "manufacturing order operation id",
            "schema": {
              "type": "integer"
            },
            "in": "path"
          }
        ],
        "responses": {
          "200": {
            "description": "New manufacturing order operation row",
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
                  "moOperationRowResponseExample": {
                    "id": 1,
                    "status": "IN_PROGRESS",
                    "type": "process",
                    "rank": 1,
                    "manufacturing_order_id": 1,
                    "operation_id": 1,
                    "operation_name": "Pack",
                    "resource_id": 1,
                    "resource_name": "Table",
                    "assigned_operators": [
                      {
                        "operator_id": 1,
                        "name": "Pack",
                        "deleted_at": null
                      }
                    ],
                    "completed_by_operators": [],
                    "active_operator_id": 1,
                    "planned_time_per_unit": 1,
                    "planned_time_parameter": 1,
                    "total_actual_time": 1,
                    "planned_cost_per_unit": 1,
                    "total_actual_cost": 1,
                    "cost_per_hour": 1,
                    "cost_parameter": 1,
                    "group_boundary": 1000,
                    "is_status_actionable": true,
                    "completed_at": "2020-10-23T10:37:05.085Z",
                    "created_at": "2020-10-23T10:37:05.085Z",
                    "updated_at": "2020-10-23T10:37:05.085Z",
                    "deleted_at": null
                  }
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