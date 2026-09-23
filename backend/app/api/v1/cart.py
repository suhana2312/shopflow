from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.cart_service import CartService
from app.schemas.cart import CartResponse, CartItemCreate, CartItemUpdate
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.get("", response_model=ApiResponse[CartResponse])
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve current user's cart with server-calculated subtotal."""
    service = CartService(db)
    cart = service.get_user_cart(current_user.id)
    return ApiResponse(data=cart)

@router.post("/items", response_model=ApiResponse[CartResponse], status_code=status.HTTP_201_CREATED)
def add_item_to_cart(
    req: CartItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add product to cart.
    NOTE: Adding an item to the cart does NOT reserve inventory.
    """
    service = CartService(db)
    cart = service.add_to_cart(current_user.id, req.product_id, req.quantity)
    return ApiResponse(data=cart, message="Item added to cart.")

@router.patch("/items/{item_id}", response_model=ApiResponse[CartResponse])
def update_cart_item(
    item_id: str,
    req: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update quantity of an existing cart item."""
    service = CartService(db)
    cart = service.update_item_quantity(current_user.id, item_id, req.quantity)
    return ApiResponse(data=cart, message="Cart item quantity updated.")

@router.delete("/items/{item_id}", response_model=ApiResponse[CartResponse])
def remove_cart_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove item from user's cart."""
    service = CartService(db)
    cart = service.remove_item(current_user.id, item_id)
    return ApiResponse(data=cart, message="Cart item removed.")

@router.delete("", response_model=ApiResponse[CartResponse])
def clear_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear all items from user's cart."""
    service = CartService(db)
    cart = service.clear_cart(current_user.id)
    return ApiResponse(data=cart, message="Cart emptied successfully.")
