# The manufacturing order object

Attribute Description id Unique identifier for the object. status Status of the order.
Possible values are “NOT_STARTED”, “BLOCKED”, "IN_PROGRESS", and “DONE”. order_no A
unique, identifying string used in the UI and controlled by the user. variant_id The ID
of the product variant being produced. planned_quantity The quantity planned to produce
with the manufacturing order. actual_quantity The actual quantity of the product made
with the manufacturing order. batch_transactions An array of batch transactions and
their quantities. A manufacturing order will always contain one batch transaction since
it supports producing into a single batch. batch_transaction.batch_id ID of the batch
for the manufactured product. batch_transactions.quantity The quantity produced in a
particular batch. location_id The ID of the location to which items are produced.
order_created_date The timestamp of creating the document. ISO 8601 format with time and
timezone must be used. done_date The timestamp of completing the manufacturing order.
ISO 8601 format with time and timezone must be used. production_deadline_date The
timestamp of the production deadline for the manufacturing order. ISO 8601 format with
time and timezone must be used. additional_info A string attached to the object to add
any internal comments, links to external files, additional instructions, etc.
is_linked_to_sales_order If a manufacturing order was made to order, it can be linked to
a sales order. sales_order_id The ID of the sales order that is linked to the
manufacturing order. sales_order_row_id The ID of the sales order row that is linked to
the manufacturing order. sales_order_delivery_deadline Delivery deadline of the sales
order that is linked to the manufacturing order. ingredient_availability The stock
status of required materials or subassemblies listed in the manufacturing order recipe
rows. Possible values are "PROCESSED", "IN_STOCK", "NOT_AVAILABLE", "EXPECTED",
"NO_RECIPE", "NOT_APPLICABLE". total_cost The total cost of manufacturing the selected
quantity of the product. This includes the cost of the ingredients (materials and
subassemblies) from recipe rows and the cost of operations multiplied by the quantity.
For open MOs, the cost calculation is shown based on the planned quantities but is
recalculated at MO completion if the actual quantities are different from the planned.
total_planned_time The planned duration of manufacturing order operations measured in
seconds. total_actual_time The actual time for completing the manufacturing order
operations measured in seconds. material_cost The total cost of materials used to make
the product. Calculated once the manufacturing order is marked as DONE.
subassemblies_cost The total cost of subassemblies used to make the product. Calculated
once the manufacturing order is marked as DONE. operations_cost The total cost of
operations for making the product. Calculated once the manufacturing order is marked as
DONE. created_at The timestamp when the manufacturing order was created. updated_at The
timestamp when the manufacturing order was last updated. deleted_at The timestamp when
the manufacturing order was deleted.
