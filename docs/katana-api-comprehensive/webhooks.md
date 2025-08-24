# Webhooks

Webhooks are great if you’re running an app that needs current, instantaneous
information from a third-party application. They’re simple to set up and very easy to
use.

## Graceful retries

Once a webhook notification is received, you should acknowledge success by providing an
HTTP 20X response within 10 seconds. If a response isn't delivered within this time, we
will attempt to resend the notification three more times according to the following
schedule: With each attempt, you'll also be given anX-Katana-Retry-NumHTTP header
indicating the attempt number (1, 2, or 3). Using temporary endpoint URLs, you can
quickly inspect webhook requests. You can create these URLs using a free hosted service
such ashttps://webhook.site.

## Events

You can configure the following events to trigger a message to registered webhooks:

| Event                                               | Description                                                                                                                                                   |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| sales_order.created                                 | Occurs when a new sales order is created.                                                                                                                     |
| sales_order.updated                                 | Occurs when a sales order is updated (any attribute).                                                                                                         |
| sales_order.deleted                                 | Occurs when a sales order is deleted.                                                                                                                         |
| sales_order.packed                                  | Occurs when a new sales status is marked as PACKED.                                                                                                           |
| sales_order.delivered                               | Occurs when a new sales status is marked as DELIVERED.                                                                                                        |
| sales_order.availability_updated                    | Occurs when availability or expected date is updated for products or ingredients.                                                                             |
| purchase_order.created                              | Occurs whenever a new purchase order is created.                                                                                                              |
| purchase_order.updated                              | Occurs whenever a purchase order is updated.                                                                                                                  |
| purchase_order.deleted                              | Occurs whenever a purchase order is deleted.                                                                                                                  |
| purchase_order.partially_received                   | Occurs whenever the purchase order status is marked as PARTIALLY_RECEIVED.                                                                                    |
| purchase_order.received                             | Occurs whenever the purchase order status is marked as RECEIVED.                                                                                              |
| purchase_order_row.created                          | Occurs whenever a new purchase order row is created.                                                                                                          |
| purchase_order_row.updated                          | Occurs whenever a new purchase order row is updated.                                                                                                          |
| purchase_order_row.deleted                          | Occurs whenever a purchase order row is deleted.                                                                                                              |
| purchase_order_row.received                         | Occurs whenever the purchase order row is marked received.                                                                                                    |
| manufacturing_order.created                         | Occurs whenever a new manufacturing order is created.                                                                                                         |
| manufacturing_order.updated                         | Occurs whenever a manufacturing order is updated (except updates of ingredient_availability, total_planned_time, total_actual_time, and cost-related fields). |
| manufacturing_order.deleted                         | Occurs whenever a manufacturing order is deleted.                                                                                                             |
| manufacturing_order.in_progress                     | Occurs whenever the manufacturing order status gets marked as IN_PROGRESS.                                                                                    |
| manufacturing_order.blocked                         | Occurs whenever the manufacturing order status gets marked as BLOCKED.                                                                                        |
| manufacturing_order.done                            | Occurs whenever the manufacturing order status gets marked as DONE.                                                                                           |
| manufacturing_order_operation_row.created           | Occurs whenever an operation row is added to a manufacturing order.                                                                                           |
| manufacturing_order_operation_row.updated           | Occurs whenever an operation row is updated in a manufacturing order.                                                                                         |
| manufacturing_order_operation_row.deleted           | Occurs whenever an operation row is deleted from a manufacturing order.                                                                                       |
| manufacturing_order_operation_row.in_progress       | Occurs whenever the operation status gets marked as IN_PROGRESS.                                                                                              |
| manufacturing_order_operation_row.paused            | Occurs whenever the operation status gets marked as PAUSED.                                                                                                   |
| manufacturing_order_operation_row.blocked           | Occurs whenever the operation status gets marked as BLOCKED.                                                                                                  |
| manufacturing_order_operation_row.completed         | Occurs whenever the operation status gets marked as COMPLETED.                                                                                                |
| manufacturing_order_recipe_row.created              | Occurs whenever a recipe row is added to a manufacturing order.                                                                                               |
| manufacturing_order_recipe_row.updated              | Occurs whenever a recipe row is updated in a manufacturing order.                                                                                             |
| manufacturing_order_recipe_row.deleted              | Occurs whenever a recipe row is deleted from a manufacturing order.                                                                                           |
| manufacturing_order_recipe_row.ingredients_in_stock | Occurs whenever the ingredient availability of a manufacturing order recipe row is updated to IN_STOCK.                                                       |
| current_inventory.product_updated                   | Occurs whenever a product's current stock level or average cost is updated.                                                                                   |
| current_inventory.material_updated                  | Occurs whenever a material's current stock level or average cost is updated.                                                                                  |
| current_inventory.product_out_of_stock              | Occurs whenever a product's current stock level is below the optimal level (quantity_missing_or_excess\<= 0).                                                 |
| current_inventory.material_out_of_stock             | Occurs whenever a material's current stock level is below the optimal level (quantity_missing_or_excess\<= 0).                                                |
| product.created                                     | Occurs whenever a new product is created.                                                                                                                     |
| product.updated                                     | Occurs whenever a product is updated.                                                                                                                         |
| product.deleted                                     | Occurs whenever a product is deleted.                                                                                                                         |
| material.created                                    | Occurs whenever a new material is created.                                                                                                                    |
| material.updated                                    | Occurs whenever a material is updated.                                                                                                                        |
| material.deleted                                    | Occurs whenever a material is deleted.                                                                                                                        |
| variant.created                                     | Occurs whenever a new variant is added to a product or material.                                                                                              |
| variant.updated                                     | Occurs whenever a variant is updated.                                                                                                                         |
| variant.deleted                                     | Occurs whenever a variant is deleted.                                                                                                                         |
| product_recipe_row.created                          | Occurs whenever a product recipe row is created.                                                                                                              |
| product_recipe_row.updated                          | Occurs whenever a product recipe row is updated.                                                                                                              |
| product_recipe_row.deleted                          | Occurs whenever a product recipe row is deleted.                                                                                                              |
| outsourced_purchase_order.created                   | Occurs whenever an outsourced purchase order is created.                                                                                                      |
| outsourced_purchase_order.updated                   | Occurs whenever an outsourced purchase order is updated.                                                                                                      |
| outsourced_purchase_order.deleted                   | Occurs whenever an outsourced purchase order is deleted.                                                                                                      |
| outsourced_purchase_order.received                  | Occurs whenever an outsourced purchase order is received.                                                                                                     |
| outsourced_purchase_order_row.created               | Occurs whenever an outsourced purchase order row is created.                                                                                                  |
| outsourced_purchase_order_row.updated               | Occurs whenever an outsourced purchase order row is updated.                                                                                                  |
| outsourced_purchase_order_row.deleted               | Occurs whenever an outsourced purchase order row is deleted.                                                                                                  |
| outsourced_purchase_order_row.received              | Occurs whenever an outsourced purchase order row is received.                                                                                                 |
| outsourced_purchase_order_recipe_row.created        | Occurs whenever an outsourced purchase order recipe row is created.                                                                                           |
| outsourced_purchase_order_recipe_row.updated        | Occurs whenever an outsourced purchase order recipe row is updated.                                                                                           |
| outsourced_purchase_order_recipe_row.deleted        | Occurs whenever an outsourced purchase order recipe row is deleted.                                                                                           |

