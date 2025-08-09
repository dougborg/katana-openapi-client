# Creating Katana webhooks

Creating Katana webhooks Suggest Edits Webhooks offer an easy way to receive
programmatic notifications from Katana regarding changes to your data as they occur.
Learn more about how Katana webhooks work and what events our [API reference] supports (
https://developer.katanamrp.com/reference/webhooks ) or if you're entirely new to
webhooks, take a look at this guide . Create a webhook URL We recommend setting up a
test webhook URL to use while following this guide. You can use several free hosted
services to create a temporary endpoint URL, such as https://webhook.site . Set up a
Katana webhook Webhook registration request example cURL curl --request POST \
--url https://api.katanamrp.com/v1/webhooks \
--header 'Accept: application/json' \
--header 'Authorization: Bearer <Your api key>' \
--header 'Content-Type: application/json' --data '{"url":"https://katanamrp.com",
"subscribed_events":[ "sales_order.updated"]}' Response example HTTP HTTP/1.1 200 OK
Content-Type: application/json

{ "id":1 "url":"https://katanamrp.com" "token":"73f82127d57a2cea" "enabled":true
"subscribed_events":["sales_order.created"] "created_at":"2021-01-28T04:58:40.492Z"
"updated_at":"2021-01-28T04:58:40.493Z" } Testing events See how requests are sent to
your test URL by triggering an event. In this example, we subscribe to sales order
updates. Update a sales order by either: Changing a sales order directly within the
Katana UI. Try writing a comment to "Additional info" -or- Sending a request via API :
Sales order update request example cURL curl --request PATCH
'https://api-staging.katanamrp.com/v1/sales_orders/<your sales order ID>' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <Your api key>' \
--data-raw '{ "additional_info":"testing" }' Updated over 3 years ago What’s Next
Webhook best practices Verifying webhook signature Webhook API endpoint Table of
Contents Create a webhook URL Set up a Katana webhook Testing events
