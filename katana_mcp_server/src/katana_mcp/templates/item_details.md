# Item Details

**SKU**: {sku} **Name**: {name} **Type**: {item_type}

## Basic Info

- **ID**: {id}
- **Description**: {description}
- **Unit of Measure**: {uom}

## Capabilities

- **Sellable**: {is_sellable}
- **Producible**: {is_producible}
- **Purchasable**: {is_purchasable}

## Pricing

- **Sales Price**: ${sales_price:,.2f}
- **Cost**: ${cost:,.2f}

## Inventory

- **In Stock**: {in_stock}
- **Available**: {available}
- **Allocated**: {allocated}
- **On Order**: {on_order}

## Supplier Info

{supplier_info}

## Next Steps

- Use `check_inventory` for real-time stock levels
- Use `create_purchase_order` to reorder if stock is low
- Use `katana://inventory/items` to browse related items

______________________________________________________________________

**Status**: Item details retrieved
