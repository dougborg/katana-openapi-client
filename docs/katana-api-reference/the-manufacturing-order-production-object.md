# The manufacturing order production object

Attribute Description id Unique identifier for the object. manufacturing_order_id The ID
of the manufacturing order the manufacturing order production belongs to. quantity The
quantity produced. production_date The timestamp of the production for the manufacturing
order. ISO 8601 format with time and timezone must be used. created_at The timestamp
when the manufacturing order production was created. updated_at The timestamp when the
manufacturing order production was last updated. deleted_at The timestamp when the
manufacturing order production was deleted. The ingredients object id Unique identifier
for the object. location_id The ID of the location of the ingredient. variant_id The ID
of product or material variant required for producing the manufacturing order
production. manufacturing_order_id The manufacturing order the manufacturing order
production belongs to. manufacturing_order_recipe_row_id The recipe row ID the
manufacturing order production ingredient belongs to. production_id The ID of the
manufacturing order production the ingredient belongs to. quantity The quantity of the
ingredients. production_date The timestamp of the manufacturing order production. cost
The cost of the ingredients. created_at The timestamp when the ingredient was created.
updated_at The timestamp when the ingredient was last updated. deleted_at The timestamp
when the ingredient was deleted. The operations object id Unique identifier for the
object. location_id The ID of the location of the manufacturing operation.
manufacturing_order_id The ID of the manufacturing order the operation belongs to.
manufacturing_order_operation_id The ID of the manufacturing order operation the
production operation belongs to. production_id The ID of the manufacturing order
production object the operation belongs to. time The time for completing the
manufacturing order operation, measured in seconds. production_date The timestamp when
the production operation was completed. cost The cost of this operation step. created_at
The timestamp when the operation was created. updated_at The timestamp when the
operation was last updated deleted_at The timestamp when the operation was deleted.
