# The sales order object

<Table align={["left","left"]}>
  <thead>
    <tr>
      <th style={{ textAlign: "left" }}>
        Attribute
      </th>

      <th style={{ textAlign: "left" }}>
        Description
      </th>
    </tr>
  </thead>

  <tbody>
    <tr>
      <td style={{ textAlign: "left" }}>
        id
      </td>

      <td style={{ textAlign: "left" }}>
        Unique identifier for the object.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        customer\_id
      </td>

      <td style={{ textAlign: "left" }}>
        ID of the customer who this order belongs to.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        order\_no
      </td>

      <td style={{ textAlign: "left" }}>
        A unique, identifying string used in the UI and controlled by the user.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        source
      </td>

      <td style={{ textAlign: "left" }}>
        Indication of whether the sales order was created manually, by API or imported from somewhere else.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        order\_created\_date
      </td>

      <td style={{ textAlign: "left" }}>
        The timestamp of creating the document. ISO 8601 format with time and timezone must be used.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        delivery\_date
      </td>

      <td style={{ textAlign: "left" }}>
        A timestamp when the items are required to be delivered to the customer. ISO 8601 format with time and timezone must be used.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        picked\_date
      </td>

      <td style={{ textAlign: "left" }}>
        The timestamp when the Sales Order Delivery status was initially marked as "PACKED" or "DELIVERED". ISO 8601 format with time and timezone must be used. If multiple fulfillments exist for a sales order, the latest picked\_date is used.\
        When using the Sales Order update endpoint (e.g. PATCH /sales-orders/\{id}), the picked\_date is applied to all connected fulfillments under that order. If you need to update only specific fulfillments, we recommend using the Sales order fulfillment endpoint to modify them individually.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        location\_id
      </td>

      <td style={{ textAlign: "left" }}>
        ID of the location from which the order is shipped by default.

        If the order is fulfilled from multiple locations, then use the Sales Order Row object to specify from which location each order row is shipped..
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        status
      </td>

      <td style={{ textAlign: "left" }}>
        Status of the order. Possible values are “NOT\_SHIPPED”, "PARTIALLY\_PACKED", "PARTIALLY\_DELIVERED", “PACKED” and “DELIVERED”.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        currency
      </td>

      <td style={{ textAlign: "left" }}>
        Currency of the sales order. Filled with customer currency by default.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        conversion\_rate
      </td>

      <td style={{ textAlign: "left" }}>
        Currency rate used to convert from sales order currency into factory base currency.  If multiple fulfillments exist for a sales order row, the latest date and corresponding rate are used.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        conversion\_date
      </td>

      <td style={{ textAlign: "left" }}>
        The date of the conversion rate used. If multiple fulfillments exist for a sales order row, the latest date is used.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        invoicing\_status
      </td>

      <td style={{ textAlign: "left" }}>
        Indicating the status of generating the invoice through accounting integration to either Xero or QuickBooks Online.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        total
      </td>

      <td style={{ textAlign: "left" }}>
        The total value of the order (including taxes) in sales order currency.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        total\_in\_base\_currency
      </td>

      <td style={{ textAlign: "left" }}>
        The total value of the order (including taxes) in base currency.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        additional\_info
      </td>

      <td style={{ textAlign: "left" }}>
        A string attached to the object to add any internal comments, links to external files, additional instructions, etc.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        customer\_ref
      </td>

      <td style={{ textAlign: "left" }}>
        An identifier to reference the customer associated with the sales order
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        sales\_order\_rows
      </td>

      <td style={{ textAlign: "left" }}>
        An array of sales order rows.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        ecommerce\_order\_type
      </td>

      <td style={{ textAlign: "left" }}>
        Name of the ecommerce platform in case the order is imported from one.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        ecommerce\_store\_name
      </td>

      <td style={{ textAlign: "left" }}>
        Name of the ecommerce store in case the order is imported from an ecommerce platform.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        ecommerce\_order\_id
      </td>

      <td style={{ textAlign: "left" }}>
        ID of the order in the source system in case it is imported from an ecommerce platform.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        product\_availability
      </td>

      <td style={{ textAlign: "left" }}>
        Stock status for the products required by the sales order. Possible values are "IN\_STOCK", "EXPECTED", "PICKED", "NOT\_AVAILABLE", "NOT\_APPLICABLE".
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        product\_expected\_date
      </td>

      <td style={{ textAlign: "left" }}>
        The latest date of a manufacturing order production deadline or a purchasing order expected arrival date that relates to the required products.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        ingredient\_availability
      </td>

      <td style={{ textAlign: "left" }}>
        Stock status for ingredients required to produce the products on the sales order. Possible values are "PROCESSED",  "IN\_STOCK", "NOT\_AVAILABLE",  "EXPECTED", "NO\_RECIPE", "NOT\_APPLICABLE".
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        ingredient\_expected\_date
      </td>

      <td style={{ textAlign: "left" }}>
        The latest date of a manufacturing order production deadline or a purchasing order expected arrival date that relates to the required ingredients to produce the products.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        production\_status
      </td>

      <td style={{ textAlign: "left" }}>
        Production status of the manufacturing order that is making products for the respective sales order. Possible values are "NOT\_STARTED", "NONE", "NOT\_APPLICABLE", "IN\_PROGRESS", "BLOCKED", "DONE".
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        created\_at
      </td>

      <td style={{ textAlign: "left" }}>
        The timestamp when the sales order was created.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        updated\_at
      </td>

      <td style={{ textAlign: "left" }}>
        The timestamp when the sales order was last updated.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        tracking\_number
      </td>

      <td style={{ textAlign: "left" }}>
        Deprecated - use tracking\_number from sales order fulfillment instead
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        tracking\_number\_url
      </td>

      <td style={{ textAlign: "left" }}>
        Deprecated - use tracking\_number\_url from sales order fulfillment instead
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        billing\_address\_id
      </td>

      <td style={{ textAlign: "left" }}>
        The ID of the billing address of the sales order.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        shipping\_address\_id
      </td>

      <td style={{ textAlign: "left" }}>
        The ID of the shipping address of the sales order.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        addresses
      </td>

      <td style={{ textAlign: "left" }}>
        An array of shipping and billing addresses.
      </td>
    </tr>
  </tbody>
