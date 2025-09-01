# app/models/payment_allocation.py

from sqlalchemy import Column, Integer, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.db import Base 

class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    id            = Column(Integer, primary_key=True, index=True)
    payment_id    = Column(Integer, ForeignKey("payments.id"), nullable=False)
    invoice_id    = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    amount        = Column(Float, nullable=False)

    payment       = relationship("Payment", back_populates="allocations")
    invoice       = relationship("Invoice", back_populates="payments")
