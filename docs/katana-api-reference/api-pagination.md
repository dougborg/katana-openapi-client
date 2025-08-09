# Pagination

All queries that retrieve a list of records are paginated. The parameters for
controlling pagination are limit and page . The limit parameter By default, we limit
results to 50 per page. If you need to increase or decrease this amount, use the limit
parameter as shown in the example below. Example of using the limit parameter cURL

# This will set the number of entities by page to 20 instead of 50.

curl --request GET \
--url https://api.katanamrp.com/v1/products?limit=20 \
--header 'Content-Type: application/json' --header 'Authorization:Bearer <API key>' ❗️
You cannot request more than 250 records at a time. If you raise the limit above this
amount, we will automatically change the limit to 250. We set the limit at 250 because
this is a good trade-off between memory consumption and performance (on the
server-side). The page parameter To paginate results, we use the offset method. The page
query parameter indicates the requested page number. By default, this query parameter is
equal to 1. 📘 In order to provide a better experience, we provide pagination metadata in
response headers, such as first_page and last_page . They are useful indicators for
requesting the previous or next pages. Example of using the page parameter cURL

# This will return the second page of records, the records being paginated by 20.

curl --request GET \
--url https://api.katanamrp.com/v1/products?limit=20&page=2 \
--header 'Content-Type: application/json' --header 'Authorization:Bearer <API key>'
Response All pagination metadata is saved as an object to the X-Pagination header. The
response contains the following structure, whether items are returned or not: Key
Description total_records Total number of records in the result set matching the
filters. total_pages Number of pages in the result set. offset The offset from 0 for the
start of this page. page The indication of the page number being requested first_page
The indication if the request page is the first one in the collection. last_page The
indication if the request page is the last one in the collection.
