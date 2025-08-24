# The stocktake row object

| Attribute                                                                                   | Description                                                         |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| id                                                                                          | Unique identifier for the object.                                   |
| variant_id                                                                                  | The ID of product or material variant being counted.                |
| batch_id                                                                                    | The ID of the batch for the counted variant.                        |
| Batch ID is a required field when counting batch trackable items.                           |                                                                     |
| stocktake_id                                                                                | The ID of the stocktake to which the order belongs.                 |
| notes                                                                                       | A string attached to the object to add any internal comments.       |
| in_stock_quantity                                                                           | Quantity in stock for that item.                                    |
| Quantity in stock is saved at the moment when the stocktake status is set to "IN_PROGRESS". |                                                                     |
| counted_quantity                                                                            | Quantity of items found in the stock.                               |
| discrepancy_quantity                                                                        | The discrepancy between the quantity in stock and counted quantity. |
| The discrepancy is the quantity used when creating a stock adjustment.                      |                                                                     |
| created_at                                                                                  | The timestamp when the stocktake row was created.                   |
| updated_at                                                                                  | The timestamp when the stocktake row was last updated.              |
| deleted_at                                                                                  | The timestamp when the stocktake row was deleted.                   |
