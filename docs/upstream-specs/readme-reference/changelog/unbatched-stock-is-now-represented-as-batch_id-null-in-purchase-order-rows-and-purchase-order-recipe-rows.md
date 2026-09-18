Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

# Unbatched stock is now represented as batch_id: null in Purchase Order rows and Purchase Order recipe rows

The batch\_id field in purchase order row and purchase order recipe row batch\_transactions now accepts null to represent unbatched stock.

Previously, unbatched stock was represented by a dedicated "Unbatched" batch record with its own ID, which had to be looked up via the batches API. Going forward, batch\_id: null replaces this dedicated ID as the way to reference unbatched stock in these batch transactions. Existing unbatched batch IDs will continue to work for backward compatibility but will be normalized to null internally.

This applies to endpoints that allow creating or updating purchase order row and purchase order recipe row batch transactions, and endpoints that return them in responses - responses will also return batch\_id: null for unbatched entries.

* GET <https://api.katanamrp.com/v1/purchase_orders>
* GET <https://api.katanamrp.com/v1/purchase_orders/{id}>
* POST <https://api.katanamrp.com/v1/purchase_order_receive>
* GET <https://api.katanamrp.com/v1/purchase_order_rows>
* GET <https://api.katanamrp.com/v1/purchase_order_rows/{id}>
* GET <https://api.katanamrp.com/v1/outsourced_purchase_order_recipe_rows>
* GET <https://api.katanamrp.com/v1/outsourced_purchase_order_recipe_rows/{id}>
* PATCH <https://api.katanamrp.com/v1/outsourced_purchase_order_recipe_rows/{id}>
* POST <https://api.katanamrp.com/v1/outsourced_purchase_order_recipe_rows/{id}>

**Example request body / response body:**

```json
{
  "batch_transactions": [
    { "batch_id": 5, "quantity": 7 },
    { "batch_id": null, "quantity": 3 }
  ]
}
```

This change currently applies to Purchase Order rows and Purchase Order recipe rows and will be rolled out to other domains in upcoming updates.