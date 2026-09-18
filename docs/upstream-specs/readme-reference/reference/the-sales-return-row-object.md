---
updatedAt: 2025-11-25T09:47:06.000Z
---

Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

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
        sales_return_id
      </td>

      <td style={{ textAlign: "left" }}>
        Reference to the parent sales return
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        variant_id
      </td>

      <td style={{ textAlign: "left" }}>
        Product variant being returned
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        fulfillment_row_id
      </td>

      <td style={{ textAlign: "left" }}>
        Reference to the original fulfillment row   
        from GET /sales_orders/id/returnable_items
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        sales_order_row_id
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
        net_price_per_unit
      </td>

      <td style={{ textAlign: "left" }}>
        Original amount paid per unit by the customer after discounts
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        reason_id
      </td>

      <td style={{ textAlign: "left" }}>
        Reference to the return reason
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        restock_location_id
      </td>

      <td style={{ textAlign: "left" }}>
        Location where items will be restocked
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        batch_transactions
      </td>

      <td style={{ textAlign: "left" }}>
        Associated batch transactions for this return
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        created_at
      </td>

      <td style={{ textAlign: "left" }}>
        The timestamp when row was created.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        updated_at
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