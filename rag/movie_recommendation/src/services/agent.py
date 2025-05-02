from src.core.agent import SearchAgent


class AgentService:
    @staticmethod
    def search_movies(query: str, user_id: str) -> str:
        return {"answer": SearchAgent.search(query, user_id)}
