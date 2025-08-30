# seed_orders.py

from sqlalchemy.orm import Session
from app.db import SessionLocal, engine, Base
import app.models.customer      # ensure Customer is registered
import app.models.order         # ensure Order is registered
import app.models.order_item    # ensure OrderItem is registered

from app.models.order import Order
from app.models.order_item import OrderItem

def seed_orders():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        sample_orders = [
            {
                "order_number": "ORD-001",
                "customer_id": 1,
                "total": 150.0,
                "status": "pending",
                "items": [
                    {"product_id": 1, "quantity": 3, "price": 50.0},
                ],
            },
            {
                "order_number": "ORD-002",
                "customer_id": 2,
                "total":  75.0,
                "status": "pending",
                "items": [
                    {"product_id": 2, "quantity": 1, "price": 75.0},
                ],
            },
        ]

        for o in sample_orders:
            exists = (
                db.query(Order)
                  .filter(Order.order_number == o["order_number"])
                  .first()
            )
            if exists:
                print(f"Skipping existing order {o['order_number']}")
                continue

            order = Order(
                order_number=o["order_number"],
                customer_id=o["customer_id"],
                total=o["total"],
                status=o["status"]
            )
            db.add(order)
            db.flush()  # populate order.id

            for itm in o["items"]:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=itm["product_id"],
                    quantity=itm["quantity"],
                    price=itm["price"]
                )
                db.add(order_item)

        db.commit()
        print("Seeding complete: orders and order_items populated.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding orders: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_orders()
