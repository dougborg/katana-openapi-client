# Returns a list of serial numbers

**GET** `https://api.katanamrp.com/v1/serial_numbers`

Returns a list of serial numbers

## API Specification Details

**Summary:** Returns a list of serial numbers **Description:** Returns a list of serial
numbers linked to the specified resource, sorted alphabetically.

### Parameters

- **resource_type** (query) *required*: Resource type
- **resource_id** (query) *required*: Resource id
- **limit** (query): Used for pagination (default is 50)
- **page** (query): Used for pagination (default is 1)

### Response Examples

#### 200 Response

Serial numbers on the specified resource

```json
[
  {
    "id": 1,
    "transaction_id": "eb4da756-0842-4495-9118-f8135f681234",
    "serial_number": "SN1",
    "resource_type": "ManufacturingOrder",
    "resource_id": 2,
    "transaction_date": "2020-10-23T10:37:05.085Z",
    "quantity_change": 1
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

#### 404 Response

Make sure data is correct

```json
{
  "statusCode": 404,
  "name": "NotFoundError",
  "message": "Not found"
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
