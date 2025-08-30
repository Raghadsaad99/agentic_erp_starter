
# seed_invoices.py
from datetime import datetime
from sqlalchemy.orm import Session
from app.db import SessionLocal, engine, Base

import app.models.customer
import app.models.invoice
import app.models.invoice_line
import app.models.payment
import app.models.payment_allocation

from app.models.invoice            import Invoice
from app.models.invoice_line       import InvoiceLine
from app.models.payment            import Payment
from app.models.payment_allocation import PaymentAllocation

def seed_invoices():
    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        # ─── Sample Invoices & Lines ───
        sample_invoices = [
            {
                "customer_id": 1,
                "invoice_number": "INV-001",
                "due_date": "2025-09-30",
                "total_amount": 100.0,
                "status": "unpaid",
                "lines": [
                    {"description": "Consulting services", "quantity": 2, "unit_price": 50.0},
                ],
            },
            {
                "customer_id": 2,
                "invoice_number": "INV-002",
                "due_date": "2025-10-15",
                "total_amount": 200.0,
                "status": "unpaid",
                "lines": [
                    {"description": "Software license", "quantity": 1, "unit_price": 200.0},
                ],
            },
        ]

        for inv in sample_invoices:
            exists = (
                db.query(Invoice)
                  .filter(Invoice.invoice_number == inv["invoice_number"])
                  .first()
            )
            if exists:
                print(f"Skipping existing invoice {inv['invoice_number']}")
                continue

            due_dt = datetime.strptime(inv["due_date"], "%Y-%m-%d")
            invoice = Invoice(
                customer_id=inv["customer_id"],
                invoice_number=inv["invoice_number"],
                due_date=due_dt,
                total_amount=inv["total_amount"],
                status=inv["status"]
            )
            db.add(invoice)
            db.flush()  # populate invoice.id

            for line in inv["lines"]:
                db.add(InvoiceLine(
                    invoice_id=invoice.id,
                    description=line["description"],
                    quantity=line["quantity"],
                    unit_price=line["unit_price"]
                ))

        db.commit()

        # ─── Sample Payments & Allocations ───
        sample_payments = [
            {
                "customer_id": 1,
                "amount": 50.0,
                "method": "bank_transfer",
                "allocations": [
                    {"invoice_number": "INV-001", "amount": 50.0},
                ],
            },
            {
                "customer_id": 2,
                "amount": 75.0,
                "method": "cash",
                "allocations": [
                    {"invoice_number": "INV-002", "amount": 75.0},
                ],
            },
        ]

        for pay in sample_payments:
            exists = (
                db.query(Payment)
                  .filter(
                      Payment.customer_id == pay["customer_id"],
                      Payment.amount == pay["amount"]
                  )
                  .first()
            )
            if exists:
                print(f"Skipping existing payment {pay['method']} of {pay['amount']}")
                continue

            payment = Payment(
                customer_id=pay["customer_id"],
                amount=pay["amount"],
                method=pay["method"]
            )
            db.add(payment)
            db.flush()  # populate payment.id

            for alloc in pay["allocations"]:
                inv_obj = (
                    db.query(Invoice)
                      .filter(Invoice.invoice_number == alloc["invoice_number"])
                      .first()
                )
                if not inv_obj:
                    continue

                db.add(PaymentAllocation(
                    payment_id=payment.id,
                    invoice_id=inv_obj.id,
                    amount=alloc["amount"]
                ))

        db.commit()
        print("Seeding complete: invoices, lines, payments, allocations.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding invoices: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_invoices()
