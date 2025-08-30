# app/models/payment.py

from sqlalchemy import Column, Integer, ForeignKey, Float, String, DateTime, func
from sqlalchemy.orm import relationship
from app.db import Base

class Payment(Base):
    __tablename__ = "payments"

    id            = Column(Integer, primary_key=True, index=True)
    customer_id   = Column(Integer, ForeignKey("customers.id"), nullable=False)
    amount        = Column(Float, nullable=False)
    method        = Column(String, nullable=False, default="cash")
    received_at   = Column(DateTime, nullable=False, server_default=func.datetime("now"))

    allocations   = relationship("PaymentAllocation", back_populates="payment")
