from sqlalchemy import and_
from src.repositories.base import ModelRepository
from src.models.chat_session import ChatSession


class ChatRepository(ModelRepository):
    model = ChatSession

    def build_filters(self, params: dict) -> list:
        filters = []
        if params.get("user_id") and params.get("session_id", None):
            filters.append(
                and_(
                    self.model.user_id == params["user_id"],
                    self.model.session_id == params["session_id"],
                )
            )
        elif params.get("user_id"):
            filters.append(self.model.user_id == params["user_id"])
        return filters

    def get_latest_unique_sessions(self, user_id: str) -> ChatSession:
        return (
            self.session.query(self.model)
            .filter(self.model.user_id == user_id)
            .distinct(self.model.session_id)
            .order_by(self.model.session_id, self.model.id.desc())
            .all()
        )
