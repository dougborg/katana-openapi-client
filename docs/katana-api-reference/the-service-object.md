# The service object

Attribute Description id Unique identifier for the object. name The service’s unique
name. uom The unit used to measure the quantity of the service (e.g. pcs, hours).
category_name A string used to group similar items for better organization and analysis.
is_sellable Sellable products can be added to Quotes and Sales orders. type Indicating
the item type. Service objects are of type "service". additional_info A string attached
to the object to add any internal comments, links to external files, additional
instructions, etc. variants An array of service variant objects. created_at The
timestamp when the service was created. updated_at The timestamp when the service was
last updated. deleted_at The timestamp when the service was deleted. archived_at The
timestamp when the service was archived. The service variant object Attribute
Description id Unique identifier for the object. sku A unique service code. sales_price
Default sales price (excluding tax), which is automatically assigned to the service when
creating sales orders. Can be manually changed on the order. default_cost Default cost
which is used to calculate profit.
