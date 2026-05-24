"""Order tools backed by Valkey.

Data model:
  order:{order_id}     -> JSON document for the placed order
  user_orders:{user}   -> sorted set of order ids scored by created_at timestamp
  order_counter        -> integer counter used to generate order ids
"""
import json
import time
import uuid

from valkey_client import r
from tools.cart_tools import _coupon_key, _get_coupon, clear_cart, get_cart


def _calculate_discount(subtotal: int, coupon: dict | None) -> tuple[int, dict | None]:
    """Returns (discount_amount, coupon_summary)."""
    if not coupon or not coupon.get("active"):
        return 0, None
    if subtotal < int(coupon.get("min_order", 0)):
        return 0, None

    if coupon["type"] == "percentage":
        discount = int(subtotal * int(coupon["value"]) / 100)
    elif coupon["type"] == "fixed":
        discount = min(int(coupon["value"]), subtotal)
    else:
        discount = 0

    return discount, {
        "code": coupon["code"],
        "type": coupon["type"],
        "value": coupon["value"],
    }


def get_cart_total(session_id: str) -> dict:
    """Get cart total with any discount applied."""
    cart = get_cart(session_id)
    subtotal = cart["subtotal"]

    code = r.get(_coupon_key(session_id))
    coupon = _get_coupon(code) if code else None
    discount, coupon_summary = _calculate_discount(subtotal, coupon)

    return {
        "subtotal": subtotal,
        "discount": discount,
        "total": max(subtotal - discount, 0),
        "items": cart["items"],
        "item_count": cart["item_count"],
        "coupon": coupon_summary,
    }


def place_order(session_id: str, user_id: str = "guest") -> dict:
    """Place the order for all items in cart."""
    totals = get_cart_total(session_id)
    if not totals["items"]:
        return {"status": "empty_cart", "message": "Cart is empty"}

    # Re-check stock and decrement atomically per product.
    for item in totals["items"]:
        raw = r.execute_command("JSON.GET", item["product_id"])
        if not raw:
            return {
                "status": "product_unavailable",
                "product_id": item["product_id"],
                "message": "Product no longer exists",
            }
        product = json.loads(raw)
        if int(product.get("stock", 0)) < item["quantity"]:
            return {
                "status": "out_of_stock",
                "product_id": item["product_id"],
                "product_name": item["name"],
                "available": int(product.get("stock", 0)),
                "requested": item["quantity"],
            }

    created_at = int(time.time())
    order_seq = r.incr("order_counter")
    order_id = f"order:{order_seq:05d}-{uuid.uuid4().hex[:6]}"

    order_doc = {
        "id": order_id,
        "user_id": user_id,
        "session_id": session_id,
        "items": totals["items"],
        "subtotal": totals["subtotal"],
        "discount": totals["discount"],
        "total": totals["total"],
        "coupon": totals["coupon"],
        "status": "confirmed",
        "created_at": created_at,
    }

    r.execute_command("JSON.SET", order_id, "$", json.dumps(order_doc))
    r.zadd(f"user_orders:{user_id}", {order_id: created_at})

    # Decrement stock for each item.
    for item in totals["items"]:
        r.execute_command(
            "JSON.NUMINCRBY", item["product_id"], "$.stock", -item["quantity"]
        )

    clear_cart(session_id)

    return {
        "status": "order_placed",
        "order_id": order_id,
        "total": totals["total"],
        "subtotal": totals["subtotal"],
        "discount": totals["discount"],
        "item_count": totals["item_count"],
    }


def get_order_history(user_id: str) -> dict:
    """Get past orders for a user."""
    order_ids = r.zrevrange(f"user_orders:{user_id}", 0, 19)
    orders = []
    for oid in order_ids:
        raw = r.execute_command("JSON.GET", oid)
        if raw:
            doc = json.loads(raw)
            orders.append({
                "order_id": doc["id"],
                "total": doc["total"],
                "status": doc["status"],
                "item_count": sum(i["quantity"] for i in doc["items"]),
                "created_at": doc["created_at"],
            })
    return {"orders": orders, "count": len(orders)}


def get_order_status(order_id: str) -> dict:
    """Get the status of a specific order."""
    raw = r.execute_command("JSON.GET", order_id)
    if not raw:
        return {"status": "not_found", "order_id": order_id}
    doc = json.loads(raw)
    return {
        "order_id": doc["id"],
        "status": doc["status"],
        "total": doc["total"],
        "items": doc["items"],
        "created_at": doc["created_at"],
    }
