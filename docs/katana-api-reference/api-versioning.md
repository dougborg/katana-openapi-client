# Versioning

All publicly released versions of Katana API will never change in a way that could
impact an existing integration. Whenever Katana makes an API change, a new version of
the API is released, which clients can choose whether or not to upgrade their
integration to. We have 2 types of releases: minor and major. Minor releases Minor
releases are characterized by adding decimal points to a whole number. For example -
v1.0 to v1.1 These releases contain only backward-compatible changes, i.e. additive
changes. It's safe for clients to move from one minor version to another unless the
additive changes aren't backward-compatible to their build. Major releases A major
release is displayed via a whole number change. For example - v1.1 to v2.0 Major
releases contain backward-incompatible updates. Any client will most likely need to
update their integration to move to a major release version. Backwards compatibility The
following changes are considered backward-compatible and non-breaking: adding new API
endpoints adding new properties to the responses from existing API endpoints adding
optional request parameters to existing API endpoints altering the message attributes
returned by validation failures or other errors
