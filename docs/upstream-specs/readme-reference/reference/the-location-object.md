# The location object

| Attribute              | Description                                                                                                                                              |
| :--------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------- |
| id                     | Unique identifier for the object.                                                                                                                        |
| name                   | Name of the location.                                                                                                                                    |
| legal\_name            | This name is added to the "Ship to" information when a purchase order for this location is printed or saved as PDF.                                      |
| address\_id            | ID of the location’s address.                                                                                                                            |
| address                | Address of the location.                                                                                                                                 |
| is\_primary            | Indicates if the location is your primary location.                                                                                                      |
| sales\_allowed         | If true, Katana enables you to select the location for sales orders and manage location-specific list for those orders.                                  |
| manufacturing\_allowed | If true, Katana enables you to select the location for manufacturing orders and manage location-specific list for those orders for manufacturing orders. |
| purchase\_allowed      | If true, Katana enables you to select the location for purchase orders and manage location-specific list for those orders.                               |
| created\_at            | The timestamp when the location was created.                                                                                                             |
| updated\_at            | The timestamp when the location was last updated.                                                                                                        |
| deleted\_at            | The timestamp when the location was deleted                                                                                                              |

## The location address object

| Attribute | Description                                                           |
| :-------- | :-------------------------------------------------------------------- |
| id        | Unique identifier for the location address object.                    |
| line\_1   | The first line of the address (street name and house number).         |
| line\_2   | The second line of the address (apartment, suite, unit, or building). |
| city      | The city of the address.                                              |
| state     | The state of the address.                                             |
| zip       | The zip code of the address.                                          |
| country   | The country of the address.                                           |