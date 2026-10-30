"""Conditional baseline-200 reads; application owns auth and RFC preconditions."""

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal

from .etag import make_etag, matches_if_none_match

_TOKEN = re.compile(r"[!#$%&'*+.^_`|~0-9A-Za-z-]+")


def _headers(headers: Mapping[str, str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for name, value in headers.items():
        if not isinstance(name, str) or not _TOKEN.fullmatch(name):
            raise ValueError("Invalid HTTP field name")
        if not isinstance(value, str) or any(ord(c) < 32 and c != "\t" or ord(c) == 127 or ord(c) > 255 for c in value):
            raise ValueError("Invalid HTTP field value")
        key = name.lower()
        if key in result:
            if key == "vary":
                value = result[key] + ", " + value
            else:
                raise ValueError("Duplicate case-insensitive HTTP field")
        result[key] = value
    return result


@dataclass(frozen=True)
class ReadRepresentation:
    """Exact selected GET bytes and headers, after application preconditions."""

    body: bytes
    headers: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.body, bytes):
            raise TypeError("Representation must contain finalized bytes")
        object.__setattr__(self, "headers", MappingProxyType(_headers(self.headers)))


@dataclass(frozen=True)
class CachePolicy:
    mode: Literal["no-store", "private", "public"] = "no-store"
    max_age: int | None = None

    def __post_init__(self) -> None:
        if self.mode not in ("no-store", "private", "public"):
            raise ValueError("Unknown cache policy")
        if self.max_age is not None and (type(self.max_age) is not int or self.max_age < 0 or self.mode == "no-store"):
            raise ValueError("Invalid cache max-age")


@dataclass(frozen=True)
class ConditionalResponse:
    status: int
    headers: Mapping[str, str]
    body: bytes

    def __post_init__(self) -> None:
        if self.status not in (200, 304) or not isinstance(self.body, bytes):
            raise ValueError("Expected finalized 200/304 response")
        if self.status == 304 and self.body:
            raise ValueError("304 responses cannot have content")
        object.__setattr__(self, "headers", MappingProxyType(_headers(self.headers)))


def conditional_response(
    representation: ReadRepresentation,
    *,
    method: Literal["GET", "HEAD"],
    if_none_match: str | None,
    policy: CachePolicy = CachePolicy(),
    vary: Sequence[str] = (),
) -> ConditionalResponse:
    """Apply If-None-Match to an existing baseline-200 representation only.

    The caller must handle authentication/errors and earlier applicable
    preconditions first. If-Modified-Since is ignored when If-None-Match is
    present. This function is not a complete precondition evaluator.
    """
    if method not in ("GET", "HEAD"):
        raise ValueError("Only GET and HEAD representations are supported")
    headers = dict(representation.headers)
    names = [v.strip() for v in headers.get("vary", "").split(",") if v.strip()]
    names += list(vary)
    unique: dict[str, str] = {}
    for name in names:
        if not isinstance(name, str) or not _TOKEN.fullmatch(name):
            raise ValueError("Invalid Vary field name")
        unique.setdefault(name.lower(), name)
    if unique:
        headers["vary"] = "*" if "*" in unique else ", ".join(unique.values())
    headers["etag"] = make_etag(representation.body)
    headers["cache-control"] = policy.mode + (f", max-age={policy.max_age}" if policy.max_age is not None else "")
    headers.pop("content-length", None)
    # Framing is owned by the server, not copied from a prior representation.
    headers.pop("transfer-encoding", None)
    headers.pop("trailer", None)
    matched = matches_if_none_match(if_none_match, headers["etag"])
    return ConditionalResponse(
        304 if matched else 200, headers, b"" if matched or method == "HEAD" else representation.body
    )
