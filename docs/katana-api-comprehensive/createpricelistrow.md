# Create price list rows

**POST** `https://api.katanamrp.com/v1/price_list_rows`

Create price list rows

## API Specification Details

**Summary:** Create price list rows **Description:** Add variants to a price list.

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "price_list_id",
    "price_list_rows"
  ],
  "properties": {
    "price_list_id": {
      "type": "number",
      "description": "ID of the price list where the rows will be added",
      "example": 2
    },
    "price_list_rows": {
      "type": "array",
      "description": "List of price list rows to be added",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": [
          "variant_id",
          "adjustment_method",
          "amount"
        ],
        "properties": {
          "variant_id": {
            "type": "number",
            "description": "ID of the variant"
          },
          "adjustment_method": {
            "type": "number",
            "description": "Adjustment method for the price list row",
            "enum": [
              "fixed",
              "percentage",
              "markup"
            ]
          },
          "amount": {
            "type": "number",
            "description": "Amount to be applied as discount or replaced price"
          }
        }
      }
    }
  },
  "example": {
    "price_list_id": 2,
    "price_list_rows": [
      {
        "variant_id": 223,
        "adjustment_method": "fixed",
        "amount": 5
      },
      {
        "variant_id": 224,
        "adjustment_method": "percentage",
        "amount": 50
      }
    ]
  }
}
```

### Response Examples

#### 200 Response

New price list row created

```json
[
  {
    "id": 6,
    "price_list_id": 2,
    "variant_id": 223,
    "adjustment_method": "fixed",
    "amount": 5,
    "created_at": "2024-06-25T08:53:38.864Z",
    "updated_at": "2024-06-25T08:53:38.864Z"
  },
  {
    "id": 7,
    "price_list_id": 2,
    "variant_id": 224,
    "adjustment_method": "percentage",
    "amount": 50,
    "created_at": "2024-06-25T08:53:38.864Z",
    "updated_at": "2024-06-25T08:53:38.864Z"
  },
  {
    "id": 8,
    "price_list_id": 2,
    "variant_id": 225,
    "adjustment_method": "markup",
    "amount": 10,
    "created_at": "2024-06-25T08:53:38.864Z",
    "updated_at": "2024-06-25T08:53:38.864Z"
  }
]
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
