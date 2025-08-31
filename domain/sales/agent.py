import re
from typing import Any, Dict, List

from services.sql import execute_query
from services.text_to_sql import text_to_sql_tool
from domain.finance.tools import (
    get_unpaid_invoices,
    get_paid_invoices,
    get_cancelled_invoices,
    get_all_invoices,
    get_invoices_by_customer
)

def wrap_table(headers: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
    return {"type": "table", "headers": headers, "rows": rows}

def wrap_text(text: str) -> Dict[str, Any]:
    return {"type": "text", "content": text}

class SalesAgent:
    def __init__(self, tools=None):
        self.tools = tools

    def process_request(self, prompt: str) -> Dict[str, Any]:
        text = prompt.lower().strip()

        # Customers
        if "list all customers" in text:
            rows = execute_query("SELECT id, name, email, phone FROM customers")
            return wrap_table(["id", "name", "email", "phone"], rows)

        if re.search(r"\bhow many customers\b", text):
            rows = execute_query("SELECT COUNT(*) FROM customers")
            count = rows[0][0] if rows else 0
            return wrap_text(f"We have {count} customers.")

        # Orders
        m = re.search(r"order items for order (\d+)", text)
        if m:
            order_id = m.group(1)
            sql = (
                "SELECT id, product_id, quantity, price "
                "FROM order_items WHERE order_id = ?"
            )
            rows = execute_query(sql, (order_id,))
            return wrap_table(["id", "product_id", "quantity", "price"], rows)

        # Invoices
        if re.search(r"\bunpaid\b", text) and "invoice" in text:
            return get_unpaid_invoices()

        if re.search(r"\bpaid\b", text) and "invoice" in text and "unpaid" not in text:
            return get_paid_invoices()

        if re.search(r"\bcancelled\b", text) and "invoice" in text:
            return get_cancelled_invoices()

        if "all invoices" in text:
            return get_all_invoices()

        m = re.search(r"invoices for customer '(.+)'", text)
        if m:
            customer_name = m.group(1)
            return get_invoices_by_customer(customer_name)

        # Fallback
        try:
            return text_to_sql_tool(prompt)
        except Exception:
            return wrap_text("Sorry, I couldn't process that sales request.")
