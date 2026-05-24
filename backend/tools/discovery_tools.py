# Member 2 owns this file.
# These are STUB implementations — replace each function body with real Valkey calls.
# DO NOT change function signatures or parameter names.

def get_trending_products() -> dict:
    """Get top trending products based on views and purchases."""
    # STUB — Member 2 replaces with ZREVRANGE trending:global
    return {"products": [], "count": 0, "note": "stub - member 2 implement this"}


def get_recently_viewed(session_id: str) -> dict:
    """Get products the user recently viewed in this session."""
    # STUB — Member 2 replaces with LRANGE user_history:{session_id}
    return {"products": [], "count": 0, "note": "stub - member 2 implement this"}


def track_product_view(session_id: str, product_id: str) -> dict:
    """Track a product view for trending and history."""
    # STUB — Member 2 replaces with LPUSH + ZINCRBY
    return {"status": "tracked"}
