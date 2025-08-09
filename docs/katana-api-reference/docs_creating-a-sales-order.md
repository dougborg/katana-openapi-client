# Creating a sales order

Creating a sales order This guide will show you all the steps needed to create a sales
order. Suggest Edits Using the Katana API, it can be easy to create integrations that
import sales orders from other systems used for customer orders. You can also import
sales orders from e-commerce platforms, CRMs, ERPs, and your own custom solution. Sales
orders in Katana contain data about customers, location, tax rate, variant, and more.
This guide will use the default sales location and pass an id reference to other
mentioned objects. This guide will use the default demo data to cover the following two
workflows: Creating a sales order when a customer, variant, and tax rate already exist
in Katana Creating new objects when references don't already exist Postman collection
You can find all the requests in this tutorial in our postman collection , you only need
to add your API key value to apiKey in the "Variables" tab. If you need it, Postman also
allows you automatically generate code examples in other languages. Gathering existing
data Customer First, let's grab some information connected to a demo data customer using
their email address " [email protected] ". Please refer to our API reference for a
complete list of usable filtering parameters. cURL Node Go Ruby Python PHP curl
--request GET 'https://api.katanamrp.com/v1/ [email protected] ' \
--header 'Authorization: Bearer <Your api key>' var myHeaders = new Headers();
myHeaders.append("Authorization", "Bearer <Your api key>");

var requestOptions = { method: 'GET', headers: myHeaders, redirect: 'manual' };

fetch("https://api.katanamrp.com/v1/ [email protected] ", requestOptions) .then(response
=> response.text()) .then(result => console.log(result)) .catch(error =>
console.log('error', error)); package main

import ( "fmt" "net/http" "io/ioutil" )

func main() {

url := "https://api.katanamrp.com/v1/ [email protected] " method := "GET"

client := &http.Client { CheckRedirect: func(req \*http.Request, via []\*http.Request)
error { return http.ErrUseLastResponse }, } req, err := http.NewRequest(method, url,
nil)

if err != nil { fmt.Println(err) return } req.Header.Add("Authorization", "Bearer
<Your api key>")

res, err := client.Do(req) if err != nil { fmt.Println(err) return } defer
res.Body.Close()

body, err := ioutil.ReadAll(res.Body) if err != nil { fmt.Println(err) return }
fmt.Println(string(body)) } require "uri" require "net/http"

url = URI("https://api.katanamrp.com/v1/ [email protected] ")

https = Net::HTTP.new(url.host, url.port) https.use_ssl = true

request = Net::HTTP::Get.new(url) request["Authorization"] = "Bearer <Your api key>"

response = https.request(request) puts response.read_body import requests

url = "https://api.katanamrp.com/v1/ [email protected] "

payload={} headers = { 'Authorization': 'Bearer <Your api key>' }

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)

<?php

$curl = curl_init();

curl_setopt_array($curl, array(
  CURLOPT_URL => 'https://api.katanamrp.com/v1/
[email protected]
',
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => '',
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 0,
  CURLOPT_FOLLOWLOCATION => true,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => 'GET',
  CURLOPT_HTTPHEADER => array(
    'Authorization: Bearer <Your api key>'
  ),
));

$response = curl_exec($curl);

curl_close($curl);
echo $response;
Our response should show all customers connected to that email address. We will then use the customer's id
customer_id
, to create our sales order.
Variant
We will use the SKU (Stock Keeping Unit) to find a matching product variant. You should see a variant with SKU "LC" within the demo data. Learn more about
listing variants here
.
cURL
Node
Go
Ruby
Python
PHP
curl --request GET 'https://api.katanamrp.com/v1/variants?sku=LC' \
--header 'Authorization: Bearer <Your api key>'
var myHeaders = new Headers();
myHeaders.append("Authorization", "Bearer <Your api key>");

var requestOptions = {
  method: 'GET',
  headers: myHeaders,
  redirect: 'manual'
};

fetch("https://api.katanamrp.com/v1/variants?sku=LC", requestOptions)
  .then(response => response.text())
  .then(result => console.log(result))
  .catch(error => console.log('error', error));
