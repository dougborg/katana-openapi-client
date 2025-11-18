# 📄 Purchase Order Preview

**Order Number**: {order_number} **Supplier**: {supplier_name} (#{supplier_id})
**Location**: {location_name} (#{location_id}) **Status**: {status}

## Items

{items_table}

## Totals

- **Subtotal**: ${subtotal:,.2f}
- **Currency**: {currency}
- **Line Items**: {item_count}

## Notes

{notes}

## ⚠️ Preview Mode

This is a **preview only**. To create the purchase order:

- Set `confirm=true` in your request

To cancel, respond with **No** or make changes to your request.

______________________________________________________________________

**Status**: Preview - not yet created
