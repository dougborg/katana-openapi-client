Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

# New endpoint for changing a manufacturing order's rank

Added the manufacturing order rerank (<https://developer.katanamrp.com/reference/rerankmanufacturingorder>) endpoint. This endpoint repositions an open manufacturing order in the production schedule relative to another manufacturing order, mirroring the drag-and-drop reordering functionality in the Katana app. When a manufacturing order is linked to a sales order, all related manufacturing orders are repositioned together.

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