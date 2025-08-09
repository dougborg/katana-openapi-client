# The customer object

Attribute Description id Unique identifier for the object. name The customer’s full name
or company name used throughout Katana for identifying the customer. first_name The
customer's first name. last_name The customer's last name. company The customer's
company name. email The customer’s email address. phone The customer’s phone number.
comment A string attached to the object to add any internal comments. currency The
currency that the customer does their business in. This currency will be used by default
when creating sales orders for the customer. reference_id Identifier for external
systems to associate the customer record with third-party integrations category Customer
category identifier to additionally group contacts based on any freely chosen value
discount_rate Customer discount rate that applies to sales order line items created_at
The timestamp when the customer was created. updated_at The timestamp when the customer
was last updated. default_billing_id The ID of the billing address that is used as
default when adding new sales orders for the customer. default_shipping_id The ID of the
shipping address that is used as default when adding new sales orders for the customer.
addresses An array of shipping and billing addresses. The customer address object
Attribute Description id Unique identifier for the customer address object. customer_id
The ID of the customer to who this address belongs. entity_type Either "billing" or
"shipping" depending on the address type. default Indicating whether the address is used
as default when adding new sales orders for the customer. first_name The first name of
the person related to the address. last_name The last name of the person related to the
address. company The company name related to the address. phone The phone number related
to the address. line_1 The first line of the address (street name and house number).
line_2 The second line of the address (apartment, suite, unit, or building). city The
city of the address. state The state of the address. zip The zip code of the address.
country The country of the address. created_at The timestamp when the address was
created. updated_at The timestamp when the address was updated.
