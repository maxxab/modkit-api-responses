"""Shallow, caller-serialized envelopes; no implicit application metadata."""

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class EnvelopeConfig:
    data_key: str = "data"
    error_key: str = "error"
    meta_key: str = "meta"

    def __post_init__(self) -> None:
        keys = (self.data_key, self.error_key, self.meta_key)
        if any(not isinstance(key, str) or not key for key in keys) or len(set(keys)) != 3:
            raise ValueError("Envelope keys must be distinct nonempty strings")


DEFAULT_ENVELOPE = EnvelopeConfig()


def build_meta(
    *, base: Mapping[str, object] | None = None, extra: Mapping[str, object] | None = None
) -> dict[str, object]:
    result = dict(base or {})
    for key, value in (extra or {}).items():
        if value is not None:
            if key in result:
                raise ValueError("Metadata keys must not override base values")
            result[key] = value
    return result


def success(
    data: object, *, config: EnvelopeConfig = DEFAULT_ENVELOPE, meta: Mapping[str, object] | None = None
) -> dict[str, object]:
    return {config.data_key: data, config.meta_key: dict(meta or {})}


def failure(
    code: str,
    message: str,
    *,
    details: Mapping[str, object] | None = None,
    config: EnvelopeConfig = DEFAULT_ENVELOPE,
    meta: Mapping[str, object] | None = None,
) -> dict[str, object]:
    return {
        config.error_key: {"code": code, "message": message, "details": dict(details or {})},
        config.meta_key: dict(meta or {}),
    }
