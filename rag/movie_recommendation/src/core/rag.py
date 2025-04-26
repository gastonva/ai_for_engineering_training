from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.vectorstores import VectorStoreRetriever
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import MessagesPlaceholder
from src.db.vector_db import VectorStoreProvider
from src.settings.settings import settings


class RAG:
    def __init__(self) -> None:
        self.vectordb_connection = settings.VectorDBConnection
        self.vector_store_provider = VectorStoreProvider(settings.CollectionName)
        self.api_key = settings.API_KEY

    def _get_retriever(self, k: int = 5) -> VectorStoreRetriever:
        embedding = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        # Get the vector store from the VectorStoreProvider
        vector_store = self.vector_store_provider.get_vector_store(embedding)

        # Build the retriever
        retriever = vector_store.as_retriever(search_kwargs={"k": k})
        return retriever

    def generate_answer(
        self, query: str, k: int = 5, history: list[dict] | None = None
    ) -> str:
        retriever = self._get_retriever(k)

        # Load the LLM
        llm = ChatOpenAI(api_key=self.api_key)

        # Contextualize question
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, just "
            "reformulate it if needed and otherwise return it as is."
        )

        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
            ]
        )

        # Create a history-aware retriever
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )

        # QA prompt
        qa_system_prompt = (
            "You are an assistant for movies recommendations. "
            "Use the retrieved context to answer. "
            "If you don't know, just say it. "
            "If the human input is in another languange than English, "
            "give the answer in that language. "
        )

        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                ("system", "Context: {context}"),
            ]
        )

        # Create QA chain
        qa_chain = create_stuff_documents_chain(llm, qa_prompt)

        # Create full chain
        full_chain = create_retrieval_chain(history_aware_retriever, qa_chain)

        # Build chat_history in LangChain message format
        chat_history = []
        if history:
            for m in history:
                chat_history.append(HumanMessage(content=m["human"]))
                chat_history.append(AIMessage(content=m["assistant"]))

        inputs = {"input": query, "chat_history": chat_history}

        result = full_chain.invoke(inputs)

        context_documents = [
            {"page_content": doc.page_content, "metadata": doc.metadata}
            for doc in result["context"]
        ]

        response = {
            "input": query,
            "context": context_documents,
            "answer": result["answer"],
        }

        return response
