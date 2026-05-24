"""Cart tools backed by Valkey.

Data model:
  cart:{session_id}        -> hash of product_id -> quantity (TTL = CART_TTL)
  cart_coupon:{session_id} -> string holding the applied coupon code (TTL = CART_TTL)
"""
import json

from valkey_client import r
from config import CART_TTL


def _cart_key(session_id: str) -> str:
    return f"cart:{session_id}"


def _coupon_key(session_id: str) -> str:
    return f"cart_coupon:{session_id}"


def _get_product(product_id: str) -> dict | None:
    raw = r.execute_command("JSON.GET", product_id)
    if not raw:
        return None
    return json.loads(raw)


def _get_coupon(code: str) -> dict | None:
    if not code:
        return None
    raw = r.execute_command("JSON.GET", f"coupon:{code.upper()}")
    if not raw:
        return None
    return json.loads(raw)


def add_to_cart(session_id: str, product_id: str, quantity: int = 1) -> dict:
    """Add a product to the user's cart."""
    if quantity <= 0:
        return {"status": "error", "message": "Quantity must be positive"}

    product = _get_product(product_id)
    if not product:
        return {"status": "error", "message": f"Product {product_id} not found"}

    cart_key = _cart_key(session_id)
    current_qty = int(r.hget(cart_key, product_id) or 0)
    new_qty = current_qty + quantity

    if new_qty > product.get("stock", 0):
        return {
            "status": "out_of_stock",
            "product_id": product_id,
            "product_name": product["name"],
            "available": product.get("stock", 0),
            "requested": new_qty,
        }

    r.hset(cart_key, product_id, new_qty)
    r.expire(cart_key, CART_TTL)

    total_items = sum(int(v) for v in r.hvals(cart_key))
    return {
        "status": "added",
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": new_qty,
        "cart_total_items": total_items,
    }


def remove_from_cart(session_id: str, product_id: str) -> dict:
    """Remove a product from the user's cart."""
    cart_key = _cart_key(session_id)
    product = _get_product(product_id)
    name = product["name"] if product else product_id

    removed = r.hdel(cart_key, product_id)
    if not removed:
        return {"status": "not_in_cart", "product_id": product_id, "product_name": name}

    if r.hlen(cart_key) == 0:
        r.delete(cart_key)
        r.delete(_coupon_key(session_id))

    return {"status": "removed", "product_id": product_id, "product_name": name}


def update_quantity(session_id: str, product_id: str, quantity: int) -> dict:
    """Update quantity of a product in cart."""
    if quantity <= 0:
        return remove_from_cart(session_id, product_id)

    product = _get_product(product_id)
    if not product:
        return {"status": "error", "message": f"Product {product_id} not found"}

    if quantity > product.get("stock", 0):
        return {
            "status": "out_of_stock",
            "product_id": product_id,
            "product_name": product["name"],
            "available": product.get("stock", 0),
            "requested": quantity,
        }

    cart_key = _cart_key(session_id)
    r.hset(cart_key, product_id, quantity)
    r.expire(cart_key, CART_TTL)

    return {
        "status": "updated",
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
    }


def get_cart(session_id: str) -> dict:
    """Get all cart items with prices and total."""
    cart_key = _cart_key(session_id)
    raw = r.hgetall(cart_key)
    if not raw:
        return {"items": [], "subtotal": 0, "item_count": 0}

    items = []
    subtotal = 0
    for product_id, qty in raw.items():
        qty = int(qty)
        product = _get_product(product_id)
        if not product:
            # Product was removed from catalog — drop it from the cart silently.
            r.hdel(cart_key, product_id)
            continue

        line_total = int(product["price"]) * qty
        subtotal += line_total
        items.append({
            "product_id": product_id,
            "name": product["name"],
            "price": int(product["price"]),
            "quantity": qty,
            "line_total": line_total,
        })

    return {
        "items": items,
        "subtotal": subtotal,
        "item_count": sum(i["quantity"] for i in items),
    }


def clear_cart(session_id: str) -> dict:
    """Clear all items from cart."""
    r.delete(_cart_key(session_id))
    r.delete(_coupon_key(session_id))
    return {"status": "cart_cleared"}


def apply_coupon(session_id: str, coupon_code: str) -> dict:
    """Apply a coupon code to the cart."""
    coupon_code = (coupon_code or "").strip().upper()
    if not coupon_code:
        return {"status": "invalid_coupon", "message": "Coupon code is required"}

    coupon = _get_coupon(coupon_code)
    if not coupon:
        return {"status": "invalid_coupon", "code": coupon_code, "message": "Coupon not found"}

    if not coupon.get("active", False):
        return {"status": "inactive_coupon", "code": coupon_code, "message": "Coupon is no longer active"}

    cart = get_cart(session_id)
    if cart["subtotal"] == 0:
        return {"status": "empty_cart", "message": "Add items to cart before applying a coupon"}

    min_order = int(coupon.get("min_order", 0))
    if cart["subtotal"] < min_order:
        return {
            "status": "min_order_not_met",
            "code": coupon_code,
            "min_order": min_order,
            "subtotal": cart["subtotal"],
        }

    r.set(_coupon_key(session_id), coupon_code, ex=CART_TTL)

    return {
        "status": "applied",
        "code": coupon_code,
        "type": coupon["type"],
        "value": coupon["value"],
        "description": coupon.get("description"),
    }
