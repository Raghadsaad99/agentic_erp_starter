# app/models/invoice.py

from sqlalchemy import Column, Integer, ForeignKey, String, Float, DateTime, func
from sqlalchemy.orm import relationship
from app.db import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    customer_id   = Column(Integer, ForeignKey("customers.id"), nullable=False)
    invoice_number= Column(String, unique=True, nullable=False)
    issue_date    = Column(DateTime, nullable=False, server_default=func.datetime("now"))
    due_date      = Column(DateTime, nullable=False)
    total_amount  = Column(Float, nullable=False, default=0.0)
    status        = Column(String, nullable=False, default="unpaid")
    created_at    = Column(DateTime, nullable=False, server_default=func.datetime("now"))

    customer      = relationship("Customer", back_populates="invoices")
    lines         = relationship("InvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    payments      = relationship("PaymentAllocation", back_populates="invoice")
