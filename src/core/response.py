from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ErrorDetail | None = None


def success_response(data: Any = None) -> dict:
    return {"success": True, "data": data, "error": None}


def error_response(code: str, message: str, status_code: int = 400) -> dict:
    """에러 응답 생성. HTTPException과 함께 사용."""
    return {"success": False, "data": None, "error": {"code": code, "message": message}}
