from fastapi import HTTPException
from sqlalchemy.orm import Session

from src.core.auth_manager import PasswordManager
from src.models import User
from src.repositories.user import UserRepository


class UserService:
    def __init__(self, session: Session) -> None:
        self.repository = UserRepository(session=session)

    def signup(self, email: str, password: str) -> User:
        user = self.repository.filter([User.email == email])
        if user:
            raise HTTPException(status_code=409, detail="User already exists")

        hashed_password = PasswordManager.get_password_hash(password)
        return self.repository.create(
            **{"email": email, "hashed_password": hashed_password, "is_active": True}
        )

    def login(self, email: str, password: str) -> User:
        user = self.repository.filter([User.email == email], first_only=True)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email")

        if not PasswordManager.verify(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid password")

        return user
