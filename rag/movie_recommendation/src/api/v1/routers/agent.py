from fastapi import APIRouter, Body, Depends
from src.db.dependencies import get_user
from src.schemas import UserQueryForAgent, AgentResponse
from src.services.agent import AgentService

from src.models.user import User

router = APIRouter()


@router.post("/search_movies")
def search_movies(
    user: User = Depends(get_user),
    body: UserQueryForAgent = Body(...),
) -> AgentResponse:
    """
    Search for movies based on user query.
    """

    return AgentService.search_movies(body.query, str(user.id))
