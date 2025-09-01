# domain/sales/tools.py
import sqlite3
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from core.config import DB_PATH
from services.text_to_sql import text_to_sql_tool

def _conn():
    return sqlite3.connect(DB_PATH)

class CreateLeadInput(BaseModel):
    customer_name: str
    contact_email: str
    message: str = ""
    score: float = 0.0
    status: str = Field(default="new")

class CreateOrderInput(BaseModel):
    customer_id: int
    items: List[Dict[str, Any]]  # [{product_id, quantity, price}]
    status: str = "pending"

def sales_sql_read(nl_query: str):
    return text_to_sql_tool(nl_query)

def sales_sql_write(action: str, payload: Dict[str, Any]):
    if action == "create_lead":
        data = CreateLeadInput(**payload)
        with _conn() as conn:
            cur = conn.execute(
                """
                INSERT INTO leads (customer_name, contact_email, message, score, status, created_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'))
                """,
                (data.customer_name, data.contact_email, data.message, data.score, data.status),
            )
            return {"lead_id": cur.lastrowid, "status": "created"}

    if action == "create_order":
        data = CreateOrderInput(**payload)
        with _conn() as conn:
            cur = conn.execute(
                "INSERT INTO orders (customer_id, total, status, created_at) VALUES (?, 0, ?, datetime('now'))",
                (data.customer_id, data.status),
            )
            order_id = cur.lastrowid
            total = 0.0
            for it in data.items:
                qty = float(it["quantity"])
                price = float(it["price"])
                total += qty * price
                conn.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                    (order_id, it["product_id"], qty, price),
                )
            conn.execute("UPDATE orders SET total = ? WHERE id = ?", (total, order_id))
            return {"order_id": order_id, "total": total, "status": "created"}

    return {"error": "unknown_action"}
