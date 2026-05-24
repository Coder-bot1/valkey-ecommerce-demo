import os
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from tools.search_tools import search_products, get_product_details, get_top_rated_products

search_agent = Agent(
    name="search_agent",
    model=LiteLlm(model="groq/llama-3.3-70b-versatile"),
    description="Finds and shows products based on user queries — search by keyword, brand, category, price, or get top rated",
    instruction="""
        You are a product search specialist for VoiceCart, an Indian e-commerce store.
        Find products matching the user's request using your tools.
        Always mention: product name, price in ₹, and rating.
        If multiple results, list top 3 with their product IDs so they can be added to cart.
        Keep response under 3 sentences.
        Always respond in plain natural language. Do not call any transfer or routing tools.
    """,
    tools=[search_products, get_product_details, get_top_rated_products],
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
)
