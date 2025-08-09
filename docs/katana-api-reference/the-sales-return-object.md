# The sales return object

Attribute Description id Unique identifier for the sales return customer_id ID of the
customer who initiated the return sales_order_id ID of the original sales order being
returned order_no Return order reference number return_location_id ID of the location
where items are being returned to status Current status of the return process currency
Currency used for the return transaction return_date Date when the return was
processed(moved to RETURNED status) order_created_date Date when the original order was
created additional_info Optional notes or comments about the return refund_status
Indicating the status of refund through accounting integration to QuickBooks Online
created_at The timestamp when return record was created. updated_at The timestamp when
return record was last updated. The return reason object Attribute Description id Unique
identifier for the return reason name Human readable description of the return reason
