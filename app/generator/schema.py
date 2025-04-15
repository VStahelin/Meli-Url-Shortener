from typing import Generic, TypeVar, Optional
from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


class StandardResponse(GenericModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str


class GeneratorRequest(BaseModel):
    url: str


class RouteStats(BaseModel):
    route: str
    avg_response_time_ms: float
    requests_per_second: float
    total_requests_last_minute: int
    total_requests: int
    total_response_time_ms: float


class ShortenedURLResponse(BaseModel):
    url: str


class DeleteURLResponse(BaseModel):
    message: str
