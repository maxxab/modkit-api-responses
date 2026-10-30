"""Optional fixed-shape models, independent of configurable mapping envelopes."""

from typing import Any

from pydantic import BaseModel, Field


class StandardResponse[T](BaseModel):
    data: T
    meta: dict[str, Any] = Field(default_factory=dict)


class StandardError(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class StandardErrorResponse(BaseModel):
    error: StandardError
    meta: dict[str, Any] = Field(default_factory=dict)
