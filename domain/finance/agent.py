from typing import Any, Dict, List
import re
from datetime import datetime, date
from sqlalchemy import func
from domain.finance.tools import finance_sql_read
from app.db import SessionLocal
from app.models.invoice import Invoice
from app.models.customer import Customer
from app.models.payment import Payment
from app.models.payment_allocation import PaymentAllocation

def wrap_table(headers: List[str], rows: List[List[Any]]) -> Dict[str, Any]:
    return {"type": "table", "headers": headers, "rows": rows}

def wrap_text(text: str) -> Dict[str, Any]:
    return {"type": "text", "content": text}

class FinanceAgent:
    def process_request(self, user_input: Any) -> Any:
        raw_input = getattr(user_input, "content", user_input)
        raw       = str(raw_input).strip()
        tl        = raw.lower()

        session = SessionLocal()
        try:
            if re.search(r"\bunpaid invoices\b", tl):
                invs = session.query(Invoice).join(Customer).order_by(Invoice.id).all()
                rows = []
                for inv in invs:
                    paid = sum(a.amount for a in inv.payments)
                    due  = inv.total_amount - paid
                    if due <= 0:
                        continue
                    status = (
                        "overdue" if inv.due_date < datetime.utcnow()
                        else "partial" if paid > 0
                        else "unpaid"
                    )
                    rows.append([
                        inv.invoice_number,
                        inv.customer.name,
                        inv.total_amount,
                        paid,
                        due,
                        status
                    ])
                return wrap_table(
                    ["Invoice #","Customer","Total","Paid","Due","Status"],
                    rows
                )

            if re.search(r"\bshow all invoices\b", tl):
                invs = session.query(Invoice).join(Customer).order_by(Invoice.id).all()
                rows = []
                for inv in invs:
                    paid = sum(a.amount for a in inv.payments)
                    due  = inv.total_amount - paid
                    status = (
                        "overdue" if inv.due_date < datetime.utcnow()
                        else "partial" if paid > 0 and due > 0
                        else "unpaid" if paid == 0
                        else "paid"
                    )
                    rows.append([
                        inv.invoice_number,
                        inv.customer.name,
                        inv.total_amount,
                        paid,
                        due,
                        status
                    ])
                return wrap_table(
                    ["Invoice #","Customer","Total","Paid","Due","Status"],
                    rows
                )

            m = re.search(r"show invoice\s+(\S+)\s+details", raw, re.I)
            if m:
                inv_no = m.group(1)
                inv = session.query(Invoice).filter(
                    func.lower(Invoice.invoice_number) == inv_no.lower()
                ).first()
                if not inv:
                    return wrap_text(f"Invoice {inv_no} not found.")
                rows = [
                    [
                        ln.description,
                        ln.quantity,
                        ln.unit_price,
                        ln.quantity * ln.unit_price
                    ]
                    for ln in inv.lines
                ]
                return wrap_table(
                    ["Description","Quantity","Unit Price","Line Total"],
                    rows
                )

            m = re.search(r"show payments for\s+(\S+)", raw, re.I)
            if m:
                inv_no = m.group(1)
                inv = session.query(Invoice).filter(
                    func.lower(Invoice.invoice_number) == inv_no.lower()
                ).first()
                if not inv:
                    return wrap_text(f"Invoice {inv_no} not found.")
                rows = [
                    [
                        alloc.payment.id,
                        alloc.payment.received_at.strftime("%Y-%m-%d %H:%M:%S"),
                        alloc.amount,
                        alloc.payment.method
                    ]
                    for alloc in inv.payments
                ]
                return wrap_table(
                    ["Payment ID","Date","Amount","Method"],
                    rows
                )

            m = re.search(r"show statement for customer\s+(\d+)", raw, re.I)
            if m:
                cust_id = int(m.group(1))
                cust    = session.get(Customer, cust_id)
                if not cust:
                    return wrap_text(f"Customer {cust_id} not found.")
                events = []
                for inv in cust.invoices:
                    events.append((inv.created_at, "Invoice", inv.invoice_number, inv.total_amount))
                for pay in session.query(Payment).filter(Payment.customer_id == cust_id).all():
                    events.append((pay.received_at, "Payment", f"#{pay.id}", -pay.amount))
                events.sort(key=lambda e: e[0])
                running = 0.0
                rows    = []
                for dt, kind, ref, amt in events:
                    running += amt
                    rows.append([
                        dt.strftime("%Y-%m-%d"),
                        kind,
                        ref,
                        amt,
                        running
                    ])
                return wrap_table(
                    ["Date","Type","Ref","Amount","Balance"],
                    rows
                )

            if re.search(r"\baging buckets\b", tl) or re.search(r"\baging report\b", tl):
                invs = session.query(Invoice).all()
                buckets = {"0-30 days": 0.0, "31-60 days": 0.0, "61+ days": 0.0}
                today = date.today()
                for inv in invs:
                    paid = sum(a.amount for a in inv.payments)
                    due  = inv.total_amount - paid
                    if due <= 0:
                        continue
                    age = (today - inv.due_date.date()).days
                    if age <= 30:
                        buckets["0-30 days"] += due
                    elif age <= 60:
                        buckets["31-60 days"] += due
                    else:
                        buckets["61+ days"] += due
                rows = [[bucket, amt] for bucket, amt in buckets.items()]
                return wrap_table(["Bucket","Total Due"], rows)

            if re.search(r"\bcash[- ]flow\b", tl):
                invs = session.query(Invoice).all()
                pays = session.query(Payment).all()
                flow = {}
                for inv in invs:
                    dt = inv.created_at.date().isoformat()
                    flow.setdefault(dt, [0.0, 0.0])[0] += inv.total_amount
                for pay in pays:
                    dt = pay.received_at.date().isoformat()
                    flow.setdefault(dt, [0.0, 0.0])[1] += pay.amount
                rows = []
                for dt in sorted(flow):
                    inv_amt, pay_amt = flow[dt]
                    rows.append([dt, inv_amt, pay_amt, pay_amt - inv_amt])
                return wrap_table(
                    ["Date","Total Invoiced","Total Paid","Net Cash Flow"],
                    rows
                )

        finally:
            session.close()

        result = finance_sql_read(raw)
        if isinstance(result, str):
            return wrap_text(result)
        if isinstance(result, list) and result and isinstance(result[0], (list, tuple)):
            return wrap_table([], result)
        return wrap_text(str(result))

    def write(self, user_input: Any) -> Any:
        raw_input = getattr(user_input, "content", user_input)
        raw       = str(raw_input).strip()
        tl        = raw.lower()

        if tl.startswith("record payment for"):
            session = SessionLocal()
            try:
                before, after = raw.split(":", 1)
                inv_no = before.strip().split()[-1]
                amt_str = after.strip()

                method_match = re.search(r"via\s+(.+)", amt_str, re.I)
                method = method_match.group(1).strip() if method_match else "manual"
                amt_clean = re.sub(r"via\s+.+", "", amt_str, flags=re.I).strip()
                amt = float(amt_clean)

                inv = session.query(Invoice).filter(
                    func.lower(Invoice.invoice_number) == inv_no.lower()
                ).first()
                if not inv:
                    return wrap_text(f"Invoice {inv_no} not found.")

                payment = Payment(
                    amount=amt,
                    method=method,
                    received_at=datetime.utcnow(),
                    customer_id=inv.customer_id
                )
                session.add(payment)
                session.flush()

                allocation = PaymentAllocation(
                    payment_id=payment.id,
                    invoice_id=inv.id,
                    amount=amt
                )
                session.add(allocation)
                session.commit()

                return wrap_text(f"Recorded payment of {amt:.2f} for invoice {inv_no} via {method}.")
            except Exception as e:
                session.rollback()
                return wrap_text(f"Error recording payment: {e}")
            finally:
                session.close()


