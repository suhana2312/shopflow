from typing import Optional
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.rate_limiter import auth_rate_limiter
from app.services.auth_service import AuthService
from app.schemas.user import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    UserResponse
)
from app.schemas.common import ApiResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post(
    "/register",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth_rate_limiter)]
)
def register(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new customer or admin user account."""
    service = AuthService(db)
    user = service.register(req)
    return ApiResponse(
        data=UserResponse.model_validate(user),
        message="User successfully registered."
    )

@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    dependencies=[Depends(auth_rate_limiter)]
)
def login(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate credentials and obtain JWT access + refresh tokens."""
    service = AuthService(db)
    tokens = service.login(req)
    return ApiResponse(
        data=tokens,
        message="Authentication successful."
    )

@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse]
)
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Rotate refresh token and retrieve a fresh JWT access token."""
    service = AuthService(db)
    tokens = service.refresh(req.refresh_token)
    return ApiResponse(
        data=tokens,
        message="Tokens refreshed successfully."
    )

@router.post("/logout", response_model=ApiResponse[None])
def logout(
    req: Optional[RefreshTokenRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Revoke refresh token and log out the user."""
    service = AuthService(db)
    raw_token = req.refresh_token if req else None
    service.logout(current_user.id, raw_token)
    return ApiResponse(message="Successfully logged out.")

@router.get("/me", response_model=ApiResponse[UserResponse])
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Retrieve currently authenticated user profile."""
    return ApiResponse(data=UserResponse.model_validate(current_user))
