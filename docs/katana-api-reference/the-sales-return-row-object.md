# The sales return row object

Attribute Description id Unique identifier for the sales return row sales_return_id
Reference to the parent sales return variant_id Product variant being returned
fulfillment_row_id Reference to the original fulfillment row sales_order_row_id
Reference to the original sales order row quantity Number of items being returned
net_price_per_unit Original amount paid per unit by the customer after discounts
reason_id Reference to the return reason restock_location_id Location where items will
be restocked batch_transactions Associated batch transactions for this return created_at
The timestamp when row was created. updated_at The timestamp when row was last updated.
The batch transaction object Attribute Description batch_id Unique identifier for the
sales return quantity The timestamp when return record was last updated. Unassigned
batch transactions object Attribute Description batch_id Unique identifier for the sales
return quantity Return order reference number batch_number ID of the location where
items are being returned to batch_created_date Current status of the return process
batch_expiration_date Currency used for the return transaction barcode Date when the
return was processed(moved to RETURNED status)
