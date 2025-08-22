# The stock adjustment object

| Attribute                                            | Description                                                                                                          |
| ---------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| id                                                   | Unique identifier for the object.                                                                                    |
| stock_adjustment_date                                | The timestamp when the adjustments for the "In stock" quantity of products and materials are recorded.               |
| ISO 8601 format with time and timezone must be used. |                                                                                                                      |
| location_id                                          | ID the stock location being adjusted.                                                                                |
| stock_adjustment_number                              | A string used to identify the stock adjustment.                                                                      |
| reason                                               | A descriptive field for your own information to enable better identification.                                        |
| additional_info                                      | A string attached to the object to add any internal comments, links to external files, additional instructions, etc. |
| stock_adjustment_rows                                | An array of stock adjustment rows.                                                                                   |
| created_at                                           | The timestamp when the stock adjustment was created.                                                                 |
| updated_at                                           | The timestamp when the stock adjustment was last updated.                                                            |

## The stock adjustment row object

The stock adjustment row object | variant_id | ID of product or material variant added
to the stock adjustment row. | | quantity | The quantity by which the stock is adjusted.
| | cost_per_unit | Unit cost of the item. The default value is set to the current
average cost of the item in stock. | | batch_transactions | An array of batch
transactions and their quantities. You can adjust stock for the same item from multiple
batches. | | batch_transaction.batch_id | ID of the batch for the adjusted item. | |
batch_transactions.quantity | The quantity adjusted from a particular batch. |
