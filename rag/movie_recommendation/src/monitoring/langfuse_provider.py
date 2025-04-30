from uuid import uuid4
from langfuse import Langfuse
from langfuse.callback import CallbackHandler
from langfuse.client import StatefulTraceClient
from src.settings.settings import settings

class LangfuseProvider:
    _instance: Langfuse | None = None

    @classmethod
    def get_instance(cls) -> Langfuse:
        if cls._instance is None:
            cls._instance = Langfuse(
                secret_key=settings.LangfuseSecretKey,
                public_key=settings.LangfusePublicKey,
                host=settings.LangfuseHost,
            )
        return cls._instance
    
    @classmethod
    def get_callback_handler(cls) -> CallbackHandler:
        return CallbackHandler()
    
    @classmethod
    def create_trace(cls, name: str) -> StatefulTraceClient:
        """
        Create a trace for the given name.
        """
        langfuse = cls.get_instance()
        return langfuse.trace(name=name, session_id=str(uuid4()))

    @classmethod
    def create_span(cls, name: str) -> None:
        """
        Create a span for the given name.
        """
        langfuse = cls.get_instance()
        return langfuse.span(name=name)