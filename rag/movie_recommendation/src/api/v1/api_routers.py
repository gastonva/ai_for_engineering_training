from fastapi import APIRouter
from src.api.v1.routers.user import router as user_router
from src.api.v1.routers.chat import router as chat_router

router = APIRouter()

router.include_router(user_router, tags=["Users"], prefix="/users")
router.include_router(chat_router, tags=["Chat"], prefix="/chat")
