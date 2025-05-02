from fastapi import APIRouter, Body, Depends

from src.db.dependencies import get_user
from src.models.user import User
from src.schemas import AgentResponse, UserQueryForAgent
from src.services.agent import AgentService

router = APIRouter()


@router.post("/search_movies")
async def search_movies(
    user: User = Depends(get_user),
    body: UserQueryForAgent = Body(...),
) -> AgentResponse:
    """
    Search for movies based on user query.
    """

    return await AgentService.search_movies(body.query, str(user.id))
