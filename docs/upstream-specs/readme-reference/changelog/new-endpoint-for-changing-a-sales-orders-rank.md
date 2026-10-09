---
agentTools:
  projectIndex: https://developer.katanamrp.com/llms.txt
---

# New endpoint for changing a sales order's rank

Added the sales order rerank (<https://developer.katanamrp.com/reference/reranksalesorder>) endpoint. This endpoint repositions an open sales order in the schedule relative to another sales order, mirroring the drag-and-drop reordering available in the Katana app. Any manufacturing orders linked to the sales order are moved together with it.

**Example payload:**

```json
{
  "order_ids": [1],
  "place": {
    "before_id": 4
  }
}
```

<br />