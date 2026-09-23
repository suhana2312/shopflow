from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import require_admin
from app.models.user import User
from app.services.category_service import CategoryService
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("", response_model=ApiResponse[List[CategoryResponse]])
def list_categories(include_inactive: bool = False, db: Session = Depends(get_db)):
    """Retrieve all active product categories."""
    service = CategoryService(db)
    cats = service.list_categories(include_inactive=include_inactive)
    return ApiResponse(data=[CategoryResponse.model_validate(c) for c in cats])

@router.get("/{category_id}", response_model=ApiResponse[CategoryResponse])
def get_category(category_id: str, db: Session = Depends(get_db)):
    """Retrieve category details by ID."""
    service = CategoryService(db)
    cat = service.get_by_id(category_id)
    return ApiResponse(data=CategoryResponse.model_validate(cat))

@router.post("", response_model=ApiResponse[CategoryResponse], status_code=status.HTTP_201_CREATED)
def create_category(
    req: CategoryCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: create a new product category."""
    service = CategoryService(db)
    cat = service.create(req)
    return ApiResponse(data=CategoryResponse.model_validate(cat), message="Category created successfully.")

@router.patch("/{category_id}", response_model=ApiResponse[CategoryResponse])
def update_category(
    category_id: str,
    req: CategoryUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: update category details."""
    service = CategoryService(db)
    cat = service.update(category_id, req)
    return ApiResponse(data=CategoryResponse.model_validate(cat), message="Category updated successfully.")

@router.delete("/{category_id}", response_model=ApiResponse[CategoryResponse])
def deactivate_category(
    category_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: safely deactivate category without breaking historical order references."""
    service = CategoryService(db)
    cat = service.deactivate(category_id)
    return ApiResponse(data=CategoryResponse.model_validate(cat), message="Category deactivated successfully.")
