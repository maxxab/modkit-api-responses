# modkit-api-responses

Small response-envelope and conditional-read helpers. Python 3.12+. The core has **no runtime dependencies**, imports no application or sibling package, and includes no client SDK.

```python
import json
from modkit_api_responses import ReadRepresentation, conditional_response, success

body = json.dumps(success({"plant": "mint"})).encode()
result = conditional_response(ReadRepresentation(body), method="GET", if_none_match=None)
assert result.status == 200
```

## Presentation

`EnvelopeConfig` configures distinct data/error/meta keys. `success` and `failure` return fresh outer dictionaries, not Pydantic models; nested payload ownership and serialization belong to the caller. Error details default to `{}`. No implicit contract name, version, catalog, logging, or key-case conversion.

`build_meta(base=..., extra=...)` omits `None` extra values and rejects collisions. Explicit `unwrap_data` unwraps only a plain dictionary with exactly the configured single key. `strip_fields` recursively removes configured string keys from a plain JSON tree, without mutating it or invoking object stringification. It rejects non-JSON, cycles and nonfinite floats; defaults are depth64 and 10,000 total nodes, configurable. It is not automatic secret detection. Excluded values are also validated/counted.

## Conditional reads

Pass **final serialized bytes** and optional headers through `ReadRepresentation`, then call `conditional_response`. Only an existing baseline-200 GET/HEAD representation is supported. Run authentication, authorization, normal errors and earlier applicable RFC preconditions first. A failed If-Match must win; If-Modified-Since is ignored when If-None-Match is present. This package is not a full precondition evaluator or middleware. Unsupported method invocation is `ValueError`, not an automatic HTTP405 response.

ETags hash exact bytes using SHA256. `matches_if_none_match` uses weak comparison, supports quoted commas/empty tags/reasonable empty list elements and standalone `*`. Combine repeated If-None-Match field lines with commas. Malformed fields are ignored in their entirety; resource limits raise `ValueError`. Defaults: 8192 UTF-8 bytes, 128 tags, configurable positive bounds. Do not silently map limit errors to successful cached responses.

Cache default is `no-store`; private permits browser storage, public requires explicit opt-in. `no-store` is not an exemption from conditional304. Vary merges case-insensitively, preserves wildcard and rejects invalid tokens; it is not a privacy boundary. Header names are normalized lowercase; supplied headers snapshot immutably. ETag/Cache-Control replaced, stale length/framing removed, other headers preserved. HEAD and304 body empty, Content-Length omitted. Keep compression/other representation transformations before validation, or have downstream middleware regenerate/remove invalid validators. Streaming/files/ranges are outside scope.

## Optional integrations

`pip install 'modkit-api-responses[pydantic]'` exposes fixed-shape `StandardResponse[T]`, `StandardError`, `StandardErrorResponse` in `adapters.pydantic`. Those model fields are not renamed by `EnvelopeConfig`.

`pip install 'modkit-api-responses[fastapi]'` exposes `encode_data` and `to_response` in `adapters.fastapi`. Encode models, explicitly transform/wrap, serialize once, hash the resulting bytes, then return `to_response(result)`. Returning a raw response bypasses framework response-model conversion/filtering; register/document schemas explicitly. Register HEAD explicitly. The adapter never JSON-serializes304 to `null` and avoids a false zero length on HEAD.

See `examples/sample_app.py` and [migration notes](docs/migration.md). MIT; copyright notices retained. Version0.1 is an initial API; publication/name availability is not established by this checkout.

## Development

`python -m pip install -r requirements-dev.txt`; `python -m pytest`; `ruff check src tests examples scripts`; `python -m build`; `python -m twine check dist/*`; `python scripts/check_wheel.py dist/<wheel>`. The checker tests a fresh venv outside checkout, both core and optional adapters; `--core-only` omits optional integration tests. CI defines three OSes; configured CI is not evidence of remote execution.
