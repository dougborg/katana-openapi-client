# The tax rate object

| Attribute                      | Description                                                                                                 |
| ------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| id                             | Unique identifier for the object.                                                                           |
| name                           | Tax name will be displayed together with a tax rate on sales and purchase orders for easier identification. |
| rate                           | This represents the tax rate percent out of 100.                                                            |
| is_default_sales               | If true, it will be used as default tax for sales orders.                                                   |
| There can be only one default. |                                                                                                             |
| is_default_purchases           | If true, it will be used as default tax for purchase orders.                                                |
| There can be only one default. |                                                                                                             |
| display_name                   | Combination of tax rate and name used for easier identification.                                            |
| created_at                     | The timestamp when the tax rate was created.                                                                |
| updated_at                     | The timestamp when the tax rate was last updated.                                                           |
