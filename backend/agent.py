import json
from groq import Groq
from config import GROQ_API_KEY
from valkey_client import r
from config import SESSION_TTL

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are VoiceCart, a friendly voice shopping assistant for an Indian e-commerce store.

You help users:
- Search for products by name, brand, category, or price
- Add or remove items from their cart
- View cart contents and totals
- Apply coupon codes
- Place orders

Rules:
- Keep ALL responses under 2 short sentences — they will be spoken aloud.
- Always use ₹ (Indian Rupee) for prices.
- Confirm every cart action by product name: "Added Sony headphones to your cart."
- If a user says "the first one" or "that one", refer back to the last search results.
- Be warm, helpful, and conversational.

You have access to these tools:
- search_products: search by keyword, brand, category, price range
- add_to_cart: add a product to cart
- remove_from_cart: remove a product from cart
- get_cart: view all cart items
- clear_cart: empty the cart
- apply_coupon: apply a discount code
- get_cart_total: get the total with discounts
- place_order: place the final order
- get_trending: get trending products
- get_recently_viewed: get recently viewed products
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search for products by keyword, brand, category, or price range",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":     {"type": "string",  "description": "Search keyword e.g. 'wireless headphones'"},
                    "brand":     {"type": "string",  "description": "Brand name e.g. 'Samsung', 'Apple', 'Nike'"},
                    "category":  {"type": "string",  "description": "Category e.g. 'smartphones', 'headphones', 'shoes', 'televisions', 'monitors'"},
                    "min_price": {"type": "integer", "description": "Minimum price in rupees"},
                    "max_price": {"type": "integer", "description": "Maximum price in rupees"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_to_cart",
            "description": "Add a product to the user's cart",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string",  "description": "Product ID e.g. 'product:01-samsung-a54'"},
                    "quantity":   {"type": "integer", "description": "Quantity to add, default 1"}
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_from_cart",
            "description": "Remove a product from the user's cart",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "Product ID to remove"}
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cart",
            "description": "Get all items in the user's cart with names, prices and total",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "clear_cart",
            "description": "Remove all items from the user's cart",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "apply_coupon",
            "description": "Apply a discount coupon code to the cart",
            "parameters": {
                "type": "object",
                "properties": {
                    "coupon_code": {"type": "string", "description": "Coupon code e.g. 'SAVE10', 'FLAT500'"}
                },
                "required": ["coupon_code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_cart_total",
            "description": "Get the cart total with any applied discounts before placing order",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "place_order",
            "description": "Place the order for all items currently in the cart",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_trending",
            "description": "Get the most trending products right now",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recently_viewed",
            "description": "Get products the user recently viewed",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]


def get_conversation_history(session_id: str) -> list:
    data = r.get(f"conversation:{session_id}")
    if data:
        return json.loads(data)
    return []


def save_conversation_history(session_id: str, history: list):
    r.set(f"conversation:{session_id}", json.dumps(history), ex=SESSION_TTL)


def run_tool(tool_name: str, tool_args: dict, session_id: str) -> str:
    # Import tool implementations — Members 2 & 3 fill these in
    # Until then, route to stub handlers below
    try:
        if tool_name == "search_products":
            from tools.search_tools import search_products
            return json.dumps(search_products(**tool_args))

        elif tool_name == "add_to_cart":
            from tools.cart_tools import add_to_cart
            return json.dumps(add_to_cart(session_id=session_id, **tool_args))

        elif tool_name == "remove_from_cart":
            from tools.cart_tools import remove_from_cart
            return json.dumps(remove_from_cart(session_id=session_id, **tool_args))

        elif tool_name == "get_cart":
            from tools.cart_tools import get_cart
            return json.dumps(get_cart(session_id=session_id))

        elif tool_name == "clear_cart":
            from tools.cart_tools import clear_cart
            return json.dumps(clear_cart(session_id=session_id))

        elif tool_name == "apply_coupon":
            from tools.cart_tools import apply_coupon
            return json.dumps(apply_coupon(session_id=session_id, **tool_args))

        elif tool_name == "get_cart_total":
            from tools.order_tools import get_cart_total
            return json.dumps(get_cart_total(session_id=session_id))

        elif tool_name == "place_order":
            from tools.order_tools import place_order
            return json.dumps(place_order(session_id=session_id))

        elif tool_name == "get_trending":
            from tools.discovery_tools import get_trending_products
            return json.dumps(get_trending_products())

        elif tool_name == "get_recently_viewed":
            from tools.discovery_tools import get_recently_viewed
            return json.dumps(get_recently_viewed(session_id=session_id))

        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    except ImportError:
        return json.dumps({"error": f"Tool '{tool_name}' not implemented yet."})
    except Exception as e:
        return json.dumps({"error": str(e)})


def run_agent(message: str, session_id: str) -> dict:
    history = get_conversation_history(session_id)

    history.append({"role": "user", "content": message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    # Agentic loop — keeps going until no more tool calls
    while True:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=512,
            temperature=0.3,
        )

        choice = response.choices[0]

        # No tool calls — final text response
        if not choice.message.tool_calls:
            final_text = choice.message.content
            history.append({"role": "assistant", "content": final_text})
            save_conversation_history(session_id, history)
            return {"response": final_text, "session_id": session_id}

        # Has tool calls — execute each one
        messages.append(choice.message)

        tool_results = []
        for tool_call in choice.message.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            result = run_tool(tool_name, tool_args, session_id)

            tool_results.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })

        messages.extend(tool_results)
        # Loop back — let the model respond after seeing tool results
