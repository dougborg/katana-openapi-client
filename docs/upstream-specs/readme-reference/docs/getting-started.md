> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Getting started with Katana API

Learn how you can use our open API to develop integrations with Katana.

The first step towards integrating Katana into your app or website is to create a Katana Professional or Professional Plus account. With an account you'll be able to:

* [Obtain API keys](https://developer.katanamrp.com/reference/api-authentication) so Katana can authenticate your integration’s API requests
* Make a test API request to confirm everything is working correctly

## Create a Katana account

In order to use the Katana API, you'll need to have be on a Professional plan or higher. If you don't have an account yet, [schedule a demo](https://katanamrp.com/talk-to-sales/) now.

## Obtain your API key

Katana authenticates your API requests using API keys attached to your account. If an API key is incorrect, outdated, or missing, Katana will return a 401 error.

#### Generate a key

1. Log in to Katana and navigate to **Settings** > **API** > **API keys**
2. Clicking on **+ Add new API key** will generate a pop-up
3. Inside the pop-up, copy your API key and (optionally) give the <br /> key a name/description

See more about [authentication](https://developer.katanamrp.com/reference/api-authentication) within the API reference.

#### Key security

Never use API keys in the frontend of your application. Doing so could make it possible for others to discover them in your source code and allow them to take unwanted control of your account. You should only use API keys on your server.

We also highly recommend removing and replacing API keys if a staff member with token access departs your company.

## Make a test API request

To check that your setup is working correctly, make a test API request using your API key to [list all sales orders](https://developer.katanamrp.com/reference/sales-order#list-all-sales-orders)

```curl
curl --request GET \
  --url https://api.katanamrp.com/v1/sales_orders \
  --header 'Accept: application/json' \
  --header 'Authorization: Bearer &lt;Your api key&gt;'
```

If everything is correct, Katana will return an array of sales order objects.

```json
{
    "data": [
        {
            "id": 1700504,
            "customer_id": 4684002,
            "order_no": "SO-1 [DEMO]",
            "source": "katana",
            "order_created_date": "2020-08-05T11:33:42.000Z",
            "delivery_date": "2020-08-05T11:33:42.000Z",
            "location_id": 19465,
            "picked_date": "2019-10-27T11:33:42.000Z",
            "invoicing_status": "notInvoiced",
            "created_at": "2021-02-04T07:40:24.754Z",
            "updated_at": "2021-02-04T11:40:02.855Z",
            "status": "NOT_SHIPPED",
            "additional_info": "",
            "sales_order_rows": [
                {
                    "id": 3711690,
                    "quantity": "1.00000",
                    "variant_id": 4162087,
                    "tax_rate_id": 53036,
                    "price_per_unit": "1250.0000000000",
                    "attributes": []
                }
            ]
        }
      ]
}
```

Once you've successfully made an API request, you’re ready to begin using Katana API.

## Working with OpenAPI Specification

The Katana API includes a [complete OpenAPI 3.0 specification](https://api.katanamrp.com/v1/openapi.json) that provides documentation for all endpoints, schemas, and authentication methods

### Import into Postman

1. Open Postman and click Import
2. Select Link and paste: [https://api.katanamrp.com/v1/openapi.json](https://api.katanamrp.com/v1/openapi.json)
3. Choose Generate collection from imported APIs
4. All endpoints will be available with pre-configured requests

### Generate a TypeScript client

```asp shell
npx openapi-typescript-codegen \
  --input https://api.katanamrp.com/v1/openapi.json \
  --output ./src/katana-api
```

<br />