# Authentication

The Katana API uses token-based authentication, which means that API keys must be
included in the Authorization header of all requests. Any request without a valid key
will fail. Authentication for custom integrations To generate a live API key: Log in to
your Katana account Go to Settings > API Select Add new API key Secure Handling of API
Keys API keys are sensitive credentials that grant access for your application. It is
crucial to follow best practices to ensure their security. This documentation outlines
the recommended approach for securely handling API keys in your application. Server-Side
Usage: API keys should only be included on your server and should never be exposed in
client-side code. Avoid embedding API keys directly into your backend code, even if it's
private. Instead use environment variables or some other mechanism, to ensure separation
of credentials from the source code. Limit Access: Restrict API key access to the
minimum number of people necessary. Grant access only to authorized individuals who
require API key usage for specific tasks or responsibilities. Treat Keys Like Passwords:
API keys should be treated as sensitive information and handled with the same level of
care as passwords. Enforce the importance of maintaining the confidentiality of API keys
and provide clear guidelines on their usage and protection. Avoid sharing API keys to
Katana staff members. Key Rotation: Implement regular key rotation as a recommended best
practice. Periodically review and update your API keys to mitigate the potential impact
of compromised keys or unauthorized access. Generate new keys, update them in the
appropriate storage mechanism (such as environment variables), and delete the old keys.
Remember, the security of your API keys directly impacts the overall security posture of
your application. By adhering to these best practices, you can minimize the risk of
unauthorized access and potential vulnerabilities. Example cURL curl --request GET \
--url https://api.katanamrp.com/v1/products \
--header 'Accept: application/json' --header 'Authorization:Bearer <API key>'
Authentication for App Partners using OAuth If you're building a publicly-available app
that accesses others' data, we require OAuth 2.0 authentication. Read more on
incorporating OAuth 2.0 into your authentication.
