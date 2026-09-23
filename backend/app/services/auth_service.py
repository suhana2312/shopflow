from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User, RefreshToken, UserRole
from app.repositories.user_repo import UserRepository
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    hash_token
)
from app.core.config import settings
from app.schemas.user import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse

class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)

    def register(self, req: UserRegisterRequest) -> User:
        existing = self.user_repo.get_by_email(req.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "code": "EMAIL_ALREADY_EXISTS",
                    "message": f"User with email '{req.email}' already registered."
                }
            )

        user = User(
            email=req.email.lower(),
            hashed_password=get_password_hash(req.password),
            full_name=req.full_name,
            role=req.role or UserRole.CUSTOMER,
            is_active=True
        )
        return self.user_repo.create(user)

    def login(self, req: UserLoginRequest) -> TokenResponse:
        user = self.user_repo.get_by_email(req.email)
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_CREDENTIALS",
                    "message": "Invalid email or password."
                }
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "ACCOUNT_DISABLED",
                    "message": "This account is inactive. Please contact support."
                }
            )

        access_token = create_access_token(subject=user.id, role=user.role.value)
        raw_refresh_token = create_refresh_token(subject=user.id)
        
        # Persist hashed refresh token
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        token_entry = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(raw_refresh_token),
            expires_at=expires_at,
            revoked=False
        )
        self.user_repo.add_refresh_token(token_entry)

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )

    def refresh(self, raw_refresh_token: str) -> TokenResponse:
        token_h = hash_token(raw_refresh_token)
        stored_token = self.user_repo.get_refresh_token(token_h)

        if not stored_token or stored_token.revoked:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "INVALID_REFRESH_TOKEN",
                    "message": "Refresh token is invalid or has been revoked."
                }
            )

        if stored_token.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "EXPIRED_REFRESH_TOKEN",
                    "message": "Refresh token has expired. Please log in again."
                }
            )

        user = self.user_repo.get_by_id(stored_token.user_id)
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "USER_NOT_FOUND", "message": "User not found or disabled."}
            )

        # Rotate refresh token: revoke old token
        stored_token.revoked = True
        self.db.commit()

        # Issue new token pair
        new_access_token = create_access_token(subject=user.id, role=user.role.value)
        new_raw_refresh = create_refresh_token(subject=user.id)
        new_expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        new_entry = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(new_raw_refresh),
            expires_at=new_expires_at,
            revoked=False
        )
        self.user_repo.add_refresh_token(new_entry)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_raw_refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserResponse.model_validate(user)
        )

    def logout(self, user_id: str, raw_refresh_token: Optional[str] = None):
        if raw_refresh_token:
            token_h = hash_token(raw_refresh_token)
            self.user_repo.revoke_refresh_token(token_h)
        else:
            self.user_repo.revoke_all_user_tokens(user_id)
