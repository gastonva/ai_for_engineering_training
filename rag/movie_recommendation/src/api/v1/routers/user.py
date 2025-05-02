from fastapi import APIRouter, Body, Depends, Response
from sqlalchemy.orm import Session

from src.core.auth_manager import AuthManager
from src.db.dependencies import get_session
from src.schemas.user import Token, UserSignupInput
from src.services.user import UserService

router = APIRouter()


@router.post("/signup")
def signup(
    response: Response,
    session: Session = Depends(get_session),
    payload: UserSignupInput = Body(...),
) -> Token | None:
    user = UserService(session).signup(payload.email, payload.password)
    return AuthManager.process_login(str(user.id), response)


@router.post("/login")
def login(
    response: Response,
    session: Session = Depends(get_session),
    payload: UserSignupInput = Body(...),
) -> Token | None:
    user = UserService(session).login(payload.email, payload.password)
    return AuthManager.process_login(str(user.id), response)
