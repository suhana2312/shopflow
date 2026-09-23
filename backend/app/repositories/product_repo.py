from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, func, and_, or_
from app.models.product import Product
from app.models.category import Category
from app.models.inventory import Inventory
from app.schemas.product import ProductFilterParams

class ProductRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, product_id: str, include_inactive: bool = False) -> Optional[Product]:
        query = (
            select(Product)
            .options(joinedload(Product.category), joinedload(Product.inventory))
            .where(Product.id == product_id)
        )
        if not include_inactive:
            query = query.where(Product.is_active == True)
        return self.db.execute(query).unique().scalar_one_or_none()

    def get_by_sku(self, sku: str) -> Optional[Product]:
        return self.db.execute(
            select(Product).where(Product.sku == sku.upper())
        ).scalar_one_or_none()

    def filter_products(self, params: ProductFilterParams) -> Tuple[List[Product], int]:
        query = (
            select(Product)
            .options(joinedload(Product.category), joinedload(Product.inventory))
            .join(Product.inventory)
        )
        count_query = select(func.count(Product.id)).join(Product.inventory)

        filters = [Product.is_active == True]

        if params.search:
            pattern = f"%{params.search.strip()}%"
            search_filter = or_(
                Product.name.ilike(pattern),
                Product.description.ilike(pattern),
                Product.brand.ilike(pattern),
                Product.sku.ilike(pattern)
            )
            filters.append(search_filter)

        if params.category:
            # Check by category ID or slug
            filters.append(
                or_(
                    Product.category_id == params.category,
                    Product.category.has(Category.slug == params.category)
                )
            )

        if params.min_price is not None:
            filters.append(Product.price >= params.min_price)

        if params.max_price is not None:
            filters.append(Product.price <= params.max_price)

        if params.in_stock_only:
            filters.append(Inventory.available_quantity > 0)

        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

        # Sorting
        if params.sort == "price_asc":
            query = query.order_by(Product.price.asc())
        elif params.sort == "price_desc":
            query = query.order_by(Product.price.desc())
        elif params.sort == "name_asc":
            query = query.order_by(Product.name.asc())
        else:
            query = query.order_by(Product.created_at.desc())

        # Total count
        total = self.db.execute(count_query).scalar() or 0

        # Pagination
        offset = (params.page - 1) * params.limit
        query = query.offset(offset).limit(params.limit)

        products = list(self.db.execute(query).unique().scalars().all())
        return products, total

    def create(self, product: Product) -> Product:
        product.sku = product.sku.upper()
        self.db.add(product)
        self.db.commit()
        self.db.refresh(product)
        return product

    def update(self, product: Product) -> Product:
        self.db.commit()
        self.db.refresh(product)
        return product

    def count_total(self) -> int:
        return self.db.execute(select(func.count(Product.id))).scalar() or 0
