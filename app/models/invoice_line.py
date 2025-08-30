# app/models/invoice_line.py

from sqlalchemy import Column, Integer, ForeignKey, String, Float
from sqlalchemy.orm import relationship
from app.db import Base

class InvoiceLine(Base):
    __tablename__ = "invoice_lines"

    id           = Column(Integer, primary_key=True, index=True)
    invoice_id   = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description  = Column(String, nullable=False)
    quantity     = Column(Integer, nullable=False, default=1)
    unit_price   = Column(Float, nullable=False, default=0.0)

    invoice      = relationship("Invoice", back_populates="lines")