## 🚧

Since some events solve specific use cases(i.e. sales_order.packed and
sales_order.delivered), if you're subscribed to bothsales order updatesandsales order
status change to delivered, you may receive two identical webhook payloads since sales
order status change to delivered is also considered an update.

## Event object

| Attribute | Description | | resource_type | stringIndicates the resource affected by
this event. | | webhook_id | numberIndicates registered webhook id that was used to send
the payload. | | action | stringThe event that triggered this webhook, e.g.
sales_order.delivered. | | object | objectThe object affected by this event. This will
contain anid,statusand anhrefto retrieve that resource. (hrefproperty doesn't apply
tosales_order.deletedorproduct_recipe_row.deletedevents) | Example event payload
HTTPHTTP/1.1 201 Created Content-Type: application/json { "resource_type":
"sales_order", "action": "sales_order.delivered", "webhook_id": "\<WEBHOOK_ID>",
"object": { "id": "\<SALES_ORDER_ID>", "status": "DELIVERED", "href":
"https://api.katanamrp.com/v1/sales_orders/\<SALES_ORDER_ID>" } HTTP/1.1 201 Created

## Verifying webhook signatures

Verifying webhook signatures To prevent attackers from imitating valid webhook events,
you should verify request signatures on your server. Each webhook you register will
return a single secret token in the token field of the API response body used to
generate an HMAC using SHA-256. You only need to register a webhook once. With each
webhook request, you'll be given anx-sha2-signatureHTTP header indicating the calculated
signature. Our Developer Hub provides a detailed guide for manually verifying webhook
signatures.
