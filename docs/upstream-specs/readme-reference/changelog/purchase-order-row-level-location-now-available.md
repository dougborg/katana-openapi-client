> ## Documentation Index
> Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt
> Use this file to discover all available pages before exploring further.

# Purchase Order Row level location now available

# Purchase order rows now support per-row location\_id for multi-location receiving

Purchase order rows now expose a `location_id` field, letting you assign a destination location to individual rows rather than only to the purchase order as a whole.

Previously, every row on a purchase order inherited the order-level location and could only be received into that single location. Going forward, each row can specify its own `location_id` at create, update, and receive time, enabling a single purchase order to deliver stock into multiple locations.

This applies to endpoints that create, update, filter, or return purchase order rows, and to the receive endpoint:

* POST [https://api.katanamrp.com/v1/purchase\_order\_rows](https://api.katanamrp.com/v1/purchase_order_rows)
* PATCH [https://api.katanamrp.com/v1/purchase\_order\_rows/\{id}](https://api.katanamrp.com/v1/purchase_order_rows/\{id})
* GET [https://api.katanamrp.com/v1/purchase\_order\_rows](https://api.katanamrp.com/v1/purchase_order_rows)
* GET [https://api.katanamrp.com/v1/purchase\_order\_rows/\{id}](https://api.katanamrp.com/v1/purchase_order_rows/\{id})
* POST [https://api.katanamrp.com/v1/purchase\_order\_receive](https://api.katanamrp.com/v1/purchase_order_receive)

`GET /purchase_order_rows` also accepts `location_id` as a query filter to list rows for a specific location. On `PATCH /purchase_order_rows/{id}`, `location_id` is updatable only while `received_date` is `null`, in line with the other editable fields on a row.

<br />