import json
from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a cart specialist for VoiceCart.
You manage the user's shopping cart — add, remove, view, clear, and apply coupons.
Always confirm the action by product name. Keep responses under 2 sentences."""

TOOLS = [
    # TODO: Member 3 — add add_to_cart, remove_from_cart, get_cart, clear_cart, apply_coupon tool definitions here
]


def _run_tool(tool_name: str, tool_args: dict, session_id: str) -> str:
    # TODO: Member 3 — route tool calls to tools/cart_tools.py
    return json.dumps({"error": f"Tool '{tool_name}' not implemented yet"})


def run(task: str, session_id: str) -> str:
    # TODO: Member 3 — implement agentic loop (same pattern as search_agent.py)
    return "Cart agent coming soon."