package main

import (
  "fmt"
  "net/http"
  "io/ioutil"
)

func main() {

  url := "https://api.katanamrp.com/v1/variants?sku=LC"
  method := "GET"

  client := &http.Client {
    CheckRedirect: func(req *http.Request, via []*http.Request) error {
      return http.ErrUseLastResponse
    },
  }
  req, err := http.NewRequest(method, url, nil)

  if err != nil {
    fmt.Println(err)
    return
  }
  req.Header.Add("Authorization", "Bearer <Your api key>")

  res, err := client.Do(req)
  if err != nil {
    fmt.Println(err)
    return
  }
  defer res.Body.Close()

  body, err := ioutil.ReadAll(res.Body)
  if err != nil {
    fmt.Println(err)
    return
  }
  fmt.Println(string(body))
}
require "uri"
require "net/http"

url = URI("https://api.katanamrp.com/v1/variants?sku=LC")

https = Net::HTTP.new(url.host, url.port)
https.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = "Bearer <Your api key>"

response = https.request(request)
puts response.read_body
import requests

url = "https://api.katanamrp.com/v1/variants?sku=LC"

payload={}
headers = {
  'Authorization': 'Bearer <Your api key>'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
<?php

$curl = curl_init();

curl_setopt_array($curl, array(
  CURLOPT_URL => 'https://api.katanamrp.com/v1/variants?sku=LC',
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => '',
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 0,
  CURLOPT_FOLLOWLOCATION => true,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => 'GET',
  CURLOPT_HTTPHEADER => array(
    'Authorization: Bearer <Your api key>'
  ),
));

$response = curl_exec($curl);

curl_close($curl);
echo $response;
Like with the customer case, take the id from the first response item and use this as
variant_id
when creating your sales order.
Tax Rate
Adding a tax rate is optional when creating a sales order, and omitting it will result in no tax rate added to the sales order. The demo data contains a 20% tax rate, so we should get that rate as a response. Head to the
reference
to learn more about tax rates.
cURL
Node
Go
Ruby
Python
PHP
curl --request GET 'https://api.katanamrp.com/v1/tax_rates?rate=20' \
--header 'Authorization: Bearer <Your api key>'
var myHeaders = new Headers();
myHeaders.append("Authorization", "Bearer <Your api key>");

var requestOptions = {
  method: 'GET',
  headers: myHeaders,
  redirect: 'manual'
};

fetch("https://api.katanamrp.com/v1/tax_rates?rate=20", requestOptions)
  .then(response => response.text())
  .then(result => console.log(result))
  .catch(error => console.log('error', error));
package main

import (
  "fmt"
  "net/http"
  "io/ioutil"
)

func main() {

  url := "https://api.katanamrp.com/v1/tax_rates?rate=20"
  method := "GET"

  client := &http.Client {
    CheckRedirect: func(req *http.Request, via []*http.Request) error {
      return http.ErrUseLastResponse
    },
  }
  req, err := http.NewRequest(method, url, nil)

  if err != nil {
    fmt.Println(err)
    return
  }
  req.Header.Add("Authorization", "Bearer <Your api key>")

  res, err := client.Do(req)
  if err != nil {
    fmt.Println(err)
    return
  }
  defer res.Body.Close()

  body, err := ioutil.ReadAll(res.Body)
  if err != nil {
    fmt.Println(err)
    return
  }
  fmt.Println(string(body))
}
require "uri"
require "net/http"

url = URI("https://api.katanamrp.com/v1/tax_rates?rate=20")

https = Net::HTTP.new(url.host, url.port)
https.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = "Bearer <Your api key>"

response = https.request(request)
puts response.read_body
import requests

url = "https://api.katanamrp.com/v1/tax_rates?rate=20"

payload={}
headers = {
  'Authorization': 'Bearer <Your api key>'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
<?php

$curl = curl_init();

curl_setopt_array($curl, array(
  CURLOPT_URL => 'https://api.katanamrp.com/v1/tax_rates?rate=20',
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => '',
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 0,
  CURLOPT_FOLLOWLOCATION => false,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => 'GET',
  CURLOPT_HTTPHEADER => array(
    'Authorization: Bearer <Your api key>'
  ),
));

$response = curl_exec($curl);

curl_close($curl);
echo $response;
Once again, grab the id and use it for
tax_rate_id
on the sales order.
Location
Location is another optional data point that you can map out. In this example, we won't be passing location id, but you can refer to
location
to learn more about location.
Sales order
Once you've gathered all the required references, we can now
create the sales order
.
cURL
Node
Go
Ruby
Python
PHP
curl --request POST 'https://api.katanamrp.com/v1/sales_orders' \
--header 'Authorization: Bearer <Your api key>' \
--header 'Content-Type: application/json' \
--data-raw '{
    "order_no": "API-001[DEMO]",
    "customer_id": <customer_id>,
    "sales_order_rows": [
        {
            "quantity": 2,
            "price_per_unit": 275,
            "tax_rate_id": <tax_rate_id>,
            "variant_id": <variant_id>
        }
    ]
}'
var myHeaders = new Headers();
myHeaders.append("Authorization", "Bearer <Your api key>");
myHeaders.append("Content-Type", "application/json");

var raw = "{\r\n    \"order_no\": \"API-001[DEMO]\",\r\n    \"customer_id\": <customer id>,\r\n    \"sales_order_rows\": [\r\n        {\r\n            \"quantity\": 2,\r\n            \"price_per_unit\": 275,\r\n            \"tax_rate_id\": <tax rate id>,\r\n            \"variant_id\": <variant id>\r\n        }\r\n    ]\r\n}";

var requestOptions = {
  method: 'POST',
  headers: myHeaders,
  body: raw,
  redirect: 'manual'
};

fetch("https://api.katanamrp.com/v1/sales_orders", requestOptions)
  .then(response => response.text())
  .then(result => console.log(result))
  .catch(error => console.log('error', error));
package main

import (
  "fmt"
  "strings"
  "net/http"
  "io/ioutil"
)

func main() {

  url := "https://api.katanamrp.com/v1/sales_orders"
  method := "POST"

  payload := strings.NewReader(`{`+"
"+`
    "order_no": "API-001[DEMO]",`+"
"+`
    "customer_id": <customer id>,`+"
"+`
    "sales_order_rows": [`+"
"+`
        {`+"
"+`
            "quantity": 2,`+"
"+`
            "price_per_unit": 275,`+"
"+`
            "tax_rate_id": <tax rate id>,`+"
"+`
            "variant_id": <variant id>`+"
"+`
        }`+"
"+`
    ]`+"
"+`
}`)

  client := &http.Client {
    CheckRedirect: func(req *http.Request, via []*http.Request) error {
      return http.ErrUseLastResponse
    },
  }
  req, err := http.NewRequest(method, url, payload)

  if err != nil {
    fmt.Println(err)
    return
  }
  req.Header.Add("Authorization", "Bearer <Your api key>")
  req.Header.Add("Content-Type", "application/json")

  res, err := client.Do(req)
  if err != nil {
    fmt.Println(err)
    return
  }
  defer res.Body.Close()

  body, err := ioutil.ReadAll(res.Body)
  if err != nil {
    fmt.Println(err)
    return
  }
  fmt.Println(string(body))
}
require "uri"
require "net/http"

url = URI("https://api.katanamrp.com/v1/sales_orders")

https = Net::HTTP.new(url.host, url.port)
https.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = "Bearer <Your api key>"
request["Content-Type"] = "application/json"
request.body = "{\r\n    \"order_no\": \"API-001[DEMO]\",\r\n    \"customer_id\": <customer id>,\r\n    \"sales_order_rows\": [\r\n        {\r\n            \"quantity\": 2,\r\n            \"price_per_unit\": 275,\r\n            \"tax_rate_id\": <tax rate id>,\r\n            \"variant_id\": <variant id>\r\n        }\r\n    ]\r\n}"

response = https.request(request)
puts response.read_body
import http.client

conn = http.client.HTTPSConnection("api.katanamrp.com")
payload = "{\r\n    \"order_no\": \"API-001[DEMO]\",\r\n    \"customer_id\": <customer id>,\r\n    \"sales_order_rows\": [\r\n        {\r\n            \"quantity\": 2,\r\n            \"price_per_unit\": 275,\r\n            \"tax_rate_id\": <tax rate id>,\r\n            \"variant_id\": <variant id>\r\n        }\r\n    ]\r\n}"
headers = {
  'Authorization': 'Bearer <Your api key>',
  'Content-Type': 'application/json'
}
conn.request("POST", "/v1/sales_orders", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
<?php

$curl = curl_init();

curl_setopt_array($curl, array(
  CURLOPT_URL => 'https://api.katanamrp.com/v1/sales_orders',
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => '',
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 0,
  CURLOPT_FOLLOWLOCATION => false,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => 'POST',
  CURLOPT_POSTFIELDS =>'{
    "order_no": "API-001[DEMO]",
    "customer_id": <customer id>,
    "sales_order_rows": [
        {
            "quantity": 2,
            "price_per_unit": 275,
            "tax_rate_id": <tax rate id>,
            "variant_id": <variant id>
        }
    ]
}',
  CURLOPT_HTTPHEADER => array(
    'Authorization: Bearer <Your api key>',
    'Content-Type: application/json'
  ),
));

$response = curl_exec($curl);

curl_close($curl);
echo $response;
In addition to fetched ids, you will need to provide an order_no, an identifier for each sales order. Each sales order row also requires a quantity and price per unit.
Creating new references
When building an integration, it's best to assume you won't always find a matching variant, customer, or tax rate. If a reference object is missing in Katana, we recommend creating a new one to ensure that the integration is stable and won't fail in the future.
Customer
A name needs to be provided to
create a new customer
. Since we initially did a search based on email, we'll provide that too (although the email address is optional).
cURL
Node
Go
Ruby
Python
PHP
curl --request POST 'https://api.katanamrp.com/v1/customers' \
--header 'Authorization: Bearer <Your api key>' \
--header 'Content-Type: application/json' \
--data-raw '{
    "email": "
[email protected]
",
    "name": "New Jane Rooms [API DEMO]"
}'
var myHeaders = new Headers();
myHeaders.append("Authorization", "Bearer <Your api key>");
myHeaders.append("Content-Type", "application/json");

var raw = JSON.stringify({"email":"
[email protected]
","name":"New Jane Rooms [API DEMO]"});

var requestOptions = {
  method: 'POST',
  headers: myHeaders,
  body: raw,
  redirect: 'manual'
};

fetch("https://api.katanamrp.com/v1/customers", requestOptions)
  .then(response => response.text())
  .then(result => console.log(result))
  .catch(error => console.log('error', error));
package main

import (
  "fmt"
  "strings"
  "net/http"
  "io/ioutil"
)

func main() {

  url := "https://api.katanamrp.com/v1/customers"
  method := "POST"

  payload := strings.NewReader(`{`+"
"+`
    "email": "
[email protected]
",`+"
"+`
    "name": "New Jane Rooms [API DEMO]"`+"
"+`
}`)

  client := &http.Client {
    CheckRedirect: func(req *http.Request, via []*http.Request) error {
      return http.ErrUseLastResponse
    },
  }
  req, err := http.NewRequest(method, url, payload)

  if err != nil {
    fmt.Println(err)
    return
  }
  req.Header.Add("Authorization", "Bearer <Your api key>")
  req.Header.Add("Content-Type", "application/json")

  res, err := client.Do(req)
  if err != nil {
    fmt.Println(err)
    return
  }
  defer res.Body.Close()

  body, err := ioutil.ReadAll(res.Body)
  if err != nil {
    fmt.Println(err)
    return
  }
  fmt.Println(string(body))
}
require "uri"
require "net/http"

url = URI("https://api.katanamrp.com/v1/customers")

https = Net::HTTP.new(url.host, url.port)
https.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = "Bearer <Your api key>"
request["Content-Type"] = "application/json"
request.body = "{\r\n    \"email\": \"
[email protected]
\",\r\n    \"name\": \"New Jane Rooms [API DEMO]\"\r\n}"

response = https.request(request)
puts response.read_body
import requests

url = "https://api.katanamrp.com/v1/customers"

payload="{\r\n    \"email\": \"
[email protected]
\",\r\n    \"name\": \"New Jane Rooms [API DEMO]\"\r\n}"
headers = {
  'Authorization': 'Bearer <Your api key>',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
<?php

$curl = curl_init();

curl_setopt_array($curl, array(
  CURLOPT_URL => 'https://api.katanamrp.com/v1/customers',
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => '',
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 0,
  CURLOPT_FOLLOWLOCATION => false,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => 'POST',
  CURLOPT_POSTFIELDS =>'{
    "email": "
[email protected]
",
    "name": "New Jane Rooms [API DEMO]"
}',
  CURLOPT_HTTPHEADER => array(
    'Authorization: Bearer <Your api key>',
    'Content-Type: application/json'
  ),
));

$response = curl_exec($curl);

curl_close($curl);
echo $response;
You should no longer get a list in the response but rather an object. Keep the
customer_id
handy for future use.
Tax rate
Let's try a real-life situation - the tax rate has risen to 25%. Unfortunately, this tax rate no longer matches the demo data, so we need to
create a new tax rate
. Let's also distinguish this tax rate as demo data to keep track of things.
cURL
Node
Go
Ruby
Python
PHP
curl --request POST 'https://api.katanamrp.com/v1/tax_rates' \
--header 'Authorization: Bearer <Your api key>' \
--header 'Content-Type: application/json' \
--data-raw '{
    "rate": 25,
    "name": "VAT [API DEMO]"
}'
var myHeaders = new Headers();
myHeaders.append("Authorization", "Bearer <Your api key>");
myHeaders.append("Content-Type", "application/json");

var raw = JSON.stringify({"rate":25,"name":"VAT [API DEMO]"});

var requestOptions = {
  method: 'POST',
  headers: myHeaders,
  body: raw,
  redirect: 'manual'
};

fetch("https://api.katanamrp.com/v1/tax_rates", requestOptions)
  .then(response => response.text())
  .then(result => console.log(result))
  .catch(error => console.log('error', error));
package main

import (
  "fmt"
  "strings"
  "net/http"
  "io/ioutil"
)

func main() {

  url := "https://api.katanamrp.com/v1/tax_rates"
  method := "POST"

  payload := strings.NewReader(`{`+"
"+`
    "rate": 25,`+"
"+`
    "name": "VAT [API DEMO]"`+"
"+`
}`)

  client := &http.Client {
    CheckRedirect: func(req *http.Request, via []*http.Request) error {
      return http.ErrUseLastResponse
    },
  }
  req, err := http.NewRequest(method, url, payload)

  if err != nil {
    fmt.Println(err)
    return
  }
  req.Header.Add("Authorization", "Bearer <Your api key>")
  req.Header.Add("Content-Type", "application/json")

  res, err := client.Do(req)
  if err != nil {
    fmt.Println(err)
    return
  }
  defer res.Body.Close()

  body, err := ioutil.ReadAll(res.Body)
  if err != nil {
    fmt.Println(err)
    return
  }
  fmt.Println(string(body))
}
require "uri"
require "net/http"

url = URI("https://api.katanamrp.com/v1/tax_rates")

https = Net::HTTP.new(url.host, url.port)
https.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = "Bearer <Your api key>"
request["Content-Type"] = "application/json"
request.body = "{\r\n    \"rate\": 25,\r\n    \"name\": \"VAT [API DEMO]\"\r\n}"

response = https.request(request)
puts response.read_body
import http.client

conn = http.client.HTTPSConnection("api.katanamrp.com")
payload = "{\r\n    \"rate\": 25,\r\n    \"name\": \"VAT [API DEMO]\"\r\n}"
headers = {
  'Authorization': 'Bearer <Your api key>',
  'Content-Type': 'application/json'
}
conn.request("POST", "/v1/tax_rates", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
<?php

$curl = curl_init();

curl_setopt_array($curl, array(
  CURLOPT_URL => 'https://api.katanamrp.com/v1/tax_rates',
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => '',
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 0,
  CURLOPT_FOLLOWLOCATION => false,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => 'POST',
  CURLOPT_POSTFIELDS =>'{
    "rate": 25,
    "name": "VAT [API DEMO]"
}',
  CURLOPT_HTTPHEADER => array(
    'Authorization: Bearer <Your api key>',
    'Content-Type: application/json'
  ),
));

$response = curl_exec($curl);

curl_close($curl);
echo $response;
Variant
Creating a variant can be somewhat trickier since it's related to a product. To
create a new variant
, we need to provide a
product_id
. First, we will search the product id by name and add a variant to it. Later on, we'll show you how to create a new product along with a variant.
When a product exists
The demo data includes a "Lounge chair [DEMO]", so let's go ahead and get this
product
.
cURL
Node
Go
Ruby
Python
PHP
curl -g --request GET 'https://api.katanamrp.com/v1/products?name=Lounge%20chair%20[DEMO]' \
--header 'Authorization: Bearer <Your api key>'
var myHeaders = new Headers();
myHeaders.append("Authorization", "Bearer <Your api key>");

var requestOptions = {
  method: 'GET',
  headers: myHeaders,
  redirect: 'manual'
};

fetch("https://api.katanamrp.com/v1/products?name=Lounge chair [DEMO]", requestOptions)
  .then(response => response.text())
  .then(result => console.log(result))
  .catch(error => console.log('error', error));
package main

import (
  "fmt"
  "net/http"
  "io/ioutil"
)

func main() {

  url := "https://api.katanamrp.com/v1/products?name=Lounge%20chair%20%5BDEMO%5D"
  method := "GET"

  client := &http.Client {
    CheckRedirect: func(req *http.Request, via []*http.Request) error {
      return http.ErrUseLastResponse
    },
  }
  req, err := http.NewRequest(method, url, nil)

  if err != nil {
    fmt.Println(err)
    return
  }
  req.Header.Add("Authorization", "Bearer <Your api key>")

  res, err := client.Do(req)
  if err != nil {
    fmt.Println(err)
    return
  }
  defer res.Body.Close()

  body, err := ioutil.ReadAll(res.Body)
  if err != nil {
    fmt.Println(err)
    return
  }
  fmt.Println(string(body))
}
require "uri"
require "net/http"

url = URI("https://api.katanamrp.com/v1/products?name=Lounge chair [DEMO]")

https = Net::HTTP.new(url.host, url.port)
https.use_ssl = true

request = Net::HTTP::Get.new(url)
request["Authorization"] = "Bearer <Your api key>"

response = https.request(request)
puts response.read_body
import requests

url = "https://api.katanamrp.com/v1/products?name=Lounge chair [DEMO]"

payload={}
headers = {
  'Authorization': 'Bearer <Your api key>'
}

response = requests.request("GET", url, headers=headers, data=payload)

print(response.text)
<?php

$curl = curl_init();

curl_setopt_array($curl, array(
  CURLOPT_URL => 'https://api.katanamrp.com/v1/products?name=Lounge%20chair%20%5BDEMO%5D',
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => '',
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 0,
  CURLOPT_FOLLOWLOCATION => false,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => 'GET',
  CURLOPT_HTTPHEADER => array(
    'Authorization: Bearer <Your api key>'
  ),
));

$response = curl_exec($curl);

curl_close($curl);
echo $response;
We need to grab the id from the first element of the response list and use this as
product_id
when
creating a variant
cURL
Node
Go
Ruby
Python
PHP
curl --request POST 'https://api.katanamrp.com/v1/variants' \
--header 'Authorization: Bearer <Your api key>' \
--header 'Content-Type: application/json' \
--data-raw '{
    "sku": "LC-2",
    "sales_price": 280,
    "product_id": <product_id>
}'
var myHeaders = new Headers();
myHeaders.append("Authorization", "Bearer <Your api key>");
myHeaders.append("Content-Type", "application/json");

var raw = "{\r\n    \"sku\": \"LC-2\",\r\n    \"sales_price\": 280,\r\n    \"product_id\": <product id>\r\n}";

var requestOptions = {
  method: 'POST',
  headers: myHeaders,
  body: raw,
  redirect: 'manual'
};

fetch("https://api.katanamrp.com/v1/variants", requestOptions)
  .then(response => response.text())
  .then(result => console.log(result))
  .catch(error => console.log('error', error));
package main

import (
  "fmt"
  "strings"
  "net/http"
  "io/ioutil"
)

func main() {

  url := "https://api.katanamrp.com/v1/variants"
  method := "POST"

  payload := strings.NewReader(`{`+"
"+`
    "sku": "LC-2",`+"
"+`
    "sales_price": 280,`+"
"+`
    "product_id": <product id>`+"
"+`
}`)

  client := &http.Client {
    CheckRedirect: func(req *http.Request, via []*http.Request) error {
      return http.ErrUseLastResponse
    },
  }
  req, err := http.NewRequest(method, url, payload)

  if err != nil {
    fmt.Println(err)
    return
  }
  req.Header.Add("Authorization", "Bearer <Your api key>")
  req.Header.Add("Content-Type", "application/json")

  res, err := client.Do(req)
  if err != nil {
    fmt.Println(err)
    return
  }
  defer res.Body.Close()

  body, err := ioutil.ReadAll(res.Body)
  if err != nil {
    fmt.Println(err)
    return
  }
  fmt.Println(string(body))
}
require "uri"
require "net/http"

url = URI("https://api.katanamrp.com/v1/variants")

https = Net::HTTP.new(url.host, url.port)
https.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = "Bearer <Your api key>"
request["Content-Type"] = "application/json"
request.body = "{\r\n    \"sku\": \"LC-2\",\r\n    \"sales_price\": 280,\r\n    \"product_id\": <product id>\r\n}"

response = https.request(request)
puts response.read_body
import requests

url = "https://api.katanamrp.com/v1/variants"

payload="{\r\n    \"sku\": \"LC-2\",\r\n    \"sales_price\": 280,\r\n    \"product_id\": <product id>\r\n}"
headers = {
  'Authorization': 'Bearer <Your api key>',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
<?php

$curl = curl_init();

curl_setopt_array($curl, array(
  CURLOPT_URL => 'https://api.katanamrp.com/v1/variants',
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => '',
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 0,
  CURLOPT_FOLLOWLOCATION => false,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => 'POST',
  CURLOPT_POSTFIELDS =>'{
    "sku": "LC-2",
    "sales_price": 280,
    "product_id": <product id>
}',
  CURLOPT_HTTPHEADER => array(
    'Authorization: Bearer <Your api key>',
    'Content-Type: application/json'
  ),
));

$response = curl_exec($curl);

curl_close($curl);
echo $response;
Let's store the id here as
variant_id
for future use.
When a product doesn't exist in the database
Sometimes a product doesn't exist yet, which means we need to
create a new product
. To do this, we need to provide the product's name and an array of variants with SKU and a default sales price. During this step, we are creating a new product and variant simultaneously.
cURL
Node
Go
Ruby
Python
PHP
curl --request POST 'https://api.katanamrp.com/v1/products' \
--header 'Authorization: Bearer <Your api key>' \
--header 'Content-Type: application/json' \
--data-raw '{
    "name": "Yet another table [API DEMO]",
    "variants": [
        {
            "sku": "YAT-1",
            "sales_price": 320
        }
    ]
}'
var myHeaders = new Headers();
myHeaders.append("Authorization", "Bearer <Your api key>");
myHeaders.append("Content-Type", "application/json");

var raw = JSON.stringify({"name":"Yet another table [API DEMO]","variants":[{"sku":"YAT-1","sales_price":320}]});

var requestOptions = {
  method: 'POST',
  headers: myHeaders,
  body: raw,
  redirect: 'manual'
};

fetch("https://api.katanamrp.com/v1/products", requestOptions)
  .then(response => response.text())
  .then(result => console.log(result))
  .catch(error => console.log('error', error));
package main

import (
  "fmt"
  "strings"
  "net/http"
  "io/ioutil"
)

func main() {

  url := "https://api.katanamrp.com/v1/products"
  method := "POST"

  payload := strings.NewReader(`{`+"
"+`
    "name": "Yet another table [API DEMO]",`+"
"+`
    "variants": [`+"
"+`
        {`+"
"+`
            "sku": "YAT-1",`+"
"+`
            "sales_price": 320`+"
"+`
        }`+"
"+`
    ]`+"
"+`
}`)

  client := &http.Client {
    CheckRedirect: func(req *http.Request, via []*http.Request) error {
      return http.ErrUseLastResponse
    },
  }
  req, err := http.NewRequest(method, url, payload)

  if err != nil {
    fmt.Println(err)
    return
  }
  req.Header.Add("Authorization", "Bearer <Your api key>")
  req.Header.Add("Content-Type", "application/json")

  res, err := client.Do(req)
  if err != nil {
    fmt.Println(err)
    return
  }
  defer res.Body.Close()

  body, err := ioutil.ReadAll(res.Body)
  if err != nil {
    fmt.Println(err)
    return
  }
  fmt.Println(string(body))
}
require "uri"
require "net/http"

url = URI("https://api.katanamrp.com/v1/products")

https = Net::HTTP.new(url.host, url.port)
https.use_ssl = true

request = Net::HTTP::Post.new(url)
request["Authorization"] = "Bearer <Your api key>"
request["Content-Type"] = "application/json"
request.body = "{\r\n    \"name\": \"Yet another table [API DEMO]\",\r\n    \"variants\": [\r\n        {\r\n            \"sku\": \"YAT-1\",\r\n            \"sales_price\": 320\r\n        }\r\n    ]\r\n}"

response = https.request(request)
puts response.read_body
import requests

url = "https://api.katanamrp.com/v1/products"

payload="{\r\n    \"name\": \"Yet another table [API DEMO]\",\r\n    \"variants\": [\r\n        {\r\n            \"sku\": \"YAT-1\",\r\n            \"sales_price\": 320\r\n        }\r\n    ]\r\n}"
headers = {
  'Authorization': 'Bearer <Your api key>',
  'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
<?php

$curl = curl_init();

curl_setopt_array($curl, array(
  CURLOPT_URL => 'https://api.katanamrp.com/v1/products',
  CURLOPT_RETURNTRANSFER => true,
  CURLOPT_ENCODING => '',
  CURLOPT_MAXREDIRS => 10,
  CURLOPT_TIMEOUT => 0,
  CURLOPT_FOLLOWLOCATION => false,
  CURLOPT_HTTP_VERSION => CURL_HTTP_VERSION_1_1,
  CURLOPT_CUSTOMREQUEST => 'POST',
  CURLOPT_POSTFIELDS =>'{
    "name": "Yet another table [API DEMO]",
    "variants": [
        {
            "sku": "YAT-1",
            "sales_price": 320
        }
    ]
}',
  CURLOPT_HTTPHEADER => array(
    'Authorization: Bearer <Your api key>',
    'Content-Type: application/json'
  ),
));

$response = curl_exec($curl);

curl_close($curl);
echo $response;
As a response, we receive the product object, but as we need the variant id to create a sales order we'll look at the variants list in the response and take the id from the first item in the list to use as
variant_id
.
Sales order
Now that we have created all the resources we need to reference, we can go ahead and create a sales order. The request to create a sales order is the
same as before
.
Updated
over 3 years ago
Table of Contents
Postman collection
Gathering existing data
Customer
Variant
Tax Rate
Location
Sales order
Creating new references
Customer
Tax rate
Variant
Sales order
