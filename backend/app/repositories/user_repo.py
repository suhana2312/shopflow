from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User, RefreshToken, UserRole

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        return self.db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()

    def create(self, user: User) -> User:
        user.email = user.email.lower()
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def list_all(self, skip: int = 0, limit: int = 50) -> List[User]:
        return list(self.db.execute(select(User).offset(skip).limit(limit)).scalars().all())

    def count_total(self) -> int:
        from sqlalchemy import func
        return self.db.execute(select(func.count(User.id))).scalar() or 0

    def add_refresh_token(self, refresh_token: RefreshToken) -> RefreshToken:
        self.db.add(refresh_token)
        self.db.commit()
        return refresh_token

    def get_refresh_token(self, token_hash: str) -> Optional[RefreshToken]:
        return self.db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        ).scalar_one_or_none()

    def revoke_refresh_token(self, token_hash: str) -> bool:
        rt = self.get_refresh_token(token_hash)
        if rt:
            rt.revoked = True
            self.db.commit()
            return True
        return False

    def revoke_all_user_tokens(self, user_id: str):
        tokens = self.db.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id, RefreshToken.revoked == False)
        ).scalars().all()
        for t in tokens:
            t.revoked = True
        self.db.commit()
