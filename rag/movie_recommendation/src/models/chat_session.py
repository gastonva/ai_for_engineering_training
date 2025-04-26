from uuid import UUID, uuid4

from sqlalchemy import JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base_class import Base


class ChatSession(Base):
    __tablename__ = "chat_session"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[UUID] = mapped_column(ForeignKey("user.id"))
    session_id: Mapped[UUID] = mapped_column(default=uuid4, nullable=False)
    chat_history: Mapped[dict] = mapped_column(JSON)
