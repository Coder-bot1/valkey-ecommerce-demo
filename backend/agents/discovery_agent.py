import json
from groq import Groq
from config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a discovery specialist for VoiceCart.
You surface trending products, recently viewed items, and personalized recommendations.
Keep responses conversational and under 2 sentences."""

TOOLS = [
    # TODO: Member 2 — add get_trending, get_recently_viewed, get_recommendations tool definitions here
]


def _run_tool(tool_name: str, tool_args: dict, session_id: str) -> str:
    # TODO: Member 2 — route tool calls to tools/discovery_tools.py
    return json.dumps({"error": f"Tool '{tool_name}' not implemented yet"})


def run(task: str, session_id: str) -> str:
    # TODO: Member 2 — implement agentic loop (same pattern as search_agent.py)
    return "Discovery agent coming soon."
