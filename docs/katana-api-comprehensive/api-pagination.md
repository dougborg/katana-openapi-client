# Pagination

All queries that retrieve a list of records are paginated. The parameters for
controlling pagination arelimitandpage.

## Thelimitparameter

Example of using the limit parameter

## Example of using the limit parameter

## ❗️

You cannot request more than 250 records at a time. If you raise the limit above this
amount, we will automatically change the limit to 250.

## Thepageparameter

To paginate results, we use the offset method. The page query parameter indicates the
requested page number. By default, this query parameter is equal to 1.

## 📘

In order to provide a better experience, we provide pagination metadata in response
headers, such asfirst_pageandlast_page. They are useful indicators for requesting the
previous or next pages. Example of using the page parameter

## Example of using the page parameter

## Response

All pagination metadata is saved as an object to theX-Paginationheader. The response
contains the following structure, whether items are returned or not:

| Key           | Description                                                            |
| ------------- | ---------------------------------------------------------------------- |
| total_records | Total number of records in the result set matching the filters.        |
| total_pages   | Number of pages in the result set.                                     |
| offset        | The offset from 0 for the start of this page.                          |
| page          | The indication of the page number being requested                      |
| first_page    | The indication if the request page is the first one in the collection. |
| last_page     | The indication if the request page is the last one in the collection.  |
