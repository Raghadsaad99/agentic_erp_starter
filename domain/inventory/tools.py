# domain/inventory/tools.py
import sqlite3
from typing import Any, Dict, List
from pydantic import BaseModel
from core.config import DB_PATH
from services.text_to_sql import text_to_sql_tool
from services.sql import execute_query

def _conn():
    """Open a direct SQLite connection to the ERP database."""
    return sqlite3.connect(DB_PATH)

class CreatePOInput(BaseModel):
    supplier_id: int
    items: List[Dict[str, float]]  # [{product_id, quantity, unit_cost}]

class ReceivePOInput(BaseModel):
    po_id: int
    product_id: int
    received_qty: float

def inventory_sql_read(nl_query: str):
    """Run a natural-language inventory query via the text-to-SQL tool."""
    return text_to_sql_tool(nl_query)

def inventory_sql_write(action: str, payload: Dict[str, Any]):
    """Perform a write action on inventory-related tables."""
    with _conn() as conn:
        if action == "create_po":
            data = CreatePOInput(**payload)
            cur = conn.execute(
                """
                INSERT INTO purchase_orders (supplier_id, status, created_at)
                VALUES (?, 'draft', datetime('now'))
                """,
                (data.supplier_id,),
            )
            po_id = cur.lastrowid
            total = 0.0
            for it in data.items:
                total += float(it["quantity"]) * float(it["unit_cost"])
                conn.execute(
                    """
                    INSERT INTO po_items (po_id, product_id, quantity, unit_cost)
                    VALUES (?, ?, ?, ?)
                    """,
                    (po_id, it["product_id"], float(it["quantity"]), float(it["unit_cost"])),
                )
            return {"po_id": po_id, "total": total, "status": "draft"}

        if action == "receive_po":
            data = ReceivePOInput(**payload)
            # Record receipt
            conn.execute(
                """
                INSERT INTO po_receipts (po_id, product_id, received_qty, received_at)
                VALUES (?, ?, ?, datetime('now'))
                """,
                (data.po_id, data.product_id, float(data.received_qty)),
            )
            # Update stock levels
            conn.execute(
                """
                UPDATE stock
                SET qty_on_hand = qty_on_hand + ?
                WHERE product_id = ?
                """,
                (float(data.received_qty), data.product_id),
            )
            # Log stock movement
            conn.execute(
                """
                INSERT INTO stock_movements (product_id, change_qty, reason, ref_id, created_at)
                VALUES (?, ?, 'purchase', ?, datetime('now'))
                """,
                (data.product_id, float(data.received_qty), data.po_id),
            )
            return {
                "po_id": data.po_id,
                "product_id": data.product_id,
                "received_qty": data.received_qty
            }

    return {"error": "unknown_action"}

def get_stock_levels():
    """Return current stock levels from the stock table."""
    return execute_query(
        "SELECT product_id, qty_on_hand, reorder_point FROM stock"
    )

def log_stock_movement(product_id: int, change: int, reason: str, ref_id: int):
    """Insert a stock movement record."""
    q = """
    INSERT INTO stock_movements (product_id, change_qty, reason, ref_id, created_at)
    VALUES (?, ?, ?, ?, datetime('now'))
    """
    return execute_query(q, (product_id, change, reason, ref_id))

