from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.category import Category

class CategoryRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, category_id: str) -> Optional[Category]:
        return self.db.execute(select(Category).where(Category.id == category_id)).scalar_one_or_none()

    def get_by_slug(self, slug: str) -> Optional[Category]:
        return self.db.execute(select(Category).where(Category.slug == slug)).scalar_one_or_none()

    def list_all(self, include_inactive: bool = False) -> List[Category]:
        query = select(Category)
        if not include_inactive:
            query = query.where(Category.is_active == True)
        return list(self.db.execute(query.order_by(Category.name.asc())).scalars().all())

    def create(self, category: Category) -> Category:
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(self, category: Category) -> Category:
        self.db.commit()
        self.db.refresh(category)
        return category

    def deactivate(self, category_id: str) -> Optional[Category]:
        cat = self.get_by_id(category_id)
        if cat:
            cat.is_active = False
            self.db.commit()
            self.db.refresh(cat)
        return cat
