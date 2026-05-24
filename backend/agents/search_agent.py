import json
from groq import Groq
from config import GROQ_API_KEY
from valkey_client import r

client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """You are a product search specialist for VoiceCart, an Indian e-commerce store.
Find products matching the user's request using your tools.
Always mention: product name, price in ₹, and rating.
If multiple results, list top 3 with their product IDs (so they can be added to cart later).
Keep response under 3 sentences."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_products",
            "description": "Search products by semantic query, brand, category, or price range",
            "parameters": {
                "type": "object",
                "properties": {
                    "query":     {"type": "string",  "description": "Natural language search e.g. 'wireless headphones with long battery'"},
                    "brand":     {"type": "string",  "description": "Brand name e.g. 'Samsung', 'Apple', 'Sony', 'Nike', 'boAt'"},
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
            "name": "get_product_details",
            "description": "Get full details of a specific product by its ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_id": {"type": "string", "description": "Product ID e.g. 'product:01-samsung-a54'"}
                },
                "required": ["product_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_rated",
            "description": "Get the top 5 highest rated products in the store",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]


def _run_tool(tool_name: str, tool_args: dict, session_id: str) -> str:
    try:
        if tool_name == "search_products":
            from tools.search_tools import search_products
            result = search_products(**tool_args)
            # Save last search results to session so cart agent can reference them
            if result.get("products"):
                r.set(f"last_search:{session_id}", json.dumps(result["products"]), ex=3600)
            # Also track views for trending
            from tools.discovery_tools import track_product_view
            for p in result.get("products", [])[:3]:
                if p.get("id"):
                    track_product_view(session_id, p["id"])
            return json.dumps(result)

        elif tool_name == "get_product_details":
            from tools.search_tools import get_product_details
            result = get_product_details(**tool_args)
            if result.get("id"):
                from tools.discovery_tools import track_product_view
                track_product_view(session_id, result["id"])
            return json.dumps(result)

        elif tool_name == "get_top_rated":
            from tools.search_tools import get_top_rated_products
            return json.dumps(get_top_rated_products())

        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    except Exception as e:
        return json.dumps({"error": str(e)})


def run(task: str, session_id: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": task}
    ]
    while True:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=512,
            temperature=0.2,
        )
        choice = response.choices[0]

        if not choice.message.tool_calls:
            return choice.message.content or "No products found."

        messages.append(choice.message)
        for tc in choice.message.tool_calls:
            result = _run_tool(tc.function.name, json.loads(tc.function.arguments), session_id)
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})
