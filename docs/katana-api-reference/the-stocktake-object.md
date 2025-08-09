# The stocktake object

Attribute Description id Unique identifier for the object. stocktake_number A string
used to identify the stocktake. location_id The ID the stocktake location. status Status
of the order. Possible values are “NOT_STARTED”, “IN_PROGRESS”, "COUNTED", and
“COMPLETED”. reason A descriptive field for your own information to enable better
identification. additional_info A string attached to the object to add any internal
comments, links to external files, additional instructions, etc. stocktake_created_date
The timestamp of creating the stocktake document. ISO 8601 format with time and timezone
must be used. started_date The timestamp of starting the stocktake. ISO 8601 format with
time and timezone must be used. completed_date The timestamp of completing the
stocktake. ISO 8601 format with time and timezone must be used.
status_update_in_progress Indicates whether the status update is still in progress. You
cannot make additional updates to stocktake or its rows while the status update is in
progress. set_remaining_items_as_counted Indicates what happens with the stock of items
listed on the stocktake without quantity. If set to true, the stock levels for these
item variants will be adjusted to 0 after the stocktake is completed.
stock_adjustment_id The ID of the stock adjustment that was created as a result of the
stocktake. created_at The timestamp when the stocktake was created. updated_at The
timestamp when the stocktake was last updated. deleted_at The timestamp when the
stocktake was deleted.
