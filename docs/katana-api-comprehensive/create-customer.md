# Create a customer

**POST** `https://api.katanamrp.com/v1/customers`

## API Specification Details

**Summary:** Create a customer **Description:** Creates a new customer object.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "name"
  ],
  "properties": {
    "name": {
      "type": "string"
    },
    "first_name": {
      "type": "string"
    },
    "last_name": {
      "type": "string"
    },
    "company": {
      "type": "string"
    },
    "email": {
      "type": "string"
    },
    "phone": {
      "type": "string"
    },
    "currency": {
      "type": "string",
      "description": "The customer\u2019s currency (ISO 4217)."
    },
    "reference_id": {
      "type": "string",
      "maxLength": 100
    },
    "category": {
      "type": "string",
      "maxLength": 100
    },
    "comment": {
      "type": "string"
    },
    "discount_rate": {
      "type": "number"
    },
    "addresses": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "entity_type"
        ],
        "properties": {
          "entity_type": {
            "type": "string",
            "enum": [
              "billing",
              "shipping"
            ]
          },
          "default": {
            "type": "boolean"
          },
          "first_name": {
            "type": "string",
            "nullable": true
          },
          "last_name": {
            "type": "string",
            "nullable": true
          },
          "company": {
            "type": "string",
            "nullable": true
          },
          "phone": {
            "type": "string",
            "nullable": true
          },
          "line_1": {
            "type": "string",
            "nullable": true
          },
          "line_2": {
            "type": "string",
            "nullable": true
          },
          "city": {
            "type": "string",
            "nullable": true
          },
          "state": {
            "type": "string",
            "nullable": true
          },
          "zip": {
            "type": "string",
            "nullable": true
          },
          "country": {
            "type": "string",
            "nullable": true
          }
        }
      }
    }
  }
}
```

### Response Examples

#### 200 Response

new customers created

```json
{
  "id": 12345,
  "name": "Luke Skywalker",
  "first_name": "Luke",
  "last_name": "Skywalker",
  "company": "Company",
  "email": "luke.skywalker@example.com",
  "comment": "Luke Skywalker was a Tatooine farmboy who rose from humble beginnings to become one of the\n            greatest Jedi the galaxy has ever known.",
  "discount_rate": 100,
  "phone": "123456",
  "currency": "USD",
  "reference_id": "ref-12345",
  "category": "category-12345",
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z",
  "deleted_at": null,
  "default_billing_id": 1,
  "default_shipping_id": 2,
  "addresses": [
    {
      "id": 1,
      "customer_id": 12345,
      "entity_type": "billing",
      "first_name": "Luke",
      "last_name": "Skywalker",
      "company": "Company",
      "phone": "123456789",
      "line_1": "Line 1",
      "line_2": "Line 2",
      "city": "City",
      "state": "State",
      "zip": "Zip",
      "country": "Country",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "created_at": "2020-10-23T10:37:05.085Z"
    },
    {
      "id": 2,
      "customer_id": 12345,
      "entity_type": "shipping",
      "first_name": "Luke",
      "last_name": "Skywalker",
      "company": "Company",
      "phone": "123456789",
      "line_1": "Line 1",
      "line_2": "Line 2",
      "city": "City",
      "state": "State",
      "zip": "Zip",
      "country": "Country",
      "updated_at": "2020-10-23T10:37:05.085Z",
      "created_at": "2020-10-23T10:37:05.085Z"
    }
  ]
}
```

#### 401 Response

Make sure you've entered your API token correctly.

```json
{
  "statusCode": 401,
  "name": "UnauthorizedError",
  "message": "Unauthorized"
}
```

#### 422 Response

Check the details property for a specific error message.

```json
{
  "statusCode": 422,
  "name": "UnprocessableEntityError",
  "message": "The request body is invalid.
  See error object `details` property for more info.",
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
```

#### 429 Response

The rate limit has been reached. Please try again later.

```json
{
  "statusCode": 429,
  "name": "TooManyRequests",
  "message": "Too Many Requests"
}
```

#### 500 Response

The server encountered an error. If this persists, please contact support

```json
{
  "statusCode": 500,
  "name": "InternalServerError",
  "message": "Internal Server Error"
}
```
