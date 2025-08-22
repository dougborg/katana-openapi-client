# Filtering

Below are some of the filters currently allowed by default to all endpoints within the
provided collections (besides /inventory and /batch_stocks).

| Key                                                                                             | Description                              |
| ----------------------------------------------------------------------------------------------- | ---------------------------------------- |
| ids                                                                                             | An array of object IDs.                  |
| limit                                                                                           | SeePagination.                           |
| page                                                                                            | SeePagination.                           |
| created_at_min                                                                                  | Return results created after this date.  |
| Format example: 2021-04-14T10:39:40.054Z.                                                       |                                          |
| created_at_max                                                                                  | Return results created before this date. |
| Format example: 2021-04-14T10:39:40.054Z.                                                       |                                          |
| updated_at_min                                                                                  | Return results updated after this date.  |
| Format example: 2021-04-14T10:39:40.054Z.                                                       |                                          |
| updated_at_max                                                                                  | Return results updated before this date. |
| Format example: 2021-04-14T10:39:40.054Z.                                                       |                                          |
| include_deleted                                                                                 | Set to false by default.                 |
| If set to true, soft-deleted records are included in the resultset.                             |                                          |
| Some resources don't support access to deleted data.                                            |                                          |
| For more information, see the corresponding documentation for the endpoint.                     |                                          |
| extend                                                                                          | An array of linked objects.              |
| When specified, the linked object will be included in the response payload.                     |                                          |
| Date filters use ISO 8601 format and come in pairs that accept both \_min and \_max parameters. |                                          |

## Example

## 🚧

If an invalid parameter is added to the filter, it won't be applied to the results.
Always double-check and make sure you've used the syntax correctly! If no results match
a filter, an empty array will be returned.
