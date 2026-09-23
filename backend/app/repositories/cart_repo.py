from typing import Optional, List
from decimal import Decimal
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select
from app.models.cart import Cart, CartItem
from app.models.product import Product

class CartRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, user_id: str) -> Cart:
        cart = self.db.execute(
            select(Cart).where(Cart.user_id == user_id)
        ).scalar_one_or_none()
        if not cart:
            cart = Cart(user_id=user_id)
            self.db.add(cart)
            self.db.commit()
            self.db.refresh(cart)
        return cart

    def get_with_items(self, user_id: str) -> Cart:
        cart = self.db.execute(
            select(Cart)
            .options(
                joinedload(Cart.items).joinedload(CartItem.product).joinedload(Product.inventory)
            )
            .where(Cart.user_id == user_id)
        ).unique().scalar_one_or_none()

        if not cart:
            cart = self.get_or_create(user_id)
        return cart

    def get_cart_item(self, item_id: str) -> Optional[CartItem]:
        return self.db.execute(
            select(CartItem).options(joinedload(CartItem.cart)).where(CartItem.id == item_id)
        ).scalar_one_or_none()

    def add_or_update_item(self, cart_id: str, product_id: str, quantity: int) -> CartItem:
        item = self.db.execute(
            select(CartItem).where(
                CartItem.cart_id == cart_id,
                CartItem.product_id == product_id
            )
        ).scalar_one_or_none()

        if item:
            item.quantity += quantity
        else:
            item = CartItem(cart_id=cart_id, product_id=product_id, quantity=quantity)
            self.db.add(item)

        self.db.commit()
        self.db.refresh(item)
        return item

    def update_quantity(self, item_id: str, quantity: int) -> Optional[CartItem]:
        item = self.get_cart_item(item_id)
        if item:
            item.quantity = quantity
            self.db.commit()
            self.db.refresh(item)
        return item

    def remove_item(self, item_id: str) -> bool:
        item = self.get_cart_item(item_id)
        if item:
            self.db.delete(item)
            self.db.commit()
            return True
        return False

    def clear_cart(self, cart_id: str):
        items = self.db.execute(
            select(CartItem).where(CartItem.cart_id == cart_id)
        ).scalars().all()
        for it in items:
            self.db.delete(it)
        self.db.flush()
