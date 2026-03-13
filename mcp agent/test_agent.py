import asyncio
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyDhkZQZukaAmQbf599UkiRfMUqhMZdmEqs")

@tool
def search_restaurants(cuisine: str, location: str) -> str:
    """Search for restaurants by cuisine and location."""
    return f"Found: Spice Garden (4.5★, 30 mins), Biryani Bros (4.7★, 40 mins) — both serve {cuisine} in {location}"

@tool
def place_order(restaurant_name: str, items: str) -> str:
    """Place an order at a restaurant."""
    return f"Order placed at {restaurant_name} for {items}! Order ID: ORD12345. ETA: 35 mins."

async def main():
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash-lite",
        google_api_key=GOOGLE_API_KEY,
    )

    agent = create_react_agent(llm, [search_restaurants, place_order])

    agent = create_react_agent(
    llm, 
    [search_restaurants, place_order],
    prompt="You are a food ordering assistant. After calling tools, always summarize the results in a friendly message to the user."
)

    print("Sending message to agent...")
    result = await agent.ainvoke({
        "messages": [{"role": "user", "content": "I want indian food in koramangala"}]
    })

    print("\n--- AGENT RESPONSE ---")
    for msg in result["messages"]:
        print(f"\n[{msg.type}]: {msg.content}")

asyncio.run(main())