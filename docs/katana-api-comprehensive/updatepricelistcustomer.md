# Update a price list customer

**PATCH** `https://api.katanamrp.com/v1/price_list_customers/{id}`

Update a price list customer

## API Specification Details

**Summary:** Update a price list customer **Description:** Updates the specified price
list customer by setting the values of the parameters passed. Any parameters not
provided will be left unchanged.

### Parameters

- **id** (path) *required*: Price list ID

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "properties": {
    "customer_id": {
      "type": "number",
      "description": "ID of the customer"
    }
  },
  "example": {
    "customer_id": 224
  }
}
```

### Response Examples

#### 200 Response

Price list customer updated

```json
{
  "id": 6,
  "price_list_id": 2,
  "customer_id": 224,
  "created_at": "2024-06-25T08:53:38.864Z",
  "updated_at": "2024-06-26T04:23:38.123Z"
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
