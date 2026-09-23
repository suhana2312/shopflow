from typing import List, Optional
from pydantic import BaseModel
from app.schemas.product import ProductResponse

class RecommendationItem(BaseModel):
    product: ProductResponse
    score: float
    reason: str

class RecommendationResponse(BaseModel):
    recommendations: List[RecommendationItem] = []
    strategy_used: str = "hybrid_affinity_collaborative"
