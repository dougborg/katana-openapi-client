> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# The product operation object

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
        product\_operation\_row\_id
      </td>

      <td style={{ textAlign: "left" }}>
        Unique identifier for an operation row. One operation row can apply to multiple product variants of the same product.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        product\_id
      </td>

      <td style={{ textAlign: "left" }}>
        The ID of the product this operation row belongs to.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        product\_variant\_id
      </td>

      <td style={{ textAlign: "left" }}>
        The ID of the product variant this operation row belongs to.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        operation\_id
      </td>

      <td style={{ textAlign: "left" }}>
        The ID of the operation needed to perform to make the product.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        operation\_name
      </td>

      <td style={{ textAlign: "left" }}>
        The name of the operation needed to perform to make the product.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        resource\_id
      </td>

      <td style={{ textAlign: "left" }}>
        The ID of the workstation or a person required for completing a certain operation.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        resource\_name
      </td>

      <td style={{ textAlign: "left" }}>
        The name of the workstation or a person required for completing a certain operation.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        type
      </td>

      <td style={{ textAlign: "left" }}>
        Different operation types allows you to use different cost calculations depending on the type of product operation

        * \*process\*\*: The process operation type is best for when products are individually built and time is the main driver of cost.
        * \*setup\*\*: The setup operation type is best for setting up a machine for production where the production quantity doesn't affect cost.
        * \*perUnit\*\*: The per unit operation type is best when cost of time isn't a factor, but only the quantity of product made.
        * \*fixed\*\*: The fixed cost operation type is useful for adding the expected extra costs that go into producing a product.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        cost\_per\_hour (deprecated)
      </td>

      <td style={{ textAlign: "left" }}>
        (This field is deprecated in favor of cost\_parameter) The expected cost of an operation, either total or per hour/unit of product (based on type). Total cost of the operation on a manufacturing order is calculated as follows:

        * \*process\*\*: cost = cost\_parameter x planned\_time\_parameter (in hours) x product quantity
        * \*setup\*\*: cost = cost\_parameter x planned\_time\_parameter (in hours)
        * \*perUnit\*\*: cost = cost\_parameter x product quantity
        * \*fixed\*\*: cost = cost\_parameter
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        cost\_parameter
      </td>

      <td style={{ textAlign: "left" }}>
        The expected cost of an operation, either total or per hour/unit of product (based on type). Total cost of the operation on a manufacturing order is calculated as follows:

        * \*process\*\*: cost = cost\_parameter x planned\_time\_parameter (in hours) x product quantity
        * \*setup\*\*: cost = cost\_parameter x planned\_time\_parameter (in hours)
        * \*perUnit\*\*: cost = cost\_parameter x product quantity
        * \*fixed\*\*: cost = cost\_parameter
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        planned\_time\_per\_unit (deprecated)
      </td>

      <td style={{ textAlign: "left" }}>
        (This field is deprecated in favor of planned\_time\_parameter) The planned duration of an operation, in seconds, to either manufacture one unit of a product or complete a manufacturing order (based on type).
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        planned\_time\_parameter
      </td>

      <td style={{ textAlign: "left" }}>
        The planned duration of an operation, in seconds, to either manufacture one unit of a product or complete a manufacturing order (based on type).
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        planned\_cost\_per\_unit
      </td>

      <td style={{ textAlign: "left" }}>
        The expected cost of an operation per unit of product, calculated by the system.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        rank
      </td>

      <td style={{ textAlign: "left" }}>
        A numerical value used for ranking the operations. We use an internal numeration system where values are not sequential. Operations with a higher value are ranked first.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        group\_boundary
      </td>

      <td style={{ textAlign: "left" }}>
        A numerical value that is used to group operations that are to be performed in parallel order.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        created\_at
      </td>

      <td style={{ textAlign: "left" }}>
        The timestamp when the manufacturing order recipe row was created.
      </td>
    </tr>

    <tr>
      <td style={{ textAlign: "left" }}>
        updated\_at
      </td>

      <td style={{ textAlign: "left" }}>
        The timestamp when the manufacturing order recipe row was last updated.
      </td>
    </tr>
  </tbody>
</Table>