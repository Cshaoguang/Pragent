from math import ceil
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: str = "0"
    message: str = "success"
    data: T | None = None


class PageResponse(BaseModel, Generic[T]):
    records: list[T] = Field(default_factory=list)
    total: int = 0
    size: int = 10
    current: int = 1
    pages: int = 0


def success(data: T | None = None, message: str = "success") -> ApiResponse[T]:
    return ApiResponse(code="0", message=message, data=data)


def page(records: list[Any], total: int, current: int, size: int) -> PageResponse[Any]:
    return PageResponse(
        records=records,
        total=total,
        current=current,
        size=size,
        pages=ceil(total / size) if size else 0,
    )
