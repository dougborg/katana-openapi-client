# Setting up OAuth 2.0

You'll need to set up OAuth 2.0 if you're building an integration with Katana that accesses other peoples' Katana data. You can do this in a few simple steps.

## Register your application

Reach out to Katana App Partners team to get started. Firstly, you'll need to provide your app's redirect URLs. This is the URL that we POST an authorization code to when your Katana user has authorized your app to use open API on their behalf. In other words, it's the URL that Katana will use to send the authorization code for your user.

Katana team will provide you `client_id` and `client_secret`.

## Get the authorization code

To get the authorization code, you need to send a GET request to `https://login.katanamrp.com/authorize`.

```text HTTP
GET https://login.katanamrp.com/authorize?
	scope=offline_access&
	response_type=code&
	audience=https://api.katanamrp.com&
 	client_id=<Your client ID>&
	redirect_uri=<Your redirect URI>
```

Your user will follow this link to the Katana site and be presented with the permissions your app is requesting. Once the user approves this request, they are redirected back via the redirect URLs you provided earlier.

## Trade your authorization code for an access token

The access token is a unique key used to make requests to the API.

To get an access token, the application must make a POST request to `https://login.katanamrp.com/oauth/token` with the following parameters:

* `grant_type`
* `client_id`
* `client_secret`
* `redirect_uri`
* `code`

```http HTTP
POST https://login.katanamrp.com/oauth/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&client_id=<Your client ID>&client_secret=<Your client secret>&redirect_uri=<Your redirect URI>&code=<Your authorization code>
```

## Use your token

Now that you have the access token, you can use this to execute queries on behalf of the user. Use the token in the `Authorization` header. You can find more from the general [API authentication](https://developer.katanamrp.com/reference/api-authentication) article.

## Refreshing your access token

A refresh token is a unique token returned when trading the authorization code for an access token. You must use the refresh token to request a new access token when the existing one expires.

To get an access token using a refresh token, the application must make a POST request to `https://login.katanamrp.com/oauth/token` with the following parameters:

* `grant_type`
* `client_id`
* `client_secret`
* `redirect_uri`
* `refresh_token`

```http
POST https://login.katanamrp.com/oauth/token HTTP/1.1
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&client_id=<Your client ID>&client_secret=<Your client secret>&redirect_uri=<Your redirect URI>&refresh_token=<Your refresh token>
```

> 📘
>
> When the access token is refreshed, a new refresh token is generated. The new refresh token should be stored safely and used the next time token is refreshed. Using an expired refresh token will return an error and invalidate all other refresh tokens in the chain.

> ❗
>
> Make sure to include `offline_access` scope to get the refresh token. The refresh token is omitted from request responses unless this scope is included when requesting the authorization code.

## Storing credentials and tokens

Please ensure you handle the OAuth client credentials for your app's identity with care. It is crucial to store these credentials in secure storage. Avoid hardcoding them, committing them to a code repository, or making them public.

User tokens, including both refresh tokens and access tokens used by your application, should be stored securely while [at rest](https://en.wikipedia.org/wiki/Data_at_rest). Never transmit them in plain text. To achieve secure storage, it is essential to encrypt the tokens when they are [at rest](https://en.wikipedia.org/wiki/Data_at_rest) and ensure that your data store is not publicly accessible on the Internet.

## Useful resources

Katana uses OAuth 2.0 protocol which is fully described [here ](https://datatracker.ietf.org/doc/html/rfc6749)