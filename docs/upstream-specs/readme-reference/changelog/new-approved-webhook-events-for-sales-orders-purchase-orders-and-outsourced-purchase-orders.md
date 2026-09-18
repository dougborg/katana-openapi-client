Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

# New .approved webhook events for sales orders, purchase orders, and outsourced purchase orders

You can now subscribe to order approval events via webhooks. Three new event types are available:

* sales\_order.approved
* purchase\_order.approved
* outsourced\_purchase\_order.approved

Each event fires when the corresponding order is approved in Katana, letting your integration react to approvals without polling order status.

Subscribe to them like any other event when creating or updating a webhook:

```curl
POST /webhooks
{
  "url": "https://example.com/webhooks/katana",
  "subscribed_events": ["sales_order.approved", "purchase_order.approved"]
}
```

The new events are also available on PATCH /webhooks/{id} and appear in the `subscribed_events` enum in the API reference.