</Table>

## The sales order row object

| Attribute                            | Description                                                                                                                                                                                 |
| :----------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| id                                   | Unique identifier for the object.                                                                                                                                                           |
| quantity                             | The quantity of items for the order line.                                                                                                                                                   |
| variant\_id                          | ID of product variant added to the order line.                                                                                                                                              |
| tax\_rate\_id                        | ID of tax added to price per unit.                                                                                                                                                          |
| location\_id                         | ID of the location from which the order row is shipped (leave empty, when sales order location should be used for all sales order rows)                                                     |
| product\_availability                | Stock status for the products required by the sales order row. Possible values are "IN\_STOCK", "EXPECTED", "PICKED", "NOT\_AVAILABLE", "NOT\_APPLICABLE"                                   |
| product\_expected\_date              | The latest date of a manufacturing order production deadline or a purchasing order expected arrival date that relates to the required products                                              |
| price\_per\_unit                     | The sales price of one unit (excluding taxes) in sales order currency.                                                                                                                      |
| price\_per\_unit\_in\_base\_currency | The sales price of one unit (excluding taxes) in base currency.                                                                                                                             |
| total                                | The total value of the sales order row (excluding taxes) in sales order currency.                                                                                                           |
| total\_in\_base\_currency            | The total value of the order (excluding taxes) in base currency.                                                                                                                            |
| cogs\_value                          | Total Cost of Goods Sold (COGS) for the delivered quantity in a sales order row. Calculated based on the average cost of the product at the time of delivery.                               |
| attributes                           | An array of sales order row attributes. Each attribute is a key-value pair. Used to add extra details to the sales order row.                                                               |
| attributes.key                       | Custom key for the sales order row attribute.                                                                                                                                               |
| attributes.value                     | Custom value for the key in sales order row attribute.                                                                                                                                      |
| batch\_transactions                  | An array of batch transactions and their quantities. You can fulfill the item on the order from multiple batches.                                                                           |
| batch\_transaction.batch\_id         | ID of the batch for the fulfilled item.                                                                                                                                                     |
| batch\_transactions.quantity         | The quantity fulfilled from a particular batch.                                                                                                                                             |
| serial\_numbers                      | An array of serial number IDs                                                                                                                                                               |
| linked\_manufacturing\_order\_id     | The ID of the manufacturing order if there is a make-to-order (MTO) manufacturing order related to the sales order row.                                                                     |
| conversion\_rate                     | Currency rate used to convert from sales order currency into factory base currency.  If multiple fulfillments exist for a sales order row, the latest date and corresponding rate are used. |
| conversion\_date                     | The date of the conversion rate used. If multiple fulfillments exist for a sales order row, the latest date is used.                                                                        |
| created\_at                          | The timestamp when the sales order row was created.                                                                                                                                         |
| updated\_at                          | The timestamp when the sales order row was last updated.                                                                                                                                    |

## The sales order address object

| Attribute        | Description                                                           |
| :--------------- | :-------------------------------------------------------------------- |
| id               | Unique identifier for the sales order address object.                 |
| sales\_order\_id | The ID of the sales order related to the address.                     |
| entity\_type     | Either "billing" or "shipping" depending on the address type.         |
| first\_name      | The first name of the person related to the address.                  |
| last\_name       | The last name of the person related to the address.                   |
| company          | The company name related to the address.                              |
| phone            | The phone number related to the address.                              |
| line\_1          | The first line of the address (street name and house number).         |
| line\_2          | The second line of the address (apartment, suite, unit, or building). |
| city             | The city of the address.                                              |
| state            | The state of the address.                                             |
| zip              | The zip code of the address.                                          |
| country          | The country of the address.                                           |
| created\_at      | The timestamp when the address was created.                           |
| updated\_at      | The timestamp when the address was updated.                           |

## The sales order returnable item object

| Attribute                        | Description                                             |
| :------------------------------- | :------------------------------------------------------ |
| variant\_id                      | Unique identifier of the delivered item variant         |
| fulfillment\_row\_id             | ID of the fulfillment row this item belongs to          |
| available\_for\_return\_quantity | Number of items that can be returned                    |
| net\_price\_per\_unit            | Price per unit after discounts                          |
| location\_id                     | Unique identifier of the location item was shipped from |
| quantity\_sold                   | Original quantity sold                                  |