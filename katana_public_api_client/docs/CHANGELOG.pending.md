## Pending Changes

### feat(client): add stock adjustment rows and improve regeneration script

- Add StockAdjustmentBatchTransaction, StockAdjustmentRow schemas
- Extend StockAdjustment & UpdateStockAdjustmentRequest with reason + rows
- Regeneration script now exports utils via root __init__.py
- Insert casts & Mapping imports for clean ty type checking
- Refresh example payloads for manufacturing, purchase orders, sales returns, price
  lists, stocktakes

Issue: #178
