# domain/finance/agent.py
import re
from datetime import datetime, date
from typing import Any, Dict, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.invoice import Invoice
from app.models.customer import Customer

# --- Config ---
DEBUG = False  # Set to True for skip reasons in console
CURRENCY_SYMBOL = "AED"

STATUS_COLORS = {
    "overdue": "🔴 overdue",
    "partial": "🟠 partial",
    "unpaid": "🟡 unpaid",
    "paid": "🟢 paid",
    "cancelled": "⚪ cancelled"
}

# --- Helpers to wrap output ---
def wrap_table(headers: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
    return {"type": "table", "headers": headers, "rows": rows}

def wrap_text(text: str) -> Dict[str, Any]:
    return {"type": "text", "content": text}

# --- Formatting helpers ---
def _fmt_currency(value: float, symbol: str = CURRENCY_SYMBOL) -> str:
    return f"{symbol} {value:,.2f}"

# --- Invoice field helpers ---
def _safe_customer_name(inv: Invoice) -> str:
    try:
        return inv.customer.name if inv.customer else "Unknown"
    except Exception:
        return "Unknown"

def _invoice_total(inv: Invoice) -> float:
    total = inv.total_amount or 0.0
    if total <= 0 and getattr(inv, "lines", None):
        try:
            total = sum((ln.quantity or 0) * (ln.unit_price or 0.0) for ln in inv.lines)
        except Exception:
            pass
    return float(total or 0.0)

def _invoice_paid(inv: Invoice) -> float:
    try:
        allocations = inv.payments or []
        return float(sum(getattr(a, "amount", 0.0) or 0.0 for a in allocations))
    except Exception:
        return 0.0

def _is_overdue(inv: Invoice) -> bool:
    if not inv.due_date:
        return False
    try:
        inv_due_date = inv.due_date.date() if isinstance(inv.due_date, datetime) else inv.due_date
        return inv_due_date < date.today()
    except Exception:
        return False

# --- Main Finance Agent ---
class FinanceAgent:
    def process_request(self, user_input: Any) -> Dict[str, Any]:
        raw_input = getattr(user_input, "content", user_input)
        raw = str(raw_input).strip()
        tl  = raw.lower()

        session: Session = SessionLocal()
        try:
            # 🔹 Unpaid invoices
            if re.search(r"\bunpaid\b", tl) and re.search(r"\binvoices?\b", tl):
                invs = session.query(Invoice).order_by(Invoice.id).all()
                rows: List[List[Any]] = []
                for inv in invs:
                    total = _invoice_total(inv)
                    paid  = _invoice_paid(inv)
                    due   = round(total - paid, 2)
                    if due > 0 and _is_overdue(inv):
                        status = "overdue"
                    elif paid > 0 and due > 0:
                        status = "partial"
                    elif paid >= total and total > 0:
                        status = "paid"
                    else:
                        status = "unpaid"
                    if status in ["unpaid", "overdue", "partial"]:
                        rows.append([
                            inv.invoice_number,
                            _safe_customer_name(inv),
                            _fmt_currency(total),
                            _fmt_currency(paid),
                            _fmt_currency(max(due, 0.0)),
                            STATUS_COLORS.get(status, status)
                        ])
                return wrap_table(["Invoice #","Customer","Total","Paid","Due","Status"], rows)

            # 🔹 Paid invoices
            if re.search(r"\bpaid\b", tl) and re.search(r"\binvoices?\b", tl) and "unpaid" not in tl:
                invs = session.query(Invoice).order_by(Invoice.id).all()
                rows: List[List[Any]] = []
                for inv in invs:
                    total = _invoice_total(inv)
                    paid  = _invoice_paid(inv)
                    due   = round(total - paid, 2)
                    if paid >= total and total > 0:
                        status = "paid"
                        rows.append([
                            inv.invoice_number,
                            _safe_customer_name(inv),
                            _fmt_currency(total),
                            _fmt_currency(paid),
                            _fmt_currency(max(due, 0.0)),
                            STATUS_COLORS.get(status, status)
                        ])
                return wrap_table(["Invoice #","Customer","Total","Paid","Due","Status"], rows)

            # 🔹 Cancelled invoices
            if re.search(r"\bcancel+?ed\b", tl) and re.search(r"\binvoices?\b", tl):
                invs = session.query(Invoice).order_by(Invoice.id).all()
                rows: List[List[Any]] = []
                for inv in invs:
                    if (inv.status or "").lower() == "cancelled":
                        total = _invoice_total(inv)
                        paid  = _invoice_paid(inv)
                        due   = round(total - paid, 2)
                        rows.append([
                            inv.invoice_number,
                            _safe_customer_name(inv),
                            _fmt_currency(total),
                            _fmt_currency(paid),
                            _fmt_currency(due),
                            STATUS_COLORS.get("cancelled", "cancelled")
                        ])
                return wrap_table(["Invoice #","Customer","Total","Paid","Due","Status"], rows)

            # 🔹 All invoices
            if re.search(r"\b(show|list|display)\s+all\s+invoices\b", tl):
                invs = session.query(Invoice).order_by(Invoice.id).all()
                rows: List[List[Any]] = []
                for inv in invs:
                    total = _invoice_total(inv)
                    paid  = _invoice_paid(inv)
                    due   = round(total - paid, 2)
                    if due > 0 and _is_overdue(inv):
                        status = "overdue"
                    elif paid > 0 and due > 0:
                        status = "partial"
                    elif paid >= total and total > 0:
                        status = "paid"
                    else:
                        status = "unpaid"
                    rows.append([
                        inv.invoice_number,
                        _safe_customer_name(inv),
                        _fmt_currency(total),
                        _fmt_currency(paid),
                        _fmt_currency(max(due, 0.0)),
                        STATUS_COLORS.get(status, status)
                    ])
                return wrap_table(["Invoice #","Customer","Total","Paid","Due","Status"], rows)

            # 🔹 Invoices by customer name (case-insensitive LIKE match, no skipping)
            m = re.search(
                r"(?:show|list|display)?\s*invoices\s+for\s+customer\s+[\"']?(.+?)[\"']?$",
                raw,
                re.I
            )
            if m:
                cust_name = m.group(1).strip()
                invs = (
                    session.query(Invoice)
                    .join(Customer, isouter=True)
                    .filter(func.lower(Customer.name).like(f"%{cust_name.lower()}%"))
                    .order_by(Invoice.id)
                    .all()
                )
                rows: List[List[Any]] = []
                for inv in invs:
                    total = _invoice_total(inv)
                    paid  = _invoice_paid(inv)
                    due   = round(total - paid, 2)
                    if due > 0 and _is_overdue(inv):
                        status = "overdue"
                    elif paid > 0 and due > 0:
                        status = "partial"
                    elif paid >= total and total > 0:
                        status = "paid"
                    else:
                        status = "unpaid"
                    rows.append([
                        inv.invoice_number,
                        _safe_customer_name(inv),
                        _fmt_currency(total),
                        _fmt_currency(paid),
                        _fmt_currency(max(due, 0.0)),
                        STATUS_COLORS.get(status, status)
                    ])
                return wrap_table(["Invoice #","Customer","Total","Paid","Due","Status"], rows)

            # Default
            return wrap_text("Sorry, I could not understand your request.")

        finally:
            session.close()
