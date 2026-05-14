# The sales return row object

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
        Unique identifier for the sales return row
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        sales\_return\_id
      </td>

      <td style={{ textAlign: "left" }}>
        Reference to the parent sales return
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        variant\_id
      </td>

      <td style={{ textAlign: "left" }}>
        Product variant being returned
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        fulfillment\_row\_id
      </td>

      <td style={{ textAlign: "left" }}>
        Reference to the original fulfillment row\
        from GET /sales\_orders/id/returnable\_items
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        sales\_order\_row\_id
      </td>

      <td style={{ textAlign: "left" }}>
        Reference to the original sales order row
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        quantity
      </td>

      <td style={{ textAlign: "left" }}>
        Number of items being returned
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        net\_price\_per\_unit
      </td>

      <td style={{ textAlign: "left" }}>
        Original amount paid per unit by the customer after discounts
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        reason\_id
      </td>

      <td style={{ textAlign: "left" }}>
        Reference to the return reason
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        restock\_location\_id
      </td>

      <td style={{ textAlign: "left" }}>
        Location where items will be restocked
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        batch\_transactions
      </td>

      <td style={{ textAlign: "left" }}>
        Associated batch transactions for this return
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        created\_at
      </td>

      <td style={{ textAlign: "left" }}>
        The timestamp when row was created.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        updated\_at
      </td>

      <td style={{ textAlign: "left" }}>
        The timestamp when row was last updated.
      </td>
    </tr>
  </tbody>
</Table>

## The batch transaction object

| Attribute | Description                                        |
| :-------- | :------------------------------------------------- |
| batch\_id | Unique identifier for the sales return             |
| quantity  | The timestamp when return record was last updated. |

## Unassigned batch transactions object

| Attribute               | Description                                                  |
| :---------------------- | :----------------------------------------------------------- |
| batch\_id               | Unique identifier for the sales return                       |
| quantity                | Return order reference number                                |
| batch\_number           | ID of the location where items are being returned to         |
| batch\_created\_date    | Current status of the return process                         |
| batch\_expiration\_date | Currency used for the return transaction                     |
| barcode                 | Date when the return was processed(moved to RETURNED status) |