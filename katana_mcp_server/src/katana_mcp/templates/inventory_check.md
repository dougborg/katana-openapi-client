# Inventory Check

**SKU**: {sku} **Product**: {product_name}

| Metric | Quantity |
|--------|----------|
| **In Stock** | {in_stock} |
| **Available** | {available_stock} |
| **Committed** | {committed} |
| **Expected** | {expected} |

## Next Steps

- Use `create_purchase_order` to reorder if stock is low
- Use `list_low_stock_items` to check other items
