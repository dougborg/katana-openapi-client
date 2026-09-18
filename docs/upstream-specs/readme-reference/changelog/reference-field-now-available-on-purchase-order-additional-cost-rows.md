Fetch the complete documentation index at: https://developer.katanamrp.com/llms.txt. Use this file to discover all available pages before exploring further. Append .md to any documentation page URL to get its markdown version.

# `reference` field now available on Purchase Order additional cost rows

The reference field, previously available only in the Katana UI, is now exposed in the API for purchase order additional cost rows. You can use it to label what a cost row actually is — for example a customs invoice or freight surcharge — directly when creating the row, instead of editing it manually in the UI afterward.

Affected endpoints:

* POST /po\_additional\_cost\_rows — set reference on creation
* PATCH /po\_additional\_cost\_rows/{id} — update or clear it (pass null to clear)
* GET /po\_additional\_cost\_rows and GET /po\_additional\_cost\_rows/{id} — returned on every row

```curl
POST /po_additional_cost_rows 
{
  "additional_cost_id": 11,
  "group_id": 21,
  "tax_rate_id": 31,
  "price": 100,
  "reference": "Customs invoice #123"
}
```

The field is an optional string (max 255 characters, nullable). This change is fully backward compatible, existing integrations are unaffected, and rows created without a reference return null.