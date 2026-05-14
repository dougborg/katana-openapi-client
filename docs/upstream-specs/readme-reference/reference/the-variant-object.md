# The variant object

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
        product\_id
      </td>

      <td style={{ textAlign: "left" }}>
        ID of the product this variant belongs to.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        material\_id
      </td>

      <td style={{ textAlign: "left" }}>
        ID of the material this variant belongs to.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        sku
      </td>

      <td style={{ textAlign: "left" }}>
        A unique code for a product variant (also called SKU).
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        sales\_price
      </td>

      <td style={{ textAlign: "left" }}>
        Default sales price (excluding tax), which is automatically assigned to the product or it's variant when creating sales orders. Can be manually changed on each order.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        purchase\_price
      </td>

      <td style={{ textAlign: "left" }}>
        Default purchase price (excluding tax) in the default currency of the supplier, which is automatically assigned to the material or its variant when creating purchase orders. Can be manually changed on each order.

        If you are purchasing in a different unit of measure than your stock unit of measure, then this is the price per purchase UoM.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        internal\_barcode
      </td>

      <td style={{ textAlign: "left" }}>
        Barcode for identifying the SKU internally.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        registered\_barcode
      </td>

      <td style={{ textAlign: "left" }}>
        Barcode printed on the physical labels of items you sell to your customers.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        supplier\_item\_codes
      </td>

      <td style={{ textAlign: "left" }}>
        Supplier provided SKU, used to identify raw materials and purchasable products from different suppliers when receiving.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        config\_attributes
      </td>

      <td style={{ textAlign: "left" }}>
        An array of variant configuration attribute objects (name and value). A variant can have configuration values to all options specified in the product object.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        config\_attributes.config\_name
      </td>

      <td style={{ textAlign: "left" }}>
        Name of the variant option (e.g. color, size). Needs to match with the variant option from product.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        config\_attributes.config\_value
      </td>

      <td style={{ textAlign: "left" }}>
        Value of the variant option (e.g. blue). Needs to match with one of the variant option values from product.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        type
      </td>

      <td style={{ textAlign: "left" }}>
        Either "product" or "material", depending on the object the variant belongs to.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        created\_at
      </td>

      <td style={{ textAlign: "left" }}>
        The timestamp when the variant was created.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        updated\_at
      </td>

      <td style={{ textAlign: "left" }}>
        The timestamp when the variant was last updated.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        minimum\_order\_quantity
      </td>

      <td style={{ textAlign: "left" }}>
        The minimum order quantity is used as a default purchase order row quantity. It can be manually changed on each order.\
        If you purchase in a different unit of measure than your stock unit of measure, then this is the quantity per purchase UoM.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        lead\_time
      </td>

      <td style={{ textAlign: "left" }}>
        Time in days used to calculate arrival date and suggested order dates of that variant
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        abc\_classification
      </td>

      <td style={{ textAlign: "left" }}>
        ABC inventory classification of the variant. Categorizes items by relative value and consumption importance. Possible values: A, B, C or null if not classified.
      </td>
    </tr>
  </tbody>
</Table>

<br />