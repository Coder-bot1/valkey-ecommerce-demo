import json
from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are an order specialist for VoiceCart.
You handle cart totals, checkout, and order placement.
Always read back the total before placing: 'Your total is ₹X. Shall I place the order?'
Keep responses short and clear."""

TOOLS = [
    # TODO: Member 3 — add get_cart_total, place_order tool definitions here
]


def _run_tool(tool_name: str, tool_args: dict, session_id: str) -> str:
    # TODO: Member 3 — route tool calls to tools/order_tools.py
    return json.dumps({"error": f"Tool '{tool_name}' not implemented yet"})


def run(task: str, session_id: str) -> str:
    # TODO: Member 3 — implement agentic loop (same pattern as search_agent.py)
    return "Order agent coming soon."
