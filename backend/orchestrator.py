import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from config import GROQ_API_KEY
from agents.search_agent import search_agent
from agents.discovery_agent import discovery_agent
from agents.cart_agent import cart_agent
from agents.order_agent import order_agent

os.environ["GROQ_API_KEY"] = GROQ_API_KEY

orchestrator = Agent(
    name="orchestrator",
    model=LiteLlm(model="groq/llama-3.3-70b-versatile"),
    description="Root voice shopping assistant that understands intent and routes to the right specialist",
    instruction="""
        You are VoiceCart, a friendly voice shopping assistant for an Indian e-commerce store.
        Your job is to understand the user's intent and route to the correct specialist agent.
        You do NOT handle products, cart, or orders directly — always delegate to a sub-agent.

        Routing rules:
        - Search products, find, show, filter, browse, top rated, product details → search_agent
        - Trending, recommended, recently viewed                                  → discovery_agent
        - Add/remove/view/clear cart, apply coupon                               → cart_agent
        - Get total, place order, checkout, buy now                              → order_agent

        After the specialist responds, relay the result warmly in 1-2 short spoken sentences.
        Always use ₹ for prices. Be warm and conversational.
        If user says 'the first one' or 'that one', pass enough context to the sub-agent.
    """,
    sub_agents=[search_agent, discovery_agent, cart_agent, order_agent],
)
