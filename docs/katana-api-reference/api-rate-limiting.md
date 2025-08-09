# Rate limiting

We've set API rate limits to protect Katana from API traffic spikes that could put our
systems at risk. These limits also help ensure that our platform remains stable and
usable for everyone. We evaluate the number of requests sent to an API and limit them if
they surpass the allowed amount. By default, Katana API allows 60 requests per 60
seconds . Your current rate limit quota is provided in the response headers of each
request. Header Description X-Ratelimit-Limit Number of requests available for this
application. X-Ratelimit-Remaining Number of requests remaining in quota.
X-Ratelimit-Reset The timestamp (as milliseconds since epoch) when the quota will reset.
Example cURL

# Example with the default rate limit of 30

HTTP/1.1 200 OK Content-Type: application/json X-RateLimit-Limit: 30
X-RateLimit-Remaining: 29 X-RateLimit-Reset: 1640995199

# If you make more than the allowed requests

HTTP/1.1 429 Too Many Requests Content-Type: application/json Retry-After: 15 If the
rate limit is surpassed, you will receive a 429 error code indicating that you have sent
too many requests within a period. If this happens, you will receive a 'Retry-After'
header with a value indicating how many seconds you need to wait before sending another
request. Handling Rate Limiting: Throttling on the Consumer Side To avoid hitting the
API rate limits, implement throttling in your client application. Throttling controls
the rate of outgoing requests, ensuring you do not exceed the allowed quota (60 requests
per 60 seconds by default). A simple approach is to queue your requests and release them
at a controlled interval, such as one request per second. Additionally, always check the
429 Too Many Requests response and the Retry-After header. If you receive this response,
pause sending new requests for the specified duration before retrying. By proactively
managing your request rate, you can maintain uninterrupted access to the Katana API and
avoid errors caused by exceeding rate limits.
