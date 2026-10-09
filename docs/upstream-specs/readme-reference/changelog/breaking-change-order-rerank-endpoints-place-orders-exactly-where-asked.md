---
agentTools:
  projectIndex: https://developer.katanamrp.com/llms.txt
---

# Breaking change: order rerank endpoints place orders exactly where asked.

From **October 7, 2026**, `POST /sales_order_rerank` and `POST /manufacturing_order_rerank` place orders exactly where asked. These endpoints used to follow the app's drag-and-drop logic, where the result depends on which way the order moves, so the same request could land an order in different places and a retry could move it again. They now place orders by position: `before_id` always means directly above, `after_id` directly below, and sending the same request again changes nothing.

Paths, authentication and request bodies stay the same, but three things change for existing integrations:

| Change                                          | Until October 7, 2026      | From October 7, 2026                                |
| ----------------------------------------------- | -------------------------- | --------------------------------------------------- |
| `place.before_id` when the order moves **down** | Lands **below** the target | Lands directly **above** the target, like moving up |
| Success response                                | `204 No Content`           | `200 OK` with `{"order_ids": [...]}`                |
| Unknown order id                                | `404`                      | `422`, same as an order that is not open            |

If you relied on the drag-and-drop result when moving an order down, send `place.after_id` instead.

The endpoints also accept `place.position` (`top` / `bottom`), `place.after_id` and up to 250 orders per request; see <Anchor target="_blank" href="https://developer.katanamrp.com/reference/reranksalesorder">Change a sales order's rank</Anchor> and <Anchor target="_blank" href="https://developer.katanamrp.com/reference/rerankmanufacturingorder">Change a manufacturing order's rank</Anchor>.