# Demand forecast object

## Demand forecast object

| Attribute    | Description                                    |
| :----------- | :--------------------------------------------- |
| variant\_id  | ID of variant                                  |
| location\_id | ID of location                                 |
| in\_stock    | Current stock level of the variant in location |
| periods      | Array of Period objects describing forecast    |

## Period object

| Attribute     | Description                                                                    |
| :------------ | :----------------------------------------------------------------------------- |
| period\_start | ISO 8601 date-time of period start (inclusive)                                 |
| period\_end   | ISO 8601 date-time of period end (inclusive)                                   |
| in\_stock     | Calculated stock level at the end of the period                                |
| expected      | Expected incoming stock (e.g. from Purchase Orders), based on orders in Katana |
| committed     | Forecasted demand for the period                                               |