"""Explicit encoding and raw responses; no implicit model filtering."""

from fastapi.encoders import jsonable_encoder
from starlette.responses import Response

from ..cache import ConditionalResponse


def encode_data(value: object) -> object:
    """Encode framework-supported values; does not rename arbitrary keys."""
    return jsonable_encoder(value)


def to_response(result: ConditionalResponse) -> Response:
    """Emit finalized bytes without JSON reserialization or added length guesses."""
    response = Response(content=result.body, status_code=result.status, headers=dict(result.headers))
    if "content-length" not in result.headers:
        # Starlette infers zero from an empty HEAD response; hypothetical GET
        # length is unknown here, so omission is preferable to a false zero.
        del response.headers["content-length"]
    return response
