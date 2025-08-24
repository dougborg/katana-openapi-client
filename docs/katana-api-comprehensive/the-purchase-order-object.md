# The purchase order object

| Attribute                                                                                                                 | Description                                                                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| id                                                                                                                        | Unique identifier for the object.                                                                                                                 |
| status                                                                                                                    | Status of the order.                                                                                                                              |
| Possible values are “NOT_RECEIVED”, “PARTIALLY_RECEIVED”, and “RECEIVED”.                                                 |                                                                                                                                                   |
| billing_status                                                                                                            | Indicating the status of generating the bill through accounting integration to either Xero or QuickBooks Online.                                  |
| Possible values are “BILLED”, “NOT_BILLED” and “PARTIALLY_BILLED”. “PARTIALLY_BILLED” does not apply to Xero integration. |                                                                                                                                                   |
| last_document_status                                                                                                      | Status of the last e-mail sent from (O)PO card.                                                                                                   |
| Possible values are "NOT_SENT", "SENDING", "FAILED", and "SENT".                                                          |                                                                                                                                                   |
| order_no                                                                                                                  | A unique, identifying string used in the UI and controlled by the user.                                                                           |
| entity_type                                                                                                               | Either "regular" or "outsourced", depending on the purchase order type.                                                                           |
| supplier_id                                                                                                               | ID of the supplier who this order belongs to.                                                                                                     |
| currency                                                                                                                  | Currency of the purchase order.                                                                                                                   |
| Filled with supplier currency by default.                                                                                 |                                                                                                                                                   |
| expected_arrival_date                                                                                                     | The timestamp when the items are expected to arrive (in full) in your warehouse.                                                                  |
| ISO 8601 format with time and timezone must be used.                                                                      |                                                                                                                                                   |
| order_created_date                                                                                                        | The timestamp of creating the document.                                                                                                           |
| ISO 8601 format with time and timezone must be used.                                                                      |                                                                                                                                                   |
| additional_info                                                                                                           | A string attached to the object to add any internal comments, links to external files, additional instructions, etc.                              |
| location_id                                                                                                               | The ID of the location to which items are received.                                                                                               |
| ingredient_availability                                                                                                   | Status of the ingredients required to produce products on an outsourced purchase order.                                                           |
| Possible values are "PROCESSED", "IN_STOCK", "NOT_AVAILABLE", "EXPECTED", "NO_RECIPE", "NOT_APPLICABLE".                  |                                                                                                                                                   |
| Only applicable when entity_type is outsourced.                                                                           |                                                                                                                                                   |
| ingredient_expected_date                                                                                                  | The latest date of a manufacturing order production deadline or a purchasing order expected arrival date that relates to the required ingredient. |
| Only applicable when entity_type is outsourced.                                                                           |                                                                                                                                                   |
| tracking_location_id                                                                                                      | The ID location where the ingredients on the outsourced purchase order are processed.                                                             |
| Only applicable when entity_type is outsourced.                                                                           |                                                                                                                                                   |
| total                                                                                                                     | The total value of the order (including taxes) in purchase order currency.                                                                        |
| total_in_base_currency                                                                                                    | The total value of the order (including taxes) in base currency.                                                                                  |
| purchase_order_rows                                                                                                       | An array of purchase order rows.                                                                                                                  |
| created_at                                                                                                                | The timestamp when the purchase order was created.                                                                                                |
| updated_at                                                                                                                | The timestamp when the purchase order was last updated.                                                                                           |

## The purchase order row object

The purchase order row object | quantity | The quantity of items for the order line. | |
variant_id | ID of product or material variant added to the order line. | | tax_rate_id
| ID of tax added to price per unit. | | price_per_unit | The sales price of one unit
(excluding taxes) in sales order currency. | | purchase_uom | The unit used to measure
the quantity of the items (e.g. pcs, kg, m) you purchase. It can be different from the
unit used to track stock. | | purchase_uom_conversion_rate | The conversion rate between
the purchase and stock tracking UoMs. | | batch_transactions | An array of batch
transactions and their quantities. You can receive stock for the same item in multiple
batches. | | batch_transaction.batch_id | ID of the batch for the received item. | |
batch_transactions.quantity | The quantity received in a particular batch. | | total |
The total value of the purchase order row (excluding taxes) in purchase order currency.
| | total_in_base_currency | The total value of the purchase order row (excluding taxes)
in base currency. | | conversion_rate | Currency rate used to convert from purchase
order currency into factory base currency. | | conversion_date | The date of the
conversion rate used. | | received_date | The date when the items on the purchase order
row were received to your stock. | | created_at | The timestamp when the purchase order
row was created. | | updated_at | The timestamp when the purchase order row was last
updated. | | arrival_date | The timestamp when the item on the row is expected to arrive
(in full) in your warehouse. ISO 8601 format with time and timezone must be used. |
