# Create product operations

Create one or many new product operation rows for a product.
    The endpoint accepts up to 150 product operation rows and processes them in bulk.
    If rows are successfully created, 204 is returned.

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
    "/product_operation_rows/": {
      "post": {
        "summary": "Create product operations",
        "tags": [
          "Product operation"
        ],
        "description": "Create one or many new product operation rows for a product.\n    The endpoint accepts up to 150 product operation rows and processes them in bulk.\n    If rows are successfully created, 204 is returned.",
        "operationId": "createProductOperationRows",
        "requestBody": {
          "description": "new product operation row details",
          "required": true,
          "content": {
            "application/json": {
              "schema": {
                "type": "object",
                "additionalProperties": false,
                "required": [
                  "rows"
                ],
                "properties": {
                  "keep_current_rows": {
                    "type": "boolean",
                    "description": "Existing production operation lines are kept by default,\n        and new lines will be added after the existing product operations.\n        Set to false to delete all existing product operation lines for related products."
                  },
                  "rows": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 150,
                    "items": {
                      "type": "object",
                      "additionalProperties": false,
                      "required": [
                        "product_variant_id"
                      ],
                      "properties": {
                        "product_variant_id": {
                          "type": "number",
                          "minimum": 1,
                          "maximum": 2147483647
                        },
                        "operation_id": {
                          "description": "If operation ID is used to map the operation, then operation_name is ignored.",
                          "type": "integer",
                          "minimum": 1,
                          "maximum": 2147483647
                        },
                        "operation_name": {
                          "description": "If operation name is used to map the operation then,\n            we match to the existing operations by name. If a match is not found, a new one is created.",
                          "type": "string"
                        },
                        "resource_id": {
                          "description": "If resource ID is used to map the resource, then resource_name is ignored.",
                          "type": "integer",
                          "minimum": 1,
                          "maximum": 2147483647
                        },
                        "resource_name": {
                          "description": "If resource name is used to map the resource then we match to the existing resources by name.\n              If a match is not found, a new one is created.",
                          "type": "string"
                        },
                        "type": {
                          "type": "string",
                          "description": "Different operation types allows you to use different cost calculations depending on the type of product operation<br/>\n              Process: The process operation type is best for when products are individually built and time is the main driver of cost.<br/>\n              Setup: The setup operation type is best for setting up a machine for production where the production quantity doesn't affect cost.<br/>\n              Per unit: The per unit operation type is best when cost of time isn't a factor, but only the quantity of product made.<br/>\n              Fixed cost: The fixed cost operation type is useful for adding the expected extra costs that go into producing a product.\n            ",
                          "enum": [
                            "process",
                            "setup",
                            "perUnit",
                            "fixed"
                          ],
                          "default": "process"
                        },
                        "cost_parameter": {
                          "type": "number",
                          "description": "The expected cost of an operation, either total or per hour/unit of product (based on type). Total cost of the operation on a manufacturing order is calculated as follows:<br/>\n              process: cost = cost_parameter x planned_time_parameter (in hours) x product quantity<br/>\n              setup: cost = cost_parameter x planned_time_parameter (in hours)<br/>\n              perUnit: cost = cost_parameter x product quantity<br/>\n              fixed: cost = cost_parameter\n            ",
                          "maximum": 1000000000000000000,
                          "minimum": 0
                        },
                        "cost_per_hour": {
                          "type": "number",
                          "deprecated": true,
                          "description": "(This field is deprecated in favor of cost_parameter) The expected cost of an operation, either total or per hour/unit of product (based on type). Total cost of the operation on a manufacturing order is calculated as follows:<br/>\n              process: cost = cost_parameter x planned_time_parameter (in hours) x product quantity<br/>\n              setup: cost = cost_parameter x planned_time_parameter (in hours)<br/>\n              perUnit: cost = cost_parameter x product quantity<br/>\n              fixed: cost = cost_parameter\n            ",
                          "maximum": 1000000000000000000,
                          "minimum": 0
                        },
                        "planned_time_parameter": {
                          "type": "integer",
                          "description": "The planned duration of an operation, in seconds, to either manufacture one unit of a product or complete a manufacturing order (based on type).",
                          "maximum": 2147483647,
                          "minimum": 0
                        },
                        "planned_time_per_unit": {
                          "type": "integer",
                          "deprecated": true,
                          "description": "(This field is deprecated in favor of planned_time_parameter) The planned duration of an operation, in seconds, to either manufacture one unit of a product or complete a manufacturing order (based on type).",
                          "maximum": 2147483647,
                          "minimum": 0
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
          "204": {
            "description": "New product operation rows were successfully added",
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