# Receive a purchase order

Receive a purchase order post https://api.katanamrp.com/v1 /purchase_order_receive If
you receive the items on the purchase order, you can mark the purchase order as
received. This will update the existing purchase order rows quantities to the quantities
left unreceived and create a new rows with the received quantities and dates. If you
want to mark all rows as received and the order doesn’t contain batch tracked items, you
can use PATCH /purchase_orders/id endpoint. Reverting the receive must also be done
through that endpoint.
