# Unbatched stock is now represented as batch_id: null in Stock Adjustments

The `batch_id` field in stock adjustment `batch_transactions` now accepts `null` to represent unbatched stock.

Previously, unbatched stock was represented by a dedicated "Unbatched" batch record with its own ID, which had to be looked up via the batches API. Going forward, `batch_id: null` replaces this dedicated ID as the way to reference unbatched stock in stock adjustments. Existing unbatched batch IDs will continue to work for backward compatibility but will be normalized to `null` internally.

This applies to both creating stock adjustments (`POST /stock_adjustments`) and reading them (`GET /stock_adjustments`) — responses will also return `batch_id: null` for unbatched entries.

**Example request body:**

```json
{
  "stock_adjustment_rows": [
    {
      "variant_id": 1,
      "quantity": 10,
      "batch_transactions": [
        { "batch_id": 5, "quantity": 7 },
        { "batch_id": null, "quantity": 3 }
      ]
    }
  ]
}
```

This change currently applies to Stock Adjustments and will be rolled out to other domains in upcoming updates.