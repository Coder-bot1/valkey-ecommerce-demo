import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from tools.order_tools import get_cart_total, place_order

order_agent = Agent(
    name="order_agent",
    model=LiteLlm(model="groq/llama-3.3-70b-versatile"),
    description="Handles checkout, cart total calculation, and order placement",
    instruction="""
        You handle orders and checkout for VoiceCart.
        Before placing an order, always read back the total: "Your total is ₹X. Shall I place the order?"
        After placing, confirm the order ID clearly.
        Keep responses short and clear.
    """,
    tools=[get_cart_total, place_order],
)
