# The outsourced purchase order recipe row object

Attribute Description id Unique identifier for the object. purchase_order_id The ID of
the outsourced purchase order the recipe row belongs to. purchase_order_row_id The ID of
the outsourced purchase order row the recipe row belongs to. ingredient_variant_id The
ID of product or material variant required for receiving the outsourced purchase order.
planned_quantity_per_unit The planned quantity to outsource one unit of the product.
ingredient_availability The stock status of the required product or material. Possible
values. are “PROCESSED”, “IN_STOCK”, “EXPECTED“, “NOT_AVAILABLE”, “NOT_APPLICABLE”.
ingredient_expected_date The latest expected arrival date that relates to the required
ingredient. notes A string attached to the object to add any internal comments.
batch_transactions An array of batch transactions and their quantities. You can use the
stock for the same item from multiple batches. batch_transactions.batch_id The ID of the
batch for the required ingredient. batch_transactions.quantity The quantity consumed
from a particular batch. cost The cost of ingredients to outsource the product. For open
OPOs, the cost calculation is shown based on current MAC or default purchase price, but
is recalculated at OPO receiving to use receiving date MAC value. created_at The
timestamp when the outsourced purchase order recipe row was created. updated_at The
timestamp when the outsourced purchase order recipe row was updated. deleted_at The
timestamp when the outsourced purchase order recipe row was deleted.
