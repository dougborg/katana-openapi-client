# Update a recipe row

Update a recipe row patch deprecated https://api.katanamrp.com/v1 /recipe_rows/ {id}
(This endpoint is deprecated in favor of BOM rows) Updates the specified recipe row by
setting the values of the parameters passed. Any parameters not provided will be left
unchanged. Since one recipe row can apply to multiple product variants, updating the row
will apply to all objects with the same recipe_row_id.
