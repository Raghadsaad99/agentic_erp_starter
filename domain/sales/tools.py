# domain/sales/tools.py
import sqlite3
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from core.config import DB_PATH
from services.text_to_sql import text_to_sql_tool
from services.sql import execute_query
from langchain.agents import Tool

def _conn():
    return sqlite3.connect(DB_PATH)

# ---------- Pydantic models for write actions ----------
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

# ---------- Core functions ----------
def sales_sql_read(nl_query: str):
    """Run sales-related natural language queries via text-to-SQL."""
    return text_to_sql_tool(nl_query)

def sales_sql_write(action: str, payload: Dict[str, Any]):
    """Perform sales-related write actions like creating leads or orders."""
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

# ---------- Extra helper functions for Sales ----------
def list_all_customers(_):
    rows = execute_query("SELECT id, name, email, phone FROM customers")
    return {"type": "table", "headers": ["id", "name", "email", "phone"], "rows": rows}

def count_customers(_):
    rows = execute_query("SELECT COUNT(*) FROM customers")
    count = rows[0][0] if rows else 0
    return {"type": "text", "content": f"We have {count} customers."}

def order_items_for_order(order_id: str):
    sql = "SELECT id, product_id, quantity, price FROM order_items WHERE order_id = ?"
    rows = execute_query(sql, (order_id,))
    return {"type": "table", "headers": ["id", "product_id", "quantity", "price"], "rows": rows}

# ---------- LangChain Tool list ----------
sales_tool_list = [
    Tool(name="List All Customers Tool", func=list_all_customers,
         description="List all customers with their ID, name, email, and phone."),
    Tool(name="Count Customers Tool", func=count_customers,
         description="Count the total number of customers."),
    Tool(name="Order Items For Order Tool", func=order_items_for_order,
         description="List all items for a given order ID."),
    Tool(name="Sales SQL Read Tool", func=sales_sql_read,
         description="Run SQL for sales-related questions not covered by other tools."),
    Tool(name="Sales SQL Write Tool", func=sales_sql_write,
         description="Perform sales write actions like creating leads or orders.")
]
