"""
LangChain Agent — connects to MCP server over HTTP
Start the MCP server first: python mcp_server.py
Then run: python agent.py
"""

import asyncio
import os
import httpx
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import StructuredTool
from pydantic import BaseModel

GROQ_API_KEY = "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"
MCP_SERVER_URL = "http://localhost:8000"


class SearchInput(BaseModel):
    cuisine: str = ""
    location: str = ""


class OrderInput(BaseModel):
    restaurant_id: str = ""
    items: list = []


TOOL_SCHEMAS = {
    "search_restaurants": SearchInput,
    "place_order": OrderInput,
}


def call_mcp_tool(tool_name: str, arguments: dict) -> str:
    """Call a tool on the MCP server via HTTP."""
    response = httpx.post(
        f"{MCP_SERVER_URL}/messages",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        },
        timeout=10.0
    )
    """print(f"[DEBUG] Response: {response.text[:300]}")"""
    result = response.json()
    return result["result"]["content"][0]["text"]


def load_mcp_tools():
    response = httpx.post(
        f"{MCP_SERVER_URL}/messages",
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        timeout=10.0
    )
    mcp_tools = response.json()["result"]["tools"]

    langchain_tools = []
    for t in mcp_tools:
        tool_name = t["name"]
        tool_desc = t["description"]
        schema = TOOL_SCHEMAS.get(tool_name)

        def make_fn(name):
            def fn(**kwargs) -> str:
                """Calls MCP tool."""
                return call_mcp_tool(name, kwargs)
            return fn

        langchain_tools.append(StructuredTool(
            name=tool_name,
            description=tool_desc,
            func=make_fn(tool_name),
            args_schema=schema,
        ))

    return langchain_tools


async def chat():
    print("\n🔌 Connecting to MCP server...")
    try:
        tools = load_mcp_tools()
        print(f"✅ Loaded {len(tools)} tools from MCP: {[t.name for t in tools]}")
    except Exception as e:
        print(f"❌ Could not connect to MCP server: {e}")
        print("   Make sure mcp_server.py is running first!")
        return

    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=GROQ_API_KEY,
    )

    agent = create_react_agent(
        llm,
        tools,
        prompt="You are a Swiggy food ordering assistant for Bangalore. After calling tools, always summarize results in a friendly message. When searching restaurants, always use specific area names for location like koramangala, indiranagar, whitefield, bangalore — never leave location empty. Map dish names to cuisines: biryani/dosa/curry = indian, noodles = chinese, burger = american. When placing orders, use the exact restaurant_id from search results."
    )

    print("\n🍔 Swiggy Agent (MCP + Groq) — type 'quit' to exit")
    print("=" * 50)

    history = []

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input or user_input.lower() == "quit":
            break

        history.append({"role": "user", "content": user_input})

        try:
            result = await agent.ainvoke({"messages": history})
            for msg in reversed(result["messages"]):
                if msg.type == "ai" and msg.content:
                    print(f"\n🤖 Agent: {msg.content}")
                    history.append({"role": "assistant", "content": msg.content})
                    break
        except Exception as e:
            if "429" in str(e) or "rate_limit" in str(e).lower():
                print("\n⚠️ Rate limit — wait 60 seconds and try again")
            else:
                print(f"\n❌ Error: {e}")


asyncio.run(chat())