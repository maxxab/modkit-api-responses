import pytest

from modkit_api_responses import CachePolicy, ReadRepresentation, conditional_response, make_etag


def representation():
    return ReadRepresentation(
        b'{"value":3}',
        {
            "Content-Type": "application/json",
            "Vary": "Accept",
            "Date": "Wed, 21 Oct 2015 07:28:00 GMT",
            "Content-Location": "/things",
            "Expires": "0",
            "Content-Length": "999",
        },
    )


def test_get_and_no_store_conditional():
    rep = representation()
    result = conditional_response(rep, method="GET", if_none_match=None)
    assert result.status == 200 and result.body == rep.body
    assert result.headers["cache-control"] == "no-store"
    assert "content-length" not in result.headers
    match = conditional_response(rep, method="GET", if_none_match=make_etag(rep.body))
    assert match.status == 304 and match.body == b""
    assert match.headers["cache-control"] == "no-store"
    for key in ("date", "content-location", "expires", "vary", "etag"):
        assert key in match.headers


@pytest.mark.parametrize("match,status", [(None, 200), ("*", 304)])
def test_head(match, status):
    result = conditional_response(representation(), method="HEAD", if_none_match=match)
    assert result.status == status and result.body == b""
    assert "content-length" not in result.headers


def test_headers_ownership_and_vary():
    headers = {"Vary": "Accept, accept", "X-Thing": "ok"}
    rep = ReadRepresentation(b"x", headers)
    headers["X-Thing"] = "changed"
    result = conditional_response(
        rep, method="GET", if_none_match=None, policy=CachePolicy("private", 60), vary=["ACCEPT", "Authorization"]
    )
    assert result.headers["cache-control"] == "private, max-age=60"
    assert result.headers["vary"] == "Accept, Authorization"
    assert result.headers["x-thing"] == "ok"
    assert conditional_response(rep, method="GET", if_none_match=None, vary=["*"]).headers["vary"] == "*"
    with pytest.raises(TypeError):
        rep.headers["x"] = "y"


@pytest.mark.parametrize("mode,age", [("bogus", None), ("private", -1), ("no-store", 2), ("public", True)])
def test_invalid_policy(mode, age):
    with pytest.raises(ValueError):
        CachePolicy(mode, age)


@pytest.mark.parametrize(
    "headers,vary", [({"Bad Name": "x"}, []), ({"X": "x\r\ny"}, []), ({}, ["bad\r\n"]), ({"Vary": "bad name"}, [])]
)
def test_header_injection(headers, vary):
    with pytest.raises(ValueError):
        conditional_response(ReadRepresentation(b"x", headers), method="GET", if_none_match=None, vary=vary)


def test_unsupported_method():
    with pytest.raises(ValueError):
        conditional_response(representation(), method="POST", if_none_match="*")
