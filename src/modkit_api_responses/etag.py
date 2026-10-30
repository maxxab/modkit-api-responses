"""Final-byte validators and bounded RFC 9110 If-None-Match parsing."""

import hashlib
import re

_TAG = re.compile(r'(?:W/)?"[\x21\x23-\x7e\x80-\xff]*"')


def make_etag(body: bytes) -> str:
    if not isinstance(body, bytes):
        raise TypeError("ETag input must be finalized bytes")
    return '"' + hashlib.sha256(body).hexdigest() + '"'


def matches_if_none_match(
    header: str | None,
    etag: str,
    *,
    representation_exists: bool = True,
    max_header_bytes: int = 8192,
    max_tags: int = 128,
) -> bool:
    """Malformed fields are ignored entirely; resource-limit excess raises ValueError.

    Combine duplicate field lines with commas before calling. This is weak
    comparison for conditional reads, not a full precondition evaluator.
    """
    if any(type(n) is not int or n < 1 for n in (max_header_bytes, max_tags)):
        raise ValueError("Parser bounds must be positive integers")
    if not isinstance(etag, str) or not _TAG.fullmatch(etag):
        raise ValueError("Invalid selected representation tag")
    if header is None:
        return False
    if not isinstance(header, str):
        raise TypeError("Conditional field must be a string")
    if len(header) > max_header_bytes or len(header.encode("utf-8")) > max_header_bytes:
        raise ValueError("Conditional field exceeds byte bound")
    text = header.strip(" \t")
    if text == "*":
        return representation_exists
    tags = []
    index = 0
    while index < len(text):
        if text[index] in " \t,":
            index += 1
            continue
        match = _TAG.match(text, index)
        if not match:
            return False
        tags.append(match.group().removeprefix("W/"))
        if len(tags) > max_tags:
            raise ValueError("Conditional field exceeds tag bound")
        index = match.end()
        while index < len(text) and text[index] in " \t":
            index += 1
        if index < len(text) and text[index] != ",":
            return False
    return representation_exists and etag.removeprefix("W/") in tags
