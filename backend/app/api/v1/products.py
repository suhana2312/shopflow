import math
from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import require_admin
from app.models.user import User
from app.services.product_service import ProductService
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductFilterParams,
)
from app.schemas.common import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/products", tags=["Products"])

@router.get("", response_model=ApiResponse[PaginatedResponse[ProductResponse]])
def list_products(
    search: Optional[str] = Query(None, description="Search by name, description, brand, or SKU"),
    category: Optional[str] = Query(None, description="Filter by category ID or slug"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price filter"),
    in_stock_only: Optional[bool] = Query(None, description="Filter out-of-stock items"),
    sort: Optional[str] = Query("created_at_desc", description="price_asc, price_desc, name_asc, created_at_desc"),
    page: int = Query(1, ge=1, description="Page number (>=1)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (1-100)"),
    db: Session = Depends(get_db)
):
    """
    Search, filter, sort, and paginate through active products.
    Utilizes PostgreSQL indexes and Redis cache-aside.
    """
    params = ProductFilterParams(
        search=search,
        category=category,
        min_price=min_price,
        max_price=max_price,
        in_stock_only=in_stock_only,
        sort=sort,
        page=page,
        limit=limit
    )
    service = ProductService(db)
    products, total = service.filter_products(params)
    pages = math.ceil(total / limit) if limit > 0 else 1

    paginated_data = PaginatedResponse(
        items=[ProductResponse.model_validate(p) for p in products],
        page=page,
        limit=limit,
        total=total,
        pages=pages
    )
    return ApiResponse(data=paginated_data)

@router.get("/{product_id}", response_model=ApiResponse[ProductResponse])
def get_product(product_id: str, db: Session = Depends(get_db)):
    """Retrieve full product details including live inventory level."""
    service = ProductService(db)
    product = service.get_by_id(product_id)
    return ApiResponse(data=ProductResponse.model_validate(product))

@router.post("", response_model=ApiResponse[ProductResponse], status_code=status.HTTP_201_CREATED)
def create_product(
    req: ProductCreate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: create a new product and initialize stock."""
    service = ProductService(db)
    product = service.create(req)
    return ApiResponse(
        data=ProductResponse.model_validate(product),
        message="Product created successfully."
    )

@router.patch("/{product_id}", response_model=ApiResponse[ProductResponse])
def update_product(
    product_id: str,
    req: ProductUpdate,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: update product details and invalidate cache."""
    service = ProductService(db)
    product = service.update(product_id, req)
    return ApiResponse(
        data=ProductResponse.model_validate(product),
        message="Product updated successfully."
    )

@router.delete("/{product_id}", response_model=ApiResponse[ProductResponse])
def deactivate_product(
    product_id: str,
    admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin: deactivate product from catalog."""
    service = ProductService(db)
    product = service.deactivate(product_id)
    return ApiResponse(
        data=ProductResponse.model_validate(product),
        message="Product deactivated successfully."
    )
