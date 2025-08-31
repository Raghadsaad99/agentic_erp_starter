import sqlite3
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from core.config import DB_PATH
from services.text_to_sql import text_to_sql_tool
from services.sql import execute_query


def _conn():
    return sqlite3.connect(DB_PATH)


class CreateInvoiceInput(BaseModel):
    customer_id: int
    invoice_number: str
    lines: List[Dict[str, Any]]  # [{description, quantity, unit_price}]
    status: str = Field(default="unpaid")


class RecordPaymentInput(BaseModel):
    customer_id: int
    amount: float
    method: str = "bank_transfer"
    allocations: List[Dict[str, Any]] = Field(default_factory=list)  # [{invoice_id, amount}]


def finance_sql_read(nl_query: str):
    return text_to_sql_tool(nl_query)


def finance_sql_write(action: str, payload: Dict[str, Any]):
    with _conn() as conn:
        if action == "create_invoice":
            data = CreateInvoiceInput(**payload)
            total = sum(float(l["quantity"]) * float(l["unit_price"]) for l in data.lines)
            cur = conn.execute(
                """
                INSERT INTO invoices (customer_id, invoice_number, issue_date, due_date, total_amount, status, created_at)
                VALUES (?, ?, date('now'), date('now','+30 day'), ?, ?, datetime('now'))
                """,
                (data.customer_id, data.invoice_number, total, data.status),
            )
            invoice_id = cur.lastrowid
            for l in data.lines:
                conn.execute(
                    "INSERT INTO invoice_lines (invoice_id, description, quantity, unit_price) VALUES (?, ?, ?, ?)",
                    (invoice_id, l["description"], float(l["quantity"]), float(l["unit_price"])),
                )
            return {"invoice_id": invoice_id, "total_amount": total, "status": data.status}

        if action == "post_payment":
            data = RecordPaymentInput(**payload)
            cur = conn.execute(
                "INSERT INTO payments (customer_id, amount, method, received_at) VALUES (?, ?, ?, datetime('now'))",
                (data.customer_id, float(data.amount), data.method),
            )
            payment_id = cur.lastrowid
            for alloc in data.allocations:
                conn.execute(
                    "INSERT INTO payment_allocations (payment_id, invoice_id, amount) VALUES (?, ?, ?)",
                    (payment_id, alloc["invoice_id"], float(alloc["amount"])),
                )
            return {"payment_id": payment_id, "status": "posted"}

    return {"error": "unknown_action"}


# ---------- Invoice helpers ----------

def get_unpaid_invoices():
    rows = execute_query("""
        SELECT 
            id AS invoice_id,
            (SELECT name FROM customers WHERE customers.id = invoices.customer_id) AS customer,
            invoice_number,
            total_amount,
            status
        FROM invoices
        WHERE status = 'unpaid'
        ORDER BY due_date ASC
    """)
    headers = ["Invoice ID", "Customer", "Invoice #", "Amount", "Status"]
    return {"type": "table", "headers": headers, "rows": rows}


def get_paid_invoices():
    rows = execute_query("""
        SELECT 
            id AS invoice_id,
            (SELECT name FROM customers WHERE customers.id = invoices.customer_id) AS customer,
            invoice_number,
            total_amount,
            status
        FROM invoices
        WHERE status = 'paid'
        ORDER BY issue_date DESC
    """)
    headers = ["Invoice ID", "Customer", "Invoice #", "Amount", "Status"]
    return {"type": "table", "headers": headers, "rows": rows}


def get_cancelled_invoices():
    rows = execute_query("""
        SELECT 
            id AS invoice_id,
            (SELECT name FROM customers WHERE customers.id = invoices.customer_id) AS customer,
            invoice_number,
            total_amount,
            status
        FROM invoices
        WHERE status = 'cancelled'
        ORDER BY issue_date DESC
    """)
    headers = ["Invoice ID", "Customer", "Invoice #", "Amount", "Status"]
    return {"type": "table", "headers": headers, "rows": rows}


def get_all_invoices():
    rows = execute_query("""
        SELECT 
            id AS invoice_id,
            (SELECT name FROM customers WHERE customers.id = invoices.customer_id) AS customer,
            invoice_number,
            total_amount,
            status
        FROM invoices
        ORDER BY issue_date DESC
    """)
    headers = ["Invoice ID", "Customer", "Invoice #", "Amount", "Status"]
    return {"type": "table", "headers": headers, "rows": rows}


def get_invoices_by_customer(customer_name: str):
    rows = execute_query("""
        SELECT 
            i.id AS invoice_id,
            c.name AS customer,
            i.invoice_number,
            i.total_amount,
            i.status
        FROM invoices i
        JOIN customers c ON c.id = i.customer_id
        WHERE c.name = ?
        ORDER BY i.issue_date DESC
    """, (customer_name,))
    headers = ["Invoice ID", "Customer", "Invoice #", "Amount", "Status"]
    return {"type": "table", "headers": headers, "rows": rows}
