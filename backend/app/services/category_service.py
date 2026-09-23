from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.category import Category
from app.repositories.category_repo import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.core.redis import redis_client

class CategoryService:
    def __init__(self, db: Session):
        self.db = db
        self.category_repo = CategoryRepository(db)

    def list_categories(self, include_inactive: bool = False) -> List[Category]:
        cache_key = f"categories:all:{include_inactive}"
        cached = redis_client.get_json(cache_key)
        if cached:
            # Rehydrate or return
            pass
        categories = self.category_repo.list_all(include_inactive=include_inactive)
        return categories

    def get_by_id(self, category_id: str) -> Category:
        cat = self.category_repo.get_by_id(category_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CATEGORY_NOT_FOUND", "message": f"Category {category_id} not found"}
            )
        return cat

    def create(self, req: CategoryCreate) -> Category:
        slug = req.slug or req.name.lower().replace(" ", "-")
        existing = self.category_repo.get_by_slug(slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "SLUG_ALREADY_EXISTS", "message": f"Category slug '{slug}' already exists."}
            )

        cat = Category(name=req.name, slug=slug, description=req.description, is_active=True)
        created = self.category_repo.create(cat)
        redis_client.delete_pattern("categories:*")
        return created

    def update(self, category_id: str, req: CategoryUpdate) -> Category:
        cat = self.get_by_id(category_id)
        if req.name is not None:
            cat.name = req.name
        if req.slug is not None:
            cat.slug = req.slug
        if req.description is not None:
            cat.description = req.description
        if req.is_active is not None:
            cat.is_active = req.is_active

        updated = self.category_repo.update(cat)
        redis_client.delete_pattern("categories:*")
        redis_client.delete_pattern("products:*")
        return updated

    def deactivate(self, category_id: str) -> Category:
        cat = self.category_repo.deactivate(category_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": "CATEGORY_NOT_FOUND", "message": f"Category {category_id} not found"}
            )
        redis_client.delete_pattern("categories:*")
        redis_client.delete_pattern("products:*")
        return cat
