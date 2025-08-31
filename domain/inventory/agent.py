import re
from typing import Any, Dict, List
from services.sql import execute_query
from domain.inventory.tools import inventory_sql_read, inventory_sql_write

RECEIVE_REGEX = re.compile(
    r"receive\s+(\d+)\s+(?:units?|pcs?|pieces?)\s+(?:of\s+)?(?:product|item)\s+(\d+)",
    re.IGNORECASE
)

def wrap_table(headers: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
    return {"type": "table", "headers": headers, "rows": rows}

def wrap_text(text: str) -> Dict[str, Any]:
    return {"type": "text", "content": text}

class InventoryAgent:
    def __init__(self, tools=None):
        self.tools = tools

    def process_request(self, prompt: str) -> Dict[str, Any]:
        text = prompt.strip()

        # Detect a "receive" command
        if RECEIVE_REGEX.search(text):
            return self.write(prompt)

        # Check stock levels
        if any(k in text.lower() for k in ["check stock levels", "inventory", "stock"]):
            rows = execute_query(
                "SELECT s.product_id, p.name, s.qty_on_hand AS on_hand, s.reorder_point "
                "FROM stock s JOIN products p ON s.product_id = p.id"
            )
            return wrap_table(
                ["Product ID", "Product Name", "Qty On Hand", "Reorder Point"], rows
            )

        # Fallback to legacy SQL read
        rows = inventory_sql_read(prompt)
        if isinstance(rows, str):
            return wrap_text(rows)
        if isinstance(rows, list) and rows and isinstance(rows[0], (list, tuple)):
            return wrap_table([], rows)

        # Fallback to LLM if tools available
        if self.tools and hasattr(self.tools, "inventory_sql_chain"):
            try:
                sql = self.tools.prompt_to_sql(prompt, self.tools.inventory_sql_chain)
                rows = execute_query(sql)
                headers = self.tools.infer_headers(sql) if hasattr(self.tools, "infer_headers") else []
                return wrap_table(headers, rows)
            except Exception:
                return wrap_text("Sorry, I couldn't process that inventory request.")

        return wrap_text("Could not process inventory request.")

    def write(self, prompt: str) -> Dict[str, Any]:
        text = prompt.strip()

        # Create PO
        if "create po" in text.lower() or "new po" in text.lower():
            res = inventory_sql_write("create_po", {
                "supplier_id": 1,
                "items": [{"product_id": 1, "quantity": 100, "unit_cost": 8.5}],
            })
            return wrap_text(f"PO created: {res}")

        # Receive <qty> units of product <id>
        m = RECEIVE_REGEX.search(text)
        if m:
            qty, pid = int(m.group(1)), int(m.group(2))
            execute_query(
                "INSERT INTO stock_movements(product_id, change_qty, reason, created_at) "
                "VALUES(?,?,?,datetime('now'))",
                (pid, qty, 'receipt')
            )
            execute_query(
                "UPDATE stock SET qty_on_hand = qty_on_hand + ? WHERE product_id = ?",
                (qty, pid)
            )
            return wrap_text(f"Received {qty} units of product {pid}.")

        # Fallback to legacy SQL write
        res = inventory_sql_write(prompt)
        if res:
            return wrap_text(str(res))

        # Fallback to LLM write if available
        if self.tools and hasattr(self.tools, "inventory_sql_chain"):
            try:
                sql = self.tools.prompt_to_sql(prompt, self.tools.inventory_sql_chain)
                rows = execute_query(sql)
                headers = self.tools.infer_headers(sql) if hasattr(self.tools, "infer_headers") else []
                return wrap_table(headers, rows)
            except Exception:
                return wrap_text("Sorry, I couldn't process that inventory write request.")

        return wrap_text("Could not parse inventory write action.")
