# Purchase Order Created

**Order ID**: {id}
**Order Number**: {order_number}
**Supplier ID**: {supplier_id}
**Location ID**: {location_id}

## Summary

- **Total Cost**: ${total_cost:,.2f}
- **Currency**: {currency}
- **Status**: {status}
- **Entity Type**: {entity_type}

## Next Steps

- Use `receive_purchase_order` tool when items arrive
- Use `verify_order_document` tool to validate supplier invoice/packing slip
- Check `katana://purchase-orders` resource for status updates

______________________________________________________________________

**Status**: Purchase order created successfully
