# The recipe / BOM object

Attribute Description recipe_id (WAS DELETED IN Q1) Unique identifier for rows that make
up the recipe of a product. recipe_row_id (CHANGED TO UUID IN Q1) Unique identifier for
a recipe row. One recipe row can apply to multiple product variants of the same product.
product_id ID of the product this recipe row belongs to. product_variant_id ID of the
product variant this recipe row belongs to. ingredient_variant_id ID of the material or
product (i.e. subassemblies) variant used to make the product variant. quantity The
quantity used to manufacture one unit of the product. notes A string attached to the
object to add any internal comments. created_at The timestamp when the recipe row was
created. updated_at The timestamp when the recipe row was last updated.
