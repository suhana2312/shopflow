from typing import Generic, TypeVar, Optional, List, Any, Dict
from pydantic import BaseModel, Field

T = TypeVar("T")

class ApiErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = "Operation completed successfully"
    data: Optional[T] = None
    error: Optional[ApiErrorDetail] = None
    request_id: Optional[str] = None

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    page: int
    limit: int
    total: int
    pages: int
