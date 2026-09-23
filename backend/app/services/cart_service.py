from decimal import Decimal
from typing import Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.repositories.cart_repo import CartRepository
from app.repositories.product_repo import ProductRepository
from app.schemas.cart import CartResponse, CartItemResponse
from app.schemas.product import ProductResponse

class CartService:
    def __init__(self, db: Session):
        self.db = db
        self.cart_repo = CartRepository(db)
        self.product_repo = ProductRepository(db)

    def get_user_cart(self, user_id: str) -> CartResponse:
        cart = self.cart_repo.get_with_items(user_id)
        
        items_response = []
        total_items = 0
        subtotal = Decimal("0.00")

        for item in cart.items:
            unit_price = item.product.discount_price if item.product.discount_price is not None else item.product.price
            item_subtotal = Decimal(str(unit_price)) * item.quantity
            subtotal += item_subtotal
            total_items += item.quantity

            items_response.append(
                CartItemResponse(
                    id=item.id,
                    cart_id=item.cart_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    product=ProductResponse.model_validate(item.product) if item.product else None,
                    subtotal=item_subtotal
                )
            )

        return CartResponse(
            id=cart.id,
            user_id=cart.user_id,
            items=items_response,
            total_items=total_items,
            subtotal=subtotal
        )

    def add_to_cart(self, user_id: str, product_id: str, quantity: int) -> CartResponse:
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_QUANTITY", "message": "Quantity must be greater than 0"}
            )

        product = self.product_repo.get_by_id(product_id)
        if not product or not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PRODUCT_NOT_FOUND", "message": "Product is not available or inactive."}
            )

        cart = self.cart_repo.get_or_create(user_id)
        
        # NOTE: Inventory is deliberately NOT reserved at this stage.
        # It is reserved strictly during the atomic checkout transaction.
        self.cart_repo.add_or_update_item(cart.id, product_id, quantity)
        return self.get_user_cart(user_id)

    def update_item_quantity(self, user_id: str, item_id: str, quantity: int) -> CartResponse:
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": "INVALID_QUANTITY", "message": "Quantity must be greater than 0"}
            )

        item = self.cart_repo.get_cart_item(item_id)
        if not item or item.cart.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CART_ITEM_NOT_FOUND", "message": "Cart item not found or unauthorized"}
            )

        self.cart_repo.update_quantity(item_id, quantity)
        return self.get_user_cart(user_id)

    def remove_item(self, user_id: str, item_id: str) -> CartResponse:
        item = self.cart_repo.get_cart_item(item_id)
        if not item or item.cart.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CART_ITEM_NOT_FOUND", "message": "Cart item not found or unauthorized"}
            )

        self.cart_repo.remove_item(item_id)
        return self.get_user_cart(user_id)

    def clear_cart(self, user_id: str) -> CartResponse:
        cart = self.cart_repo.get_or_create(user_id)
        self.cart_repo.clear_cart(cart.id)
        self.db.commit()
        return self.get_user_cart(user_id)
