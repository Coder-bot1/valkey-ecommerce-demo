# Member 3 owns this file.
# These are STUB implementations — replace each function body with real Valkey calls.
# DO NOT change function signatures or parameter names.

def get_cart_total(session_id: str) -> dict:
    """Get cart total with any discount applied."""
    # STUB — Member 3 replaces with HGETALL + coupon lookup
    return {"subtotal": 0, "discount": 0, "total": 0, "items": [], "note": "stub"}


def place_order(session_id: str, user_id: str = "guest") -> dict:
    """Place the order for all items in cart."""
    # STUB — Member 3 replaces with JSON.SET order + DEL cart
    return {"status": "order_placed", "order_id": "order:stub-000", "total": 0, "note": "stub"}


def get_order_history(user_id: str) -> dict:
    """Get past orders for a user."""
    # STUB — Member 3 replaces with ZREVRANGE user_orders:{user_id}
    return {"orders": [], "count": 0, "note": "stub"}


def get_order_status(order_id: str) -> dict:
    """Get the status of a specific order."""
    # STUB — Member 3 replaces with JSON.GET order:{id}
    return {"order_id": order_id, "status": "confirmed", "total": 0, "note": "stub"}
