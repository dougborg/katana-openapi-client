# Verifying a webhook signature

Verifying a webhook signature This guide walks you through how to verify request
signatures on your server to prevent attackers from imitating valid webhook events.
Suggest Edits Extracting the signature and event body Each webhook event has an
x-sha2-signature header. This header contains the webhook event’s signature in
hexadecimal format. Remember to use the raw event request body because the fields may be
reordered if you first parse it from JSON. 📘 Use the raw event body and don't convert to
an object first. Compute the expected signature A webhook event is valid if the
signature from the header is equal to the expected signature you compute for it. Make
sure signatures are both in binary or hexadecimal before comparing. Example pseudocode
The following pseudocode might be useful for you: verify_webhook_event_signature fun
verify_webhook_event_signature(webhook_event_request) signature_header_hexadecimal =
webhook_event_request.get_header("x-sha2-signature")

# Make sure to use the raw event body and not to convert it to an object first.

raw_event_body = webhook_event_request.body_as_string

# Compute the HMAC using the SHA256 algorithm and using your webhook's token as the key.

expected_signature = hmac(algorithm="SHA256", key=webhook_token, data=raw_event_body)

# Make sure signatures are both in binary, or both in hexadecimal, before comparing.

signature_header = decode_hexadecimal(signature_header_hexadecimal)

# compare computed signature to received signature.

if compare(signature_header, expected_signature) # It is now safe to parse the event
body. return parse_json(raw_event_body) else # Handle an invalid webhook event.
error("Invalid webhook event") Updated over 3 years ago What’s Next Webhook API endpoint
Webhook best practices Table of Contents Extracting the signature and event body Compute
the expected signature Example pseudocode
