# The sales order row object

Attribute Description id Unique identifier for the object. sales_order_id The ID of the
sales order the row belongs to. quantity The quantity of items for the order line.
variant_id ID of product variant added to the order line. tax_rate_id ID of tax added to
price per unit. location_id ID of the location from which the order row is shipped
(leave empty, when sales order location should be used for this sales order row)
product_availability Stock status for the products required by the sales order row.
Possible values are "IN_STOCK", "EXPECTED", "PICKED", "NOT_AVAILABLE", "NOT_APPLICABLE"
product_expected_date The latest date of a manufacturing order production deadline or a
purchasing order expected arrival date that relates to the required products
price_per_unit Sales price of one unit (excluding taxes).
price_per_unit_in_base_currency The sales price of one unit (excluding taxes) in base
currency. total_discount The total discount amount applied to the entire sales order row
(excluding taxes) total The total value of the sales order row (excluding taxes) in
sales order currency. total_in_base_currency The total value of the order row (excluding
taxes) in base currency. cogs_value Total Cost of Goods Sold (COGS) for the delivered
quantity. Calculated based on the average cost of the product at the time of delivery
attributes An array of sales order row attributes. Each attribute is a key-value pair.
Used to add extra details to the sales order row. attributes.key Custom key for the
sales order row attribute. attributes.value Custom value for the key in sales order row
attribute. batch_transactions An array of batch transactions and their quantities. You
can fulfill the item on the order from multiple batches. batch_transaction.batch_id ID
of the batch for the fulfilled item. batch_transactions.quantity The quantity fulfilled
from a particular batch. serial_numbers An array of serial number IDs
serial_number_transactions An array of serial number transactions and their quantities.
You can add multiple serial numbers to an item.
serial_number_transactions.serial_number_id ID of the serial number for the fulfilled
item. serial_number_transactions.quantity The quantity of given serial number, can
either be added (1) or removed (0) linked_manufacturing_order_id The ID of the
manufacturing order if there is a make-to-order (MTO) manufacturing order related to the
sales order row. conversion_rate Currency rate used to convert from sales order currency
into factory base currency. If multiple fulfillments exist for a sales order row, the
latest date and corresponding rate are used. conversion_date The date of the conversion
rate used. If multiple fulfillments exist for a sales order row, the latest date is
used. created_at The timestamp when the sales order row was created. updated_at The
timestamp when the sales order row was last updated.
