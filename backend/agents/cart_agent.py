import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from tools.cart_tools import add_to_cart, remove_from_cart, get_cart, clear_cart, apply_coupon

cart_agent = Agent(
    name="cart_agent",
    model=LiteLlm(model="groq/llama-3.3-70b-versatile"),
    description="Manages shopping cart — add, remove, view items and apply coupon codes",
    instruction="""
        You manage the user's shopping cart for VoiceCart.
        Always confirm the action you took by product name, never by product ID.
        Keep responses under 2 sentences.
        Example: "Added Sony WH-1000XM5 to your cart. You now have 2 items."
        Always respond in plain natural language. Do not call any transfer or routing tools.
    """,
    tools=[add_to_cart, remove_from_cart, get_cart, clear_cart, apply_coupon],
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
