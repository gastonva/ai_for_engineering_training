from uuid import UUID
from src.core.rag import RAG
from src.repositories.chat import ChatRepository
from sqlalchemy.orm import Session


class ChatService:
    def __init__(self, session: Session):
        self.repository = ChatRepository(session)

    def chat(self, query: str, user_id: UUID, session_id: UUID | None) -> dict:
        rag = RAG()

        filters = self.repository.build_filters(
            {
                "user_id": user_id,
                "session_id": session_id,
            }
        )
        chat_session = self.repository.filter(filters)

        if not chat_session:
            answer = rag.generate_answer(query=query)
            self.repository.create(
                **{
                    "user_id": user_id,
                    "chat_history": {
                        "input": query,
                        "context": answer["context"],
                        "answer": answer["answer"],
                    },
                }
            )
            return {
                "user_id": user_id,
                "generated": answer,
            }

        # Get previous 10 responses
        chat_history = [
            {
                "human": session.chat_history["input"],
                "assistant": session.chat_history["answer"],
            }
            for id, session in enumerate(chat_session)
            if id < 10
        ]

        answer = rag.generate_answer(
            query=query,
            history=chat_history,
        )

        self.repository.create(
            **{
                "user_id": user_id,
                "session_id": session_id,
                "chat_history": {
                    "input": query,
                    "context": answer["context"],
                    "answer": answer["answer"],
                },
            }
        )

        return {
            "user_id": user_id,
            "generated": answer,
        }

    def history(self, user_id: UUID) -> list[dict]:
        chat_sessions = self.repository.get_latest_unique_sessions(user_id=user_id)
        if not chat_sessions:
            return {"history": []}

        # Get unique session IDs with the latest user query
        unique_sessions = []
        for session in chat_sessions:
            session_id = session.session_id
            unique_sessions.append(
                {
                    "session_id": session_id,
                    "latest_query": session.chat_history["input"],
                }
            )

        return {"history": unique_sessions}
