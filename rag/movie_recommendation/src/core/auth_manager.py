from datetime import datetime, timedelta, timezone
from typing import Tuple

from fastapi import HTTPException, Request, Response
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy.orm import Session
from src.models import User
from src.repositories.user import UserRepository
from src.schemas import Token, TokenPayload
from src.settings.settings import settings


class PasswordManager:
    context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @classmethod
    def verify(cls, password: str, hashed_password: str) -> bool:
        return cls.context.verify(password, hashed_password)

    @classmethod
    def get_password_hash(cls, password: str) -> str:
        return cls.context.hash(password)


class AuthManager:
    algorithm = "HS256"
    cookie_name = "access-token"
    header_name = "Authorization"
    credentials_exception = HTTPException(
        status_code=401,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    accept_cookie = settings.AcceptCookie
    accept_header = settings.AcceptToken

    @classmethod
    def create_access_token(
        cls, user_id: str, expires_delta: timedelta | None = None
    ) -> Tuple[str, datetime]:
        expires = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=settings.AccessTokenExpiresMinutes)
        )
        claims = {"exp": expires, "user_id": user_id}
        token = jwt.encode(
            claims=claims, key=settings.JWTSigningKey, algorithm=cls.algorithm
        )
        return token, expires

    @classmethod
    def _set_cookie(cls, response: Response, token: str) -> None:
        response.set_cookie(key=cls.cookie_name, value=token, httponly=True)

    @classmethod
    def process_login(cls, user_id: str, response: Response) -> Token | None:
        token, expires = cls.create_access_token(user_id)
        if cls.accept_cookie:
            cls._set_cookie(response=response, token=token)
        if cls.accept_header:
            return Token(access_token=token, expires_at=expires)
        return None

    def get_user_from_token(self, token: str, session: Session) -> User:
        try:
            payload = jwt.decode(
                token=token, key=settings.JWTSigningKey, algorithms=self.algorithm
            )
            token_data = TokenPayload(**payload)
        except (JWTError, ValidationError):
            raise self.credentials_exception
        repository = UserRepository(session)
        user = repository.filter([User.id == token_data.user_id], first_only=True)
        if not user:
            raise self.credentials_exception
        return user

    def _get_token_from_cookie(self, request: Request) -> str | None:
        token = request.cookies.get(self.cookie_name)
        return token

    def _get_token_from_header(self, request: Request) -> str | None:
        authorization = request.headers.get(self.header_name)
        scheme, token = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            return None
        return token

    def _get_token(self, request: Request) -> str:
        token = None
        if self.accept_header:
            token = self._get_token_from_header(request)
        if not token and self.accept_cookie:
            token = self._get_token_from_cookie(request)
        if not token:
            raise self.credentials_exception
        return token

    def __call__(self, request: Request, session: Session) -> User:
        token = self._get_token(request)
        return self.get_user_from_token(token, session)
