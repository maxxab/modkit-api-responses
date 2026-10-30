"""A dependency-free garden app using the installed library (not ERP)."""

import json

from modkit_api_responses import (
    CachePolicy,
    EnvelopeConfig,
    ReadRepresentation,
    conditional_response,
    failure,
    strip_fields,
    success,
)

config = EnvelopeConfig(data_key="result", error_key="problem", meta_key="context")
payload = success(
    strip_fields({"plant": "mint", "private_note": "omit"}, names={"private_note"}),
    config=config,
    meta={"application": "garden"},
)
body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode()
representation = ReadRepresentation(body, {"Content-Type": "application/json"})
first = conditional_response(representation, method="GET", if_none_match=None, policy=CachePolicy("private", 30))
assert first.status == 200 and first.body == body
assert json.loads(first.body)["result"] == {"plant": "mint"}
second = conditional_response(representation, method="GET", if_none_match="W/" + first.headers["etag"])
assert second.status == 304 and second.body == b""
assert failure("NOT_FOUND", "Plant missing", config=config)["problem"]["details"] == {}
