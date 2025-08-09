# The stock transfer object

Attribute Description id Unique identifier for the object. stock_transfer_number A
string used to identify the stock transfer. source_location_id ID the location from
which you are transferring the items. target_location_id ID the location to which you
are transferring the items. transfer_date The timestamp of transferring the items from
one location to another. ISO 8601 format with time and timezone must be used.
additional_info A string attached to the object to add any internal comments, links to
external files, additional instructions, etc. stock_transfer_rows An array of stock
transfer rows. created_at The timestamp when the stock transfer was created. updated_at
The timestamp when the stock transfer was last updated. The stock transfer row object
Attribute Description variant_id ID of product or material variant added to the stock
transfer row. quantity The quantity transferred from one location to another.
batch_transactions An array of batch transactions and their quantities. You can transfer
stock for the same item from multiple batches. batch_transaction.batch_id ID of the
batch for the transferred item. batch_transactions.quantity The quantity transferred
from a particular batch.
