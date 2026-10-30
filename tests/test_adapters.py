import asyncio
import json
from datetime import UTC, datetime

from fastapi import FastAPI, Request, Response
from fastapi.testclient import TestClient
from pydantic import BaseModel

from modkit_api_responses import ReadRepresentation, conditional_response, make_etag, strip_fields, success
from modkit_api_responses.adapters.fastapi import encode_data, to_response
from modkit_api_responses.adapters.pydantic import StandardError, StandardErrorResponse, StandardResponse


def test_models_encoding_and_explicit_filtering():
    class Item(BaseModel):
        name: str
        secret: str
        created: datetime

    encoded = encode_data(Item(name="sample", secret="hidden", created=datetime(2026, 1, 1, tzinfo=UTC)))
    assert strip_fields(encoded, names={"secret"}) == {"name": "sample", "created": "2026-01-01T00:00:00Z"}
    first = StandardResponse(data=3)
    first.meta["x"] = 1
    assert StandardResponse(data=4).meta == {}
    assert StandardErrorResponse(error=StandardError(code="X", message="no")).model_dump() == {
        "error": {"code": "X", "message": "no", "details": None},
        "meta": {},
    }
    assert encode_data({"camelCase": 3}) == {"camelCase": 3}


def test_raw_asgi_head_and_304():
    async def run(method, header):
        result = conditional_response(ReadRepresentation(b"nonempty"), method=method, if_none_match=header)
        response = to_response(result)
        sent = []

        async def receive():
            return {"type": "http.request", "body": b""}

        async def send(message):
            sent.append(message)

        await response({"type": "http", "method": method}, receive, send)
        assert b"".join(m.get("body", b"") for m in sent) == b""
        assert b"content-length" not in dict(sent[0]["headers"])

    for method, header in [("HEAD", None), ("HEAD", "*"), ("GET", "*")]:
        asyncio.run(run(method, header))


def test_get_wire_bytes_unchanged():
    body = b'{"unicode":"\\u00e9"}'
    response = to_response(conditional_response(ReadRepresentation(body), method="GET", if_none_match=None))
    assert response.body == body and response.headers["etag"] == make_etag(body)


def test_application_boundary():
    app = FastAPI()
    body = json.dumps(success({"name": "unrelated garden"})).encode()
    tag = make_etag(body)

    @app.get("/garden", response_model=None, operation_id="get_garden")
    @app.head("/garden", response_model=None, operation_id="head_garden")
    def garden(request: Request):
        if request.headers.get("authorization") != "example":
            return Response(status_code=401)
        # This sample handles its one supported strong If-Match value explicitly.
        if request.headers.get("if-match") not in (None, tag):
            return Response(status_code=412)
        return to_response(
            conditional_response(
                ReadRepresentation(body, {"Content-Type": "application/json"}),
                method=request.method,
                if_none_match=request.headers.get("if-none-match"),
            )
        )

    @app.get("/ordinary")
    def ordinary():
        return {"unchanged": True}

    with TestClient(app) as client:
        assert client.get("/garden", headers={"if-none-match": "*"}).status_code == 401
        auth = {"authorization": "example"}
        assert client.get("/garden", headers={**auth, "if-match": "bad", "if-none-match": "*"}).status_code == 412
        result = client.get("/garden", headers={**auth, "if-none-match": tag, "if-modified-since": "invalid"})
        assert result.status_code == 304 and not result.content
        assert client.head("/garden", headers=auth).content == b""
        assert client.get("/garden", headers=auth).content == body
        assert client.get("/ordinary").json() == {"unchanged": True}
        assert "/garden" in client.get("/openapi.json").json()["paths"]
