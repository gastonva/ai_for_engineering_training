from src.core.agent import SearchAgent


class AgentService:
    @staticmethod
    def search_movies(query: str) -> str:
        return {"answer": SearchAgent.search(query)}
