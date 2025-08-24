# The sales order address object

| Attribute      | Description                                                           |
| -------------- | --------------------------------------------------------------------- |
| id             | Unique identifier for the sales order address object.                 |
| sales_order_id | The ID of the sales order related to the address.                     |
| entity_type    | Either "billing" or "shipping" depending on the address type.         |
| first_name     | The first name of the person related to the address.                  |
| last_name      | The last name of the person related to the address.                   |
| company        | The company name related to the address.                              |
| phone          | The phone number related to the address.                              |
| line_1         | The first line of the address (street name and house number).         |
| line_2         | The second line of the address (apartment, suite, unit, or building). |
| city           | The city of the address.                                              |
| state          | The state of the address.                                             |
| zip            | The zip code of the address.                                          |
| country        | The country of the address.                                           |
| created_at     | The timestamp when the address was created.                           |
| updated_at     | The timestamp when the address was updated.                           |
