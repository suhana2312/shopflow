import hashlib
import json
from decimal import Decimal
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.product import Product
from app.models.inventory import Inventory
from app.repositories.product_repo import ProductRepository
from app.repositories.inventory_repo import InventoryRepository
from app.schemas.product import ProductCreate, ProductUpdate, ProductFilterParams, ProductResponse
from app.core.redis import redis_client
from app.core.config import settings

class ProductService:
    def __init__(self, db: Session):
        self.db = db
        self.product_repo = ProductRepository(db)
        self.inventory_repo = InventoryRepository(db)

    def get_by_id(self, product_id: str, include_inactive: bool = False) -> Product:
        # Cache-aside for individual product
        cache_key = f"product:{product_id}"
        if not include_inactive:
            cached_data = redis_client.get_json(cache_key)
            if cached_data:
                # We can return from cache or DB; querying DB with joinedload ensures full object attributes
                pass

        product = self.product_repo.get_by_id(product_id, include_inactive=include_inactive)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "PRODUCT_NOT_FOUND", "message": f"Product with ID '{product_id}' not found."}
            )

        # Store in Redis with TTL (300s)
        try:
            prod_dict = {
                "id": product.id,
                "sku": product.sku,
                "name": product.name,
                "price": str(product.price),
                "is_active": product.is_active
            }
            redis_client.set_json(cache_key, prod_dict, ex=300)
        except Exception:
            pass

        return product

    def filter_products(self, params: ProductFilterParams) -> Tuple[List[Product], int]:
        # Generate cache key based on filter hash
        params_str = f"{params.search}:{params.category}:{params.min_price}:{params.max_price}:{params.in_stock_only}:{params.sort}:{params.page}:{params.limit}"
        hash_key = hashlib.md5(params_str.encode()).hexdigest()
        cache_key = f"products:search:{hash_key}"

        products, total = self.product_repo.filter_products(params)
        return products, total

    def create(self, req: ProductCreate) -> Product:
        existing = self.product_repo.get_by_sku(req.sku)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "SKU_ALREADY_EXISTS", "message": f"Product with SKU '{req.sku}' already exists."}
            )

        product = Product(
            sku=req.sku.upper(),
            name=req.name,
            description=req.description,
            price=req.price,
            discount_price=req.discount_price,
            category_id=req.category_id,
            brand=req.brand,
            image_url=req.image_url,
            is_active=True
        )
        created_product = self.product_repo.create(product)

        # Initialize inventory record
        inventory = Inventory(
            product_id=created_product.id,
            available_quantity=req.initial_stock,
            reserved_quantity=0,
            sold_quantity=0,
            low_stock_threshold=req.low_stock_threshold or settings.DEFAULT_LOW_STOCK_THRESHOLD
        )
        self.db.add(inventory)
        self.db.commit()

        # Invalidate product cache
        redis_client.delete_pattern("products:*")

        return self.get_by_id(created_product.id)

    def update(self, product_id: str, req: ProductUpdate) -> Product:
        product = self.get_by_id(product_id, include_inactive=True)

        if req.name is not None:
            product.name = req.name
        if req.description is not None:
            product.description = req.description
        if req.price is not None:
            product.price = req.price
        if req.discount_price is not None:
            product.discount_price = req.discount_price
        if req.category_id is not None:
            product.category_id = req.category_id
        if req.brand is not None:
            product.brand = req.brand
        if req.image_url is not None:
            product.image_url = req.image_url
        if req.is_active is not None:
            product.is_active = req.is_active

        updated = self.product_repo.update(product)

        # Invalidate cache
        redis_client.delete(f"product:{product_id}")
        redis_client.delete_pattern("products:*")

        return updated

    def deactivate(self, product_id: str) -> Product:
        product = self.get_by_id(product_id, include_inactive=True)
        product.is_active = False
        updated = self.product_repo.update(product)

        redis_client.delete(f"product:{product_id}")
        redis_client.delete_pattern("products:*")
        return updated
