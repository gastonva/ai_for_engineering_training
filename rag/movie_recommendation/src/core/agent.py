from typing import TypedDict, Annotated
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import SystemMessage, ToolMessage, HumanMessage
from langchain_openai import ChatOpenAI
from src.settings.settings import settings
import logging
from src.monitoring.langfuse_provider import LangfuseProvider
from langfuse.decorators import observe
import os

logger = logging.getLogger(__name__)

os.environ["LANGFUSE_PUBLIC_KEY"] = settings.LangfusePublicKey
os.environ["LANGFUSE_SECRET_KEY"] = settings.LangfuseSecretKey
os.environ["LANGFUSE_HOST"] = settings.LangfuseHost


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


class Agent:
    def __init__(
        self, tools: list, llm: object, system_prompt: str, user_id: str
    ) -> None:
        self.tools = tools
        self.llm = llm
        self.system_prompt = system_prompt
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges(
            "llm", self.exists_action, {True: "action", False: END}
        )
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile()
        self.tools = {t.name: t for t in tools}

        self.langfuse_callback_handler = LangfuseProvider.get_callback_handler(
            user_id=user_id
        )
        self.model = llm.bind_tools(tools)

    def exists_action(self, state: AgentState):
        result = state["messages"][-1]
        return len(result.tool_calls) > 0

    def call_openai(self, state: AgentState):
        messages = state["messages"]
        if self.system_prompt:
            messages = [SystemMessage(content=self.system_prompt)] + messages
        message = self.model.invoke(messages)
        return {"messages": [message]}

    def take_action(self, state: AgentState):
        tool_calls = state["messages"][-1].tool_calls
        results = []
        self.langfuse_callback_handler.on_tool_start({"name": t["name"]}, t["args"])
        for t in tool_calls:
            logger.info(f"Calling: {t}")
            if not t["name"] in self.tools:
                logger.info("\n ....bad tool name....")
                result = "bad tool name, retry"
                self.langfuse_callback_handler.on_tool_end(result)
            else:
                result = self.tools[t["name"]].invoke(t["args"])
                self.langfuse_callback_handler.on_tool_end(result)
            results.append(
                ToolMessage(tool_call_id=t["id"], name=t["name"], content=str(result))
            )
        logger.info("Back to the model!")
        return {"messages": results}


class SearchAgent:
    tools = [TavilySearch(max_results=4, tavily_api_key=settings.TAVILY_API_KEY)]

    @classmethod
    @observe(name="search_agent.search", as_type="tool")
    def search(cls, query: str, user_id: str) -> str:
        llm = ChatOpenAI(
            api_key=settings.API_KEY,
            model="o4-mini",
            callbacks=[LangfuseProvider.get_callback_handler(user_id=user_id)],
        )
        system_prompt = (
            "You are a search agent. You will be given a query and you will "
            "search for the answer using the Tavily search engine. "
            "You will return the results in a structured format."
        )
        agent = Agent(cls.tools, llm, system_prompt, user_id)
        user_search = [HumanMessage(content=query)]
        result = agent.graph.invoke({"messages": user_search})
        return result["messages"][-1].content
