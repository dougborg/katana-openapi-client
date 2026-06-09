> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# The BOM row object

| Attribute               | Description                                                                                  |
| :---------------------- | :------------------------------------------------------------------------------------------- |
| id                      | Unique identifier for the object.                                                            |
| product\_variant\_id    | ID of the product variant this recipe row belongs to.                                        |
| product\_item\_id       | ID of the product this recipe row belongs to.                                                |
| ingredient\_variant\_id | ID of the material or product (i.e. subassemblies) variant used to make the product variant. |
| quantity                | The quantity used to manufacture one unit of the product.                                    |
| notes                   | A string attached to the object to add any internal comments.                                |
| created\_at             | The timestamp when the row was created.                                                      |
| updated\_at             | The timestamp when the row was last updated.                                                 |