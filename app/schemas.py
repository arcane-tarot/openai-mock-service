from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ResponseRequest(BaseModel):
    model_config = ConfigDict(extra="allow")

    model: str = Field(min_length=1, max_length=200)
    input: str | list[dict[str, Any]]
    stream: bool = False


class ErrorDetail(BaseModel):
    message: str
    type: str
    param: str | None = None
    code: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
