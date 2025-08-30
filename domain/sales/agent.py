import re
from typing import Any, Dict, List

from services.sql import execute_query
from services.text_to_sql import text_to_sql_tool   # <-- updated import
from app.db import SessionLocal
from app.models.customer import Customer
from app.models.order import Order
from app.models.order_item import OrderItem


def wrap_table(headers: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
    return {"type": "table", "headers": headers, "rows": rows}


def wrap_text(text: str) -> Dict[str, Any]:
    return {"type": "text", "content": text}


class SalesAgent:
    def __init__(self, tools=None):
        # tools can contain LLM chains, header inference, etc.
        self.tools = tools

    def process_request(self, prompt: str) -> Dict[str, Any]:
        text = prompt.lower().strip()

        # 1️⃣ List all customers
        if "list all customers" in text:
            rows = execute_query("SELECT id, name, email, phone FROM customers")
            return wrap_table(["id", "name", "email", "phone"], rows)

        # 2️⃣ How many customers?
        if re.search(r"\bhow many customers\b", text):
            rows = execute_query("SELECT COUNT(*) FROM customers")
            count = rows[0][0] if rows else 0
            return wrap_text(f"We have {count} customers.")

        # 3️⃣ Show order items for order <id>
        m = re.search(r"order items for order (\d+)", text)
        if m:
            order_id = m.group(1)
            sql = (
                "SELECT id, product_id, quantity, unit_price "
                "FROM order_items WHERE order_id = ?"
            )
            rows = execute_query(sql, (order_id,))
            return wrap_table(["id", "product_id", "quantity", "unit_price"], rows)

        # 4️⃣ Fallback → SQL‐tool (text_to_sql_tool)
        #    This returns either a table payload or a text/error payload
        try:
            result = text_to_sql_tool(prompt)
            return result
        except Exception as e:
            return wrap_text(f"Error generating or running fallback SQL: {e}")

        # If nothing matched, generic fallback
        # (this line is actually unreachable due to the try/except above)
        # return wrap_text("Could not understand or process the request.")
