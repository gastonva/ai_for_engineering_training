import inspect
import logging
import os
from typing import Annotated, TypedDict
from uuid import uuid4

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch
from langfuse.decorators import observe
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.monitoring.langfuse_provider import LangfuseProvider
from src.settings.settings import settings

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

    async def take_action(self, state: AgentState):
        tool_calls = state["messages"][-1].tool_calls
        results = []
        for t in tool_calls:
            logger.info(f"Calling: {t}")
            if not t["name"] in self.tools:
                logger.info("\n ....bad tool name....")
                result = "bad tool name, retry"
                self.langfuse_callback_handler.on_tool_end(result)
            else:
                self.langfuse_callback_handler.on_tool_start(
                    {"name": t["name"]}, t["args"], run_id=uuid4()
                )
                tool = self.tools[t["name"]]
                args = t["args"]
                if hasattr(tool, "ainvoke") and callable(getattr(tool, "ainvoke")):
                    result = await tool.ainvoke(args)
                elif inspect.iscoroutinefunction(tool):
                    result = await tool(args)
                else:
                    result = tool.invoke(args)
                self.langfuse_callback_handler.on_tool_end(result, run_id=uuid4())
            results.append(
                ToolMessage(tool_call_id=t["id"], name=t["name"], content=str(result))
            )
        logger.info("Back to the model!")
        return {"messages": results}


class SearchAgent:
    # Setup the MCP client
    server_params = StdioServerParameters(
        command="python",
        args=["./src/mcp_servers/movie_search_server.py"],
    )

    tools = [TavilySearch(max_results=4, tavily_api_key=settings.TAVILY_API_KEY)]

    @classmethod
    @observe(name="search_agent.search", as_type="tool")
    async def search(cls, query: str, user_id: str) -> str:
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
        async with stdio_client(cls.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()

                # Get tools
                mcp_tools = await load_mcp_tools(session)
                if mcp_tools:
                    cls.tools.extend(mcp_tools)
                agent = Agent(cls.tools, llm, system_prompt, user_id)
                user_search = [HumanMessage(content=query)]
                result = await agent.graph.ainvoke({"messages": user_search})
        return result["messages"][-1].content
