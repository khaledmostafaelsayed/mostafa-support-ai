"""Local tools for the customer-support demo. All records are fictional."""
from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def _load_orders() -> dict:
    with (DATA_DIR / "orders.json").open("r", encoding="utf-8") as file:
        return json.load(file)


def _load_faq() -> list[dict]:
    with (DATA_DIR / "faq.json").open("r", encoding="utf-8") as file:
        return json.load(file)


def lookup_order(order_id: str) -> dict:
    """Return a minimal safe view of a demo order."""
    order_id = (order_id or "").strip().upper().replace(" ", "-")
    orders = _load_orders()
    order = orders.get(order_id)
    if not order:
        return {"ok": False, "error": "Order not found in fictional demo data."}
    return {
        "ok": True,
        "order_id": order_id,
        "status": order["status"],
        "estimated_delivery": order.get("estimated_delivery"),
        "days_since_delivery": order.get("days_since_delivery"),
    }


def check_refund_eligibility(order_id: str) -> dict:
    """Check demo return-window eligibility; this never issues a refund."""
    order = lookup_order(order_id)
    if not order["ok"]:
        return order
    days = order.get("days_since_delivery")
    if order["status"].lower() != "delivered" or days is None:
        return {
            "ok": True,
            "order_id": order["order_id"],
            "eligible": False,
            "reason": "The demo order must be delivered before its return window can be checked.",
            "policy_days": 30,
        }
    eligible = int(days) <= 30
    reason = (
        f"Delivered {days} days ago, within the 30-day demo return window."
        if eligible else
        f"Delivered {days} days ago, outside the 30-day demo return window."
    )
    return {"ok": True, "order_id": order["order_id"], "eligible": eligible, "reason": reason, "days_since_delivery": int(days), "policy_days": 30}


def search_faq(question: str) -> dict:
    """Simple keyword FAQ retrieval for Arabic and English offline demos."""
    q = (question or "").lower()
    faq_items = _load_faq()
    best_item = None
    best_score = 0
    for item in faq_items:
        score = sum(1 for keyword in item["keywords"] if keyword.lower() in q)
        if score > best_score:
            best_item, best_score = item, score
    if best_item is None:
        return {"ok": False, "answer": None, "answer_ar": None, "error": "No matching FAQ found in demo data."}
    return {
        "ok": True,
        "topic": best_item["topic"],
        "topic_ar": best_item.get("topic_ar", best_item["topic"]),
        "answer": best_item["answer"],
        "answer_ar": best_item.get("answer_ar", best_item["answer"]),
    }
