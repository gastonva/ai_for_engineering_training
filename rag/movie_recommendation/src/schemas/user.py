from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserSignupInput(BaseModel):
    email: str = Field(..., description="User's email", examples=["john@doe.com"])
    password: str = Field(..., description="User's password", examples=["Hello!123"])


class UserSignupOutput(BaseModel):
    bearer_token: str = Field(..., description="Auth Bearer token")


class Token(BaseModel):
    token_type: str = "Bearer"
    access_token: str
    expires_at: datetime


class TokenPayload(BaseModel):
    user_id: UUID
