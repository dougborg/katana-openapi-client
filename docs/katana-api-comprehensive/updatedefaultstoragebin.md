# Update a storage bin

**PATCH** `https://api.katanamrp.com/v1/bin_locations/{id}`

## API Specification Details

**Summary:** Update a storage bin **Description:** Updates the specified storage bin by
setting the values of the parameters passed. Any parameters not provided will be left
unchanged.

### Parameters

- **id** (path) *required*: Storage bin id

### Request Schema

```json
{
  "type": "object",
  "additionalProperties": false,
  "required": [
    "bin_name",
    "location_id"
  ],
  "properties": {
    "bin_name": {
      "type": "string"
    }
  }
}
```

### Response Examples

#### 200 Response

Storage bin updated

```json
{
  "id": 12345,
  "bin_name": "Bin-2",
  "location_id": 12346,
  "created_at": "2020-10-23T10:37:05.085Z",
  "updated_at": "2020-10-23T10:37:05.085Z",
  "deleted_at": null
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
