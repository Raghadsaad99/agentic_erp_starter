
# seed_customers.py
from sqlalchemy.orm import Session
from app.db import SessionLocal, engine, Base
from app.models.customer import Customer

def seed_customers():
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)

    db: Session = SessionLocal()
    try:
        sample_customers = [
            {"name": "Acme Corp", "email": "contact@acme.com", "phone": "123-456-7890"},
            {"name": "Globex",   "email": "info@globex.com",    "phone": "098-765-4321"},
        ]

        for cust in sample_customers:
            exists = (
                db.query(Customer)
                  .filter(Customer.email == cust["email"])
                  .first()
            )
            if not exists:
                db.add(Customer(**cust))

        db.commit()
        print("Seeding complete: customers table populated.")
    except Exception as e:
        db.rollback()
        print(f"Error seeding customers: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_customers()
