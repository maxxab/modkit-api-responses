# Explicit adoption, not a drop-in source migration

The generic library retains success/error/meta presentation, optional fixed Pydantic shapes, exact-single-key unwrap and recursive exclusions. Applications own catalog, metadata and route discovery. No source application has been modified by this extraction.

- Use `success(data, meta=...)` instead of a helper injecting `standard-v1`/api_version. Return type is a dictionary; optional StandardResponse is separate. Supply contract/version metadata explicitly if required. `build_meta` rejects overrides rather than silently replacing base metadata.
- Use `encode_data` explicitly for framework objects, then `unwrap_data` / `strip_fields` if wanted. No snake_case conversion promise. Normalization and bounds differ; arbitrary objects are not accepted by the JSON-tree transform.
- Use `failure(code, message, details=...)`; no catalog lookup or private exception message inference.
- Service health/version payload models and hardcoded supported-version discovery are intentionally not part of this library.
- Serialize the selected representation exactly once. `ReadRepresentation` hashes emitted bytes, not intermediate canonical JSON/path/query. Adoption invalidates older validator strings. URI already participates in HTTP cache keys.
- Prior weak-validator behavior may return200; this library intentionally uses RFC9110 weak comparison for If-None-Match and can return304. This is a deliberate contract change, not claimed behavior-preserving migration.
- Conditional helper returns immutable response description rather than mutating a framework response and returning a payload. HEAD/304 are empty. Full auth/precondition checks remain caller-owned; do not apply to failures or other baseline statuses.
- Optional raw FastAPI responses bypass response-model filtering. Explicit schema documentation and final-byte ownership are application responsibilities.

Before adoption, characterize route auth, response models, middleware, bytes, cache/privacy and existing error contracts. Source migration requires separate authorization. Initial0.x releases may change API with explicit release notes; no release created here.
