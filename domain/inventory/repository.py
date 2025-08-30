# domain/inventory/repository.py
from services.sql import execute_query

def get_stock_levels():
    return execute_query("SELECT product_id, qty_on_hand, reorder_point FROM stock")

def log_stock_movement(product_id: int, change: int, reason: str, ref_id: int):
    q = """
    INSERT INTO stock_movements (product_id, change_qty, reason, ref_id, created_at)
    VALUES (?, ?, ?, ?, datetime('now'))
    """
    return execute_query(q, (product_id, change, reason, ref_id))
