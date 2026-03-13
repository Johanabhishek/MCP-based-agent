"""
MCP Server over HTTP (SSE transport)
Run this first: python mcp_server.py
It starts on http://localhost:8000
"""

import json
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn
import asyncio

app = FastAPI()

# ── Mock data ────────────────────────────────────────────────────────────────

RESTAURANTS = [
    {"id": "r1", "name": "Spice Garden",  "cuisine": "indian",  "location": "koramangala", "rating": 4.5, "eta": "30 mins"},
    {"id": "r2", "name": "Wok This Way",  "cuisine": "chinese", "location": "koramangala", "rating": 4.2, "eta": "25 mins"},
    {"id": "r3", "name": "Biryani Bros",  "cuisine": "indian",  "location": "indiranagar",  "rating": 4.7, "eta": "40 mins"},
    {"id": "r4", "name": "Burger Barn",   "cuisine": "american","location": "koramangala", "rating": 4.1, "eta": "20 mins"},
    {"id": "r5", "name": "Dosa Delight",  "cuisine": "indian",  "location": "whitefield",   "rating": 4.6, "eta": "30 mins"},
]

MENUS = {
    "r1": ["Butter Chicken", "Paneer Tikka", "Garlic Naan", "Dal Makhani"],
    "r2": ["Hakka Noodles", "Manchurian", "Fried Rice", "Spring Rolls"],
    "r3": ["Chicken Biryani", "Mutton Biryani", "Raita", "Shorba"],
    "r4": ["Classic Burger", "Cheese Fries", "Onion Rings", "Milkshake"],
    "r5": ["Masala Dosa", "Idli Sambar", "Vada", "Filter Coffee"],
}

# ── Tool logic ────────────────────────────────────────────────────────────────

def search_restaurants(cuisine: str = "", location: str = "") -> dict:
    results = RESTAURANTS
    if cuisine:
        results = [r for r in results if cuisine.lower() in r["cuisine"]]
    if location:
        results = [r for r in results if location.lower() in r["location"]]
    for r in results:
        r["menu"] = MENUS.get(r["id"], [])
    return {"found": len(results), "restaurants": results}

def place_order(restaurant_id: str, items: list) -> dict:
    restaurant = next((r for r in RESTAURANTS if r["id"] == restaurant_id), None)
    if not restaurant:
        return {"success": False, "message": f"Restaurant '{restaurant_id}' not found."}
    valid_menu = MENUS.get(restaurant_id, [])
    invalid = [i for i in items if i not in valid_menu]
    if invalid:
        return {"success": False, "message": f"The item(s) {invalid} aren't in the menu. Here's the menu for {restaurant['name']}: {valid_menu}"}
    order_id = f"ORD{abs(hash(restaurant_id + str(items))) % 100000:05d}"
    return {
        "success": True,
        "order_id": order_id,
        "restaurant": restaurant["name"],
        "items": items,
        "total": f"₹{len(items) * 150}",
        "eta": restaurant["eta"],
        "message": f"Order placed! Arrives in {restaurant['eta']}."
    }

# ── MCP Tools manifest ────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "search_restaurants",
        "description": "Search for restaurants by cuisine and/or location. Returns list with menus.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cuisine":  {"type": "string", "description": "e.g. indian, chinese, american"},
                "location": {"type": "string", "description": "e.g. koramangala, indiranagar, whitefield"}
            }
        }
    },
    {
        "name": "place_order",
        "description": "Place a food order. Needs restaurant_id from search results and list of item names.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "restaurant_id": {"type": "string"},
                "items": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["restaurant_id", "items"]
        }
    }
]

# ── MCP HTTP endpoints ────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"name": "swiggy-mcp-server", "version": "1.0.0", "protocol": "MCP over HTTP"}

@app.get("/sse")
async def sse_endpoint():
    """SSE endpoint — MCP client connects here first"""
    async def event_stream():
        # Send server info
        data = json.dumps({
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
            "params": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "swiggy-mcp-server", "version": "1.0.0"},
                "capabilities": {"tools": {}}
            }
        })
        yield f"data: {data}\n\n"
        # Keep alive
        while True:
            await asyncio.sleep(30)
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")

@app.post("/messages")
async def messages_endpoint(request: dict):
    """Main JSON-RPC endpoint"""
    method = request.get("method")
    req_id = request.get("id")
    params = request.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "swiggy-mcp-server", "version": "1.0.0"}
            }
        }

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS}}

    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "search_restaurants":
            result = search_restaurants(**args)
        elif tool_name == "place_order":
            result = place_order(
                restaurant_id=args.get("restaurant_id", ""),
                items=args.get("items", [])
            )
        else:
            result = {"error": f"Unknown tool: {tool_name}"}

        return {
            "jsonrpc": "2.0", "id": req_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}],
                "isError": False
            }
        }

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Unknown method: {method}"}}

if __name__ == "__main__":
    print(" MCP Server running at http://localhost:8000")
    print("   Tools: search_restaurants, place_order")
    uvicorn.run(app, host="0.0.0.0", port=8000)