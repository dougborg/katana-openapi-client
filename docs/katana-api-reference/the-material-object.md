# The material object

Attribute Description id Unique identifier for the object. name The material’s unique
name. uom The unit used to measure the quantity of the material (e.g. pcs, kg, m). This
unit is also used for the item on orders and product recipes. category_name A string
used to group similar items for better organization and analysis. is_sellable Sellable
products can be added to Quotes and Sales orders. default_supplier_id The supplier added
to a purchase order automatically when the related material is added to the order. type
Indicating the item type. Material objects are of type "material". additional_info A
string attached to the object to add any internal comments, links to external files,
additional instructions, etc. purchase_uom If you are purchasing in a different unit of
measure than the default unit of measure (used for tracking stock) for this item, you
can define the purchase unit. Value null indicates that purchasing is done in same unit
of measure. If value is not null , purchase_uom_conversion_rate must also be populated.
purchase_uom_conversion_rate The conversion rate between the purchase and material UoMs.
If used, material must have a purchase_uom that is different from uom. batch_tracked
Batch tracking enables you to assign batch numbers and expiration dates to manufactured
items. variants An array of material variant objects. created_at The timestamp when the
material was created. updated_at The timestamp when the material was last updated.
archived_at The timestamp when the material was archived. configs An array of material
variant configurations. The material config object Attribute Description id Unique
identifier for the object. name Name of the variant option (e.g. color, size). values An
array of values for a variant option. (e.g. blue, green, red).
