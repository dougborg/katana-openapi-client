# The location object

| Attribute             | Description                                                                                                                                              |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| id                    | Unique identifier for the object.                                                                                                                        |
| name                  | Name of the location.                                                                                                                                    |
| legal_name            | This name is added to the "Ship to" information when a purchase order for this location is printed or saved as PDF.                                      |
| address_id            | ID of the location’s address.                                                                                                                            |
| address               | Address of the location.                                                                                                                                 |
| is_primary            | Indicates if the location is your primary location.                                                                                                      |
| sales_allowed         | If true, Katana enables you to select the location for sales orders and manage location-specific list for those orders.                                  |
| manufacturing_allowed | If true, Katana enables you to select the location for manufacturing orders and manage location-specific list for those orders for manufacturing orders. |
| purchase_allowed      | If true, Katana enables you to select the location for purchase orders and manage location-specific list for those orders.                               |
| created_at            | The timestamp when the location was created.                                                                                                             |
| updated_at            | The timestamp when the location was last updated.                                                                                                        |
| deleted_at            | The timestamp when the location was deleted                                                                                                              |

## The location address object

The location address object | id | Unique identifier for the location address object. |
| line_1 | The first line of the address (street name and house number). | | line_2 |
The second line of the address (apartment, suite, unit, or building). | | city | The
city of the address. | | state | The state of the address. | | zip | The zip code of the
address. | | country | The country of the address. |
