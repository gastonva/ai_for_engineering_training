from fastapi import APIRouter, Body, Depends
from sqlalchemy.orm import Session

from src.db.dependencies import get_session, get_user
from src.models.user import User
from src.schemas import ChatAnswer, ChatHistory, ChatQuery
from src.services.chat import ChatService

router = APIRouter()


@router.post("/ask")
def chat(
    session: Session = Depends(get_session),
    user: User = Depends(get_user),
    chat_query: ChatQuery = Body(...),
) -> ChatAnswer:
    return ChatService(session).chat(chat_query.query, user.id, chat_query.session_id)


@router.get("/history")
def chat_history(
    session: Session = Depends(get_session), user: User = Depends(get_user)
) -> ChatHistory:
    return ChatService(session).history(user.id)
