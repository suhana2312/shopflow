from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_optional_user
from app.models.user import User
from app.services.recommendation_service import RecommendationService
from app.schemas.recommendation import RecommendationResponse
from app.schemas.common import ApiResponse

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("", response_model=ApiResponse[RecommendationResponse])
def get_recommendations(
    limit: int = Query(6, ge=1, le=20),
    current_user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    AI/Heuristic product recommendation endpoint:
    - Logged-in customers: Multi-signal heuristic based on purchase history, co-occurrence, and category affinity
    - Guests: Top trending products by sales velocity
    """
    service = RecommendationService(db)
    user_id = current_user.id if current_user else None
    result = service.get_recommendations_for_user(user_id=user_id, limit=limit)
    return ApiResponse(data=result)
