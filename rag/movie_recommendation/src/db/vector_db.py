from langchain_community.vectorstores import PGVector
from langchain_core.embeddings import Embeddings

from src.settings.settings import settings


class VectorStoreProvider:
    def __init__(self, collection_name: str, use_jsonb: bool = True):
        self._connection = settings.VectorDBConnection
        self._collection_name = collection_name
        self._use_jsonb = use_jsonb
        self._vector_store = None

    def get_vector_store(self, embedding_function: Embeddings) -> PGVector:
        if not self._vector_store:
            self._vector_store = PGVector(
                embedding_function=embedding_function,
                collection_name=self._collection_name,
                connection_string=self._connection,
                use_jsonb=self._use_jsonb,
            )
        return self._vector_store
