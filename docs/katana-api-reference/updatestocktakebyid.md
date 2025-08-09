# Update a stocktake

Update a stocktake patch https://api.katanamrp.com/v1 /stocktakes/ {id} Updates the
specified stocktake by setting the values of the parameters passed. Any parameters not
provided will be left unchanged. Status updates can take a long time so 204 is returned.
If you need to continue with updates on same entity or its rows, you need to poll if
status update has ended (status_update_in_progress) and continue after that.
