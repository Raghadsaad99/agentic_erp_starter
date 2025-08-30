# domain/inventory/agent.py
import re
from typing import Any, Dict, List
from services.sql import execute_query
from domain.inventory.tools import inventory_sql_read, inventory_sql_write

def wrap_table(headers: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
    return {"type": "table", "headers": headers, "rows": rows}

def wrap_text(text: str) -> Dict[str, Any]:
    return {"type": "text", "content": text}

class InventoryAgent:
    def __init__(self, tools=None):
        self.tools = tools

    def process_request(self, prompt: str) -> Dict[str, Any]:
        text = prompt.strip()

        # 🔹 Detect a "receive" command and forward to write()
        if re.search(
            r"receive\s+\d+\s+(?:units?|pcs?|pieces?)\s+(?:of\s+)?(?:product|item)\s+\d+",
            text,
            re.IGNORECASE
        ):
            return self.write(prompt)

        # 1️⃣ Check stock levels
        if "check stock levels" in text.lower() or "inventory" in text.lower() or "stock" in text.lower():
            rows = execute_query(
                "SELECT s.product_id, p.name, s.qty_on_hand AS on_hand, s.reorder_point "
                "FROM stock s JOIN products p ON s.product_id = p.id"
            )
            return wrap_table(
                ["Product ID", "Product Name", "Qty On Hand", "Reorder Point"], rows
            )

        # 2️⃣ Fallback to legacy SQL read
        rows = inventory_sql_read(prompt)
        if isinstance(rows, str):
            return wrap_text(rows)
        if isinstance(rows, list) and rows and isinstance(rows[0], (list, tuple)):
            return wrap_table([], rows)

        # 3️⃣ Fallback to LLM if tools are available
        if self.tools and hasattr(self.tools, "inventory_sql_chain"):
            try:
                sql = self.tools.prompt_to_sql(prompt, self.tools.inventory_sql_chain)
                rows = execute_query(sql)
                headers = self.tools.infer_headers(sql) if hasattr(self.tools, "infer_headers") else []
                return wrap_table(headers, rows)
            except Exception as e:
                return wrap_text(f"Error generating SQL via LLM: {e}")

        return wrap_text("Could not process inventory request.")

    def write(self, prompt: str) -> Dict[str, Any]:
        text = prompt.strip()

        # 1️⃣ Create PO
        if "create po" in text.lower() or "new po" in text.lower():
            res = inventory_sql_write("create_po", {
                "supplier_id": 1,
                "items": [{"product_id": 1, "quantity": 100, "unit_cost": 8.5}],
            })
            return wrap_text(f"PO created: {res}")

        # 2️⃣ Receive <qty> units of product <id>
        m = re.search(
            r"receive\s+(\d+)\s+(?:units?|pcs?|pieces?)\s+(?:of\s+)?(?:product|item)\s+(\d+)",
            text,
            re.IGNORECASE
        )
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

        # 3️⃣ Fallback to legacy SQL write
        res = inventory_sql_write(prompt)
        if res:
            return wrap_text(str(res))

        # 4️⃣ Fallback to LLM write if available
        if self.tools and hasattr(self.tools, "inventory_sql_chain"):
            try:
                sql = self.tools.prompt_to_sql(prompt, self.tools.inventory_sql_chain)
                rows = execute_query(sql)
                headers = self.tools.infer_headers(sql) if hasattr(self.tools, "infer_headers") else []
                return wrap_table(headers, rows)
            except Exception as e:
                return wrap_text(f"Error generating SQL via LLM: {e}")

        return wrap_text("Could not parse inventory write action.")
