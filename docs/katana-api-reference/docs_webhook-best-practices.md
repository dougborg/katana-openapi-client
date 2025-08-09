# Best practices for webhook use

Best practices for webhook use This section describes some common practices for dealing
with webhooks. Suggest Edits When should you use webhooks? The most common reason for
using webhooks is when actions need to be made based on specific events. With Katana,
this usually refers to events such as sales orders being placed, delivered, etc. If
you're not using webhooks, you'll need to poll for data while including time intervals.
How should I handle webhook requests? Webhooks have no official specification, so
they're managed and served based on the originating service. When receiving a request,
it's essential to be attentive regarding three key issues: Quickly respond to webhook
requests

- If an incoming webhook triggers lengthy processing in your system, we recommend you
  create a processing queue for events. If you don't implement a process, a timeout may
  result, and you will receive a webhook retry. Place importance on responsiveness over
  availability
- As the handler of incoming webhooks, we know that the most common constraint is
  availability since your setup should be ready to receive a webhook at all times, with
  minimal interruptions. Luckily, the response to a webhook doesn't need to include the
  processing results of that webhook. Your setup only needs to acknowledge the webhook
  request initially but can process it later. Fortunately, you can introduce queues
  between receiving a webhook and processing it. Deduplicate incoming events
- We can't guarantee that webhook messages will be delivered only once, so it's
  essential to include a mechanism that prevents duplicated events. Retry logic Katana
  ensures webhook delivery through detection failure and retries. If the original
  notification sending attempt fails due to receiving a non-2XX response code or
  exceeding a timeout of 10 seconds, we will retry three more times: after 30, 120, and
  900 seconds. If it fails for each attempt, it's counted as one non-successful
  delivery. What if my webhook handling service goes down? A key component of general
  quality software design is confirming data validation and handling failures
  gracefully. If for some reason, your service that handles Katana webhooks goes down an
  extended period, you'll need some way to catch up on missed notifications. The best to
  handle these situations is to build a harness that fetches data from the time you were
  down and feeds it into the webhook processing code one object at a time. The one
  hangup is that you'll need the processing code to be sufficiently decoupled from the
  request handlers that you can call it separately. Updated over 3 years ago What’s Next
  Verifying webhook signature Webhook API reference Table of Contents When should you
  use webhooks? How should I handle webhook requests? Retry logic What if my webhook
  handling service goes down?
