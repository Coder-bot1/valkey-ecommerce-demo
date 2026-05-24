# Member 3 owns this file.
# These are STUB implementations — replace each function body with real Valkey calls.
# DO NOT change function signatures or parameter names.

def add_to_cart(session_id: str, product_id: str, quantity: int = 1) -> dict:
    """Add a product to the user's cart."""
    # STUB — Member 3 replaces with HSET cart:{session_id}
    return {"status": "added", "product_name": "Product", "quantity": quantity, "cart_total_items": 1, "note": "stub"}


def remove_from_cart(session_id: str, product_id: str) -> dict:
    """Remove a product from the user's cart."""
    # STUB — Member 3 replaces with HDEL cart:{session_id}
    return {"status": "removed", "product_id": product_id, "note": "stub"}


def update_quantity(session_id: str, product_id: str, quantity: int) -> dict:
    """Update quantity of a product in cart."""
    # STUB — Member 3 replaces with HSET cart:{session_id}
    return {"status": "updated", "quantity": quantity, "note": "stub"}


def get_cart(session_id: str) -> dict:
    """Get all cart items with prices and total."""
    # STUB — Member 3 replaces with HGETALL cart:{session_id}
    return {"items": [], "total": 0, "item_count": 0, "note": "stub"}


def clear_cart(session_id: str) -> dict:
    """Clear all items from cart."""
    # STUB — Member 3 replaces with DEL cart:{session_id}
    return {"status": "cart_cleared", "note": "stub"}


def apply_coupon(session_id: str, coupon_code: str) -> dict:
    """Apply a coupon code to the cart."""
    # STUB — Member 3 replaces with JSON.GET coupon:{code}
    return {"status": "applied", "code": coupon_code, "discount_value": 10, "note": "stub"}
