# The purchase order row object

| Attribute                                                                                | Description                                                                               |
| ---------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| id                                                                                       | Unique identifier for the object.                                                         |
| quantity                                                                                 | The quantity of items for the order line.                                                 |
| variant_id                                                                               | ID of product or material variant added to the order line.                                |
| tax_rate_id                                                                              | ID of tax added to price per unit.                                                        |
| group_id                                                                                 | ID of a group of purchase order rows linked by partial deliveries within a single order.  |
| Useful for tracking and managing items received in groups under the same purchase order. |                                                                                           |
| price_per_unit                                                                           | The purchase price of one unit (excluding taxes) in purchase order currency.              |
| purchase_uom                                                                             | The unit used to measure the quantity of the items (e.g. pcs, kg, m) you purchase.        |
| It can be different from the unit used to track stock.                                   |                                                                                           |
| purchase_uom_conversion_rate                                                             | The conversion rate between the purchase and stock tracking UoMs.                         |
| batch_transactions                                                                       | An array of batch transactions and their quantities.                                      |
| You can receive stock for the same item in multiple batches.                             |                                                                                           |
| batch_transaction.batch_id                                                               | ID of the batch for the received item.                                                    |
| batch_transactions.quantity                                                              | The quantity received in a particular batch.                                              |
| total                                                                                    | The total value of the purchase order row (excluding taxes) in purchase order currency.   |
| total_in_base_currency                                                                   | The total value of the purchase order row (excluding taxes) in base currency.             |
| conversion_rate                                                                          | Currency rate used to convert from purchase order currency into factory base currency.    |
| conversion_date                                                                          | The date of the conversion rate used.                                                     |
| received_date                                                                            | The date when the items on the purchase order row were received to your stock.            |
| created_at                                                                               | The timestamp when the purchase order row was created.                                    |
| updated_at                                                                               | The timestamp when the purchase order row was last updated.                               |
| arrival_date                                                                             | The timestamp when the item on the row is expected to arrive (in full) in your warehouse. |
| ISO 8601 format with time and timezone must be used.                                     |                                                                                           |
