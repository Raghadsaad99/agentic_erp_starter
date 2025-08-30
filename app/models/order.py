# app/models/order.py

from sqlalchemy import (
    Column, Integer, ForeignKey, Float, String, DateTime, func
)
from sqlalchemy.orm import relationship
from app.db import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    total = Column(Float, nullable=False, default=0.0)
    status = Column(String, nullable=False, default="pending")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.datetime("now")
    )

    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
