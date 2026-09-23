from typing import List, Protocol, Optional, Set
from sqlalchemy.orm import Session
from sqlalchemy import select, func, desc
from app.models.product import Product
from app.models.orders import Order, OrderItem
from app.models.cart import Cart, CartItem
from app.models.inventory import Inventory
from app.schemas.recommendation import RecommendationItem, RecommendationResponse
from app.schemas.product import ProductResponse

class RecommendationStrategy(Protocol):
    def get_recommendations(self, db: Session, user_id: Optional[str], limit: int) -> List[RecommendationItem]:
        ...

class HybridAffinityRecommendationEngine:
    """
    Production-style recommendation algorithm combining multiple signals:
    1. Past purchase category affinity
    2. Items frequently bought together (co-occurrence in historical order_items)
    3. Active cart affinity
    4. Popularity fallback (most sold products) for cold-start users
    """
    def get_recommendations(self, db: Session, user_id: Optional[str], limit: int = 6) -> List[RecommendationItem]:
        recommendations: List[RecommendationItem] = []
        seen_product_ids: Set[str] = set()

        if user_id:
            # 1. Gather products and categories from user's historical orders
            user_order_items = db.execute(
                select(OrderItem.product_id, Product.category_id)
                .join(Product, OrderItem.product_id == Product.id)
                .join(Order, OrderItem.order_id == Order.id)
                .where(Order.user_id == user_id)
            ).all()

            user_purchased_ids = {row[0] for row in user_order_items if row[0]}
            user_categories = {row[1] for row in user_order_items if row[1]}
            seen_product_ids.update(user_purchased_ids)

            # 2. Frequently Bought Together (Co-occurrence)
            if user_purchased_ids:
                co_occurring = db.execute(
                    select(OrderItem.product_id, func.count(OrderItem.order_id).label("freq"))
                    .where(
                        OrderItem.order_id.in_(
                            select(OrderItem.order_id).where(OrderItem.product_id.in_(user_purchased_ids))
                        ),
                        ~OrderItem.product_id.in_(seen_product_ids)
                    )
                    .group_by(OrderItem.product_id)
                    .order_by(desc("freq"))
                    .limit(3)
                ).all()

                for prod_id, freq in co_occurring:
                    prod = db.execute(select(Product).where(Product.id == prod_id, Product.is_active == True)).scalar_one_or_none()
                    if prod and prod.id not in seen_product_ids:
                        seen_product_ids.add(prod.id)
                        recommendations.append(
                            RecommendationItem(
                                product=ProductResponse.model_validate(prod),
                                score=round(0.85 + (min(freq, 10) * 0.01), 2),
                                reason="Frequently bought together with items from your order history"
                            )
                        )

            # 3. Category Affinity: Products in the same categories
            if user_categories and len(recommendations) < limit:
                needed = limit - len(recommendations)
                cat_products = db.execute(
                    select(Product)
                    .join(Inventory, Product.id == Inventory.product_id)
                    .where(
                        Product.category_id.in_(user_categories),
                        Product.is_active == True,
                        ~Product.id.in_(seen_product_ids),
                        Inventory.available_quantity > 0
                    )
                    .order_by(desc(Inventory.sold_quantity))
                    .limit(needed)
                ).scalars().all()

                for prod in cat_products:
                    if prod.id not in seen_product_ids:
                        seen_product_ids.add(prod.id)
                        recommendations.append(
                            RecommendationItem(
                                product=ProductResponse.model_validate(prod),
                                score=0.75,
                                reason=f"Popular in categories you love ({prod.category.name if prod.category else 'Tech'})"
                            )
                        )

        # 4. Cold-Start / Popularity Fallback
        if len(recommendations) < limit:
            needed = limit - len(recommendations)
            top_sellers = db.execute(
                select(Product)
                .join(Inventory, Product.id == Inventory.product_id)
                .where(
                    Product.is_active == True,
                    ~Product.id.in_(seen_product_ids),
                    Inventory.available_quantity > 0
                )
                .order_by(desc(Inventory.sold_quantity), desc(Product.created_at))
                .limit(needed)
            ).scalars().all()

            for prod in top_sellers:
                if prod.id not in seen_product_ids:
                    seen_product_ids.add(prod.id)
                    recommendations.append(
                        RecommendationItem(
                            product=ProductResponse.model_validate(prod),
                            score=0.60,
                            reason="Trending & top-selling product"
                        )
                    )

        return recommendations[:limit]

class RecommendationService:
    def __init__(self, db: Session, engine: Optional[RecommendationStrategy] = None):
        self.db = db
        self.engine = engine or HybridAffinityRecommendationEngine()

    def get_recommendations_for_user(self, user_id: Optional[str] = None, limit: int = 6) -> RecommendationResponse:
        items = self.engine.get_recommendations(self.db, user_id, limit)
        return RecommendationResponse(
            recommendations=items,
            strategy_used="hybrid_affinity_collaborative"
        )
