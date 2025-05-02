from src.core.agent import SearchAgent


class AgentService:
    @staticmethod
    async def search_movies(query: str, user_id: str) -> str:
        return {"answer": await SearchAgent.search(query, user_id)}
