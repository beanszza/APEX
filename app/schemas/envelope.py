"""Generic API Response Envelope."""

from typing import Generic, TypeVar, Any
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation completed successfully."
    data: T | None = None

    @classmethod
    def success_response(cls, data: T, message: str = "Success") -> "ApiResponse[T]":
        return cls(success=True, message=message, data=data)

    @classmethod
    def failure_response(cls, message: str) -> "ApiResponse[Any]":
        return ApiResponse[Any](success=False, message=message, data=None)
