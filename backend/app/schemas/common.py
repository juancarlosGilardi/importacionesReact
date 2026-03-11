from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    data: list[T]
    total: int
    page: int
    per_page: int


class MessageResponse(BaseModel):
    message: str
    id: int | None = None
