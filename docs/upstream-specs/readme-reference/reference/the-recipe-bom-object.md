> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# The recipe / BOM object

| Attribute               | Description                                                                                                                            |
| :---------------------- | :------------------------------------------------------------------------------------------------------------------------------------- |
| recipe\_id              | (WAS DELETED IN Q1) Unique identifier for rows that make up the recipe of a product.                                                   |
| recipe\_row\_id         | (CHANGED TO UUID IN Q1) Unique identifier for a recipe row. One recipe row can apply to multiple product variants of the same product. |
| product\_id             | ID of the product this recipe row belongs to.                                                                                          |
| product\_variant\_id    | ID of the product variant this recipe row belongs to.                                                                                  |
| ingredient\_variant\_id | ID of the material or product (i.e. subassemblies) variant used to make the product variant.                                           |
| quantity                | The quantity used to manufacture one unit of the product.                                                                              |
| notes                   | A string attached to the object to add any internal comments.                                                                          |
| created\_at             | The timestamp when the recipe row was created.                                                                                         |
| updated\_at             | The timestamp when the recipe row was last updated.                                                                                    |