# 🍔 Swiggy Agent — LangChain + MCP + Gemini

A food ordering assistant that teaches you how LangChain agents and MCP work together.

---

## Setup

```bash
pip install -r requirements.txt
```

Get a free Gemini API key from https://aistudio.google.com/

Set your key:
```bash
export GOOGLE_API_KEY="your-key-here"
```

Run the agent:
```bash
python agent.py
```

---

## Try these prompts

```
I want to order Indian food in Koramangala
Show me Chinese restaurants in Indiranagar
Order Butter Chicken and Garlic Naan from Spice Garden
What's the best rated restaurant near Whitefield?
```

---

## How it works — the mental model

### What is LangChain?
LangChain is a framework that lets you connect LLMs to tools, memory, and data sources.
The core idea: instead of just generating text, the LLM can **decide to call a function**,
see the result, and keep reasoning until it has a final answer. This loop is called ReAct.

```
User: "Order biryani in Koramangala"
         ↓
LangChain Agent (Gemini)
  → "I should search for biryani restaurants first"
  → calls search_restaurants(cuisine="indian", location="koramangala")
  → sees results: [Spice Garden, Biryani Bros...]
  → "Now I'll tell the user the options"
  → responds with restaurant list
         ↓
User: "Order from Biryani Bros — Chicken Biryani"
         ↓
  → calls place_order(restaurant_id="r4", items=["Chicken Biryani"])
  → sees: {"order_id": "ORD12345", "eta": "40 mins", ...}
  → responds with confirmation
```

### What is MCP?
MCP (Model Context Protocol) is a standard for how AI agents discover and call tools.
Think of it like a USB standard — any MCP-compatible agent can plug into any MCP server.

Without MCP: each agent needs custom code to call each tool.
With MCP: the agent asks "what tools do you have?" and the server responds with a schema.

```
Agent                          MCP Server
  |                                |
  |-- initialize ----------------> |   (handshake)
  |<- ok, I'm swiggy-server ------ |
  |                                |
  |-- tools/list ----------------> |   (discovery)
  |<- [search_restaurants,         |
  |    place_order] -------------- |
  |                                |
  |-- tools/call ---------------->  |  (execution)
  |   search_restaurants(...)       |
  |<- {restaurants: [...]} ------- |
```

### What is the ReAct loop?
ReAct = Reason + Act. The agent alternates between:
- **Thought**: what do I need to do?
- **Action**: call a tool
- **Observation**: here's what the tool returned
- **Repeat** until it has enough info to answer

This is the difference between a chatbot (replies immediately) and an agent (thinks, acts, observes).

---

## File structure

```
swiggy-agent/
├── mcp_server.py   # The MCP server — exposes tools over JSON-RPC/stdio
├── agent.py        # The LangChain agent — connects to MCP, uses Gemini
├── requirements.txt
└── README.md
```

---

## What to say in the Swiggy interview

> "I built a small project to understand how LangChain agents and MCP work together.
> The MCP server exposes tools — search and place_order — over the standard protocol.
> LangChain's MultiServerMCPClient discovers those tools automatically and wraps them
> for the agent. Gemini then decides when to call which tool based on user intent.
> This pattern maps directly to what I'd build for the WhatsApp ordering agent —
> the same separation between tool exposure (MCP server) and reasoning (LangChain agent)."
