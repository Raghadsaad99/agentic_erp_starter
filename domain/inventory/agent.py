# domain/inventory/agent.py
from langchain.agents import Tool
from services.text_to_sql import text_to_sql_tool
from services.sql import execute_query
import sqlite3
from typing import Any, Dict, List
from pydantic import BaseModel
from core.config import DB_PATH

def _conn():
    return sqlite3.connect(DB_PATH)

class CreatePOInput(BaseModel):
    supplier_id: int
    items: List[Dict[str, float]]

class ReceivePOInput(BaseModel):
    po_id: int
    product_id: int
    received_qty: float

def inventory_sql_read(nl_query: str):
    return text_to_sql_tool(nl_query)

def inventory_sql_write(action: str, payload: Dict[str, Any]):
    with _conn() as conn:
        if action == "create_po":
            data = CreatePOInput(**payload)
            cur = conn.execute("INSERT INTO purchase_orders (supplier_id, status, created_at) VALUES (?, 'draft', datetime('now'))", (data.supplier_id,))
            po_id = cur.lastrowid
            total = 0.0
            for it in data.items:
                total += float(it["quantity"]) * float(it["unit_cost"])
                conn.execute("INSERT INTO po_items (po_id, product_id, quantity, unit_cost) VALUES (?, ?, ?, ?)",
                             (po_id, it["product_id"], float(it["quantity"]), float(it["unit_cost"])))
            return {"po_id": po_id, "total": total, "status": "draft"}
        if action == "receive_po":
            data = ReceivePOInput(**payload)
            conn.execute("INSERT INTO po_receipts (po_id, product_id, received_qty, received_at) VALUES (?, ?, ?, datetime('now'))",
                         (data.po_id, data.product_id, float(data.received_qty)))
            conn.execute("UPDATE stock SET qty_on_hand = qty_on_hand + ? WHERE product_id = ?",
                         (float(data.received_qty), data.product_id))
            conn.execute("INSERT INTO stock_movements (product_id, change_qty, reason, ref_id, created_at) VALUES (?, ?, 'purchase', ?, datetime('now'))",
                         (data.product_id, float(data.received_qty), data.po_id))
            return {"po_id": data.po_id, "product_id": data.product_id, "received_qty": data.received_qty}
    return {"error": "unknown_action"}

def get_stock_levels():
    return {"type": "table", "headers": ["Product ID", "Qty On Hand", "Reorder Point"],
            "rows": execute_query("SELECT product_id, qty_on_hand, reorder_point FROM stock")}

def log_stock_movement(product_id: int, change: int, reason: str, ref_id: int):
    return execute_query("INSERT INTO stock_movements (product_id, change_qty, reason, ref_id, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
                         (product_id, change, reason, ref_id))

inventory_tool_list = [
    Tool(name="Inventory SQL Read Tool", func=inventory_sql_read, description="Run SQL queries for inventory-related questions."),
    Tool(name="Inventory SQL Write Tool", func=inventory_sql_write, description="Perform inventory write actions like creating purchase orders or receiving stock."),
    Tool(name="Get Stock Levels Tool", func=lambda _: get_stock_levels(), description="List current stock levels for all products."),
    Tool(name="Log Stock Movement Tool", func=lambda args: log_stock_movement(**args), description="Log a stock movement for a given product.")
]
