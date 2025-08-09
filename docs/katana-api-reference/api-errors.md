# HTTP status codes

Katana API uses standard HTTP status codes to indicate the success or failure of API
requests. Katana will return an error with the corresponding status code if a request
fails. In general, there are three status code ranges one can expect: 2xx success status
codes confirm that a request worked as expected 4xx error status codes indicate an error
related to the information provided (e.g., a required parameter was omitted) 5xx error
status codes are uncommon and would indicate an error with our servers 🚧 4xx and 5xx
responses may be returned for any request and clients should be ready to cater to them.
All errors return with this same structure: JSON { "error": { "statusCode":
\<STATUS_CODE> "name": \<ERROR_NAME>, "code": \<ERROR_CODE>, "details": \<DETAILS - NOT
ALWAYS PRESENT> } } Example HTTP HTTP/1.1 422 Unprocessable Entity Content-Type:
application/json

{ "error": { "statusCode": 422, "name": "UnprocessableEntityError", "message": "The
request body is invalid. See error object `details` property for more info.", "code":
"VALIDATION_FAILED", "details": \[ { "path": ".city", "code": "maxLength", "message":
"should NOT be longer than 10 characters", "info": { "limit": 10 } } \] } } If you
encounter an error, the response will contain an error object with the following
attributes: Key Description statusCode A number indicating the HTTP error code. name
Name of the error. message Human readable description of the error. code The type of
error returned. details The invalid fields and their associated errors. Only applies to
validation errors. Error codes and how to resolve them Status Code Action 400 Make sure
your request is formatted correctly. 401 Make sure your API token is correctly entered.
404 Make sure the URI is formatted correctly. 422 Check the details property for a
specific error message. 429 The rate limit has been reached. Please try again later. 500
The server encountered an error. If this persists, please contact support.
