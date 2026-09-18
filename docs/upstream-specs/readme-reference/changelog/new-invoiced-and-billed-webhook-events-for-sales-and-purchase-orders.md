Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

# New invoiced and billed webhook events for sales and purchase orders

You can now subscribe to three new webhook events that fire when an invoice or bill is recorded against an order in your connected accounting integration (QuickBooks or Xero):

* `sales_order.invoiced` — fires when an invoice is added to or removed from a sales order.
* `purchase_order.billed` — fires when a bill is added to or removed from a purchase order.
* `outsourced_purchase_order.billed` — the same, for outsourced purchase orders.

Each event fires **once per invoice or bill**, so you get a separate notification for every invoice on an order rather than only when the order's overall status flips. The payload identifies the specific invoice or bill (`invoice_id` / `bill_id`, `integration_type`), tells you whether it was added or removed (`operation`), and includes the order's current invoicing/billing status — so an integration can react in real time instead of polling.

<br />