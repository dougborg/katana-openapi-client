Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

# Unbatched stock is now represented as batch_id: null in Stock Transfer rows

The batch\_id field in stock transfer row batch\_transactions now accepts null to represent unbatched stock - i.e. stock with no batch (untraced).

Previously, unbatched stock was represented by a dedicated "Unbatched" batch record with its own ID, which had to be looked up via the batches API. Going forward, batch\_id: null replaces this dedicated ID as the way to reference unbatched stock in these batch transactions. Existing unbatched batch IDs will continue to work for backward compatibility in request payload but will be normalized to null internally and in responses.

This applies to endpoints that allow creating or updating stock transfer row batch transactions, and endpoints that return them in responses — responses will also return batch\_id: null for unbatched entries.

Note: batch\_transactions for batched (traced) stock are always populated with actual batch records. Unbatched stock, however, is reported as a batch\_id: null entry only after the stock transfer has ▎ left the origin location.

* GET   <https://api.katanamrp.com/v1/stock_transfers>
* GET   <https://api.katanamrp.com/v1/stock_transfers/{id}>
* POST  <https://api.katanamrp.com/v1/stock_transfers>
* PATCH <https://api.katanamrp.com/v1/stock_transfers/{id}>

**Example request body / response body:**

```json
{
  "batch_transactions": [
    { "batch_id": 5, "quantity": 7 },
    { "batch_id": null, "quantity": 3 }
  ]
}
```

This change continues the rollout of batch\_id: null for unbatched stock across domains, following Purchase Order rows and Purchase Order recipe rows, and will be extended to other domains in upcoming updates.